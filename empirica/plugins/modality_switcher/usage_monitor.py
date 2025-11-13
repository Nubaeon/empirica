"""
UsageMonitor - Phase 0

Tracks model call usage, costs, and enforces budget limits.
Prevents runaway premium costs with policy controls.

Usage:
    monitor = UsageMonitor()
    monitor.check_budget("openai")  # Raises if over budget
    monitor.record_call("openai", tokens=1000, cost=0.03)
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CallRecord:
    """Record of a single model call"""
    timestamp: float
    provider: str
    tokens_used: int
    cost_usd: float
    call_type: str  # "local", "non_premium", "premium"
    success: bool
    error_code: Optional[str] = None
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


@dataclass
class BudgetPolicy:
    """Budget policy for a provider"""
    max_calls_per_hour: int = 100
    max_calls_per_day: int = 1000
    max_cost_per_hour: float = 1.0  # USD
    max_cost_per_day: float = 10.0  # USD
    max_cost_per_month: float = 100.0  # USD
    stop_on_quota_exceeded: bool = True
    fallback_to_local: bool = True


class UsageMonitor:
    """
    Tracks usage and enforces budget policies.
    
    Persists state to JSON file for continuity across sessions.
    Conservative defaults prevent runaway costs.
    """
    
    DEFAULT_POLICIES = {
        'local': BudgetPolicy(
            max_calls_per_hour=1000,
            max_calls_per_day=10000,
            max_cost_per_hour=0.0,
            max_cost_per_day=0.0,
            max_cost_per_month=0.0,
            stop_on_quota_exceeded=False,
            fallback_to_local=False,
        ),
        'non_premium': BudgetPolicy(
            max_calls_per_hour=200,
            max_calls_per_day=2000,
            max_cost_per_hour=0.5,
            max_cost_per_day=5.0,
            max_cost_per_month=50.0,
            stop_on_quota_exceeded=True,
            fallback_to_local=True,
        ),
        'premium': BudgetPolicy(
            max_calls_per_hour=50,
            max_calls_per_day=200,
            max_cost_per_hour=1.0,
            max_cost_per_day=10.0,
            max_cost_per_month=100.0,
            stop_on_quota_exceeded=True,
            fallback_to_local=True,
        ),
    }
    
    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize UsageMonitor.
        
        Args:
            state_file: Path to JSON file for persistence
                       Defaults to ~/.empirica/usage_monitor.json
        """
        if state_file is None:
            state_file = Path.home() / ".empirica" / "usage_monitor.json"
        
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize state
        self.records: list[CallRecord] = []
        self.policies: Dict[str, BudgetPolicy] = {}
        self.stop_usage_flags: Dict[str, bool] = {}
        
        self._load_state()
    
    def _load_state(self):
        """Load state from JSON file"""
        if not self.state_file.exists():
            logger.info(f"📊 UsageMonitor: Creating new state file at {self.state_file}")
            self.policies = self.DEFAULT_POLICIES.copy()
            self._save_state()
            return
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            
            # Load records
            self.records = [CallRecord(**rec) for rec in data.get('records', [])]
            
            # Load policies
            policies_data = data.get('policies', {})
            for provider, policy_dict in policies_data.items():
                self.policies[provider] = BudgetPolicy(**policy_dict)
            
            # Load stop flags
            self.stop_usage_flags = data.get('stop_usage_flags', {})
            
            # Apply defaults for missing providers
            for provider, policy in self.DEFAULT_POLICIES.items():
                if provider not in self.policies:
                    self.policies[provider] = policy
            
            logger.info(f"📊 UsageMonitor: Loaded {len(self.records)} records from {self.state_file}")
            
        except Exception as e:
            logger.error(f"Failed to load usage state: {e}")
            self.policies = self.DEFAULT_POLICIES.copy()
    
    def _save_state(self):
        """Save state to JSON file"""
        try:
            data = {
                'records': [asdict(rec) for rec in self.records],
                'policies': {
                    provider: asdict(policy)
                    for provider, policy in self.policies.items()
                },
                'stop_usage_flags': self.stop_usage_flags,
                'last_saved': datetime.now().isoformat(),
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save usage state: {e}")
    
    def record_call(
        self,
        provider: str,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        call_type: str = "non_premium",
        success: bool = True,
        error_code: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ):
        """
        Record a model call.
        
        Args:
            provider: Provider identifier (e.g., "openai", "anthropic")
            tokens_used: Number of tokens consumed
            cost_usd: Estimated cost in USD
            call_type: "local", "non_premium", or "premium"
            success: Whether call succeeded
            error_code: Error code if failed (e.g., "quota_exceeded")
            meta: Additional metadata
        """
        record = CallRecord(
            timestamp=time.time(),
            provider=provider,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            call_type=call_type,
            success=success,
            error_code=error_code,
            meta=meta or {}
        )
        
        self.records.append(record)
        
        # Handle quota exceeded
        if error_code == "quota_exceeded":
            policy = self.policies.get(call_type, self.DEFAULT_POLICIES.get(call_type))
            if policy and policy.stop_on_quota_exceeded:
                self.stop_usage_flags[provider] = True
                logger.warning(f"⛔ Quota exceeded for {provider}, stopping usage")
        
        self._save_state()
        logger.debug(f"📊 Recorded call: {provider} ({call_type}) - {tokens_used} tokens, ${cost_usd:.4f}")
    
    def check_budget(self, provider: str, call_type: str = "non_premium") -> bool:
        """
        Check if a call would exceed budget limits.
        
        Args:
            provider: Provider identifier
            call_type: "local", "non_premium", or "premium"
            
        Returns:
            bool: True if within budget, False otherwise
            
        Raises:
            BudgetExceededError: If budget exceeded and policy is strict
        """
        # Check stop flag
        if self.stop_usage_flags.get(provider, False):
            logger.warning(f"⛔ Usage stopped for {provider} (quota exceeded)")
            return False
        
        policy = self.policies.get(call_type, self.DEFAULT_POLICIES.get(call_type))
        if policy is None:
            logger.warning(f"No policy for {call_type}, allowing call")
            return True
        
        now = time.time()
        
        # Filter recent records for this provider and call type
        hour_ago = now - 3600
        day_ago = now - 86400
        month_ago = now - (30 * 86400)
        
        provider_records = [
            r for r in self.records
            if r.provider == provider and r.call_type == call_type and r.success
        ]
        
        hour_records = [r for r in provider_records if r.timestamp >= hour_ago]
        day_records = [r for r in provider_records if r.timestamp >= day_ago]
        month_records = [r for r in provider_records if r.timestamp >= month_ago]
        
        # Check call count limits
        if len(hour_records) >= policy.max_calls_per_hour:
            logger.warning(f"⚠️  {provider} hour limit reached: {len(hour_records)}/{policy.max_calls_per_hour}")
            return False
        
        if len(day_records) >= policy.max_calls_per_day:
            logger.warning(f"⚠️  {provider} day limit reached: {len(day_records)}/{policy.max_calls_per_day}")
            return False
        
        # Check cost limits (skip if limit is 0.0, which means unlimited/free)
        hour_cost = sum(r.cost_usd for r in hour_records)
        day_cost = sum(r.cost_usd for r in day_records)
        month_cost = sum(r.cost_usd for r in month_records)
        
        if policy.max_cost_per_hour > 0.0 and hour_cost >= policy.max_cost_per_hour:
            logger.warning(f"⚠️  {provider} hour cost limit: ${hour_cost:.2f}/${policy.max_cost_per_hour:.2f}")
            return False
        
        if policy.max_cost_per_day > 0.0 and day_cost >= policy.max_cost_per_day:
            logger.warning(f"⚠️  {provider} day cost limit: ${day_cost:.2f}/${policy.max_cost_per_day:.2f}")
            return False
        
        if policy.max_cost_per_month > 0.0 and month_cost >= policy.max_cost_per_month:
            logger.warning(f"⚠️  {provider} month cost limit: ${month_cost:.2f}/${policy.max_cost_per_month:.2f}")
            return False
        
        return True
    
    def get_usage_summary(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage summary statistics.
        
        Args:
            provider: Optional provider to filter by
            
        Returns:
            Dict with usage statistics
        """
        records = self.records
        if provider:
            records = [r for r in records if r.provider == provider]
        
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400
        month_ago = now - (30 * 86400)
        
        hour_records = [r for r in records if r.timestamp >= hour_ago and r.success]
        day_records = [r for r in records if r.timestamp >= day_ago and r.success]
        month_records = [r for r in records if r.timestamp >= month_ago and r.success]
        
        return {
            'total_calls': len(records),
            'successful_calls': len([r for r in records if r.success]),
            'failed_calls': len([r for r in records if not r.success]),
            'hour': {
                'calls': len(hour_records),
                'tokens': sum(r.tokens_used for r in hour_records),
                'cost_usd': sum(r.cost_usd for r in hour_records),
            },
            'day': {
                'calls': len(day_records),
                'tokens': sum(r.tokens_used for r in day_records),
                'cost_usd': sum(r.cost_usd for r in day_records),
            },
            'month': {
                'calls': len(month_records),
                'tokens': sum(r.tokens_used for r in month_records),
                'cost_usd': sum(r.cost_usd for r in month_records),
            },
            'stop_flags': self.stop_usage_flags,
        }
    
    def reset_stop_flag(self, provider: str):
        """
        Reset stop usage flag for a provider.
        
        Args:
            provider: Provider identifier
        """
        if provider in self.stop_usage_flags:
            del self.stop_usage_flags[provider]
            self._save_state()
            logger.info(f"✅ Reset stop flag for {provider}")
    
    def set_policy(self, call_type: str, policy: BudgetPolicy):
        """
        Update budget policy for a call type.
        
        Args:
            call_type: "local", "non_premium", or "premium"
            policy: New budget policy
        """
        self.policies[call_type] = policy
        self._save_state()
        logger.info(f"✅ Updated policy for {call_type}")
    
    def cleanup_old_records(self, days: int = 30):
        """
        Remove records older than specified days.
        
        Args:
            days: Number of days to keep
        """
        cutoff = time.time() - (days * 86400)
        old_count = len(self.records)
        self.records = [r for r in self.records if r.timestamp >= cutoff]
        removed = old_count - len(self.records)
        
        if removed > 0:
            self._save_state()
            logger.info(f"🗑️  Cleaned up {removed} old records (>{days} days)")
