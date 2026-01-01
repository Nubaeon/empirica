#!/usr/bin/env python3
"""
Empirica PreCompact Hook - Capture epistemic state before memory compacting

This hook runs automatically before Claude Code compacts the conversation.
It saves a checkpoint as a ref-doc to enable drift detection post-compact.
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime


def find_project_root() -> Path:
    """
    Find the Empirica project root by searching for .empirica/ directory with valid database.

    Search order:
    1. EMPIRICA_WORKSPACE_ROOT environment variable
    2. Known development paths (prioritized to avoid polluted temp dirs)
    3. Search upward from current directory
    4. Fallback to current directory
    """
    def has_valid_db(path: Path) -> bool:
        """Check if path has valid Empirica database"""
        db_path = path / '.empirica' / 'sessions' / 'sessions.db'
        return db_path.exists() and db_path.stat().st_size > 0

    # 1. Check environment variable
    if workspace_root := os.getenv('EMPIRICA_WORKSPACE_ROOT'):
        workspace_path = Path(workspace_root).expanduser().resolve()
        if has_valid_db(workspace_path):
            return workspace_path

    # 2. Try known development paths FIRST (to avoid polluted temp dirs like /tmp/.empirica)
    known_paths = [
        Path.home() / 'empirical-ai' / 'empirica',
        Path.home() / 'empirica',
        Path('/workspace'),
    ]
    for path in known_paths:
        if has_valid_db(path):
            return path

    # 3. Search upward from current directory (only if has valid DB)
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if has_valid_db(parent):
            return parent
        # Stop at filesystem root
        if parent == parent.parent:
            break

    # 4. Fallback to current directory
    return Path.cwd()


def main():
    # Read hook input from stdin (provided by Claude Code)
    hook_input = json.loads(sys.stdin.read())

    session_id = hook_input.get('session_id')
    trigger = hook_input.get('trigger', 'auto')  # 'auto' or 'manual'

    # CRITICAL: Find and change to project root BEFORE importing empirica
    # This ensures SessionDatabase uses the correct database path
    project_root = find_project_root()
    original_cwd = os.getcwd()
    os.chdir(project_root)

    # Auto-detect latest Empirica session (no env var needed)
    empirica_session = None
    try:
        # Import after cwd change to use correct database
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
        pass  # Session detection failure is non-fatal

    if not empirica_session:
        # Exit silently if no Empirica session active
        print(json.dumps({
            "ok": True,
            "skipped": True,
            "reason": "No active Empirica session detected"
        }))
        sys.exit(0)

    # NOTE: Auto-commit removed to prevent polluting git history
    # Snapshots are saved to .empirica/ref-docs/ which is gitignored
    # If you need to preserve state, manually commit before compact

    # Step 1: Capture FRESH epistemic vectors (canonical via assess-state)
    print(f"\n📊 Step 1: Capture fresh vectors (assess-state - canonical)")
    assess_result = subprocess.run(
        ['empirica', 'assess-state', '--session-id', empirica_session, '--output', 'json'],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=os.getcwd()
    )
    
    fresh_vectors = {}
    if assess_result.returncode == 0:
        try:
            assess_data = json.loads(assess_result.stdout)
            fresh_vectors = assess_data.get('state', {}).get('vectors', {})
            print(f"  ✓ Fresh vectors: {len(fresh_vectors)} vectors captured")
        except Exception as e:
            print(f"  ⚠️  Could not parse assess-state output: {e}")
    else:
        print(f"  ⚠️  assess-state failed: {assess_result.stderr}")

    # Step 2: Run project-bootstrap for context anchor (findings, unknowns, goals)
    # CRITICAL: Must pass --ai-id to find the session
    ai_id = os.getenv('EMPIRICA_AI_ID', 'claude-code')
    print(f"\n📦 Step 2: Capture context anchor (project-bootstrap)")
    try:
        result = subprocess.run(
            [
                'empirica', 'project-bootstrap',
                '--ai-id', ai_id,
                '--include-live-state',
                '--trigger', 'pre_compact',
                '--output', 'json'
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()  # Run in current directory (project root)
        )

        if result.returncode == 0:
            # Success - save snapshot
            bootstrap = json.loads(result.stdout) if result.stdout else {}

            # Extract breadcrumbs (CLI wraps in {"ok", "project_id", "breadcrumbs"})
            breadcrumbs = bootstrap.get('breadcrumbs', bootstrap)

            # Save snapshot to .empirica/ref-docs (Path already imported at top)
            ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
            ref_docs_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            snapshot_path = ref_docs_dir / f"pre_summary_{timestamp}.json"

            # session_id and live_state are in breadcrumbs
            snapshot = {
                "type": "pre_summary_snapshot",
                "timestamp": timestamp,
                "session_id": breadcrumbs.get('session_id'),
                "trigger": trigger,
                "live_state": breadcrumbs.get('live_state'),
                "vectors_canonical": fresh_vectors,  # TIER 2a: Canonical vectors from assess-state
                "checkpoint": fresh_vectors or (breadcrumbs.get('live_state', {}).get('vectors', {}) if breadcrumbs.get('live_state') else {}),
                "breadcrumbs_summary": {
                    "findings_count": len(breadcrumbs.get('findings', [])),
                    "unknowns_count": len(breadcrumbs.get('unknowns', [])),
                    "goals_count": len(breadcrumbs.get('goals', [])),
                    "dead_ends_count": len(breadcrumbs.get('dead_ends', []))
                }
            }

            with open(snapshot_path, 'w') as f:
                json.dump(snapshot, f, indent=2)

            print(json.dumps({
                "ok": True,
                "trigger": trigger,
                "empirica_session_id": breadcrumbs.get('session_id'),
                "snapshot_saved": True,
                "snapshot_path": str(snapshot_path),
                "message": f"Pre-compact snapshot saved ({trigger} compact)"
            }), file=sys.stdout)

            # Also print user-visible message to stderr
            session_id_str = breadcrumbs.get('session_id', 'Unknown')
            session_display = session_id_str[:8] if session_id_str else 'Unknown'
            live_state = breadcrumbs.get('live_state', {})
            vectors = live_state.get('vectors', {}) if live_state else {}

            print(f"""
📸 Empirica: Pre-compact snapshot saved
   Session: {session_display}...
   Trigger: {trigger}
   Snapshot: {snapshot_path.name}
   Vectors: know={vectors.get('know', 'N/A')}, unc={vectors.get('uncertainty', 'N/A')}
""", file=sys.stderr)

            sys.exit(0)
        else:
            # Error running project-bootstrap
            print(json.dumps({
                "ok": False,
                "error": result.stderr,
                "empirica_session_id": empirica_session
            }))
            sys.exit(2)  # Blocking error (show to user)

    except subprocess.TimeoutExpired:
        print(json.dumps({
            "ok": False,
            "error": "project-bootstrap timed out (>30s)"
        }))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)
        }))
        sys.exit(2)

if __name__ == '__main__':
    main()
