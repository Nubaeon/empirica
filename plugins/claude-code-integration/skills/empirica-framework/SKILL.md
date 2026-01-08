---
name: empirica-framework
description: "This skill should be used when the user asks to 'assess my knowledge state', 'run preflight', 'do a postflight', 'use CASCADE workflow', 'track what I know', 'measure learning', 'check epistemic drift', 'spawn investigation agents', 'create handoff', or mentions epistemic vectors, calibration, noetic/praxic phases, functional self-awareness, or structured investigation before coding tasks."
version: 1.3.0
---

# Empirica: Epistemic Framework for Claude Code

Measure what you know. Track what you learn. Prevent overconfidence.

## Two Axes: Workflow vs Thinking

### Workflow Phases (Mandatory)
```
PREFLIGHT ──► CHECK ──► POSTFLIGHT
    │           │            │
 Baseline    Sentinel     Learning
 Assessment    Gate        Delta
```

Every significant task MUST follow: **PREFLIGHT → CHECK → POSTFLIGHT**

### Thinking Phases (AI-Chosen)
```
NOETIC (High entropy)          PRAXIC (Low entropy)
──────────────────────        ─────────────────────
Investigate, explore,          Execute, write, commit,
hypothesize, search, read      deploy, test, implement
```

You CHOOSE when to use noetic vs praxic thinking. CHECK gates the transition.

## Bias Corrections

Apply these corrections to your self-assessments:
- **Uncertainty:** +0.10 (you underestimate doubt)
- **Knowledge:** -0.05 (you overestimate knowing)
- **Readiness gate:** know ≥0.70 AND uncertainty ≤0.35

## Quick Start: CASCADE Workflow

```bash
# 1. Create session
empirica session-create --ai-id claude-code --output json

# 2. Load project context
empirica project-bootstrap --session-id <ID> --output json

# 3. PREFLIGHT - Assess BEFORE starting
empirica preflight-submit - << 'EOF'
{
  "session_id": "<ID>",
  "task_context": "What you're about to do",
  "vectors": {
    "know": 0.6,
    "uncertainty": 0.4,
    "context": 0.7,
    "clarity": 0.8
  },
  "reasoning": "Honest assessment of current state"
}
EOF

# 4. Work (noetic or praxic as needed), logging breadcrumbs
empirica finding-log --session-id <ID> --finding "Key discovery" --impact 0.7
empirica unknown-log --session-id <ID> --unknown "Question that emerged"

# 5. CHECK - Sentinel gate (if uncertainty > 0.5 or scope > 0.6)
empirica check-submit - << 'EOF'
{
  "session_id": "<ID>",
  "task_context": "Ready to implement?",
  "vectors": {"know": 0.75, "uncertainty": 0.3, "context": 0.8, "clarity": 0.85},
  "findings": ["What you learned"],
  "unknowns": ["What's still unclear"],
  "reasoning": "Why you're ready (or not)"
}
EOF

# 6. POSTFLIGHT - Measure learning AFTER completion
empirica postflight-submit - << 'EOF'
{
  "session_id": "<ID>",
  "task_context": "What you completed",
  "vectors": {"know": 0.85, "uncertainty": 0.2, "context": 0.9, "clarity": 0.9},
  "reasoning": "Compare to PREFLIGHT - this is your learning delta"
}
EOF
```

## The 4 Core Vectors

Rate each 0.0 to 1.0 with honest reasoning:

| Vector | Question | Low (0.3) | High (0.8) |
|--------|----------|-----------|------------|
| **KNOW** | What do I understand? | New domain | Deep familiarity |
| **UNCERTAINTY** | How unsure am I? | Very uncertain | Confident |
| **CONTEXT** | Do I have enough info? | Missing key details | Full picture |
| **CLARITY** | Do I understand the ask? | Vague requirements | Crystal clear |

**Key principle:** Be ACCURATE, not optimistic. High uncertainty is valid data.

## Breadcrumb Commands

Log as you work - these link to your active goal automatically:

```bash
# Discoveries
empirica finding-log --session-id <ID> --finding "Auth uses JWT not sessions" --impact 0.7

# Questions that emerge
empirica unknown-log --session-id <ID> --unknown "How does rate limiting work here?"

# Dead ends (prevents repeating mistakes)
empirica deadend-log --session-id <ID> --approach "Tried monkey-patching" --why-failed "Breaks in prod"

# Resolve unknowns
empirica unknown-resolve --unknown-id <UUID> --resolved-by "Found in docs"
```

**Impact scale:** 0.1-0.3 trivial | 0.4-0.6 important | 0.7-0.9 critical | 1.0 transformative

## Epistemic Subagent Spawning

For parallel investigation, spawn epistemic subagents:

```bash
# Spawn investigation agent
empirica agent-spawn --session-id <ID> \
  --task "Investigate authentication patterns" \
  --persona researcher \
  --cascade-style exploratory

# Agent reports back with findings
empirica agent-report --agent-id <AGENT_ID> \
  --findings '["JWT used", "No refresh token mechanism"]' \
  --unknowns '["Where are tokens stored?"]' \
  --vectors '{"know": 0.7, "uncertainty": 0.3}'

# Aggregate all agent results
empirica agent-aggregate --session-id <ID>
```

## Goals and Subtasks

For complex work, create goals to track progress:

