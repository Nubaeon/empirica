"""
Empirica Metrics Module

Tracks and reports on epistemic performance metrics:
- Flow state detection and tracking
- Learning velocity calculation
- CASCADE completeness scoring
- Goal completion rates

Components:
- FlowStateDetector: Detects when AI is in productive flow state
- MetricsCollector: Aggregates session and project metrics
- EfficiencyReport: Generates productivity reports

Usage:
    from empirica.metrics import FlowStateDetector, get_efficiency_report

    # Check flow state
    detector = FlowStateDetector(session_id)
    if detector.in_flow():
        print("AI is in flow state")

    # Get efficiency report
    report = get_efficiency_report(session_id)
"""
