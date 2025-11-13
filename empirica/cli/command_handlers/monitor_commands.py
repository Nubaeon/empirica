"""
Monitoring Commands - CLI commands for usage monitoring and cost tracking

Provides real-time visibility into adapter usage, costs, and performance.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import os

from empirica.plugins.modality_switcher.modality_switcher import ModalitySwitcher
from empirica.plugins.modality_switcher.register_adapters import get_registry
from empirica.plugins.modality_switcher.config_loader import get_config
from ..cli_utils import handle_cli_error


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
            except:
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
            self.stats["adapters"][adapter] = {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0}
        
        self.stats["adapters"][adapter]["requests"] += 1
        self.stats["adapters"][adapter]["tokens"] += tokens
        self.stats["adapters"][adapter]["cost"] += cost
        
        if not success:
            self.stats["adapters"][adapter]["errors"] += 1
        
        self.stats["total_requests"] += 1
        self.stats["total_cost"] += cost
        
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
            self.stats["history"] = self.stats["history"][-1000:]
        
        self._save_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset all statistics."""
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
    Display real-time monitoring dashboard.
    
    Shows current usage statistics with optional live updates.
    """
    try:
        print("\n📊 Empirica Usage Monitor")
        print("=" * 70)
        
        monitor = UsageMonitor()
        stats = monitor.get_stats()
        
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
        output_file = args.output
        
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
