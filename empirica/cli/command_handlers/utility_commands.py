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


def handle_feedback_command(args):
    """Handle feedback command"""
    try:
        from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
        
        logger.info(f"Processing feedback for decision: {args.decision_id}")
        print(f"📝 Processing feedback for decision: {args.decision_id}")
        
        # Create outcome dictionary
        outcome = {
            'success': args.success,
            'timestamp': time.time()
        }
        
        if args.notes:
            outcome['notes'] = args.notes
        
        # Process feedback via epistemic cascade
        feedback_result = run_epistemic_cascade(
            task=f"Process feedback for decision {args.decision_id}: {'success' if args.success else 'failure'}",
            context={'outcome': outcome, 'decision_id': args.decision_id},
            confidence_threshold=0.5
        )
        
        
        logger.info(f"Feedback processed successfully for decision: {args.decision_id}")
        print(f"✅ Feedback processed for decision: {args.decision_id}")
        print(f"   📊 Outcome: {'Success' if args.success else 'Failure'}")
        print(f"   📝 Notes: {args.notes if args.notes else 'None'}")
        print(f"   🧠 Learning confidence: {feedback_result.get('confidence', 0.0):.2f}")
        
    except Exception as e:
        handle_cli_error(e, "Feedback processing", getattr(args, 'verbose', False))


def handle_goal_analysis_command(args):
    """Handle goal analysis command"""
    try:
        from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
        
        
        logger.info(f"Analyzing goal feasibility: {args.goal}")
        print(f"🎯 Analyzing goal: {args.goal}")
        
        context = parse_json_safely(getattr(args, 'context', None))
        
        # Use epistemic cascade for goal analysis
        result = run_epistemic_cascade(
            task=f"Goal analysis: {args.goal}",
            context=context or {},
            confidence_threshold=0.7
        )
        
        print(f"📊 Goal Feasibility: {result.get('confidence', 0.0):.2f}")
        print(f"🎯 Decision: {result.get('final_decision', 'INVESTIGATE')}")
        print(f"💭 Reasoning: {result.get('reasoning', 'N/A')}")
        
        if result.get('required_actions'):
            print(f"⚡ Required Actions:")
            for action in result['required_actions']:
                print(f"   • {action}")
        
        if getattr(args, 'verbose', False):
            epistemic_state = result.get('epistemic_state', {})
            if epistemic_state:
                print("🧠 Epistemic State:")
                for key, value in epistemic_state.items():
                    print(f"   • {key}: {value:.2f}")
        
    except Exception as e:
        handle_cli_error(e, "Goal analysis", getattr(args, 'verbose', False))


def handle_calibration_command(args):
    """Handle calibration command"""
    try:
        from empirica.calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration
        
        print(f"🎯 Running calibration analysis...")
        
        analyzer = UncertaintyAnalyzer()
        
        # Get calibration data
        if hasattr(args, 'data_file') and args.data_file:
            with open(args.data_file, 'r') as f:
                calibration_data = json.load(f)
        else:
            # Use default calibration assessment
            calibration_data = analyzer.get_default_calibration_data()
        
        result = analyzer.analyze_calibration(calibration_data)
        
        print(f"✅ Calibration analysis complete")
        print(f"   📊 Overall calibration score: {result.get('calibration_score', 0):.2f}")
        print(f"   🎯 Accuracy: {result.get('accuracy', 0):.2f}")
        print(f"   📈 Trend: {result.get('trend', 'stable')}")
        
        if getattr(args, 'verbose', False):
            print("🔍 Detailed calibration metrics:")
            for metric, value in result.get('detailed_metrics', {}).items():
                print(f"   • {metric}: {value}")
        
    except Exception as e:
        handle_cli_error(e, "Calibration", getattr(args, 'verbose', False))


