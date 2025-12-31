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
        
        # Build query with optional AI ID filter
        query = """
            SELECT
                session_id, ai_id, user_id, start_time, end_time,
                total_cascades, avg_confidence, drift_detected
            FROM sessions
        """
        params = []

        # Add AI ID filter if provided
        if hasattr(args, 'ai_id') and args.ai_id:
            query += "WHERE ai_id = ? "
            params.append(args.ai_id)

        query += "ORDER BY start_time DESC LIMIT ?"
        params.append(args.limit if hasattr(args, 'limit') else 50)

        cursor.execute(query, params)
        
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
        import json

        # Support both positional and named argument for session ID
        session_id_arg = args.session_id or getattr(args, 'session_id_named', None)
        if not session_id_arg:
            if getattr(args, 'output', None) == 'json':
                print(json.dumps({"ok": False, "error": "Session ID required"}))
            else:
                print("\n❌ Session ID required")
                print("💡 Usage: empirica sessions-show <session-id>")
                print("💡 Or: empirica sessions-show --session-id <session-id>")
            return

        # Resolve session alias to UUID
        try:
            session_id = resolve_session_id(session_id_arg)
        except ValueError as e:
            if getattr(args, 'output', None) == 'json':
                print(json.dumps({"ok": False, "error": str(e)}))
            else:
                print(f"\n❌ {str(e)}")
                print(f"💡 Provided: {session_id_arg}")
                print(f"💡 List sessions with: empirica sessions-list")
            return

        db = SessionDatabase()  # Use path resolver

        # Get session summary (use resolved session_id)
        summary = db.get_session_summary(session_id, detail_level="detailed")
        
        if not summary:
            logger.warning(f"Session not found: {session_id_arg}")
            if getattr(args, 'output', None) == 'json':
                print(json.dumps({"ok": False, "error": f"Session not found: {session_id_arg}"}))
            else:
                print(f"\n❌ Session not found: {session_id_arg}")
                print(f"💡 List sessions with: empirica sessions list")
            db.close()
            return
        
        # If JSON output requested, return early
        if getattr(args, 'output', None) == 'json':
            print(json.dumps({"ok": True, "session": summary}))
            db.close()
            return
        
        print_header(f"📊 Session Details: {session_id[:8]}")
        
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


