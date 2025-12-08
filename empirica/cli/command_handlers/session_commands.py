"""
Session Management Commands - Query and manage Empirica sessions

Provides commands for:
- Listing all sessions
- Showing detailed session info with epistemic vectors
- Exporting session data to JSON
"""

import json
import logging
from datetime import datetime
from ..cli_utils import handle_cli_error, print_header

# Set up logging for session commands
logger = logging.getLogger(__name__)


def handle_sessions_list_command(args):
    """List all sessions with summary information"""
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()  # Use path resolver
        cursor = db.conn.cursor()
        
        # Query all sessions
        cursor.execute("""
            SELECT 
                session_id, ai_id, user_id, start_time, end_time,
                total_cascades, avg_confidence, drift_detected
            FROM sessions
            ORDER BY start_time DESC
            LIMIT ?
        """, (args.limit if hasattr(args, 'limit') else 50,))
        
        sessions = cursor.fetchall()
        
        logger.info(f"Found {len(sessions)} sessions to display")
        
        # Check output format FIRST (before any printing)
        if hasattr(args, 'output') and args.output == 'json':
            # JSON output only
            if not sessions:
                print(json.dumps({"ok": False, "sessions": [], "count": 0, "message": "No sessions found"}))
            else:
                sessions_list = []
                for row in sessions:
                    session_id, ai_id, user_id, start_time, end_time, cascades, conf, drift = row
                    sessions_list.append({
                        "session_id": session_id,
                        "ai_id": ai_id,
                        "user_id": user_id,
                        "start_time": str(start_time),
                        "end_time": str(end_time) if end_time else None,
                        "total_cascades": cascades,
                        "avg_confidence": conf,
                        "drift_detected": bool(drift)
                    })
                print(json.dumps({"ok": True, "sessions": sessions_list, "count": len(sessions)}))
            db.close()
            return
        
        # Pretty output (terminal)
        print_header("📋 Empirica Sessions")
        
        if not sessions:
            logger.info("No sessions found in database")
            print("\n📭 No sessions found")
            print("💡 Create a session with: empirica preflight <task>")
            db.close()
            return
        
        print(f"\n📊 Found {len(sessions)} sessions:\n")
        
        for row in sessions:
            session_id, ai_id, user_id, start_time, end_time, cascades, conf, drift = row
            
            # Format timestamps - handle various types (str, datetime, float/timestamp)
            def format_timestamp(ts):
                """Format timestamp handling str, datetime, or numeric timestamp"""
                if not ts:
                    return None
                try:
                    if isinstance(ts, str):
                        # Try parsing ISO format string
                        return datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")
                    elif isinstance(ts, (int, float)):
                        # Unix timestamp
                        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                    elif hasattr(ts, 'strftime'):
                        # datetime object
                        return ts.strftime("%Y-%m-%d %H:%M")
                    else:
                        # Unknown format, return as string
                        return str(ts)
                except (ValueError, AttributeError, OSError) as e:
                    # Invalid timestamp, return as string
                    return str(ts) if ts else None
            
            start = format_timestamp(start_time) or "N/A"
            end = format_timestamp(end_time) or "Active"
            
            # Status indicator
            status = "✅" if end_time else "⏳"
            drift_icon = "⚠️" if drift else ""
            
            print(f"{status} {session_id[:8]}")
            print(f"   🤖 AI: {ai_id}")
            if user_id:
                print(f"   👤 User: {user_id}")
            print(f"   📅 Started: {start}")
            print(f"   🏁 Ended: {end}")
            print(f"   🔄 Cascades: {cascades}")
            if conf:
                print(f"   📊 Avg Confidence: {conf:.2f}")
            if drift:
                print(f"   {drift_icon} Drift Detected")
            print()
        
        if len(sessions) >= 50 and not hasattr(args, 'limit'):
            print("💡 Showing 50 most recent sessions. Use --limit to see more.")
        
        print(f"💡 View details: empirica sessions show <session_id>")
        
        db.close()
        
    except Exception as e:
        handle_cli_error(e, "Listing sessions", getattr(args, 'verbose', False))


