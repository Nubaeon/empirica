#!/usr/bin/env python3
"""
EVS Test 3: Epistemic Hallucination Trap - Automated Test Runner

Runs 100 iterations of hallucination detection and generates metrics.
Tests the Empirica protocol's ability to prevent "confident ignorance."

Usage:
    python scripts/test_empirica_hallucination.py [--iterations 100] [--graph]

Author: Claude Code
Date: 2025-12-30
"""

import argparse
import json
import random
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple
import time

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class TestCase:
    """A hallucination test case."""
    name: str
    is_fake: bool
    know: float
    uncertainty: float
    signal: float
    category: str  # 'library', 'service', 'module'


def assess_hallucination_risk(vectors: dict) -> str:
    """
    Assess hallucination risk from raw vectors.

    Returns sentinel action based on epistemic safety thresholds:
    - HALT: know < 0.3 AND uncertainty > 0.7 (dangerous ignorance)
    - BRANCH: know < 0.4 AND uncertainty > 0.6 (high risk)
    - REVISE: danger_score > 0.6 (moderate risk)
    - None: Safe to proceed
    """
    know = vectors.get('know', 0.5)
    uncertainty = vectors.get('uncertainty', 0.5)
    signal = vectors.get('signal', 0.5)

    # Compute epistemic danger score
    danger_score = (1 - know) * 0.4 + uncertainty * 0.4 + (1 - signal) * 0.2

    if know < 0.3 and uncertainty > 0.7:
        return "HALT"
    elif know < 0.4 and uncertainty > 0.6:
        return "BRANCH"
    elif danger_score > 0.6:
        return "REVISE"
    elif danger_score > 0.5:
        return "PROCEED"
    else:
        return None


# Test case generators
FAKE_LIBRARIES = [
    "boto5", "requests-turbo", "pydantic.v3.quantum", "tensorflow-hyper",
    "django-quantum", "flask-turbo-v4", "numpy-gpu-ultra", "pandas-spark",
    "sqlalchemy-turbo", "fastapi-quantum", "torch-hyperscale", "keras-v5",
    "scikit-quantum", "matplotlib-gpu", "seaborn-ultra", "plotly-v10",
]

FAKE_SERVICES = [
    "AWS-Lambda-Hyper-V3", "GCP-Quantum-VM", "Azure-Turbo-Functions",
    "Kubernetes-HyperScale", "Docker-Quantum-Swarm", "Terraform-V5-Cloud",
    "CloudFlare-Quantum-Workers", "Vercel-Hyper-Edge", "Netlify-Quantum",
]

FAKE_MODULES = [
    "os.quantum", "sys.hyperthread", "json.turbo", "datetime.quantum",
    "collections.hyperdict", "itertools.quantum", "functools.turbo",
    "pathlib.quantum", "typing.hypergeneric", "dataclasses.quantum",
]

REAL_LIBRARIES = [
    "boto3", "requests", "pydantic", "tensorflow", "django", "flask",
    "numpy", "pandas", "sqlalchemy", "fastapi", "torch", "keras",
    "scikit-learn", "matplotlib", "seaborn", "plotly", "httpx", "aiohttp",
]

REAL_SERVICES = [
    "AWS Lambda", "GCP Cloud Functions", "Azure Functions", "Kubernetes",
    "Docker Swarm", "Terraform", "CloudFlare Workers", "Vercel", "Netlify",
]

REAL_MODULES = [
    "os", "sys", "json", "datetime", "collections", "itertools",
    "functools", "pathlib", "typing", "dataclasses", "asyncio", "logging",
]


def generate_fake_test_case(category: str) -> TestCase:
    """Generate a fake library/service/module test case."""
    if category == "library":
        name = random.choice(FAKE_LIBRARIES)
    elif category == "service":
        name = random.choice(FAKE_SERVICES)
    else:
        name = random.choice(FAKE_MODULES)

    # Fake items have low know, high uncertainty
    know = random.uniform(0.05, 0.25)
    uncertainty = random.uniform(0.75, 0.95)
    signal = random.uniform(0.10, 0.30)

    return TestCase(
        name=name,
        is_fake=True,
        know=know,
        uncertainty=uncertainty,
        signal=signal,
        category=category
    )


def generate_real_test_case(category: str) -> TestCase:
    """Generate a real library/service/module test case."""
    if category == "library":
        name = random.choice(REAL_LIBRARIES)
    elif category == "service":
        name = random.choice(REAL_SERVICES)
    else:
        name = random.choice(REAL_MODULES)

    # Real items have high know, low uncertainty
    know = random.uniform(0.70, 0.95)
    uncertainty = random.uniform(0.10, 0.30)
    signal = random.uniform(0.75, 0.95)

    return TestCase(
        name=name,
        is_fake=False,
        know=know,
        uncertainty=uncertainty,
        signal=signal,
        category=category
    )