def handle_session_snapshot_command(args):
    """Handle session-snapshot command - show where you left off"""
    from empirica.data.session_database import SessionDatabase
    from empirica.utils.session_resolver import resolve_session_id
    import json
    
    # Resolve session ID (supports aliases)
    session_id = resolve_session_id(args.session_id)
    
    db = SessionDatabase()
    snapshot = db.get_session_snapshot(session_id)
    db.close()
    
    if not snapshot:
        print(f"❌ Session not found: {args.session_id}")
        return 1
    
    if args.output == 'json':
        print(json.dumps(snapshot, indent=2))
        return 0
    
    # Human-readable output
    print(f"\n📸 Session Snapshot: {session_id[:8]}...")
    print(f"   AI: {snapshot['ai_id']}")
    if snapshot.get('subject'):
        print(f"   Subject: {snapshot['subject']}")
    
    # Git state
    git = snapshot['git_state']
    if 'error' not in git:
        print(f"\n🔀 Git State:")
        print(f"   Branch: {git['branch']}")
        print(f"   Commit: {git['commit']}")
        print(f"   Diff: {git['diff_stat']}")
        if git.get('last_5_commits'):
            print(f"   Recent commits:")
            for commit in git['last_5_commits'][:3]:
                print(f"      {commit}")
    
    # Epistemic trajectory
    trajectory = snapshot['epistemic_trajectory']
    if trajectory:
        print(f"\n🧠 Epistemic Trajectory:")
        if 'preflight' in trajectory:
            pre = trajectory['preflight']
            print(f"   PREFLIGHT: know={pre.get('know', 0):.2f}, uncertainty={pre.get('uncertainty', 0):.2f}")
        if 'check_gates' in trajectory:
            print(f"   CHECK gates: {len(trajectory['check_gates'])} decision points")
        if 'postflight' in trajectory:
            post = trajectory['postflight']
            print(f"   POSTFLIGHT: know={post.get('know', 0):.2f}, uncertainty={post.get('uncertainty', 0):.2f}")
    
    # Learning delta
    delta = snapshot.get('learning_delta', {})
    if delta:
        print(f"\n📈 Learning Delta:")
        significant = {k: v for k, v in delta.items() if abs(v) >= 0.1}
        for key, value in sorted(significant.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
            sign = '+' if value > 0 else ''
            print(f"   {key}: {sign}{value:.3f}")
    
    # Active goals
    goals = snapshot.get('active_goals', [])
    if goals:
        print(f"\n🎯 Active Goals ({len(goals)}):")
        for goal in goals[:3]:
            print(f"   - {goal['objective']} ({goal['progress']})")
    
    # Sources
    sources = snapshot.get('sources_referenced', [])
    if sources:
        print(f"\n📚 Sources Referenced ({len(sources)}):")
        for src in sources[:5]:
            print(f"   - {src['title']} ({src['type']}, confidence={src['confidence']:.2f})")
    
    return 0

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
        
        # Check if output format is JSON (to stdout)
        output_format = getattr(args, 'output_format', 'file')
        if output_format == 'json' or getattr(args, 'format', None) == 'json':
            # Output JSON to stdout
            print(json.dumps({"ok": True, "session": summary}))
            db.close()
            return
        
        # Determine output file
        output_file = args.output if hasattr(args, 'output') and args.output else f"session_{session_id_arg[:8]}.json"
        
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


def handle_memory_compact_command(args):
    """
    Memory-compact: Create epistemic continuity across session boundaries

    Workflow:
    1. Checkpoint current epistemic state (pre-compact)
    2. Run project-bootstrap to load ground truth
    3. Create continuation session with lineage
    4. Return formatted output for IDE injection

    Args from JSON stdin:
        session_id: Session to compact (supports aliases)
        create_continuation: bool (default: true)
        include_bootstrap: bool (default: true)
        checkpoint_current: bool (default: true)
        compact_mode: "full" | "minimal" | "context_only" (default: "full")
    """
    try:
        import sys
        from empirica.data.session_database import SessionDatabase
        from empirica.utils.session_resolver import resolve_session_id

        # Read JSON config from stdin or file
        if hasattr(args, 'config') and args.config:
            if args.config == '-':
                # Read from stdin
                config = json.load(sys.stdin)
            else:
                # Read from file
                with open(args.config, 'r') as f:
                    config = json.load(f)
        else:
            # No argument provided, read from stdin (AI-first mode)
            config = json.load(sys.stdin)

        # Extract parameters with defaults
        session_id_arg = config.get('session_id')
        if not session_id_arg:
            print(json.dumps({
                "ok": False,
                "error": "session_id required",
                "hint": "Provide session_id in JSON config"
            }))
            return 1

        create_continuation = config.get('create_continuation', True)
        include_bootstrap = config.get('include_bootstrap', True)
        checkpoint_current = config.get('checkpoint_current', True)
        compact_mode = config.get('compact_mode', 'full')

        # NEW: Accept current_vectors from AI (accurate pre-compact state)
        current_vectors = config.get('current_vectors', None)

        # Resolve session alias to UUID
        try:
            session_id = resolve_session_id(session_id_arg)
        except ValueError as e:
            print(json.dumps({
                "ok": False,
                "error": str(e),
                "provided": session_id_arg
            }))
            return 1

        logger.info(f"Starting memory-compact for session {session_id[:8]}...")

        db = SessionDatabase()

        # Verify session exists
        session_info = db.get_session(session_id)
        if not session_info:
            print(json.dumps({
                "ok": False,
                "error": f"Session not found: {session_id_arg}"
            }))
            db.close()
            return 1

        project_id = session_info.get('project_id')
        ai_id = session_info.get('ai_id', 'unknown')

        output = {
            "ok": True,
            "operation": "memory_compact",
            "session_id": session_id,
            "compact_mode": compact_mode
        }

        # Step 1: Checkpoint current state (pre-compact tag)
        vectors_to_save = None
        if checkpoint_current:
            logger.info("Creating pre-compact checkpoint...")

            # Use current_vectors if provided, otherwise get latest from session
            if current_vectors:
                vectors_to_save = current_vectors
                logger.info("Using current_vectors from hook input (accurate pre-compact state)")
            else:
                latest_vectors_result = db.get_latest_vectors(session_id)
                if latest_vectors_result:
                    vectors_to_save = latest_vectors_result.get('vectors', {})
                    logger.warning("Using historical vectors (no current_vectors provided)")

            if vectors_to_save:
                from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

                reflex_logger = GitEnhancedReflexLogger(session_id=session_id)
                checkpoint_id = reflex_logger.add_checkpoint(
                    phase="PRE_MEMORY_COMPACT",
                    # round auto-increments
                    vectors=vectors_to_save,
                    metadata={"reasoning": "Pre-compact epistemic state snapshot for continuity measurement"},
                    epistemic_tags={"memory_compact": True, "pre_compact": True}
                )

                output["pre_compact_checkpoint"] = {
                    "checkpoint_id": checkpoint_id,
                    "vectors": vectors_to_save,
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(f"Pre-compact checkpoint created: {checkpoint_id[:8]}")
            else:
                logger.warning("No epistemic vectors available - skipping checkpoint")
                output["pre_compact_checkpoint"] = None

        # Step 2: Run project-bootstrap (load ground truth)
        bootstrap_context = None
        if include_bootstrap and project_id:
            logger.info(f"Loading bootstrap context for project {project_id[:8]}...")

            try:
                # Call bootstrap method on database
                bootstrap_context = db.bootstrap_project_breadcrumbs(
                    project_id=project_id,
                    check_integrity=False,
                    context_to_inject=True,
                    task_description=None,
                    epistemic_state=None,
                    subject=None
                )

                output["bootstrap_context"] = bootstrap_context
                logger.info(f"Bootstrap loaded: {len(bootstrap_context.get('findings', []))} findings, "
                           f"{len(bootstrap_context.get('unknowns', []))} unknowns, "
                           f"{len(bootstrap_context.get('incomplete_work', []))} incomplete goals")

            except Exception as e:
                logger.error(f"Bootstrap failed: {e}")
                output["bootstrap_context"] = {"error": str(e)}

        # Step 3: Create continuation session
        continuation_session_id = None
        if create_continuation:
            logger.info("Creating continuation session...")

            # Create new session linked via git notes (metadata linkage for future)
            continuation_session_id = db.create_session(
                ai_id=ai_id,
                subject=None
            )

            # Set project_id for continuation session
            if project_id:
                cursor = db.conn.cursor()
                cursor.execute("""
                    UPDATE sessions SET project_id = ? WHERE session_id = ?
                """, (project_id, continuation_session_id))
                db.conn.commit()

            # Step 3a: Calculate recommended PREFLIGHT for continuation (preserves delta calculation)
            recommended_preflight = None
            if vectors_to_save:
                # Adjust vectors for fresh session context
                recommended_preflight = vectors_to_save.copy()

                # Context increases (bootstrap loaded)
                if 'context' in recommended_preflight:
                    recommended_preflight['context'] = min(
                        recommended_preflight.get('context', 0.5) + 0.10,
                        1.0
                    )

                # Uncertainty slightly increases (fresh session)
                recommended_preflight['uncertainty'] = min(
                    recommended_preflight.get('uncertainty', 0.3) + 0.05,
                    1.0
                )

                # State resets for continuation (change/completion adjust for new session)
                recommended_preflight['state'] = recommended_preflight.get('state', 0.7)
                recommended_preflight['change'] = 0.20  # Fresh start
                recommended_preflight['completion'] = 0.15  # Just beginning

            # Step 3b: Create PREFLIGHT checkpoint in continuation session (CRITICAL for delta calculation!)
            # This enables: continuation session PREFLIGHT → POSTFLIGHT delta calculation
            from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
            continuation_logger = GitEnhancedReflexLogger(session_id=continuation_session_id)

            if recommended_preflight:
                # Create actual PREFLIGHT checkpoint (not SESSION_CONTINUATION)
                preflight_checkpoint_id = continuation_logger.add_checkpoint(
                    phase="PREFLIGHT",  # ✅ CRITICAL: Must be PREFLIGHT for delta calculation
                    # round auto-increments
                    vectors=recommended_preflight,
                    metadata={
                        "parent_session_id": session_id,
                        "reason": "memory_compact_continuation",
                        "compact_mode": compact_mode,
                        "reasoning": "Continuation session PREFLIGHT (adjusted from pre-compact state + bootstrap context)"
                    },
                    epistemic_tags={"continuation": True, "memory_compact": True}
                )
                logger.info(f"Continuation PREFLIGHT checkpoint created: {preflight_checkpoint_id[:8]}")

                output["continuation_preflight"] = {
                    "checkpoint_id": preflight_checkpoint_id,
                    "vectors": recommended_preflight,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning("No vectors available for continuation PREFLIGHT checkpoint")

            output["continuation"] = {
                "new_session_id": continuation_session_id,
                "parent_session_id": session_id,
                "ai_id": ai_id,
                "lineage_depth": 1  # Could calculate actual depth
            }

            logger.info(f"Continuation session created: {continuation_session_id[:8]}")

            # Add recommended_preflight to output for reference
            if recommended_preflight:
                output["recommended_preflight"] = recommended_preflight
                output["calibration_notes"] = (
                    "CONTEXT +0.10 (bootstrap loaded), "
                    "UNCERTAINTY +0.05 (fresh session), "
                    "CHANGE/COMPLETION reset for continuation"
                )

        # Step 5: Format for IDE injection
        if compact_mode == "full":
            output["ide_injection"] = format_ide_injection(
                session_id=session_id,
                continuation_session_id=continuation_session_id,
                bootstrap_context=bootstrap_context,
                pre_compact_vectors=vectors_to_save
            )

        db.close()

        # Output JSON
        print(json.dumps(output, indent=2, default=str))
        return 0

    except Exception as e:
        handle_cli_error(e, "Memory compact", getattr(args, 'verbose', False))
        return 1


def format_ide_injection(session_id, continuation_session_id, bootstrap_context, pre_compact_vectors):
    """
    Format bootstrap context for IDE injection into conversation summary

    Returns markdown-formatted context for the IDE to inject after summarization.
    """
    lines = []

    lines.append("## Empirica Context (Loaded from Ground Truth)")
    lines.append("")
    lines.append("**Session Continuity:**")
    lines.append(f"- Continuing from session: `{session_id}`")
    if continuation_session_id:
        lines.append(f"- New session: `{continuation_session_id}`")

    if pre_compact_vectors:
        know = pre_compact_vectors.get('foundation', {}).get('know', 0)
        uncertainty = pre_compact_vectors.get('uncertainty', 0)
        lines.append(f"- Pre-compact epistemic state: know={know:.2f}, uncertainty={uncertainty:.2f}")

    lines.append("")

    # Recent findings
    if bootstrap_context and 'findings' in bootstrap_context:
        findings = bootstrap_context['findings']
        if findings:
            lines.append(f"**Recent Findings ({len(findings)} total):**")
            for i, finding in enumerate(findings[:10], 1):
                finding_text = finding if isinstance(finding, str) else finding.get('finding_text', str(finding))
                lines.append(f"{i}. {finding_text[:100]}...")
            lines.append("")

    # Unresolved unknowns
    if bootstrap_context and 'unknowns' in bootstrap_context:
        unknowns = bootstrap_context['unknowns']
        if unknowns:
            lines.append(f"**Unresolved Unknowns ({len(unknowns)} total):**")
            for i, unknown in enumerate(unknowns[:10], 1):
                unknown_text = unknown if isinstance(unknown, str) else unknown.get('unknown', str(unknown))
                lines.append(f"{i}. {unknown_text[:100]}...")
            lines.append("")

    # Incomplete goals
    if bootstrap_context and 'incomplete_work' in bootstrap_context:
        goals = bootstrap_context['incomplete_work']
        if goals:
            lines.append(f"**Incomplete Goals ({len(goals)} in-progress):**")
            for i, goal in enumerate(goals[:5], 1):
                objective = goal.get('goal', goal.get('objective', str(goal)))
                progress = goal.get('progress', '?/?')
                lines.append(f"{i}. {objective[:70]} - {progress}")
            lines.append("")

    # Recommended PREFLIGHT
    if pre_compact_vectors:
        lines.append("**Recommended PREFLIGHT:**")
        know = pre_compact_vectors.get('foundation', {}).get('know', 0)
        context = min(pre_compact_vectors.get('foundation', {}).get('context', 0.5) + 0.10, 1.0)
        uncertainty = min(pre_compact_vectors.get('uncertainty', 0.3) + 0.05, 1.0)
        lines.append(f"- engagement={pre_compact_vectors.get('engagement', 0.85):.2f}")
        lines.append(f"- know={know:.2f}, context={context:.2f}")
        lines.append(f"- uncertainty={uncertainty:.2f}")

    return "\n".join(lines)
