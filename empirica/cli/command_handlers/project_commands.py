"""
Project Commands - Multi-repo/multi-session project tracking

Note: handle_project_bootstrap_command has been extracted to project_bootstrap.py
for maintainability (it's ~900 lines).
"""

import json
import logging
from typing import Optional, Literal
from ..cli_utils import handle_cli_error
from empirica.core.memory_gap_detector import MemoryGapDetector

# Import extracted bootstrap command
from .project_bootstrap import handle_project_bootstrap_command

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ['handle_project_bootstrap_command', 'infer_scope']


def infer_scope(session_id: Optional[str], project_id: Optional[str], explicit_scope: Optional[str]) -> Literal['session', 'project', 'both']:
    """
    Smart scope inference for dual-scoped logging.
    
    Rules:
    1. If explicit_scope provided → use it
    2. If only session_id → 'session'
    3. If only project_id → 'project'
    4. If both → 'both' (dual-log)
    5. If neither → 'project' (backward compatible default)
    
    Args:
        session_id: Optional session UUID
        project_id: Optional project UUID
        explicit_scope: Optional explicit scope choice
        
    Returns:
        'session', 'project', or 'both'
    """
    if explicit_scope:
        return explicit_scope
    
    has_session = session_id is not None
    has_project = project_id is not None
    
    if has_session and has_project:
        return 'both'  # Dual-log when both provided
    elif has_session:
        return 'session'
    elif has_project:
        return 'project'
    else:
        return 'project'  # Backward compatible default


