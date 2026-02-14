"""
Project Commands - Multi-repo/multi-session project tracking
"""

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Any
from ..cli_utils import handle_cli_error
from empirica.core.memory_gap_detector import MemoryGapDetector

logger = logging.getLogger(__name__)


# ============================================================================
# WORKSPACE DATABASE ACCESS
# ============================================================================
# The workspace database (~/.empirica/workspace/workspace.db) contains the
# global_projects table with all projects across the ecosystem.
# This is separate from SessionDatabase which operates on local project data.
# ============================================================================

def get_workspace_db_path() -> Path:
    """Get path to workspace database"""
    return Path.home() / '.empirica' / 'workspace' / 'workspace.db'


def get_workspace_projects() -> List[Dict[str, Any]]:
    """
    Get all projects from workspace database.

    Returns list of project dicts with keys:
    - id, name, description, trajectory_path, status, project_type
    - total_transactions, total_findings, total_unknowns, etc.
    - folder_name (derived from trajectory_path)
    """
    workspace_db = get_workspace_db_path()
    if not workspace_db.exists():
        return []

    try:
        conn = sqlite3.connect(str(workspace_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, name, description, trajectory_path, git_remote_url,
                git_branch, total_transactions, total_findings,
                total_unknowns, total_dead_ends, total_goals,
                last_transaction_id, last_transaction_timestamp,
                last_sync_timestamp, status, project_type, project_tags,
                created_timestamp, updated_timestamp
            FROM global_projects
            WHERE status = 'active'
            ORDER BY updated_timestamp DESC
        """)

        projects = []
        for row in cursor.fetchall():
            project = dict(row)
            # Derive folder name from trajectory_path
            # e.g., /home/user/empirical-ai/empirica-platform/.empirica -> empirica-platform
            traj_path = project.get('trajectory_path', '')
            if traj_path:
                folder_name = Path(traj_path).parent.name
                project['folder_name'] = folder_name
            else:
                project['folder_name'] = project.get('name', '')
            projects.append(project)

        conn.close()
        return projects
    except Exception as e:
        logger.warning(f"Failed to read workspace database: {e}")
        return []


def _update_active_work(project_path: str, folder_name: str, empirica_session_id: str = None, claude_session_id: str = None) -> bool:
    """
    Update active_work markers AND TTY session for cross-project continuity.

    This is called by project-switch to record which project is currently active.
    Updates:
    1. TTY session file's project_path - PRIMARY source for hooks/statusline
    2. Session-specific active_work file (if TTY session exists) - backup
    3. Canonical active_work file - fallback for first-time compaction

    The TTY session file is the source of truth for "what project is this
    Claude instance working on". Hooks and statusline read it to determine
    the correct project context.

    Args:
        project_path: Full path to the project directory
        folder_name: The project's folder name (ground truth identifier)
        empirica_session_id: Optional session ID to attach to (for Sentinel/MCP tools)
        claude_session_id: Claude Code conversation UUID (for instance isolation when called via Bash tool)

    Returns:
        True if successfully written, False otherwise
    """
    import time
    from empirica.utils.session_resolver import get_tty_session, get_tty_key

    try:
        marker_dir = Path.home() / '.empirica'
        marker_dir.mkdir(parents=True, exist_ok=True)

        # Try to get Claude session ID - prefer explicit parameter over TTY session
        # claude_session_id parameter is set when called from project-switch with --claude-session-id
        tty_session = get_tty_session()
        if not claude_session_id:
            claude_session_id = tty_session.get('claude_session_id') if tty_session else None

        # CRITICAL: Update instance_projects and TTY session with new project_path
        # instance_projects is used by Sentinel and statusline when running via Bash tool
        # TTY session is used for direct terminal context
        tty_key = get_tty_key()
        tmux_pane = os.environ.get('TMUX_PANE')
        instance_id = f"tmux_{tmux_pane.lstrip('%')}" if tmux_pane else None

        # When TMUX_PANE is absent (Bash tool subprocess), resolve instance_id
        # from claude_session_id by scanning instance_projects/ files.
        # Hooks (which DO have TMUX_PANE) write claude_session_id to instance_projects
        # at session start — this reverse-lookup finds the correct tmux pane.
        if not instance_id and claude_session_id:
            instance_dir = marker_dir / 'instance_projects'
            if instance_dir.exists():
                for ip_file in instance_dir.glob('tmux_*.json'):
                    try:
                        with open(ip_file, 'r') as f:
                            ip_data = json.load(f)
                        if ip_data.get('claude_session_id') == claude_session_id:
                            instance_id = ip_file.stem  # e.g. "tmux_14"
                            logger.debug(f"Resolved instance_id={instance_id} from claude_session_id match in {ip_file.name}")
                            break
                    except Exception:
                        continue

        # PRESERVE existing claude_session_id if TTY session doesn't have it
        # This handles the case where session-init hook ran and wrote claude_session_id
        # to instance_projects, but TTY session wasn't updated (e.g., Bash tool context)
        if not claude_session_id and instance_id:
            existing_instance_file = marker_dir / 'instance_projects' / f'{instance_id}.json'
            if existing_instance_file.exists():
                try:
                    with open(existing_instance_file, 'r') as f:
                        existing_data = json.load(f)
                        claude_session_id = existing_data.get('claude_session_id')
                        logger.debug(f"Preserved claude_session_id from existing instance_projects: {claude_session_id}")
                except Exception:
                    pass

        # Warn if claude_session_id is still null - instance isolation works but active_work
        # cross-referencing will be limited. Hooks (session-init, post-compact) are responsible
        # for establishing the claude_session_id linkage.
        if not claude_session_id and instance_id:
            logger.warning(
                f"claude_session_id unknown for {instance_id}. Instance isolation works via "
                f"instance_id, but active_work cross-referencing limited. This is normal if "
                f"called via Bash before any hook established the linkage."
            )

        # Write instance_projects FIRST - works via Bash tool where tty fails
        if instance_id:
            instance_dir = marker_dir / 'instance_projects'
            instance_dir.mkdir(parents=True, exist_ok=True)
            instance_file = instance_dir / f'{instance_id}.json'
            instance_data = {
                'project_path': project_path,
                'tty_key': tty_key,  # May be None if via Bash tool
                'claude_session_id': claude_session_id,
                'empirica_session_id': empirica_session_id,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z')
            }
            with open(instance_file, 'w') as f:
                json.dump(instance_data, f, indent=2)
            logger.debug(f"Updated instance_projects: {instance_id} -> {folder_name}")

        # Write TTY session if available (direct terminal context)
        if tty_key:
            tty_sessions_dir = marker_dir / 'tty_sessions'
            tty_sessions_dir.mkdir(parents=True, exist_ok=True)
            tty_session_file = tty_sessions_dir / f'{tty_key}.json'

            # Read existing TTY session, update project_path, write back
            tty_data = {}
            if tty_session_file.exists():
                try:
                    with open(tty_session_file, 'r') as f:
                        tty_data = json.load(f)
                except Exception:
                    pass

            # Update with new project path
            tty_data['project_path'] = project_path
            tty_data['tty_key'] = tty_key
            tty_data['instance_id'] = instance_id
            tty_data['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')

            with open(tty_session_file, 'w') as f:
                json.dump(tty_data, f, indent=2)
            logger.debug(f"Updated TTY session project_path: {folder_name}")

        active_work = {
            'project_path': project_path,
            'folder_name': folder_name,
            'claude_session_id': claude_session_id,
            'empirica_session_id': empirica_session_id,  # For Sentinel/MCP session attachment
            'source': 'project-switch',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'timestamp_epoch': time.time()
        }

        # Also write to session-specific file (if we know the session)
        # This prevents race conditions with other Claude instances
        if claude_session_id:
            session_marker_path = marker_dir / f'active_work_{claude_session_id}.json'
            with open(session_marker_path, 'w') as f:
                json.dump(active_work, f, indent=2)
            logger.debug(f"Updated session-specific active_work: {folder_name}")

        # Also write canonical file as fallback
        # Pre-compact hook reads this when session-specific doesn't exist
        marker_path = marker_dir / 'active_work.json'

        with open(marker_path, 'w') as f:
            json.dump(active_work, f, indent=2)

        logger.debug(f"Updated active_work.json: {folder_name} -> {project_path}")
        return True

    except Exception as e:
        logger.warning(f"Failed to update active_work.json: {e}")
        return False


def resolve_workspace_project(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Resolve a project by name, folder name, or UUID from workspace database.

    Args:
        identifier: Project name, folder name (repo directory name), or UUID

    Returns:
        Project dict or None if not found
    """
    projects = get_workspace_projects()

    # Try exact UUID match first
    for p in projects:
        if p.get('id') == identifier:
            return p

    # Try folder name match (most intuitive for users)
    identifier_lower = identifier.lower()
    for p in projects:
        if p.get('folder_name', '').lower() == identifier_lower:
            return p

    # Try project name match
    for p in projects:
        if p.get('name', '').lower() == identifier_lower:
            return p

    # Try partial folder name match
    for p in projects:
        folder = p.get('folder_name', '').lower()
        if folder and identifier_lower in folder:
            return p

    return None


def handle_project_create_command(args):
    """Handle project-create command"""
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.data.repositories.projects import ProjectRepository

        # Parse arguments
        name = args.name
        description = getattr(args, 'description', None)
        repos_str = getattr(args, 'repos', None)
        project_type = getattr(args, 'type', None)
        tags_str = getattr(args, 'tags', None)
        parent = getattr(args, 'parent', None)

        # Parse repos JSON if provided
        repos = None
        if repos_str:
            repos = json.loads(repos_str)

        # Parse tags (comma-separated or JSON array)
        tags = None
        if tags_str:
            if tags_str.startswith('['):
                tags = json.loads(tags_str)
            else:
                tags = [t.strip() for t in tags_str.split(',')]

        # Validate project_type
        if project_type and project_type not in ProjectRepository.PROJECT_TYPES:
            print(f"⚠️  Unknown type '{project_type}'. Valid types: {', '.join(ProjectRepository.PROJECT_TYPES)}")
            project_type = 'product'

        # Create project
        db = SessionDatabase()
        project_id = db.create_project(
            name=name,
            description=description,
            repos=repos,
            project_type=project_type,
            project_tags=tags,
            parent_project_id=parent
        )
        db.close()

        # Register in workspace.db for cross-project visibility (project-list, project-switch)
        try:
            from empirica.config.path_resolver import get_git_root
            from .workspace_init import _register_in_workspace_db

            # Determine trajectory_path: use git root if in repo, otherwise first repo path
            git_root = get_git_root()
            if git_root:
                trajectory_path = str(git_root)
            elif repos and len(repos) > 0:
                trajectory_path = repos[0]
            else:
                trajectory_path = None

            if trajectory_path:
                _register_in_workspace_db(
                    project_id=project_id,
                    name=name,
                    trajectory_path=trajectory_path,
                    description=description,
                    git_remote_url=None  # Could extract from git if needed
                )
                logger.debug(f"Registered project {name} in workspace.db")
        except Exception as e:
            logger.warning(f"Failed to register in workspace.db: {e}")
            # Non-fatal - project still created in local DB

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "project_id": project_id,
                "name": name,
                "project_type": project_type or 'product',
                "tags": tags or [],
                "repos": repos or [],
                "parent_project_id": parent,
                "message": "Project created successfully"
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Project created successfully")
            print(f"   Project ID: {project_id}")
            print(f"   Name: {name}")
            print(f"   Type: {project_type or 'product'}")
            if tags:
                print(f"   Tags: {', '.join(tags)}")
            if description:
                print(f"   Description: {description}")
            if repos:
                print(f"   Repos: {', '.join(repos)}")
            if parent:
                print(f"   Parent: {parent}")

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Project create", getattr(args, 'verbose', False))
        return None


def handle_project_handoff_command(args):
    """Handle project-handoff command"""
    try:
        from empirica.data.session_database import SessionDatabase

        # Parse arguments
        project_id = args.project_id
        project_summary = args.summary
        key_decisions_str = getattr(args, 'key_decisions', None)
        patterns_str = getattr(args, 'patterns', None)
        remaining_work_str = getattr(args, 'remaining_work', None)
        
        # Parse JSON arrays
        key_decisions = json.loads(key_decisions_str) if key_decisions_str else None
        patterns = json.loads(patterns_str) if patterns_str else None
        remaining_work = json.loads(remaining_work_str) if remaining_work_str else None

        # Create project handoff
        db = SessionDatabase()
        handoff_id = db.create_project_handoff(
            project_id=project_id,
            project_summary=project_summary,
            key_decisions=key_decisions,
            patterns_discovered=patterns,
            remaining_work=remaining_work
        )
        
        # Get aggregated learning deltas
        total_deltas = db.aggregate_project_learning_deltas(project_id)
        
        db.close()

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "handoff_id": handoff_id,
                "project_id": project_id,
                "total_learning_deltas": total_deltas,
                "message": "Project handoff created successfully"
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Project handoff created successfully")
            print(f"   Handoff ID: {handoff_id}")
            print(f"   Project: {project_id[:8]}...")
            print(f"\n📊 Total Learning Deltas:")
            for vector, delta in total_deltas.items():
                if delta != 0:
                    sign = "+" if delta > 0 else ""
                    print(f"      {vector}: {sign}{delta:.2f}")

        print(json.dumps({"handoff_id": handoff_id, "total_deltas": total_deltas}, indent=2))
        return 0

    except Exception as e:
        handle_cli_error(e, "Project handoff", getattr(args, 'verbose', False))
        return 1


def handle_project_list_command(args):
    """Handle project-list command - lists all projects from workspace database"""
    try:
        # Query workspace database for global projects
        projects = get_workspace_projects()

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "projects_count": len(projects),
                "projects": [
                    {
                        "id": p.get('id'),
                        "name": p.get('name'),
                        "folder_name": p.get('folder_name'),
                        "description": p.get('description'),
                        "status": p.get('status'),
                        "project_type": p.get('project_type'),
                        "total_findings": p.get('total_findings', 0),
                        "total_unknowns": p.get('total_unknowns', 0),
                        "total_goals": p.get('total_goals', 0),
                        "last_activity": p.get('updated_timestamp'),
                        "trajectory_path": p.get('trajectory_path')
                    }
                    for p in projects
                ]
            }
            print(json.dumps(result, indent=2))
        else:
            if not projects:
                print("📁 No projects found in workspace.")
                print("\nTip: Run 'empirica workspace-init' to scan and register projects.")
                return None

            print(f"📁 Found {len(projects)} project(s) in workspace:\n")
            for i, p in enumerate(projects, 1):
                name = p.get('name', 'Unknown')
                folder = p.get('folder_name', '')
                status = p.get('status', 'active')
                findings = p.get('total_findings', 0)
                unknowns = p.get('total_unknowns', 0)

                # Show folder name prominently (this is how users will switch)
                print(f"{i}. {folder} ({status})")
                if name != folder:
                    print(f"   Name: {name}")
                if p.get('description'):
                    desc = p['description'][:60] + '...' if len(p.get('description', '')) > 60 else p.get('description', '')
                    print(f"   {desc}")
                print(f"   📝 {findings} findings  ❓ {unknowns} unknowns")
                print()

            print("💡 Switch projects with: empirica project-switch <folder-name>")

        return None

    except Exception as e:
        handle_cli_error(e, "Project list", getattr(args, 'verbose', False))
        return None


def handle_project_bootstrap_command(args):
    """Handle project-bootstrap command - show epistemic breadcrumbs"""
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.config.project_config_loader import get_current_subject
        from empirica.cli.utils.project_resolver import resolve_project_id
        import subprocess

        output_format = getattr(args, 'output', 'human')
        project_id = getattr(args, 'project_id', None)

        def _error_output(error_msg: str, hint: str = None):
            """Output error in appropriate format"""
            if output_format == 'json':
                result = {'ok': False, 'error': error_msg}
                if hint:
                    result['hint'] = hint
                print(json.dumps(result))
            else:
                print(f"❌ Error: {error_msg}")
                if hint:
                    print(f"\nTip: {hint}")
            return None

        # Auto-detect project if not provided
        # Priority: 1) local .empirica/project.yaml, 2) git remote URL
        if not project_id:
            # Method 1: Read from local .empirica/project.yaml (highest priority)
            # This is what project-init creates - no git remote required
            # Use active context first, fall back to CWD
            try:
                import yaml
                import os
                from empirica.utils.session_resolver import get_active_project_path
                context_project = get_active_project_path()
                base_path = context_project if context_project else os.getcwd()
                project_yaml = os.path.join(base_path, '.empirica', 'project.yaml')
                if os.path.exists(project_yaml):
                    with open(project_yaml, 'r') as f:
                        project_config = yaml.safe_load(f)
                        if project_config and project_config.get('project_id'):
                            project_id = project_config['project_id']
            except Exception:
                pass  # Fall through to git remote method

            # Method 2: Match git remote URL (fallback for repos without project-init)
            if not project_id:
                try:
                    from empirica.cli.utils.project_resolver import (
                        get_current_git_repo, resolve_project_by_git_repo, normalize_git_url
                    )

                    git_repo = get_current_git_repo()
                    if git_repo:
                        db = SessionDatabase()
                        project_id = resolve_project_by_git_repo(git_repo, db)

                        if not project_id:
                            # Fallback: try substring match for legacy projects
                            result = subprocess.run(
                                ['git', 'remote', 'get-url', 'origin'],
                                capture_output=True, text=True, timeout=5
                            )
                            if result.returncode == 0:
                                git_url = result.stdout.strip()
                                cursor = db.adapter.conn.cursor()
                                cursor.execute("""
                                    SELECT id FROM projects WHERE repos LIKE ?
                                    ORDER BY last_activity_timestamp DESC LIMIT 1
                                """, (f'%{git_url}%',))
                                row = cursor.fetchone()
                                if row:
                                    project_id = row['id']

                        db.close()

                        if not project_id:
                            return _error_output(
                                f"No project found for git repo: {git_repo}",
                                "Create a project with: empirica project-create --name <name>"
                            )
                    else:
                        return _error_output(
                            "Not in a git repository or no remote 'origin' configured",
                            "Run 'git remote add origin <url>' or use --project-id"
                        )
                except Exception as e:
                    return _error_output(
                        f"Auto-detecting project failed: {e}",
                        "Use --project-id to specify project explicitly"
                    )
        else:
            # Resolve project name to UUID if needed
            db = SessionDatabase()
            project_id = resolve_project_id(project_id, db)
            db.close()
        
        check_integrity = False  # Disabled: naive parser has false positives. Use pattern matcher instead.
        context_to_inject = getattr(args, 'context_to_inject', False)
        task_description = getattr(args, 'task_description', None)
        
        # Parse epistemic_state from JSON string if provided
        epistemic_state = None
        epistemic_state_str = getattr(args, 'epistemic_state', None)
        if epistemic_state_str:
            try:
                epistemic_state = json.loads(epistemic_state_str)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in --epistemic-state: {e}")
                return None
        
        # Auto-detect subject from current directory
        subject = getattr(args, 'subject', None)
        if subject is None:
            subject = get_current_subject()  # Auto-detect from directory
        
        db = SessionDatabase()

        # Get new parameters
        session_id = getattr(args, 'session_id', None)
        include_live_state = getattr(args, 'include_live_state', False)
        # DEPRECATED: fresh_assess removed - use 'empirica assess-state' for canonical vector capture
        trigger = getattr(args, 'trigger', None)
        depth = getattr(args, 'depth', 'auto')
        ai_id = getattr(args, 'ai_id', None)  # Get AI ID for epistemic handoff

        # SessionStart Hook: Auto-load MCO config after memory compact
        mco_config = None
        if trigger == 'post_compact':
            from empirica.config.mco_loader import get_mco_config
            from pathlib import Path
            from empirica.utils.session_resolver import get_active_project_path

            # Find latest pre_summary snapshot - use active context, not CWD
            context_project = get_active_project_path()
            project_base = Path(context_project) if context_project else Path.cwd()
            ref_docs_dir = project_base / ".empirica" / "ref-docs"
            if ref_docs_dir.exists():
                snapshot_files = sorted(
                    ref_docs_dir.glob("pre_summary_*.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

                if snapshot_files:
                    latest_snapshot = snapshot_files[0]

                    # Try to load MCO config from snapshot
                    try:
                        with open(latest_snapshot) as f:
                            snapshot_data = json.load(f)
                            mco_snapshot = snapshot_data.get('mco_config')

                            if mco_snapshot:
                                # Format MCO config for output
                                mco_loader = get_mco_config()
                                mco_config = {
                                    'source': 'pre_summary_snapshot',
                                    'snapshot_path': str(latest_snapshot),
                                    'config': mco_snapshot,
                                    'formatted': mco_loader.format_for_prompt(mco_snapshot)
                                }
                            else:
                                # Fallback: Load fresh from files
                                mco_loader = get_mco_config()
                                mco_snapshot = mco_loader.export_snapshot(
                                    session_id=session_id or 'unknown',
                                    ai_id=ai_id,
                                    cascade_style='default'
                                )
                                mco_config = {
                                    'source': 'mco_files_fallback',
                                    'snapshot_path': None,
                                    'config': mco_snapshot,
                                    'formatted': mco_loader.format_for_prompt(mco_snapshot)
                                }
                    except Exception as e:
                        logger.warning(f"Could not load MCO from snapshot: {e}")
                        # Continue without MCO config

        breadcrumbs = db.bootstrap_project_breadcrumbs(
            project_id,
            check_integrity=check_integrity,
            context_to_inject=context_to_inject,
            task_description=task_description,
            epistemic_state=epistemic_state,
            subject=subject,
            session_id=session_id,
            include_live_state=include_live_state,
            # fresh_assess removed - use 'empirica assess-state' for canonical vector capture
            trigger=trigger,
            depth=depth,
            ai_id=ai_id  # Pass AI ID to bootstrap
        )

        # EIDETIC/EPISODIC MEMORY RETRIEVAL: Hot memories based on task context
        # This arms the AI with relevant facts and session narratives from Qdrant
        eidetic_memories = None
        episodic_memories = None
        if task_description and project_id:
            try:
                from empirica.core.qdrant.vector_store import search_eidetic, search_episodic, _check_qdrant_available
                if _check_qdrant_available():
                    eidetic_results = search_eidetic(project_id, task_description, limit=5, min_confidence=0.5)
                    if eidetic_results:
                        eidetic_memories = {
                            'query': task_description,
                            'facts': eidetic_results,
                            'count': len(eidetic_results)
                        }
                    episodic_results = search_episodic(project_id, task_description, limit=3, apply_recency_decay=True)
                    if episodic_results:
                        episodic_memories = {
                            'query': task_description,
                            'narratives': episodic_results,
                            'count': len(episodic_results)
                        }
                    logger.debug(f"Memory retrieval: {len(eidetic_results or [])} eidetic, {len(episodic_results or [])} episodic")
            except Exception as e:
                logger.debug(f"Memory retrieval failed (optional): {e}")

        # Add memories to breadcrumbs
        if eidetic_memories:
            breadcrumbs['eidetic_memories'] = eidetic_memories
        if episodic_memories:
            breadcrumbs['episodic_memories'] = episodic_memories

        # Optional: Detect memory gaps if session-id provided
        memory_gap_report = None
        session_id = getattr(args, 'session_id', None)

        if session_id:
            # Get current session vectors
            current_vectors = db.get_latest_vectors(session_id)

            if current_vectors:
                # Get memory gap policy from config or use default
                gap_policy = getattr(args, 'memory_gap_policy', None)
                if gap_policy:
                    policy = {'enforcement': gap_policy}
                else:
                    policy = {'enforcement': 'inform'}  # Default: just show gaps

                # Detect memory gaps
                detector = MemoryGapDetector(policy)
                session_context = {
                    'session_id': session_id,
                    'breadcrumbs_loaded': False,  # Will be updated if AI loads them
                    'finding_references': 0,  # TODO: Track actual references
                    'compaction_events': []  # TODO: Load from database
                }

                memory_gap_report = detector.detect_gaps(
                    current_vectors=current_vectors,
                    breadcrumbs=breadcrumbs,
                    session_context=session_context
                )

        # Add workflow suggestions based on session state
        workflow_suggestions = None
        if session_id:
            from empirica.cli.utils.workflow_suggestions import get_workflow_suggestions
            workflow_suggestions = get_workflow_suggestions(
                project_id=project_id,
                session_id=session_id,
                db=db
            )

        # Optional: Query global learnings for cross-project context
        global_learnings = None
        include_global = getattr(args, 'include_global', False)
        if include_global and task_description:
            try:
                from empirica.core.qdrant.vector_store import search_global
                global_results = search_global(task_description, limit=5)
                if global_results:
                    global_learnings = {
                        'query': task_description,
                        'results': global_results,
                        'count': len(global_results)
                    }
            except Exception as e:
                logger.debug(f"Global learnings query failed (non-fatal): {e}")

        # Re-install auto-capture hooks for resumed/existing sessions
        if session_id:
            try:
                from empirica.core.issue_capture import initialize_auto_capture, install_auto_capture_hooks, get_auto_capture
                existing = get_auto_capture()
                if not existing:
                    auto_capture = initialize_auto_capture(session_id, enable=True)
                    install_auto_capture_hooks(auto_capture)
                    logger.debug(f"Auto-capture hooks reinstalled for session {session_id[:8]}")
            except Exception as e:
                logger.debug(f"Auto-capture hook reinstall failed (non-fatal): {e}")

        # Load project skills from project_skills/*.yaml
        project_skills = None
        try:
            import yaml
            import os
            from empirica.utils.session_resolver import get_active_project_path
            context_project = get_active_project_path()
            base_path = context_project if context_project else os.getcwd()
            skills_dir = os.path.join(base_path, 'project_skills')
            if os.path.exists(skills_dir):
                skills_list = []
                for filename in os.listdir(skills_dir):
                    if filename.endswith(('.yaml', '.yml')):
                        filepath = os.path.join(skills_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                skill = yaml.safe_load(f)
                                if skill:
                                    skills_list.append(skill)
                        except Exception as skill_err:
                            logger.debug(f"Failed to load skill {filename}: {skill_err}")
                if skills_list:
                    project_skills = {
                        'count': len(skills_list),
                        'skills': skills_list
                    }
        except Exception as e:
            logger.debug(f"Project skills loading failed (non-fatal): {e}")

        db.close()

        if "error" in breadcrumbs:
            print(f"❌ {breadcrumbs['error']}")
            return None

        # Add memory gaps to breadcrumbs if detected
        if memory_gap_report and memory_gap_report.detected:
            breadcrumbs['memory_gaps'] = [
                {
                    'gap_id': gap.gap_id,
                    'type': gap.gap_type,
                    'content': gap.content,
                    'severity': gap.severity,
                    'gap_score': gap.gap_score,
                    'evidence': gap.evidence,
                    'resolution_action': gap.resolution_action
                }
                for gap in memory_gap_report.gaps
            ]
            breadcrumbs['memory_gap_analysis'] = {
                'detected': True,
                'overall_gap': memory_gap_report.overall_gap,
                'claimed_know': memory_gap_report.claimed_know,
                'expected_know': memory_gap_report.expected_know,
                'enforcement_mode': policy.get('enforcement', 'inform'),
                'recommended_actions': memory_gap_report.actions
            }

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "project_id": project_id,
                "breadcrumbs": breadcrumbs
            }
            if workflow_suggestions:
                result['workflow_automation'] = workflow_suggestions
            if mco_config:
                result['mco_config'] = mco_config
            if global_learnings:
                result['global_learnings'] = global_learnings
            if project_skills:
                result['project_skills'] = project_skills
            print(json.dumps(result, indent=2))
        else:
            # Print MCO config first if post-compact (SessionStart hook)
            if mco_config:
                print("\n" + "=" * 70)
                print("🔧 MCO Configuration Restored (SessionStart Hook)")
                print("=" * 70)
                if mco_config['source'] == 'pre_summary_snapshot':
                    print(f"   Source: {mco_config['snapshot_path']}")
                else:
                    print(f"   Source: Fresh load from MCO files (snapshot had no MCO)")
                print("=" * 70)
                print(mco_config['formatted'])
                print("\n" + "=" * 70)
                print("💡 Your configuration has been restored from pre-compact snapshot.")
                print("   Apply these bias corrections during CASCADE assessments.")
                print("=" * 70 + "\n")

            project = breadcrumbs['project']
            last = breadcrumbs['last_activity']

            # ===== PROJECT CONTEXT BANNER =====
            print("━" * 64)
            print("🎯 PROJECT CONTEXT")
            print("━" * 64)
            print()
            print(f"📁 Project: {project['name']}")
            print(f"🆔 ID: {project_id}")
            
            # Get git URL
            git_url = None
            try:
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    git_url = result.stdout.strip()
                    print(f"🔗 Repository: {git_url}")
            except:
                pass
            
            print(f"📍 Location: {db.db_path.parent.parent if hasattr(db, 'db_path') and db.db_path else 'Unknown'}")
            print(f"💾 Database: .empirica/sessions/sessions.db")
            print()
            print("⚠️  All commands write to THIS project's database.")
            print("   Findings, sessions, goals → stored in this project context.")
            print()
            print("━" * 64)
            print()
            
            # ===== PROJECT SUMMARY =====
            print(f"📋 Project Summary")
            print(f"   {project['description']}")
            if project['repos']:
                print(f"   Repos: {', '.join(project['repos'])}")
            print(f"   Total sessions: {project['total_sessions']}")
            print()
            
            print(f"🕐 Last Activity:")
            print(f"   {last['summary']}")
            print(f"   Next focus: {last['next_focus']}")
            print()
            
            # ===== AI EPISTEMIC HANDOFF =====
            if breadcrumbs.get('ai_epistemic_handoff'):
                handoff = breadcrumbs['ai_epistemic_handoff']
                print(f"🧠 Epistemic Handoff (from {handoff.get('ai_id', 'unknown')}):")
                vectors = handoff.get('vectors', {})
                deltas = handoff.get('deltas', {})
                
                if vectors:
                    print(f"   State (POSTFLIGHT):")
                    print(f"      Engagement: {vectors.get('engagement', 'N/A'):.2f}", end='')
                    if 'engagement' in deltas:
                        delta = deltas['engagement']
                        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
                        print(f" {arrow} {delta:+.2f}", end='')
                    print()
                    
                    if 'foundation' in vectors:
                        f = vectors['foundation']
                        d = deltas.get('foundation', {})
                        print(f"      Foundation: know={f.get('know', 'N/A'):.2f}", end='')
                        if 'know' in d:
                            print(f" {d['know']:+.2f}", end='')
                        print(f", do={f.get('do', 'N/A'):.2f}", end='')
                        if 'do' in d:
                            print(f" {d['do']:+.2f}", end='')
                        print(f", context={f.get('context', 'N/A'):.2f}", end='')
                        if 'context' in d:
                            print(f" {d['context']:+.2f}", end='')
                        print()
                    
                    print(f"      Uncertainty: {vectors.get('uncertainty', 'N/A'):.2f}", end='')
                    if 'uncertainty' in deltas:
                        delta = deltas['uncertainty']
                        arrow = "↓" if delta < 0 else "↑" if delta > 0 else "→"  # Lower is better
                        print(f" {arrow} {delta:+.2f}", end='')
                    print()
                
                if handoff.get('reasoning'):
                    print(f"   Learning: {handoff['reasoning'][:80]}...")
                print()

            # ===== FLOW STATE METRICS =====
            if breadcrumbs.get('flow_metrics'):
                flow = breadcrumbs['flow_metrics']
                current = flow.get('current_flow')

                if current:
                    print(f"⚡ Flow State (AI Productivity):")
                    print(f"   Current: {current['emoji']} {current['flow_state']} ({current['flow_score']}/100)")

                    # Show trend if available
                    trend = flow.get('trend', {})
                    if trend.get('emoji'):
                        print(f"   Trend: {trend['emoji']} {trend['description']}")

                    # Show average
                    avg = flow.get('average_flow', 0)
                    print(f"   Average (last 5): {avg}/100")

                    # Show blockers if any
                    blockers = flow.get('blockers', [])
                    if blockers:
                        print(f"   ⚠️  Blockers:")
                        for blocker in blockers[:3]:
                            print(f"      • {blocker}")

                    # Show flow triggers status
                    triggers = flow.get('triggers_present', {})
                    if triggers:
                        active_triggers = [name for name, present in triggers.items() if present]
                        if active_triggers:
                            print(f"   ✓ Active triggers: {', '.join(active_triggers)}")

                    print()

            # ===== HEALTH SCORE (EPISTEMIC QUALITY) =====
            if breadcrumbs.get('health_score'):
                health = breadcrumbs['health_score']
                current = health.get('current_health')

                if current:
                    print(f"💪 Health Score (Epistemic Quality):")
                    print(f"   Current: {current['health_score']}/100")

                    # Show trend if available
                    trend = health.get('trend', {})
                    if trend.get('emoji'):
                        print(f"   Trend: {trend['emoji']} {trend['description']}")

                    # Show average
                    avg = health.get('average_health', 0)
                    print(f"   Average (last 5): {avg}/100")

                    # Show component breakdown
                    components = health.get('components', {})
                    if components:
                        print(f"   Components:")
                        kq = components.get('knowledge_quality', {})
                        ep = components.get('epistemic_progress', {})
                        cap = components.get('capability', {})
                        conf = components.get('confidence', {})
                        eng = components.get('engagement', {})
                        
                        print(f"      Knowledge Quality: {kq.get('average', 0):.2f}")
                        print(f"      Epistemic Progress: {ep.get('average', 0):.2f}")
                        print(f"      Capability: {cap.get('average', 0):.2f}")
                        print(f"      Confidence: {conf.get('confidence_score', 0):.2f}")
                        print(f"      Engagement: {eng.get('engagement', 0):.2f}")
                    print()

            if breadcrumbs.get('findings'):
                print(f"📝 Recent Findings (last 10):")
                for i, f in enumerate(breadcrumbs['findings'][:10], 1):
                    print(f"   {i}. {f}")
                print()
            
            if breadcrumbs.get('unknowns'):
                unresolved = [u for u in breadcrumbs['unknowns'] if not u['is_resolved']]
                if unresolved:
                    print(f"❓ Unresolved Unknowns:")
                    for i, u in enumerate(unresolved[:5], 1):
                        print(f"   {i}. {u['unknown']}")
                    print()
            
            if breadcrumbs.get('dead_ends'):
                print(f"💀 Dead Ends (What Didn't Work):")
                for i, d in enumerate(breadcrumbs['dead_ends'][:5], 1):
                    print(f"   {i}. {d['approach']}")
                    print(f"      → Why: {d['why_failed']}")
                print()
            
            if breadcrumbs['mistakes_to_avoid']:
                print(f"⚠️  Recent Mistakes to Avoid:")
                for i, m in enumerate(breadcrumbs['mistakes_to_avoid'][:3], 1):
                    cost = m.get('cost_estimate', 'unknown')
                    cause = m.get('root_cause_vector', 'unknown')
                    print(f"   {i}. {m['mistake']} (cost: {cost}, cause: {cause})")
                    print(f"      → {m['prevention']}")
                print()
            
            if breadcrumbs.get('key_decisions'):
                print(f"💡 Key Decisions:")
                for i, d in enumerate(breadcrumbs['key_decisions'], 1):
                    print(f"   {i}. {d}")
                print()
            
            if breadcrumbs.get('reference_docs'):
                print(f"📄 Reference Docs:")
                for i, doc in enumerate(breadcrumbs['reference_docs'][:5], 1):
                    path = doc.get('doc_path', 'unknown')
                    doc_type = doc.get('doc_type', 'unknown')
                    print(f"   {i}. {path} ({doc_type})")
                    if doc.get('description'):
                        print(f"      {doc['description']}")
                print()
            
            if breadcrumbs.get('recent_artifacts'):
                print(f"📝 Recently Modified Files (last 10 sessions):")
                for i, artifact in enumerate(breadcrumbs['recent_artifacts'][:10], 1):
                    print(f"   {i}. Session {artifact['session_id']} ({artifact['ai_id']})")
                    print(f"      Task: {artifact['task_summary']}")
                    print(f"      Files modified ({len(artifact['files_modified'])}):")
                    for file in artifact['files_modified'][:5]:  # Show first 5 files
                        print(f"        • {file}")
                    if len(artifact['files_modified']) > 5:
                        print(f"        ... and {len(artifact['files_modified']) - 5} more")
                print()
            
            # ===== NEW: Active Work Section =====
            if breadcrumbs.get('active_sessions') or breadcrumbs.get('active_goals'):
                print(f"🚀 Active Work (In Progress):")
                print()
                
                # Show active sessions
                if breadcrumbs.get('active_sessions'):
                    print(f"   📡 Active Sessions:")
                    for sess in breadcrumbs['active_sessions'][:3]:
                        from datetime import datetime
                        start = datetime.fromisoformat(str(sess['start_time']))
                        elapsed = datetime.now() - start
                        hours = int(elapsed.total_seconds() / 3600)
                        print(f"      • {sess['session_id'][:8]}... ({sess['ai_id']}) - {hours}h ago")
                        if sess.get('subject'):
                            print(f"        Subject: {sess['subject']}")
                    print()
                
                # Show active goals
                if breadcrumbs.get('active_goals'):
                    print(f"   🎯 Goals In Progress:")
                    for goal in breadcrumbs['active_goals'][:5]:
                        beads_link = f" [BEADS: {goal['beads_issue_id']}]" if goal.get('beads_issue_id') else " ⚠️ No BEADS link"
                        print(f"      • [{goal['id'][:8]}] {goal['objective']}{beads_link}")
                        print(f"        AI: {goal['ai_id']} | Subtasks: {goal['subtask_count']}")
                        
                        # Show recent findings for this goal
                        goal_findings = [f for f in breadcrumbs.get('findings_with_goals', []) if f['goal_id'] == goal['id']]
                        if goal_findings:
                            print(f"        Latest: {goal_findings[0]['finding'][:60]}...")
                    print()
                
                # Show epistemic artifacts
                if breadcrumbs.get('epistemic_artifacts'):
                    print(f"   📊 Epistemic Artifacts:")
                    for artifact in breadcrumbs['epistemic_artifacts'][:3]:
                        size_kb = artifact['size'] / 1024
                        print(f"      • {artifact['path']} ({size_kb:.1f} KB)")
                    print()
                
                # Show AI activity summary
                if breadcrumbs.get('ai_activity'):
                    print(f"   👥 AI Activity (Last 7 Days):")
                    for ai in breadcrumbs['ai_activity'][:5]:
                        print(f"      • {ai['ai_id']}: {ai['session_count']} session(s)")
                    print()
                    print(f"   💡 Tip: Use format '<model>-<workstream>' (e.g., claude-cli-testing)")
                    print()
            
            # ===== END NEW =====
            
            # ===== FLOW STATE METRICS =====
            if breadcrumbs.get('flow_metrics') is not None:
                print(f"📊 Flow State Analysis (Recent Sessions):")
                print()
                
                flow_metrics = breadcrumbs['flow_metrics']
                flow_data = flow_metrics.get('flow_scores', [])
                if flow_data:
                    for i, session in enumerate(flow_data[:5], 1):
                        score = session['flow_score']
                        # Choose emoji based on score
                        if score >= 0.9:
                            emoji = "⭐"
                        elif score >= 0.7:
                            emoji = "🟢"
                        elif score >= 0.5:
                            emoji = "🟡"
                        else:
                            emoji = "🔴"
                        
                        print(f"   {i}. {session['session_id']} ({session['ai_id']})")
                        print(f"      Flow Score: {score:.2f} {emoji}")
                        
                        # Show top 3 components
                        components = session['components']
                        top_3 = sorted(components.items(), key=lambda x: x[1], reverse=True)[:3]
                        print(f"      Top factors: {', '.join([f'{k}={v:.2f}' for k, v in top_3])}")
                        
                        # Show recommendations if any
                        if session['recommendations']:
                            print(f"      💡 {session['recommendations'][0]}")
                        print()
                    
                    # Show what creates flow
                    print(f"   💡 Flow Triggers (Optimize for these):")
                    print(f"      ✅ CASCADE complete (PREFLIGHT → POSTFLIGHT)")
                    print(f"      ✅ Bootstrap loaded early")
                    print(f"      ✅ Goal with subtasks")
                    print(f"      ✅ CHECK for high-scope work")
                    print(f"      ✅ AI naming convention (<model>-<workstream>)")
                    print()
                else:
                    print(f"   💡 No completed sessions yet")
                    print(f"   Tip: Close active sessions with POSTFLIGHT to see flow metrics")
                    print(f"   Flow score will show patterns from completed work")
                    print()
            
            # ===== DATABASE SCHEMA SUMMARY =====
            if breadcrumbs.get('database_summary'):
                print(f"🗄️  Database Schema (Epistemic Data Store):")
                print()
                
                db_summary = breadcrumbs['database_summary']
                print(f"   Total Tables: {db_summary.get('total_tables', 0)}")
                print(f"   Tables With Data: {db_summary.get('tables_with_data', 0)}")
                print()
                
                # Show key tables (static knowledge reminder)
                if db_summary.get('key_tables'):
                    print(f"   📌 Key Tables:")
                    for table, description in list(db_summary['key_tables'].items())[:6]:
                        print(f"      • {table}: {description}")
                    print()
                
                # Show top tables by row count
                if db_summary.get('top_tables'):
                    print(f"   📊 Most Active Tables:")
                    for table_info in db_summary['top_tables'][:5]:
                        print(f"      • {table_info}")
                    print()
                
                # Reference to full schema
                if db_summary.get('schema_doc'):
                    print(f"   📖 Full Schema: {db_summary['schema_doc']}")
                    print()
            
            # ===== STRUCTURE HEALTH =====
            if breadcrumbs.get('structure_health'):
                print(f"🏗️  Project Structure Health:")
                print()
                
                health = breadcrumbs['structure_health']
                
                # Show detected pattern with confidence
                confidence = health.get('confidence', 0.0)
                conformance = health.get('conformance', 0.0)
                
                # Choose emoji based on conformance
                if conformance >= 0.9:
                    emoji = "✅"
                elif conformance >= 0.7:
                    emoji = "🟢"
                elif conformance >= 0.5:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                print(f"   Detected Pattern: {health.get('detected_name', 'Unknown')} {emoji}")
                print(f"   Detection Confidence: {confidence:.2f}")
                print(f"   Pattern Conformance: {conformance:.2f}")
                print(f"   Description: {health.get('description', '')}")
                print()
                
                # Show violations if any
                violations = health.get('violations', [])
                if violations:
                    print(f"   ⚠️  Conformance Issues ({len(violations)}):")
                    for violation in violations[:3]:
                        print(f"      • {violation}")
                    if len(violations) > 3:
                        print(f"      ... and {len(violations) - 3} more")
                    print()
                
                # Show suggestions
                suggestions = health.get('suggestions', [])
                if suggestions:
                    print(f"   💡 Suggestions:")
                    for suggestion in suggestions[:3]:
                        print(f"      {suggestion}")
                    print()
            
            # ===== FILE TREE =====
            if breadcrumbs.get('file_tree'):
                print(f"📁 Project Structure (depth 3, respects .gitignore):")
                print()
                # Indent the tree output slightly
                tree_lines = breadcrumbs['file_tree'].split('\n')
                for line in tree_lines[:50]:  # Limit to 50 lines
                    if line.strip():
                        print(f"   {line}")
                if len(tree_lines) > 50:
                    print(f"   ... ({len(tree_lines) - 50} more lines)")
                print()
            
            if breadcrumbs['incomplete_work']:
                print(f"🎯 Incomplete Work:")
                for i, w in enumerate(breadcrumbs['incomplete_work'], 1):
                    objective = w.get('objective', w.get('goal', 'Unknown'))
                    status = w.get('status', 'unknown')
                    print(f"   {i}. {objective} ({status})")
                print()

            if breadcrumbs.get('available_skills'):
                print(f"🛠️  Available Skills:")
                for i, skill in enumerate(breadcrumbs['available_skills'], 1):
                    tags = ', '.join(skill.get('tags', [])) if skill.get('tags') else 'no tags'
                    print(f"   {i}. {skill['title']} ({skill['id']})")
                    print(f"      Tags: {tags}")
                print()

            if breadcrumbs.get('semantic_docs'):
                print(f"📖 Core Documentation:")
                for i, doc in enumerate(breadcrumbs['semantic_docs'][:3], 1):
                    print(f"   {i}. {doc['title']}")
                    print(f"      Path: {doc['path']}")
                print()
            
            if breadcrumbs.get('integrity_analysis'):
                print(f"🔍 Doc-Code Integrity Analysis:")
                integrity = breadcrumbs['integrity_analysis']
                
                if 'error' in integrity:
                    print(f"   ⚠️  Analysis failed: {integrity['error']}")
                else:
                    cli = integrity['cli_commands']
                    print(f"   Score: {cli['integrity_score']:.1%} ({cli['total_in_code']} code, {cli['total_in_docs']} docs)")
                    
                    if integrity.get('missing_code'):
                        print(f"\n   🔴 Missing Implementations ({cli['missing_implementations']} total):")
                        for item in integrity['missing_code'][:5]:
                            print(f"      • empirica {item['command']} (severity: {item['severity']})")
                            if item['mentioned_in']:
                                print(f"        Mentioned in: {item['mentioned_in'][0]['file']}")
                    
                    if integrity.get('missing_docs'):
                        print(f"\n   📝 Missing Documentation ({cli['missing_documentation']} total):")
                        for item in integrity['missing_docs'][:5]:
                            print(f"      • empirica {item['command']}")
                print()

            # Workflow Automation Suggestions (if session-id provided)
            if workflow_suggestions:
                from empirica.cli.utils.workflow_suggestions import format_workflow_suggestions
                workflow_output = format_workflow_suggestions(workflow_suggestions)
                if workflow_output.strip():
                    print(workflow_output)

            # Memory Gap Analysis (if session-id provided)
            if breadcrumbs.get('memory_gap_analysis'):
                analysis = breadcrumbs['memory_gap_analysis']
                enforcement = analysis.get('enforcement_mode', 'inform')

                # Select emoji based on enforcement mode
                mode_emoji = {
                    'inform': '🧠',
                    'warn': '⚠️',
                    'strict': '🔴',
                    'block': '🛑'
                }.get(enforcement, '🧠')

                print(f"{mode_emoji} Memory Gap Analysis (Mode: {enforcement.upper()}):")

                if analysis['detected']:
                    gap_score = analysis['overall_gap']
                    claimed = analysis['claimed_know']
                    expected = analysis['expected_know']

                    print(f"   Knowledge Assessment:")
                    print(f"      Claimed KNOW:  {claimed:.2f}")
                    print(f"      Expected KNOW: {expected:.2f}")
                    print(f"      Gap Score:     {gap_score:.2f}")

                    # Group gaps by type
                    gaps_by_type = {}
                    for gap in breadcrumbs.get('memory_gaps', []):
                        gap_type = gap['type']
                        if gap_type not in gaps_by_type:
                            gaps_by_type[gap_type] = []
                        gaps_by_type[gap_type].append(gap)

                    # Display gaps by severity
                    if gaps_by_type:
                        print(f"\n   Detected Gaps:")

                        # Priority order
                        type_order = ['confabulation', 'unreferenced_findings', 'unincorporated_unknowns',
                                     'file_unawareness', 'compaction']

                        for gap_type in type_order:
                            if gap_type not in gaps_by_type:
                                continue

                            gaps = gaps_by_type[gap_type]
                            severity_icon = {
                                'critical': '🔴',
                                'high': '🟠',
                                'medium': '🟡',
                                'low': '🔵'
                            }

                            # Show type header
                            type_label = gap_type.replace('_', ' ').title()
                            print(f"\n      {type_label} ({len(gaps)}):")

                            # Show top 3 gaps of this type
                            for gap in gaps[:3]:
                                icon = severity_icon.get(gap['severity'], '•')
                                content = gap['content'][:80] + '...' if len(gap['content']) > 80 else gap['content']
                                print(f"      {icon} {content}")
                                if gap.get('resolution_action'):
                                    print(f"         → {gap['resolution_action']}")

                            if len(gaps) > 3:
                                print(f"         ... and {len(gaps) - 3} more")

                    # Show recommended actions
                    if analysis.get('recommended_actions'):
                        print(f"\n   Recommended Actions:")
                        for i, action in enumerate(analysis['recommended_actions'][:5], 1):
                            print(f"      {i}. {action}")
                else:
                    print(f"   ✅ No memory gaps detected - context is current")

                print()

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Project bootstrap", getattr(args, 'verbose', False))
        return None


def handle_finding_log_command(args):
    """Handle finding-log command - AI-first with config file support"""
    try:
        import os
        import sys
        from empirica.data.session_database import SessionDatabase
        from empirica.cli.utils.project_resolver import resolve_project_id
        from empirica.cli.cli_utils import parse_json_safely

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
            project_id = config_data.get('project_id')
            session_id = config_data.get('session_id')  # Optional - auto-derives from transaction
            finding = config_data.get('finding')
            goal_id = config_data.get('goal_id')
            subtask_id = config_data.get('subtask_id')
            impact = config_data.get('impact')  # Optional - auto-derives if None
            output_format = 'json'
        else:
            # LEGACY MODE
            session_id = args.session_id
            finding = args.finding
            project_id = args.project_id
            goal_id = getattr(args, 'goal_id', None)
            subtask_id = getattr(args, 'subtask_id', None)
            impact = getattr(args, 'impact', None)  # Optional - auto-derives if None
            output_format = getattr(args, 'output', 'json')

        # UNIFIED: Auto-derive session_id if not provided (works for both modes)
        if not session_id:
            from empirica.utils.session_resolver import get_active_empirica_session_id
            session_id = get_active_empirica_session_id()

        # Validate required fields
        if not session_id or not finding:
            print(json.dumps({
                "ok": False,
                "error": "No active transaction and --session-id not provided",
                "hint": "Either run PREFLIGHT first, or provide --session-id explicitly"
            }))
            sys.exit(1)

        # Auto-detect subject from current directory
        from empirica.config.project_config_loader import get_current_subject
        subject = config_data.get('subject') if config_data else getattr(args, 'subject', None)
        if subject is None:
            subject = get_current_subject()  # Auto-detect from directory
        
        # Show project context (quiet mode - single line)
        if output_format != 'json':
            from empirica.cli.cli_utils import print_project_context
            print_project_context(quiet=True)
        
        db = SessionDatabase()

        # Auto-resolve project_id if not provided
        if not project_id:
            # Try to get project from session record
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT project_id FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row and row['project_id']:
                project_id = row['project_id']
                logger.info(f"Auto-resolved project_id from session: {project_id[:8]}...")
            else:
                # Fallback: try to resolve from unified context (NOT CWD)
                try:
                    from empirica.utils.session_resolver import get_active_context
                    context = get_active_context()
                    project_path = context.get('project_path')
                    if project_path:
                        import yaml
                        from pathlib import Path
                        project_yaml = Path(project_path) / '.empirica' / 'project.yaml'
                        if project_yaml.exists():
                            with open(project_yaml) as f:
                                project_config = yaml.safe_load(f)
                                project_id = project_config.get('project_id')
                                if project_id:
                                    logger.info(f"Auto-resolved project_id from context: {project_id[:8]}...")
                except Exception:
                    pass

        # Resolve project name to UUID if still not resolved
        if project_id:
            project_id = resolve_project_id(project_id, db)
        else:
            # Last resort: create a generic project ID based on session if no project context available
            import hashlib
            project_id = hashlib.md5(f"session-{session_id}".encode()).hexdigest()
            logger.warning(f"Using fallback project_id derived from session: {project_id[:8]}...")

        # At this point, project_id should be resolved
        
        # SESSION-BASED AUTO-LINKING: If goal_id not provided, check for active goal in session
        if not goal_id:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT id FROM goals 
                WHERE session_id = ? AND is_completed = 0 
                ORDER BY created_timestamp DESC 
                LIMIT 1
            """, (session_id,))
            active_goal = cursor.fetchone()
            if active_goal:
                goal_id = active_goal['id']
                # Note: subtask_id remains None unless explicitly provided

        # Auto-derive active transaction_id
        transaction_id = None
        try:
            from empirica.utils.session_resolver import read_active_transaction
            transaction_id = read_active_transaction()
        except Exception:
            pass

        # PROJECT-SCOPED: All findings are project-scoped (session_id preserved for provenance)
        finding_id = db.log_finding(
            project_id=project_id,
            session_id=session_id,
            finding=finding,
            goal_id=goal_id,
            subtask_id=subtask_id,
            subject=subject,
            impact=impact,
            transaction_id=transaction_id
        )

        # Get ai_id from session for git notes
        ai_id = 'claude-code'  # Default
        try:
            cursor = db.conn.cursor()
            cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row['ai_id']:
                ai_id = row['ai_id']
        except:
            pass

        db.close()

        # GIT NOTES: Store finding in git notes for sync (canonical source)
        git_stored = False
        try:
            from empirica.core.canonical.empirica_git.finding_store import GitFindingStore
            git_store = GitFindingStore()

            git_stored = git_store.store_finding(
                finding_id=finding_id,
                project_id=project_id,
                session_id=session_id,
                ai_id=ai_id,
                finding=finding,
                impact=impact,
                goal_id=goal_id,
                subtask_id=subtask_id,
                subject=subject
            )
            if git_stored:
                logger.info(f"✓ Finding {finding_id[:8]} stored in git notes")
        except Exception as git_err:
            # Non-fatal - log but continue
            logger.warning(f"Git notes storage failed: {git_err}")

        # AUTO-EMBED: Add finding to Qdrant for semantic search
        embedded = False
        if project_id and finding_id:
            try:
                from empirica.core.qdrant.vector_store import embed_single_memory_item
                from datetime import datetime
                embedded = embed_single_memory_item(
                    project_id=project_id,
                    item_id=finding_id,
                    text=finding,
                    item_type='finding',
                    session_id=session_id,
                    goal_id=goal_id,
                    subtask_id=subtask_id,
                    subject=subject,
                    impact=impact,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as embed_err:
                # Non-fatal - log but continue
                logger.warning(f"Auto-embed failed: {embed_err}")

        # EIDETIC MEMORY: Extract fact and add to eidetic layer for confidence tracking
        eidetic_result = None
        if project_id and finding_id:
            try:
                from empirica.core.qdrant.vector_store import (
                    embed_eidetic,
                    confirm_eidetic_fact,
                )
                import hashlib

                # Content hash for deduplication
                content_hash = hashlib.md5(finding.encode()).hexdigest()

                # Try to confirm existing fact first
                confirmed = confirm_eidetic_fact(project_id, content_hash, session_id)
                if confirmed:
                    eidetic_result = "confirmed"
                    logger.debug(f"Confirmed existing eidetic fact: {content_hash[:8]}")
                else:
                    # Create new eidetic entry
                    eidetic_created = embed_eidetic(
                        project_id=project_id,
                        fact_id=finding_id,
                        content=finding,
                        fact_type="fact",
                        domain=subject,  # Use subject as domain hint
                        confidence=0.5 + ((impact or 0.5) * 0.2),  # Higher impact → higher initial confidence
                        confirmation_count=1,
                        source_sessions=[session_id] if session_id else [],
                        source_findings=[finding_id],
                        tags=[subject] if subject else [],
                    )
                    if eidetic_created:
                        eidetic_result = "created"
                        logger.debug(f"Created new eidetic fact: {finding_id}")
            except Exception as eidetic_err:
                # Non-fatal - log but continue
                logger.warning(f"Eidetic ingestion failed: {eidetic_err}")

        # IMMUNE SYSTEM: Decay related lessons when findings are logged
        # This implements the pattern where new learnings naturally supersede old lessons
        # CENTRAL TOLERANCE: Scope decay to finding's domain to prevent autoimmune attacks
        decayed_lessons = []
        try:
            from empirica.core.lessons.storage import LessonStorageManager
            lesson_storage = LessonStorageManager()
            decayed_lessons = lesson_storage.decay_related_lessons(
                finding_text=finding,
                domain=subject,  # Central tolerance: only decay lessons in same domain
                decay_amount=0.05,  # 5% decay per related finding
                min_confidence=0.3,  # Floor at 30%
                keywords_threshold=2  # Require at least 2 keyword matches
            )
            if decayed_lessons:
                logger.info(f"IMMUNE: Decayed {len(decayed_lessons)} related lessons in domain '{subject}'")

                # Cross-layer sync: propagate YAML lesson decay to Qdrant payloads
                try:
                    from empirica.core.qdrant.vector_store import propagate_lesson_confidence_to_qdrant
                    if project_id:
                        for dl in decayed_lessons:
                            propagate_lesson_confidence_to_qdrant(
                                project_id,
                                dl.get('name', ''),
                                dl.get('new_confidence', 0.3)
                            )
                except Exception as qdrant_sync_err:
                    logger.debug(f"Lesson→Qdrant sync skipped: {qdrant_sync_err}")
        except Exception as decay_err:
            # Non-fatal - log but continue
            logger.debug(f"Lesson decay check failed: {decay_err}")

        # Cross-layer: decay eidetic facts that contradict this finding
        # Only when a domain/subject is provided — domainless findings spray too broadly
        eidetic_decayed = 0
        try:
            from empirica.core.qdrant.vector_store import decay_eidetic_by_finding
            if project_id and subject:
                eidetic_decayed = decay_eidetic_by_finding(
                    project_id,
                    finding,
                    domain=subject,
                )
                if eidetic_decayed:
                    logger.info(f"IMMUNE: Decayed {eidetic_decayed} eidetic facts by finding in domain '{subject}'")
        except Exception as eidetic_err:
            logger.debug(f"Eidetic decay skipped: {eidetic_err}")

        result = {
            "ok": True,
            "finding_id": finding_id,
            "project_id": project_id if project_id else None,
            "session_id": session_id,
            "git_stored": git_stored,  # Git notes for sync
            "embedded": embedded,
            "eidetic": eidetic_result,  # "created" | "confirmed" | None
            "immune_decay": decayed_lessons if decayed_lessons else None,  # Lessons affected by this finding
            "eidetic_decayed": eidetic_decayed if eidetic_decayed else None,
            "message": "Finding logged to project scope"
        }

        # Format output (AI-first = JSON by default)
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output (legacy)
            print(f"✅ Finding logged successfully")
            print(f"   Finding ID: {finding_id}")
            if project_id:
                print(f"   Project: {project_id[:8]}...")
            if git_stored:
                print(f"   📝 Stored in git notes for sync")
            if embedded:
                print(f"   🔍 Auto-embedded for semantic search")
            if decayed_lessons:
                print(f"   🛡️ IMMUNE: Decayed {len(decayed_lessons)} related lesson(s)")
                for dl in decayed_lessons:
                    print(f"      - {dl['name']}: {dl['previous_confidence']:.2f} → {dl['new_confidence']:.2f}")

        return 0  # Success

    except Exception as e:
        handle_cli_error(e, "Finding log", getattr(args, 'verbose', False))
        return None


def handle_unknown_log_command(args):
    """Handle unknown-log command - AI-first with config file support"""
    try:
        import os
        import sys
        from empirica.data.session_database import SessionDatabase
        from empirica.cli.utils.project_resolver import resolve_project_id
        from empirica.cli.cli_utils import parse_json_safely

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
            project_id = config_data.get('project_id')
            session_id = config_data.get('session_id')
            unknown = config_data.get('unknown')
            goal_id = config_data.get('goal_id')
            subtask_id = config_data.get('subtask_id')
            impact = config_data.get('impact')  # Optional - auto-derives if None
            output_format = 'json'
        else:
            session_id = args.session_id
            unknown = args.unknown
            project_id = args.project_id
            goal_id = getattr(args, 'goal_id', None)
            subtask_id = getattr(args, 'subtask_id', None)
            impact = getattr(args, 'impact', None)  # Optional - auto-derives if None
            output_format = getattr(args, 'output', 'json')

        # UNIFIED: Auto-derive session_id if not provided (works for both modes)
        if not session_id:
            from empirica.utils.session_resolver import get_active_empirica_session_id
            session_id = get_active_empirica_session_id()

        # Validate required fields
        if not session_id or not unknown:
            print(json.dumps({
                "ok": False,
                "error": "No active transaction and --session-id not provided",
                "hint": "Either run PREFLIGHT first, or provide --session-id explicitly"
            }))
            sys.exit(1)

        # Auto-detect subject from current directory
        from empirica.config.project_config_loader import get_current_subject
        subject = config_data.get('subject') if config_data else getattr(args, 'subject', None)
        if subject is None:
            subject = get_current_subject()  # Auto-detect from directory
        
        # Show project context (quiet mode - single line)
        if output_format != 'json':
            from empirica.cli.cli_utils import print_project_context
            print_project_context(quiet=True)
        
        db = SessionDatabase()

        # Auto-resolve project_id if not provided
        if not project_id:
            # Try to get project from session record
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT project_id FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row and row['project_id']:
                project_id = row['project_id']
                logger.info(f"Auto-resolved project_id from session: {project_id[:8]}...")
            else:
                # Fallback: try to resolve from unified context (NOT CWD)
                try:
                    from empirica.utils.session_resolver import get_active_context
                    context = get_active_context()
                    project_path = context.get('project_path')
                    if project_path:
                        import yaml
                        from pathlib import Path
                        project_yaml = Path(project_path) / '.empirica' / 'project.yaml'
                        if project_yaml.exists():
                            with open(project_yaml) as f:
                                project_config = yaml.safe_load(f)
                                project_id = project_config.get('project_id')
                                if project_id:
                                    logger.info(f"Auto-resolved project_id from context: {project_id[:8]}...")
                except Exception:
                    pass

        # Resolve project name to UUID if still not resolved
        if project_id:
            project_id = resolve_project_id(project_id, db)
        else:
            # Last resort: create a generic project ID based on session if no project context available
            import hashlib
            project_id = hashlib.md5(f"session-{session_id}".encode()).hexdigest()
            logger.warning(f"Using fallback project_id derived from session: {project_id[:8]}...")

        # At this point, project_id should be resolved
        
        # SESSION-BASED AUTO-LINKING: If goal_id not provided, check for active goal in session
        if not goal_id:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT id FROM goals 
                WHERE session_id = ? AND is_completed = 0 
                ORDER BY created_timestamp DESC 
                LIMIT 1
            """, (session_id,))
            active_goal = cursor.fetchone()
            if active_goal:
                goal_id = active_goal['id']

        # Auto-derive active transaction_id
        transaction_id = None
        try:
            from empirica.utils.session_resolver import read_active_transaction
            transaction_id = read_active_transaction()
        except Exception:
            pass

        # PROJECT-SCOPED: All unknowns are project-scoped (session_id preserved for provenance)
        unknown_id = db.log_unknown(
            project_id=project_id,
            session_id=session_id,
            unknown=unknown,
            goal_id=goal_id,
            subtask_id=subtask_id,
            subject=subject,
            impact=impact,
            transaction_id=transaction_id
        )

        # Get ai_id from session for git notes
        ai_id = 'claude-code'  # Default
        try:
            cursor = db.conn.cursor()
            cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row['ai_id']:
                ai_id = row['ai_id']
        except:
            pass

        db.close()

        # GIT NOTES: Store unknown in git notes for sync (canonical source)
        git_stored = False
        try:
            from empirica.core.canonical.empirica_git.unknown_store import GitUnknownStore
            git_store = GitUnknownStore()

            git_stored = git_store.store_unknown(
                unknown_id=unknown_id,
                project_id=project_id,
                session_id=session_id,
                ai_id=ai_id,
                unknown=unknown,
                goal_id=goal_id,
                subtask_id=subtask_id
            )
            if git_stored:
                logger.info(f"✓ Unknown {unknown_id[:8]} stored in git notes")
        except Exception as git_err:
            # Non-fatal - log but continue
            logger.warning(f"Git notes storage failed: {git_err}")

        # AUTO-EMBED: Add unknown to Qdrant for semantic search
        embedded = False
        if project_id and unknown_id:
            try:
                from empirica.core.qdrant.vector_store import embed_single_memory_item
                from datetime import datetime
                embedded = embed_single_memory_item(
                    project_id=project_id,
                    item_id=unknown_id,
                    text=unknown,
                    item_type='unknown',
                    session_id=session_id,
                    goal_id=goal_id,
                    subtask_id=subtask_id,
                    subject=subject,
                    impact=impact,
                    is_resolved=False,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as embed_err:
                # Non-fatal - log but continue
                logger.warning(f"Auto-embed failed: {embed_err}")

        result = {
            "ok": True,
            "unknown_id": unknown_id,
            "project_id": project_id if project_id else None,
            "session_id": session_id,
            "git_stored": git_stored,  # Git notes for sync
            "embedded": embedded,
            "message": "Unknown logged to project scope"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Unknown logged successfully")
            print(f"   Unknown ID: {unknown_id}")
            if project_id:
                print(f"   Project: {project_id[:8]}...")
            if git_stored:
                print(f"   📝 Stored in git notes for sync")
            if embedded:
                print(f"   🔍 Auto-embedded for semantic search")

        return 0  # Success

    except Exception as e:
        handle_cli_error(e, "Unknown log", getattr(args, 'verbose', False))
        return None


def handle_unknown_resolve_command(args):
    """Handle unknown-resolve command"""
    try:
        from empirica.data.session_database import SessionDatabase

        unknown_id = getattr(args, 'unknown_id', None)
        resolved_by = getattr(args, 'resolved_by', None)
        output_format = getattr(args, 'output', 'json')

        if not unknown_id or not resolved_by:
            result = {
                "ok": False,
                "error": "unknown_id and resolved_by are required"
            }
            print(json.dumps(result))
            return 1

        # Resolve the unknown
        db = SessionDatabase()
        db.resolve_unknown(unknown_id=unknown_id, resolved_by=resolved_by)
        db.close()

        # Format output
        result = {
            "ok": True,
            "unknown_id": unknown_id,
            "resolved_by": resolved_by,
            "message": "Unknown resolved successfully"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Unknown resolved successfully")
            print(f"   Unknown ID: {unknown_id[:8]}...")
            print(f"   Resolved by: {resolved_by}")

        return 0

    except Exception as e:
        handle_cli_error(e, "Unknown resolve", getattr(args, 'verbose', False))
        return 1


def handle_deadend_log_command(args):
    """Handle deadend-log command - AI-first with config file support"""
    try:
        import os
        import sys
        from empirica.data.session_database import SessionDatabase
        from empirica.cli.utils.project_resolver import resolve_project_id
        from empirica.cli.cli_utils import parse_json_safely

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
            project_id = config_data.get('project_id')
            session_id = config_data.get('session_id')  # Optional - auto-derives from transaction
            approach = config_data.get('approach')
            why_failed = config_data.get('why_failed')
            goal_id = config_data.get('goal_id')
            subtask_id = config_data.get('subtask_id')
            impact = config_data.get('impact')  # Optional - auto-derives if None
            output_format = 'json'
        else:
            session_id = args.session_id
            approach = args.approach
            why_failed = args.why_failed
            project_id = args.project_id
            goal_id = getattr(args, 'goal_id', None)
            subtask_id = getattr(args, 'subtask_id', None)
            impact = getattr(args, 'impact', None)  # Optional - auto-derives if None
            output_format = getattr(args, 'output', 'json')

        # UNIFIED: Auto-derive session_id if not provided (works for both modes)
        if not session_id:
            from empirica.utils.session_resolver import get_active_empirica_session_id
            session_id = get_active_empirica_session_id()

        # Validate required fields
        if not session_id or not approach or not why_failed:
            print(json.dumps({
                "ok": False,
                "error": "No active transaction and --session-id not provided",
                "hint": "Either run PREFLIGHT first, or provide --session-id explicitly"
            }))
            sys.exit(1)

        # Auto-detect subject from current directory
        from empirica.config.project_config_loader import get_current_subject
        subject = config_data.get('subject') if config_data else getattr(args, 'subject', None)
        if subject is None:
            subject = get_current_subject()  # Auto-detect from directory

        db = SessionDatabase()

        # Auto-resolve project_id if not provided
        if not project_id:
            # Try to get project from session record
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT project_id FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row and row['project_id']:
                project_id = row['project_id']
                logger.info(f"Auto-resolved project_id from session: {project_id[:8]}...")
            else:
                # Fallback: try to resolve from unified context (NOT CWD)
                try:
                    from empirica.utils.session_resolver import get_active_context
                    context = get_active_context()
                    project_path = context.get('project_path')
                    if project_path:
                        import yaml
                        from pathlib import Path
                        project_yaml = Path(project_path) / '.empirica' / 'project.yaml'
                        if project_yaml.exists():
                            with open(project_yaml) as f:
                                project_config = yaml.safe_load(f)
                                project_id = project_config.get('project_id')
                                if project_id:
                                    logger.info(f"Auto-resolved project_id from context: {project_id[:8]}...")
                except Exception:
                    pass

        # Resolve project name to UUID if still not resolved
        if project_id:
            project_id = resolve_project_id(project_id, db)
        else:
            # Last resort: create a generic project ID based on session if no project context available
            import hashlib
            project_id = hashlib.md5(f"session-{session_id}".encode()).hexdigest()
            logger.warning(f"Using fallback project_id derived from session: {project_id[:8]}...")

        # At this point, project_id should be resolved
        
        # SESSION-BASED AUTO-LINKING: If goal_id not provided, check for active goal in session
        if not goal_id:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT id FROM goals 
                WHERE session_id = ? AND is_completed = 0 
                ORDER BY created_timestamp DESC 
                LIMIT 1
            """, (session_id,))
            active_goal = cursor.fetchone()
            if active_goal:
                goal_id = active_goal['id']

        # Auto-derive active transaction_id
        transaction_id = None
        try:
            from empirica.utils.session_resolver import read_active_transaction
            transaction_id = read_active_transaction()
        except Exception:
            pass

        # PROJECT-SCOPED: All dead ends are project-scoped (session_id preserved for provenance)
        dead_end_id = db.log_dead_end(
            project_id=project_id,
            session_id=session_id,
            approach=approach,
            why_failed=why_failed,
            goal_id=goal_id,
            subtask_id=subtask_id,
            subject=subject,
            impact=impact,
            transaction_id=transaction_id
        )

        # Get ai_id from session for git notes
        ai_id = 'claude-code'  # Default
        try:
            cursor = db.conn.cursor()
            cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row['ai_id']:
                ai_id = row['ai_id']
        except:
            pass

        db.close()

        # GIT NOTES: Store dead end in git notes for sync (canonical source)
        git_stored = False
        try:
            from empirica.core.canonical.empirica_git.dead_end_store import GitDeadEndStore
            git_store = GitDeadEndStore()

            git_stored = git_store.store_dead_end(
                dead_end_id=dead_end_id,
                project_id=project_id,
                session_id=session_id,
                ai_id=ai_id,
                approach=approach,
                why_failed=why_failed,
                goal_id=goal_id,
                subtask_id=subtask_id
            )
            if git_stored:
                logger.info(f"✓ Dead end {dead_end_id[:8]} stored in git notes")
        except Exception as git_err:
            # Non-fatal - log but continue
            logger.warning(f"Git notes storage failed: {git_err}")

        result = {
            "ok": True,
            "dead_end_id": dead_end_id,
            "project_id": project_id if project_id else None,
            "git_stored": git_stored,
            "message": "Dead end logged to project scope"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Dead end logged successfully")
            print(f"   Dead End ID: {dead_end_id[:8]}...")
            if project_id:
                print(f"   Project: {project_id[:8]}...")
            if git_stored:
                print(f"   📝 Stored in git notes for sync")

        return 0  # Success

    except Exception as e:
        handle_cli_error(e, "Dead end log", getattr(args, 'verbose', False))
        return None


def handle_assumption_log_command(args):
    """Handle assumption-log command — log unverified assumptions to Qdrant."""
    try:
        import os
        import sys
        import time
        import uuid
        from empirica.cli.cli_utils import parse_json_safely

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

        if config_data:
            project_id = config_data.get('project_id')
            session_id = config_data.get('session_id')
            assumption = config_data.get('assumption')
            confidence = config_data.get('confidence', 0.5)
            domain = config_data.get('domain')
            goal_id = config_data.get('goal_id')
            output_format = 'json'
        else:
            project_id = getattr(args, 'project_id', None)
            session_id = getattr(args, 'session_id', None)
            assumption = getattr(args, 'assumption', None)
            confidence = getattr(args, 'confidence', 0.5)
            domain = getattr(args, 'domain', None)
            goal_id = getattr(args, 'goal_id', None)
            output_format = getattr(args, 'output', 'json')

        # Auto-derive session_id
        if not session_id:
            from empirica.utils.session_resolver import get_active_empirica_session_id
            session_id = get_active_empirica_session_id()

        if not assumption:
            print(json.dumps({"ok": False, "error": "Assumption text is required (--assumption or config)"}))
            sys.exit(1)

        # Auto-resolve project_id
        if not project_id:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            if session_id:
                cursor = db.conn.cursor()
                cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                if row and row['project_id']:
                    project_id = row['project_id']
            db.close()

        if not project_id:
            print(json.dumps({"ok": False, "error": "Could not resolve project_id"}))
            sys.exit(1)

        # Auto-derive transaction_id
        transaction_id = None
        try:
            from empirica.utils.session_resolver import read_active_transaction
            transaction_id = read_active_transaction()
        except Exception:
            pass

        # Store to Qdrant
        assumption_id = str(uuid.uuid4())
        embedded = False
        try:
            from empirica.core.qdrant.vector_store import embed_assumption, _check_qdrant_available
            if _check_qdrant_available():
                embed_assumption(
                    project_id=project_id,
                    assumption_id=assumption_id,
                    assumption=assumption,
                    confidence=confidence,
                    status="unverified",
                    entity_type="project",
                    entity_id=project_id,
                    session_id=session_id,
                    transaction_id=transaction_id,
                    domain=domain,
                    timestamp=time.time(),
                )
                embedded = True
        except Exception as e:
            logger.debug(f"Qdrant embed failed (non-fatal): {e}")

        result = {
            "ok": True,
            "assumption_id": assumption_id,
            "project_id": project_id,
            "assumption": assumption,
            "confidence": confidence,
            "status": "unverified",
            "embedded": embedded,
            "message": "Assumption logged" + (" (Qdrant)" if embedded else " (Qdrant unavailable)"),
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"Assumption logged: {assumption_id[:8]}...")
            print(f"   Confidence: {confidence}")
            if embedded:
                print(f"   Stored in Qdrant")

        return 0

    except Exception as e:
        handle_cli_error(e, "Assumption log", getattr(args, 'verbose', False))
        return None


def handle_decision_log_command(args):
    """Handle decision-log command — log decisions with alternatives to Qdrant."""
    try:
        import os
        import sys
        import time
        import uuid
        from empirica.cli.cli_utils import parse_json_safely

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

        if config_data:
            project_id = config_data.get('project_id')
            session_id = config_data.get('session_id')
            choice = config_data.get('choice')
            alternatives = config_data.get('alternatives', '')
            rationale = config_data.get('rationale', '')
            confidence = config_data.get('confidence', 0.7)
            reversibility = config_data.get('reversibility', 'exploratory')
            domain = config_data.get('domain')
            goal_id = config_data.get('goal_id')
            output_format = 'json'
        else:
            project_id = getattr(args, 'project_id', None)
            session_id = getattr(args, 'session_id', None)
            choice = getattr(args, 'choice', None)
            alternatives = getattr(args, 'alternatives', '')
            rationale = getattr(args, 'rationale', '')
            confidence = getattr(args, 'confidence', 0.7)
            reversibility = getattr(args, 'reversibility', 'exploratory')
            domain = getattr(args, 'domain', None)
            goal_id = getattr(args, 'goal_id', None)
            output_format = getattr(args, 'output', 'json')

        # Auto-derive session_id
        if not session_id:
            from empirica.utils.session_resolver import get_active_empirica_session_id
            session_id = get_active_empirica_session_id()

        if not choice:
            print(json.dumps({"ok": False, "error": "Choice text is required (--choice or config)"}))
            sys.exit(1)

        # Parse alternatives if comma-separated string
        if isinstance(alternatives, str) and alternatives:
            try:
                import json as json_mod
                alternatives_list = json_mod.loads(alternatives)
            except (json.JSONDecodeError, ValueError):
                alternatives_list = [a.strip() for a in alternatives.split(',') if a.strip()]
        elif isinstance(alternatives, list):
            alternatives_list = alternatives
        else:
            alternatives_list = []

        # Auto-resolve project_id
        if not project_id:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            if session_id:
                cursor = db.conn.cursor()
                cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                if row and row['project_id']:
                    project_id = row['project_id']
            db.close()

        if not project_id:
            print(json.dumps({"ok": False, "error": "Could not resolve project_id"}))
            sys.exit(1)

        # Auto-derive transaction_id
        transaction_id = None
        try:
            from empirica.utils.session_resolver import read_active_transaction
            transaction_id = read_active_transaction()
        except Exception:
            pass

        # Store to Qdrant
        decision_id = str(uuid.uuid4())
        embedded = False
        try:
            from empirica.core.qdrant.vector_store import embed_decision, _check_qdrant_available
            if _check_qdrant_available():
                embed_decision(
                    project_id=project_id,
                    decision_id=decision_id,
                    choice=choice,
                    alternatives=json.dumps(alternatives_list),
                    rationale=rationale,
                    confidence_at_decision=confidence,
                    reversibility=reversibility,
                    entity_type="project",
                    entity_id=project_id,
                    session_id=session_id,
                    transaction_id=transaction_id,
                    timestamp=time.time(),
                )
                embedded = True
        except Exception as e:
            logger.debug(f"Qdrant embed failed (non-fatal): {e}")

        result = {
            "ok": True,
            "decision_id": decision_id,
            "project_id": project_id,
            "choice": choice,
            "alternatives": alternatives_list,
            "rationale": rationale,
            "confidence": confidence,
            "reversibility": reversibility,
            "embedded": embedded,
            "message": "Decision logged" + (" (Qdrant)" if embedded else " (Qdrant unavailable)"),
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"Decision logged: {decision_id[:8]}...")
            print(f"   Choice: {choice}")
            print(f"   Alternatives: {', '.join(alternatives_list) if alternatives_list else 'none'}")
            print(f"   Reversibility: {reversibility}")
            if embedded:
                print(f"   Stored in Qdrant")

        return 0

    except Exception as e:
        handle_cli_error(e, "Decision log", getattr(args, 'verbose', False))
        return None


def handle_refdoc_add_command(args):
    """Handle refdoc-add command"""
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.cli.utils.project_resolver import resolve_project_id

        # Get project_id from args FIRST (bug fix: was using before assignment)
        project_id = args.project_id
        doc_path = args.doc_path
        doc_type = getattr(args, 'doc_type', None)
        description = getattr(args, 'description', None)

        db = SessionDatabase()

        # Auto-resolve project_id if not provided
        if not project_id:
            # Try to get project from session record
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT project_id FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row and row['project_id']:
                project_id = row['project_id']
                logger.info(f"Auto-resolved project_id from session: {project_id[:8]}...")
            else:
                # Fallback: try to resolve from unified context (NOT CWD)
                try:
                    from empirica.utils.session_resolver import get_active_context
                    context = get_active_context()
                    project_path = context.get('project_path')
                    if project_path:
                        import yaml
                        from pathlib import Path
                        project_yaml = Path(project_path) / '.empirica' / 'project.yaml'
                        if project_yaml.exists():
                            with open(project_yaml) as f:
                                project_config = yaml.safe_load(f)
                                project_id = project_config.get('project_id')
                                if project_id:
                                    logger.info(f"Auto-resolved project_id from context: {project_id[:8]}...")
                except Exception:
                    pass

        # Resolve project name to UUID if still not resolved
        if project_id:
            project_id = resolve_project_id(project_id, db)
        else:
            # Last resort: create a generic project ID based on session if no project context available
            import hashlib
            project_id = hashlib.md5(f"session-{session_id}".encode()).hexdigest()
            logger.warning(f"Using fallback project_id derived from session: {project_id[:8]}...")

        # At this point, project_id should be resolved

        doc_id = db.add_reference_doc(
            project_id=project_id,
            doc_path=doc_path,
            doc_type=doc_type,
            description=description
        )
        db.close()

        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "doc_id": doc_id,
                "project_id": project_id,
                "message": "Reference doc added successfully"
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Reference doc added successfully")
            print(f"   Doc ID: {doc_id}")
            print(f"   Path: {doc_path}")

        return 0  # Success

    except Exception as e:
        handle_cli_error(e, "Reference doc add", getattr(args, 'verbose', False))
        return None


def handle_source_add_command(args):
    """Handle source-add command — entity-agnostic epistemic source logging.

    Sources are bidirectional:
      --noetic: evidence IN (source_used — informed knowledge)
      --praxic: output OUT (source_created — produced by action)
    """
    try:
        import time
        import uuid
        from empirica.data.session_database import SessionDatabase
        from empirica.cli.utils.project_resolver import resolve_project_id

        title = args.title
        description = getattr(args, 'description', None)
        source_type = getattr(args, 'source_type', 'document')
        doc_path = getattr(args, 'path', None)
        source_url = getattr(args, 'url', None)
        confidence = getattr(args, 'confidence', 0.7)
        direction = 'noetic' if getattr(args, 'noetic', False) else 'praxic'
        session_id = getattr(args, 'session_id', None)
        project_id = getattr(args, 'project_id', None)
        output_format = getattr(args, 'output', 'human')

        # Auto-derive session_id from active transaction
        if not session_id:
            from empirica.utils.session_resolver import get_active_empirica_session_id
            session_id = get_active_empirica_session_id()

        if not session_id:
            print(json.dumps({
                "ok": False,
                "error": "No active transaction and --session-id not provided",
                "hint": "Either run PREFLIGHT first, or provide --session-id explicitly"
            }))
            return 1

        db = SessionDatabase()

        # Auto-resolve project_id from session if not provided
        if not project_id:
            cursor = db.conn.cursor()
            cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                project_id = row['project_id'] if isinstance(row, dict) else row[0]

        if not project_id:
            print(json.dumps({
                "ok": False,
                "error": "Could not resolve project_id",
                "hint": "Provide --project-id or ensure active session has a project"
            }))
            db.close()
            return 1

        # Auto-derive transaction_id
        transaction_id = None
        try:
            from empirica.cli.command_handlers.workflow_commands import read_active_transaction
            tx = read_active_transaction()
            if tx:
                transaction_id = tx.get('transaction_id')
        except Exception:
            pass

        source_id = str(uuid.uuid4())

        # Build metadata
        metadata = {
            "direction": direction,
            "doc_path": doc_path,
            "source_url": source_url,
            "transaction_id": transaction_id,
        }

        # Insert into epistemic_sources table
        db.conn.execute("""
            INSERT INTO epistemic_sources (
                id, project_id, session_id, source_type, source_url,
                title, description, confidence, epistemic_layer,
                discovered_by_ai, discovered_at, source_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_id, project_id, session_id, source_type,
            source_url or doc_path,
            title, description, confidence, direction,
            'claude-code', time.time(), json.dumps(metadata)
        ))
        db.conn.commit()

        # Also add to project_reference_docs for backwards compatibility
        if doc_path:
            try:
                db.add_reference_doc(
                    project_id=project_id,
                    doc_path=doc_path,
                    doc_type=source_type,
                    description=description
                )
            except Exception:
                pass  # Not critical if legacy table fails

        db.close()

        if output_format == 'json':
            print(json.dumps({
                "ok": True,
                "source_id": source_id,
                "project_id": project_id,
                "session_id": session_id,
                "transaction_id": transaction_id,
                "direction": direction,
                "title": title,
                "message": f"Source added ({direction})"
            }, indent=2))
        else:
            direction_emoji = "📥" if direction == 'noetic' else "📤"
            print(f"{direction_emoji} Source added ({direction})")
            print(f"   Source ID: {source_id[:12]}...")
            print(f"   Title: {title}")
            print(f"   Type: {source_type}")
            print(f"   Direction: {direction} ({'evidence IN' if direction == 'noetic' else 'output OUT'})")
            if doc_path:
                print(f"   Path: {doc_path}")
            if source_url:
                print(f"   URL: {source_url}")

        return 0

    except Exception as e:
        handle_cli_error(e, "Source add", getattr(args, 'verbose', False))
        return None


def handle_workspace_overview_command(args):
    """Handle workspace-overview command - show epistemic health of all projects"""
    try:
        from empirica.data.session_database import SessionDatabase
        from datetime import datetime, timedelta
        
        db = SessionDatabase()
        overview = db.get_workspace_overview()
        db.close()
        
        # Get output format and sorting options
        output_format = getattr(args, 'output', 'dashboard')
        sort_by = getattr(args, 'sort_by', 'activity')
        filter_status = getattr(args, 'filter', None)
        
        # Sort projects
        projects = overview['projects']
        if sort_by == 'knowledge':
            projects.sort(key=lambda p: p.get('health_score', 0), reverse=True)
        elif sort_by == 'uncertainty':
            projects.sort(key=lambda p: p.get('epistemic_state', {}).get('uncertainty', 0.5))
        elif sort_by == 'name':
            projects.sort(key=lambda p: p.get('name', ''))
        # Default: 'activity' - already sorted by last_activity_timestamp DESC
        
        # Filter projects by status
        if filter_status:
            projects = [p for p in projects if p.get('status') == filter_status]
        
        # JSON output
        if output_format == 'json':
            result = {
                "ok": True,
                "workspace_stats": overview['workspace_stats'],
                "total_projects": len(projects),
                "projects": projects
            }
            print(json.dumps(result, indent=2))
            # Return None to avoid exit code issues and duplicate output
            return None
        
        # Dashboard output (human-readable)
        stats = overview['workspace_stats']
        
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║  Empirica Workspace Overview - Epistemic Project Management    ║")
        print("╚════════════════════════════════════════════════════════════════╝\n")
        
        print("📊 Workspace Summary")
        print(f"   Total Projects:    {stats['total_projects']}")
        print(f"   Total Sessions:    {stats['total_sessions']}")
        print(f"   Active Sessions:   {stats['active_sessions']}")
        print(f"   Average Know:      {stats['avg_know']:.2f}")
        print(f"   Average Uncertainty: {stats['avg_uncertainty']:.2f}")
        print()
        
        if not projects:
            print("   No projects found.")
            print(json.dumps({"projects": []}, indent=2))
            return 0
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        print("📁 Projects by Epistemic Health\n")
        
        # Group by health tier
        high_health = [p for p in projects if p['health_score'] >= 0.7]
        medium_health = [p for p in projects if 0.5 <= p['health_score'] < 0.7]
        low_health = [p for p in projects if p['health_score'] < 0.5]
        
        # Display high health projects
        if high_health:
            print("🟢 HIGH KNOWLEDGE (know ≥ 0.7)")
            for i, p in enumerate(high_health, 1):
                _display_project(i, p)
            print()
        
        # Display medium health projects
        if medium_health:
            print("🟡 MEDIUM KNOWLEDGE (0.5 ≤ know < 0.7)")
            for i, p in enumerate(medium_health, 1):
                _display_project(i, p)
            print()
        
        # Display low health projects
        if low_health:
            print("🔴 LOW KNOWLEDGE (know < 0.5)")
            for i, p in enumerate(low_health, 1):
                _display_project(i, p)
            print()
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        print("💡 Quick Commands:")
        print(f"   • Bootstrap project:  empirica project-bootstrap --project-id <PROJECT_ID>")
        print(f"   • Check ready goals:  empirica goals-ready --session-id <SESSION_ID>")
        print(f"   • List all projects:  empirica project-list")
        print()
        
        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Workspace overview", getattr(args, 'verbose', False))
        return None


def _display_project(index, project):
    """Helper to display a single project in dashboard format"""
    name = project['name']
    health = project['health_score']
    know = project['epistemic_state']['know']
    uncertainty = project['epistemic_state']['uncertainty']
    findings = project['findings_count']
    unknowns = project['unknowns_count']
    dead_ends = project['dead_ends_count']
    sessions = project['total_sessions']
    
    # Format last activity
    last_activity = project.get('last_activity')
    if last_activity:
        try:
            from datetime import datetime
            last_dt = datetime.fromtimestamp(last_activity)
            now = datetime.now()
            delta = now - last_dt
            if delta.days == 0:
                time_ago = "today"
            elif delta.days == 1:
                time_ago = "1 day ago"
            elif delta.days < 7:
                time_ago = f"{delta.days} days ago"
            elif delta.days < 30:
                weeks = delta.days // 7
                time_ago = f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = delta.days // 30
                time_ago = f"{months} month{'s' if months > 1 else ''} ago"
        except:
            time_ago = "unknown"
    else:
        time_ago = "never"
    
    print(f"   {index}. {name} │ Health: {health:.2f} │ Know: {know:.2f} │ Sessions: {sessions} │ ⏰ {time_ago}")
    print(f"      Findings: {findings}  Unknowns: {unknowns}  Dead Ends: {dead_ends}")
    
    # Show warnings
    if uncertainty > 0.7:
        print(f"      ⚠️  High uncertainty ({uncertainty:.2f}) - needs investigation")
    if dead_ends > 0 and sessions > 0:
        dead_end_ratio = dead_ends / sessions
        if dead_end_ratio > 0.3:
            print(f"      🚨 High dead end ratio ({dead_end_ratio:.0%}) - many failed approaches")
    if unknowns > 20:
        print(f"      ❓ Many unresolved unknowns ({unknowns}) - systematically resolve them")
    
    # Show project ID (shortened)
    project_id = project['project_id']
    print(f"      ID: {project_id[:8]}...")


def handle_workspace_map_command(args):
    """Handle workspace-map command - discover git repos and show epistemic status"""
    try:
        from empirica.data.session_database import SessionDatabase
        import subprocess
        from pathlib import Path
        
        # Get current directory and scan parent
        current_dir = Path.cwd()
        parent_dir = current_dir.parent
        
        output_format = getattr(args, 'output', 'dashboard')
        
        # Find all git repositories in parent directory
        git_repos = []
        logger.info(f"Scanning {parent_dir} for git repositories...")
        
        for item in parent_dir.iterdir():
            if not item.is_dir():
                continue
            
            git_dir = item / '.git'
            if not git_dir.exists():
                continue
            
            # This is a git repo - get remote URL
            try:
                result = subprocess.run(
                    ['git', '-C', str(item), 'remote', 'get-url', 'origin'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                remote_url = result.stdout.strip() if result.returncode == 0 else None
                
                repo_info = {
                    'path': str(item),
                    'name': item.name,
                    'remote_url': remote_url,
                    'has_remote': remote_url is not None
                }
                
                git_repos.append(repo_info)
                
            except Exception as e:
                logger.debug(f"Error getting remote for {item.name}: {e}")
                git_repos.append({
                    'path': str(item),
                    'name': item.name,
                    'remote_url': None,
                    'has_remote': False,
                    'error': str(e)
                })
        
        # Load ecosystem manifest (optional - enhances output with dependency info)
        eco_graph = None
        try:
            from empirica.core.ecosystem import load_ecosystem
            eco_graph = load_ecosystem()
        except Exception:
            pass  # Manifest not found or invalid - continue without it

        # Match with Empirica projects
        db = SessionDatabase()
        cursor = db.conn.cursor()
        
        for repo in git_repos:
            if not repo['has_remote']:
                repo['empirica_project'] = None
                continue
            
            # Try to find matching project
            cursor.execute("""
                SELECT id, name, status, total_sessions,
                       (SELECT r.know FROM reflexes r
                        JOIN sessions s ON s.session_id = r.session_id
                        WHERE s.project_id = projects.id
                        ORDER BY r.timestamp DESC LIMIT 1) as latest_know,
                       (SELECT r.uncertainty FROM reflexes r
                        JOIN sessions s ON s.session_id = r.session_id
                        WHERE s.project_id = projects.id
                        ORDER BY r.timestamp DESC LIMIT 1) as latest_uncertainty
                FROM projects
                WHERE repos LIKE ?
            """, (f'%{repo["remote_url"]}%',))
            
            row = cursor.fetchone()
            if row:
                repo['empirica_project'] = {
                    'project_id': row[0],
                    'name': row[1],
                    'status': row[2],
                    'total_sessions': row[3],
                    'know': row[4] if row[4] else 0.5,
                    'uncertainty': row[5] if row[5] else 0.5
                }
            else:
                repo['empirica_project'] = None
        
        db.close()
        
        # Enrich repos with ecosystem dependency info
        if eco_graph:
            for repo in git_repos:
                eco_name = repo['name']
                if eco_name in eco_graph.projects:
                    downstream = sorted(eco_graph.downstream(eco_name))
                    upstream = sorted(eco_graph.upstream(eco_name))
                    eco_config = eco_graph.projects[eco_name]
                    repo['ecosystem'] = {
                        'role': eco_config.get('role'),
                        'type': eco_config.get('type'),
                        'downstream': downstream,
                        'downstream_count': len(downstream),
                        'upstream': upstream,
                        'upstream_count': len(upstream),
                    }
                else:
                    repo['ecosystem'] = None

        # JSON output
        if output_format == 'json':
            result = {
                "ok": True,
                "parent_directory": str(parent_dir),
                "total_repos": len(git_repos),
                "tracked_repos": sum(1 for r in git_repos if r['empirica_project']),
                "untracked_repos": sum(1 for r in git_repos if not r['empirica_project']),
                "has_ecosystem_manifest": eco_graph is not None,
                "repos": git_repos
            }
            print(json.dumps(result, indent=2))
            return None  # Already printed; returning dict would cause double-print by dispatch

        # Dashboard output
        tracked = [r for r in git_repos if r['empirica_project']]
        untracked = [r for r in git_repos if not r['empirica_project']]
        
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║  Git Workspace Map - Epistemic Health                         ║")
        print("╚════════════════════════════════════════════════════════════════╝\n")
        
        print(f"📂 Parent Directory: {parent_dir}")
        print(f"   Total Git Repos:  {len(git_repos)}")
        print(f"   Tracked:          {len(tracked)}")
        print(f"   Untracked:        {len(untracked)}")
        print()
        
        if tracked:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            print("🟢 Tracked in Empirica\n")
            
            for repo in tracked:
                proj = repo['empirica_project']
                status_icon = "🟢" if proj['status'] == 'active' else "🟡"
                
                print(f"{status_icon} {repo['name']}")
                print(f"   Path: {repo['path']}")
                print(f"   Project: {proj['name']}")
                print(f"   Know: {proj['know']:.2f} | Uncertainty: {proj['uncertainty']:.2f} | Sessions: {proj['total_sessions']}")
                print(f"   ID: {proj['project_id'][:8]}...")
                eco = repo.get('ecosystem')
                if eco:
                    print(f"   Role: {eco['role']} | Deps: {eco['upstream_count']} upstream, {eco['downstream_count']} downstream")
                print()
        
        if untracked:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            print("⚪ Not Tracked in Empirica\n")
            
            for repo in untracked:
                print(f"⚪ {repo['name']}")
                print(f"   Path: {repo['path']}")
                if repo['has_remote']:
                    print(f"   Remote: {repo['remote_url']}")
                    print(f"   → To track: empirica project-create --name '{repo['name']}' --repos '[\"{repo['remote_url']}\"]'")
                else:
                    print(f"   ⚠️  No remote configured")
                print()
        
        if eco_graph:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            summary = eco_graph.summary()
            print(f"📋 Ecosystem Manifest: {summary['total_projects']} projects, {summary['dependency_edges']} dependency edges")
            print()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        print("Quick Commands:")
        print(f"   empirica workspace-overview           # Epistemic health of all projects")
        print(f"   empirica ecosystem-check              # Full ecosystem dependency map")
        print(f"   empirica ecosystem-check --project X  # Upstream/downstream for project X")
        print(f"   empirica ecosystem-check --file F     # Impact analysis for file F")
        print()
        return 0
        
    except Exception as e:
        handle_cli_error(e, "Workspace map", getattr(args, 'verbose', False))
        return 1


def handle_workspace_list_command(args):
    """Handle workspace-list command - list projects with types, tags, and hierarchy"""
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.data.repositories.projects import ProjectRepository

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Build query with optional filters
        query = """
            SELECT id, name, description, status, project_type, project_tags,
                   parent_project_id, total_sessions, last_activity_timestamp
            FROM projects
        """
        params = []
        conditions = []

        # Filter by type
        filter_type = getattr(args, 'type', None)
        if filter_type:
            conditions.append("project_type = ?")
            params.append(filter_type)

        # Filter by parent
        filter_parent = getattr(args, 'parent', None)
        if filter_parent:
            conditions.append("parent_project_id = ?")
            params.append(filter_parent)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY project_type, name"

        cursor.execute(query, params)
        projects = [dict(row) for row in cursor.fetchall()]

        # Filter by tags if specified (in-memory filtering since tags are JSON)
        filter_tags = getattr(args, 'tags', None)
        if filter_tags:
            tag_list = [t.strip().lower() for t in filter_tags.split(',')]
            filtered = []
            for p in projects:
                project_tags = json.loads(p.get('project_tags') or '[]')
                project_tags_lower = [t.lower() for t in project_tags]
                if any(tag in project_tags_lower for tag in tag_list):
                    filtered.append(p)
            projects = filtered

        db.close()

        # Parse JSON fields
        for p in projects:
            p['project_tags'] = json.loads(p.get('project_tags') or '[]')

        output_format = getattr(args, 'output', 'human')
        show_tree = getattr(args, 'tree', False)

        # JSON output
        if output_format == 'json':
            result = {
                "ok": True,
                "filters": {
                    "type": filter_type,
                    "tags": filter_tags,
                    "parent": filter_parent
                },
                "total_projects": len(projects),
                "projects": projects
            }
            print(json.dumps(result, indent=2))
            return None

        # Human-readable output
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║  Empirica Workspace - Projects by Type                         ║")
        print("╚════════════════════════════════════════════════════════════════╝\n")

        if not projects:
            print("   No projects found matching filters.")
            return None

        if show_tree:
            # Tree view - group by parent relationships
            _display_project_tree(projects)
        else:
            # Default - group by type
            types_order = ProjectRepository.PROJECT_TYPES
            for ptype in types_order:
                type_projects = [p for p in projects if p.get('project_type') == ptype]
                if type_projects:
                    icon = _get_type_icon(ptype)
                    print(f"{icon} {ptype.upper()}")
                    print("─" * 60)
                    for p in type_projects:
                        tags_str = ', '.join(p['project_tags']) if p['project_tags'] else ''
                        parent_str = f" (child of {p['parent_project_id'][:8]}...)" if p['parent_project_id'] else ''
                        print(f"   {p['name']}{parent_str}")
                        print(f"      ID: {p['id'][:8]}...  Sessions: {p['total_sessions']}")
                        if tags_str:
                            print(f"      Tags: {tags_str}")
                        if p['description']:
                            print(f"      {p['description'][:60]}...")
                        print()
                    print()

        # Summary
        type_counts = {}
        for p in projects:
            ptype = p.get('project_type', 'product')
            type_counts[ptype] = type_counts.get(ptype, 0) + 1

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📊 Summary")
        for ptype, count in sorted(type_counts.items()):
            print(f"   {_get_type_icon(ptype)} {ptype}: {count}")
        print()

        return None

    except Exception as e:
        handle_cli_error(e, "Workspace list", getattr(args, 'verbose', False))
        return None


def _get_type_icon(project_type):
    """Get emoji icon for project type"""
    icons = {
        'product': '📦',
        'application': '🖥️',
        'feature': '⚡',
        'research': '🔬',
        'documentation': '📚',
        'infrastructure': '🏗️',
        'operations': '⚙️'
    }
    return icons.get(project_type, '📁')


def _display_project_tree(projects):
    """Display projects as a tree based on parent relationships"""
    # Build parent -> children map
    children_map = {}
    roots = []

    for p in projects:
        parent_id = p.get('parent_project_id')
        if parent_id:
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(p)
        else:
            roots.append(p)

    def print_tree(project, indent=0):
        prefix = "   " * indent
        icon = _get_type_icon(project.get('project_type', 'product'))
        tags_str = f" [{', '.join(project['project_tags'])}]" if project['project_tags'] else ''
        print(f"{prefix}{icon} {project['name']}{tags_str}")
        print(f"{prefix}   ID: {project['id'][:8]}... | Type: {project.get('project_type', 'product')}")

        # Print children
        children = children_map.get(project['id'], [])
        for child in children:
            print_tree(child, indent + 1)

    for root in roots:
        print_tree(root)
        print()


def handle_ecosystem_check_command(args):
    """Handle ecosystem-check command - analyze dependencies and impact from ecosystem.yaml"""
    try:
        from empirica.core.ecosystem import load_ecosystem

        manifest_path = getattr(args, 'manifest', None)
        output_format = getattr(args, 'output', 'human')

        try:
            graph = load_ecosystem(manifest_path)
        except FileNotFoundError as e:
            if output_format == 'json':
                print(json.dumps({"ok": False, "error": str(e)}))
            else:
                print(f"Error: {e}")
            return 1

        # --validate: check manifest integrity
        if getattr(args, 'validate', False):
            issues = graph.validate()
            if output_format == 'json':
                print(json.dumps({
                    "ok": len(issues) == 0,
                    "issues": issues,
                    "issue_count": len(issues),
                }))
            else:
                if issues:
                    print(f"Found {len(issues)} issue(s):\n")
                    for i in issues:
                        print(f"  WARNING: {i}")
                else:
                    print("Ecosystem manifest is valid. No issues found.")
            return 0 if not issues else 1

        # --file: impact analysis for a specific file
        check_file = getattr(args, 'file', None)
        if check_file:
            impact = graph.impact_of(check_file)
            if output_format == 'json':
                print(json.dumps({"ok": True, **impact}, indent=2))
            else:
                if impact['project']:
                    print(f"File: {check_file}")
                    print(f"Project: {impact['project']}")
                    print(f"Exports affected: {'Yes' if impact['exports_affected'] else 'No'}")
                    print(f"Downstream impact: {impact['downstream_count']} project(s)")
                    if impact['downstream']:
                        for d in impact['downstream']:
                            print(f"  -> {d}")
                else:
                    print(f"File '{check_file}' does not belong to any known project.")
            return 0

        # --project: show upstream/downstream for a specific project
        check_project = getattr(args, 'project', None)
        if check_project:
            if check_project not in graph.projects:
                msg = f"Project '{check_project}' not found in manifest."
                if output_format == 'json':
                    print(json.dumps({"ok": False, "error": msg}))
                else:
                    print(msg)
                return 1

            upstream = sorted(graph.upstream(check_project))
            downstream = sorted(graph.downstream(check_project))
            config = graph.projects[check_project]

            if output_format == 'json':
                print(json.dumps({
                    "ok": True,
                    "project": check_project,
                    "role": config.get('role'),
                    "type": config.get('type'),
                    "description": config.get('description'),
                    "upstream": upstream,
                    "upstream_count": len(upstream),
                    "downstream": downstream,
                    "downstream_count": len(downstream),
                }, indent=2))
            else:
                print(f"Project: {check_project}")
                print(f"  Role: {config.get('role', 'unknown')}")
                print(f"  Type: {config.get('type', 'unknown')}")
                print(f"  Description: {config.get('description', '')}")
                print()
                print(f"Upstream ({len(upstream)}):")
                for u in upstream:
                    print(f"  <- {u}")
                if not upstream:
                    print("  (none - root project)")
                print()
                print(f"Downstream ({len(downstream)}):")
                for d in downstream:
                    print(f"  -> {d}")
                if not downstream:
                    print("  (none - leaf project)")
            return 0

        # --role: filter by role
        check_role = getattr(args, 'role', None)
        if check_role:
            projects = graph.by_role(check_role)
            if output_format == 'json':
                print(json.dumps({
                    "ok": True,
                    "role": check_role,
                    "count": len(projects),
                    "projects": projects,
                }, indent=2))
            else:
                print(f"Projects with role '{check_role}' ({len(projects)}):")
                for p in sorted(projects):
                    desc = graph.projects[p].get('description', '')
                    print(f"  {p}: {desc}")
            return 0

        # --tag: filter by tag
        check_tag = getattr(args, 'tag', None)
        if check_tag:
            projects = graph.by_tag(check_tag)
            if output_format == 'json':
                print(json.dumps({
                    "ok": True,
                    "tag": check_tag,
                    "count": len(projects),
                    "projects": projects,
                }, indent=2))
            else:
                print(f"Projects with tag '{check_tag}' ({len(projects)}):")
                for p in sorted(projects):
                    desc = graph.projects[p].get('description', '')
                    print(f"  {p}: {desc}")
            return 0

        # Default: full ecosystem summary
        summary = graph.summary()

        if output_format == 'json':
            print(json.dumps({"ok": True, **summary}, indent=2))
            return 0

        # Dashboard output
        print("=" * 64)
        print("  Empirica Ecosystem Overview")
        print("=" * 64)
        print()
        print(f"  Total Projects: {summary['total_projects']}")
        print(f"  Dependency Edges: {summary['dependency_edges']}")
        print()

        print("  By Role:")
        for role, count in sorted(summary['by_role'].items()):
            print(f"    {role:20s} {count}")
        print()

        print("  By Type:")
        for ptype, count in sorted(summary['by_type'].items()):
            print(f"    {ptype:20s} {count}")
        print()

        print(f"  Root Projects ({len(summary['root_projects'])}):")
        for p in summary['root_projects']:
            print(f"    {p}")
        print()

        print(f"  Leaf Projects ({len(summary['leaf_projects'])}):")
        for p in summary['leaf_projects']:
            print(f"    {p}")
        print()

        # Show dependency tree for core
        print("  Dependency Tree (from empirica):")
        _print_dep_tree(graph, 'empirica', indent=4)
        print()

        return 0

    except Exception as e:
        handle_cli_error(e, "Ecosystem check", getattr(args, 'verbose', False))
        return 1


def _print_dep_tree(graph, project, indent=0, visited=None):
    """Print dependency tree for a project (downstream)."""
    if visited is None:
        visited = set()
    if project in visited:
        print(" " * indent + f"{project} (circular)")
        return
    visited.add(project)
    print(" " * indent + project)
    direct = sorted(graph.downstream(project, transitive=False))
    for dep in direct:
        _print_dep_tree(graph, dep, indent + 2, visited.copy())


"""
Project Switch Command Handler
Implements empirica project-switch for clear AI agent UX when changing projects
"""

import json
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def handle_project_switch_command(args):
    """
    Handle project-switch command - Switch to a different project with context loading

    Resolves projects from workspace database by:
    1. Folder name (most intuitive - e.g., 'empirica-platform')
    2. Project name
    3. UUID

    Provides clear UX for AI agents:
    1. Resolves project from workspace database
    2. Shows "you are here" banner with project path
    3. Automatically runs project-bootstrap
    4. Shows next steps

    Does NOT create a session (explicit action for user)
    """
    try:
        project_identifier = args.project_identifier
        output_format = getattr(args, 'output', 'human')
        # Get claude_session_id from CLI arg (enables instance isolation via Bash tool)
        cli_claude_session_id = getattr(args, 'claude_session_id', None)

        # 1. Resolve project from workspace database
        project = resolve_workspace_project(project_identifier)

        if not project:
            error_msg = f"Project not found: {project_identifier}"
            hint = "Run 'empirica project-list' to see available projects"

            if output_format == 'json':
                print(json.dumps({
                    'ok': False,
                    'error': error_msg,
                    'hint': hint
                }))
            else:
                print(f"❌ {error_msg}")
                print(f"\nTip: {hint}")

            return None

        # 2. Extract project details
        project_id = project.get('id')
        project_name = project.get('name')
        folder_name = project.get('folder_name')
        trajectory_path = project.get('trajectory_path', '')

        # Derive project root from trajectory path
        # trajectory_path = /home/user/project/.empirica -> project_path = /home/user/project
        project_path = None
        if trajectory_path:
            project_path = Path(trajectory_path).parent

        # 3. FORCED POSTFLIGHT: Close any open transaction from current project
        # Transactions are project-scoped, so switching projects should close the current one
        postflight_result = None
        try:
            from empirica.utils.session_resolver import read_active_transaction
            from empirica.config.path_resolver import get_empirica_root
            from empirica.core.statusline_cache import get_instance_id

            # Get current project from instance_projects (not CWD - may be wrong via Bash tool)
            # IMPORTANT: Use instance-specific file for multi-instance isolation
            current_empirica_root = None
            instance_id = get_instance_id()

            # Priority 1: Read from instance_projects (set by previous project-switch)
            if instance_id:
                instance_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
                if instance_file.exists():
                    try:
                        import json as _json
                        with open(instance_file, 'r') as f:
                            inst_data = _json.load(f)
                        inst_project_path = inst_data.get('project_path')
                        if inst_project_path:
                            current_empirica_root = Path(inst_project_path) / '.empirica'
                    except Exception:
                        pass

            # Priority 2: Fallback to CWD-based detection
            if not current_empirica_root:
                current_empirica_root = get_empirica_root()
            if current_empirica_root:
                suffix = f"_{instance_id}" if instance_id else ""
                tx_path = current_empirica_root / f'active_transaction{suffix}.json'
                if tx_path.exists():
                    import json as _json
                    with open(tx_path, 'r') as f:
                        tx_data = _json.load(f)

                    if tx_data.get('status') == 'open':
                        # Only auto-close if the transaction is from a DIFFERENT project
                        # than the destination. Switching to the same project (or switching
                        # right after opening a transaction) should NOT destroy the transaction.
                        tx_project_path = tx_data.get('project_path', '')
                        dest_project_str = str(project_path) if project_path else ''
                        # Normalize for comparison (resolve symlinks, trailing slashes)
                        tx_project_normalized = str(Path(tx_project_path).resolve()) if tx_project_path else ''
                        dest_normalized = str(Path(dest_project_str).resolve()) if dest_project_str else ''

                        if tx_project_normalized == dest_normalized:
                            # Transaction is for the destination project — don't close it
                            postflight_result = {"ok": True, "reason": "transaction_preserved", "note": "Transaction is for destination project, not closed"}
                        else:
                            # Transaction is for a different project — close it
                            import subprocess
                            tx_session_id = tx_data.get('session_id')
                            if tx_session_id:
                                postflight_cmd = ['empirica', 'postflight-submit', '-']
                                postflight_input = _json.dumps({
                                    "session_id": tx_session_id,
                                    "vectors": {
                                        "know": 0.7,
                                        "uncertainty": 0.3,
                                        "context": 0.7,
                                        "completion": 0.5
                                    },
                                    "reasoning": f"Auto-POSTFLIGHT: Project switch to {folder_name}. Transaction auto-closed to maintain epistemic measurement integrity."
                                })
                                # Run in current project directory (before switch)
                                result = subprocess.run(
                                    postflight_cmd,
                                    input=postflight_input,
                                    capture_output=True,
                                    text=True,
                                    timeout=30,
                                    cwd=str(current_empirica_root.parent)  # Project root
                                )
                                if result.returncode == 0:
                                    postflight_result = {"ok": True, "reason": "project_switch"}
                                    # Clear the old transaction file so sentinel doesn't see stale state
                                    try:
                                        tx_path.unlink()
                                    except Exception:
                                        pass
                                    if output_format == 'human':
                                        print("📊 Auto-closed previous transaction (POSTFLIGHT)")
                                else:
                                    postflight_result = {"ok": False, "error": result.stderr[:200]}
        except Exception as e:
            # Non-fatal - continue with switch even if POSTFLIGHT fails
            postflight_result = {"ok": False, "error": str(e)}
            logger.debug(f"Auto-POSTFLIGHT on project-switch failed (non-fatal): {e}")

        # 4. SESSION CONTINUITY: Update global session registry with new project
        # Sessions are per-conversation (global), not per-project.
        # Project-switch just updates which project the session is working on.
        attached_session = None
        try:
            from empirica.data.repositories.sessions import update_session_project
            from empirica.core.statusline_cache import get_instance_id
            import sqlite3

            current_instance_id = get_instance_id()

            # Get current session from global registry
            workspace_db = Path.home() / '.empirica' / 'workspace' / 'workspace.db'
            if workspace_db.exists():
                conn = sqlite3.connect(str(workspace_db))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Find active session for this instance
                if current_instance_id:
                    cursor.execute("""
                        SELECT session_id, ai_id, created_at
                        FROM global_sessions
                        WHERE instance_id = ? AND status = 'active'
                        ORDER BY last_activity DESC NULLS LAST, created_at DESC
                        LIMIT 1
                    """, (current_instance_id,))
                else:
                    # Fallback: most recent active session
                    cursor.execute("""
                        SELECT session_id, ai_id, created_at
                        FROM global_sessions
                        WHERE status = 'active'
                        ORDER BY last_activity DESC NULLS LAST, created_at DESC
                        LIMIT 1
                    """)

                row = cursor.fetchone()
                if row:
                    attached_session = {
                        'session_id': row['session_id'],
                        'ai_id': row['ai_id'],
                        'start_time': row['created_at']
                    }
                    # Update the session's current project in global registry
                    update_session_project(row['session_id'], project_id)
                conn.close()

            # 4b. ENSURE SESSION EXISTS IN TARGET PROJECT'S DB
            # The session from global_sessions may not exist in the target project's
            # per-project sessions.db (it was created in a different project).
            # The statusline reads from per-project DB, so a missing session = "inactive".
            if attached_session and project_path:
                try:
                    target_db_path = Path(project_path) / '.empirica' / 'sessions' / 'sessions.db'
                    if target_db_path.exists():
                        target_conn = sqlite3.connect(str(target_db_path))
                        target_cursor = target_conn.cursor()

                        # Check if session already exists in target DB
                        target_cursor.execute(
                            "SELECT session_id FROM sessions WHERE session_id = ?",
                            (attached_session['session_id'],)
                        )
                        if not target_cursor.fetchone():
                            # Session doesn't exist in target — mirror it
                            from datetime import datetime, timezone
                            target_cursor.execute("""
                                INSERT INTO sessions (
                                    session_id, ai_id, start_time, bootstrap_level,
                                    components_loaded, project_id, instance_id
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                attached_session['session_id'],
                                attached_session['ai_id'],
                                attached_session.get('start_time') or datetime.now(timezone.utc).isoformat(),
                                1,  # bootstrap_level
                                0,  # components_loaded
                                project_id,
                                current_instance_id
                            ))
                            target_conn.commit()
                            if output_format == 'human':
                                print(f"📎 Session mirrored to target project database")
                        else:
                            # Session exists but may have wrong project_id — update it
                            target_cursor.execute(
                                "UPDATE sessions SET project_id = ? WHERE session_id = ?",
                                (project_id, attached_session['session_id'])
                            )
                            target_conn.commit()
                        target_conn.close()
                except Exception as e2:
                    logger.debug(f"Session mirroring to target DB failed (non-fatal): {e2}")
        except Exception as e:
            logger.debug(f"Session continuity update failed (non-fatal): {e}")

        # 5. Update active_work.json for cross-project continuity
        # This ensures pre-compact hook preserves project context even when Claude Code resets CWD
        # Include empirica_session_id so Sentinel and MCP tools can attach to the correct session
        if project_path:
            attached_session_id = attached_session['session_id'] if attached_session else None
            _update_active_work(str(project_path), folder_name, empirica_session_id=attached_session_id, claude_session_id=cli_claude_session_id)

        # 6. Show context banner
        if output_format == 'human':
            print()
            print("━" * 70)
            print("🎯 PROJECT CONTEXT SWITCH")
            print("━" * 70)
            print()
            print(f"📁 Project: {folder_name}")
            if project_name != folder_name:
                print(f"   Name: {project_name}")
            print(f"🆔 Project ID: {project_id[:8]}...")
            if project_path:
                print(f"📍 Location: {project_path}")
            print(f"📊 Findings: {project.get('total_findings', 0)}  "
                  f"Unknowns: {project.get('total_unknowns', 0)}  "
                  f"Goals: {project.get('total_goals', 0)}")
            if attached_session:
                print(f"🔗 Attached to session: {attached_session['session_id'][:8]}... (AI: {attached_session['ai_id']})")
            print()

        # 7. AUTO-BOOTSTRAP: Load context for the new project
        bootstrap_result = None
        try:
            import subprocess
            # Run project-bootstrap for the new project
            # Use --output json to capture result, but don't print it in human mode
            # If we found an attached session, pass it to bootstrap
            bootstrap_cmd = ['empirica', 'project-bootstrap', '--output', 'json']
            if attached_session:
                bootstrap_cmd.extend(['--session-id', attached_session['session_id']])
            if project_path:
                # Run in project directory to ensure correct context
                result = subprocess.run(
                    bootstrap_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(project_path)
                )
                if result.returncode == 0:
                    try:
                        import json as _json
                        bootstrap_result = _json.loads(result.stdout)
                        if output_format == 'human':
                            print("✅ Project context loaded (auto-bootstrap)")
                    except:
                        bootstrap_result = {"ok": True, "note": "bootstrap ran but non-JSON output"}
                else:
                    bootstrap_result = {"ok": False, "error": result.stderr[:200]}
        except Exception as e:
            # Non-fatal - continue even if bootstrap fails
            bootstrap_result = {"ok": False, "error": str(e)}
            logger.debug(f"Auto-bootstrap on project-switch failed (non-fatal): {e}")

        # 6. Show project context summary from workspace data
        if output_format == 'human':
            findings = project.get('total_findings', 0)
            unknowns = project.get('total_unknowns', 0)
            dead_ends = project.get('total_dead_ends', 0)
            goals = project.get('total_goals', 0)

            if findings or unknowns or goals:
                print("📋 Project Context Summary:")
                print()
                if findings:
                    print(f"   📝 {findings} findings logged")
                if unknowns:
                    print(f"   ❓ {unknowns} unknowns tracked")
                if dead_ends:
                    print(f"   🚫 {dead_ends} dead-ends recorded")
                if goals:
                    print(f"   🎯 {goals} goals defined")
                print()
            else:
                print("📋 No epistemic artifacts yet in this project.")
                print()

            # Suggest running bootstrap in project directory for full context
            if project_path and project_path.exists():
                print(f"💡 For full context, run in project directory:")
                print(f"   cd {project_path} && empirica project-bootstrap")
                print()
        
        # 6. Show next steps
        if output_format == 'human':
            print()
            print("━" * 70)
            print("💡 Next Steps")
            print("━" * 70)
            print()
            print("  1. Start a transaction (PREFLIGHT) to begin measured work")
            print()
            print("  2. Investigate before acting — log findings, unknowns, dead-ends")
            print()
            print("  3. CHECK when ready to proceed, POSTFLIGHT when work is complete")
            print()
            print("⚠️  All commands now write to this project's database.")
            print("    Findings, sessions, goals → stored in this project context.")
            print()
        elif output_format == 'json':
            result = {
                'ok': True,
                'project_id': project_id,
                'project_name': project_name,
                'folder_name': folder_name,
                'project_path': str(project_path) if project_path else None,
                'stats': {
                    'findings': project.get('total_findings', 0),
                    'unknowns': project.get('total_unknowns', 0),
                    'goals': project.get('total_goals', 0)
                },
                'next_steps': [
                    'Run PREFLIGHT to start a measured transaction',
                    'Investigate before acting — log findings and unknowns',
                    'CHECK when ready, POSTFLIGHT when complete'
                ],
                'postflight_result': postflight_result,
                'attached_session': attached_session,
                'bootstrap_result': bootstrap_result
            }
            print(json.dumps(result, indent=2))
        
        return None
        
    except Exception as e:
        logger.exception(f"Error in project-switch: {e}")
        if output_format == 'json':
            print(json.dumps({'ok': False, 'error': str(e)}))
        else:
            print(f"❌ Error switching project: {e}")
        return None
