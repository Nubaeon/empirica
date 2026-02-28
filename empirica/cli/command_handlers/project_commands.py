"""
Project Commands - Multi-repo/multi-session project tracking
"""

import json
import logging
import os
import sqlite3
import subprocess
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


def ensure_workspace_schema(conn) -> None:
    """Create workspace tables if they don't exist.

    Called before any workspace.db operations to ensure the schema is present.
    This makes workspace-init and project-list work on fresh installs without
    requiring a separate schema migration step.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            trajectory_path TEXT NOT NULL UNIQUE,
            git_remote_url TEXT,
            git_branch TEXT DEFAULT 'main',
            total_transactions INTEGER DEFAULT 0,
            total_findings INTEGER DEFAULT 0,
            total_unknowns INTEGER DEFAULT 0,
            total_dead_ends INTEGER DEFAULT 0,
            total_goals INTEGER DEFAULT 0,
            last_transaction_id TEXT,
            last_transaction_timestamp REAL,
            last_sync_timestamp REAL,
            status TEXT DEFAULT 'active',
            project_type TEXT DEFAULT 'product',
            project_tags TEXT,
            created_timestamp REAL NOT NULL,
            updated_timestamp REAL NOT NULL,
            metadata TEXT
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_projects_status
        ON global_projects(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_projects_type
        ON global_projects(project_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_projects_last_tx
        ON global_projects(last_transaction_timestamp)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instance_bindings (
            instance_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            project_path TEXT,
            bound_timestamp REAL NOT NULL,
            FOREIGN KEY (project_id) REFERENCES global_projects(id)
        )
    """)
    # Global session registry — enables cross-project session tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sessions (
            session_id TEXT PRIMARY KEY,
            ai_id TEXT,
            origin_project_id TEXT,
            current_project_id TEXT,
            instance_id TEXT,
            status TEXT DEFAULT 'active',
            parent_session_id TEXT,
            created_at REAL,
            last_activity REAL,
            FOREIGN KEY (origin_project_id) REFERENCES global_projects(id),
            FOREIGN KEY (current_project_id) REFERENCES global_projects(id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_sessions_instance
        ON global_sessions(instance_id, status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_sessions_project
        ON global_sessions(current_project_id)
    """)
    # Entity-artifact cross-references — links artifacts to CRM entities
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entity_artifacts (
            id TEXT PRIMARY KEY,
            artifact_type TEXT NOT NULL,
            artifact_id TEXT NOT NULL,
            artifact_source TEXT,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            relationship TEXT DEFAULT 'about',
            relevance REAL DEFAULT 1.0,
            discovered_via TEXT,
            engagement_id TEXT,
            transaction_id TEXT,
            created_at REAL,
            created_by_ai TEXT,
            UNIQUE(artifact_type, artifact_id, entity_type, entity_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_artifacts_entity
        ON entity_artifacts(entity_type, entity_id)
    """)
    conn.commit()


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
        ensure_workspace_schema(conn)
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

        # Fallback 3: Read instance_id from TTY session file.
        # The TTY session stores instance_id from a prior hook that had TMUX_PANE.
        # This handles the case where Bash tool has no TMUX_PANE AND claude_session_id
        # is null (e.g., session-create doesn't write claude_session_id to TTY file).
        if not instance_id and tty_session:
            instance_id = tty_session.get('instance_id')
            if instance_id:
                logger.debug(f"Resolved instance_id={instance_id} from TTY session file")

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
        # Two formats exist:
        # 1. Old format: /home/user/project/.empirica -> project_path = /home/user/project
        # 2. New format: /home/user/project (no .empirica suffix) -> use as-is
        project_path = None
        if trajectory_path:
            traj = Path(trajectory_path)
            if traj.name == '.empirica':
                # Old format: path ends with .empirica, take parent
                project_path = traj.parent
            else:
                # New format: path is the project root directly
                project_path = traj

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
                            # Transaction is for a different project — abandon it.
                            # We do NOT submit fake POSTFLIGHT vectors because that
                            # poisons calibration data. The delta is lost, but a lost
                            # delta is better than a fabricated one.
                            tx_id = tx_data.get('transaction_id', 'unknown')
                            try:
                                tx_path.unlink()
                            except Exception:
                                pass
                            postflight_result = {
                                "ok": True,
                                "reason": "transaction_abandoned",
                                "transaction_id": tx_id,
                                "note": "Transaction abandoned on project-switch (no fake vectors submitted). Submit POSTFLIGHT before switching to preserve deltas."
                            }
                            if output_format == 'human':
                                print(f"⚠️  Previous transaction abandoned (submit POSTFLIGHT before switching to preserve deltas)")
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

        # 4c. ENSURE PROJECT EXISTS IN TARGET'S LOCAL projects TABLE
        # Domain projects created via redistribution/workspace.db may have an empty
        # local projects table, causing finding-log, project-bootstrap, and other
        # commands to fail with "Project not found". Fix: auto-populate from workspace.db.
        if project_path and project_id:
            try:
                target_db_path = Path(project_path) / '.empirica' / 'sessions' / 'sessions.db'
                if target_db_path.exists():
                    target_conn = sqlite3.connect(str(target_db_path))
                    target_cursor = target_conn.cursor()

                    # Check if project already exists in target's local projects table
                    target_cursor.execute(
                        "SELECT id FROM projects WHERE id = ?",
                        (project_id,)
                    )
                    if not target_cursor.fetchone():
                        # Project missing from local DB — populate from workspace.db metadata
                        import time
                        now = time.time()
                        project_description = project.get('description', '')
                        proj_type = project.get('project_type', 'product')
                        proj_tags = project.get('project_tags', '')
                        created_ts = project.get('created_timestamp', now)

                        target_cursor.execute("""
                            INSERT INTO projects (
                                id, name, description, repos, created_timestamp,
                                last_activity_timestamp, status, metadata,
                                total_sessions, total_goals, total_epistemic_deltas,
                                project_data, project_type, project_tags, parent_project_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            project_id,
                            project_name or folder_name,
                            project_description,
                            None,  # repos
                            created_ts,
                            now,  # last_activity_timestamp
                            'active',
                            None,  # metadata
                            0,  # total_sessions
                            0,  # total_goals
                            None,  # total_epistemic_deltas
                            '{}',  # project_data (required NOT NULL)
                            proj_type,
                            proj_tags,
                            None  # parent_project_id
                        ))
                        target_conn.commit()
                        if output_format == 'human':
                            print(f"📦 Project record created in local database")
                    target_conn.close()
            except Exception as e3:
                logger.debug(f"Local projects table population failed (non-fatal): {e3}")

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

        # 8. NO AUTO-PREFLIGHT: The AI must submit its own PREFLIGHT with genuine
        # self-assessed vectors. System-generated vectors poison calibration data.
        # The Sentinel will nudge the AI to submit PREFLIGHT when it detects
        # no open transaction after project-switch.
        preflight_result = {
            "needed": True,
            "note": "Submit PREFLIGHT with your own vector self-assessment to open a transaction."
        }
        if output_format == 'human':
            print("📋 Submit PREFLIGHT to open a transaction (self-assess your vectors)")

        # 9. Show project context summary from workspace data
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
        
        # 10. Show next steps
        if output_format == 'human':
            print()
            print("━" * 70)
            print("💡 Next Steps")
            print("━" * 70)
            print()
            if preflight_result and preflight_result.get('ok'):
                print("  Transaction is open — you're in noetic phase.")
                print()
                print("  1. Investigate — log findings, unknowns, dead-ends")
                print()
                print("  2. CHECK when ready to act, POSTFLIGHT when work is complete")
            else:
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
                'bootstrap_result': bootstrap_result,
                'preflight_result': preflight_result
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