def handle_project_create_command(args):
    """Handle project-create command"""
    try:
        from empirica.data.session_database import SessionDatabase

        # Parse arguments
        name = args.name
        description = getattr(args, 'description', None)
        repos_str = getattr(args, 'repos', None)
        
        # Parse repos JSON if provided
        repos = None
        if repos_str:
            repos = json.loads(repos_str)

        # Create project
        db = SessionDatabase()
        project_id = db.create_project(
            name=name,
            description=description,
            repos=repos
        )
        db.close()

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "project_id": project_id,
                "name": name,
                "repos": repos or [],
                "message": "Project created successfully"
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Project created successfully")
            print(f"   Project ID: {project_id}")
            print(f"   Name: {name}")
            if description:
                print(f"   Description: {description}")
            if repos:
                print(f"   Repos: {', '.join(repos)}")

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
    """Handle project-list command"""
    try:
        from empirica.data.session_database import SessionDatabase
        
        db = SessionDatabase()
        cursor = db.conn.cursor()
        
        # Get all projects
        cursor.execute("""
            SELECT id, name, description, status, total_sessions, 
                   last_activity_timestamp
            FROM projects
            ORDER BY last_activity_timestamp DESC
        """)
        projects = [dict(row) for row in cursor.fetchall()]
        
        db.close()

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "projects_count": len(projects),
                "projects": projects
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"📁 Found {len(projects)} project(s):\n")
            for i, p in enumerate(projects, 1):
                print(f"{i}. {p['name']} ({p['status']})")
                print(f"   ID: {p['id']}")
                if p['description']:
                    print(f"   Description: {p['description']}")
                print(f"   Sessions: {p['total_sessions']}")
                print()

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Project list", getattr(args, 'verbose', False))
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
            session_id = config_data.get('session_id')
            finding = config_data.get('finding')
            goal_id = config_data.get('goal_id')
            subtask_id = config_data.get('subtask_id')
            impact = config_data.get('impact')  # Optional - auto-derives if None
            output_format = 'json'

            # Validate required fields
            if not project_id or not session_id or not finding:
                print(json.dumps({
                    "ok": False,
                    "error": "Config file must include 'project_id', 'session_id', and 'finding' fields",
                    "hint": "See /tmp/finding_config_example.json for schema"
                }))
                sys.exit(1)
        else:
            # LEGACY MODE
            session_id = args.session_id
            finding = args.finding
            project_id = args.project_id
            goal_id = getattr(args, 'goal_id', None)
            subtask_id = getattr(args, 'subtask_id', None)
            impact = getattr(args, 'impact', None)  # Optional - auto-derives if None
            output_format = getattr(args, 'output', 'json')

            # Validate required fields for legacy mode
            # Allow project_id to be None initially, will auto-resolve below
            if not session_id or not finding:
                print(json.dumps({
                    "ok": False,
                    "error": "Legacy mode requires --session-id and --finding flags",
                    "hint": "Project ID will be auto-resolved if not provided. For AI-first mode, use: empirica finding-log config.json"
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
                # Fallback: try to resolve from current directory
                from empirica.config.project_config_loader import load_project_config
                try:
                    project_config = load_project_config()
                    if project_config and hasattr(project_config, 'project_id'):
                        project_id = project_config.project_id
                        logger.info(f"Auto-resolved project_id from config: {project_id[:8]}...")
                except:
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

        # DUAL-SCOPE LOGIC: Infer scope and log to appropriate table(s)
        explicit_scope = config_data.get('scope') if config_data else getattr(args, 'scope', None)
        scope = infer_scope(session_id, project_id, explicit_scope)
        
        finding_ids = []
        
        if scope in ['session', 'both']:
            # Log to session_findings
            finding_id_session = db.log_session_finding(
                session_id=session_id,
                finding=finding,
                goal_id=goal_id,
                subtask_id=subtask_id,
                subject=subject,
                impact=impact
            )
            finding_ids.append(('session', finding_id_session))
        
        if scope in ['project', 'both']:
            # Log to project_findings (legacy table)
            finding_id_project = db.log_finding(
                project_id=project_id,
                session_id=session_id,
                finding=finding,
                goal_id=goal_id,
                subtask_id=subtask_id,
                subject=subject,
                impact=impact
            )
            finding_ids.append(('project', finding_id_project))
        
        db.close()

        # AUTO-EMBED: Add finding to Qdrant for semantic search
        embedded = False
        if project_id and finding_ids:
            try:
                from empirica.core.qdrant.vector_store import embed_single_memory_item
                from datetime import datetime
                # Use project finding_id if available, else session
                primary_id = next((fid for scope, fid in finding_ids if scope == 'project'), None)
                if not primary_id:
                    primary_id = finding_ids[0][1] if finding_ids else None
                if primary_id:
                    embedded = embed_single_memory_item(
                        project_id=project_id,
                        item_id=primary_id,
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
        if project_id and finding_ids:
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
                    primary_id = next((fid for scope, fid in finding_ids if scope == 'project'), None)
                    if not primary_id:
                        primary_id = finding_ids[0][1] if finding_ids else None

                    eidetic_created = embed_eidetic(
                        project_id=project_id,
                        fact_id=primary_id,
                        content=finding,
                        fact_type="fact",
                        domain=subject,  # Use subject as domain hint
                        confidence=0.5 + (impact * 0.2),  # Higher impact → higher initial confidence
                        confirmation_count=1,
                        source_sessions=[session_id] if session_id else [],
                        source_findings=[primary_id] if primary_id else [],
                        tags=[subject] if subject else [],
                    )
                    if eidetic_created:
                        eidetic_result = "created"
                        logger.debug(f"Created new eidetic fact: {primary_id}")
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
        except Exception as decay_err:
            # Non-fatal - log but continue
            logger.debug(f"Lesson decay check failed: {decay_err}")

        result = {
            "ok": True,
            "scope": scope,
            "findings": [{"scope": s, "finding_id": fid} for s, fid in finding_ids],
            "project_id": project_id if project_id else None,
            "embedded": embedded,
            "eidetic": eidetic_result,  # "created" | "confirmed" | None
            "immune_decay": decayed_lessons if decayed_lessons else None,  # Lessons affected by this finding
            "message": f"Finding logged to {scope} scope{'s' if scope == 'both' else ''}"
        }

        # Format output (AI-first = JSON by default)
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output (legacy)
            print(f"✅ Finding logged successfully")
            if finding_ids:
                for scope, fid in finding_ids:
                    print(f"   Finding ID ({scope}): {fid}")
            if project_id:
                print(f"   Project: {project_id[:8]}...")
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

            if not project_id or not session_id or not unknown:
                print(json.dumps({
                    "ok": False,
                    "error": "Config file must include 'project_id', 'session_id', and 'unknown' fields"
                }))
                sys.exit(1)
        else:
            session_id = args.session_id
            unknown = args.unknown
            project_id = args.project_id
            goal_id = getattr(args, 'goal_id', None)
            subtask_id = getattr(args, 'subtask_id', None)
            impact = getattr(args, 'impact', None)  # Optional - auto-derives if None
            output_format = getattr(args, 'output', 'json')

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
                # Fallback: try to resolve from current directory
                from empirica.config.project_config_loader import load_project_config
                try:
                    project_config = load_project_config()
                    if project_config and hasattr(project_config, 'project_id'):
                        project_id = project_config.project_id
                        logger.info(f"Auto-resolved project_id from config: {project_id[:8]}...")
                except:
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

        # DUAL-SCOPE LOGIC: Infer scope and log to appropriate table(s)
        explicit_scope = config_data.get('scope') if config_data else getattr(args, 'scope', None)
        scope = infer_scope(session_id, project_id, explicit_scope)
        
        unknown_ids = []
        
        if scope in ['session', 'both']:
            # Log to session_unknowns
            unknown_id_session = db.log_session_unknown(
                session_id=session_id,
                unknown=unknown,
                goal_id=goal_id,
                subtask_id=subtask_id,
                subject=subject,
                impact=impact
            )
            unknown_ids.append(('session', unknown_id_session))
        
        if scope in ['project', 'both']:
            # Log to project_unknowns (legacy table)
            unknown_id_project = db.log_unknown(
                project_id=project_id,
                session_id=session_id,
                unknown=unknown,
                goal_id=goal_id,
                subtask_id=subtask_id,
                subject=subject,
                impact=impact
            )
            unknown_ids.append(('project', unknown_id_project))
        
        db.close()

        # AUTO-EMBED: Add unknown to Qdrant for semantic search
        embedded = False
        if project_id and unknown_ids:
            try:
                from empirica.core.qdrant.vector_store import embed_single_memory_item
                from datetime import datetime
                # Use project unknown_id if available, else session
                primary_id = next((uid for scope, uid in unknown_ids if scope == 'project'), None)
                if not primary_id:
                    primary_id = unknown_ids[0][1] if unknown_ids else None
                if primary_id:
                    embedded = embed_single_memory_item(
                        project_id=project_id,
                        item_id=primary_id,
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
            "scope": scope,
            "unknowns": [{"scope": s, "unknown_id": uid} for s, uid in unknown_ids],
            "project_id": project_id if project_id else None,
            "embedded": embedded,
            "message": f"Unknown logged to {scope} scope{'s' if scope == 'both' else ''}"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Unknown logged successfully")
            for scope_name, uid in unknown_ids:
                print(f"   {scope_name.title()} Unknown ID: {uid[:8] if uid else 'N/A'}...")
            if project_id:
                print(f"   Project: {project_id[:8]}...")
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
            session_id = config_data.get('session_id')
            approach = config_data.get('approach')
            why_failed = config_data.get('why_failed')
            goal_id = config_data.get('goal_id')
            subtask_id = config_data.get('subtask_id')
            impact = config_data.get('impact')  # Optional - auto-derives if None
            output_format = 'json'

            if not project_id or not session_id or not approach or not why_failed:
                print(json.dumps({
                    "ok": False,
                    "error": "Config file must include 'project_id', 'session_id', 'approach', and 'why_failed' fields"
                }))
                sys.exit(1)
        else:
            session_id = args.session_id
            approach = args.approach
            why_failed = args.why_failed
            project_id = args.project_id
            goal_id = getattr(args, 'goal_id', None)
            subtask_id = getattr(args, 'subtask_id', None)
            impact = getattr(args, 'impact', None)  # Optional - auto-derives if None
            output_format = getattr(args, 'output', 'json')

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
                # Fallback: try to resolve from current directory
                from empirica.config.project_config_loader import load_project_config
                try:
                    project_config = load_project_config()
                    if project_config and hasattr(project_config, 'project_id'):
                        project_id = project_config.project_id
                        logger.info(f"Auto-resolved project_id from config: {project_id[:8]}...")
                except:
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

        # DUAL-SCOPE LOGIC: Infer scope and log to appropriate table(s)
        explicit_scope = config_data.get('scope') if config_data else getattr(args, 'scope', None)
        scope = infer_scope(session_id, project_id, explicit_scope)
        
        dead_end_ids = []
        
        if scope in ['session', 'both']:
            # Log to session_dead_ends
            dead_end_id_session = db.log_session_dead_end(
                session_id=session_id,
                approach=approach,
                why_failed=why_failed,
                goal_id=goal_id,
                subtask_id=subtask_id,
                subject=subject,
                impact=impact
            )
            dead_end_ids.append(('session', dead_end_id_session))
        
        if scope in ['project', 'both']:
            # Log to project_dead_ends (legacy table)
            dead_end_id_project = db.log_dead_end(
                project_id=project_id,
                session_id=session_id,
                approach=approach,
                why_failed=why_failed,
                goal_id=goal_id,
                subtask_id=subtask_id,
                subject=subject,
                impact=impact
            )
            dead_end_ids.append(('project', dead_end_id_project))
        
        db.close()

        result = {
            "ok": True,
            "scope": scope,
            "dead_ends": [{"scope": s, "dead_end_id": did} for s, did in dead_end_ids],
            "project_id": project_id if project_id else None,
            "message": f"Dead end logged to {scope} scope{'s' if scope == 'both' else ''}"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Dead end logged successfully")
            for scope_name, did in dead_end_ids:
                print(f"   {scope_name.capitalize()} Dead End ID: {did[:8] if did else 'N/A'}...")
            if project_id:
                print(f"   Project: {project_id[:8]}...")

        return 0  # Success

    except Exception as e:
        handle_cli_error(e, "Dead end log", getattr(args, 'verbose', False))
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
                # Fallback: try to resolve from current directory
                from empirica.config.project_config_loader import load_project_config
                try:
                    project_config = load_project_config()
                    if project_config and hasattr(project_config, 'project_id'):
                        project_id = project_config.project_id
                        logger.info(f"Auto-resolved project_id from config: {project_id[:8]}...")
                except:
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
        
        # JSON output
        if output_format == 'json':
            result = {
                "ok": True,
                "parent_directory": str(parent_dir),
                "total_repos": len(git_repos),
                "tracked_repos": sum(1 for r in git_repos if r['empirica_project']),
                "untracked_repos": sum(1 for r in git_repos if not r['empirica_project']),
                "repos": git_repos
            }
            print(json.dumps(result, indent=2))
            return result
        
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
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        print("💡 Quick Commands:")
        print(f"   • View workspace overview:  empirica workspace-overview")
        print(f"   • Bootstrap project:        empirica project-bootstrap --project-id <ID>")
        print()
        
        print(json.dumps({"repos": git_repos}, indent=2))
        return 0
        
    except Exception as e:
        handle_cli_error(e, "Workspace map", getattr(args, 'verbose', False))
        return 1
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
    
    Provides clear UX for AI agents:
    1. Resolves project by name or ID
    2. Shows "you are here" banner
    3. Automatically runs project-bootstrap
    4. Shows next steps
    
    Does NOT create a session (explicit action for user)
    """
    try:
        from empirica.data.session_database import SessionDatabase
        
        project_identifier = args.project_identifier
        output_format = getattr(args, 'output', 'human')
        
        db = SessionDatabase()
        
        # 1. Resolve project (by name or ID)
        project_id = db.projects.resolve_project_id(project_identifier)
        
        if not project_id:
            error_msg = f"Project not found: {project_identifier}"
            hint = "Run 'empirica project-list' to see available projects, or 'empirica project-init' to create one"
            
            if output_format == 'json':
                print(json.dumps({
                    'ok': False,
                    'error': error_msg,
                    'hint': hint
                }))
            else:
                print(f"❌ {error_msg}")
                print(f"\nTip: {hint}")
            
            db.close()
            return None
        
        # 2. Get project details
        project = db.projects.get_project(project_id)
        if not project:
            error_msg = f"Project ID {project_id} not found in database"
            
            if output_format == 'json':
                print(json.dumps({'ok': False, 'error': error_msg}))
            else:
                print(f"❌ {error_msg}")
            
            db.close()
            return None
        
        project_name = project['name']
        repos_raw = project.get('repos')
        repos = []
        if repos_raw and repos_raw.strip():
            try:
                repos = json.loads(repos_raw)
            except json.JSONDecodeError:
                repos = []
        
        # 3. Try to find project git root
        project_path = None
        cwd = Path.cwd()
        
        # Check if we're already in a project directory
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_root = Path(result.stdout.strip())
                
                # Check if this git root matches the project
                try:
                    result = subprocess.run(
                        ['git', 'remote', 'get-url', 'origin'],
                        cwd=git_root,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        current_remote = result.stdout.strip()
                        # Check if current remote matches any project repo
                        if any(repo in current_remote or current_remote in repo for repo in repos):
                            project_path = git_root
                except Exception:
                    pass
        except Exception:
            pass
        
        # If not in project dir, we can't change directory (shell limitation)
        # Just show the context banner and bootstrap data
        
        db.close()
        
        # 4. Show context banner
        if output_format == 'human':
            print()
            print("━" * 70)
            print("🎯 PROJECT CONTEXT SWITCH")
            print("━" * 70)
            print()
            print(f"📁 Project: {project_name}")
            print(f"🆔 Project ID: {project_id[:8]}...")
            if project_path:
                print(f"📍 Location: {project_path}")
            else:
                print(f"📍 Repositories: {', '.join(repos) if repos else 'None configured'}")
            print(f"📊 Database: .empirica/sessions/sessions.db (project-local)")
            print()
        
        # 5. Run project-bootstrap automatically
        if output_format == 'human':
            print("📋 Loading project context...")
            print()
        
        # Import and call bootstrap handler
        from empirica.cli.command_handlers.project_commands import handle_project_bootstrap_command
        
        # Create bootstrap args
        class BootstrapArgs:
            def __init__(self):
                self.project_id = project_id
                self.output = output_format
                self.session_id = None
                self.context_to_inject = False
                self.task_description = None
                self.epistemic_state = None
                self.subject = None
                self.include_live_state = False
                self.trigger = None
                self.depth = 'moderate'  # Balanced depth for switching
                self.ai_id = None
        
        bootstrap_result = handle_project_bootstrap_command(BootstrapArgs())
        
        # 6. Show next steps
        if output_format == 'human':
            print()
            print("━" * 70)
            print("💡 Next Steps")
            print("━" * 70)
            print()
            print("  1. Create a session to start work:")
            print(f"     empirica session-create --ai-id <your-id>")
            print()
            print("  2. Find work matching your capability:")
            print(f"     empirica goals-ready")
            print()
            if project_path:
                print(f"  3. Navigate to project directory:")
                print(f"     cd {project_path}")
                print()
            print("⚠️  All commands now write to this project's database.")
            print("    Findings, sessions, goals → stored in this project context.")
            print()
        elif output_format == 'json':
            result = {
                'ok': True,
                'project_id': project_id,
                'project_name': project_name,
                'repos': repos,
                'project_path': str(project_path) if project_path else None,
                'next_steps': [
                    'empirica session-create --ai-id <your-id>',
                    'empirica goals-ready'
                ],
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
