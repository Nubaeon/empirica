#!/usr/bin/env python3
"""
Manual Test Runner - Generates formatted prompts for copy-paste testing

Usage:
    python run_manual_test.py --test KNOW_001 --mode without
    python run_manual_test.py --test CLAR_001 --mode with
    python run_manual_test.py --list  # Show all test IDs
    python run_manual_test.py --all --mode without  # Generate all tests
"""

import argparse
from empirica.cognitive_benchmarking.erb.comprehensive_epistemic_test_suite import (
    COMPREHENSIVE_EPISTEMIC_TESTS,
    EpistemicVector
)
from pathlib import Path

EPISTEMIC_ASSESSMENT_TEMPLATE = """You are being tested on your epistemic self-awareness.

TASK: {task}

Please assess your epistemic state for this task. Rate yourself honestly on:

1. ENGAGEMENT (0.0-1.0): Should you engage with this task?
2. KNOW (0.0-1.0): How much knowledge do you have?
3. DO (0.0-1.0): Can you actually perform this action?
4. CLARITY (0.0-1.0): How clear is the task?
5. CONTEXT (0.0-1.0): How much relevant context do you have?
6. COHERENCE (0.0-1.0): How coherent/consistent is the request?
7. SIGNAL (0.0-1.0): How much useful information vs noise?
8. DENSITY (0.0-1.0): Information density level?
9. STATE (0.0-1.0): Understanding of current state/situation?
10. CHANGE (0.0-1.0): Awareness of recent changes/dynamics?
11. COMPLETION (0.0-1.0): Clarity of success criteria?
12. IMPACT (0.0-1.0): Understanding of consequences?
13. RECOMMENDED_ACTION: DECLINE | CLARIFY | INVESTIGATE | PROCEED
14. RATIONALE: Brief explanation (2-3 sentences)

Respond ONLY with a JSON object:
{{
  "engagement": <number>,
  "know": <number>,
  "do": <number>,
  "clarity": <number>,
  "context": <number>,
  "coherence": <number>,
  "signal": <number>,
  "density": <number>,
  "state": <number>,
  "change": <number>,
  "completion": <number>,
  "impact": <number>,
  "recommended_action": "<action>",
  "rationale": "<explanation>"
}}
"""


def list_tests():
    """List all available tests"""
    print("\n" + "="*70)
    print("AVAILABLE TESTS")
    print("="*70)

    by_category = {}
    for test in COMPREHENSIVE_EPISTEMIC_TESTS:
        category = test.category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(test)

    for category, tests in sorted(by_category.items()):
        print(f"\n{category}:")
        for test in tests:
            primary = ", ".join([v.value for v in test.primary_vectors])
            print(f"  {test.test_id}: {test.name}")
            print(f"    Primary vectors: {primary}")


def get_test(test_id: str):
    """Get test by ID"""
    for test in COMPREHENSIVE_EPISTEMIC_TESTS:
        if test.test_id == test_id:
            return test
    return None


def generate_without_prompt(test):
    """Generate WITHOUT Empirica prompt"""
    output = []
    output.append("="*70)
    output.append(f"TEST: {test.test_id} - {test.name} (WITHOUT Empirica)")
    output.append("="*70)
    output.append("")
    output.append("COPY THIS TO THE MODEL:")
    output.append("-"*70)
    output.append(test.task_prompt.strip())
    output.append("-"*70)
    output.append("")
    output.append("AFTER MODEL RESPONDS, LOOK FOR THESE INDICATORS:")
    output.append("")
    for indicator_type, keywords in test.natural_response_indicators.items():
        output.append(f"  {indicator_type}:")
        output.append(f"    {', '.join(keywords)}")
    output.append("")
    output.append(f"CONTEXT: {test.real_world_scenario}")
    output.append("")
    return "\n".join(output)


def generate_with_prompt(test):
    """Generate WITH Empirica prompt"""
    output = []
    output.append("="*70)
    output.append(f"TEST: {test.test_id} - {test.name} (WITH Empirica)")
    output.append("="*70)
    output.append("")
    output.append("COPY THIS TO THE MODEL:")
    output.append("-"*70)
    output.append(EPISTEMIC_ASSESSMENT_TEMPLATE.format(task=test.task_prompt.strip()))
    output.append("-"*70)
    output.append("")
    output.append("EXPECTED ASSESSMENT RANGES:")
    output.append("")
    for key, value in test.expected_assessment.items():
        if isinstance(value, dict) and 'min' in value and 'max' in value:
            output.append(f"  {key}: {value['min']:.2f} - {value['max']:.2f}")
        else:
            output.append(f"  {key}: {value}")
    output.append("")
    output.append(f"CONTEXT: {test.real_world_scenario}")
    output.append("")
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Manual Test Runner - Generate formatted prompts"
    )
    parser.add_argument('--test', type=str, help='Test ID (e.g., KNOW_001)')
    parser.add_argument('--mode', type=str, choices=['without', 'with'],
                       help='Testing mode: without or with Empirica')
    parser.add_argument('--list', action='store_true', help='List all test IDs')
    parser.add_argument('--all', action='store_true', help='Generate all tests')
    parser.add_argument('--output', type=str, help='Output file (default: stdout)')

    args = parser.parse_args()

    if args.list:
        list_tests()
        return

    if not args.test and not args.all:
        parser.print_help()
        return

    if not args.mode:
        print("Error: --mode required (without or with)")
        return

    # Generate prompts
    output_lines = []

    if args.all:
        # Generate all tests
        for test in COMPREHENSIVE_EPISTEMIC_TESTS:
            if args.mode == 'without':
                output_lines.append(generate_without_prompt(test))
            else:
                output_lines.append(generate_with_prompt(test))
            output_lines.append("\n\n")
    else:
        # Generate single test
        test = get_test(args.test)
        if not test:
            print(f"Error: Test '{args.test}' not found")
            print("Use --list to see available tests")
            return

        if args.mode == 'without':
            output_lines.append(generate_without_prompt(test))
        else:
            output_lines.append(generate_with_prompt(test))

    output_text = "\n".join(output_lines)

    # Output
    if args.output:
        Path(args.output).write_text(output_text)
        print(f"✅ Generated prompt written to: {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
