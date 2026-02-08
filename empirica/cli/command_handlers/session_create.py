"""
Session Create Command - Explicit session creation

Session lifecycle:
- Auto-closes previous sessions in SAME project with POSTFLIGHT
- Warns about active sessions in OTHER projects (doesn't auto-close)
- Ensures complete trajectories for calibration
"""

import json
import re
import sys
from ..cli_utils import handle_cli_error


def _is_uuid_format(value: str) -> bool:
    """Check if a string looks like a UUID (8-4-4-4-12 hex format)."""
    if not value or not isinstance(value, str):
        return False
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, value.lower()))


def auto_close_previous_sessions(db, ai_id, current_project_id, current_instance_id=None, output_format='json'):
    """
    Auto-close previous sessions with POSTFLIGHT for clean lifecycle.

    - Same project AND same instance: auto-close with POSTFLIGHT
    - Same project, different instance: leave open (multi-pane support)
    - Other projects: warn only (don't auto-close)

    Args:
        db: SessionDatabase instance
        ai_id: AI identifier
        current_project_id: Project ID for the new session
        current_instance_id: Instance ID (e.g., tmux:%8) for multi-pane isolation
        output_format: Output format ('json' or 'human')

    Returns: dict with closed_sessions and warnings
    """
    from datetime import datetime

    cursor = db.conn.cursor()
    result = {
        "closed_sessions": [],
        "warnings": []
    }

    # Find all active sessions for this AI (no end_time timestamp)
    cursor.execute("""
        SELECT session_id, project_id, created_at, instance_id
        FROM sessions
        WHERE ai_id = ? AND end_time IS NULL
        ORDER BY created_at DESC
    """, (ai_id,))
    active_sessions = cursor.fetchall()

    for session in active_sessions:
        session_id = session['session_id']
        session_project_id = session['project_id']
        session_instance_id = session['instance_id']

        # Same project: check instance_id for multi-pane support
        if session_project_id == current_project_id:
            # Only auto-close if same instance OR no instance tracking
            # This allows multiple tmux panes to have concurrent sessions
            if current_instance_id and session_instance_id and session_instance_id != current_instance_id:
                # Different instance in same project - leave open (multi-pane)
                continue
            # Same project: auto-close with POSTFLIGHT

            # Get last CHECK or PREFLIGHT vectors for POSTFLIGHT
            cursor.execute("""
                SELECT know, uncertainty, do, context, clarity, coherence,
                       signal, density, state, change, completion, impact, engagement
                FROM reflexes
                WHERE session_id = ? AND phase IN ('CHECK', 'PREFLIGHT')
                ORDER BY timestamp DESC LIMIT 1
            """, (session_id,))
            last_vectors = cursor.fetchone()

            # Create auto-POSTFLIGHT
            if last_vectors:
                vectors = {
                    'know': last_vectors['know'] or 0.5,
                    'uncertainty': last_vectors['uncertainty'] or 0.3,
                    'do': last_vectors['do'] or 0.5,
                    'context': last_vectors['context'] or 0.5,
                    'clarity': last_vectors['clarity'] or 0.5,
                    'coherence': last_vectors['coherence'] or 0.5,
                    'signal': last_vectors['signal'] or 0.5,
                    'density': last_vectors['density'] or 0.5,
                    'state': last_vectors['state'] or 0.5,
                    'change': last_vectors['change'] or 0.5,
                    'completion': 1.0,  # Session ended = complete
                    'impact': last_vectors['impact'] or 0.5,
                    'engagement': last_vectors['engagement'] or 0.5,
                }
            else:
                # No vectors found, use defaults
                vectors = {
                    'know': 0.5, 'uncertainty': 0.3, 'do': 0.5, 'context': 0.5,
                    'clarity': 0.5, 'coherence': 0.5, 'signal': 0.5, 'density': 0.5,
                    'state': 0.5, 'change': 0.5, 'completion': 1.0, 'impact': 0.5,
                    'engagement': 0.5
                }

            # Insert auto-POSTFLIGHT
            timestamp = datetime.now().timestamp()
            reflex_data = json.dumps({
                'auto_closed': True,
                'reason': 'New session created',
                'vectors': vectors
            })

            cursor.execute("""
                INSERT INTO reflexes (
                    session_id, phase, know, uncertainty, do, context,
                    clarity, coherence, signal, density, state, change,
                    completion, impact, engagement, reflex_data, timestamp
                ) VALUES (?, 'POSTFLIGHT', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                vectors['know'], vectors['uncertainty'], vectors['do'], vectors['context'],
                vectors['clarity'], vectors['coherence'], vectors['signal'], vectors['density'],
                vectors['state'], vectors['change'], vectors['completion'], vectors['impact'],
                vectors['engagement'], reflex_data, timestamp
            ))

            # Mark session as ended
            cursor.execute("""
                UPDATE sessions SET end_time = ? WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))

            result["closed_sessions"].append({
                "session_id": session_id,
                "project_id": session_project_id
            })

        else:
            # Different project: warn only
            if session_project_id:
                # Get project name for nicer warning
                cursor.execute("SELECT name FROM projects WHERE id = ?", (session_project_id,))
                project_row = cursor.fetchone()
                project_name = project_row['name'] if project_row else session_project_id[:8]

                result["warnings"].append({
                    "session_id": session_id,
                    "project_id": session_project_id,
                    "project_name": project_name,
                    "message": f"Active session in project '{project_name}' - run 'empirica session-close' there"
                })

    db.conn.commit()
    return result


