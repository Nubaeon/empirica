"""
Project Commands - Multi-repo/multi-session project tracking
"""

import json
import logging
from typing import Optional
from ..cli_utils import handle_cli_error
from empirica.core.memory_gap_detector import MemoryGapDetector

logger = logging.getLogger(__name__)


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

        return {"project_id": project_id}

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

        return {"handoff_id": handoff_id, "total_deltas": total_deltas}

    except Exception as e:
        handle_cli_error(e, "Project handoff", getattr(args, 'verbose', False))
        return None


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

        return {"projects": projects}

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

        project_id = getattr(args, 'project_id', None)
        
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
                        print(f"❌ Error: No project found for git remote: {git_url}")
                        print(f"\nTip: Create a project or specify --project-id explicitly")
                        return None
                else:
                    print(f"❌ Error: Not in a git repository or no remote 'origin' configured")
                    print(f"\nTip: Run 'git remote add origin <url>' or use --project-id")
                    return None
            except Exception as e:
                print(f"❌ Error auto-detecting project: {e}")
                print(f"\nTip: Use --project-id to specify project explicitly")
                return None
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
        breadcrumbs = db.bootstrap_project_breadcrumbs(
            project_id,
            check_integrity=check_integrity,
            context_to_inject=context_to_inject,
            task_description=task_description,
            epistemic_state=epistemic_state,
            subject=subject
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
            print(json.dumps(result, indent=2))
        else:
            project = breadcrumbs['project']
            last = breadcrumbs['last_activity']
            
            print(f"📋 Project Context: {project['name']}")
            print(f"   {project['description']}")
            print(f"   Repos: {', '.join(project['repos'])}")
            print(f"   Total sessions: {project['total_sessions']}")
            print()
            
            print(f"🕐 Last Activity:")
            print(f"   {last['summary']}")
            print(f"   Next focus: {last['next_focus']}")
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
                    print(f"   {i}. {m['mistake']} (cost: {m['cost']}, cause: {m['root_cause']})")
                    print(f"      → {m['prevention']}")
                print()
            
            if breadcrumbs['key_decisions']:
                print(f"💡 Key Decisions:")
                for i, d in enumerate(breadcrumbs['key_decisions'], 1):
                    print(f"   {i}. {d}")
                print()
            
            if breadcrumbs.get('reference_docs'):
                print(f"📄 Reference Docs:")
                for i, doc in enumerate(breadcrumbs['reference_docs'][:5], 1):
                    print(f"   {i}. {doc['path']} ({doc['type']})")
                    if doc['description']:
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
            
            if breadcrumbs['incomplete_work']:
                print(f"🎯 Incomplete Work:")
                for i, w in enumerate(breadcrumbs['incomplete_work'], 1):
                    print(f"   {i}. {w['goal']} ({w['progress']})")
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

        return {"breadcrumbs": breadcrumbs}

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
            output_format = getattr(args, 'output', 'json')

            # Validate required fields for legacy mode
            if not project_id or not session_id or not finding:
                print(json.dumps({
                    "ok": False,
                    "error": "Legacy mode requires --project-id, --session-id, and --finding flags",
                    "hint": "For AI-first mode, use: empirica finding-log config.json"
                }))
                sys.exit(1)

        # Auto-detect subject from current directory
        from empirica.config.project_config_loader import get_current_subject
        subject = config_data.get('subject') if config_data else getattr(args, 'subject', None)
        if subject is None:
            subject = get_current_subject()  # Auto-detect from directory
        
        db = SessionDatabase()

        # Resolve project name to UUID
        project_id = resolve_project_id(project_id, db)
        
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

        finding_id = db.log_finding(
            project_id=project_id,
            session_id=session_id,
            finding=finding,
            goal_id=goal_id,
            subtask_id=subtask_id,
            subject=subject
        )
        db.close()

        result = {
            "ok": True,
            "finding_id": finding_id,
            "project_id": project_id,
            "message": "Finding logged successfully"
        }

        # Format output (AI-first = JSON by default)
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output (legacy)
            print(f"✅ Finding logged successfully")
            print(f"   Finding ID: {finding_id}")
            print(f"   Project: {project_id[:8]}...")

        return {"finding_id": finding_id}

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
            output_format = getattr(args, 'output', 'json')

        # Auto-detect subject from current directory
        from empirica.config.project_config_loader import get_current_subject
        subject = config_data.get('subject') if config_data else getattr(args, 'subject', None)
        if subject is None:
            subject = get_current_subject()  # Auto-detect from directory
        
        db = SessionDatabase()

        # Resolve project name to UUID
        project_id = resolve_project_id(project_id, db)
        
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

        unknown_id = db.log_unknown(
            project_id=project_id,
            session_id=session_id,
            unknown=unknown,
            goal_id=goal_id,
            subtask_id=subtask_id,
            subject=subject
        )
        db.close()

        result = {
            "ok": True,
            "unknown_id": unknown_id,
            "project_id": project_id,
            "message": "Unknown logged successfully"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Unknown logged successfully")
            print(f"   Unknown ID: {unknown_id}")
            print(f"   Project: {project_id[:8]}...")

        return {"unknown_id": unknown_id}

    except Exception as e:
        handle_cli_error(e, "Unknown log", getattr(args, 'verbose', False))
        return None


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
            output_format = getattr(args, 'output', 'json')

        # Auto-detect subject from current directory
        from empirica.config.project_config_loader import get_current_subject
        subject = config_data.get('subject') if config_data else getattr(args, 'subject', None)
        if subject is None:
            subject = get_current_subject()  # Auto-detect from directory
        
        db = SessionDatabase()

        # Resolve project name to UUID
        project_id = resolve_project_id(project_id, db)
        
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

        dead_end_id = db.log_dead_end(
            project_id=project_id,
            session_id=session_id,
            approach=approach,
            why_failed=why_failed,
            goal_id=goal_id,
            subtask_id=subtask_id,
            subject=subject
        )
        db.close()

        result = {
            "ok": True,
            "dead_end_id": dead_end_id,
            "project_id": project_id,
            "message": "Dead end logged successfully"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Dead end logged successfully")
            print(f"   Dead End ID: {dead_end_id}")
            print(f"   Project: {project_id[:8]}...")

        return {"dead_end_id": dead_end_id}

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

        # Resolve project name to UUID
        project_id = resolve_project_id(project_id, db)

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

        return {"doc_id": doc_id}

    except Exception as e:
        handle_cli_error(e, "Reference doc add", getattr(args, 'verbose', False))
        return None
