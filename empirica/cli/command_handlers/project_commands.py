"""
Project Commands - Multi-repo/multi-session project tracking
"""

import json
import logging
from typing import Optional, Literal
from ..cli_utils import handle_cli_error
from empirica.core.memory_gap_detector import MemoryGapDetector

logger = logging.getLogger(__name__)


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

        # Auto-detect project from git remote URL if not provided
        if not project_id:
            try:
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    git_url = result.stdout.strip()
                    # Find project by matching repo URL
                    db = SessionDatabase()
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT id FROM projects WHERE repos LIKE ?
                    """, (f'%{git_url}%',))
                    row = cursor.fetchone()
                    if row:
                        project_id = row['id']
                    db.close()

                    if not project_id:
                        return _error_output(
                            f"No project found for git remote: {git_url}",
                            "Create a project or specify --project-id explicitly"
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

            # Find latest pre_summary snapshot
            ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
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
            skills_dir = os.path.join(os.getcwd(), 'project_skills')
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

        result = {
            "ok": True,
            "scope": scope,
            "findings": [{"scope": s, "finding_id": fid} for s, fid in finding_ids],
            "project_id": project_id if project_id else None,
            "embedded": embedded,
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
