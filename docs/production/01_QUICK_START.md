# 🚀 Quick Start Guide

Get up and running with Empirica in 5 minutes.

---

## Installation

```bash
# Clone repository
git clone https://github.com/Nubaeon/empirica
cd empirica

# Install dependencies
pip install -r requirements.txt

# Verify installation (basic check)
python3 -c "import empirica; print('✅ Empirica installed!')"

# Or verify CLI is available
empirica --help
```

---

## Choose Your Interface

Empirica offers two ways to work:
1. **CLI Commands** (Recommended for most users) - Simple, fast, no coding required
2. **Python API** (Advanced) - Full programmatic control

---

## Quick Start: CLI Workflow

The easiest way to use Empirica is via CLI commands:

### 1. Bootstrap Empirica
```bash
# Initialize with standard components
empirica bootstrap --level 2
```

### 2. Start a Cascade with PREFLIGHT
```bash
# Create session and get assessment prompt (non-blocking)
empirica preflight "Should I refactor the authentication system?" \
  --session-id $(uuidgen) \
  --prompt-only

# Returns immediately with self-assessment prompt
```

### 3. Submit Your Self-Assessment
```bash
# Rate your epistemic state honestly (13 vectors, 0.0-1.0 scale)
empirica preflight-submit \
  --session-id <your-session-id> \
  --vectors '{
    "engagement": 0.85,
    "know": 0.70,
    "do": 0.80,
    "context": 0.75,
    "clarity": 0.85,
    "coherence": 0.80,
    "signal": 0.75,
    "density": 0.65,
    "state": 0.75,
    "change": 0.40,
    "completion": 0.20,
    "impact": 0.80,
    "uncertainty": 0.45
  }' \
  --output json
```

### 4. Continue with CHECK Phase
```bash
# After investigation, assess readiness to act
empirica check \
  --session-id <your-session-id> \
  --findings '["Finding 1", "Finding 2"]' \
  --unknowns '["Unknown 1"]' \
  --confidence 0.75 \
  --output json

# Submit updated assessment
empirica check-submit \
  --session-id <your-session-id> \
  --vectors '{...}' \
  --decision proceed \
  --reasoning "Ready to act because..."
```

### 5. Complete with POSTFLIGHT
```bash
# After completing work, reflect on learning
empirica postflight <your-session-id> \
  --summary "What you accomplished" \
  --prompt-only

# Submit final assessment
empirica postflight-submit \
  --session-id <your-session-id> \
  --vectors '{...}' \
  --changes "KNOW: 0.70→0.90 (+0.20), UNCERTAINTY: 0.45→0.15 (-0.30)"
```

**Key Feature: `--prompt-only` Flag**
- Returns assessment prompt immediately (non-blocking)
- No LLM calls, no waiting
- Perfect for AI agents that want control over timing
- Omit flag for blocking mode (waits for LLM response)

---

## Your First Cascade (Python API)

```python
import asyncio
from empirica.core.metacognitive_cascade import MetacognitiveCascade

async def main():
    # Create cascade
    cascade = MetacognitiveCascade()
    
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
cascade = MetacognitiveCascade(
    enable_bayesian=True,           # Evidence-based belief tracking
    enable_drift_monitor=True,      # Behavioral integrity checks
    enable_action_hooks=True,       # Real-time dashboard
    auto_start_dashboard=False      # Manual tmux start
)
```

---

## Watch Live in Dashboard

**Note:** Dashboard functionality is currently available via MCP integration (see below). 
Standalone dashboard support is planned for a future release.

For now, monitor your cascades via:
- CLI command output with `--output json`
- Database queries: `empirica sessions-show <session-id>`
- MCP tools in Claude Desktop

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
from empirica.investigation.investigation_plugin import InvestigationPlugin

jira_plugin = InvestigationPlugin(
    name="jira_search",
    description="Search JIRA for related issues",
    improves_vectors=["know", "context"],
    confidence_gain=0.20
)

cascade = MetacognitiveCascade(
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

## Data Storage

Empirica stores all session data locally:

**Database Location:** `.empirica/sessions/sessions.db` (project-relative)
- All assessments (PREFLIGHT, CHECK, POSTFLIGHT)
- Learning progression metrics
- Session metadata

**Git Checkpoints:** `git notes refs/empirica/checkpoints/`
- 97.5% token reduction for session resumption
- Stored alongside your git repository

**Handoff Reports:** `git notes refs/empirica/handoff/`
- 98% token reduction for session continuity
- Enable multi-agent coordination

**View Your Data:**
```bash
# List all sessions
empirica sessions-list

# Show session details
empirica sessions-show <session-id>

# Query handoff reports
empirica handoff-query --session-id <session-id> --output json
```

---

## Troubleshooting

**Import Error (ModuleNotFoundError):**
```bash
# Ensure you're in the project directory
cd /path/to/empirica

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import empirica; print('✅ Ready!')"

# Test CLI
empirica --help
```

**Can't Find Session Data:**
```bash
# Database is project-relative, not global
# Check current directory
ls .empirica/sessions/sessions.db

# Or specify full path
empirica sessions-list
```

**CLI Command Not Found:**
```bash
# Ensure empirica is in PATH
pip install -e .

# Or use full path
python3 -m empirica.cli.cli_core --help
```

**JSON Parsing Errors:**
```bash
# Ensure JSON is properly quoted
empirica preflight-submit \
  --vectors '{"engagement": 0.85, "know": 0.70, ...}'
#          ^ single quotes around JSON object
```

---

**Ready to dive deeper?** → `04_ARCHITECTURE_OVERVIEW.md`
