#!/usr/bin/env python3
"""
Empirica PostCompact Hook - Restore epistemic context after memory compacting

This hook runs when a new session starts after compacting.
It loads bootstrap + pre-compact ref-doc, presenting evidence for drift detection.
"""

import json
import sys
import subprocess
import os

# Add empirica to path for signaling module
from pathlib import Path
sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))

def main():
    # Read hook input from stdin (provided by Claude Code)
    hook_input = json.loads(sys.stdin.read())

    session_id = hook_input.get('session_id')
    source = hook_input.get('source')  # Should be 'compact'

    # Auto-detect latest Empirica session (no env var needed)
    empirica_session = None
    try:
        # Path already imported at top of file
        sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))
        from empirica.utils.session_resolver import get_latest_session_id

        # Get latest active claude-code* session
        # Try claude-code-* variants first, fallback to any active session
        for ai_pattern in ['claude-code', None]:
            try:
                empirica_session = get_latest_session_id(ai_id=ai_pattern, active_only=True)
                break
            except ValueError:
                continue
    except Exception:
        pass

    if not empirica_session:
        # Exit silently if no Empirica session active
        print(json.dumps({
            "ok": True,
            "skipped": True,
            "reason": "No active Empirica session detected"
        }))
        sys.exit(0)

    # Run project-bootstrap with fresh assessment and adaptive depth
    try:
        result = subprocess.run(
            [
                'empirica', 'project-bootstrap',
                '--include-live-state',
                '--fresh-assess',
                '--trigger', 'post_compact',  # Auto-loads pre-snapshot, calculates drift
                '--depth', 'auto',  # Adaptive depth based on drift
                '--output', 'json'
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )

        if result.returncode == 0:
            # Success - load output for injection
            bootstrap = json.loads(result.stdout) if result.stdout else {}

            # Load pre-snapshot for comparison
            try:
                ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
                snapshots = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)

                pre_snapshot = None
                if snapshots:
                    with open(snapshots[0], 'r') as f:
                        pre_snapshot = json.load(f)
            except:
                pre_snapshot = None

            # Calculate drift using proper check-drift API (not inline heuristics)
            drift = None
            drift_details = {}
            drift_report = None
            sentinel_action = None

            # Always try check-drift if we have a pre-snapshot
            if pre_snapshot:
                # Use check-drift CLI for proper epistemic drift detection
                # Signaling level can be set via environment variable
                signaling_level = os.environ.get('EMPIRICA_SIGNALING_LEVEL', 'default')
                try:
                    drift_result = subprocess.run(
                        [
                            'empirica', 'check-drift',
                            '--session-id', empirica_session,
                            '--trigger', 'post_summary',
                            '--threshold', '0.2',  # Standard drift threshold
                            '--signaling', signaling_level,
                            '--output', 'json'
                        ],
                        capture_output=True,
                        text=True,
                        timeout=15,
                        cwd=os.getcwd()
                    )

                    if drift_result.returncode == 0 and drift_result.stdout:
                        drift_report = json.loads(drift_result.stdout)
                        drift = drift_report.get('drift_score')
                        drift_details = drift_report.get('drift_details', {})

                        # Write drift cache for statusline
                        try:
                            from empirica.core.signaling import (
                                SignalingState, write_drift_cache,
                                get_drift_level, detect_sentinel_action
                            )

                            state = SignalingState(
                                phase='POST_COMPACT',
                                vectors=drift_report.get('current_vectors') or drift_report.get('current_state', {}).get('vectors'),
                                drift_score=drift,
                                drift_details=drift_details,
                                drift_level=get_drift_level(drift),
                                sentinel_action=detect_sentinel_action(drift, drift_details),
                                session_id=empirica_session,
                                ai_id='claude-code'
                            )
                            write_drift_cache(state, os.getcwd())
                        except Exception as cache_err:
                            # Cache write failure is non-fatal
                            pass

                        # Check for sentinel gate triggers
                        if drift_report.get('sentinel_triggered'):
                            sentinel_action = drift_report.get('sentinel_action')
                except Exception as e:
                    # Fallback to basic calculation if check-drift fails
                    pre_vectors = (
                        pre_snapshot.get('live_state', {}).get('vectors', {}) or
                        pre_snapshot.get('checkpoint', {}).get('vectors', {})
                    )
                    post_vectors = bootstrap.get('live_state', {}).get('vectors', {}) if bootstrap.get('live_state') else {}

                    for key in ['know', 'uncertainty', 'engagement', 'impact', 'completion']:
                        if key in pre_vectors and key in post_vectors:
                            drift_details[key] = post_vectors[key] - pre_vectors[key]

                    drift = sum(abs(v) for v in drift_details.values()) / len(drift_details) if drift_details else None

            # Print structured output for Claude Code to inject
            print(json.dumps({
                "ok": True,
                "empirica_session_id": empirica_session,
                "drift": drift,
                "drift_details": drift_details,
                "drift_report": drift_report,
                "sentinel_action": sentinel_action,
                "pre_snapshot": {
                    "timestamp": pre_snapshot.get('timestamp') if pre_snapshot else None,
                    "vectors": (
                        (pre_snapshot.get('live_state') or {}).get('vectors', {}) or
                        (pre_snapshot.get('checkpoint') or {}).get('vectors', {})
                    ) if pre_snapshot else {}
                },
                "post_state": {
                    "vectors": (bootstrap.get('live_state') or {}).get('vectors', {}),
                    "git": (bootstrap.get('live_state') or {}).get('git', {})
                },
                "breadcrumbs": {
                    "findings": bootstrap.get('findings', []),
                    "unknowns": bootstrap.get('unknowns', []),
                    "goals": bootstrap.get('goals', []),
                    "dead_ends": bootstrap.get('dead_ends', []),
                    "reference_docs": bootstrap.get('reference_docs', [])
                },
                "breadcrumbs_summary": {
                    "findings_count": len(bootstrap.get('findings', [])),
                    "unknowns_count": len(bootstrap.get('unknowns', [])),
                    "goals_count": len(bootstrap.get('goals', [])),
                    "dead_ends_count": len(bootstrap.get('dead_ends', []))
                },
                "inject_context": True,
                "message": "Post-compact: Bootstrap evidence loaded with adaptive depth"
            }), file=sys.stdout)

            # User-visible summary message with metacognitive signaling
            drift_msg = f"{drift:.1%} ({_drift_level(drift)})" if drift is not None else "N/A (no pre-state)"
            drift_emoji = _drift_emoji(drift)

            # Check for sentinel gate triggers
            sentinel_msg = ""
            if sentinel_action:
                sentinel_emoji = {
                    'HALT': '⛔',
                    'BRANCH': '🔱',
                    'REVISE': '🔄',
                    'LOCK': '🔒'
                }.get(sentinel_action, '⚠️')
                sentinel_msg = f"\n\n{sentinel_emoji} SENTINEL: {sentinel_action}\n   Memory drift exceeded safety threshold. Human review recommended."

            print(f"""
🔄 Empirica: Post-compact context loaded

📊 Drift Analysis: {drift_emoji}
   Overall drift: {drift_msg}{sentinel_msg}
""", file=sys.stderr)

            if drift_details:
                for key, value in drift_details.items():
                    direction = "↑" if value > 0 else "↓" if value < 0 else "→"
                    vec_emoji = _vector_emoji(key, abs(value) if isinstance(value, (int, float)) else 0.5)
                    print(f"   {key}: {vec_emoji} {direction} {abs(value):.2f}", file=sys.stderr)

            depth_msg = _get_depth_from_bootstrap(bootstrap)
            drift_context = f"based on {drift:.1%} drift" if drift is not None else "based on available context"

            print(f"""
📚 Bootstrap Evidence:
   Findings: {len(bootstrap.get('findings', []))}
   Unknowns: {len(bootstrap.get('unknowns', []))}
   Goals: {len(bootstrap.get('goals', []))}

💡 Context depth: {depth_msg}
   Adaptive loading {drift_context}
""", file=sys.stderr)

            sys.exit(0)
        else:
            # Error running project-bootstrap
            print(json.dumps({
                "ok": False,
                "error": result.stderr,
                "empirica_session_id": empirica_session
            }))
            sys.exit(1)  # Non-blocking error

    except subprocess.TimeoutExpired:
        print(json.dumps({
            "ok": False,
            "error": "project-bootstrap timed out (>30s)"
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)
        }))
        sys.exit(1)

