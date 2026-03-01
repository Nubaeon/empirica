"""
Artifact Log Commands - Noetic artifact logging (findings, unknowns, dead-ends, etc.)

Split from project_commands.py for maintainability.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from ..cli_utils import handle_cli_error
from .project_commands import get_workspace_db_path

logger = logging.getLogger(__name__)


def _create_entity_artifact_link(
    artifact_type: str,
    artifact_id: str,
    entity_type: str,
    entity_id: str,
    project_path: Optional[str] = None,
    discovered_via: Optional[str] = None,
    transaction_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
):
    """Create cross-reference in workspace.db entity_artifacts table.

    Called after artifact insert when entity_type is not 'project'.
    Links artifacts in sessions.db to entities (org, contact, engagement)
    in workspace.db for cross-entity discovery.
    """
    if not entity_type or entity_type == 'project':
        return  # No cross-link needed for project-scoped artifacts

    import time
    import uuid

    workspace_db = get_workspace_db_path()
    if not workspace_db.exists():
        logger.debug("Workspace DB not found, skipping entity_artifacts link")
        return

    # Resolve artifact_source (trajectory_path for this project)
    if not project_path:
        try:
            from empirica.utils.session_resolver import get_active_project_path
            project_path = get_active_project_path()
        except Exception:
            pass

    # artifact_source = trajectory_path (.empirica dir), NOT full sessions.db path
    # EntityArtifactStore._populate_content() appends /sessions/sessions.db
    artifact_source = str(Path(project_path) / '.empirica') if project_path else None

    try:
        conn = sqlite3.connect(str(workspace_db))
        conn.execute("""
            INSERT OR IGNORE INTO entity_artifacts (
                id, artifact_type, artifact_id, artifact_source,
                entity_type, entity_id, relationship, relevance,
                discovered_via, engagement_id, transaction_id,
                created_at, created_by_ai
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            artifact_type,
            artifact_id,
            artifact_source,
            entity_type,
            entity_id,
            'about',  # default relationship
            1.0,
            discovered_via,
            engagement_id,
            transaction_id,
            time.time(),
            'claude-code',
        ))
        conn.commit()
        conn.close()
        logger.info(f"🔗 Entity artifact linked: {artifact_type} → {entity_type}/{entity_id[:8]}...")
    except Exception as e:
        logger.debug(f"Entity artifact link failed (non-fatal): {e}")