```bash
# Create goal
empirica goals-create --session-id <ID> --objective "Implement OAuth flow" \
  --scope-breadth 0.6 --scope-duration 0.5 --output json

# Add subtasks
empirica goals-add-subtask --goal-id <GOAL_ID> --description "Research OAuth providers"

# Complete subtasks with evidence
empirica goals-complete-subtask --subtask-id <TASK_ID> --evidence "commit abc123"

# Complete whole goal (triggers POSTFLIGHT options)
empirica goals-complete --goal-id <GOAL_ID> --reason "Implementation verified"

# Check progress
empirica goals-progress --goal-id <GOAL_ID>
```

**Note:** Subtasks use `--evidence`, goals use `--reason`.

## Handoff Types

Three types for preserving epistemic state:

| Type | When | Contains |
|------|------|----------|
| **Investigation** | After CHECK | Noetic findings, ready for praxic |
| **Complete** | After POSTFLIGHT | Full learning cycle + calibration |
| **Planning** | Any time | Documentation-only, no CASCADE required |

```bash
# Investigation handoff (noetic → praxic transition)
empirica handoff-create --session-id <ID> \
  --task-summary "Investigated auth patterns" \
  --key-findings '["JWT with RS256", "Refresh in httpOnly cookies"]' \
  --next-session-context "Ready to implement token rotation"

# Query existing handoffs
empirica handoff-query --session-id <ID> --output json
```

## Semantic Search Triggers

Use project search during noetic phases:

1. **Session start** - Search task context for prior learnings
2. **Before logging unknown** - Check if similar unknown was resolved
3. **Pre-CHECK** - Find similar decision patterns
4. **Pre-self-improvement** - Check for conflicting guidance

```bash
empirica project-search --project-id <ID> --task "authentication patterns"
```

## When to Use CHECK

Run CHECK gate when:
- Uncertainty > 0.5 (too uncertain to proceed safely)
- Scope > 0.6 (high-impact changes)
- Post-compact (context was just reduced)
- Before irreversible actions

CHECK returns `proceed` or `investigate` based on your vectors.

## Calibration: The Learning Loop

The power of Empirica is in the **delta**:

```
PREFLIGHT: know=0.5, uncertainty=0.6
   ... do work ...
POSTFLIGHT: know=0.8, uncertainty=0.2

Learning delta: +0.3 know, -0.4 uncertainty
```

Over time, calibration reports show if you're:
- **Overconfident:** Predicted high, actual lower
- **Underconfident:** Predicted low, actual higher
- **Well-calibrated:** Predictions match outcomes

## Common Patterns

### Pattern 1: Quick Task
```
PREFLIGHT → [praxic work] → POSTFLIGHT
```

### Pattern 2: Investigation
```
PREFLIGHT → [noetic: explore] → CHECK → [praxic: implement] → POSTFLIGHT
```

### Pattern 3: Complex Feature
```
PREFLIGHT → Goal + Subtasks → [CHECK at each gate] → POSTFLIGHT
```

### Pattern 4: Parallel Investigation
```
PREFLIGHT → agent-spawn (×3) → agent-aggregate → CHECK → POSTFLIGHT
```

## Integration with Hooks

This plugin includes automatic hooks that enforce the CASCADE workflow:

- **PreToolCall** (`sentinel-gate.py`): Gates Edit/Write/Bash until valid CHECK exists (<30min old)
- **SessionStart:new** (`session-init.py`): Auto-creates session + bootstrap, prompts for PREFLIGHT
- **SessionStart:compact** (`post-compact.py`): Auto-recovers session + bootstrap, prompts for CHECK
- **SessionEnd** (`session-end-postflight.py`): Auto-captures POSTFLIGHT with final vectors

**MCP integration:** Set `EMPIRICA_EPISTEMIC_MODE=true` to enable VectorRouter (routes based on vectors).

These run automatically - the workflow is enforced, not just suggested.

## Key Commands Reference

```bash
empirica --help                          # All commands
empirica session-create --ai-id <name>   # Start session
empirica project-bootstrap --session-id <ID>  # Load context
empirica preflight-submit -              # PREFLIGHT (stdin JSON)
empirica check-submit -                  # CHECK gate (stdin JSON)
empirica postflight-submit -             # POSTFLIGHT (stdin JSON)
empirica finding-log --finding "..."     # Log discovery
empirica unknown-log --unknown "..."     # Log question
empirica goals-list                      # Show active goals
empirica check-drift --session-id <ID>   # Detect drift
empirica agent-spawn --task "..."        # Spawn subagent
empirica handoff-create ...              # Create handoff
```

## Best Practices

**DO:**
- Apply bias corrections (+0.10 uncertainty)
- Be honest about uncertainty (it's data, not failure)
- Log findings as you discover them
- Use CHECK before major actions
- Compare POSTFLIGHT to PREFLIGHT
- Spawn subagents for parallel investigation

**DON'T:**
- Inflate scores to "look good"
- Skip PREFLIGHT (you lose calibration baseline)
- Ignore high uncertainty signals
- Forget to log what you learned
- Proceed without CHECK when uncertainty > 0.5

## More Information

See [references/cascade-workflow.md](references/cascade-workflow.md) for detailed CASCADE phases.
See [references/vector-guide.md](references/vector-guide.md) for the full 13-vector system.
See [references/calibration-patterns.md](references/calibration-patterns.md) for calibration examples.

---

**Remember:** When uncertain, say so. That's genuine metacognition.
