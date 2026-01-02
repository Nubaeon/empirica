---
name: empirica-framework
description: Empirica epistemic workflow - creates goals, submits findings/unknowns, manages sessions, runs CASCADE phases (PREFLIGHT/CHECK/POSTFLIGHT). Use when working with epistemic assessments, goals, findings, or session management.
allowed-tools: Bash(empirica:*),Read,Grep,Glob
---

# Empirica Framework Skill

## Overview

Empirica provides epistemic self-awareness for AI agents through vector-based assessments and structured workflows.

## Quick Reference

### Session Setup
```bash
empirica session-create --ai-id claude-code --output json
empirica project-bootstrap --session-id <ID> --output json
```

### CASCADE Workflow (per-goal)
```bash
# 1. PREFLIGHT - baseline assessment
empirica preflight-submit - << 'EOF'
{
  "session_id": "<ID>",
  "vectors": {"know": 0.5, "uncertainty": 0.6, "context": 0.4, ...},
  "reasoning": "Initial assessment before task"
}
EOF

# 2. CHECK - gate decision (auto-computed from vectors)
empirica check-submit - << 'EOF'
{
  "session_id": "<ID>",
  "vectors": {"know": 0.75, "uncertainty": 0.25, ...},
  "reasoning": "Post-investigation assessment"
}
EOF
# Returns: decision (proceed/investigate), metacog section with gate status

# 3. POSTFLIGHT - learning delta
empirica postflight-submit - << 'EOF'
{
  "session_id": "<ID>",
  "vectors": {"know": 0.85, "uncertainty": 0.15, "completion": 1.0, ...},
  "reasoning": "Task complete, measured learning"
}
EOF
```

### Epistemic Breadcrumbs
```bash
empirica finding-log --session-id <ID> --finding "What was learned" --impact 0.7
empirica unknown-log --session-id <ID> --unknown "What remains unclear"
empirica deadend-log --session-id <ID> --approach "What was tried" --why-failed "Why it failed"
empirica unknown-resolve --unknown-id <UUID> --resolved-by "How resolved"
```

**Impact scale:** 0.1-0.3 trivial | 0.4-0.6 important | 0.7-0.9 critical | 1.0 transformative

### Goal Management
```bash
empirica goals-create - << 'EOF'
{
  "session_id": "<ID>",
  "objective": "What to achieve",
  "scope": {"breadth": 0.3, "duration": 0.2, "coordination": 0.1}
}
EOF

empirica goals-add-subtask --goal-id <UUID> --description "Subtask" --output json
empirica goals-complete-subtask --task-id <UUID> --evidence "Done" --output json
empirica goals-list --output json
empirica goals-progress --goal-id <UUID> --output json
```

### Agent Spawning
```bash
# Spawn with persona
empirica agent-spawn --session-id <ID> --task "Task" --persona researcher

# Auto-select best emerged persona (turtle mode)
empirica agent-spawn --session-id <ID> --task "Task" --turtle
```

### Drift Detection
```bash
empirica check-drift --session-id <ID> --output json
```

## 13 Epistemic Vectors

| Category | Vectors |
|----------|---------|
| Foundation | engagement, know, do, context |
| Comprehension | clarity, coherence, signal, density |
| Execution | state, change, completion, impact |
| Meta | uncertainty |

**Readiness gate:** know >= 0.70 AND uncertainty <= 0.35 (after bias correction)

## Bias Corrections

Apply when self-assessing:
- completion: +0.54 (you underestimate progress)
- change: +0.31 (you underestimate change impact)
- uncertainty: -0.19 (you overestimate uncertainty)
- know: +0.17 (you underestimate knowledge)

## Workflow Pattern

```
Per Goal:
  PREFLIGHT (baseline)
      ↓
  NOETIC (investigate until ready)
      ↓
  CHECK (gate: proceed or investigate?)
      ↓
  PRAXIC (execute)
      ↓
  POSTFLIGHT (measure learning)
      ↓
  COMMIT (persist changes)
```

**One goal = one epistemic loop.** Do not batch.