def _extract_entity_params(config_data, args):
    """Extract entity_type, entity_id, via from config or CLI args.

    Returns (entity_type, entity_id, via) tuple.
    """
    if config_data:
        entity_type = config_data.get('entity_type')
        entity_id = config_data.get('entity_id')
        via = config_data.get('via')
    else:
        entity_type = getattr(args, 'entity_type', None)
        entity_id = getattr(args, 'entity_id', None)
        via = getattr(args, 'via', None)
    return entity_type, entity_id, via

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

        # Entity scoping (cross-entity provenance)
        entity_type, entity_id, via = _extract_entity_params(config_data, args)

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
            transaction_id=transaction_id,
            entity_type=entity_type,
            entity_id=entity_id
        )

        # ENTITY CROSS-LINK: If entity is not project, create workspace.db link
        if entity_type and entity_type != 'project' and entity_id:
            _create_entity_artifact_link(
                artifact_type='finding',
                artifact_id=finding_id,
                entity_type=entity_type,
                entity_id=entity_id,
                discovered_via=via,
                transaction_id=transaction_id,
            )

        # Get ai_id from session for git notes
        ai_id = 'claude-code'  # Default
        try:
            cursor = db.conn.cursor()
            cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row['ai_id']:
                ai_id = row['ai_id']
        except Exception:
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
            "entity_type": entity_type or 'project',
            "entity_id": entity_id,
            "via": via,
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

        # Entity scoping (cross-entity provenance)
        entity_type, entity_id, via = _extract_entity_params(config_data, args)

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
            transaction_id=transaction_id,
            entity_type=entity_type,
            entity_id=entity_id
        )

        # ENTITY CROSS-LINK: If entity is not project, create workspace.db link
        if entity_type and entity_type != 'project' and entity_id:
            _create_entity_artifact_link(
                artifact_type='unknown',
                artifact_id=unknown_id,
                entity_type=entity_type,
                entity_id=entity_id,
                discovered_via=via,
                transaction_id=transaction_id,
            )

        # Get ai_id from session for git notes
        ai_id = 'claude-code'  # Default
        try:
            cursor = db.conn.cursor()
            cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row['ai_id']:
                ai_id = row['ai_id']
        except Exception:
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

        # Entity scoping (cross-entity provenance)
        entity_type, entity_id, via = _extract_entity_params(config_data, args)

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
            transaction_id=transaction_id,
            entity_type=entity_type,
            entity_id=entity_id
        )

        # ENTITY CROSS-LINK: If entity is not project, create workspace.db link
        if entity_type and entity_type != 'project' and entity_id:
            _create_entity_artifact_link(
                artifact_type='dead_end',
                artifact_id=dead_end_id,
                entity_type=entity_type,
                entity_id=entity_id,
                discovered_via=via,
                transaction_id=transaction_id,
            )

        # Get ai_id from session for git notes
        ai_id = 'claude-code'  # Default
        try:
            cursor = db.conn.cursor()
            cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row['ai_id']:
                ai_id = row['ai_id']
        except Exception:
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

        # Entity scoping (cross-entity provenance)
        entity_type, entity_id, via = _extract_entity_params(config_data, args)

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

        # Default entity scope
        resolved_entity_type = entity_type or 'project'
        resolved_entity_id = entity_id or (project_id if resolved_entity_type == 'project' else None)

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
                    entity_type=resolved_entity_type,
                    entity_id=resolved_entity_id,
                    session_id=session_id,
                    transaction_id=transaction_id,
                    domain=domain,
                    timestamp=time.time(),
                )
                embedded = True
        except Exception as e:
            logger.debug(f"Qdrant embed failed (non-fatal): {e}")

        # ENTITY CROSS-LINK: If entity is not project, create workspace.db link
        if entity_type and entity_type != 'project' and entity_id:
            _create_entity_artifact_link(
                artifact_type='assumption',
                artifact_id=assumption_id,
                entity_type=entity_type,
                entity_id=entity_id,
                discovered_via=via,
                transaction_id=transaction_id,
            )

        result = {
            "ok": True,
            "assumption_id": assumption_id,
            "project_id": project_id,
            "entity_type": resolved_entity_type,
            "entity_id": resolved_entity_id,
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

        # Entity scoping (cross-entity provenance)
        entity_type, entity_id, via = _extract_entity_params(config_data, args)

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

        # Default entity scope
        resolved_entity_type = entity_type or 'project'
        resolved_entity_id = entity_id or (project_id if resolved_entity_type == 'project' else None)

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
                    entity_type=resolved_entity_type,
                    entity_id=resolved_entity_id,
                    session_id=session_id,
                    transaction_id=transaction_id,
                    timestamp=time.time(),
                )
                embedded = True
        except Exception as e:
            logger.debug(f"Qdrant embed failed (non-fatal): {e}")

        # ENTITY CROSS-LINK: If entity is not project, create workspace.db link
        if entity_type and entity_type != 'project' and entity_id:
            _create_entity_artifact_link(
                artifact_type='decision',
                artifact_id=decision_id,
                entity_type=entity_type,
                entity_id=entity_id,
                discovered_via=via,
                transaction_id=transaction_id,
            )

        result = {
            "ok": True,
            "decision_id": decision_id,
            "project_id": project_id,
            "entity_type": resolved_entity_type,
            "entity_id": resolved_entity_id,
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

        # Entity scoping (cross-entity provenance)
        entity_type = getattr(args, 'entity_type', None)
        entity_id = getattr(args, 'entity_id', None)
        via = getattr(args, 'via', None)

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

        # Default entity scope
        resolved_entity_type = entity_type or 'project'
        resolved_entity_id = entity_id or (project_id if resolved_entity_type == 'project' else None)

        # Insert into epistemic_sources table
        db.conn.execute("""
            INSERT INTO epistemic_sources (
                id, project_id, session_id, source_type, source_url,
                title, description, confidence, epistemic_layer,
                discovered_by_ai, discovered_at, source_metadata,
                entity_type, entity_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_id, project_id, session_id, source_type,
            source_url or doc_path,
            title, description, confidence, direction,
            'claude-code', time.time(), json.dumps(metadata),
            resolved_entity_type, resolved_entity_id
        ))
        db.conn.commit()

        # ENTITY CROSS-LINK: If entity is not project, create workspace.db link
        if entity_type and entity_type != 'project' and entity_id:
            _create_entity_artifact_link(
                artifact_type='source',
                artifact_id=source_id,
                entity_type=entity_type,
                entity_id=entity_id,
                discovered_via=via,
                transaction_id=transaction_id,
            )

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

