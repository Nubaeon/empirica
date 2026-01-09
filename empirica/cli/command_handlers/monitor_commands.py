"""
Monitoring Commands - CLI commands for usage monitoring and cost tracking

NOTE: Modality switcher (adapter monitoring) is deprecated.
This module provides basic session monitoring via Empirica core.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

# Modality switcher is DEPRECATED and no longer available
MODALITY_AVAILABLE = False

from ..cli_utils import handle_cli_error

# Set up logging for monitor commands
logger = logging.getLogger(__name__)


class UsageMonitor:
    """
    Track and display adapter usage statistics.
    
    Monitors:
    - Request counts per adapter
    - Total costs
    - Average latency
    - Success/failure rates
    """
    
    def __init__(self, stats_file: Path = None):
        """
        Initialize UsageMonitor.
        
        Args:
            stats_file: Path to stats file (default from config)
        """
        config = get_config()
        
        if stats_file is None:
            default_path = config.get('monitoring.export_path', '~/.empirica/usage_stats.json')
            self.stats_file = Path(default_path).expanduser()
        else:
            self.stats_file = stats_file
        
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load existing stats or create new."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load stats from {self.stats_file}: {e}")
                pass
        
        # Initialize new stats
        return {
            "session_start": datetime.now().isoformat(),
            "adapters": {
                "minimax": {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0},
                "qwen": {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0},
                "local": {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0}
            },
            "total_requests": 0,
            "total_cost": 0.0,
            "fallbacks": 0,
            "history": []
        }
    
    def _save_stats(self):
        """Save stats to file."""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def record_request(
        self, 
        adapter: str, 
        success: bool, 
        tokens: int = 0, 
        cost: float = 0.0,
        latency: float = 0.0
    ):
        """Record a request."""
        if adapter not in self.stats["adapters"]:
            logger.debug(f"Creating new stats entry for adapter: {adapter}")
            self.stats["adapters"][adapter] = {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0}
        
        self.stats["adapters"][adapter]["requests"] += 1
        self.stats["adapters"][adapter]["tokens"] += tokens
        self.stats["adapters"][adapter]["cost"] += cost
        
        if not success:
            self.stats["adapters"][adapter]["errors"] += 1
            logger.warning(f"Request error recorded for adapter: {adapter}")
        
        self.stats["total_requests"] += 1
        self.stats["total_cost"] += cost
        
        logger.debug(f"Recorded request: adapter={adapter}, success={success}, tokens={tokens}, cost=${cost:.4f}")
        
        # Add to history
        self.stats["history"].append({
            "timestamp": datetime.now().isoformat(),
            "adapter": adapter,
            "success": success,
            "tokens": tokens,
            "cost": cost,
            "latency": latency
        })
        
        # Keep only last 1000 records
        if len(self.stats["history"]) > 1000:
            logger.debug("Trimming history to last 1000 records")
            self.stats["history"] = self.stats["history"][-1000:]
        
        self._save_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset all statistics."""
        logger.info("Resetting all monitoring statistics")
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "adapters": {
                "minimax": {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0},
                "qwen": {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0},
                "local": {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0}
            },
            "total_requests": 0,
            "total_cost": 0.0,
            "fallbacks": 0,
            "history": []
        }
        self._save_stats()


def handle_monitor_command(args):
    """
    Unified monitor handler (consolidates all 4 monitor commands).

    NOTE: Adapter usage monitoring (modality switcher) is deprecated.
    Use session and project commands for Empirica monitoring.
    """
    try:
        print("\n📊 Empirica Usage Monitor")
        print("=" * 70)

        print("\n⚠️  Adapter Monitoring Deprecated")
        print("-" * 70)
        print("The modality switcher (adapter routing) feature has been deprecated.")
        print("Adapter usage statistics are no longer tracked.")

        print("\n💡 Alternative Monitoring Commands:")
        print("-" * 70)
        print("   empirica sessions-list          - View session history")
        print("   empirica project-bootstrap      - View project state")
        print("   empirica efficiency-report      - View token efficiency")
        print("   empirica query findings         - View learnings")
        print("   empirica query issues           - View auto-captured issues")

        print("\n📈 Session Statistics:")
        print("-" * 70)

        # Try to show basic session stats from Empirica core
        try:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            sessions = db.get_all_sessions(limit=5)
            db.close()

            if sessions:
                print(f"   Recent sessions: {len(sessions)}")
                for s in sessions[:3]:
                    print(f"     • {s.get('session_id', 'N/A')[:8]}... ({s.get('ai_id', 'unknown')})")
            else:
                print("   No sessions recorded yet")
        except Exception:
            print("   Session data unavailable")

        print("=" * 70)

    except Exception as e:
        handle_cli_error(e, "Monitor", getattr(args, 'verbose', False))


