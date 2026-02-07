# CASCADE Workflow API Reference

**Version:** 1.5.0
**Purpose:** Epistemic measurement phases for AI self-assessment and grounded calibration

---

## Overview

The CASCADE workflow defines the epistemic measurement phases that track AI knowledge state across work cycles:

```
PREFLIGHT ──► CHECK ──► POSTFLIGHT ──► POST-TEST
    │           │            │              │
 Baseline    Sentinel     Learning      Grounded
 Assessment    Gate        Delta       Verification
```

**Key concept:** The PREFLIGHT → POSTFLIGHT cycle is a **measurement window** (epistemic transaction), not a goal boundary. Between measurements, epistemic state is wave-like (continuous). PREFLIGHT/POSTFLIGHT collapse it to particles (discrete vectors).

---

## Transaction-First Architecture

After PREFLIGHT, most commands auto-derive `--session-id` from the active transaction. The CLI uses `get_active_empirica_session_id()` with priority:

1. Active transaction (`active_transaction_*.json`)
2. active_work file
3. instance_projects file

**File tracking:**
- `{project}/.empirica/active_transaction_{suffix}.json` — Transaction state (survives compaction)
- `~/.empirica/active_work_{claude_session_id}.json` — Session context

---

## Epistemic Vectors

All CASCADE commands accept these vectors (0.0-1.0):

| Vector | Description | Typical Range |
|--------|-------------|---------------|
| `know` | Confidence in current knowledge | 0.4-0.9 |
| `uncertainty` | Epistemic uncertainty level | 0.1-0.6 |
| `do` | Ability to execute the task | 0.3-0.9 |
| `completion` | Progress toward goal (phase-aware) | 0.0-1.0 |
| `context` | Understanding of current situation | 0.5-0.95 |
| `clarity` | Clarity of requirements | 0.5-0.9 |
| `impact` | Expected impact of work | 0.3-0.9 |
| `change` | Magnitude of changes made | 0.0-0.8 |
| `state` | Codebase state understanding | 0.5-0.9 |
| `density` | Information density of session | 0.3-0.8 |
| `signal` | Signal-to-noise ratio | 0.4-0.9 |
| `coherence` | Logical consistency | 0.6-0.95 |
| `engagement` | Task engagement level | 0.5-0.9 |

**Readiness gate:** `know >= 0.70 AND uncertainty <= 0.35`

---

## Commands

### `preflight-submit`

Submit baseline epistemic assessment before work begins. Opens an epistemic transaction.

**CLI Usage:**
```bash
# AI-first mode (recommended)
empirica preflight-submit - << 'EOF'
{
  "session_id": "auto",
  "task_description": "Implement user authentication",
  "vectors": {
    "know": 0.6,
    "uncertainty": 0.4,
    "do": 0.3,
    "completion": 0.0,
    "context": 0.7
  },
  "reasoning": "Familiar with auth patterns but need to investigate this codebase"
}
EOF

# Legacy flag mode
empirica preflight-submit \
  --session-id <ID> \
  --vectors '{"know": 0.6, "uncertainty": 0.4}' \
  --reasoning "..."
```

**Input Schema:**
```json
{
  "session_id": "string (UUID or 'auto')",
  "task_description": "string (what you intend to do)",
  "vectors": {
    "know": 0.0-1.0,
    "uncertainty": 0.0-1.0,
    "do": 0.0-1.0,
    "completion": 0.0-1.0,
    "context": 0.0-1.0
  },
  "reasoning": "string (explanation of epistemic state)"
}
```

**Output:**
```json
{
  "ok": true,
  "session_id": "abc123...",
  "transaction_id": "def456...",
  "checkpoint_id": "git-sha",
  "message": "PREFLIGHT assessment submitted",
  "vectors_submitted": 5,
  "learning_prior": {
    "adjustments": {"know": -0.03, "uncertainty": 0.04},
    "total_evidence": 3946,
    "summary": {
      "overestimates": ["know"],
      "underestimates": ["completion"],
      "well_calibrated": ["uncertainty", "context"]
    }
  },
  "sentinel": {
    "enabled": true,
    "decision": "proceed"
  }
}
```

