"""
Utility Commands - General purpose CLI commands for feedback, calibration, etc.
"""

import json
import logging
import time
from typing import Dict, Any
from ..cli_utils import print_component_status, handle_cli_error, parse_json_safely

# Set up logging for utility commands
logger = logging.getLogger(__name__)


def handle_sessions_list_command(args):
    """List all sessions"""
    try:
        from ..cli_utils import print_header
        
        # Check if JSON output requested
        output_json = getattr(args, 'output', None) == 'json'
        
        if not output_json:
            print_header("📋 Empirica Sessions")
        
        from empirica.data.session_database import SessionDatabase
        from datetime import datetime
        
        db = SessionDatabase()
        
        # Query sessions
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT session_id, ai_id, start_time, end_time,
                   (SELECT COUNT(*) FROM cascades WHERE cascades.session_id = sessions.session_id) as cascade_count
            FROM sessions
            ORDER BY start_time DESC
            LIMIT ?
        """, (args.limit,))
        
        sessions = cursor.fetchall()
        
        # JSON output
        if output_json:
            output = {
                "sessions": [
                    {
                        "session_id": s[0],
                        "ai_id": s[1],
                        "start_time": s[2],
                        "end_time": s[3],
                        "cascade_count": s[4],
                        "status": "complete" if s[3] and s[3] != 'None' else "active"
                    }
                    for s in sessions
                ],
                "total": len(sessions)
            }
            
            print(json.dumps(output, indent=2, default=str))
            db.close()
            return
        
        if not sessions:
            print("\n📭 No sessions found")
            print("💡 Sessions are created when you run preflight or cascade commands")
            db.close()
            return
        
        print(f"\n📊 Found {len(sessions)} session(s):\n")
        
        for session in sessions:
            session_id, ai_id, start_time, end_time, cascade_count = session
            
            # Parse timestamps
            started = datetime.fromisoformat(start_time) if start_time else None
            ended = datetime.fromisoformat(end_time) if end_time and end_time != 'None' else None
            
            # Status indicator
            status = "✅ Complete" if ended else "🔄 Active"
            
            print(f"  🆔 {session_id}")
            print(f"     AI: {ai_id}")
            print(f"     Started: {started.strftime('%Y-%m-%d %H:%M:%S') if started else 'Unknown'}")
            if ended:
                duration = (ended - started).total_seconds() if started else 0
                print(f"     Ended: {ended.strftime('%Y-%m-%d %H:%M:%S')} ({duration:.1f}s)")
            print(f"     Status: {status}")
            print(f"     Cascades: {cascade_count}")
            
            if args.verbose:
                # Show cascade details
                cursor.execute("""
                    SELECT cascade_id, task, started_at
                    FROM cascades
                    WHERE session_id = ?
                    ORDER BY started_at DESC
                    LIMIT 5
                """, (session_id,))
                cascades = cursor.fetchall()
                
                if cascades:
                    print(f"     Recent cascades:")
                    for cascade_id, task, c_started in cascades:
                        task_preview = (task[:50] + '...') if len(task) > 50 else task
                        print(f"       • {cascade_id[:8]}: {task_preview}")
            
            print()
        
        db.close()
        
        print(f"💡 Use 'empirica sessions-show <session_id>' for detailed info")
        
    except Exception as e:
        handle_cli_error(e, "Listing sessions", getattr(args, 'verbose', False))

def handle_sessions_show_command(args):
    """Show detailed session information"""
    try:
        from ..cli_utils import print_header
        
        # Check if JSON output requested
        output_json = getattr(args, 'output', None) == 'json'
        
        if not output_json:
            print_header(f"📄 Session Details: {args.session_id}")
        
        from empirica.data.session_database import SessionDatabase
        from datetime import datetime
        import json
        
        db = SessionDatabase()
        
        # Get session info
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT session_id, ai_id, start_time, end_time
            FROM sessions
            WHERE session_id = ?
        """, (args.session_id,))
        
        session = cursor.fetchone()
        
        if not session:
            print(f"\n❌ Session '{args.session_id}' not found")
            db.close()
            return
        
        session_id, ai_id, start_time, end_time = session
        
        # Parse timestamps
        started = datetime.fromisoformat(start_time) if start_time else None
        ended = datetime.fromisoformat(end_time) if end_time and end_time != 'None' else None
        
        # JSON output
        if output_json:
            # Get cascades for JSON
            cursor.execute("""
                SELECT cascade_id, task, started_at, completed_at
                FROM cascades
                WHERE session_id = ?
                ORDER BY started_at DESC
            """, (args.session_id,))
            
            cascades = cursor.fetchall()
            
            output = {
                "session_id": session_id,
                "ai_id": ai_id,
                "start_time": start_time,
                "end_time": end_time,
                "status": "complete" if ended else "active",
                "cascades": [
                    {
                        "cascade_id": c[0],
                        "task": c[1],
                        "started_at": c[2],
                        "ended_at": c[3]
                    }
                    for c in cascades
                ]
            }
            
            print(json.dumps(output, indent=2, default=str))
            db.close()
            return
        
        # Show session info
        print(f"\n🆔 Session ID: {session_id}")
        print(f"🤖 AI ID: {ai_id}")
        print(f"⏰ Started: {started.strftime('%Y-%m-%d %H:%M:%S') if started else 'Unknown'}")
        
        if ended:
            duration = (ended - started).total_seconds() if started else 0
            print(f"✅ Ended: {ended.strftime('%Y-%m-%d %H:%M:%S')} (Duration: {duration:.1f}s)")
        else:
            print(f"🔄 Status: Active")
        
        # Get cascades
        cursor.execute("""
            SELECT cascade_id, task, started_at, ended_at
            FROM cascades
            WHERE session_id = ?
            ORDER BY started_at DESC
        """, (args.session_id,))
        
        cascades = cursor.fetchall()
        
        print(f"\n📊 Cascades: {len(cascades)}")
        
        for i, (cascade_id, task, c_started, c_ended) in enumerate(cascades, 1):
            print(f"\n  {i}. Cascade {cascade_id[:8]}")
            print(f"     Task: {task}")
            
            c_start_time = datetime.fromisoformat(c_started) if c_started else None
            c_end_time = datetime.fromisoformat(c_ended) if c_ended and c_ended != 'None' else None
            
            print(f"     Started: {c_start_time.strftime('%H:%M:%S') if c_start_time else 'Unknown'}")
            if c_end_time:
                c_duration = (c_end_time - c_start_time).total_seconds() if c_start_time else 0
                print(f"     Duration: {c_duration:.1f}s")
            
            if args.verbose:
                # Get metadata from unified reflexes table instead of legacy cascade_metadata
                cursor.execute("""
                    SELECT phase, reflex_data
                    FROM reflexes
                    WHERE cascade_id = ?
                """, (cascade_id,))

                reflex_entries = cursor.fetchall()

                if reflex_entries:
                    print(f"     Metadata:")
                    for phase, reflex_data in reflex_entries:
                        try:
                            data = json.loads(reflex_data)
                            # Extract meaningful info from reflex_data
                            if 'vectors' in data:
                                vectors = data['vectors']
                                for key, value in vectors.items():
                                    if key in ['know', 'do', 'context', 'clarity', 'coherence', 'signal', 'density', 'state', 'change', 'completion', 'impact', 'engagement', 'uncertainty']:
                                        print(f"       {key}: {value}")
                            if 'reasoning' in data:
                                print(f"       reasoning: {data['reasoning'][:100]}...")
                        except json.JSONDecodeError:
                            print(f"       phase: {phase}, raw_data: {reflex_data[:100]}...")
                        if key in ['preflight_vectors', 'postflight_vectors']:
                            try:
                                vectors = json.loads(value)
                                print(f"       {key}:")
                                print(f"         KNOW: {vectors.get('know', 'N/A'):.2f}" if isinstance(vectors.get('know'), (int, float)) else f"         KNOW: N/A")
                                print(f"         DO: {vectors.get('do', 'N/A'):.2f}" if isinstance(vectors.get('do'), (int, float)) else f"         DO: N/A")
                                print(f"         CONTEXT: {vectors.get('context', 'N/A'):.2f}" if isinstance(vectors.get('context'), (int, float)) else f"         CONTEXT: N/A")
                                print(f"         UNCERTAINTY: {vectors.get('uncertainty', 'N/A'):.2f}" if isinstance(vectors.get('uncertainty'), (int, float)) else f"         UNCERTAINTY: N/A")
                            except:
                                print(f"       {key}: {value[:100]}")
                        else:
                            value_preview = (value[:80] + '...') if len(value) > 80 else value
                            print(f"       {key}: {value_preview}")
        
        db.close()
        
        print(f"\n💡 Use 'empirica sessions-export {args.session_id}' to export full data")
        
    except Exception as e:
        handle_cli_error(e, "Showing session", getattr(args, 'verbose', False))

