# 🚀 Quick Start Guide

Get up and running with Empirica in 5 minutes.

---

## Installation

```bash
# Clone repository
git clone https://github.com/your-org/empirica
cd empirica

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "from metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade; print('✅ Ready!')"
```

---

## Your First Cascade

```python
import asyncio
from metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade

async def main():
    # Create cascade
    cascade = CanonicalEpistemicCascade()
    
    # Run epistemic reasoning
    result = await cascade.run_epistemic_cascade(
        task="Should I refactor the authentication system?",
        context={"cwd": "/project", "complexity": "high"}
    )
    
    # Check result
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Rationale: {result['rationale']}")

asyncio.run(main())
```

**Output:**
```
Action: investigate
Confidence: 0.65
Rationale: Knowledge gap detected - need to understand current implementation
```

---

## Enable All Features

```python
cascade = CanonicalEpistemicCascade(
    enable_bayesian=True,           # Evidence-based belief tracking
    enable_drift_monitor=True,      # Behavioral integrity checks
    enable_action_hooks=True,       # Real-time dashboard
    auto_start_dashboard=False      # Manual tmux start
)
```

---

## Watch Live in Dashboard

```bash
# Terminal 1: Start dashboard
tmux new -s empirica
python3 tmux_dashboard/start_agi_dashboard.sh

# Terminal 2: Run cascade
python3 your_script.py

# Watch cascade progress in real-time in tmux!
```

---

## Via MCP (Claude Desktop)

**mcp_config.json:**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "python3",
      "args": ["/path/to/empirica/mcp_local/empirica_mcp_server.py"]
    }
  }
}
```

**Use in Claude:**
```
You: "Use Empirica to analyze if I should refactor this code"

Claude calls: cascade_run_full
{
  "question": "Should I refactor the auth code?",
  "enable_dashboard": true
}
```

---

## Next Steps

- **Understand the system:** Read `04_ARCHITECTURE_OVERVIEW.md`
- **Learn investigation:** Read `07_INVESTIGATION_SYSTEM.md`
- **Add custom tools:** Read `10_PLUGIN_SYSTEM.md`
- **Deploy to prod:** Read `17_PRODUCTION_DEPLOYMENT.md`

---

## Common Patterns

### Pattern 1: Simple Decision
```python
result = await cascade.run_epistemic_cascade(
    task="Should I proceed with deployment?",
    context={"tests_passed": True}
)
```

### Pattern 2: With Custom Plugins
```python
from metacognitive_cascade.investigation_plugin import InvestigationPlugin

jira_plugin = InvestigationPlugin(
    name="jira_search",
    description="Search JIRA for related issues",
    improves_vectors=["know", "context"],
    confidence_gain=0.20
)

cascade = CanonicalEpistemicCascade(
    investigation_plugins={"jira_search": jira_plugin}
)
```

### Pattern 3: Precision-Critical Domain
```python
# For medical, legal, financial, security domains
result = await cascade.run_epistemic_cascade(
    task="Analyze patient medication interactions",
    context={"domain": "medical"}
)

# Bayesian Guardian auto-activates for precision-critical domains
```

---

## What You Get

✅ **No Heuristics** - Genuine LLM-powered reasoning  
✅ **Strategic Guidance** - Suggests, doesn't control  
✅ **Evidence Tracking** - Bayesian belief calibration  
✅ **Behavioral Integrity** - Drift detection  
✅ **Extensible** - Add your own tools  
✅ **Live Monitoring** - Real-time dashboard  

---

## Troubleshooting

**Import Error:**
```bash
pip install -r requirements.txt
```

**Dashboard Not Starting:**
```bash
# Check tmux installed
tmux -V

# Start manually
tmux new -s empirica
```

**Cascade Runs But No Dashboard:**
```python
# Ensure hooks enabled
cascade = CanonicalEpistemicCascade(enable_action_hooks=True)
```

---

**Ready to dive deeper?** → `04_ARCHITECTURE_OVERVIEW.md`
