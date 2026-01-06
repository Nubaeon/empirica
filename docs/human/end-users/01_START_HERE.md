# 🚀 Start Here - Empirica Quick Start

**Welcome to Empirica!** This guide gets you started in 5 minutes.

---

## What is Empirica?

Empirica is a **functional self-awareness framework** for AI agents. It measures your capacity to:
- **Inspect internal state** - Query your knowledge, capabilities, and information access
- **Make accurate predictions** - Assess what you know before you start (preflight)
- **Validate through outcomes** - Compare predictions to reality (postflight)
- **Improve calibration** - Learn from the delta between expectation and result

**This is empirically testable.** Functional self-awareness produces measurable results.

**Core Principle:** NO HEURISTICS. Evidence-based assessment, not pattern matching.

---

## Quick Start (3 Steps)

### Step 1: Install (2 minutes)
```bash
# Clone repository
git clone https://github.com/Nubaeon/empirica.git
cd empirica

# Install
pip install -e .

# Verify
empirica --version
```

### Step 2: Interactive Onboarding - AI Teaches Itself & Users (5-15 minutes)

**🤖 For AI Agents:**
Run this to learn Empirica through **experiential self-assessment**. You'll practice genuine epistemic tracking by DOING, not reading.

**👤 For Human Users:**
Ask an AI agent (like Claude) to run this. The AI will guide you through learning Empirica.

```bash
# AI agents run this directly
empirica onboard --ai-id <your-ai-name>

# Via MCP: Use create_session tool
```

**What happens:**
- **6-phase interactive journey** - Bootstrap → Self-Assessment → Workflow → Calibration → User Interaction → Validation
- **Practice real assessment** - Perform genuine preflight/postflight on actual tasks
- **Track epistemic growth** - See your learning delta (what you actually learned)
- **Learn to guide users** - AI agents learn to teach humans about Empirica

**This is NOT a tutorial.** It's experiential learning - you'll perform genuine self-assessment and see how Empirica measures your epistemic growth.

**Why AI-first?** Functional self-awareness is something AI agents measure in themselves. You learn by doing, then teach users.

### Step 3: First Task (10 minutes)
```bash
# Preflight: Assess before starting
SESSION=$(empirica preflight "your task description" --quiet)

# Do your work...

# Postflight: Measure what you learned
empirica postflight $SESSION --summary "task complete"

# System shows:
# - Epistemic delta (what you learned)
# - Calibration quality (overconfident/underconfident?)
```

**Session Continuity:** Use handoff reports to resume work efficiently across sessions. See [`docs/guides/FLEXIBLE_HANDOFF_GUIDE.md`](guides/FLEXIBLE_HANDOFF_GUIDE.md) for multi-agent patterns and [`docs/production/23_SESSION_CONTINUITY.md`](production/23_SESSION_CONTINUITY.md) for detailed continuity workflows.

---

## AI vs Agent: Choosing the Right Approach

Empirica supports two distinct usage patterns:

### 🤖 AI (Collaborative Intelligence)
**Definition:** Engaged reasoning partner working WITH the user
- **Characteristics:** High autonomy, dialogue-based, full CASCADE workflow
- **Use for:** Planning, design, research, complex problem-solving
- **CASCADE:** Full workflow (PREFLIGHT → POSTFLIGHT)
- **Examples:** Claude, GPT-4 collaborating on feature design

### 🔧 Agent (Acting Intelligence)  
**Definition:** Focused executor of specific, well-defined tasks
- **Characteristics:** Task-focused, minimal dialogue, simplified CASCADE
- **Use for:** Implementation, testing, documentation, routine tasks
- **CASCADE:** ACT-focused (execute subtasks efficiently)
- **Examples:** Mini-agent implementing tests, code formatters

**Quick Rule:** Use AI for thinking/planning, Agent for execution.  
**See:** [`docs/AI_VS_AGENT_EMPIRICA_PATTERNS.md`](AI_VS_AGENT_EMPIRICA_PATTERNS.md) for detailed patterns.

---

## Choose Your Interface

Empirica works **four different ways** - pick what fits your workflow:

### 1. **CLI** (Command Line) - Start here!
```bash
empirica preflight "task"
empirica postflight <session>
```
**Best for:** Terminal workflows, scripts, quick tasks

### 2. **MCP Server** (IDE Integration)
Install and configure in your IDE (Claude Desktop, Cursor, Windsurf, Rovo Dev):
```bash
pip install empirica-mcp
```
```json
{
  "empirica": {
    "command": "empirica-mcp"
  }
}
```
**Best for:** Real-time epistemic tracking while coding