def _display_turtle_health():
    """Display epistemic health metrics (the turtle view)."""
    print("\n" + "=" * 70)
    print("🐢 Epistemic Health (Turtles All The Way Down)")
    print("=" * 70)

    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.data.flow_state_calculator import calculate_flow_score, classify_flow_state, identify_flow_blockers
        from empirica.utils.session_resolver import get_latest_session_id

        db = SessionDatabase()

        # Get current session
        try:
            session_id = get_latest_session_id(ai_id='claude-code', active_only=True)
        except ValueError:
            session_id = None

        if not session_id:
            print("\n   ⚠️  No active session found")
            print("   Run: empirica session-create --ai-id <your-id>")
            return

        # Get project_id for this session
        cursor = db.conn.cursor()
        cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        project_id = row[0] if row else None

        # Get latest vectors for flow calculation
        cursor.execute("""
            SELECT engagement, know, do, context, clarity, coherence,
                   signal, density, state, change, completion, impact, uncertainty
            FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()

        vectors = {}
        if row:
            vector_names = ['engagement', 'know', 'do', 'context', 'clarity', 'coherence',
                           'signal', 'density', 'state', 'change', 'completion', 'impact', 'uncertainty']
            vectors = {name: val for name, val in zip(vector_names, row) if val is not None}

        # Flow State (using vector-based calculator)
        print("\n   ✨ Flow State")
        print("   " + "-" * 40)

        if vectors:
            flow_score = calculate_flow_score(vectors)
            flow_state, flow_emoji = classify_flow_state(flow_score)
            print(f"   Current: {flow_emoji} {flow_state} ({flow_score:.1f}/100)")

            # Show blockers if any
            blockers = identify_flow_blockers(vectors)
            if blockers:
                print(f"   Blockers: {blockers[0]}")
        else:
            print("   ⚠️  No vectors recorded - run PREFLIGHT first")

        # CASCADE Completeness
        print("\n   🔄 CASCADE Completeness")
        print("   " + "-" * 40)
        cursor.execute("""
            SELECT phase, COUNT(*) as count
            FROM reflexes
            WHERE session_id = ?
            GROUP BY phase
        """, (session_id,))
        phases = {row[0]: row[1] for row in cursor.fetchall()}

        has_preflight = phases.get('PREFLIGHT', 0) > 0
        has_check = phases.get('CHECK', 0) > 0
        has_postflight = phases.get('POSTFLIGHT', 0) > 0

        cascade_parts = []
        cascade_parts.append("✅ PREFLIGHT" if has_preflight else "⬜ PREFLIGHT")
        cascade_parts.append("✅ CHECK" if has_check else "⬜ CHECK")
        cascade_parts.append("✅ POSTFLIGHT" if has_postflight else "⬜ POSTFLIGHT")
        print(f"   {' → '.join(cascade_parts)}")

        completeness = sum([has_preflight, has_postflight]) / 2 * 100
        print(f"   Completeness: {completeness:.0f}%")

        # Unknowns/Findings Ratio
        if project_id:
            print("\n   📊 Knowledge State")
            print("   " + "-" * 40)
            cursor.execute("SELECT COUNT(*) FROM project_findings WHERE project_id = ?", (project_id,))
            findings_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM project_unknowns WHERE project_id = ? AND is_resolved = 0", (project_id,))
            unknowns_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM project_unknowns WHERE project_id = ? AND is_resolved = 1", (project_id,))
            resolved_count = cursor.fetchone()[0]

            print(f"   Findings: {findings_count} | Unknowns: {unknowns_count} open, {resolved_count} resolved")

            if unknowns_count + findings_count > 0:
                knowledge_ratio = findings_count / (unknowns_count + findings_count) * 100
                bar_len = int(knowledge_ratio / 5)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                print(f"   Knowledge: [{bar}] {knowledge_ratio:.0f}%")

        # Latest vectors
        print("\n   📈 Latest Vectors")
        print("   " + "-" * 40)
        cursor.execute("""
            SELECT know, uncertainty, engagement, completion
            FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        if row:
            know, unc, eng, comp = row
            print(f"   know={know:.2f}  uncertainty={unc:.2f}  engagement={eng:.2f}  completion={comp:.2f}")
        else:
            print("   No vectors recorded yet")

        db.close()

    except Exception as e:
        logger.warning(f"Turtle health check failed: {e}")
        print(f"\n   ⚠️  Could not load epistemic health: {e}")


def handle_monitor_export_command(args):
    """
    Export monitoring data to file.
    
    Supports JSON and CSV formats.
    """
    try:
        print("\n📤 Exporting Monitoring Data")
        print("=" * 70)
        
        monitor = UsageMonitor()
        stats = monitor.get_stats()
        
        output_format = getattr(args, 'format', 'json')
        output_file = getattr(args, 'output', None) or getattr(args, 'export', None)
        
        if output_format == 'json':
            # Export as JSON
            with open(output_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"\n✅ Exported to JSON: {output_file}")
            
        elif output_format == 'csv':
            # Export history as CSV
            import csv
            
            history = stats.get("history", [])
            
            if not history:
                print("⚠️  No history to export")
                return
            
            with open(output_file, 'w', newline='') as f:
                fieldnames = ['timestamp', 'adapter', 'success', 'tokens', 'cost', 'latency']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in history:
                    writer.writerow({k: record.get(k, '') for k in fieldnames})
            
            print(f"\n✅ Exported to CSV: {output_file}")
            print(f"   Records: {len(history)}")
        
        print("=" * 70)
        
    except Exception as e:
        handle_cli_error(e, "Monitor Export", getattr(args, 'verbose', False))


def handle_monitor_reset_command(args):
    """
    Reset monitoring statistics.
    
    Clears all recorded data.
    """
    try:
        print("\n🔄 Resetting Monitoring Statistics")
        print("=" * 70)
        
        # Confirm unless --yes flag
        if not getattr(args, 'yes', False):
            confirm = input("\n⚠️  This will clear all monitoring data. Continue? [y/N]: ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ Reset cancelled")
                return
        
        monitor = UsageMonitor()
        monitor.reset_stats()
        
        print("\n✅ Statistics reset")
        print(f"   Stats file: {monitor.stats_file}")
        print("=" * 70)
        
    except Exception as e:
        handle_cli_error(e, "Monitor Reset", getattr(args, 'verbose', False))


def handle_monitor_cost_command(args):
    """
    Display cost analysis.
    
    Shows detailed cost breakdown by adapter and time period.
    """
    try:
        print("\n💰 Cost Analysis")
        print("=" * 70)
        
        monitor = UsageMonitor()
        stats = monitor.get_stats()
        
        total_cost = stats.get("total_cost", 0.0)
        adapters_stats = stats.get("adapters", {})
        
        print(f"\n📊 Total Cost: ${total_cost:.4f}")
        
        print("\n" + "=" * 70)
        print("Cost by Adapter:")
        print("=" * 70)
        
        for adapter, data in sorted(adapters_stats.items(), key=lambda x: x[1].get('cost', 0.0), reverse=True):
            cost = data.get("cost", 0.0)
            requests = data.get("requests", 0)
            
            if cost > 0:
                percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                avg_cost = cost / requests if requests > 0 else 0
                
                print(f"\n🔹 {adapter.upper()}")
                print(f"   Total:       ${cost:.4f} ({percentage:.1f}%)")
                print(f"   Avg/Request: ${avg_cost:.6f}")
                print(f"   Requests:    {requests:,}")
        
        # Project costs
        if getattr(args, 'project', False):
            print("\n" + "=" * 70)
            print("📈 Cost Projections")
            print("=" * 70)
            
            total_requests = stats.get("total_requests", 0)
            
            if total_requests > 0:
                avg_cost_per_request = total_cost / total_requests
                
                print(f"\n   Average cost per request: ${avg_cost_per_request:.6f}")
                print(f"\n   Projected costs:")
                print(f"      100 requests:   ${avg_cost_per_request * 100:.2f}")
                print(f"      1,000 requests: ${avg_cost_per_request * 1000:.2f}")
                print(f"      10,000 requests: ${avg_cost_per_request * 10000:.2f}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        handle_cli_error(e, "Cost Analysis", getattr(args, 'verbose', False))


def handle_pre_summary_snapshot(session_id: str, output_format: str, cycle=None, round_num=None, scope_depth=None):
    """
    Pre-summary trigger: Save current checkpoint as ref-doc.

    Creates a snapshot of current epistemic state BEFORE memory compacting.
    Saved as ref-doc in .empirica/ref-docs/pre_summary_<timestamp>.json

    This ref-doc becomes the anchor for post-summary drift detection.
    """
    from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
    from empirica.data.session_database import SessionDatabase
    from datetime import datetime, timezone
    from pathlib import Path
    import json

    # Load current checkpoint (most recent epistemic state)
    git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
    checkpoints = git_logger.list_checkpoints(limit=1)

    if not checkpoints:
        if output_format == 'json':
            print(json.dumps({
                "ok": False,
                "error": "No checkpoints found for session",
                "message": "Run PREFLIGHT or CHECK to create a checkpoint first",
                "session_id": session_id
            }))
            return
        else:
            print("\n📸 Pre-Summary Snapshot")
            print("=" * 70)
            print(f"   Session ID: {session_id}")
            print("=" * 70)
            print("\n⚠️  No checkpoints found for session")
            print("   Run PREFLIGHT or CHECK to create a checkpoint first")
            return

    # Print header only for human output
    if output_format != 'json':
        print("\n📸 Pre-Summary Snapshot")
        print("=" * 70)
        print(f"   Session ID: {session_id}")
        print("=" * 70)

    current_checkpoint = checkpoints[0]

    # Also capture bootstrap snapshot
    db = SessionDatabase()
    try:
        # Get project_id from session
        session_data = db.get_session(session_id)
        project_id = session_data.get('project_id') if session_data else None

        bootstrap = db.bootstrap_project_breadcrumbs(
            project_id=project_id,
            check_integrity=False
        ) if project_id else {}
    except Exception as e:
        logger.warning(f"Could not load bootstrap: {e}")
        bootstrap = {}

    # Get MCO configuration for this session
    from empirica.config.mco_loader import get_mco_config
    mco = get_mco_config()

    # Get AI ID from session to infer model/persona
    ai_id = session_data.get('ai_id') if session_data else None

    # Export MCO snapshot
    mco_snapshot = mco.export_snapshot(
        session_id=session_id,
        ai_id=ai_id,
        cascade_style='default'  # TODO: Track active cascade_style in session
    )

    # Create ref-doc snapshot
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    snapshot = {
        "type": "pre_summary_snapshot",
        "session_id": session_id,
        "timestamp": timestamp,
        "checkpoint": current_checkpoint,
        "investigation_context": {
            "cycle": cycle,
            "round": round_num,
            "scope_depth": scope_depth
        },
        "bootstrap_summary": {
            "findings_count": len(bootstrap.get('findings', [])),
            "unknowns_count": len(bootstrap.get('unknowns', [])),
            "goals_count": len(bootstrap.get('goals', [])),
            "dead_ends_count": len(bootstrap.get('dead_ends', []))
        },
        "mco_config": mco_snapshot  # ← NEW: MCO configuration preserved
    }

    # Save as ref-doc
    ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
    ref_docs_dir.mkdir(parents=True, exist_ok=True)

    ref_doc_path = ref_docs_dir / f"pre_summary_{timestamp}.json"

    with open(ref_doc_path, 'w') as f:
        json.dump(snapshot, f, indent=2)

    # Also add to database ref-docs table
    try:
        if project_id:
            db.add_reference_doc(
                project_id=project_id,
                doc_path=str(ref_doc_path),
                doc_type="pre_summary_snapshot",
                description=f"Pre-summary epistemic snapshot captured at {timestamp}"
            )
    except Exception as e:
        logger.warning(f"Could not add to ref-docs table: {e}")

    if output_format == 'json':
        print(json.dumps({
            "ok": True,
            "snapshot_path": str(ref_doc_path),
            "timestamp": timestamp,
            "session_id": session_id
        }))
    else:
        print(f"\n✅ Snapshot saved: {ref_doc_path.name}")
        print(f"   Vectors: {len(current_checkpoint.get('vectors', {}))}")
        print(f"   Findings: {snapshot['bootstrap_summary']['findings_count']}")
        print(f"   Unknowns: {snapshot['bootstrap_summary']['unknowns_count']}")
        print("\n💡 After summarization, run:")
        print(f"   empirica check-drift --session-id {session_id} --trigger post_summary")
        print("=" * 70)


def handle_post_summary_drift_check(session_id: str, output_format: str, signaling_level: str = 'default'):
    """
    Post-summary trigger: Compare current state to pre-summary snapshot.

    Loads pre-summary ref-doc + current bootstrap as anchor.
    Calculates drift between pre-compact vectors and current state.
    Detects sentinel gate triggers for critical drift thresholds.

    Signaling levels:
    - basic: Drift score + sentinel action only (minimal, for automation)
    - default: Key vectors (know, uncertainty, context, clarity) + sentinel
    - full: All 13 vectors + investigation context + bootstrap evidence

    This detects metacognitive drift from memory compacting.
    """
    from empirica.data.session_database import SessionDatabase
    from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
    from pathlib import Path
    import json

    db = SessionDatabase()

    # Find most recent pre-summary snapshot ref-doc
    ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"

    if not ref_docs_dir.exists():
        error_msg = "No ref-docs directory found. Run with --trigger pre_summary before memory compacting"
        if output_format == 'json':
            print(json.dumps({"ok": False, "error": error_msg}))
            return
        print(f"\n⚠️  {error_msg}")
        return

    # Find pre_summary files
    snapshot_files = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)

    if not snapshot_files:
        error_msg = "No pre-summary snapshot found. Run with --trigger pre_summary before memory compacting"
        if output_format == 'json':
            print(json.dumps({"ok": False, "error": error_msg}))
            return
        print(f"\n⚠️  {error_msg}")
        return

    # Load most recent snapshot
    snapshot_path = snapshot_files[0]

    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)

    # Get pre-compact vectors (from checkpoint or live_state)
    # Handle case where keys exist but values are None
    checkpoint_data = snapshot.get('checkpoint') or {}
    live_state_data = snapshot.get('live_state') or {}
    pre_vectors = checkpoint_data.get('vectors', {}) or live_state_data.get('vectors', {})
    pre_timestamp = snapshot.get('timestamp', 'Unknown')

    # Load current epistemic state
    try:
        git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
        checkpoints = git_logger.list_checkpoints(limit=1)
        # Guard against None checkpoint entries
        current_vectors = {}
        if checkpoints and checkpoints[0] is not None:
            current_vectors = checkpoints[0].get('vectors', {}) or {}
    except Exception as e:
        logger.warning(f"Could not load current checkpoint: {e}")
        current_vectors = {}

    # Load bootstrap for context
    try:
        session_data = db.get_session(session_id)
        project_id = session_data.get('project_id') if session_data else None

        bootstrap = db.generate_project_bootstrap(
            session_id=session_id,
            project_id=project_id,
            include_file_tree=False
        ) if project_id else {}
    except Exception as e:
        logger.warning(f"Could not load bootstrap: {e}")
        bootstrap = {}

    findings = bootstrap.get('findings', [])
    unknowns = bootstrap.get('unknowns', [])
    goals = bootstrap.get('goals', [])
    dead_ends = bootstrap.get('dead_ends', [])
    incomplete = [g for g in goals if g.get('status') != 'completed']

    # Calculate drift per vector
    drift_details = {}
    core_vectors = ['know', 'uncertainty', 'context', 'clarity', 'engagement', 'completion', 'impact']

    for key in core_vectors:
        pre_val = pre_vectors.get(key)
        post_val = current_vectors.get(key)
        if pre_val is not None and post_val is not None:
            drift_details[key] = post_val - pre_val

    # Calculate overall drift score (average absolute drift)
    if drift_details:
        drift_score = sum(abs(v) for v in drift_details.values()) / len(drift_details)
    else:
        drift_score = None

    # Sentinel gate detection (Traffic Light system thresholds)
    # Biological Dashboard Calibration:
    # - Crystalline (🔵): Delta < 0.1 - Ground truth
    # - Solid (🟢): 0.1 ≤ Delta < 0.2 - Working knowledge
    # - Emergent (🟡): 0.2 ≤ Delta < 0.3 - Forming understanding
    # - Flicker (🔴): 0.3 ≤ Delta < 0.4 - Active uncertainty
    # - Void (⚪): Delta ≥ 0.4 - Unknown territory
    sentinel_triggered = False
    sentinel_action = None

    if drift_score is not None:
        if drift_score >= 0.5:
            sentinel_triggered = True
            sentinel_action = 'HALT'  # ⛔ Critical drift - stop and review
        elif drift_score >= 0.4:
            sentinel_triggered = True
            sentinel_action = 'BRANCH'  # 🔱 Major drift - consider branching
        elif drift_score >= 0.3:
            sentinel_triggered = True
            sentinel_action = 'REVISE'  # 🔄 Significant drift - reassess
        # Below 0.3 - no sentinel trigger

    # Check for specific danger patterns
    know_drift = drift_details.get('know', 0)
    uncertainty_drift = drift_details.get('uncertainty', 0)

    # Pattern: Know dropped significantly AND uncertainty increased
    if know_drift < -0.3 and uncertainty_drift > 0.2:
        sentinel_triggered = True
        sentinel_action = 'LOCK'  # 🔒 Dangerous pattern - lock state before proceeding

    # Determine what to include based on signaling level
    key_vectors = ['know', 'uncertainty', 'context', 'clarity']
    all_vectors = ['know', 'uncertainty', 'context', 'clarity', 'engagement', 'completion', 'impact',
                   'do', 'coherence', 'signal', 'density', 'state', 'change']

    # JSON output for hooks/automation
    if output_format == 'json':
        if signaling_level == 'basic':
            # Minimal output - just what automation needs
            output = {
                "ok": True,
                "drift_score": drift_score,
                "sentinel_triggered": sentinel_triggered,
                "sentinel_action": sentinel_action
            }
        elif signaling_level == 'default':
            # Standard output - key vectors
            key_drift = {k: v for k, v in drift_details.items() if k in key_vectors}
            output = {
                "ok": True,
                "session_id": session_id,
                "drift_score": drift_score,
                "drift_details": key_drift,
                "sentinel_triggered": sentinel_triggered,
                "sentinel_action": sentinel_action,
                "pre_vectors": {k: pre_vectors.get(k) for k in key_vectors if pre_vectors.get(k) is not None},
                "current_vectors": {k: current_vectors.get(k) for k in key_vectors if current_vectors.get(k) is not None}
            }
        else:  # full
            # Complete output - everything
            output = {
                "ok": True,
                "session_id": session_id,
                "drift_score": drift_score,
                "drift_details": drift_details,
                "sentinel_triggered": sentinel_triggered,
                "sentinel_action": sentinel_action,
                "pre_summary": {
                    "timestamp": pre_timestamp,
                    "vectors": pre_vectors,
                    "snapshot_path": str(snapshot_path)
                },
                "current_state": {
                    "vectors": current_vectors
                },
                "bootstrap": {
                    "findings_count": len(findings),
                    "unknowns_count": len(unknowns),
                    "goals_count": len(goals),
                    "incomplete_goals": len(incomplete),
                    "dead_ends_count": len(dead_ends)
                },
                "investigation_context": snapshot.get('investigation_context', {})
            }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    # Traffic light emoji based on drift
    def get_drift_display(score):
        if score is None:
            return "⚪", "Unknown"
        elif score < 0.1:
            return "🔵", "Crystalline"
        elif score < 0.2:
            return "🟢", "Solid"
        elif score < 0.3:
            return "🟡", "Emergent"
        elif score < 0.4:
            return "🔴", "Flicker"
        else:
            return "⚪", "Void"

    emoji, level = get_drift_display(drift_score)

    if signaling_level == 'basic':
        # Basic: One-line summary
        if drift_score is not None:
            line = f"{emoji} Drift: {drift_score:.1%} ({level})"
            if sentinel_triggered:
                sentinel_emoji = {'HALT': '⛔', 'BRANCH': '🔱', 'REVISE': '🔄', 'LOCK': '🔒'}.get(sentinel_action, '⚠️')
                line += f" | {sentinel_emoji} {sentinel_action}"
            print(line)
        else:
            print("⚪ Drift: N/A (no vector data)")
        return

    elif signaling_level == 'default':
        # Default: Key vectors with sentinel
        print(f"\n{emoji} Post-Compact Drift: {drift_score:.1%} ({level})" if drift_score else "\n⚪ Drift: Unknown")

        if sentinel_triggered:
            sentinel_emoji = {'HALT': '⛔', 'BRANCH': '🔱', 'REVISE': '🔄', 'LOCK': '🔒'}.get(sentinel_action, '⚠️')
            print(f"{sentinel_emoji} SENTINEL: {sentinel_action}")

        if drift_details:
            print("\nKey Vectors:")
            for key in key_vectors:
                if key in drift_details:
                    value = drift_details[key]
                    direction = "↑" if value > 0 else "↓" if value < 0 else "→"
                    # Vector-specific interpretation
                    if key == "uncertainty":
                        status = "🟢" if value <= 0 else "🔴"
                    elif key == "know":
                        status = "🟢" if value >= 0 else "🔴"
                    else:
                        status = "🟡" if abs(value) > 0.1 else "⚪"
                    print(f"   {status} {key}: {direction} {abs(value):.2f}")
        return

    # Full: Complete analysis
    print("\n🔄 Post-Summary Drift Check (Full)")
    print("=" * 70)
    print(f"   Session ID: {session_id}")
    print("=" * 70)

    # Show drift analysis
    print("\n📊 DRIFT ANALYSIS:")
    print("=" * 70)

    if drift_score is not None:
        print(f"\n   Overall Drift: {emoji} {drift_score:.1%} ({level})")

        if sentinel_triggered:
            sentinel_emoji = {'HALT': '⛔', 'BRANCH': '🔱', 'REVISE': '🔄', 'LOCK': '🔒'}.get(sentinel_action, '⚠️')
            print(f"\n   {sentinel_emoji} SENTINEL GATE: {sentinel_action}")
            print(f"      Memory drift exceeded safety threshold. Human review recommended.")

        print("\n   Per-Vector Drift (All 13):")
        for key in all_vectors:
            if key in drift_details:
                value = drift_details[key]
                direction = "↑" if value > 0 else "↓" if value < 0 else "→"
                # Color code based on significance
                if abs(value) >= 0.3:
                    marker = "🔴"
                elif abs(value) >= 0.2:
                    marker = "🟡"
                elif abs(value) >= 0.1:
                    marker = "🟢"
                else:
                    marker = "⚪"
                print(f"      {marker} {key}: {direction} {abs(value):.2f}")
            elif key in pre_vectors or key in current_vectors:
                print(f"      ⚪ {key}: (partial data)")
    else:
        print("\n   ⚠️  Could not calculate drift (missing vector data)")

    # Show pre-summary state
    print("\n📊 PRE-COMPACT STATE:")
    print("=" * 70)
    print(f"\n   Captured: {pre_timestamp}")
    for key in all_vectors:
        val = pre_vectors.get(key)
        if val is not None:
            print(f"   {key.upper()}: {val:.2f}")

    # Show current state
    print("\n📊 CURRENT STATE:")
    print("=" * 70)
    for key in all_vectors:
        val = current_vectors.get(key)
        if val is not None:
            print(f"   {key.upper()}: {val:.2f}")

    # Show investigation context from snapshot
    inv_context = snapshot.get('investigation_context', {})
    if any(inv_context.values()):
        print("\n🔬 INVESTIGATION CONTEXT:")
        print("=" * 70)
        if inv_context.get('cycle'):
            print(f"   Cycle: {inv_context['cycle']}")
        if inv_context.get('round'):
            print(f"   Round: {inv_context['round']}")
        if inv_context.get('scope_depth') is not None:
            depth_label = "surface" if inv_context['scope_depth'] < 0.4 else "moderate" if inv_context['scope_depth'] < 0.7 else "deep"
            print(f"   Scope Depth: {inv_context['scope_depth']:.2f} ({depth_label})")

    # Show bootstrap context
    print("\n📚 BOOTSTRAP EVIDENCE:")
    print("=" * 70)
    print(f"   Findings: {len(findings)}")
    print(f"   Unknowns: {len(unknowns)}")
    print(f"   Goals: {len(goals)} ({len(incomplete)} incomplete)")
    print(f"   Dead Ends: {len(dead_ends)}")

    print("\n" + "=" * 70)