def handle_sessions_export_command(args):
    """Export session to JSON file"""
    try:
        from ..cli_utils import print_header
        print_header(f"💾 Exporting Session: {args.session_id}")
        
        from empirica.data.session_database import SessionDatabase
        import json
        from pathlib import Path
        
        db = SessionDatabase()
        
        # Determine output file
        output_file = args.output if args.output else f"session_{args.session_id}.json"
        output_path = Path(output_file)
        
        # Get session info
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT session_id, ai_id, start_time, end_time
            FROM sessions
            WHERE session_id = ?
        """, (args.session_id,))
        
        session = cursor.fetchone()
        
        if not session:
            print(f"\n❌ Session '{args.session_id}' not found")
            db.close()
            return
        
        session_id, ai_id, start_time, end_time = session
        
        # Build export data
        export_data = {
            "session_id": session_id,
            "ai_id": ai_id,
            "start_time": start_time,
            "end_time": end_time,
            "cascades": []
        }
        
        # Get cascades
        cursor.execute("""
            SELECT cascade_id, task, started_at, ended_at, result, context
            FROM cascades
            WHERE session_id = ?
            ORDER BY started_at ASC
        """, (args.session_id,))
        
        cascades = cursor.fetchall()
        
        for cascade_id, task, c_started, c_ended, result, context in cascades:
            cascade_data = {
                "cascade_id": cascade_id,
                "task": task,
                "started_at": c_started,
                "ended_at": c_ended,
                "result": result,
                "context": json.loads(context) if context else {},
                "metadata": {}
            }
            
            # Get metadata from unified reflexes table instead of legacy cascade_metadata
            cursor.execute("""
                SELECT phase, reflex_data
                FROM reflexes
                WHERE cascade_id = ?
            """, (cascade_id,))

            reflex_entries = cursor.fetchall()
            for phase, reflex_data in reflex_entries:
                try:
                    reflex_dict = json.loads(reflex_data)
                    # Add reflex data to metadata, using phase as a differentiator
                    cascade_data["metadata"][f"{phase.lower()}_reflex"] = reflex_dict
                except json.JSONDecodeError:
                    cascade_data["metadata"][f"{phase.lower()}_reflex"] = reflex_data
            
            export_data["cascades"].append(cascade_data)
        
        db.close()
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n✅ Session exported successfully")
        print(f"📁 File: {output_path.absolute()}")
        print(f"📊 Cascades: {len(export_data['cascades'])}")
        print(f"💾 Size: {output_path.stat().st_size} bytes")
        
    except Exception as e:
        handle_cli_error(e, "Exporting session", getattr(args, 'verbose', False))

def handle_log_token_saving(args):
    """Log a token saving event"""
    from empirica.data.session_database import SessionDatabase
    
    db = SessionDatabase()
    
    saving_id = db.log_token_saving(
        session_id=args.session_id,
        saving_type=args.type,
        tokens_saved=args.tokens,
        evidence=args.evidence
    )
    
    db.close()
    
    if args.output == 'json':
        print(json.dumps({
            'ok': True,
            'saving_id': saving_id,
            'tokens_saved': args.tokens,
            'type': args.type
        }))
    else:
        print(f"✅ Token saving logged: {args.tokens} tokens saved ({args.type})")


def handle_efficiency_report(args):
    """Show token efficiency report for session"""
    from empirica.data.session_database import SessionDatabase
    
    db = SessionDatabase()
    savings = db.get_session_token_savings(args.session_id)
    
    if args.output == 'json':
        print(json.dumps(savings, indent=2))
    else:
        print("\n📊 Token Efficiency Report")
        print("━" * 60)
        print(f"✅ Tokens Saved This Session:     {savings['total_tokens_saved']:,} tokens")
        print(f"💰 Cost Saved:                    ${savings['cost_saved_usd']:.4f} USD")
        
        if savings['breakdown']:
            print("\nBreakdown:")
            for saving_type, data in savings['breakdown'].items():
                type_label = saving_type.replace('_', ' ').title()
                print(f"  {type_label:.<30} {data['tokens']:,} tokens ({data['count']}x)")
        else:
            print("\n  (No token savings logged yet)")
        
        print("━" * 60)
    
    db.close()
