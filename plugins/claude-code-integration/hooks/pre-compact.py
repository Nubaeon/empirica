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

def main():
    # Read hook input from stdin (provided by Claude Code)
    hook_input = json.loads(sys.stdin.read())

    session_id = hook_input.get('session_id')
    trigger = hook_input.get('trigger', 'auto')  # 'auto' or 'manual'

    # Auto-detect latest Empirica session (no env var needed)
    empirica_session = None
    try:
        # Import after subprocess to avoid circular imports
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

    # Auto-commit working directory before snapshot
    # This ensures snapshot captures all recent work
    try:
        result = subprocess.run(
            ['git', 'add', '-A'],
            cwd=os.getcwd(),
            capture_output=True,
            timeout=5
        )

        # Only commit if there are changes staged
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=5
        )

        if status_result.stdout.strip():
            commit_result = subprocess.run(
                ['git', 'commit', '-m', f'[auto] Pre-compact snapshot - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=10
            )
    except Exception as e:
        # Auto-commit failure is not fatal
        pass

    # Run project-bootstrap with fresh assessment
    try:
        result = subprocess.run(
            [
                'empirica', 'project-bootstrap',
                '--include-live-state',
                '--fresh-assess',
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

            # Save snapshot to .empirica/ref-docs
            from pathlib import Path
            from datetime import datetime

            ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
            ref_docs_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            snapshot_path = ref_docs_dir / f"pre_summary_{timestamp}.json"

            snapshot = {
                "type": "pre_summary_snapshot",
                "timestamp": timestamp,
                "session_id": bootstrap.get('session_id'),
                "trigger": trigger,
                "live_state": bootstrap.get('live_state'),
                "breadcrumbs_summary": {
                    "findings_count": len(bootstrap.get('findings', [])),
                    "unknowns_count": len(bootstrap.get('unknowns', [])),
                    "goals_count": len(bootstrap.get('goals', [])),
                    "dead_ends_count": len(bootstrap.get('dead_ends', []))
                }
            }

            with open(snapshot_path, 'w') as f:
                json.dump(snapshot, f, indent=2)

            print(json.dumps({
                "ok": True,
                "trigger": trigger,
                "empirica_session_id": bootstrap.get('session_id'),
                "snapshot_saved": True,
                "snapshot_path": str(snapshot_path),
                "message": f"Pre-compact snapshot saved ({trigger} compact)"
            }), file=sys.stdout)

            # Also print user-visible message to stderr
            print(f"""
📸 Empirica: Pre-compact snapshot saved
   Session: {bootstrap.get('session_id', 'Unknown')[:8]}...
   Trigger: {trigger}
   Snapshot: {snapshot_path.name}
   Fresh state: {bootstrap.get('live_state', {}).get('fresh', False)}
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