def handle_session_create_command(args):
    """Create a new session - AI-first with config file support"""
    try:
        import os
        import subprocess
        from empirica.data.session_database import SessionDatabase
        from ..cli_utils import parse_json_safely

        # AI-FIRST MODE: Check if config file provided
        config_data = None
        if hasattr(args, 'config') and args.config:
            if args.config == '-':
                config_data = parse_json_safely(sys.stdin.read())
            else:
                if not os.path.exists(args.config):
                    print(json.dumps({"ok": False, "error": f"Config file not found: {args.config}"}))
                    sys.exit(1)
                with open(args.config, 'r') as f:
                    config_data = parse_json_safely(f.read())

        # Extract parameters from config or fall back to legacy flags
        if config_data:
            # AI-FIRST MODE
            ai_id = config_data.get('ai_id')
            user_id = config_data.get('user_id')
            project_id = config_data.get('project_id')  # Optional explicit project ID
            parent_session_id = config_data.get('parent_session_id')
            output_format = 'json'

            # Validate required fields
            if not ai_id:
                print(json.dumps({
                    "ok": False,
                    "error": "Config file must include 'ai_id' field",
                    "hint": "See /tmp/session_config_example.json for schema"
                }))
                sys.exit(1)
        else:
            # LEGACY MODE
            ai_id = args.ai_id
            user_id = getattr(args, 'user_id', None)
            project_id = getattr(args, 'project_id', None)  # Optional explicit project ID
            parent_session_id = getattr(args, 'parent_session_id', None)
            output_format = getattr(args, 'output', 'json')  # Default to JSON

            # Validate required fields for legacy mode
            if not ai_id:
                print(json.dumps({
                    "ok": False,
                    "error": "Legacy mode requires --ai-id flag",
                    "hint": "For AI-first mode, use: empirica session-create config.json"
                }))
                sys.exit(1)

        # Auto-detect subject from current directory
        from empirica.config.project_config_loader import get_current_subject
        subject = config_data.get('subject') if config_data else getattr(args, 'subject', None)
        if subject is None:
            subject = get_current_subject()  # Auto-detect from directory
        
        # Show project context before creating session
        if output_format != 'json':
            from empirica.cli.cli_utils import print_project_context
            print()
            project_context = print_project_context(quiet=False, verbose=False)
            print()

        # AUTO-INIT: Initialize .empirica/ if not present (issue #25)
        # Simple: if --auto-init flag passed and .empirica/ missing, run project-init
        auto_init_performed = False
        if getattr(args, 'auto_init', False):
            from empirica.config.path_resolver import get_git_root
            git_root = get_git_root()

            if not git_root:
                if output_format == 'json':
                    print(json.dumps({
                        "ok": False,
                        "error": "Cannot auto-init: Not in a git repository",
                        "hint": "Run 'git init' first, then try again"
                    }))
                else:
                    print("❌ Cannot auto-init: Not in a git repository")
                    print("   Run 'git init' first, then try again")
                sys.exit(1)

            # Check if .empirica/ already exists
            empirica_config = git_root / '.empirica' / 'config.yaml'
            if not empirica_config.exists():
                if output_format != 'json':
                    print("🔧 Auto-initializing Empirica in this repository...")

                try:
                    from empirica.cli.command_handlers.project_init import handle_project_init_command
                    from types import SimpleNamespace

                    # Use defaults: directory name, no description
                    init_args = SimpleNamespace(
                        non_interactive=True,
                        output='json' if output_format == 'json' else 'default',
                        project_name=git_root.name,
                        project_description=None,
                        enable_beads=False,
                        create_semantic_index=False,
                        force=False
                    )

                    result = handle_project_init_command(init_args)
                    if result is None:
                        if output_format != 'json':
                            print("❌ Auto-init failed. Run 'empirica project-init' manually.")
                        sys.exit(1)

                    auto_init_performed = True
                    project_id = result.get('project_id')

                    if output_format != 'json':
                        print(f"✅ Project auto-initialized: {git_root.name}")
                        print()

                except Exception as e:
                    if output_format == 'json':
                        print(json.dumps({
                            "ok": False,
                            "error": f"Auto-init failed: {e}",
                            "hint": "Run 'empirica project-init' manually"
                        }))
                    else:
                        print(f"❌ Auto-init failed: {e}")
                        print("   Run 'empirica project-init' manually")
                    sys.exit(1)

        # REQUIRE INITIALIZATION: Fail early if project not initialized (prevents orphaned sessions)
        # Only check if in a git repo - non-git directories fall back to global ~/.empirica/
        from empirica.config.path_resolver import get_git_root
        git_root = get_git_root()
        if git_root:
            empirica_config = git_root / '.empirica' / 'config.yaml'
            if not empirica_config.exists():
                if output_format == 'json':
                    print(json.dumps({
                        "ok": False,
                        "error": "Project not initialized",
                        "hint": "Run 'empirica project-init' or use 'empirica session-create --auto-init'",
                        "git_root": str(git_root)
                    }))
                else:
                    print(f"❌ Project not initialized in {git_root.name}")
                    print(f"\nOptions:")
                    print(f"  1. Initialize: empirica project-init")
                    print(f"  2. Auto-init:  empirica session-create --ai-id {ai_id} --auto-init")
                sys.exit(1)

        # EARLY PROJECT DETECTION: Needed for auto-close of previous sessions
        early_project_id = project_id  # From config if provided

        # Resolve folder_name to UUID if explicit --project-id was passed
        # Without this, passing --project-id empirica stores 'empirica' instead of UUID
        if early_project_id and not _is_uuid_format(early_project_id):
            try:
                import sqlite3 as _sqlite3
                workspace_db = os.path.join(os.path.expanduser('~'), '.empirica', 'workspace', 'workspace.db')
                if os.path.exists(workspace_db):
                    conn = _sqlite3.connect(workspace_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM global_projects WHERE name = ?", (early_project_id,))
                    row = cursor.fetchone()
                    conn.close()
                    if row:
                        early_project_id = row[0]  # Use UUID instead of folder_name
            except Exception:
                pass  # Keep original value if resolution fails

        if not early_project_id:
            # Method 0: Check resolver context files (highest priority)
            # Priority: instance_projects (TMUX) > active_work (Claude session) > canonical active_work
            try:
                from empirica.utils.session_resolver import get_tty_session
                import json as _json
                import sqlite3 as _sqlite3

                def _resolve_folder_to_uuid(folder_name):
                    """Resolve folder_name to project UUID via workspace.db."""
                    if not folder_name:
                        return None
                    workspace_db = os.path.join(os.path.expanduser('~'), '.empirica', 'workspace', 'workspace.db')
                    if os.path.exists(workspace_db):
                        conn = _sqlite3.connect(workspace_db)
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM global_projects WHERE name = ?", (folder_name,))
                        row = cursor.fetchone()
                        conn.close()
                        if row:
                            return row[0]
                    return None

                def _get_project_id_from_context(context_data):
                    """Extract project_id from context data, resolving folder_name or project_path."""
                    # Priority 1: Direct project_id
                    if context_data.get('project_id'):
                        pid = context_data['project_id']
                        # If it's already a UUID, use it; otherwise resolve
                        if _is_uuid_format(pid):
                            return pid
                        return _resolve_folder_to_uuid(pid)

                    # Priority 2: folder_name (resolve via workspace.db)
                    if context_data.get('folder_name'):
                        resolved = _resolve_folder_to_uuid(context_data['folder_name'])
                        if resolved:
                            return resolved

                    # Priority 3: project_path (read project.yaml at that path)
                    if context_data.get('project_path'):
                        project_path = context_data['project_path']
                        import yaml
                        project_yaml = os.path.join(project_path, '.empirica', 'project.yaml')
                        if os.path.exists(project_yaml):
                            try:
                                with open(project_yaml, 'r') as f:
                                    config = yaml.safe_load(f)
                                    if config and config.get('project_id'):
                                        return config['project_id']
                            except Exception:
                                pass

                    return None

                # Priority 0a: Check instance_projects (TMUX-keyed, works via Bash tool)
                # This is written by project-init and project-switch
                tmux_pane = os.environ.get('TMUX_PANE')
                if tmux_pane and not early_project_id:
                    instance_id = f"tmux_{tmux_pane.lstrip('%')}"
                    instance_file = os.path.join(
                        os.path.expanduser('~'), '.empirica',
                        'instance_projects', f'{instance_id}.json'
                    )
                    if os.path.exists(instance_file):
                        with open(instance_file, 'r') as f:
                            instance_data = _json.load(f)
                            early_project_id = _get_project_id_from_context(instance_data)

                # Priority 0b: Try TTY-specific active_work (multi-instance isolation)
                if not early_project_id:
                    tty_session = get_tty_session(warn_if_stale=False)
                    if tty_session:
                        claude_session_id = tty_session.get('claude_session_id')
                        if claude_session_id:
                            active_work_path = os.path.join(
                                os.path.expanduser('~'), '.empirica',
                                f'active_work_{claude_session_id}.json'
                            )
                            if os.path.exists(active_work_path):
                                with open(active_work_path, 'r') as f:
                                    active_work = _json.load(f)
                                    early_project_id = _get_project_id_from_context(active_work)

                # Priority 0c: Fallback to canonical active_work.json
                if not early_project_id:
                    canonical_path = os.path.join(os.path.expanduser('~'), '.empirica', 'active_work.json')
                    if os.path.exists(canonical_path):
                        with open(canonical_path, 'r') as f:
                            active_work = _json.load(f)
                            early_project_id = _get_project_id_from_context(active_work)
            except Exception:
                pass  # Fall through to other methods

            # Method 1: Read from local .empirica/project.yaml (only if Method 0 didn't find)
            if not early_project_id:
                try:
                    import yaml
                    project_yaml = os.path.join(os.getcwd(), '.empirica', 'project.yaml')
                    if os.path.exists(project_yaml):
                        with open(project_yaml, 'r') as f:
                            project_config = yaml.safe_load(f)
                            if project_config and project_config.get('project_id'):
                                early_project_id = project_config['project_id']
                except Exception:
                    pass

            # Method 1b: Resolve folder_name to UUID via workspace.db
            # project.yaml may contain folder_name (e.g., 'empirica') instead of UUID
            # We need the UUID for consistent cross-table references (goals, sessions)
            if early_project_id and not _is_uuid_format(early_project_id):
                try:
                    import sqlite3
                    workspace_db = os.path.join(os.path.expanduser('~'), '.empirica', 'workspace', 'workspace.db')
                    if os.path.exists(workspace_db):
                        conn = sqlite3.connect(workspace_db)
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM global_projects WHERE name = ?", (early_project_id,))
                        row = cursor.fetchone()
                        if row:
                            early_project_id = row[0]  # Use UUID
                        conn.close()
                except Exception:
                    pass  # Keep folder_name if resolution fails

            # Method 2: Match git remote URL
            if not early_project_id:
                try:
                    result = subprocess.run(
                        ['git', 'remote', 'get-url', 'origin'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        git_url = result.stdout.strip()
                        db_temp = SessionDatabase()
                        cursor = db_temp.conn.cursor()
                        cursor.execute("""
                            SELECT id FROM projects WHERE repos LIKE ?
                        """, (f'%{git_url}%',))
                        row = cursor.fetchone()
                        if row:
                            early_project_id = row['id']
                        db_temp.close()
                except Exception:
                    pass

        # AUTO-CLOSE PREVIOUS SESSIONS before creating new one
        # Get current instance_id for multi-pane isolation
        from empirica.utils.session_resolver import get_instance_id
        current_instance_id = get_instance_id()

        db = SessionDatabase()
        close_result = auto_close_previous_sessions(db, ai_id, early_project_id, current_instance_id, output_format)

        if close_result["closed_sessions"]:
            if output_format != 'json':
                for closed in close_result["closed_sessions"]:
                    print(f"🔄 Auto-closed previous session: {closed['session_id'][:8]}... (POSTFLIGHT submitted)")
            # Note: JSON output will include this in final result

        if close_result["warnings"]:
            if output_format != 'json':
                for warning in close_result["warnings"]:
                    print(f"⚠️  {warning['message']}")

        # Now create the new session
        session_id = db.create_session(
            ai_id=ai_id,
            components_loaded=6,  # Standard component count
            subject=subject,
            parent_session_id=parent_session_id
        )
        db.close()  # Close connection before auto-capture (prevents lock)

        # Update active_session file for statusline (instance-specific)
        # Uses instance_id (e.g., tmux:%0) to prevent cross-pane bleeding
        from pathlib import Path
        from empirica.utils.session_resolver import get_instance_id

        instance_id = get_instance_id()
        instance_suffix = ""
        if instance_id:
            # Sanitize instance_id for filename (replace special chars)
            safe_instance = instance_id.replace(":", "_").replace("%", "")
            instance_suffix = f"_{safe_instance}"

        # ALWAYS write to global ~/.empirica/ for instance-specific files
        # This ensures statusline can find active session regardless of cwd
        # The project_path in the JSON tells us which project's DB to use
        active_session_file = Path.home() / '.empirica' / f'active_session{instance_suffix}'
        active_session_file.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write: temp file + rename prevents partial reads from concurrent access
        # Store JSON with session_id AND project_path so statusline can find
        # the correct DB even when cwd changes (prevents user confusion about data loss)
        import tempfile
        import json as _json
        active_session_data = {
            "session_id": session_id,
            "project_path": str(Path.cwd()),
            "ai_id": ai_id
        }
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(active_session_file.parent))
        try:
            with os.fdopen(tmp_fd, 'w') as tmp_f:
                tmp_f.write(_json.dumps(active_session_data))
            os.rename(tmp_path, str(active_session_file))
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        # Write TTY session file for multi-instance isolation
        # This enables CLI commands to find the active session via TTY context
        try:
            from empirica.utils.session_resolver import write_tty_session
            write_tty_session(
                empirica_session_id=session_id,
                project_path=str(Path.cwd())
            )
        except Exception:
            pass  # Non-critical - isolation is best-effort

        # NOTE: PREFLIGHT must be user-submitted with genuine vectors
        # Do NOT auto-generate - breaks continuity and learning metrics
        # Users must submit: empirica preflight-submit - < preflight.json

        # Initialize auto-capture for this session
        from empirica.core.issue_capture import initialize_auto_capture, install_auto_capture_hooks
        try:
            auto_capture = initialize_auto_capture(session_id, enable=True)
            install_auto_capture_hooks(auto_capture)  # Install logging hooks
            if output_format != 'json':
                print(f"✅ Auto-capture enabled with logging hooks")
        except Exception as e:
            if output_format != 'json':
                print(f"⚠️  Auto-capture initialization warning: {e}")

        # Re-open database for project linking
        db = SessionDatabase()

        # Use early-detected project_id (already computed above for auto-close)
        # ALWAYS use early_project_id since it may have been resolved from folder_name to UUID
        project_id = early_project_id

        # Link session to project if found
        if project_id:
            cursor = db.conn.cursor()
            cursor.execute("""
                UPDATE sessions SET project_id = ? WHERE session_id = ?
            """, (project_id, session_id))
            db.conn.commit()
            
            # Show confirmation that session is linked to this project
            if output_format != 'json':
                cursor.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
                row = cursor.fetchone()
                if row:
                    print(f"✅ Session linked to project: {row['name']}")
                    print()

        db.close()

        if output_format == 'json':
            result = {
                "ok": True,
                "session_id": session_id,
                "ai_id": ai_id,
                "user_id": user_id,
                "project_id": project_id,
                "parent_session_id": parent_session_id,
                "auto_init_performed": auto_init_performed,
                "message": "Session created successfully",
                "lifecycle": {
                    "auto_closed_sessions": close_result["closed_sessions"],
                    "cross_project_warnings": close_result["warnings"]
                }
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Session created successfully!")
            print(f"   📋 Session ID: {session_id}")
            print(f"   🤖 AI ID: {ai_id}")

            # Show project breadcrumbs if project was detected
            if project_id:
                print(f"   📁 Project: {project_id[:8]}...")
                print(f"\n📚 Project Context:")
                db = SessionDatabase()
                breadcrumbs = db.bootstrap_project_breadcrumbs(project_id, mode="session_start")
                db.close()

                if "error" not in breadcrumbs:
                    project = breadcrumbs['project']
                    print(f"   Project: {project['name']}")
                    print(f"   Description: {project['description']}")

                    if breadcrumbs.get('findings'):
                        print(f"\n   Recent Findings (last 5):")
                        for finding in breadcrumbs['findings'][:5]:
                            print(f"     • {finding}")

                    unresolved = [u for u in breadcrumbs.get('unknowns', []) if not u['is_resolved']]
                    if unresolved:
                        print(f"\n   Unresolved Unknowns:")
                        for u in unresolved[:3]:
                            print(f"     • {u['unknown']}")

                    if breadcrumbs.get('available_skills'):
                        print(f"\n   Available Skills:")
                        for skill in breadcrumbs['available_skills'][:3]:
                            print(f"     • {skill['title']} ({', '.join(skill['tags'])})")

            print(f"\nNext steps:")
            print(f"   empirica preflight --session-id {session_id} --prompt \"Your task\"")
        
    except Exception as e:
        if getattr(args, 'output', 'default') == 'json':
            print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        else:
            print(f"❌ Failed to create session: {e}")
        handle_cli_error(e, "Session create", getattr(args, 'verbose', False))
        sys.exit(1)