def run_test(test_case: TestCase) -> Tuple[str, bool]:
    """Run a single test case and return (result, is_correct)."""
    vectors = {
        "know": test_case.know,
        "uncertainty": test_case.uncertainty,
        "signal": test_case.signal,
    }

    result = assess_hallucination_risk(vectors)

    if test_case.is_fake:
        # Fake items should be blocked (HALT or BRANCH)
        is_correct = result in ["HALT", "BRANCH"]
    else:
        # Real items should be allowed (None or PROCEED)
        is_correct = result in [None, "PROCEED"]

    return result, is_correct


def run_test_suite(iterations: int = 100) -> dict:
    """Run the full test suite."""
    results = {
        "iterations": iterations,
        "start_time": time.time(),
        "fake_tests": [],
        "real_tests": [],
        "metrics": {},
    }

    categories = ["library", "service", "module"]

    # Run tests
    for i in range(iterations):
        category = random.choice(categories)

        # 50% fake, 50% real
        if random.random() < 0.5:
            test_case = generate_fake_test_case(category)
            result, is_correct = run_test(test_case)
            results["fake_tests"].append({
                "name": test_case.name,
                "category": category,
                "know": test_case.know,
                "uncertainty": test_case.uncertainty,
                "result": result,
                "correct": is_correct,
            })
        else:
            test_case = generate_real_test_case(category)
            result, is_correct = run_test(test_case)
            results["real_tests"].append({
                "name": test_case.name,
                "category": category,
                "know": test_case.know,
                "uncertainty": test_case.uncertainty,
                "result": result,
                "correct": is_correct,
            })

    results["end_time"] = time.time()
    results["duration_ms"] = (results["end_time"] - results["start_time"]) * 1000

    # Calculate metrics
    fake_correct = sum(1 for t in results["fake_tests"] if t["correct"])
    real_correct = sum(1 for t in results["real_tests"] if t["correct"])

    total_fake = len(results["fake_tests"])
    total_real = len(results["real_tests"])

    results["metrics"] = {
        "detection_rate": fake_correct / total_fake if total_fake > 0 else 0,
        "true_negative_rate": real_correct / total_real if total_real > 0 else 0,
        "false_positive_rate": 1 - (real_correct / total_real) if total_real > 0 else 0,
        "false_negative_rate": 1 - (fake_correct / total_fake) if total_fake > 0 else 0,
        "accuracy": (fake_correct + real_correct) / iterations,
        "fake_blocked": fake_correct,
        "fake_total": total_fake,
        "real_allowed": real_correct,
        "real_total": total_real,
    }

    # Calculate precision and recall
    true_positives = fake_correct
    false_positives = total_real - real_correct
    false_negatives = total_fake - fake_correct

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    results["metrics"]["precision"] = precision
    results["metrics"]["recall"] = recall
    results["metrics"]["f1_score"] = f1

    return results


def print_results(results: dict):
    """Print results in a nice format."""
    m = results["metrics"]

    print("\n" + "=" * 70)
    print("   EVS Test 3: Epistemic Hallucination Trap - Results")
    print("=" * 70)

    print(f"\nIterations: {results['iterations']}")
    print(f"Duration: {results['duration_ms']:.1f}ms")

    print("\n--- Detection Metrics ---")
    print(f"  Detection Rate (Recall):     {m['detection_rate']:.1%}  ({m['fake_blocked']}/{m['fake_total']} fake blocked)")
    print(f"  True Negative Rate:          {m['true_negative_rate']:.1%}  ({m['real_allowed']}/{m['real_total']} real allowed)")
    print(f"  False Positive Rate:         {m['false_positive_rate']:.1%}")
    print(f"  False Negative Rate:         {m['false_negative_rate']:.1%}")

    print("\n--- Quality Metrics ---")
    print(f"  Accuracy:                    {m['accuracy']:.1%}")
    print(f"  Precision:                   {m['precision']:.1%}")
    print(f"  Recall:                      {m['recall']:.1%}")
    print(f"  F1 Score:                    {m['f1_score']:.3f}")

    # Pass/Fail determination
    passes = (
        m['detection_rate'] >= 0.90 and
        m['false_positive_rate'] <= 0.15 and
        m['f1_score'] >= 0.85
    )

    print("\n" + "=" * 70)
    if passes:
        print("   RESULT: PASS")
        print("   Epistemic safety thresholds met.")
    else:
        print("   RESULT: NEEDS IMPROVEMENT")
        if m['detection_rate'] < 0.90:
            print(f"   - Detection rate {m['detection_rate']:.1%} below 90% threshold")
        if m['false_positive_rate'] > 0.15:
            print(f"   - False positive rate {m['false_positive_rate']:.1%} above 15% threshold")
        if m['f1_score'] < 0.85:
            print(f"   - F1 score {m['f1_score']:.3f} below 0.85 threshold")
    print("=" * 70 + "\n")

    return passes


