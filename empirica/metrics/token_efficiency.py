"""
Token Efficiency Metrics

Measures token usage efficiency for Empirica workflows, comparing git-based
vs prompt-based context loading strategies.

Key Metrics:
- Tokens per phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
- Total session token usage
- Percentage reduction (baseline vs optimized)
- Cost savings estimation

Purpose: Validate the 80-90% token reduction hypothesis for git integration.

Usage:
    metrics = TokenEfficiencyMetrics(session_id="abc-123")

    # Measure context load
    metrics.measure_context_load(
        phase="PREFLIGHT",
        method="git",
        content=checkpoint_json
    )

    # Compare with baseline
    report = metrics.compare_efficiency(baseline_session_id="session-5")

    # Export report
    metrics.export_report(format="markdown", output_path="report.md")
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone  # type: ignore[reportAttributeAccessIssue]
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TokenMeasurement:
    """Single token usage measurement"""
    phase: str
    method: str  # "git" or "prompt"
    tokens: int
    timestamp: str
    content_type: str  # "checkpoint", "diff", "full_history", etc.
    metadata: dict[str, Any]


class TokenEfficiencyMetrics:
    """
    Track and analyze token efficiency for Empirica workflows.

    Compares git-based checkpoint loading (target) vs prompt-based full history
    loading (baseline) to validate token reduction hypothesis.
    """

    def __init__(
        self,
        session_id: str,
        storage_dir: str = ".empirica/metrics"
    ):
        """
        Initialize token efficiency tracker.

        Args:
            session_id: Session identifier
            storage_dir: Directory for storing metrics
        """
        self.session_id = session_id
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.measurements: list[TokenMeasurement] = []

        # Expected baseline token counts (from empirical data)
        self.baseline_tokens = {
            "PREFLIGHT": 6500,
            "CHECK": 3500,
            "ACT": 1500,
            "POSTFLIGHT": 5500
        }

        # Target token counts (compressed checkpoints)
        self.target_tokens = {
            "PREFLIGHT": 450,
            "CHECK": 400,
            "ACT": 500,
            "POSTFLIGHT": 850
        }

    def measure_context_load(
        self,
        phase: str,
        method: str,
        content: str,
        content_type: str = "checkpoint",
        metadata: dict[str, Any] | None = None
    ) -> TokenMeasurement:
        """
        Measure token usage for context loading operation.

        Args:
            phase: Workflow phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
            method: Loading method ("git" or "prompt")
            content: Actual content being loaded
            content_type: Type of content (checkpoint, diff, full_history, etc.)
            metadata: Additional metadata

        Returns:
            TokenMeasurement record
        """
        token_count = self._count_tokens(content)

        measurement = TokenMeasurement(
            phase=phase,
            method=method,
            tokens=token_count,
            timestamp=datetime.now(timezone.utc).isoformat(),
            content_type=content_type,
            metadata=metadata or {}
        )

        self.measurements.append(measurement)

        logger.info(
            f"Token measurement: {phase}/{method} = {token_count} tokens "
            f"({content_type})"
        )

        return measurement

    def _count_tokens(self, text: str) -> int:
        """
        Estimate token count from text.

        Uses simple approximation: len(text.split()) * 1.3

        Note: Phase 1.5 uses this approximation. Production will use tiktoken
        for accurate OpenAI token counting.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        word_count = len(text.split())
        return int(word_count * 1.3)

    def get_phase_total(self, phase: str, method: str | None = None) -> int:
        """
        Get total tokens for a specific phase.

        Args:
            phase: Phase to sum (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
            method: Filter by method (optional)

        Returns:
            Total token count for phase
        """
        filtered = [
            m for m in self.measurements
            if m.phase == phase and (method is None or m.method == method)
        ]

        return sum(m.tokens for m in filtered)

    def get_session_total(self, method: str | None = None) -> int:
        """
        Get total tokens for entire session.

        Args:
            method: Filter by method (optional)

        Returns:
            Total token count
        """
        filtered = [
            m for m in self.measurements
            if method is None or m.method == method
        ]

        return sum(m.tokens for m in filtered)

    def calculate_reduction(self, baseline_tokens: int, actual_tokens: int) -> dict[str, Any]:
        """
        Calculate token reduction metrics.

        Args:
            baseline_tokens: Baseline (prompt-based) token count
            actual_tokens: Actual (git-based) token count

        Returns:
            Reduction metrics dictionary
        """
        reduction_absolute = baseline_tokens - actual_tokens
        reduction_percentage = (reduction_absolute / baseline_tokens * 100) if baseline_tokens > 0 else 0

        # Cost estimation (using GPT-4 pricing: $0.01 per 1K tokens)
        cost_per_1k_tokens = 0.01
        baseline_cost = (baseline_tokens / 1000) * cost_per_1k_tokens
        actual_cost = (actual_tokens / 1000) * cost_per_1k_tokens
        cost_savings = baseline_cost - actual_cost

        return {
            "baseline_tokens": baseline_tokens,
            "actual_tokens": actual_tokens,
            "reduction_absolute": reduction_absolute,
            "reduction_percentage": round(reduction_percentage, 2),
            "baseline_cost_usd": round(baseline_cost, 4),
            "actual_cost_usd": round(actual_cost, 4),
            "cost_savings_usd": round(cost_savings, 4)
        }

    def compare_efficiency(self, baseline_session_id: str | None = None) -> dict[str, Any]:
        """
        Compare current session efficiency against baseline.

        Args:
            baseline_session_id: Session ID for baseline comparison (optional)
                                If not provided, uses theoretical baseline values

        Returns:
            Comprehensive efficiency report
        """
        report = {
            "session_id": self.session_id,
            "baseline_session_id": baseline_session_id or "theoretical",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phases": {},
            "total": {}
        }

        # Per-phase comparison
        for phase in ["PREFLIGHT", "CHECK", "ACT", "POSTFLIGHT"]:
            actual_tokens = self.get_phase_total(phase, method="git")
            baseline_tokens = self.baseline_tokens.get(phase, 0)

            if actual_tokens > 0 or baseline_tokens > 0:
                report["phases"][phase] = self.calculate_reduction(
                    baseline_tokens, actual_tokens
                )

        # Total session comparison
        actual_total = self.get_session_total(method="git")
        baseline_total = sum(self.baseline_tokens.values())

        report["total"] = self.calculate_reduction(baseline_total, actual_total)

        # Success criteria validation
        target_reduction_pct = 80  # 80% reduction target
        achieved_reduction_pct = report["total"]["reduction_percentage"]

        report["success_criteria"] = {
            "target_reduction_pct": target_reduction_pct,
            "achieved_reduction_pct": achieved_reduction_pct,
            "target_met": achieved_reduction_pct >= target_reduction_pct
        }

        return report

    def export_report(
        self,
        format: str = "json",
        output_path: str | None = None
    ) -> str:
        """
        Export efficiency report.

        Args:
            format: Export format ("json", "csv", "markdown")
            output_path: Output file path (optional, prints to stdout if None)

        Returns:
            Report content as string
        """
        report = self.compare_efficiency()

        if format == "json":
            content = json.dumps(report, indent=2)

        elif format == "markdown":
            content = self._format_markdown_report(report)

        elif format == "csv":
            content = self._format_csv_report(report)

        else:
            raise ValueError(f"Unsupported format: {format}")

        # Write to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w') as f:
                f.write(content)

            logger.info(f"Report exported to: {output_file}")

        return content

    def _format_markdown_report(self, report: dict[str, Any]) -> str:
        """Format report as Markdown."""
        lines = [
            "# Token Efficiency Report",
            "",
            f"**Session:** `{report['session_id']}`  ",
            f"**Baseline:** `{report['baseline_session_id']}`  ",
            f"**Generated:** {report['timestamp']}",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Baseline Tokens | {report['total']['baseline_tokens']:,} |",
            f"| Actual Tokens | {report['total']['actual_tokens']:,} |",
            f"| Reduction | {report['total']['reduction_absolute']:,} ({report['total']['reduction_percentage']:.1f}%) |",
            f"| Cost Savings | ${report['total']['cost_savings_usd']:.4f} |",
            "",
            f"**Target Met:** {'✅ YES' if report['success_criteria']['target_met'] else '❌ NO'} "
            f"({report['success_criteria']['achieved_reduction_pct']:.1f}% vs {report['success_criteria']['target_reduction_pct']}% target)",
            "",
            "## Per-Phase Breakdown",
            "",
            "| Phase | Baseline | Actual | Reduction | % |",
            "|-------|----------|--------|-----------|---|"
        ]

        for phase, metrics in report['phases'].items():
            lines.append(
                f"| {phase} | {metrics['baseline_tokens']:,} | "
                f"{metrics['actual_tokens']:,} | "
                f"{metrics['reduction_absolute']:,} | "
                f"{metrics['reduction_percentage']:.1f}% |"
            )

        lines.extend([
            "",
            "## Detailed Measurements",
            "",
            f"Total measurements recorded: {len(self.measurements)}",
            ""
        ])

        for i, measurement in enumerate(self.measurements, 1):
            lines.append(
                f"{i}. **{measurement.phase}** ({measurement.method}): "
                f"{measurement.tokens} tokens - {measurement.content_type}"
            )

        return "\n".join(lines)

    def _format_csv_report(self, report: dict[str, Any]) -> str:
        """Format report as CSV."""
        lines = [
            "phase,method,baseline_tokens,actual_tokens,reduction_absolute,reduction_percentage,cost_savings_usd"
        ]

        for phase, metrics in report['phases'].items():
            lines.append(
                f"{phase},git,{metrics['baseline_tokens']},{metrics['actual_tokens']},"
                f"{metrics['reduction_absolute']},{metrics['reduction_percentage']},"
                f"{metrics['cost_savings_usd']}"
            )

        # Add total row
        total = report['total']
        lines.append(
            f"TOTAL,git,{total['baseline_tokens']},{total['actual_tokens']},"
            f"{total['reduction_absolute']},{total['reduction_percentage']},"
            f"{total['cost_savings_usd']}"
        )

        return "\n".join(lines)

    def save_measurements(self):
        """Save measurements to disk for persistence."""
        filepath = self.storage_dir / f"metrics_{self.session_id}.json"

        data = {
            "session_id": self.session_id,
            "measurements": [asdict(m) for m in self.measurements],
            "saved_at": datetime.now(timezone.utc).isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics saved to: {filepath}")

    def load_measurements(self) -> bool:
        """
        Load measurements from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        filepath = self.storage_dir / f"metrics_{self.session_id}.json"

        if not filepath.exists():
            return False

        try:
            with open(filepath) as f:
                data = json.load(f)

            self.measurements = [
                TokenMeasurement(**m) for m in data['measurements']
            ]

            logger.info(f"Loaded {len(self.measurements)} measurements from {filepath}")
            return True

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load measurements: {e}")
            return False
