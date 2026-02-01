---
name: empirica-framework
description: "This skill should be used when the user asks to 'assess my knowledge state', 'run preflight', 'do a postflight', 'use CASCADE workflow', 'track what I know', 'measure learning', 'check epistemic drift', 'spawn investigation agents', 'create handoff', or mentions epistemic vectors, calibration, noetic/praxic phases, functional self-awareness, or structured investigation before coding tasks."
version: 2.1.0
---

# Empirica: Epistemic Framework Reference

Measure what you know. Track what you learn. Prevent overconfidence.

**v2.1.0:** Dual-track calibration (grounded verification), 4-phase CASCADE with POST-TEST.
See CLAUDE.md for canonical terms (noetic/praxic/epistemic/context).

---

## CASCADE Workflow

Every significant task follows: **PREFLIGHT → CHECK → POSTFLIGHT → POST-TEST**

```
PREFLIGHT ──► CHECK ──► POSTFLIGHT ──► POST-TEST
    │           │            │              │
 Baseline    Sentinel     Learning      Grounded
 Assessment    Gate        Delta       Verification
```

### PREFLIGHT (Measure baseline)

Submit your honest epistemic state BEFORE starting work:

```bash
empirica preflight-submit - << 'EOF'
{
  "session_id": "<ID>",
  "task_context": "What you're about to do",
  "vectors": {
    "know": 0.6, "uncertainty": 0.4,
    "context": 0.7, "clarity": 0.8
  },
  "reasoning": "Honest assessment of current state"
}
EOF
```

### CHECK (Sentinel gate)

Submit when ready to transition from noetic to praxic:

```bash
empirica check-submit - << 'EOF'
{
  "session_id": "<ID>",
  "vectors": {
    "know": 0.75, "uncertainty": 0.3,
    "context": 0.8, "clarity": 0.85
  },
  "reasoning": "Why ready (or not)"
}
EOF
```

Returns `proceed` or `investigate` based on readiness gate: `know >= 0.70 AND uncertainty <= 0.35` (after bias correction).

**When to CHECK:**
- Uncertainty > 0.5 (too uncertain)
- Scope > 0.6 (high-impact changes)
- Post-compact (context reduced)
- Before irreversible actions

### POSTFLIGHT (Measure delta + trigger grounded verification)

Submit AFTER completing work — the delta between PREFLIGHT and POSTFLIGHT is your learning measurement:

```bash
empirica postflight-submit - << 'EOF'
{
  "session_id": "<ID>",
  "vectors": {
    "know": 0.85, "uncertainty": 0.2,
    "context": 0.9, "clarity": 0.9
  },
  "reasoning": "Compare to PREFLIGHT - this is your learning delta"
}
EOF
```

