# Git Checkpoint Architecture - How It Maps to CASCADE

## TL;DR

**Git checkpoints are SEPARATE from PREFLIGHT/CHECK/POSTFLIGHT** - they are manual snapshots you create during the CASCADE workflow.

## Architecture Overview

```
CASCADE Phases          Git Storage          CLI Commands
─────────────────────────────────────────────────────────────
PREFLIGHT              SQLite + JSON        empirica preflight
  ↓                        ↓                 empirica preflight-submit
  ├─> Vectors stored   sessions.db          
  └─> Optional git     git notes            empirica checkpoint-create --phase=PREFLIGHT
      checkpoint       (compressed)
  
INVESTIGATE            JSON logs            (no CLI command - manual work)
  ↓                        ↓
  └─> Optional git     git notes            empirica checkpoint-create --phase=INVESTIGATE
      checkpoint       (compressed)
  
CHECK                  SQLite + JSON        empirica check
  ↓                        ↓                 empirica check-submit
  ├─> Decision stored  sessions.db
  └─> Optional git     git notes            empirica checkpoint-create --phase=CHECK
      checkpoint       (compressed)
  
ACT                    JSON logs            (no CLI command - actual work)
  ↓                        ↓
  └─> Optional git     git notes            empirica checkpoint-create --phase=ACT
      checkpoint       (compressed)
  
POSTFLIGHT             SQLite + JSON        empirica postflight
  ↓                        ↓                 empirica postflight-submit
  ├─> Vectors stored   sessions.db
  ├─> Deltas computed  (PREFLIGHT vs POSTFLIGHT)
  └─> Optional git     git notes            empirica checkpoint-create --phase=POSTFLIGHT
      checkpoint       (compressed)
```

## Three Storage Layers

### 1. SQLite Database (`.empirica/sessions/sessions.db`)
**Purpose:** Session metadata and epistemic state  
**Stores:**
- Session creation (`ai_id`, `session_id`, `bootstrap_level`)
- PREFLIGHT vectors (13 epistemic dimensions)
- CHECK decisions (`proceed` / `investigate`)
- POSTFLIGHT vectors (13 epistemic dimensions)
- Calibration deltas (PREFLIGHT → POSTFLIGHT)

**Written by:**
- `empirica preflight-submit`
- `empirica check-submit`
- `empirica postflight-submit`

### 2. JSON Logs (`.empirica_reflex_logs/`)
**Purpose:** Detailed workflow logs and history  
**Stores:**
- Full assessment objects
- Timestamps and workflow progression
- Investigation findings
- Human-readable logs

**Written by:**
- All CASCADE commands
- Reflex logger (automatic)

### 3. Git Notes (Compressed Checkpoints)
**Purpose:** 97.5% token-reduced resumption points  
**Stores:**
- Compressed epistemic state snapshots
- Phase + round number
- Essential vectors only
- Metadata (progress, notes)

**Written by:**
- `empirica checkpoint-create` (MANUAL)
- NOT automatic - you must call it explicitly

## Key Insight: Checkpoints Are Optional

```python
# PREFLIGHT is automatic (stores to SQLite + JSON)
empirica preflight "Task description" --ai-id claude-code

# Checkpoint is OPTIONAL (stores to git notes)
empirica checkpoint-create --session-id latest:active:claude-code \
    --phase PREFLIGHT --round 1 --metadata '{"note": "Initial assessment"}'
```

## When to Create Git Checkpoints

✅ **Create checkpoints when:**
- Long-running tasks (>30 min)
- Before context window might fill up
- Natural breakpoints in workflow
- Before risky operations
- End of session for resumption

❌ **Don't create checkpoints when:**
- Simple tasks (<10 min)
- Already at end of session
- No risk of interruption

## MCP Tool Mapping

### MCP Tools → CLI Commands

```json
{
  "bootstrap_session": "empirica bootstrap --ai-id X",
  "execute_preflight": "empirica preflight 'task' --prompt-only",
  "submit_preflight_assessment": "empirica preflight-submit --session-id X --vectors {}",
  "execute_check": "empirica check --session-id X",
  "submit_check_assessment": "empirica check-submit --session-id X --decision proceed",
  "execute_postflight": "empirica postflight X --prompt-only",
  "submit_postflight_assessment": "empirica postflight-submit --session-id X --vectors {}",
  "create_git_checkpoint": "empirica checkpoint-create --session-id X --phase ACT",
  "load_git_checkpoint": "empirica checkpoint-load X"
}
```

### Stateless vs Stateful

**Stateless (handled in MCP):**
- `get_empirica_introduction()` - Returns markdown intro
- `get_workflow_guidance()` - Returns phase guidance
- `cli_help()` - Returns CLI help text

**Stateful (routed to CLI):**
- All workflow commands (preflight, check, postflight)
- All goal/task commands
- All checkpoint commands
- All session commands