**Side Effects:**
- Creates epistemic transaction file
- Records baseline vectors to database and git notes
- Loads learning prior (calibration adjustments from history)
- Returns pattern warnings if approaching known dead-ends

---

### `check-submit`

Validate readiness to proceed with action (NOETIC → PRAXIC gate).

**CLI Usage:**
```bash
# AI-first mode (recommended)
empirica check-submit - << 'EOF'
{
  "session_id": "auto",
  "action_description": "Write authentication middleware",
  "vectors": {
    "know": 0.8,
    "uncertainty": 0.2,
    "context": 0.85,
    "scope": 0.4
  },
  "reasoning": "Investigated codebase, found auth patterns, ready to implement"
}
EOF
```

**Input Schema:**
```json
{
  "session_id": "string",
  "action_description": "string (what you're about to do)",
  "vectors": {
    "know": 0.0-1.0,
    "uncertainty": 0.0-1.0,
    "context": 0.0-1.0,
    "scope": 0.0-1.0
  },
  "reasoning": "string",
  "round": "integer (optional, for tracking)"
}
```

**Output:**
```json
{
  "ok": true,
  "session_id": "abc123...",
  "decision": "proceed",
  "round": 1,
  "metacog": {
    "computed_decision": "proceed",
    "raw_vectors": {"know": 0.8, "uncertainty": 0.2},
    "bias_corrections": {"know": -0.03, "uncertainty": 0.04},
    "readiness_gate": "know>=0.70 AND uncertainty<=0.35",
    "gate_passed": true
  },
  "sentinel": {
    "enabled": true,
    "decision": "proceed"
  },
  "blindspots": {
    "count": 0
  }
}
```

**Decision Values:**
| Decision | Meaning |
|----------|---------|
| `proceed` | Gate passed, continue to praxic phase |
| `investigate` | Confidence too low, stay in noetic phase |
| `proceed_with_caution` | Edge case, proceed but monitor closely |

**Side Effects:**
- Creates CHECK checkpoint snapshot
- Evaluates readiness gate
- Checks for blindspots
- Sentinel may override decision

---

### `postflight-submit`

Record learning delta and create epistemic snapshot. Closes the transaction.

**CLI Usage:**
```bash
# AI-first mode (recommended)
empirica postflight-submit - << 'EOF'
{
  "session_id": "auto",
  "task_description": "Implemented JWT authentication",
  "vectors": {
    "know": 0.88,
    "uncertainty": 0.12,
    "do": 0.9,
    "completion": 1.0,
    "context": 0.85
  },
  "summary": "Implemented JWT auth with RS256 signing, added refresh token support"
}
EOF
```

**Input Schema:**
```json
{
  "session_id": "string",
  "task_description": "string",
  "vectors": {
    "know": 0.0-1.0,
    "uncertainty": 0.0-1.0,
    "do": 0.0-1.0,
    "completion": 0.0-1.0,
    "context": 0.0-1.0
  },
  "summary": "string (what was accomplished)"
}
```

**Output:**
```json
{
  "ok": true,
  "session_id": "abc123...",
  "checkpoint_id": "git-sha",
  "postflight_confidence": 0.88,
  "deltas": {
    "know": 0.28,
    "uncertainty": -0.28,
    "do": 0.6,
    "completion": 1.0
  },
  "calibration": {
    "verification_id": "uuid",
    "evidence_count": 5,
    "sources": ["artifacts", "sentinel", "git"],
    "grounded_coverage": 0.31,
    "calibration_score": 0.29,
    "gaps": {"know": 0.38, "uncertainty": 0.12}
  },
  "storage_layers": {
    "sqlite": true,
    "git_notes": true,
    "bayesian_beliefs": true,
    "episodic_memory": true,
    "qdrant_memory": true,
    "grounded_calibration": true
  },
  "snapshot": {
    "created": true,
    "snapshot_id": "uuid"
  }
}
```

**Side Effects:**
- Closes epistemic transaction (removes active_transaction file)
- Computes learning deltas (POSTFLIGHT - PREFLIGHT)
- Updates Bayesian beliefs for calibration
- Creates epistemic snapshot for session replay
- Syncs to Qdrant memory (if configured)
- Runs grounded calibration (POST-TEST) with objective evidence
- Exports learning trajectory to `.breadcrumbs.yaml`

