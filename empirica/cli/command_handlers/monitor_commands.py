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


def handle_check_drift_command(args):
    """
    Check for epistemic drift by comparing current state to historical baselines.

    Uses MirrorDriftMonitor to detect unexpected drops in epistemic vectors
    that indicate memory corruption, context loss, or other drift.
    """
    try:
        from empirica.core.drift.mirror_drift_monitor import MirrorDriftMonitor
        from empirica.core.canonical.empirica_git.checkpoint_manager import CheckpointManager

        session_id = args.session_id
        threshold = getattr(args, 'threshold', 0.2)
        lookback = getattr(args, 'lookback', 5)
        output_format = getattr(args, 'output', 'human')

        print("\n🔍 Epistemic Drift Detection")
        print("=" * 70)
        print(f"   Session ID:  {session_id}")
        print(f"   Threshold:   {threshold}")
        print(f"   Lookback:    {lookback} checkpoints")
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