def handle_sessions_show_command(args):
    """Show detailed session information including epistemic vectors"""
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.utils.session_resolver import resolve_session_id

        # Support both positional and named argument for session ID
        session_id_arg = args.session_id or getattr(args, 'session_id_named', None)
        if not session_id_arg:
            print("\n❌ Session ID required")
            print("💡 Usage: empirica sessions-show <session-id>")
            print("💡 Or: empirica sessions-show --session-id <session-id>")
            return

        # Resolve session alias to UUID
        try:
            session_id = resolve_session_id(session_id_arg)
        except ValueError as e:
            print(f"\n❌ {str(e)}")
            print(f"💡 Provided: {session_id_arg}")
            print(f"💡 List sessions with: empirica sessions-list")
            return

        print_header(f"📊 Session Details: {session_id[:8]}")

        db = SessionDatabase()  # Use path resolver

        # Get session summary (use resolved session_id)
        summary = db.get_session_summary(session_id, detail_level="detailed")
        
        if not summary:
            logger.warning(f"Session not found: {session_id_arg}")
            print(f"\n❌ Session not found: {session_id_arg}")
            print(f"💡 List sessions with: empirica sessions list")
            db.close()
            return
        
        # Basic info
        print(f"\n🆔 Session ID: {summary['session_id']}")
        print(f"🤖 AI: {summary['ai_id']}")
        print(f"📅 Started: {summary['start_time']}")
        if summary.get('end_time'):
            print(f"🏁 Ended: {summary['end_time']}")
        else:
            print(f"⏳ Status: Active")
        
        # Cascades
        print(f"\n🔄 Total Cascades: {summary['total_cascades']}")
        if summary.get('avg_confidence'):
            print(f"📊 Average Confidence: {summary['avg_confidence']:.2f}")
        
        # Show cascade tasks
        if args.verbose and isinstance(summary.get('cascades'), list):
            print(f"\n📋 Cascade Tasks:")
            for i, cascade in enumerate(summary['cascades'][:10], 1):
                if isinstance(cascade, dict):
                    task = cascade.get('task', 'Unknown')
                    conf = cascade.get('final_confidence')
                    print(f"   {i}. {task}")
                    if conf:
                        print(f"      Confidence: {conf:.2f}")
                else:
                    print(f"   {i}. {cascade}")
            
            if summary['total_cascades'] > 10:
                print(f"   ... and {summary['total_cascades'] - 10} more")
        
        # Epistemic vectors (preflight)
        if summary.get('preflight'):
            print(f"\n🚀 Preflight Epistemic State:")
            vectors = summary['preflight']
            print(f"   • KNOW:    {vectors.get('know', 0.5):.2f}")
            print(f"   • DO:      {vectors.get('do', 0.5):.2f}")
            print(f"   • CONTEXT: {vectors.get('context', 0.5):.2f}")
            
            if args.verbose:
                print(f"\n   Comprehension:")
                print(f"   • CLARITY:   {vectors.get('clarity', 0.5):.2f}")
                print(f"   • COHERENCE: {vectors.get('coherence', 0.5):.2f}")
                print(f"   • SIGNAL:    {vectors.get('signal', 0.5):.2f}")
                print(f"   • DENSITY:   {vectors.get('density', 0.5):.2f}")
                
                print(f"\n   Execution:")
                print(f"   • STATE:      {vectors.get('state', 0.5):.2f}")
                print(f"   • CHANGE:     {vectors.get('change', 0.5):.2f}")
                print(f"   • COMPLETION: {vectors.get('completion', 0.5):.2f}")
                print(f"   • IMPACT:     {vectors.get('impact', 0.5):.2f}")
                
                print(f"\n   Meta-Cognitive:")
                print(f"   • ENGAGEMENT:  {vectors.get('engagement', 0.5):.2f}")
                print(f"   • UNCERTAINTY: {vectors.get('uncertainty', 0.5):.2f}")
        
        # Epistemic vectors (postflight)
        if summary.get('postflight'):
            print(f"\n🏁 Postflight Epistemic State:")
            vectors = summary['postflight']
            print(f"   • KNOW:    {vectors.get('know', 0.5):.2f}")
            print(f"   • DO:      {vectors.get('do', 0.5):.2f}")
            print(f"   • CONTEXT: {vectors.get('context', 0.5):.2f}")
            
            if args.verbose:
                print(f"\n   Comprehension:")
                print(f"   • CLARITY:   {vectors.get('clarity', 0.5):.2f}")
                print(f"   • COHERENCE: {vectors.get('coherence', 0.5):.2f}")
                print(f"   • SIGNAL:    {vectors.get('signal', 0.5):.2f}")
                print(f"   • DENSITY:   {vectors.get('density', 0.5):.2f}")
                
                print(f"\n   Execution:")
                print(f"   • STATE:      {vectors.get('state', 0.5):.2f}")
                print(f"   • CHANGE:     {vectors.get('change', 0.5):.2f}")
                print(f"   • COMPLETION: {vectors.get('completion', 0.5):.2f}")
                print(f"   • IMPACT:     {vectors.get('impact', 0.5):.2f}")
                
                print(f"\n   Meta-Cognitive:")
                print(f"   • ENGAGEMENT:  {vectors.get('engagement', 0.5):.2f}")
                print(f"   • UNCERTAINTY: {vectors.get('uncertainty', 0.5):.2f}")
        
        # Epistemic delta (learning)
        if summary.get('epistemic_delta'):
            print(f"\n📈 Learning Delta (Preflight → Postflight):")
            delta = summary['epistemic_delta']
            
            # Show significant changes
            significant = {k: v for k, v in delta.items() if abs(v) >= 0.05}
            
            if significant:
                for key, value in sorted(significant.items(), key=lambda x: abs(x[1]), reverse=True):
                    icon = "↗" if value > 0 else "↘"
                    print(f"   {icon} {key.upper():12s} {value:+.2f}")
            else:
                print(f"   ➖ Minimal change (all < ±0.05)")
        
        # Tools used
        if summary.get('tools_used'):
            print(f"\n🔧 Investigation Tools Used:")
            for tool in summary['tools_used']:
                print(f"   • {tool['tool']}: {tool['count']} times")
        
        # Export hint
        print(f"\n💡 Export to JSON: empirica sessions export {session_id_arg}")
        
        db.close()
        
    except Exception as e:
        handle_cli_error(e, "Showing session details", getattr(args, 'verbose', False))