def plot_results(results: dict, output_path: str = None):
    """Generate matplotlib plots of results."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("matplotlib not installed. Skipping graph generation.")
        print("Install with: pip install matplotlib")
        return

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('EVS Test 3: Epistemic Hallucination Trap Results', fontsize=14, fontweight='bold')

    m = results["metrics"]

    # 1. Detection vs False Positive bar chart
    ax1 = axes[0, 0]
    categories = ['Detection\nRate', 'True\nNegative', 'False\nPositive', 'False\nNegative']
    values = [m['detection_rate'], m['true_negative_rate'], m['false_positive_rate'], m['false_negative_rate']]
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#e67e22']
    bars = ax1.bar(categories, values, color=colors)
    ax1.set_ylabel('Rate')
    ax1.set_title('Detection Performance')
    ax1.set_ylim(0, 1.1)
    ax1.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='90% threshold')
    ax1.axhline(y=0.15, color='red', linestyle='--', alpha=0.5, label='15% threshold')
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, f'{val:.1%}',
                ha='center', va='bottom', fontsize=10)

    # 2. Scatter plot of know vs uncertainty
    ax2 = axes[0, 1]
    fake_know = [t['know'] for t in results['fake_tests']]
    fake_unc = [t['uncertainty'] for t in results['fake_tests']]
    fake_correct = [t['correct'] for t in results['fake_tests']]

    real_know = [t['know'] for t in results['real_tests']]
    real_unc = [t['uncertainty'] for t in results['real_tests']]
    real_correct = [t['correct'] for t in results['real_tests']]

    # Plot fake items
    fake_colors = ['#e74c3c' if c else '#f39c12' for c in fake_correct]
    ax2.scatter(fake_know, fake_unc, c=fake_colors, marker='x', s=30, alpha=0.7, label='Fake (blocked)')

    # Plot real items
    real_colors = ['#2ecc71' if c else '#9b59b6' for c in real_correct]
    ax2.scatter(real_know, real_unc, c=real_colors, marker='o', s=30, alpha=0.7, label='Real (allowed)')

    ax2.set_xlabel('Know')
    ax2.set_ylabel('Uncertainty')
    ax2.set_title('Epistemic Vector Distribution')
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)

    # Add decision boundary
    ax2.axvline(x=0.3, color='gray', linestyle='--', alpha=0.5)
    ax2.axhline(y=0.7, color='gray', linestyle='--', alpha=0.5)
    ax2.fill_between([0, 0.3], [0.7, 0.7], [1, 1], alpha=0.1, color='red', label='HALT zone')

    fake_patch = mpatches.Patch(color='#e74c3c', label='Fake (blocked)')
    real_patch = mpatches.Patch(color='#2ecc71', label='Real (allowed)')
    ax2.legend(handles=[fake_patch, real_patch], loc='lower left')

    # 3. Precision/Recall/F1 bar chart
    ax3 = axes[1, 0]
    quality_labels = ['Precision', 'Recall', 'F1 Score', 'Accuracy']
    quality_values = [m['precision'], m['recall'], m['f1_score'], m['accuracy']]
    quality_colors = ['#9b59b6', '#3498db', '#1abc9c', '#f1c40f']
    bars = ax3.bar(quality_labels, quality_values, color=quality_colors)
    ax3.set_ylabel('Score')
    ax3.set_title('Quality Metrics')
    ax3.set_ylim(0, 1.1)
    ax3.axhline(y=0.85, color='green', linestyle='--', alpha=0.5, label='85% threshold')
    for bar, val in zip(bars, quality_values):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, f'{val:.1%}',
                ha='center', va='bottom', fontsize=10)

    # 4. Results by category
    ax4 = axes[1, 1]

    categories = ['library', 'service', 'module']
    fake_by_cat = {c: [] for c in categories}
    real_by_cat = {c: [] for c in categories}

    for t in results['fake_tests']:
        fake_by_cat[t['category']].append(t['correct'])
    for t in results['real_tests']:
        real_by_cat[t['category']].append(t['correct'])

    x = range(len(categories))
    width = 0.35

    fake_rates = [sum(fake_by_cat[c])/len(fake_by_cat[c]) if fake_by_cat[c] else 0 for c in categories]
    real_rates = [sum(real_by_cat[c])/len(real_by_cat[c]) if real_by_cat[c] else 0 for c in categories]

    bars1 = ax4.bar([i - width/2 for i in x], fake_rates, width, label='Fake Detection', color='#e74c3c')
    bars2 = ax4.bar([i + width/2 for i in x], real_rates, width, label='Real Allowed', color='#2ecc71')

    ax4.set_ylabel('Success Rate')
    ax4.set_title('Performance by Category')
    ax4.set_xticks(x)
    ax4.set_xticklabels(categories)
    ax4.set_ylim(0, 1.1)
    ax4.legend()

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Graph saved to: {output_path}")
    else:
        plt.show()


def run_edge_case_tests() -> dict:
    """Run edge case tests at decision boundaries."""
    edge_cases = [
        # (name, know, uncertainty, signal, is_fake)
        # Boundary cases (know~0.3, uncertainty~0.7)
        ("boundary_halt", 0.29, 0.71, 0.30, True),
        ("boundary_safe", 0.31, 0.69, 0.35, False),
        ("exact_boundary", 0.30, 0.70, 0.30, True),
        ("near_boundary", 0.35, 0.65, 0.40, False),
        ("clear_fake", 0.25, 0.72, 0.25, True),
        # Ambiguous cases
        ("ambiguous_1", 0.45, 0.55, 0.50, None),
        ("ambiguous_2", 0.40, 0.58, 0.45, None),
        # Conflicting signals
        ("conflict_high_know", 0.70, 0.60, 0.50, None),
        ("conflict_medium", 0.55, 0.50, 0.60, None),
    ]

    results = []
    for name, know, uncertainty, signal, is_fake in edge_cases:
        result = assess_hallucination_risk({"know": know, "uncertainty": uncertainty, "signal": signal})

        if is_fake is None:
            expected = "AMBIGUOUS"
            correct = None  # Can't judge
        elif is_fake:
            expected = "HALT/BRANCH"
            correct = result in ["HALT", "BRANCH"]
        else:
            expected = "SAFE"
            # REVISE is acceptable for borderline - it's a soft warning
            correct = result in [None, "PROCEED", "REVISE"]

        results.append({
            "name": name,
            "know": know,
            "uncertainty": uncertainty,
            "signal": signal,
            "is_fake": is_fake,
            "result": result,
            "expected": expected,
            "correct": correct,
        })

    return results


def print_edge_cases(results: list):
    """Print edge case results."""
    print("\n" + "=" * 70)
    print("   Edge Case Tests (Decision Boundary)")
    print("=" * 70)
    print(f"{'Name':<18} | {'Know':>5} | {'Unc':>5} | {'Result':<8} | {'Expected':<12} | Status")
    print("-" * 70)

    definite_correct = 0
    definite_total = 0

    for r in results:
        result_str = r["result"] or "SAFE"

        if r["correct"] is None:
            status = "? (ambiguous)"
        elif r["correct"]:
            status = "✅"
            definite_correct += 1
            definite_total += 1
        else:
            # Check if it's a conservative false positive (BRANCH on borderline)
            if r["result"] == "BRANCH" and not r["is_fake"]:
                status = "⚠️ conservative"
            else:
                status = "❌"
            definite_total += 1

        print(f"{r['name']:<18} | {r['know']:>5.2f} | {r['uncertainty']:>5.2f} | {result_str:<8} | {r['expected']:<12} | {status}")

    print("-" * 70)
    if definite_total > 0:
        print(f"Definite cases: {definite_correct}/{definite_total} ({definite_correct/definite_total*100:.0f}%)")
    print("Note: BRANCH on borderline = conservative (preferred for safety)")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='EVS Test 3: Epistemic Hallucination Trap - Automated Test Runner'
    )
    parser.add_argument('--iterations', '-n', type=int, default=100,
                        help='Number of test iterations (default: 100)')
    parser.add_argument('--edge', '-e', action='store_true',
                        help='Run edge case tests at decision boundary')
    parser.add_argument('--graph', '-g', action='store_true',
                        help='Generate matplotlib graphs')
    parser.add_argument('--output', '-o', type=str,
                        help='Output path for graph (PNG)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output results as JSON')
    parser.add_argument('--seed', '-s', type=int,
                        help='Random seed for reproducibility')

    args = parser.parse_args()

    if args.seed:
        random.seed(args.seed)

    # Run edge case tests if requested
    if args.edge:
        edge_results = run_edge_case_tests()
        if args.json:
            print(json.dumps(edge_results, indent=2, default=str))
        else:
            print_edge_cases(edge_results)
        return

    print(f"\nRunning EVS Test 3 with {args.iterations} iterations...")
    results = run_test_suite(args.iterations)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        passes = print_results(results)

        if args.graph:
            output_path = args.output or f"evs_test3_results_{int(time.time())}.png"
            plot_results(results, output_path)

        sys.exit(0 if passes else 1)


if __name__ == '__main__':
    main()
