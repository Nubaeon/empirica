"""
Session Create Command - Explicit session creation
"""

import json
import sys
from ..cli_utils import handle_cli_error


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
        
        db = SessionDatabase()
        session_id = db.create_session(
            ai_id=ai_id,
            components_loaded=6,  # Standard component count
            subject=subject
        )
        db.close()  # Close connection before auto-capture (prevents lock)

        # NOTE: PREFLIGHT must be user-submitted with genuine vectors
        # Do NOT auto-generate - breaks continuity and learning metrics
        # Users must submit: empirica preflight-submit - < preflight.json

        # Initialize auto-capture for this session
        from empirica.core.issue_capture import initialize_auto_capture
        try:
            auto_capture = initialize_auto_capture(session_id, enable=True)
            if output_format != 'json':
                print(f"✅ Auto-capture enabled for this session")
        except Exception as e:
            if output_format != 'json':
                print(f"⚠️  Auto-capture initialization warning: {e}")

        # Re-open database for project linking
        db = SessionDatabase()
        
        # Try to auto-detect project from git remote URL (if not explicitly provided)
        if not project_id:
            try:
                # Get git remote URL
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    git_url = result.stdout.strip()
                    # Find project by matching repo URL
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT id FROM projects WHERE repos LIKE ?
                    """, (f'%{git_url}%',))
                    row = cursor.fetchone()
                    if row:
                        project_id = row['id']
            except Exception:
                pass

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
                "message": "Session created successfully"
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