---

## Grounded Calibration (POST-TEST)

POSTFLIGHT automatically triggers grounded calibration, which compares self-assessed vectors against objective evidence.

**Evidence Sources:**
| Source | Quality | Vectors Grounded |
|--------|---------|-----------------|
| pytest results | OBJECTIVE | know, do, clarity |
| Git metrics | OBJECTIVE | do, change, state |
| Goal/subtask completion | SEMI_OBJECTIVE | completion, do, know |
| Artifact ratios | SEMI_OBJECTIVE | know, uncertainty, signal |
| Issue resolution | SEMI_OBJECTIVE | impact, signal |
| Sentinel decisions | SEMI_OBJECTIVE | context, uncertainty |

**Ungroundable vectors:** engagement, coherence, density (no objective signal)

---

## Python API

```python
from empirica.cli.command_handlers.workflow_commands import (
    handle_preflight_submit_command,
    handle_check_submit_command,
    handle_postflight_submit_command,
)

# Or use the database directly
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()

# Record PREFLIGHT
db.record_checkpoint(
    session_id=session_id,
    checkpoint_type='preflight',
    vectors={'know': 0.6, 'uncertainty': 0.4},
    reasoning='Initial assessment'
)

# Record POSTFLIGHT
db.record_checkpoint(
    session_id=session_id,
    checkpoint_type='postflight',
    vectors={'know': 0.85, 'uncertainty': 0.15},
    reasoning='Completed investigation'
)
```

---

## Transaction Lifecycle

```
1. session-create → Creates Empirica session
2. PREFLIGHT → Opens transaction, baseline vectors
   ↓
3. Work phase (noetic investigation, praxic action)
   - Log findings, unknowns, dead-ends
   - Complete subtasks, goals
   ↓
4. CHECK → Gate decision (proceed/investigate)
   ↓
5. POSTFLIGHT → Close transaction, learning delta
   ↓
6. POST-TEST → Grounded calibration (automatic)
```

**Transactions survive compaction:** The transaction file persists across Claude Code session boundaries. A new session will pick up an open transaction.

---

## Sentinel Integration

The Sentinel gate enforces the CASCADE workflow:

1. **PreToolUse hooks** block praxic tools (Edit/Write/Bash) until CHECK passes
2. **Session hooks** auto-create sessions and bootstrap projects
3. **POSTFLIGHT hooks** capture learning at session end

**Pause Sentinel:**
```bash
touch ~/.empirica/sentinel_paused   # Pause
rm ~/.empirica/sentinel_paused      # Unpause
```

**Environment Variables:**
```bash
EMPIRICA_SENTINEL_MODE=controller   # Active blocking (default)
EMPIRICA_SENTINEL_MODE=observer     # Log-only (no blocking)
EMPIRICA_SENTINEL_LOOPING=false     # Disable investigate loops
```

---

## Best Practices

1. **Always PREFLIGHT before investigation** — Establishes baseline for learning measurement
2. **CHECK before major actions** — Gate prevents premature praxic work
3. **POSTFLIGHT honestly** — Accurate vectors enable calibration improvement
4. **Log artifacts during work** — finding-log, unknown-log, deadend-log feed POST-TEST
5. **Multiple goals per transaction is fine** — Transactions measure coherent work chunks
6. **Natural commit points** — Close transaction at confidence inflection, topic pivot, or context shift

---

## Related Documentation

- [NOETIC_PRAXIC_FRAMEWORK.md](../../architecture/NOETIC_PRAXIC_FRAMEWORK.md) — Thinking phases
- [SENTINEL_ARCHITECTURE.md](../../architecture/SENTINEL_ARCHITECTURE.md) — Gate enforcement
- [GROUNDED_CALIBRATION.md](../../architecture/GROUNDED_CALIBRATION.md) — POST-TEST verification
- [SESSION_RESOLVER_API.md](../SESSION_RESOLVER_API.md) — Transaction-first resolution