def handle_check_drift_command(args):
    """
    Check for epistemic drift by comparing current state to historical baselines.

    Uses MirrorDriftMonitor to detect unexpected drops in epistemic vectors
    that indicate memory corruption, context loss, or other drift.

    Trigger modes:
    - manual: Standard drift check against historical baselines
    - pre_summary: Save current checkpoint as ref-doc before memory compacting
    - post_summary: Compare current state to pre-summary ref-doc using bootstrap as anchor
    """
    try:
        from empirica.core.drift.mirror_drift_monitor import MirrorDriftMonitor
        from empirica.core.canonical.empirica_git.checkpoint_manager import CheckpointManager
        from empirica.data.session_database import SessionDatabase
        from datetime import datetime, timezone
        from pathlib import Path

        session_id = args.session_id
        trigger = getattr(args, 'trigger', 'manual')
        threshold = getattr(args, 'threshold', 0.2)
        lookback = getattr(args, 'lookback', 5)
        cycle = getattr(args, 'cycle', None)
        round_num = getattr(args, 'round', None)
        scope_depth = getattr(args, 'scope_depth', None)
        signaling_level = getattr(args, 'signaling', 'default')
        output_format = getattr(args, 'output', 'human')

        # Handle pre-summary trigger: Save checkpoint as ref-doc
        if trigger == 'pre_summary':
            return handle_pre_summary_snapshot(session_id, output_format, cycle, round_num, scope_depth)

        # Handle post-summary trigger: Compare with pre-summary ref-doc
        if trigger == 'post_summary':
            return handle_post_summary_drift_check(session_id, output_format, signaling_level)

        # Manual mode: Standard drift detection
        # Only print header for human-readable output
        if output_format != 'json':
            print("\n🔍 Epistemic Drift Detection")
            print("=" * 70)
            print(f"   Session ID:  {session_id}")
            print(f"   Threshold:   {threshold}")
            print(f"   Lookback:    {lookback} checkpoints")
            if cycle is not None:
                print(f"   Cycle:       {cycle}")
            if round_num is not None:
                print(f"   Round:       {round_num}")
            if scope_depth is not None:
                depth_label = "surface" if scope_depth < 0.4 else "moderate" if scope_depth < 0.7 else "deep"
                print(f"   Scope Depth: {scope_depth:.2f} ({depth_label})")
            print("=" * 70)

        # Load current epistemic state from latest checkpoint (using git notes, not commit history)
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
        checkpoints = git_logger.list_checkpoints(limit=lookback)

        if not checkpoints:
            print("\n⚠️  No checkpoints found for session")
            print("   Run PREFLIGHT or CHECK to create a checkpoint first")
            return

        current_checkpoint = checkpoints[0]

        # Guard against None checkpoint entries
        if current_checkpoint is None:
            print("\n⚠️  Checkpoint data is invalid (None)")
            print("   Run PREFLIGHT or CHECK to create a valid checkpoint")
            return

        # Create mock assessment from checkpoint vectors
        class MockAssessment:
            def __init__(self, vectors):
                for name, score in (vectors or {}).items():
                    setattr(self, name, type('VectorState', (), {'score': score})())

        current_assessment = MockAssessment(current_checkpoint.get('vectors', {}))

        # Run drift detection (disable logging for JSON output to keep it clean)
        monitor = MirrorDriftMonitor(
            drift_threshold=threshold,
            lookback_window=lookback,
            enable_logging=(output_format != 'json')
        )

        report = monitor.detect_drift(current_assessment, session_id)

        # Output results
        if output_format == 'json':
            # JSON output
            output = {
                'session_id': session_id,
                'drift_detected': report.drift_detected,
                'severity': report.severity,
                'recommended_action': report.recommended_action,
                'drifted_vectors': report.drifted_vectors,
                'pattern': report.pattern,
                'pattern_confidence': report.pattern_confidence,
                'checkpoints_analyzed': report.checkpoints_analyzed,
                'reason': report.reason
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print("\n📊 Drift Analysis Results")
            print("=" * 70)

            if not report.drift_detected:
                print("\n✅ No drift detected")
                print(f"   Epistemic state is stable")
                if report.reason:
                    print(f"   Reason: {report.reason}")
            else:
                # Pattern-aware display
                if report.pattern == 'TRUE_DRIFT':
                    print(f"\n🔴 TRUE DRIFT DETECTED (Memory Loss)")
                    print(f"   Pattern: KNOW↓ + CLARITY↓ + CONTEXT↓")
                    print(f"   Confidence: {report.pattern_confidence:.2f}")
                    print(f"   ⚠️  CHECK BREADCRUMBS - Possible context loss")
                elif report.pattern == 'LEARNING':
                    print(f"\n✅ LEARNING PATTERN (Discovering Complexity)")
                    print(f"   Pattern: KNOW↓ + CLARITY↑")
                    print(f"   Confidence: {report.pattern_confidence:.2f}")
                    print(f"   ℹ️  This is healthy - discovering what you don't know")
                elif report.pattern == 'SCOPE_DRIFT':
                    print(f"\n⚠️  SCOPE DRIFT DETECTED (Task Expansion)")
                    print(f"   Pattern: KNOW↓ + scope indicators↑")
                    print(f"   Confidence: {report.pattern_confidence:.2f}")
                    print(f"   💡 Consider running PREFLIGHT on expanded scope")
                else:
                    severity_emoji = {
                        'low': '⚠️ ',
                        'medium': '⚠️ ',
                        'high': '🚨',
                        'critical': '🛑'
                    }.get(report.severity, '⚠️ ')
                    print(f"\n{severity_emoji} DRIFT DETECTED")

                print(f"\n   Severity: {report.severity.upper()}")
                print(f"   Recommended Action: {report.recommended_action.replace('_', ' ').upper()}")
                print(f"   Checkpoints Analyzed: {report.checkpoints_analyzed}")

                print("\n🔻 Drifted Vectors:")
                print("=" * 70)

                for vec in report.drifted_vectors:
                    vector_name = vec['vector']
                    baseline = vec['baseline']
                    current = vec['current']
                    drift = vec['drift']
                    vec_severity = vec['severity']

                    print(f"\n   {vector_name.upper()}")
                    print(f"      Baseline:  {baseline:.2f}")
                    print(f"      Current:   {current:.2f}")
                    print(f"      Drift:     -{drift:.2f} ({vec_severity})")

                # Recommendations
                print("\n💡 Recommendations:")
                print("=" * 70)

                if report.recommended_action == 'stop_and_reassess':
                    print("   🛑 STOP: Severe drift detected")
                    print("   → Review session history")
                    print("   → Check for context loss or memory corruption")
                    print("   → Consider restarting session with fresh context")
                elif report.recommended_action == 'investigate':
                    print("   🔍 INVESTIGATE: Significant drift detected")
                    print("   → Review recent work for quality")
                    print("   → Check if epistemic state accurately reflects knowledge")
                    print("   → Consider running CHECK assessment")
                elif report.recommended_action == 'monitor_closely':
                    print("   👀 MONITOR: Moderate drift detected")
                    print("   → Continue work but watch for further drift")
                    print("   → Run periodic drift checks")
                else:
                    print("   ✅ Continue work as normal")

            print("\n" + "=" * 70)

    except Exception as e:
        handle_cli_error(e, "Check Drift", getattr(args, 'verbose', False))


def handle_mco_load_command(args):
    """
    Load and present MCO (Meta-Agent Configuration Object) configuration.

    Used for:
    1. Session start - Load fresh MCO config for AI
    2. Post-compact - Reload MCO config from pre-summary snapshot
    3. Manual query - Check active MCO configuration

    Args from argparse:
        session_id: Session identifier (optional)
        ai_id: AI identifier (optional, for model/persona inference)
        snapshot: Path to pre_summary snapshot (optional, for post-compact reload)
        model: Explicit model override (optional)
        persona: Explicit persona override (optional)
        output: Output format ('json' or 'human', default 'human')
    """
    from empirica.config.mco_loader import get_mco_config
    from empirica.data.session_database import SessionDatabase
    from pathlib import Path
    import json

    try:
        session_id = getattr(args, 'session_id', None)
        ai_id = getattr(args, 'ai_id', None)
        snapshot_path = getattr(args, 'snapshot', None)
        model = getattr(args, 'model', None)
        persona = getattr(args, 'persona', None)
        output_format = getattr(args, 'output', 'human')

        mco = get_mco_config()

        # Load from snapshot if post-compact
        if snapshot_path:
            try:
                with open(snapshot_path) as f:
                    snapshot_data = json.load(f)
                    mco_snapshot = snapshot_data.get('mco_config', {})

                if not mco_snapshot:
                    if output_format == 'json':
                        print(json.dumps({
                            "ok": False,
                            "error": "No MCO config found in snapshot",
                            "message": "Snapshot may be from older version before MCO integration"
                        }))
                    else:
                        print("\n⚠️  No MCO Configuration in Snapshot")
                        print("=" * 70)
                        print("   This snapshot was created before MCO integration.")
                        print("   Falling back to fresh MCO load from files...")
                        print("=" * 70)
                        # Fall through to fresh load
                    snapshot_path = None

                else:
                    formatted = mco.format_for_prompt(mco_snapshot)

                    if output_format == 'json':
                        print(json.dumps({
                            "ok": True,
                            "source": "pre_summary_snapshot",
                            "snapshot_path": snapshot_path,
                            "mco_config": mco_snapshot,
                            "formatted": formatted
                        }))
                    else:
                        print("\n🔧 MCO Configuration (Post-Compact Reload)")
                        print("=" * 70)
                        print(f"   Source: {snapshot_path}")
                        print("=" * 70)
                        print(formatted)
                        print("\n💡 Your configuration has been restored from pre-compact snapshot.")
                        print("   Apply these bias corrections when doing PREFLIGHT/CHECK/POSTFLIGHT.")

                    return

            except Exception as e:
                logger.error(f"Failed to load snapshot: {e}")
                if output_format == 'json':
                    print(json.dumps({"ok": False, "error": str(e)}))
                else:
                    print(f"\n❌ Error loading snapshot: {e}")
                return

        # Fresh load from MCO files
        if session_id:
            db = SessionDatabase()
            try:
                session_data = db.get_session(session_id)
                if session_data:
                    ai_id = ai_id or session_data.get('ai_id')
            except:
                pass

        # Export snapshot
        mco_snapshot = mco.export_snapshot(
            session_id=session_id or 'unknown',
            ai_id=ai_id,
            model=model,
            persona=persona,
            cascade_style='default'
        )

        formatted = mco.format_for_prompt(mco_snapshot)

        if output_format == 'json':
            print(json.dumps({
                "ok": True,
                "source": "mco_files",
                "session_id": session_id,
                "ai_id": ai_id,
                "mco_config": mco_snapshot,
                "formatted": formatted
            }))
        else:
            print("\n🔧 MCO Configuration (Fresh Load)")
            print("=" * 70)
            if session_id:
                print(f"   Session ID: {session_id}")
            if ai_id:
                print(f"   AI ID: {ai_id}")
            print("=" * 70)
            print(formatted)
            print("\n💡 Internalize these values. Apply bias corrections during CASCADE assessments.")

    except Exception as e:
        handle_cli_error(e, "MCO Load", getattr(args, 'verbose', False))


def handle_assess_state_command(args):
    """
    Capture sessionless epistemic state (fresh measurement without session context).

    Used for:
    - Statusline displays (current epistemic state)
    - Pre-compact snapshots (fresh vectors before memory compacting)
    - Post-compact snapshots (fresh vectors after memory compacting)
    - Monitoring dashboards (current epistemic health)

    Unlike check-drift (which compares states), assess-state captures a fresh measurement.
    Not stored in reflexes table (sessionless), can be included in snapshots.

    Output:
    - JSON: Just vectors and metadata
    - Human: Formatted display with context
    """
    try:
        from datetime import datetime, timezone
        import json

        session_id = getattr(args, 'session_id', None)
        prompt = getattr(args, 'prompt', None)
        output_format = getattr(args, 'output', 'human')
        verbose = getattr(args, 'verbose', False)

        # Print header only for human output
        if output_format != 'json':
            print("\n🔍 Epistemic State Assessment (Sessionless)")
            print("=" * 70)
            if session_id:
                print(f"   Session ID: {session_id}")
            if prompt:
                print(f"   Context: {prompt[:60]}...")
            print("=" * 70)

        # If session_id provided, load last checkpoint as reference
        vectors = {}
        checkpoint_data = {}

        if session_id:
            # Try git notes first (canonical source)
            try:
                from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
                git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
                checkpoints = git_logger.list_checkpoints(limit=1)

                if checkpoints and checkpoints[0] is not None:
                    checkpoint_data = checkpoints[0]
                    vectors = checkpoint_data.get('vectors', {}) or {}
            except Exception as e:
                if verbose:
                    logger.warning(f"Could not load checkpoint from git notes: {e}")

            # Fallback to reflexes table if git notes empty
            if not vectors:
                try:
                    from empirica.data.session_database import SessionDatabase
                    db = SessionDatabase()
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT engagement, know, do, context, clarity, coherence,
                               signal, density, state, change, completion, impact, uncertainty
                        FROM reflexes
                        WHERE session_id = ?
                        ORDER BY timestamp DESC LIMIT 1
                    """, (session_id,))
                    row = cursor.fetchone()
                    db.close()

                    if row:
                        vectors = {
                            'engagement': row[0], 'know': row[1], 'do': row[2],
                            'context': row[3], 'clarity': row[4], 'coherence': row[5],
                            'signal': row[6], 'density': row[7], 'state': row[8],
                            'change': row[9], 'completion': row[10], 'impact': row[11],
                            'uncertainty': row[12]
                        }
                        # Filter None values
                        vectors = {k: v for k, v in vectors.items() if v is not None}
                        checkpoint_data = {'vectors': vectors, 'source': 'reflexes_table'}
                except Exception as e:
                    if verbose:
                        logger.warning(f"Could not load checkpoint from reflexes: {e}")

        # Capture fresh state
        # In production, this would call into an LLM or use cached epistemic state
        # For now, return the last known checkpoint vectors with metadata
        state = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'vectors': vectors,
            'has_session': session_id is not None,
            'has_checkpoint': bool(checkpoint_data),
            'prompt_context': prompt is not None
        }

        # Output results
        if output_format == 'json':
            print(json.dumps({
                'ok': True,
                'state': state,
                'session_id': session_id,
                'timestamp': state['timestamp']
            }))
        else:
            print("\n📊 Current Epistemic Vectors:")
            print("-" * 70)
            if vectors:
                for key, value in sorted(vectors.items()):
                    if isinstance(value, (int, float)):
                        bar_length = int(value * 20)
                        bar = "█" * bar_length + "░" * (20 - bar_length)
                        print(f"   {key:20s} {value:5.2f}  {bar}")
                    else:
                        print(f"   {key:20s} {str(value)}")
            else:
                print("   ⚠️  No vectors available")
                print("   Run PREFLIGHT or CHECK to establish baseline")
            print("-" * 70)
            print(f"\n   Timestamp: {state['timestamp']}")
            if session_id:
                print(f"   Session:   {session_id}")
            print()

        # TURTLE MODE: Recursive grounding check (Noetic Handshake)
        if getattr(args, 'turtle', False):
            _display_turtle_stack(vectors, session_id, prompt)

    except Exception as e:
        handle_cli_error(e, "Assess State", getattr(args, 'verbose', False))


def _display_turtle_stack(vectors: dict, session_id: str = None, prompt: str = None):
    """
    Display recursive grounding stack trace (the Noetic Handshake).

    Verifies observer stability before observing by checking grounding layers:
    - Layer 0: User Intent (can we parse the request?)
    - Layer 1: Noetic Grasp (do we understand the concept?)
    - Layer 2: Praxic Path (can we execute?)
    - Layer 3: Epistemic Safety (is uncertainty below threshold?)
    """
    print("\n" + "=" * 70)
    print("🐢 TURTLE STACK REPORT (Recursive Grounding Check)")
    print("=" * 70)

    # Moon phase indicators based on confidence levels
    def get_moon_phase(score: float) -> tuple:
        """Return (emoji, status) based on score."""
        if score >= 0.85:
            return "🌕", "CRYSTALLINE"
        elif score >= 0.70:
            return "🌔", "SOLID"
        elif score >= 0.50:
            return "🌓", "EMERGENT"
        elif score >= 0.30:
            return "🌒", "FORMING"
        else:
            return "🌑", "DARK"

    # Calculate layer scores from vectors
    layers = []
    safe_to_proceed = True

    # Layer 0: User Intent (based on context + signal)
    context = vectors.get('context', 0.5)
    signal = vectors.get('signal', 0.5)
    layer0_score = (context + signal) / 2
    moon0, status0 = get_moon_phase(layer0_score)
    layers.append({
        'layer': 0,
        'name': 'USER INTENT',
        'score': layer0_score,
        'moon': moon0,
        'status': status0,
        'detail': f"Context={context:.2f}, Signal={signal:.2f}"
    })

    # Layer 1: Noetic Grasp (based on know + clarity + coherence)
    know = vectors.get('know', 0.5)
    clarity = vectors.get('clarity', 0.5)
    coherence = vectors.get('coherence', 0.5)
    layer1_score = (know + clarity + coherence) / 3
    moon1, status1 = get_moon_phase(layer1_score)
    layers.append({
        'layer': 1,
        'name': 'NOETIC GRASP',
        'score': layer1_score,
        'moon': moon1,
        'status': status1,
        'detail': f"Know={know:.2f}, Clarity={clarity:.2f}, Coherence={coherence:.2f}"
    })

    # Layer 2: Praxic Path (based on do + state + change)
    do = vectors.get('do', 0.5)
    state = vectors.get('state', 0.5)
    change = vectors.get('change', 0.5)
    layer2_score = (do + state + change) / 3
    moon2, status2 = get_moon_phase(layer2_score)
    layers.append({
        'layer': 2,
        'name': 'PRAXIC PATH',
        'score': layer2_score,
        'moon': moon2,
        'status': status2,
        'detail': f"Do={do:.2f}, State={state:.2f}, Change={change:.2f}"
    })

    # Layer 3: Epistemic Safety (based on uncertainty + engagement + impact)
    uncertainty = vectors.get('uncertainty', 0.5)
    engagement = vectors.get('engagement', 0.5)
    impact = vectors.get('impact', 0.5)
    # For safety, LOW uncertainty is GOOD, so we invert it
    safety_score = ((1 - uncertainty) + engagement + impact) / 3
    moon3, status3 = get_moon_phase(safety_score)
    layers.append({
        'layer': 3,
        'name': 'EPISTEMIC SAFETY',
        'score': safety_score,
        'moon': moon3,
        'status': status3,
        'detail': f"Uncertainty={uncertainty:.2f} (inverted), Engagement={engagement:.2f}"
    })

    # Display each layer
    for layer in layers:
        print(f"\n  🐢 [LAYER {layer['layer']}: {layer['name']}] -> {layer['moon']} {layer['status']}")
        print(f"     Score: {layer['score']:.2f} | {layer['detail']}")

        # Check for warnings
        if layer['score'] < 0.50:
            print(f"     ⚠️  Warning: {layer['name']} is below grounding threshold")
            safe_to_proceed = False
        elif layer['score'] < 0.70:
            print(f"     ⚡ Caution: {layer['name']} may need investigation")

    # Overall status
    print("\n" + "-" * 70)
    overall_score = sum(l['score'] for l in layers) / len(layers)
    overall_moon, overall_status = get_moon_phase(overall_score)

    if safe_to_proceed and overall_score >= 0.70:
        print(f"STATUS: {overall_moon} [{overall_status}] - SAFE TO PROCEED")
        print("        Observer is stable. Grounding verified.")
    elif safe_to_proceed and overall_score >= 0.50:
        print(f"STATUS: {overall_moon} [{overall_status}] - PROCEED WITH CAUTION")
        print("        Observer is forming. Consider CHECK before praxic action.")
    else:
        print(f"STATUS: {overall_moon} [{overall_status}] - HALT RECOMMENDED")
        print("        Observer is unstable. Run PREFLIGHT or investigate unknowns.")

    print("=" * 70)
    print()


def handle_trajectory_project_command(args):
    """
    Project viable epistemic paths forward based on current grounding.

    The Turtle Telescope: Uses current turtle stack + context to project
    which epistemic paths are viable given the observer's grounding state.

    Paths:
    - PRAXIC: Execute with confidence (grounding >= 0.70)
    - NOETIC-SHALLOW: Quick investigation (grounding 0.50-0.70)
    - NOETIC-DEEP: Thorough investigation (grounding < 0.50 or high unknowns)
    - SCOPE-EXPAND: Broaden task scope (requires high grounding + low unknowns)
    - HANDOFF: Transfer to different AI/session (unstable observer)
    - HALT: Stop and seek human guidance (critical issues)
    """
    import sqlite3
    from empirica.data.session_database import SessionDatabase
    from empirica.core.canonical.empirica_git import SentinelHooks
    from empirica.core.canonical.empirica_git.sentinel_hooks import auto_enable_sentinel
    auto_enable_sentinel()

    try:
        session_id = getattr(args, 'session_id', None)
        output_format = getattr(args, 'output', 'human')
        show_turtle = getattr(args, 'turtle', False)
        depth = getattr(args, 'depth', 3)
        verbose = getattr(args, 'verbose', False)

        db = SessionDatabase()

        # Get current vectors (same logic as assess-state)
        vectors = {}
        project_id = None

        if session_id:
            # Try to get vectors from last checkpoint
            from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

            try:
                reflex_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
                checkpoints = reflex_logger.list_checkpoints(session_id=session_id, limit=1)
                if checkpoints:
                    checkpoint = checkpoints[0]
                    vectors = checkpoint.get('vectors', {})
            except Exception:
                pass

            # Get project_id from session
            session = db.get_session(session_id)
            if session:
                project_id = session.get('project_id')

        # Fallback: get from reflexes table
        if not vectors:
            try:
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT know, do, context, clarity, coherence, signal, density,
                               engagement, state, change, completion, impact, uncertainty
                        FROM reflexes ORDER BY id DESC LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        vector_names = ['know', 'do', 'context', 'clarity', 'coherence', 'signal', 'density',
                                       'engagement', 'state', 'change', 'completion', 'impact', 'uncertainty']
                        vectors = {name: row[i] for i, name in enumerate(vector_names) if row[i] is not None}
            except Exception:
                pass

        # If still no vectors, use defaults
        if not vectors:
            vectors = {
                'know': 0.5, 'do': 0.5, 'context': 0.5, 'clarity': 0.5,
                'coherence': 0.5, 'signal': 0.5, 'density': 0.5,
                'engagement': 0.5, 'state': 0.5, 'change': 0.5,
                'completion': 0.5, 'impact': 0.5, 'uncertainty': 0.5
            }

        # Calculate turtle stack layers
        def get_moon_phase(score: float) -> tuple:
            if score >= 0.85:
                return "🌕", "CRYSTALLINE"
            elif score >= 0.70:
                return "🌔", "SOLID"
            elif score >= 0.50:
                return "🌓", "EMERGENT"
            elif score >= 0.30:
                return "🌒", "FORMING"
            else:
                return "🌑", "DARK"

        # Layer calculations
        layer0_score = (vectors.get('context', 0.5) + vectors.get('signal', 0.5)) / 2  # USER INTENT
        layer1_score = (vectors.get('know', 0.5) + vectors.get('clarity', 0.5) + vectors.get('coherence', 0.5)) / 3  # NOETIC GRASP
        layer2_score = (vectors.get('do', 0.5) + vectors.get('state', 0.5) + vectors.get('change', 0.5)) / 3  # PRAXIC PATH
        uncertainty = vectors.get('uncertainty', 0.5)
        layer3_score = ((1 - uncertainty) + vectors.get('engagement', 0.5) + vectors.get('impact', 0.5)) / 3  # EPISTEMIC SAFETY

        overall_grounding = (layer0_score + layer1_score + layer2_score + layer3_score) / 4
        overall_moon, overall_status = get_moon_phase(overall_grounding)

        layers = [
            {'name': 'USER INTENT', 'score': layer0_score, 'moon': get_moon_phase(layer0_score)},
            {'name': 'NOETIC GRASP', 'score': layer1_score, 'moon': get_moon_phase(layer1_score)},
            {'name': 'PRAXIC PATH', 'score': layer2_score, 'moon': get_moon_phase(layer2_score)},
            {'name': 'EPISTEMIC SAFETY', 'score': layer3_score, 'moon': get_moon_phase(layer3_score)},
        ]

        # Get unknowns and findings count
        unknowns_count = 0
        findings_count = 0

        if project_id:
            try:
                with sqlite3.connect(db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM project_unknowns WHERE project_id = ? AND is_resolved = 0", (project_id,))
                    unknowns_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM project_findings WHERE project_id = ?", (project_id,))
                    findings_count = cursor.fetchone()[0]
            except Exception:
                pass

        # Get Sentinel status if available
        sentinel_status = None
        sentinel_moon = None
        if SentinelHooks.is_enabled():
            turtle_result = SentinelHooks.turtle_check()
            sentinel_status = turtle_result.get('status')
            sentinel_moon = turtle_result.get('moon')

        # Calculate path viabilities
        paths = []

        # PRAXIC path - can we execute?
        praxic_confidence = min(layer1_score, layer2_score, layer3_score)
        praxic_viable = praxic_confidence >= 0.70 and unknowns_count <= 3
        praxic_blockers = []
        if layer1_score < 0.70:
            praxic_blockers.append(f"NOETIC GRASP too low ({layer1_score:.2f})")
        if layer2_score < 0.70:
            praxic_blockers.append(f"PRAXIC PATH unclear ({layer2_score:.2f})")
        if unknowns_count > 3:
            praxic_blockers.append(f"{unknowns_count} unknowns blocking")

        paths.append({
            'name': 'PRAXIC',
            'icon': '🟢' if praxic_viable else '🟡' if praxic_confidence >= 0.50 else '🔴',
            'confidence': praxic_confidence,
            'viable': praxic_viable,
            'description': 'Execute with confidence. Grounding supports action.',
            'blockers': praxic_blockers,
            'action': 'Enter praxic phase, implement the planned changes'
        })

        # NOETIC-SHALLOW path - quick investigation
        noetic_shallow_confidence = (layer0_score + layer1_score) / 2
        noetic_shallow_viable = 0.50 <= overall_grounding < 0.70 or (unknowns_count > 0 and unknowns_count <= 5)
        paths.append({
            'name': 'NOETIC-SHALLOW',
            'icon': '🟢' if noetic_shallow_viable else '🟡',
            'confidence': noetic_shallow_confidence,
            'viable': noetic_shallow_viable,
            'description': 'Quick targeted investigation. Address specific unknowns.',
            'blockers': [] if noetic_shallow_viable else ['Grounding too low for shallow investigation'],
            'action': f'Investigate {min(unknowns_count, 3)} unknowns, then re-CHECK'
        })

        # NOETIC-DEEP path - thorough investigation
        noetic_deep_confidence = layer0_score  # Only need USER INTENT to start deep investigation
        noetic_deep_viable = overall_grounding < 0.50 or unknowns_count > 5
        paths.append({
            'name': 'NOETIC-DEEP',
            'icon': '🟢' if noetic_deep_viable else '🟡',
            'confidence': noetic_deep_confidence,
            'viable': noetic_deep_viable,
            'description': 'Thorough investigation required. Many unknowns or low grounding.',
            'blockers': [] if noetic_deep_viable else ['Grounding sufficient for shallower path'],
            'action': 'Deep exploration, log findings, resolve unknowns before proceeding'
        })

        # SCOPE-EXPAND path - broaden task scope
        scope_expand_confidence = overall_grounding * (1 - (unknowns_count / 10)) if unknowns_count <= 10 else 0
        scope_expand_viable = overall_grounding >= 0.75 and unknowns_count <= 2 and scope_expand_confidence is not None
        scope_blockers = []
        if overall_grounding < 0.75:
            scope_blockers.append(f"Grounding ({overall_grounding:.2f}) < 0.75 threshold")
        if unknowns_count > 2:
            scope_blockers.append(f"{unknowns_count} unknowns would expand further")
        paths.append({
            'name': 'SCOPE-EXPAND',
            'icon': '🟢' if scope_expand_viable else '🔴',
            'confidence': max(0, scope_expand_confidence),
            'viable': scope_expand_viable,
            'description': 'Broaden task scope. Current grounding supports expansion.',
            'blockers': scope_blockers,
            'action': 'Add subtasks or related goals, then re-baseline with PREFLIGHT'
        })

        # HANDOFF path - transfer to different AI
        handoff_confidence = 1 - overall_grounding  # Inverse - more confident to handoff when grounding low
        handoff_viable = overall_grounding < 0.40 or (sentinel_status and sentinel_status in ['forming', 'dark'])
        paths.append({
            'name': 'HANDOFF',
            'icon': '🟡' if handoff_viable else '⚪',
            'confidence': handoff_confidence,
            'viable': handoff_viable,
            'description': 'Transfer to different AI/session. Observer stability questionable.',
            'blockers': [] if handoff_viable else ['Observer stable enough to continue'],
            'action': 'Create handoff artifact, transfer context to fresh session/AI'
        })

        # HALT path - stop and seek guidance
        halt_confidence = 1 - min(layer3_score, overall_grounding)  # High when safety/grounding low
        halt_viable = layer3_score < 0.30 or overall_grounding < 0.25
        paths.append({
            'name': 'HALT',
            'icon': '🔴' if halt_viable else '⚪',
            'confidence': halt_confidence,
            'viable': halt_viable,
            'description': 'Stop and seek human guidance. Critical grounding issues.',
            'blockers': [] if halt_viable else ['No critical issues detected'],
            'action': 'Escalate to human, do not proceed without guidance'
        })

        # Ensure all paths have valid viable values (defensive)
        for p in paths:
            if p['viable'] is None:
                p['viable'] = False
            if p['confidence'] is None:
                p['confidence'] = 0.0

        # Sort paths by viability first, then confidence (descending)
        paths.sort(key=lambda p: (-int(bool(p['viable'])), -p['confidence']))

        # Determine recommendation
        recommendation = paths[0]['name']
        recommendation_action = paths[0]['action']

        # Build result
        result = {
            'ok': True,
            'grounding': {
                'overall': overall_grounding,
                'moon': overall_moon,
                'status': overall_status,
                'layers': [{'name': l['name'], 'score': l['score'], 'moon': l['moon'][0], 'status': l['moon'][1]} for l in layers]
            },
            'context': {
                'session_id': session_id,
                'project_id': project_id,
                'unknowns_count': unknowns_count,
                'findings_count': findings_count
            },
            'sentinel': {
                'status': sentinel_status,
                'moon': sentinel_moon
            } if sentinel_status else None,
            'paths': [{
                'name': p['name'],
                'icon': p['icon'],
                'confidence': round(p['confidence'], 2),
                'viable': p['viable'],
                'description': p['description'],
                'blockers': p['blockers'],
                'action': p['action']
            } for p in paths[:depth + 2]],  # Show depth+2 paths
            'recommendation': {
                'path': recommendation,
                'action': recommendation_action
            }
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            print("\n" + "=" * 70)
            print("🔭 TRAJECTORY PROJECTION (Turtle Telescope)")
            print("=" * 70)

            print(f"\nCurrent Grounding: {overall_moon} {overall_status} ({overall_grounding:.2f})")

            if show_turtle:
                print("\n┌─ TURTLE STACK ─────────────────────────────────────────────────────┐")
                for layer in layers:
                    moon, status = layer['moon']
                    print(f"│  Layer {layers.index(layer)}: {layer['name']:20} {moon} {status:12} ({layer['score']:.2f}) │")
                print("└────────────────────────────────────────────────────────────────────┘")

            print(f"\nContext: {unknowns_count} unknowns | {findings_count} findings")
            if sentinel_status:
                print(f"Sentinel: {sentinel_moon} {sentinel_status.upper()}")

            print("\n┌─ VIABLE PATHS ─────────────────────────────────────────────────────┐")
            for i, path in enumerate(paths[:depth + 2]):
                viable_marker = "✓" if path['viable'] else "○"
                print(f"│                                                                    │")
                print(f"│  {path['icon']} {path['name']:15} (confidence: {path['confidence']:.2f}) [{viable_marker}]")
                print(f"│     {path['description'][:60]}")
                if verbose and path['blockers']:
                    for blocker in path['blockers'][:2]:
                        print(f"│     ⚠ {blocker[:55]}")
            print("│                                                                    │")
            print("└────────────────────────────────────────────────────────────────────┘")

            print(f"\n📍 RECOMMENDATION: {recommendation}")
            print(f"   {recommendation_action}")
            print("=" * 70)
            print()

    except Exception as e:
        handle_cli_error(e, "Trajectory Project", getattr(args, 'verbose', False))