def _drift_level(drift):
    """Convert drift percentage to level label"""
    if drift is None:
        return "unknown"
    elif drift > 0.3:
        return "high"
    elif drift > 0.1:
        return "medium"
    else:
        return "low"


def _drift_emoji(drift):
    """
    Return emoji based on drift level (Traffic Light system)

    Biological Dashboard Calibration:
    - Crystalline (🔵): Delta < 0.1 - Ground truth; pure coherence
    - Solid (🟢): 0.1 ≤ Delta < 0.2 - Working knowledge
    - Emergent (🟡): 0.2 ≤ Delta < 0.3 - Forming understanding
    - Flicker (🔴): 0.3 ≤ Delta < 0.4 - Active uncertainty
    - Void (⚪): No data or Delta ≥ 0.4 - Unknown territory
    """
    if drift is None:
        return "⚪"  # Void - no data
    elif drift < 0.1:
        return "🔵"  # Crystalline - ground truth
    elif drift < 0.2:
        return "🟢"  # Solid - working knowledge
    elif drift < 0.3:
        return "🟡"  # Emergent - forming understanding
    elif drift < 0.4:
        return "🔴"  # Flicker - active uncertainty
    else:
        return "⚪"  # Void - unknown territory


def _vector_emoji(key, value):
    """
    Return emoji for individual vector based on value and type

    Vector interpretation:
    - High positive drift (>0.2): Significant change
    - Moderate drift (0.1-0.2): Normal variation
    - Low drift (<0.1): Stable

    Key-specific interpretations:
    - know: Higher = better (learning)
    - uncertainty: Lower = better (confidence)
    - completion: Higher = progress
    - engagement: Stability preferred
    """
    # Vector-specific interpretations
    if key == "uncertainty":
        # For uncertainty, lower is better
        if value < 0.1:
            return "🟢"  # Stable low uncertainty
        elif value < 0.2:
            return "🟡"  # Moderate uncertainty change
        else:
            return "🔴"  # High uncertainty drift (concerning)
    elif key in ["know", "completion"]:
        # For knowledge/completion, positive drift is good
        if value < 0.1:
            return "⚪"  # Minimal change
        elif value < 0.2:
            return "🟢"  # Good progress
        else:
            return "🔵"  # Significant learning
    elif key == "impact":
        # Impact changes are noteworthy
        if value < 0.1:
            return "⚪"  # Minimal
        elif value < 0.3:
            return "🟡"  # Moderate
        else:
            return "🔴"  # High impact drift
    else:
        # Generic vectors (engagement, context, etc.)
        if value < 0.1:
            return "🟢"  # Stable
        elif value < 0.2:
            return "🟡"  # Moderate change
        else:
            return "🔴"  # Significant drift

def _get_depth_from_bootstrap(bootstrap):
    """Infer depth from loaded data size"""
    findings_count = len(bootstrap.get('findings', []))
    if findings_count <= 5:
        return "minimal"
    elif findings_count <= 10:
        return "moderate"
    else:
        return "full"

if __name__ == '__main__':
    main()
