"""
Architecture Assessment Command Handlers

CLI handlers for epistemic architecture assessment.
"""

import json
import sys
from pathlib import Path

from empirica.core.architecture_assessment import ComponentAssessor


def handle_assess_component_command(args):
    """Handle assess-component command."""
    project_root = Path(args.project_root).resolve()
    assessor = ComponentAssessor(str(project_root))

    assessment = assessor.assess(args.path)

    if args.output == 'json':
        print(json.dumps(assessment.to_dict(), indent=2, default=str))
    elif args.output == 'summary':
        print(assessment.summary())
    else:
        # Full text output
        _print_assessment_text(assessment)

    return 0


def handle_assess_compare_command(args):
    """Handle assess-compare command."""
    project_root = Path(args.project_root).resolve()
    assessor = ComponentAssessor(str(project_root))

    comparison = assessor.compare(args.path_a, args.path_b)

    if args.output == 'json':
        print(json.dumps(comparison, indent=2, default=str))
    else:
        _print_comparison_text(comparison)

    return 0


def handle_assess_directory_command(args):
    """Handle assess-directory command."""
    project_root = Path(args.project_root).resolve()
    assessor = ComponentAssessor(str(project_root))

    target_dir = Path(args.path)
    if not target_dir.is_absolute():
        target_dir = project_root / target_dir

    # Find all Python files
    py_files = list(target_dir.rglob("*.py"))
    if not py_files:
        print(f"No Python files found in {target_dir}")
        return 1

    # Assess all
    assessments = []
    for py_file in py_files:
        try:
            assessment = assessor.assess(str(py_file))
            assessments.append(assessment)
        except Exception as e:
            print(f"Warning: Could not assess {py_file}: {e}", file=sys.stderr)

    # Sort by confidence (lowest first = worst health)
    assessments.sort(key=lambda a: a.vectors.confidence_score())

    if args.output == 'json':
        # Calculate average health from all assessments
        avg_health = 0.0
        if assessments:
            health_scores = [a.vectors.confidence_score() for a in assessments]
            avg_health = sum(health_scores) / len(health_scores)

        output = {
            'total_files': len(py_files),
            'assessed': len(assessments),
            'average_health': avg_health,
            'worst_components': [a.to_dict() for a in assessments[:args.top]],
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        _print_directory_assessment(assessments, args.top, target_dir)

    return 0


def _print_assessment_text(assessment):
    """Print detailed assessment in text format."""
    vectors = assessment.vectors
    confidence = vectors.confidence_score()

    # Risk level with color coding
    risk_colors = {
        'low': '\033[92m',      # Green
        'medium': '\033[93m',   # Yellow
        'high': '\033[91m',     # Red
        'critical': '\033[95m', # Magenta
    }
    reset = '\033[0m'
    risk_color = risk_colors.get(assessment.risk_level, '')

    print(f"\n{'='*60}")
    print(f"🔬 EPISTEMIC ASSESSMENT: {assessment.component_name}")
    print(f"{'='*60}")
    print(f"Type: {assessment.component_type}")
    print(f"Path: {assessment.component_path}")
    print(f"Analyzed: {assessment.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n📊 CONFIDENCE: {confidence:.0%} | RISK: {risk_color}{assessment.risk_level.upper()}{reset}")

    print(f"\n{'─'*60}")
    print("📈 EPISTEMIC VECTORS")
    print(f"{'─'*60}")

    # Group vectors by category
    foundation = [
        ('Know', vectors.know),
        ('Uncertainty', vectors.uncertainty, True),  # Inverted
        ('Context', vectors.context),
    ]

    quality = [
        ('Clarity', vectors.clarity),
        ('Coherence', vectors.coherence),
        ('Signal', vectors.signal),
        ('Density', vectors.density, True),  # Inverted
    ]

    activity = [
        ('Engagement', vectors.engagement),
        ('State', vectors.state),
        ('Change', vectors.change, True),  # Inverted
    ]

    outcome = [
        ('Completion', vectors.completion),
        ('Impact', vectors.impact, True),  # Inverted
        ('Do', vectors.do),
    ]

    def print_vector(name, value, inverted=False):
        bar_width = 20
        filled = int(value * bar_width)
        bar = '█' * filled + '░' * (bar_width - filled)
        indicator = ' ⚠' if inverted and value > 0.6 else ''
        print(f"  {name:12s} [{bar}] {value:.0%}{indicator}")

    print("\nFoundation:")
    for v in foundation:
        print_vector(*v)

    print("\nQuality:")
    for v in quality:
        print_vector(*v)

    print("\nActivity:")
    for v in activity:
        print_vector(*v)

    print("\nOutcome:")
    for v in outcome:
        print_vector(*v)

    # Coupling metrics
    if assessment.coupling:
        c = assessment.coupling
        print(f"\n{'─'*60}")
        print("🔗 COUPLING METRICS")
        print(f"{'─'*60}")
        print(f"  Afferent (incoming):  {c.afferent_coupling}")
        print(f"  Efferent (outgoing):  {c.efferent_coupling}")
        print(f"  Instability:          {c.instability:.2f}")
        print(f"  Abstractness:         {c.abstractness:.2f}")
        print(f"  Distance from main:   {c.distance_from_main:.2f}")
        print(f"  API surface ratio:    {c.api_surface_ratio:.0%}")
        print(f"  Public functions:     {c.public_functions}")
        print(f"  Private functions:    {c.private_functions}")
        if c.leaked_internals:
            print(f"  ⚠️ Leaked internals:   {c.leaked_internals}")

    # Stability metrics
    if assessment.stability:
        s = assessment.stability
        print(f"\n{'─'*60}")
        print("📉 STABILITY METRICS")
        print(f"{'─'*60}")
        print(f"  Total commits:        {s.total_commits}")
        print(f"  Recent (30d):         {s.recent_commits_30d}")
        print(f"  Unique authors:       {s.unique_authors}")
        print(f"  Avg lines/commit:     {s.avg_lines_per_commit:.1f}")
        print(f"  Churn rate:           {s.churn_rate:.2f}")
        print(f"  Hotspot score:        {s.hotspot_score:.2f}")
        print(f"  Age (days):           {s.age_days}")
        print(f"  Days since change:    {s.days_since_last_change}")
        print(f"  Maintenance ratio:    {s.maintenance_ratio:.0%}")

    # Recommendations
    if assessment.recommendations:
        print(f"\n{'─'*60}")
        print("💡 RECOMMENDATIONS")
        print(f"{'─'*60}")
        for i, rec in enumerate(assessment.recommendations, 1):
            print(f"  {i}. {rec}")

    # Priority improvements
    if assessment.improvement_priority:
        print(f"\n{'─'*60}")
        print("🎯 PRIORITY IMPROVEMENTS")
        print(f"{'─'*60}")
        print(f"  Focus on: {', '.join(assessment.improvement_priority)}")

    print(f"\n{'='*60}\n")


def _print_comparison_text(comparison):
    """Print comparison in text format."""
    print(f"\n{'='*60}")
    print("🔍 COMPONENT COMPARISON")
    print(f"{'='*60}")

    print(f"\n{comparison['component_a']:^29s} vs {comparison['component_b']:^29s}")
    print(f"{'─'*60}")

    # Confidence and risk
    conf_a = comparison['confidence_a']
    conf_b = comparison['confidence_b']
    print(f"  Confidence:  {conf_a:.0%}                    {conf_b:.0%}")
    print(f"  Risk:        {comparison['risk_a']:20s} {comparison['risk_b']}")

    # Vector differences
    print(f"\n{'─'*60}")
    print("Vector Differences (A - B):")
    print(f"{'─'*60}")

    for vector, diff in comparison['vector_differences'].items():
        if abs(diff) > 0.1:
            direction = "←" if diff < 0 else "→"
            print(f"  {vector:12s}: {diff:+.0%} {direction}")

    print(f"\n🏆 Healthier: {comparison['healthier']}")
    print(f"{'='*60}\n")


def _print_directory_assessment(assessments, top_n, target_dir):
    """Print directory assessment summary."""
    print(f"\n{'='*60}")
    print(f"📁 DIRECTORY ASSESSMENT: {target_dir.name}")
    print(f"{'='*60}")
    print(f"Total files assessed: {len(assessments)}")

    # Overall stats
    if assessments:
        avg_confidence = sum(a.vectors.confidence_score() for a in assessments) / len(assessments)
        risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for a in assessments:
            risk_counts[a.risk_level] = risk_counts.get(a.risk_level, 0) + 1

        print(f"\nAverage confidence: {avg_confidence:.0%}")
        print(f"Risk distribution: 🟢 {risk_counts['low']} low | 🟡 {risk_counts['medium']} medium | 🔴 {risk_counts['high']} high | 💀 {risk_counts['critical']} critical")

    # Worst components
    print(f"\n{'─'*60}")
    print(f"⚠️ TOP {top_n} WORST COMPONENTS (by confidence)")
    print(f"{'─'*60}")

    for i, assessment in enumerate(assessments[:top_n], 1):
        conf = assessment.vectors.confidence_score()
        risk_symbols = {'low': '🟢', 'medium': '🟡', 'high': '🔴', 'critical': '💀'}
        symbol = risk_symbols.get(assessment.risk_level, '❓')

        # Truncate path for display
        display_path = str(Path(assessment.component_path).relative_to(target_dir))
        if len(display_path) > 40:
            display_path = "..." + display_path[-37:]

        print(f"  {i:2d}. {symbol} {display_path:40s} ({conf:.0%})")

    print(f"\n{'='*60}\n")