### 3. **Bootstraps** (Interactive Learning)
```bash
python3 empirica/bootstraps/optimal_metacognitive_bootstrap.py
```
**Best for:** Learning Empirica, practicing assessment

### 4. **Python API** (Programmatic)
```python
from empirica.core.canonical import CanonicalEpistemicAssessor
assessor = CanonicalEpistemicAssessor(agent_id="my-ai")
```
**Best for:** Custom integrations, automation

---

## MCP Tool Parameters Guide

When using Empirica via MCP (Model Context Protocol), avoid these common parameter errors:

### Critical Parameters (Most Common Issues)

```python
# ✅ Correct usage
create_goal(
    scope="project_wide",  # Must be enum: "task_specific" | "session_scoped" | "project_wide"
    success_criteria=["Tests pass", "Documentation updated"],  # Array, not string
    session_id="uuid"
)

add_subtask(
    goal_id="uuid",
    description="Write unit tests",
    importance="high",  # NOT "epistemic_importance"
    estimated_tokens=500
)

complete_subtask(
    task_id="uuid",  # NOT "subtask_id"
    evidence="Created 15 tests, all passing, 95% coverage"
)

submit_postflight_assessment(
    session_id="uuid",
    reasoning="Learned OAuth patterns, confidence improved from 0.6 to 0.9"  # NOT "changes"
)
```

### Common Errors to Avoid

| Function | Wrong ❌ | Correct ✅ |
|----------|----------|------------|
| `create_goal` | `scope="any text"` | `scope="project_wide"` (enum only) |
| `create_goal` | `success_criteria="Tests pass"` | `success_criteria=["Tests pass"]` (array) |
| `add_subtask` | `epistemic_importance="high"` | `importance="high"` |
| `complete_subtask` | `subtask_id="uuid"` | `task_id="uuid"` |
| `submit_postflight` | `changes="learned x,y"` | `reasoning="learned x,y"` |

**Tip:** Use IDE autocomplete or check the schema - parameter names matter!

---

## Next Steps

### For AI Agents:
📖 **Read:** [`docs/skills/SKILL.md`](skills/SKILL.md) - Complete guide for AI agents

### For Users:
📚 **Read:** [`docs/ONBOARDING_GUIDE.md`](ONBOARDING_GUIDE.md) - Complete learning path  
🎯 **Try:** [`docs/guides/TRY_EMPIRICA_NOW.md`](guides/TRY_EMPIRICA_NOW.md) - Hands-on demo  
📖 **Reference:** [`docs/production/README.md`](production/README.md) - 21 comprehensive guides  

### Need Help?
- **Installation issues:** [`docs/02_INSTALLATION.md`](02_INSTALLATION.md)
- **Troubleshooting:** [`docs/03_TROUBLESHOOTING.md`](03_TROUBLESHOOTING.md)

---

## The 4 Core Vectors (Quick Reference)

For most tasks, focus on these:

**KNOW** (0.0-1.0): Do I understand this domain?
- 0.8+ = Expert, 0.5-0.7 = Proficient, 0.3-0.5 = Novice

**DO** (0.0-1.0): Can I execute this task?
- 0.8+ = Confident, 0.5-0.7 = Capable with supervision, <0.5 = Need help

**CONTEXT** (0.0-1.0): Do I have enough information?
- 0.8+ = Complete, 0.5-0.7 = Sufficient, <0.5 = Risky to proceed

**UNCERTAINTY** (0.0-1.0): How uncertain am I?
- 0.8+ = Very uncertain (acknowledge unknowns!), <0.3 = Confident

**Optional 5th vector for unclear requests:**

**CLARITY** (0.0-1.0): Do I understand what's being asked?
- 0.8+ = Crystal clear, 0.5-0.7 = Clear enough, <0.5 = Ask for clarification
- Useful when: One-shot requests, unclear prompts, CLI workflows
- Low CLARITY → Ask user to clarify before proceeding

**Remember:** High uncertainty is GOOD when appropriate. Be honest!

---

## Core Principles

✅ **NO HEURISTICS** - Genuine self-assessment only  
✅ **BE HONEST** - Acknowledge what you don't know  
✅ **TRACK LEARNING** - Preflight → postflight shows growth  
✅ **VALIDATE CALIBRATION** - Were your predictions accurate?  

---

**Ready?** Run `empirica onboard` to begin! 🚀
