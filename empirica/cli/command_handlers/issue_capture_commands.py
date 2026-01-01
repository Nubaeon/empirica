#!/usr/bin/env python3
"""
CLI commands for auto issue capture system.

Enables AIs to:
  - List captured issues
  - Mark issues for handoff
  - Resolve issues
  - Export for other AIs
"""

import json
import sys
from typing import Optional

from empirica.core.issue_capture import (
    get_auto_capture,
    initialize_auto_capture,
    IssueSeverity,
    IssueCategory,
)


def handle_issue_list_command(args):
    """List captured issues with optional filtering.

    Supports three query modes (dual-scope like findings/unknowns):
    - --session-id: Session-scoped (issues from one session)
    - --project-id: Project-scoped (issues from all sessions in project)
    - Neither: Global (recent issues across all projects)
    """
    try:
        import sqlite3
        from empirica.data.session_database import SessionDatabase

        session_id = getattr(args, 'session_id', None)
        project_id = getattr(args, 'project_id', None)
        status = getattr(args, 'status', None)
        category = getattr(args, 'category', None)
        severity = getattr(args, 'severity', None)
        output = getattr(args, 'output', 'json')
        limit = getattr(args, 'limit', 100)

        # Determine query scope
        scope = 'session' if session_id else ('project' if project_id else 'global')

        if session_id:
            # Session-scoped: use existing service
            service = get_auto_capture()
            if not service or service.session_id != session_id:
                service = initialize_auto_capture(session_id)

            issues = service.list_issues(
                status=status,
                category=category,
                severity=severity,
                limit=limit
            )
        else:
            # Project-scoped or global: direct database query
            db = SessionDatabase()

            # Build query with optional filters
            query = """
                SELECT i.id, i.session_id, i.severity, i.category, i.code_location,
                       i.message, i.stack_trace, i.context, i.status, i.assigned_to_ai,
                       i.root_cause_id, i.resolution, i.created_at, i.updated_at,
                       i.issue_category, s.project_id
                FROM auto_captured_issues i
                JOIN sessions s ON i.session_id = s.session_id
                WHERE 1=1
            """
            params = []

            if project_id:
                query += " AND s.project_id = ?"
                params.append(project_id)

            if status:
                query += " AND i.status = ?"
                params.append(status)

            if category:
                query += " AND i.category = ?"
                params.append(category)

            if severity:
                query += " AND i.severity = ?"
                params.append(severity)

            query += " ORDER BY i.created_at DESC LIMIT ?"
            params.append(limit)

            try:
                with sqlite3.connect(db.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    issues = []
                    for row in rows:
                        issues.append({
                            'id': row['id'],
                            'session_id': row['session_id'],
                            'project_id': row['project_id'],
                            'severity': row['severity'],
                            'category': row['category'],
                            'code_location': row['code_location'],
                            'message': row['message'],
                            'stack_trace': row['stack_trace'],
                            'context': row['context'],
                            'status': row['status'],
                            'assigned_to_ai': row['assigned_to_ai'],
                            'root_cause_id': row['root_cause_id'],
                            'resolution': row['resolution'],
                            'created_at': row['created_at'],
                            'updated_at': row['updated_at'],
                            'issue_category': row['issue_category']
                        })
            except Exception as e:
                issues = []

        if output == 'json':
            result = {
                "ok": True,
                "scope": scope,
                "session_id": session_id,
                "project_id": project_id,
                "issue_count": len(issues),
                "filters": {
                    "status": status,
                    "category": category,
                    "severity": severity
                },
                "issues": issues
            }
            print(json.dumps(result))
        else:
            # Human-readable format
            scope_label = f"session {session_id[:8]}..." if session_id else (
                f"project {project_id[:8]}..." if project_id else "all projects"
            )
            print(f"\n{'='*80}")
            print(f"📋 CAPTURED ISSUES ({len(issues)} total) - {scope_label}")
            print(f"{'='*80}\n")

            if not issues:
                print("✅ No issues found")
                return 0

            for issue in issues:
                severity_emoji = {
                    "blocker": "🚫",
                    "high": "⚠️",
                    "medium": "⚠️",
                    "low": "ℹ️"
                }.get(issue['severity'], "❓")

                print(f"{severity_emoji} {issue['severity'].upper()} - {issue['category']}")
                print(f"   {issue['message'][:100]}")
                print(f"   Location: {issue.get('code_location', 'unknown')}")
                print(f"   Status: {issue['status']}")
                if scope != 'session':
                    print(f"   Session: {issue.get('session_id', 'unknown')[:8]}...")
                if issue.get('assigned_to_ai'):
                    print(f"   Assigned to: {issue['assigned_to_ai']}")
                print()

        return 0

    except Exception as e:
        result = {
            "ok": False,
            "error": str(e)
        }
        print(json.dumps(result))
        return 1


def handle_issue_show_command(args):
    """Show detailed information about a specific issue"""
    try:
        session_id = getattr(args, 'session_id', None)
        issue_id = getattr(args, 'issue_id', None)
        output = getattr(args, 'output', 'json')
        
        if not session_id or not issue_id:
            result = {
                "ok": False,
                "error": "session_id and issue_id are required"
            }
            print(json.dumps(result))
            return 1
        
        # Get service
        service = get_auto_capture()
        if not service or service.session_id != session_id:
            service = initialize_auto_capture(session_id)
        
        # Find issue
        issues = service.list_issues(limit=1000)
        issue = next((i for i in issues if i['id'] == issue_id), None)
        
        if not issue:
            result = {
                "ok": False,
                "error": f"Issue {issue_id} not found"
            }
            print(json.dumps(result))
            return 1
        
        if output == 'json':
            # Parse context if it's JSON string
            try:
                issue['context'] = json.loads(issue['context']) if isinstance(issue['context'], str) else issue['context']
            except:
                pass
            
            result = {
                "ok": True,
                "issue": issue
            }
            print(json.dumps(result))
        else:
            # Human-readable
            print(f"\n{'='*80}")
            print(f"📌 ISSUE: {issue['id']}")
            print(f"{'='*80}\n")
            
            print(f"Severity: {issue['severity'].upper()}")
            print(f"Category: {issue['category']}")
            print(f"Status: {issue['status']}")
            print(f"Location: {issue['code_location']}")
            print(f"Created: {issue['created_at']}")
            if issue['assigned_to_ai']:
                print(f"Assigned to: {issue['assigned_to_ai']}")
            
            print(f"\nMessage:\n  {issue['message']}\n")
            
            if issue['stack_trace']:
                print("Stack Trace:")
                print(issue['stack_trace'][:1000])
                if len(issue['stack_trace']) > 1000:
                    print("... (truncated)")
            
            if issue['context']:
                print(f"\nContext:")
                try:
                    ctx = json.loads(issue['context']) if isinstance(issue['context'], str) else issue['context']
                    for key, value in ctx.items():
                        print(f"  {key}: {value}")
                except:
                    print(f"  {issue['context']}")
        
        return 0
        
    except Exception as e:
        result = {
            "ok": False,
            "error": str(e)
        }
        print(json.dumps(result))
        return 1


def handle_issue_handoff_command(args):
    """Mark issue for handoff to another AI"""
    try:
        session_id = getattr(args, 'session_id', None)
        issue_id = getattr(args, 'issue_id', None)
        assigned_to = getattr(args, 'assigned_to', None)
        output = getattr(args, 'output', 'json')
        
        if not all([session_id, issue_id, assigned_to]):
            result = {
                "ok": False,
                "error": "session_id, issue_id, and assigned_to are required"
            }
            print(json.dumps(result))
            return 1
        
        # Get service
        service = get_auto_capture()
        if not service or service.session_id != session_id:
            service = initialize_auto_capture(session_id)
        
        # Mark for handoff
        success = service.mark_for_handoff(issue_id, assigned_to)
        
        if success:
            result = {
                "ok": True,
                "message": f"Issue {issue_id} marked for handoff to {assigned_to}",
                "issue_id": issue_id,
                "assigned_to": assigned_to
            }
            print(json.dumps(result))
            return 0
        else:
            result = {
                "ok": False,
                "error": f"Failed to mark issue {issue_id} for handoff"
            }
            print(json.dumps(result))
            return 1
            
    except Exception as e:
        result = {
            "ok": False,
            "error": str(e)
        }
        print(json.dumps(result))
        return 1


def handle_issue_resolve_command(args):
    """Mark issue as resolved"""
    try:
        session_id = getattr(args, 'session_id', None)
        issue_id = getattr(args, 'issue_id', None)
        resolution = getattr(args, 'resolution', None)
        output = getattr(args, 'output', 'json')
        
        if not all([session_id, issue_id, resolution]):
            result = {
                "ok": False,
                "error": "session_id, issue_id, and resolution are required"
            }
            print(json.dumps(result))
            return 1
        
        # Get service
        service = get_auto_capture()
        if not service or service.session_id != session_id:
            service = initialize_auto_capture(session_id)
        
        # Mark as resolved
        success = service.resolve_issue(issue_id, resolution)
        
        if success:
            result = {
                "ok": True,
                "message": f"Issue {issue_id} marked as resolved",
                "issue_id": issue_id,
                "resolution": resolution
            }
            print(json.dumps(result))
            return 0
        else:
            result = {
                "ok": False,
                "error": f"Failed to resolve issue {issue_id}"
            }
            print(json.dumps(result))
            return 1
            
    except Exception as e:
        result = {
            "ok": False,
            "error": str(e)
        }
        print(json.dumps(result))
        return 1


def handle_issue_export_command(args):
    """Export issues for handoff to another AI"""
    try:
        session_id = getattr(args, 'session_id', None)
        assigned_to = getattr(args, 'assigned_to', None)
        output = getattr(args, 'output', 'json')
        
        if not all([session_id, assigned_to]):
            result = {
                "ok": False,
                "error": "session_id and assigned_to are required"
            }
            print(json.dumps(result))
            return 1
        
        # Get service
        service = get_auto_capture()
        if not service or service.session_id != session_id:
            service = initialize_auto_capture(session_id)
        
        # Export
        export_data = service.export_for_handoff(assigned_to)
        
        result = {
            "ok": True,
            "export": export_data
        }
        print(json.dumps(result))
        return 0
            
    except Exception as e:
        result = {
            "ok": False,
            "error": str(e)
        }
        print(json.dumps(result))
        return 1


def handle_issue_stats_command(args):
    """Show issue capture statistics"""
    try:
        session_id = getattr(args, 'session_id', None)
        output = getattr(args, 'output', 'json')
        
        if not session_id:
            result = {
                "ok": False,
                "error": "session_id is required"
            }
            print(json.dumps(result))
            return 1
        
        # Get service
        service = get_auto_capture()
        if not service or service.session_id != session_id:
            service = initialize_auto_capture(session_id)
        
        # Get stats
        stats = service.get_stats()
        
        if output == 'json':
            result = {
                "ok": True,
                "stats": stats
            }
            print(json.dumps(result))
        else:
            print(f"\n{'='*80}")
            print(f"📊 ISSUE CAPTURE STATISTICS")
            print(f"{'='*80}\n")
            
            for key, value in stats.items():
                print(f"{key}: {value}")
        
        return 0
            
    except Exception as e:
        result = {
            "ok": False,
            "error": str(e)
        }
        print(json.dumps(result))
        return 1