## The --ai-id Fix Impact

### Before Fix
```bash
# Session created with session_id as ai_id (confusing!)
empirica preflight "task"
# → Creates session with ai_id = <random-uuid>
```

### After Fix
```bash
# Session created with specified ai_id (correct!)
empirica preflight "task" --ai-id claude-code
# → Creates session with ai_id = "claude-code"

# Default still works (backward compatible)
empirica preflight "task"
# → Creates session with ai_id = "empirica_cli"
```

### Why This Matters

**Multi-AI tracking:**
```sql
-- Before: All sessions had random UUIDs as ai_id
SELECT ai_id, session_id FROM sessions;
-- 88dbf132-cc7c-4a4b-9b59-77df3b13dbd2 | abc123
-- a89b9d94-d907-4a95-ab8d-df8824990bec | def456

-- After: Sessions grouped by AI agent
SELECT ai_id, session_id FROM sessions;
-- claude-code    | abc123
-- mini-agent     | def456
-- gemini-flash   | ghi789
```

**Resume by AI:**
```bash
# Find last session for specific AI
empirica sessions-resume --ai-id claude-code --count 1

# Use alias for commands
empirica checkpoint-load latest:active:claude-code
```

## Complete Workflow Example

```bash
# 1. Bootstrap session (creates in SQLite)
empirica bootstrap --ai-id mini-agent --level 2

# 2. PREFLIGHT (stores to SQLite + JSON)
empirica preflight "Implement feature X" --ai-id mini-agent --session-id latest:active:mini-agent
empirica preflight-submit --session-id latest:active:mini-agent \
    --vectors '{"engagement": 0.8, "know": 0.4, ...}'

# 3. OPTIONAL: Create git checkpoint
empirica checkpoint-create --session-id latest:active:mini-agent \
    --phase PREFLIGHT --round 1

# 4. INVESTIGATE (manual work - logs to JSON)
# ... research, code exploration, etc ...

# 5. OPTIONAL: Create git checkpoint after investigation
empirica checkpoint-create --session-id latest:active:mini-agent \
    --phase INVESTIGATE --round 1 --metadata '{"findings": "3 key insights"}'

# 6. CHECK (stores to SQLite + JSON)
empirica check --session-id latest:active:mini-agent
empirica check-submit --session-id latest:active:mini-agent \
    --decision proceed --vectors '{...}'

# 7. ACT (manual work - logs to JSON)
# ... implement the feature ...

# 8. OPTIONAL: Create git checkpoint during ACT
empirica checkpoint-create --session-id latest:active:mini-agent \
    --phase ACT --round 1 --metadata '{"progress": "50%"}'

# 9. POSTFLIGHT (stores to SQLite + JSON, computes deltas)
empirica postflight latest:active:mini-agent
empirica postflight-submit --session-id latest:active:mini-agent \
    --vectors '{"engagement": 0.9, "know": 0.8, ...}'

# 10. OPTIONAL: Final checkpoint
empirica checkpoint-create --session-id latest:active:mini-agent \
    --phase POSTFLIGHT --round 1
```

## Resumption Flow

```bash
# Session interrupted? Resume from checkpoint:

# 1. Load last checkpoint (from git notes)
empirica checkpoint-load latest:active:mini-agent
# → Returns: last phase, round, vectors, metadata

# 2. Query session state (from SQLite)
empirica sessions-show latest:active:mini-agent
# → Returns: full session history, all assessments

# 3. Resume workflow from where you left off
empirica check --session-id latest:active:mini-agent
```

## Token Savings

### Without Git Checkpoints
- Full session context: ~50,000 tokens
- All logs, all history, all assessments

### With Git Checkpoints
- Compressed checkpoint: ~1,250 tokens (97.5% reduction!)
- Essential state only
- Reconstruct full context on-demand from SQLite/JSON

## Summary

| Feature | Storage | Automatic? | CLI Command |
|---------|---------|------------|-------------|
| **PREFLIGHT vectors** | SQLite + JSON | ✅ Yes | `preflight-submit` |
| **CHECK decision** | SQLite + JSON | ✅ Yes | `check-submit` |
| **POSTFLIGHT vectors** | SQLite + JSON | ✅ Yes | `postflight-submit` |
| **Calibration deltas** | SQLite | ✅ Yes | (computed automatically) |
| **Git checkpoints** | git notes | ❌ No | `checkpoint-create` (manual) |
| **Reflex logs** | JSON | ✅ Yes | (automatic) |

**Key Takeaway:** Git checkpoints are an OPTIONAL optimization for long-running sessions, not a required part of CASCADE workflow. Use them when you need efficient resumption or context management.

---

**Updated:** 2025-11-27  
**Status:** Accurate post-fix analysis
