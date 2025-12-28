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

def main():
    # Read hook input from stdin (provided by Claude Code)
    hook_input = json.loads(sys.stdin.read())

    session_id = hook_input.get('session_id')
    source = hook_input.get('source')  # Should be 'compact'

    # Auto-detect latest Empirica session (no env var needed)
    empirica_session = None
    try:
        # Import after subprocess to avoid circular imports
        from pathlib import Path
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
                from pathlib import Path
                ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
                snapshots = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)

                pre_snapshot = None
                if snapshots:
                    with open(snapshots[0], 'r') as f:
                        pre_snapshot = json.load(f)
            except:
                pre_snapshot = None

            # Calculate drift if both states available
            drift = None
            drift_details = {}
            if pre_snapshot and bootstrap.get('live_state'):
                # Handle both old and new snapshot formats
                # Old format: checkpoint.vectors
                # New format: live_state.vectors
                pre_vectors = (
                    pre_snapshot.get('live_state', {}).get('vectors', {}) or
                    pre_snapshot.get('checkpoint', {}).get('vectors', {})
                )
                post_vectors = bootstrap['live_state'].get('vectors', {})

                # Calculate drift for each vector
                for key in ['know', 'uncertainty', 'engagement', 'impact', 'completion']:
                    if key in pre_vectors and key in post_vectors:
                        drift_details[key] = post_vectors[key] - pre_vectors[key]

                # Average absolute drift
                drift = sum(abs(v) for v in drift_details.values()) / len(drift_details) if drift_details else None

            # Print structured output for Claude Code to inject
            print(json.dumps({
                "ok": True,
                "empirica_session_id": empirica_session,
                "drift": drift,
                "drift_details": drift_details,
                "pre_snapshot": {
                    "timestamp": pre_snapshot.get('timestamp') if pre_snapshot else None,
                    "vectors": (
                        pre_snapshot.get('live_state', {}).get('vectors', {}) or
                        pre_snapshot.get('checkpoint', {}).get('vectors', {})
                    ) if pre_snapshot else {}
                },
                "post_state": {
                    "vectors": bootstrap.get('live_state', {}).get('vectors', {}),
                    "git": bootstrap.get('live_state', {}).get('git', {})
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

            # User-visible summary message
            drift_msg = f"{drift:.1%} ({_drift_level(drift)})" if drift is not None else "N/A (no pre-state)"

            print(f"""
🔄 Empirica: Post-compact context loaded

📊 Drift Analysis:
   Overall drift: {drift_msg}
""", file=sys.stderr)

            if drift_details:
                for key, value in drift_details.items():
                    direction = "↑" if value > 0 else "↓" if value < 0 else "→"
                    print(f"   {key}: {direction} {abs(value):.2f}", file=sys.stderr)

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