def handle_uvl_command(args):
    """Handle UVL (Uncertainty Vector Learning) command"""
    try:
        from empirica.calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration
        
        print(f"🧠 Running UVL analysis...")
        
        analyzer = UncertaintyAnalyzer()
        
        # Parse context if provided
        context = parse_json_safely(getattr(args, 'context', None))
        
        # Run UVL analysis
        result = analyzer.run_uvl_analysis(
            task=args.task if hasattr(args, 'task') else "General UVL analysis",
            context=context
        )
        
        print(f"✅ UVL analysis complete")
        print(f"   🎯 Task: {result.get('task', 'Unknown')}")
        print(f"   📊 Confidence: {result.get('confidence', 0):.2f}")
        print(f"   🧠 Learning vectors: {len(result.get('vectors', []))}")
        
        if getattr(args, 'verbose', False) and result.get('vectors'):
            print("🔍 Uncertainty vectors:")
            for vector in result['vectors']:
                print(f"   • {vector.get('name', 'Unknown')}: {vector.get('value', 0):.2f}")
        
    except Exception as e:
        handle_cli_error(e, "UVL analysis", getattr(args, 'verbose', False))


def handle_sessions_list_command(args):
    """List all sessions"""
    try:
        from ..cli_utils import print_header
        print_header("📋 Empirica Sessions")
        
        from empirica.data.session_database import SessionDatabase
        from datetime import datetime
        
        db = SessionDatabase()
        
        # Query sessions
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT session_id, ai_id, started_at, ended_at,
                   (SELECT COUNT(*) FROM cascades WHERE cascades.session_id = sessions.session_id) as cascade_count
            FROM sessions
            ORDER BY started_at DESC
            LIMIT ?
        """, (args.limit,))
        
        sessions = cursor.fetchall()
        
        if not sessions:
            print("\n📭 No sessions found")
            print("💡 Sessions are created when you run preflight or cascade commands")
            db.close()
            return
        
        print(f"\n📊 Found {len(sessions)} session(s):\n")
        
        for session in sessions:
            session_id, ai_id, started_at, ended_at, cascade_count = session
            
            # Parse timestamps
            started = datetime.fromisoformat(started_at) if started_at else None
            ended = datetime.fromisoformat(ended_at) if ended_at and ended_at != 'None' else None
            
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
        print_header(f"📄 Session Details: {args.session_id}")
        
        from empirica.data.session_database import SessionDatabase
        from datetime import datetime
        import json
        
        db = SessionDatabase()
        
        # Get session info
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT session_id, ai_id, started_at, ended_at
            FROM sessions
            WHERE session_id = ?
        """, (args.session_id,))
        
        session = cursor.fetchone()
        
        if not session:
            print(f"\n❌ Session '{args.session_id}' not found")
            db.close()
            return
        
        session_id, ai_id, started_at, ended_at = session
        
        # Parse timestamps
        started = datetime.fromisoformat(started_at) if started_at else None
        ended = datetime.fromisoformat(ended_at) if ended_at and ended_at != 'None' else None
        
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
                # Get metadata
                cursor.execute("""
                    SELECT metadata_key, metadata_value
                    FROM cascade_metadata
                    WHERE cascade_id = ?
                """, (cascade_id,))
                
                metadata = cursor.fetchall()
                
                if metadata:
                    print(f"     Metadata:")
                    for key, value in metadata:
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
            SELECT session_id, ai_id, started_at, ended_at
            FROM sessions
            WHERE session_id = ?
        """, (args.session_id,))
        
        session = cursor.fetchone()
        
        if not session:
            print(f"\n❌ Session '{args.session_id}' not found")
            db.close()
            return
        
        session_id, ai_id, started_at, ended_at = session
        
        # Build export data
        export_data = {
            "session_id": session_id,
            "ai_id": ai_id,
            "started_at": started_at,
            "ended_at": ended_at,
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
            
            # Get metadata
            cursor.execute("""
                SELECT metadata_key, metadata_value
                FROM cascade_metadata
                WHERE cascade_id = ?
            """, (cascade_id,))
            
            metadata = cursor.fetchall()
            for key, value in metadata:
                try:
                    cascade_data["metadata"][key] = json.loads(value)
                except:
                    cascade_data["metadata"][key] = value
            
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