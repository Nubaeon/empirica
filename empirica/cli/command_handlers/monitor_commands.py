"""
Monitoring Commands - CLI commands for usage monitoring and cost tracking

Provides real-time visibility into adapter usage, costs, and performance.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import os

from empirica.plugins.modality_switcher.modality_switcher import ModalitySwitcher
from empirica.plugins.modality_switcher.register_adapters import get_registry
from empirica.plugins.modality_switcher.config_loader import get_config
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

    Shows current usage statistics with optional live updates.
    """
    # Route based on flags
    if getattr(args, 'export', None):
        return handle_monitor_export_command(args)
    elif getattr(args, 'reset', False):
        return handle_monitor_reset_command(args)
    elif getattr(args, 'cost', False):
        return handle_monitor_cost_command(args)

    # Default: show dashboard
    try:
        logger.info("Displaying monitoring dashboard")
        print("\n📊 Empirica Usage Monitor")
        print("=" * 70)

        monitor = UsageMonitor()
        stats = monitor.get_stats()
        
        logger.debug(f"Loaded stats: {stats.get('total_requests', 0)} total requests")
        
        # Get config for cost estimates
        config = get_config()
        adapter_costs = config.get_adapter_costs()
        
        # Display session info
        session_start = stats.get("session_start", "Unknown")
        print(f"\n⏰ Session Start: {session_start}")
        print(f"📝 Stats File: {monitor.stats_file}")
        
        # Display total stats
        print("\n" + "=" * 70)
        print("📈 Overall Statistics")
        print("=" * 70)
        print(f"   Total Requests:  {stats.get('total_requests', 0):,}")
        print(f"   Total Cost:      ${stats.get('total_cost', 0.0):.4f}")
        print(f"   Fallbacks:       {stats.get('fallbacks', 0)}")
        
        # Display per-adapter stats
        print("\n" + "=" * 70)
        print("🤖 Adapter Statistics")
        print("=" * 70)
        
        adapters_stats = stats.get("adapters", {})
        
        for adapter_name in ["minimax", "qwen", "local"]:
            adapter_data = adapters_stats.get(adapter_name, {})
            requests = adapter_data.get("requests", 0)
            tokens = adapter_data.get("tokens", 0)
            cost = adapter_data.get("cost", 0.0)
            errors = adapter_data.get("errors", 0)
            
            if requests > 0:
                error_rate = (errors / requests) * 100
                print(f"\n🔹 {adapter_name.upper()}")
                print(f"   Requests:   {requests:,}")
                print(f"   Tokens:     {tokens:,}")
                print(f"   Cost:       ${cost:.4f}")
                print(f"   Errors:     {errors} ({error_rate:.1f}%)")
                
                if tokens > 0:
                    avg_tokens = tokens / requests
                    print(f"   Avg Tokens: {avg_tokens:.0f}/request")
            else:
                print(f"\n🔹 {adapter_name.upper()}")
                print(f"   No usage recorded")
        
        # Display recent activity
        if getattr(args, 'history', False):
            history = stats.get("history", [])
            recent = history[-10:] if len(history) > 10 else history
            
            if recent:
                print("\n" + "=" * 70)
                print("📜 Recent Activity (last 10 requests)")
                print("=" * 70)
                
                for i, record in enumerate(reversed(recent), 1):
                    timestamp = record.get("timestamp", "?")
                    adapter = record.get("adapter", "?")
                    success = "✅" if record.get("success") else "❌"
                    cost = record.get("cost", 0.0)
                    latency = record.get("latency", 0.0)
                    
                    print(f"   {i}. {timestamp} | {adapter:8s} {success} | ${cost:.4f} | {latency:.1f}s")
        
        # Health check
        if getattr(args, 'health', False):
            print("\n" + "=" * 70)
            print("💓 Adapter Health Check")
            print("=" * 70)
            
            registry = get_registry()
            health_results = registry.health_check_all()
            
            for adapter, healthy in health_results.items():
                status = "✅ Healthy" if healthy else "❌ Unhealthy"
                print(f"   {adapter:10s}: {status}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        handle_cli_error(e, "Monitor", getattr(args, 'verbose', False))


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
    from datetime import datetime
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


def handle_post_summary_drift_check(session_id: str, output_format: str):
    """
    Post-summary trigger: Compare current state to pre-summary snapshot.

    Loads pre-summary ref-doc + current bootstrap as anchor.
    Presents evidence for AI to reassess, then facilitates comparison.

    This detects metacognitive drift from memory compacting.
    """
    from empirica.data.session_database import SessionDatabase
    from pathlib import Path
    import json

    print("\n🔄 Post-Summary Drift Check")
    print("=" * 70)
    print(f"   Session ID: {session_id}")
    print("=" * 70)

    db = SessionDatabase()

    # Find most recent pre-summary snapshot ref-doc
    ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"

    if not ref_docs_dir.exists():
        print("\n⚠️  No ref-docs directory found")
        print("   Run with --trigger pre_summary before memory compacting")
        return

    # Find pre_summary files for this session
    snapshot_files = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)

    if not snapshot_files:
        print("\n⚠️  No pre-summary snapshot found")
        print("   Run with --trigger pre_summary before memory compacting")
        return

    # Load most recent snapshot
    snapshot_path = snapshot_files[0]

    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)

    # Verify it's for this session
    if snapshot.get('session_id') != session_id:
        print(f"\n⚠️  Latest snapshot is for different session: {snapshot.get('session_id')}")
        print(f"   Looking for snapshot for: {session_id}")
        return

    # Load current bootstrap (ground truth)
    try:
        session_data = db.get_session(session_id)
        project_id = session_data.get('project_id') if session_data else None

        bootstrap = db.generate_project_bootstrap(
            session_id=session_id,
            project_id=project_id,
            include_file_tree=True  # Full context for reassessment
        ) if project_id else {}
    except Exception as e:
        logger.warning(f"Could not load bootstrap: {e}")
        bootstrap = {}

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

    # Present evidence for reassessment
    print("\n📚 BOOTSTRAP EVIDENCE (Ground Truth):")
    print("=" * 70)

    findings = bootstrap.get('findings', [])
    unknowns = bootstrap.get('unknowns', [])
    goals = bootstrap.get('goals', [])
    dead_ends = bootstrap.get('dead_ends', [])

    print(f"\n   Findings: {len(findings)}")
    if findings:
        print(f"      Most recent: \"{findings[0].get('finding', 'N/A')[:60]}...\"")

    print(f"\n   Active Unknowns: {len(unknowns)}")
    if unknowns:
        for i, unk in enumerate(unknowns[:3], 1):
            print(f"      {i}. {unk.get('unknown', 'N/A')[:60]}")

    print(f"\n   Goals: {len(goals)}")
    incomplete = [g for g in goals if g.get('status') != 'completed']
    if incomplete:
        print(f"      Incomplete: {len(incomplete)}")

    print(f"\n   Dead Ends: {len(dead_ends)}")

    # Show pre-summary state
    print("\n📊 YOUR PRE-SUMMARY STATE:")
    print("=" * 70)

    pre_vectors = snapshot.get('checkpoint', {}).get('vectors', {})
    pre_timestamp = snapshot.get('timestamp', 'Unknown')

    print(f"\n   Captured: {pre_timestamp}")
    print(f"   KNOW:        {pre_vectors.get('know', 'N/A')}")
    print(f"   UNCERTAINTY: {pre_vectors.get('uncertainty', 'N/A')}")
    print(f"   CONTEXT:     {pre_vectors.get('context', 'N/A')}")
    print(f"   CLARITY:     {pre_vectors.get('clarity', 'N/A')}")

    # Prompt for reassessment
    print("\n❓ REASSESSMENT PROMPT:")
    print("=" * 70)
    print(f"""
   Based on the bootstrap evidence above:
   - {len(findings)} findings show what was learned
   - {len(unknowns)} unknowns show what's still unclear
   - {len(incomplete)} incomplete goals show ongoing work

   Compare to your pre-summary state from {pre_timestamp}.

   Run CHECK or PREFLIGHT now to create fresh assessment.
   System will compare to detect drift.
    """)

    print("=" * 70)

    # Output for JSON mode
    if output_format == 'json':
        return json.dumps({
            "ok": True,
            "pre_summary": {
                "timestamp": pre_timestamp,
                "vectors": pre_vectors,
                "snapshot_path": str(snapshot_path)
            },
            "bootstrap": {
                "findings_count": len(findings),
                "unknowns_count": len(unknowns),
                "goals_count": len(goals),
                "incomplete_goals": len(incomplete),
                "dead_ends_count": len(dead_ends)
            },
            "action_required": "Run CHECK or PREFLIGHT to create fresh assessment for comparison"
        }, indent=2)


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
        from datetime import datetime
        from pathlib import Path

        session_id = args.session_id
        trigger = getattr(args, 'trigger', 'manual')
        threshold = getattr(args, 'threshold', 0.2)
        lookback = getattr(args, 'lookback', 5)
        cycle = getattr(args, 'cycle', None)
        round_num = getattr(args, 'round', None)
        scope_depth = getattr(args, 'scope_depth', None)
        output_format = getattr(args, 'output', 'human')

        # Handle pre-summary trigger: Save checkpoint as ref-doc
        if trigger == 'pre_summary':
            return handle_pre_summary_snapshot(session_id, output_format, cycle, round_num, scope_depth)

        # Handle post-summary trigger: Compare with pre-summary ref-doc
        if trigger == 'post_summary':
            return handle_post_summary_drift_check(session_id, output_format)

        # Manual mode: Standard drift detection
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

        # Load current epistemic state from latest checkpoint
        manager = CheckpointManager()
        checkpoints = manager.load_recent_checkpoints(session_id=session_id, count=1)

        if not checkpoints:
            print("\n⚠️  No checkpoints found for session")
            print("   Run PREFLIGHT or CHECK to create a checkpoint first")
            return

        current_checkpoint = checkpoints[0]

        # Create mock assessment from checkpoint vectors
        class MockAssessment:
            def __init__(self, vectors):
                for name, score in vectors.items():
                    setattr(self, name, type('VectorState', (), {'score': score})())

        current_assessment = MockAssessment(current_checkpoint.get('vectors', {}))

        # Run drift detection
        monitor = MirrorDriftMonitor(
            drift_threshold=threshold,
            lookback_window=lookback,
            enable_logging=True
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
