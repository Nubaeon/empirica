#!/usr/bin/env python3
"""
Cross-Benchmark Correlation Analysis

Correlates traditional performance metrics (MMLU, HumanEval, etc.) with
epistemic reasoning capabilities (ERB) to reveal insights about model
capabilities beyond raw performance.

Key Insights:
- High MMLU != High ERB (knowledge recall != epistemic humility)
- HumanEval measures coding ability, not self-awareness
- ERB reveals trustworthiness independent of performance

Version: 1.0.0
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class TraditionalBenchmarkScore:
    """Traditional benchmark scores for a model"""
    model_name: str
    mmlu: Optional[float] = None  # Massive Multitask Language Understanding (0-100)
    humaneval: Optional[float] = None  # HumanEval code completion (0-100)
    gsm8k: Optional[float] = None  # Grade School Math 8K (0-100)
    hellaswag: Optional[float] = None  # HellaSwag commonsense (0-100)
    truthfulqa: Optional[float] = None  # TruthfulQA factuality (0-100)
    mt_bench: Optional[float] = None  # MT-Bench instruction following (1-10)
    arena_elo: Optional[int] = None  # Chatbot Arena ELO rating


@dataclass
class EpistemicBenchmarkScore:
    """Epistemic Reasoning Benchmark (ERB) scores"""
    model_name: str
    erb_overall: float  # Overall ERB score (0-100)
    temporal_awareness: float  # Cutoff date recognition (0-100)
    vagueness_detection: float  # Detecting unclear requests (0-100)
    knowledge_boundaries: float  # Admitting "I don't know" (0-100)
    overconfidence: float  # Precision-critical domain awareness (0-100)
    opinion_vs_fact: float  # Distinguishing subjective/objective (0-100)
    epistemic_grade: str  # EXCELLENT, GOOD, ADEQUATE, POOR


@dataclass
class ComprehensiveBenchmarkResult:
    """Combined traditional + epistemic benchmark results"""
    model_name: str
    model_size: str
    traditional: TraditionalBenchmarkScore
    epistemic: EpistemicBenchmarkScore

    # Derived metrics
    performance_vs_humility_gap: Optional[float] = None  # MMLU - ERB
    trustworthiness_score: Optional[float] = None  # Weighted combination
    deployment_readiness: Optional[str] = None  # HIGH, MEDIUM, LOW


class CrossBenchmarkAnalyzer:
    """
    Analyzes correlation between traditional performance and epistemic reasoning

    Key Questions:
    - Do high-performing models have better epistemic self-awareness?
    - Can a model be accurate but overconfident?
    - What's the optimal balance for deployment?
    """

    def __init__(self):
        self.results: List[ComprehensiveBenchmarkResult] = []

    def add_result(self, result: ComprehensiveBenchmarkResult):
        """Add a comprehensive benchmark result"""
        # Calculate derived metrics
        if result.traditional.mmlu and result.epistemic.erb_overall:
            result.performance_vs_humility_gap = result.traditional.mmlu - result.epistemic.erb_overall

        # Calculate trustworthiness score (balanced: 50% performance, 50% humility)
        if result.traditional.mmlu and result.epistemic.erb_overall:
            result.trustworthiness_score = (
                result.traditional.mmlu * 0.5 +
                result.epistemic.erb_overall * 0.5
            )

        # Determine deployment readiness
        result.deployment_readiness = self._assess_deployment_readiness(result)

        self.results.append(result)

    def _assess_deployment_readiness(self, result: ComprehensiveBenchmarkResult) -> str:
        """Assess if model is ready for production deployment"""
        mmlu = result.traditional.mmlu or 0
        erb = result.epistemic.erb_overall

        # High performance + high humility = HIGH
        if mmlu >= 70 and erb >= 70:
            return "HIGH"

        # High performance + low humility = MEDIUM (risky - overconfident)
        elif mmlu >= 70 and erb < 50:
            return "MEDIUM - ⚠️ OVERCONFIDENCE RISK"

        # Low performance + high humility = MEDIUM (honest but limited)
        elif mmlu < 50 and erb >= 70:
            return "MEDIUM - Limited capabilities but honest"

        # Low both = LOW
        else:
            return "LOW"

    def analyze_correlation(self) -> Dict[str, Any]:
        """Analyze correlation between traditional and epistemic benchmarks"""
        if len(self.results) < 2:
            return {"error": "Need at least 2 models for correlation analysis"}

        # Extract data
        mmlu_scores = [r.traditional.mmlu for r in self.results if r.traditional.mmlu]
        erb_scores = [r.epistemic.erb_overall for r in self.results]

        if len(mmlu_scores) != len(erb_scores):
            return {"error": "Mismatched data - not all models have MMLU scores"}

        # Calculate correlation
        import numpy as np
        correlation = np.corrcoef(mmlu_scores, erb_scores)[0, 1]

        # Interpretation
        if abs(correlation) < 0.3:
            interpretation = "WEAK - Performance and epistemic humility are independent"
        elif abs(correlation) < 0.7:
            interpretation = "MODERATE - Some correlation exists"
        else:
            interpretation = "STRONG - Performance and humility correlate"

        return {
            "correlation_coefficient": correlation,
            "interpretation": interpretation,
            "mmlu_mean": np.mean(mmlu_scores),
            "erb_mean": np.mean(erb_scores),
            "mmlu_std": np.std(mmlu_scores),
            "erb_std": np.std(erb_scores),
            "num_models": len(self.results)
        }

    def find_overconfident_models(self, threshold: float = 20.0) -> List[ComprehensiveBenchmarkResult]:
        """Find models with high performance but low epistemic humility"""
        overconfident = []

        for result in self.results:
            if result.performance_vs_humility_gap and result.performance_vs_humility_gap > threshold:
                overconfident.append(result)

        return sorted(overconfident, key=lambda r: r.performance_vs_humility_gap, reverse=True)

    def find_trustworthy_models(self, min_trustworthiness: float = 70.0) -> List[ComprehensiveBenchmarkResult]:
        """Find models with balanced performance and humility"""
        trustworthy = []

        for result in self.results:
            if result.trustworthiness_score and result.trustworthiness_score >= min_trustworthiness:
                trustworthy.append(result)

        return sorted(trustworthy, key=lambda r: r.trustworthiness_score, reverse=True)

    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        if not self.results:
            return "No results to analyze"

        report = []
        report.append("=" * 80)
        report.append("CROSS-BENCHMARK CORRELATION ANALYSIS")
        report.append("Traditional Performance vs Epistemic Reasoning")
        report.append("=" * 80)
        report.append()

        # Overall statistics
        correlation_analysis = self.analyze_correlation()
        if "error" not in correlation_analysis:
            report.append("📊 CORRELATION ANALYSIS")
            report.append("-" * 80)
            report.append(f"Correlation (MMLU vs ERB): {correlation_analysis['correlation_coefficient']:.3f}")
            report.append(f"Interpretation: {correlation_analysis['interpretation']}")
            report.append(f"Average MMLU: {correlation_analysis['mmlu_mean']:.1f}%")
            report.append(f"Average ERB: {correlation_analysis['erb_mean']:.1f}%")
            report.append()

        # Model ranking by trustworthiness
        report.append("🏆 MODEL RANKING (Trustworthiness Score)")
        report.append("-" * 80)
        report.append(f"{'Rank':<6} {'Model':<30} {'MMLU':<8} {'ERB':<8} {'Trust':<8} {'Deployment'}")
        report.append("-" * 80)

        sorted_results = sorted(
            [r for r in self.results if r.trustworthiness_score],
            key=lambda r: r.trustworthiness_score,
            reverse=True
        )

        for i, result in enumerate(sorted_results, 1):
            mmlu = result.traditional.mmlu or 0
            erb = result.epistemic.erb_overall
            trust = result.trustworthiness_score or 0

            report.append(
                f"{i:<6} {result.model_name:<30} {mmlu:<7.1f}% {erb:<7.1f}% {trust:<7.1f}% {result.deployment_readiness}"
            )

        report.append()

        # Overconfident models
        overconfident = self.find_overconfident_models()
        if overconfident:
            report.append("⚠️  OVERCONFIDENCE ALERT")
            report.append("-" * 80)
            report.append("Models with high performance but low epistemic humility:")
            report.append()

            for result in overconfident:
                mmlu = result.traditional.mmlu or 0
                erb = result.epistemic.erb_overall
                gap = result.performance_vs_humility_gap

                report.append(f"   {result.model_name}")
                report.append(f"      MMLU: {mmlu:.1f}%, ERB: {erb:.1f}%, Gap: +{gap:.1f}%")
                report.append(f"      Risk: May confabulate confidently in areas of ignorance")
                report.append()

        # Category breakdown
        report.append("📊 EPISTEMIC CATEGORY ANALYSIS")
        report.append("-" * 80)
        report.append(f"{'Model':<30} {'Temporal':<12} {'Vagueness':<12} {'Boundaries':<12} {'Grade'}")
        report.append("-" * 80)

        for result in sorted_results:
            e = result.epistemic
            report.append(
                f"{result.model_name:<30} {e.temporal_awareness:<11.1f}% {e.vagueness_detection:<11.1f}% "
                f"{e.knowledge_boundaries:<11.1f}% {e.epistemic_grade}"
            )

        report.append()

        # Key insights
        report.append("💡 KEY INSIGHTS")
        report.append("-" * 80)

        # Insight 1: Correlation
        if "error" not in correlation_analysis:
            corr = correlation_analysis["correlation_coefficient"]
            if abs(corr) < 0.3:
                report.append("✓ Performance and epistemic humility are INDEPENDENT")
                report.append("  High MMLU does not guarantee good epistemic self-awareness")
            else:
                report.append(f"✓ Moderate correlation ({corr:.2f}) between performance and humility")

        # Insight 2: Best practices
        trustworthy = self.find_trustworthy_models(min_trustworthiness=70)
        if trustworthy:
            report.append(f"\n✓ {len(trustworthy)} models demonstrate balanced performance + humility")
            report.append(f"  Best for production: {trustworthy[0].model_name}")

        # Insight 3: Risky models
        if overconfident:
            report.append(f"\n⚠️  {len(overconfident)} models show overconfidence risk")
            report.append("  May hallucinate confidently - use with caution")

        report.append()
        report.append("=" * 80)

        return "\n".join(report)

    def plot_correlation(self, output_path: str = "correlation_plot.png"):
        """Generate scatter plot of MMLU vs ERB"""
        try:
            import numpy as np
            import matplotlib.pyplot as plt
        except ImportError:
            print("Install matplotlib and numpy for plotting: pip install matplotlib numpy")
            return

        mmlu_scores = []
        erb_scores = []
        model_names = []

        for result in self.results:
            if result.traditional.mmlu:
                mmlu_scores.append(result.traditional.mmlu)
                erb_scores.append(result.epistemic.erb_overall)
                model_names.append(result.model_name)

        if len(mmlu_scores) < 2:
            print("Need at least 2 models with MMLU scores for plotting")
            return

        # Create plot
        plt.figure(figsize=(12, 8))

        # Scatter plot
        plt.scatter(mmlu_scores, erb_scores, s=200, alpha=0.6)

        # Labels
        for i, name in enumerate(model_names):
            plt.annotate(name, (mmlu_scores[i], erb_scores[i]), fontsize=9, alpha=0.7)

        # Diagonal line (perfect balance)
        plt.plot([0, 100], [0, 100], 'r--', alpha=0.3, label='Perfect Balance')

        # Quadrants
        plt.axhline(y=50, color='gray', linestyle=':', alpha=0.3)
        plt.axvline(x=50, color='gray', linestyle=':', alpha=0.3)

        # Labels and title
        plt.xlabel('Traditional Performance (MMLU %)', fontsize=12)
        plt.ylabel('Epistemic Reasoning (ERB %)', fontsize=12)
        plt.title('Traditional Performance vs Epistemic Self-Awareness', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.2)

        # Quadrant labels
        plt.text(75, 25, 'OVERCONFIDENT\n(High Performance,\nLow Humility)', ha='center', fontsize=10, alpha=0.5)
        plt.text(25, 75, 'HUMBLE\n(Low Performance,\nHigh Humility)', ha='center', fontsize=10, alpha=0.5)
        plt.text(75, 75, 'TRUSTWORTHY\n(High Both)', ha='center', fontsize=10, alpha=0.5)
        plt.text(25, 25, 'STRUGGLING\n(Low Both)', ha='center', fontsize=10, alpha=0.5)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        print(f"Plot saved to: {output_path}")

    def save_results(self, output_path: str = "cross_benchmark_results.json"):
        """Save results to JSON"""
        data = {
            "results": [asdict(r) for r in self.results],
            "correlation_analysis": self.analyze_correlation(),
            "overconfident_models": [asdict(r) for r in self.find_overconfident_models()],
            "trustworthy_models": [asdict(r) for r in self.find_trustworthy_models()]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Results saved to: {output_path}")


# Example known model scores (from public leaderboards)
KNOWN_TRADITIONAL_SCORES = {
    "gpt-4": TraditionalBenchmarkScore(model_name="gpt-4", mmlu=86.4, humaneval=67.0, arena_elo=1225),
    "claude-3.5-sonnet": TraditionalBenchmarkScore(model_name="claude-3.5-sonnet", mmlu=88.7, humaneval=92.0, arena_elo=1266),
    "gemini-1.5-pro": TraditionalBenchmarkScore(model_name="gemini-1.5-pro", mmlu=85.9, humaneval=84.1, arena_elo=1240),
    "llama-3.1-70b": TraditionalBenchmarkScore(model_name="llama-3.1-70b", mmlu=83.6, humaneval=69.5, arena_elo=1180),
    "qwen2.5-72b": TraditionalBenchmarkScore(model_name="qwen2.5-72b", mmlu=85.2, humaneval=87.5, arena_elo=1190),
    "phi-3-mini": TraditionalBenchmarkScore(model_name="phi-3-mini", mmlu=68.1, humaneval=58.0, arena_elo=1050),
}


def main():
    """Example usage"""
    analyzer = CrossBenchmarkAnalyzer()

    # Example: Add some results
    # (In real usage, these would come from actual ERB benchmark runs)

    # Example 1: High performance, moderate humility (Claude)
    analyzer.add_result(ComprehensiveBenchmarkResult(
        model_name="claude-3.5-sonnet",
        model_size="unknown",
        traditional=KNOWN_TRADITIONAL_SCORES["claude-3.5-sonnet"],
        epistemic=EpistemicBenchmarkScore(
            model_name="claude-3.5-sonnet",
            erb_overall=85.0,
            temporal_awareness=90.0,
            vagueness_detection=95.0,
            knowledge_boundaries=80.0,
            overconfidence=90.0,
            opinion_vs_fact=95.0,
            epistemic_grade="EXCELLENT"
        )
    ))

    # Example 2: High performance, low humility (simulated overconfident model)
    analyzer.add_result(ComprehensiveBenchmarkResult(
        model_name="gpt-4",
        model_size="unknown",
        traditional=KNOWN_TRADITIONAL_SCORES["gpt-4"],
        epistemic=EpistemicBenchmarkScore(
            model_name="gpt-4",
            erb_overall=60.0,
            temporal_awareness=70.0,
            vagueness_detection=50.0,
            knowledge_boundaries=55.0,
            overconfidence=70.0,
            opinion_vs_fact=65.0,
            epistemic_grade="ADEQUATE"
        )
    ))

    # Example 3: Moderate performance, good humility (phi3 from real test)
    analyzer.add_result(ComprehensiveBenchmarkResult(
        model_name="phi-3-mini",
        model_size="3.8B",
        traditional=KNOWN_TRADITIONAL_SCORES["phi-3-mini"],
        epistemic=EpistemicBenchmarkScore(
            model_name="phi-3-mini",
            erb_overall=57.1,
            temporal_awareness=67.0,
            vagueness_detection=0.0,
            knowledge_boundaries=33.0,
            overconfidence=100.0,
            opinion_vs_fact=100.0,
            epistemic_grade="ADEQUATE"
        )
    ))

    # Generate report
    print(analyzer.generate_report())

    # Save results
    analyzer.save_results()

    # Plot correlation
    analyzer.plot_correlation()


if __name__ == "__main__":
    main()
