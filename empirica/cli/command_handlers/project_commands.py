"""
Project Commands - Multi-repo/multi-session project tracking
"""

import json
import logging
from typing import Optional
from ..cli_utils import handle_cli_error

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

        project_id = args.project_id
        
        db = SessionDatabase()
        breadcrumbs = db.bootstrap_project_breadcrumbs(project_id)
        db.close()

        if "error" in breadcrumbs:
            print(f"❌ {breadcrumbs['error']}")
            return None

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

        return {"breadcrumbs": breadcrumbs}

    except Exception as e:
        handle_cli_error(e, "Project bootstrap", getattr(args, 'verbose', False))
        return None


def handle_finding_log_command(args):
    """Handle finding-log command"""
    try:
        from empirica.data.session_database import SessionDatabase

        project_id = args.project_id
        session_id = args.session_id
        finding = args.finding
        goal_id = getattr(args, 'goal_id', None)
        subtask_id = getattr(args, 'subtask_id', None)
        
        db = SessionDatabase()
        finding_id = db.log_finding(
            project_id=project_id,
            session_id=session_id,
            finding=finding,
            goal_id=goal_id,
            subtask_id=subtask_id
        )
        db.close()

        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "finding_id": finding_id,
                "project_id": project_id,
                "message": "Finding logged successfully"
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Finding logged successfully")
            print(f"   Finding ID: {finding_id}")
            print(f"   Project: {project_id[:8]}...")

        return {"finding_id": finding_id}

    except Exception as e:
        handle_cli_error(e, "Finding log", getattr(args, 'verbose', False))
        return None


def handle_unknown_log_command(args):
    """Handle unknown-log command"""
    try:
        from empirica.data.session_database import SessionDatabase

        project_id = args.project_id
        session_id = args.session_id
        unknown = args.unknown
        goal_id = getattr(args, 'goal_id', None)
        subtask_id = getattr(args, 'subtask_id', None)
        
        db = SessionDatabase()
        unknown_id = db.log_unknown(
            project_id=project_id,
            session_id=session_id,
            unknown=unknown,
            goal_id=goal_id,
            subtask_id=subtask_id
        )
        db.close()

        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "unknown_id": unknown_id,
                "project_id": project_id,
                "message": "Unknown logged successfully"
            }
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
    """Handle deadend-log command"""
    try:
        from empirica.data.session_database import SessionDatabase

        project_id = args.project_id
        session_id = args.session_id
        approach = args.approach
        why_failed = args.why_failed
        goal_id = getattr(args, 'goal_id', None)
        subtask_id = getattr(args, 'subtask_id', None)
        
        db = SessionDatabase()
        dead_end_id = db.log_dead_end(
            project_id=project_id,
            session_id=session_id,
            approach=approach,
            why_failed=why_failed,
            goal_id=goal_id,
            subtask_id=subtask_id
        )
        db.close()

        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "dead_end_id": dead_end_id,
                "project_id": project_id,
                "message": "Dead end logged successfully"
            }
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

        project_id = args.project_id
        doc_path = args.doc_path
        doc_type = getattr(args, 'doc_type', None)
        description = getattr(args, 'description', None)
        
        db = SessionDatabase()
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