def handle_sessions_export_command(args):
    """Export session data to JSON file"""
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.utils.session_resolver import resolve_session_id

        # Support both positional and named argument for session ID
        session_id_arg = args.session_id or getattr(args, 'session_id_named', None)
        if not session_id_arg:
            print("\n❌ Session ID required")
            print("💡 Usage: empirica sessions-export <session-id>")
            print("💡 Or: empirica sessions-export --session-id <session-id>")
            return

        # Resolve session alias to UUID
        try:
            session_id = resolve_session_id(session_id_arg)
        except ValueError as e:
            print(f"\n❌ {str(e)}")
            print(f"💡 Provided: {session_id_arg}")
            return

        print_header(f"📦 Exporting Session: {session_id[:8]}")

        db = SessionDatabase()  # Use path resolver

        # Get full session summary (use resolved session_id)
        summary = db.get_session_summary(session_id, detail_level="full")
        
        if not summary:
            logger.warning(f"Session not found for export: {session_id_arg}")
            print(f"\n❌ Session not found: {session_id_arg}")
            db.close()
            return
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            output_file = f"session_{session_id_arg[:8]}.json"
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Session data exported to {output_file}")
        
        print(f"\n✅ Session exported successfully")
        print(f"📄 File: {output_file}")
        print(f"📊 Size: {len(json.dumps(summary, default=str))} bytes")
        
        # Summary stats
        print(f"\n📋 Exported Data:")
        print(f"   • Session ID: {summary['session_id']}")
        print(f"   • AI: {summary['ai_id']}")
        print(f"   • Cascades: {summary['total_cascades']}")
        if summary.get('preflight'):
            print(f"   • Preflight vectors: ✅")
        if summary.get('postflight'):
            print(f"   • Postflight vectors: ✅")
        if summary.get('epistemic_delta'):
            print(f"   • Learning delta: ✅")
        
        db.close()
        
    except Exception as e:
        handle_cli_error(e, "Exporting session", getattr(args, 'verbose', False))


# handle_session_end_command removed - use handoff-create instead
