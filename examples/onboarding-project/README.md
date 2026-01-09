# Empirica Onboarding - Choose Your Adventure

Welcome to Empirica! Pick a mini-project that matches your interest.

## Why Multiple Projects?

Empirica shines when there's **genuine uncertainty** - when you don't know the answer upfront and must investigate. Each project is designed to give you a real epistemic journey where your confidence naturally changes.

## Choose Your Project

| Project | Difficulty | Time | Best For |
|---------|------------|------|----------|
| [Bug Hunt](projects/bug-hunt/) | ⭐⭐ | 20 min | Debugging, investigation |
| [Code Archaeology](projects/code-archaeology/) | ⭐⭐⭐ | 30 min | Understanding unfamiliar code |
| [API Explorer](projects/api-explorer/) | ⭐⭐ | 25 min | Learning new APIs |
| [Refactor Decision](projects/refactor-decision/) | ⭐⭐⭐ | 30 min | Architecture decisions |

## What You'll Learn

All projects teach the same Empirica workflow:

1. **PREFLIGHT** - Honest baseline: "What do I actually know?"
2. **Breadcrumbs** - Log findings, unknowns, dead-ends as you work
3. **CHECK** - Gate decisions with confidence vectors
4. **POSTFLIGHT** - Measure your learning delta

## Quick Start

```bash
# 1. Install Empirica
pip install empirica

# 2. Create session
empirica session-create --ai-id claude-code --output json

# 3. Pick a project and follow its WALKTHROUGH.md
cd examples/onboarding-project/projects/bug-hunt/
cat WALKTHROUGH.md
```

## The Epistemic Payoff

After completing any project, you'll have:
- A recorded learning journey with confidence progression
- Findings you can search later (`empirica project-search`)
- Dead-ends that prevent future mistakes
- Calibration data showing how accurate your self-assessments were

---

**Tip:** Start with Bug Hunt if you're new. It's the most intuitive demonstration of epistemic tracking.