**POST-TEST (automatic):** POSTFLIGHT automatically triggers grounded verification —
objective evidence (tests, artifacts, git, goals) is collected and compared to your
self-assessed vectors. The gap = real calibration error. See [Dual-Track Calibration](#dual-track-calibration).

---

## The 13 Epistemic Vectors

Rate each 0.0 to 1.0 with honest reasoning:

### Foundation
| Vector | Question |
|--------|----------|
| **engagement** | How invested am I in this task? |
| **know** | What do I understand about the domain? |
| **do** | Can I execute the required actions? |
| **context** | Do I have enough surrounding information? |

### Comprehension
| Vector | Question |
|--------|----------|
| **clarity** | Do I understand what's being asked? |
| **coherence** | Does my understanding fit together? |
| **signal** | Am I detecting relevant patterns? |
| **density** | How information-rich is my current state? |

### Execution
| Vector | Question |
|--------|----------|
| **state** | Do I understand the current system state? |
| **change** | How much has changed since I last assessed? |
| **completion** | How complete is this phase? (phase-aware) |
| **impact** | How significant is this work? |

### Meta
| Vector | Question |
|--------|----------|
| **uncertainty** | How unsure am I? (higher = more uncertain) |

**Key principle:** Be ACCURATE, not optimistic. High uncertainty is valid data.

---

## Dual-Track Calibration

Empirica uses two parallel calibration tracks:

### Track 1: Self-Referential (PREFLIGHT → POSTFLIGHT)

Measures **learning trajectory** — how vectors change during work.
Updated automatically on each POSTFLIGHT via Bayesian update.

*Example bias corrections (exact values injected from `.breadcrumbs.yaml`):*
- **Completion:** ~+0.52 (underestimate progress)
- **Impact:** ~+0.29 (underestimate significance)
- **Density/Signal/Change:** ~+0.10 to +0.13

### Track 2: Grounded Verification (POSTFLIGHT → Objective Evidence)

Measures **calibration accuracy** — does your self-assessment match reality?
Triggered automatically after each POSTFLIGHT.

**Evidence sources (collected automatically):**

| Source | Quality | Vectors Grounded |
|--------|---------|-----------------|
| pytest results | OBJECTIVE | know, do, clarity |
| Git metrics | OBJECTIVE | do, change, state |
| Goal completion | SEMI_OBJECTIVE | completion, do, know |
| Artifact counts | SEMI_OBJECTIVE | know, uncertainty, signal |
| Issue tracking | SEMI_OBJECTIVE | impact, signal |
| Sentinel decisions | SEMI_OBJECTIVE | context, uncertainty |

**Ungroundable vectors:** engagement, coherence, density — no objective signal exists.

**When tracks disagree:** Track 2 (grounded) is more trustworthy. The `grounded_calibration.divergence`
section in `.breadcrumbs.yaml` shows the gap per vector.

```bash
# Self-referential calibration (Track 1)
empirica calibration-report

# Grounded calibration (Track 2) — compare self-assessment vs evidence
empirica calibration-report --grounded

# Trajectory — is calibration improving over time?
empirica calibration-report --trajectory
```

*Exact values injected from `.breadcrumbs.yaml` at session start.*

---

## Noetic Artifacts (Breadcrumbs)

Log as you work — these link to your active goal automatically:

```bash
# Findings — what was learned
empirica finding-log --session-id <ID> --finding "Auth uses JWT not sessions" --impact 0.7

# Unknowns — what remains unclear
empirica unknown-log --session-id <ID> --unknown "How does rate limiting work here?"

# Dead-ends — approaches that failed (prevents re-exploration)
empirica deadend-log --session-id <ID> --approach "Tried monkey-patching" --why-failed "Breaks in prod"

# Resolve unknowns when answered
empirica unknown-resolve --unknown-id <UUID> --resolved-by "Found in docs"
```

**Impact scale:** 0.1–0.3 trivial | 0.4–0.6 important | 0.7–0.9 critical | 1.0 transformative

---

## Praxic Artifacts (Goals + Subtasks)

For complex work, create goals to track progress:

```bash
# Create goal
empirica goals-create --session-id <ID> --objective "Implement OAuth flow" \
  --scope-breadth 0.6 --scope-duration 0.5 --output json

# Add subtasks
empirica goals-add-subtask --goal-id <GOAL_ID> --description "Research OAuth providers"

# Complete subtasks with evidence
empirica goals-complete-subtask --subtask-id <TASK_ID> --evidence "commit abc123"

# Complete whole goal
empirica goals-complete --goal-id <GOAL_ID> --reason "Implementation verified"

# Check progress
empirica goals-progress --goal-id <GOAL_ID>
```

**Note:** Subtasks use `--evidence`, goals use `--reason`.

---

## Memory Operations

### Semantic Search (Qdrant)

```bash
# Focused search (eidetic facts + episodic arcs)
empirica project-search --project-id <ID> --task "authentication patterns"

# Full search (all 4 collections: docs, memory, eidetic, episodic)
empirica project-search --project-id <ID> --task "query" --type all

# Include cross-project learnings (ecosystem scope)
empirica project-search --project-id <ID> --task "query" --global

# Sync project memory to Qdrant
empirica project-embed --project-id <ID> --output json
```

**Automatic ingestion (when Qdrant available):**
- `finding-log` → eidetic facts + immune decay on lessons
- `postflight-submit` → episodic narratives + auto-embed + **grounded verification** (post-test evidence)
- `SessionStart` hook → retrieves relevant memories post-compact

**Pattern retrieval (auto-triggered):**
- **PREFLIGHT:** Returns lessons, dead-ends, relevant findings
- **CHECK:** Validates against dead-ends, triggers mistake risk warnings

**Optional setup:** `export EMPIRICA_QDRANT_URL="http://localhost:6333"`

Empirica works fully without Qdrant — core CASCADE, goals, and calibration use SQLite.

### Search Triggers

Use project search during noetic phases:
1. Session start — prior learnings for current task
2. Before logging unknown — check if already resolved
3. Pre-CHECK — similar decision patterns
4. Pre-self-improvement — conflicting guidance

---

## Multi-Agent Operations

### Spawn Investigation Agents

```bash
# Single agent
empirica agent-spawn --session-id <ID> \
  --task "Investigate authentication patterns" \
  --persona researcher --cascade-style exploratory

# Parallel agents with attention budget
empirica agent-parallel --session-id <ID> \
  --task "Analyze security and architecture" \
  --budget 20 --max-agents 5
```

Budget allocates by information gain: high-uncertainty domains get more resources.
SubagentStop hook auto-gates rollup: scores by confidence x novelty x relevance.

### Handoff Types

| Type | When | Contains |
|------|------|----------|
| **Investigation** | After CHECK | Noetic artifacts, ready for praxic |
| **Complete** | After POSTFLIGHT | Full learning cycle + calibration |
| **Planning** | Any time | Documentation-only, no CASCADE required |

```bash
empirica handoff-create --session-id <ID> \
  --task-summary "Investigated auth patterns" \
  --key-findings '["JWT with RS256", "Refresh in httpOnly cookies"]' \
  --next-session-context "Ready to implement token rotation"
```

---

## Sentinel Safety Gates

Sentinel controls praxic actions (Edit, Write, NotebookEdit):

**Readiness gate:** `know >= 0.70 AND uncertainty <= 0.35` (after bias correction)

**Core features (always on):**
- PREFLIGHT requirement before acting
- Decision parsing (blocks if CHECK returned "investigate")
- Vector threshold validation
- Anti-gaming: minimum noetic duration (30s) with evidence check

**Anti-gaming:** If CHECK submitted <30s after PREFLIGHT AND no noetic artifacts logged → blocked with "Rushed assessment. Investigate and log learnings first."

**Configuration:**
```bash
export EMPIRICA_MIN_NOETIC_DURATION=60       # Adjust min noetic duration
export EMPIRICA_SENTINEL_LOOPING=false        # Disable investigate loops
export EMPIRICA_SENTINEL_MODE=observer        # Log-only (no blocking)
export EMPIRICA_SENTINEL_MODE=controller      # Active blocking (default)
export EMPIRICA_SENTINEL_CHECK_EXPIRY=true    # 30-min CHECK expiry
export EMPIRICA_SENTINEL_REQUIRE_BOOTSTRAP=true
```

---

## Common Patterns

### Quick Task
```
PREFLIGHT → [praxic work] → POSTFLIGHT → POST-TEST
```

### Investigation → Implementation
```
PREFLIGHT → [noetic: explore] → CHECK → [praxic: implement] → POSTFLIGHT → POST-TEST
```

### Complex Feature
```
PREFLIGHT → Goal + Subtasks → [CHECK at each gate] → POSTFLIGHT → POST-TEST
```

### Parallel Investigation
```
PREFLIGHT → agent-spawn (×N) → agent-aggregate → CHECK → POSTFLIGHT → POST-TEST
```

POST-TEST is automatic — triggered by POSTFLIGHT. No manual step needed.

---

## Hook Integration

Hooks enforce CASCADE automatically:

| Hook | Event | Action |
|------|-------|--------|
| `sentinel-gate.py` | PreToolUse | Gates Edit/Write until valid CHECK |
| `session-init.py` | SessionStart:new | Auto-creates session + bootstrap |
| `post-compact.py` | SessionStart:compact | Auto-recovers session, prompts CHECK |
| `session-end-postflight.py` | SessionEnd | Auto-captures POSTFLIGHT |
| `tool-router.py` | UserPromptSubmit | Vector-aware tool/agent routing |

**MCP Server Restart:** After updating empirica-mcp code, restart the server:
```bash
pkill -f empirica-mcp  # Kill running server
# Then use /mcp in Claude Code to reconnect
```

---

## Full Command Reference

```bash
empirica --help                          # All commands
empirica session-create --ai-id <name>   # Start session
empirica project-bootstrap --session-id <ID>  # Load context
empirica preflight-submit -              # PREFLIGHT (stdin JSON)
empirica check-submit -                  # CHECK gate (stdin JSON)
empirica postflight-submit -             # POSTFLIGHT (stdin JSON)
empirica finding-log --finding "..."     # Log noetic artifact (finding)
empirica unknown-log --unknown "..."     # Log noetic artifact (unknown)
empirica deadend-log --approach "..."    # Log noetic artifact (dead-end)
empirica goals-create --objective "..."  # Create praxic artifact (goal)
empirica goals-list                      # Show active goals
empirica check-drift --session-id <ID>   # Detect epistemic drift
empirica calibration-report              # Self-referential calibration (Track 1)
empirica calibration-report --grounded   # Grounded calibration (Track 2)
empirica calibration-report --trajectory # Calibration trend over time
empirica agent-spawn --task "..."        # Spawn domain agent
empirica agent-parallel --task "..."     # Parallel investigation
empirica handoff-create ...              # Create handoff
empirica project-search --task "..."     # Semantic memory search
```

---

## Best Practices

**DO:**
- Apply bias corrections from `.breadcrumbs.yaml` (both self-ref and grounded)
- Be honest about uncertainty (it's data, not failure)
- Log noetic artifacts as you discover them (also anti-gaming evidence)
- Use CHECK before major praxic actions
- Compare POSTFLIGHT to PREFLIGHT (Track 1: learning delta)
- Check `calibration-report --grounded` to see if self-assessment matches evidence (Track 2)
- Use `calibration-report --trajectory` to see if calibration is improving

**DON'T:**
- Inflate scores (Sentinel detects rushed assessments)
- Skip PREFLIGHT (lose baseline AND get blocked)
- Ignore high uncertainty signals
- Proceed without CHECK when uncertainty > 0.5
- Rush PREFLIGHT→CHECK without actual noetic work
- Trust Track 1 over Track 2 when they diverge (grounded evidence wins)

---

**Remember:** When uncertain, say so. That's genuine metacognition.
