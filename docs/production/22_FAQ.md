# ❓ Frequently Asked Questions

Quick answers to common questions about Empirica.

---

## General

### What is Empirica?
A production-grade epistemic reasoning system that helps AIs measure and validate their knowledge state without interfering with their internal reasoning processes.

### Why "no heuristics"?
Instead of counting keywords or using simple rules, Empirica uses genuine LLM-powered self-assessment for authentic epistemic reasoning.

### What's "Approach B"?
The investigation philosophy: measure + suggest (not execute). Empirica maps tool capabilities and suggests actions, but lets the LLM decide and execute.

---

## Getting Started

### How do I install it?
```bash
git clone [repo]
cd empirica
pip install -r requirements.txt
```

See `01_QUICK_START.md` for details.

### What's the simplest way to use it?
```python
from metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade
cascade = CanonicalEpistemicCascade()
result = await cascade.run_epistemic_cascade(task, context)
```

### Can I use it with Claude Desktop?
Yes! See `12_MCP_INTEGRATION.md` for setup instructions.

---

## Features

### What are the 12 epistemic vectors?
KNOW, DO, CONTEXT, CLARITY, COHERENCE, SIGNAL, DENSITY, STATE, CHANGE, COMPLETION, IMPACT, ENGAGEMENT. See `05_EPISTEMIC_VECTORS.md`.

### What's the Bayesian Guardian?
Real-time evidence-based belief tracking that detects when your intuition diverges from accumulated evidence. See `08_BAYESIAN_GUARDIAN.md`.

### What's the Drift Monitor?
Behavioral integrity monitoring that detects sycophancy drift and tension avoidance. See `09_DRIFT_MONITOR.md`.

### What's the plugin system?
A way to add custom investigation tools without modifying core code. See `10_PLUGIN_SYSTEM.md`.

---

## Investigation

### When does investigation happen?
When overall confidence < threshold (default 0.70) and gaps are significant.

### When is investigation skipped?
When: 1) No significant gaps, 2) Simple tasks, 3) Creative tasks with good engagement, 4) Acceptable confidence.

### What's user clarification priority?
User clarification has the HIGHEST confidence gain (0.40-0.45) because it gets information directly from the source of truth.

### What tools are available?
16+ tools including web_search, semantic_search_qdrant, session_manager_search, user_clarification, and more. Plus unlimited via plugins.

---

## Configuration

### How do I enable all features?
```python
cascade = CanonicalEpistemicCascade(
    enable_bayesian=True,
    enable_drift_monitor=True,
    enable_action_hooks=True,
    auto_start_dashboard=True
)
```

### How do I change the confidence threshold?
```python
cascade = CanonicalEpistemicCascade(
    action_confidence_threshold=0.80  # Default is 0.70
)
```

### How do I add custom plugins?
```python
from metacognitive_cascade.investigation_plugin import InvestigationPlugin

my_plugin = InvestigationPlugin(...)
cascade = CanonicalEpistemicCascade(
    investigation_plugins={'my_tool': my_plugin}
)
```

---

## Dashboard

### What is the tmux dashboard?
A real-time visualization of cascade progress showing 12D vectors, phases, Bayesian status, and drift warnings.

### How do I start it?
```bash
tmux new -s empirica
python3 tmux_dashboard/start_agi_dashboard.sh
```

Or:
```python
cascade = CanonicalEpistemicCascade(auto_start_dashboard=True)
```

### What does it show?
- Current cascade phase
- All 12 epistemic vectors with visual bars
- Bayesian Guardian status
- Drift Monitor warnings
- Chain of thought reasoning
- Strategic guidance

---

## Bayesian Guardian

### When does it activate?
Precision-critical domains (medical, legal, security), low clarity situations, or after discrepancies.

### When does it stay dormant?
Creative tasks, high confidence situations, simple tasks.

### What are discrepancies?
When your intuitive belief diverges from evidence-based belief (overconfidence or underconfidence).

### How do I update beliefs?
```python
cascade.update_from_tool_execution(
    tool_name='web_search',
    success=True,
    vector_addressed='know',
    strength=0.8
)
```

---

## Drift Monitor

### What is sycophancy drift?
Pattern where delegate (user-pleasing) weight increases over time, becoming too agreeable.

### What is tension avoidance?
Pattern where conflicts and disagreements are not being acknowledged.

### How many decisions needed?
At least 10 synthesis decisions for drift detection.

### What happens if drift detected?
Warning provided with recommendations (increase trustee weight, activate skeptic mode).

---

## Troubleshooting

### Import errors?
```bash
pip install -r requirements.txt
```

### MCP server not starting?
Check Python path in config and install dependencies.

### Dashboard not showing?
Ensure `enable_action_hooks=True` and tmux is installed.

### Bayesian not activating?
Check domain classification and clarity scores. May be correctly dormant for creative tasks.

---

## Performance

### How fast is it?
- No investigation: 2-5 seconds
- With investigation: 10-30 seconds
- Depends on tool usage and LLM response time

### Can I run multiple cascades?
Yes, concurrent cascades are supported.

### Memory usage?
Lightweight - minimal memory footprint.

---

## Production

### Is it production ready?
Yes! All features complete, tested, and documented.

### How do I monitor in production?
- Reflex Frame logs (`.empirica_reflex_logs/`)
- Dashboard (tmux)
- Bayesian summaries
- Drift analysis

### How do I tune thresholds?
Collect production data, analyze confidence calibration, adjust thresholds based on domain.

---

## Advanced

### Can I customize the cascade flow?
Core flow is fixed (THINK → ACT), but you can:
- Add custom plugins
- Configure thresholds
- Enable/disable features
- Extend via inheritance

### Can I use a different LLM?
The canonical assessor uses a placeholder. Replace with your LLM integration.

### Can I add new vectors?
The 12 vectors are canonical. Extend via metadata or custom assessment layers.

---

## Community

### Can I contribute?
Yes! See `23_CONTRIBUTING.md` for guidelines.

### Where do I report bugs?
Open an issue in the repository.

### Can I share plugins?
Yes! Community plugins welcome.

---

## Philosophy

### Why "measure without controlling"?
Respect for LLM autonomy. Empirica provides measurement and guidance, but the LLM makes decisions.

### Why prioritize user clarification?
Users have information that's impossible to get elsewhere. Better to ask than assume.

### Why evidence-based calibration?
Intuition can be biased. Real evidence provides objective grounding.

---

Still have questions? Check the full documentation or open an issue!

