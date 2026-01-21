"""
Project Bootstrap Command - Epistemic context loading for AI sessions

Extracted from project_commands.py for maintainability.
This is the largest single command handler (~900 lines) as it handles:
- Project auto-detection (git repo, local config)
- Breadcrumb loading (findings, unknowns, dead-ends, mistakes)
- Epistemic state display (goals, flow metrics, health score)
- Multiple output formats (human, json)
"""

import json
import logging
from ..cli_utils import handle_cli_error
from empirica.core.memory_gap_detector import MemoryGapDetector

logger = logging.getLogger(__name__)


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
            try:
                import yaml
                import os
                project_yaml = os.path.join(os.getcwd(), '.empirica', 'project.yaml')
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


