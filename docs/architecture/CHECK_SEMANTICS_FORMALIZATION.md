# CHECK Semantics Formalization

**Date:** 2025-12-26
**Purpose:** Clarify CHECK vs check-drift, session-bound vs sessionless epistemic assessment

---

## The Problem

We're using "CHECK" ambiguously in two contexts:

### Context 1: Session-Bound Decision Gate (CASCADE Workflow)
```
PREFLIGHT → [work] → CHECK (proceed vs investigate) → [more work] → POSTFLIGHT
```
- **Purpose:** Mid-session decision gate
- **Requires:** session_id (must be in active session)
- **Outputs:** Decision (proceed/investigate), confidence, vectors
- **Stored:** SQLite reflexes table, git notes

### Context 2: Sessionless Epistemic State Check (Compact Boundaries)
```
PreCompact → [COMPACT] → PostCompact
```
- **Purpose:** Measure epistemic state at memory boundaries
- **Should NOT require:** session_id (pre-compact might be end of old session, post-compact is start of new session)
- **Outputs:** Vectors only (no decision)
- **Stored:** Snapshot JSON (not reflexes table)

---

## User's Questions

### Q1: Should we decouple CHECK and make it sessionless?
**Answer:** NO - keep CHECK session-bound

**Rationale:**
- CHECK is fundamentally about *decision gates during work*
- Requires session context (what work am I doing?)
- Needs to write to reflexes table for drift detection
- Part of CASCADE workflow semantics

### Q2: Should we decouple check-drift and add epistemic-state-check?
**Answer:** YES - create new command `empirica assess-state`

**Rationale:**
- check-drift is about *comparing* states (detecting drift)
- assess-state is about *capturing* state (fresh measurement)
- Compact boundaries need capture, not comparison
- Sessionless assessment is useful beyond compacts (statusline, monitoring, etc.)

---

## Proposed Solution

### New Command: `empirica assess-state`

**Purpose:** Capture epistemic state without session binding

**Usage:**
```bash
# At compact boundaries (no session required)
empirica assess-state --output json

# With session context (optional)
empirica assess-state --session-id abc123 --output json

# With prompt/context (for self-assessment)
empirica assess-state --prompt "Assess current epistemic state after memory compact" --output json
```

**Output:**
```json
{
  "ok": true,
  "timestamp": "2025-12-26T01:30:00",
  "vectors": {
    "engagement": 0.85,
    "know": 0.70,
    "uncertainty": 0.30,
    "impact": 0.75,
    "completion": 0.60,
    ...
  },
  "reasoning": "Self-assessed reasoning",
  "session_id": "abc123"  // Optional, if provided
}
```

**Storage:**
- NOT in reflexes table (sessionless)
- Can be included in snapshot JSON
- Can be used for statusline display
- Can feed into CHECK if session context added later

---

## Workflow Integration

### Pre-Compact (Current vs Proposed)

**Current (Stale):**
```python
# pre-compact.py
subprocess.run(['empirica', 'check-drift', '--trigger', 'pre_summary'])
# → Loads last checkpoint (may be hours old)
```

**Proposed (Fresh):**
```python
# pre-compact.py

# Step 1: Capture fresh state
fresh_state = subprocess.run(
    ['empirica', 'assess-state', '--output', 'json'],
    capture_output=True,
    text=True
)
vectors = json.loads(fresh_state.stdout).get('vectors', {})

# Step 2: Save snapshot with FRESH vectors
snapshot = {
    "type": "pre_summary_snapshot",
    "timestamp": now(),
    "vectors": vectors,  # <-- FRESH, not from old checkpoint
    "session_id": session_id,
    "investigation_context": {...}
}
save_snapshot(snapshot)
```

### Post-Compact (Current vs Proposed)

**Current (Passive):**
```python
# post-compact.py
print("💡 Recommendation: Run CHECK or PREFLIGHT to reassess")
# → User must manually run command
```

**Proposed (Active - Self-Prompting):**
```python
# post-compact.py

# Load evidence
bootstrap = load_bootstrap()
pre_snapshot = load_pre_snapshot()

# Auto-assess fresh state
fresh_state = subprocess.run(
    ['empirica', 'assess-state',
     '--prompt', f"Bootstrap evidence: {bootstrap}. Pre-compact state: {pre_snapshot}. Assess current state.",
     '--output', 'json'],
    capture_output=True,
    text=True
)
post_vectors = json.loads(fresh_state.stdout).get('vectors', {})

# Compare and report drift
drift = calculate_drift(pre_snapshot['vectors'], post_vectors)

print(f"""
📊 Drift Analysis:
   Pre-compact: know={pre_snapshot['vectors']['know']:.2f}, uncertainty={pre_snapshot['vectors']['uncertainty']:.2f}
   Post-compact: know={post_vectors['know']:.2f}, uncertainty={post_vectors['uncertainty']:.2f}
   Drift: {drift:.2%}
""")
```

---

## Self-Prompting Philosophy

**User's insight:** "Any AI with metacognitive abilities and context window awareness should be able to self-prompt"

**Implications:**

1. **assess-state can self-prompt:**
   - AI receives compact boundary signal
   - AI introspects current state
   - AI generates epistemic vectors via self-reflection
   - No human input needed

2. **Works across all AI interfaces:**
   - Claude Code (hooks)
   - ChatGPT (plugins)
   - Cursor (extensions)
   - Any AI with:
     - Metacognitive ability (can reflect on own state)
     - Context window awareness (knows token count)
     - Tool access (can call empirica commands)

3. **check-drift becomes comparison tool:**
   - assess-state = capture
   - check-drift = compare
   - Separation of concerns

---

## CHECK Command Stays Session-Bound

**CHECK workflow unchanged:**
```bash
# During active session work
empirica check -  # JSON via stdin
{
  "session_id": "abc123",
  "vectors": {...},
  "decision": "proceed",  # or "investigate"
  "reasoning": "..."
}
```

**Purpose:** Decision gate during work
**Requires:** session_id (work context)
**Outputs:** Decision + confidence + vectors
**Stored:** Reflexes table + git notes

---

## Implementation Plan

### Phase 1: Create assess-state Command
1. Add parser: `empirica/cli/parsers/epistemic_parsers.py`
2. Add handler: `empirica/cli/command_handlers/epistemic_commands.py`
3. Implement sessionless assessment (no reflexes table write)
4. Return JSON with vectors only

### Phase 2: Integrate into Pre-Compact
1. Modify `pre-compact.py` to call assess-state
2. Save snapshot with fresh vectors
3. Test: Verify no stale checkpoints

### Phase 3: Integrate into Post-Compact
1. Modify `post-compact.py` to call assess-state
2. Auto-compare pre vs post vectors
3. Display drift analysis
4. Test: Verify drift detection works

### Phase 4: Add Self-Prompting Context
1. Add `--prompt` parameter to assess-state
2. Allow AI to pass evidence/context for self-assessment
3. Test with statusline integration

---

## Backward Compatibility

**Existing commands unchanged:**
- `empirica check` - still session-bound, still decision gate
- `empirica check-drift` - still comparison tool
- `empirica preflight-submit` - still session start baseline
- `empirica postflight-submit` - still session completion

**New command:**
- `empirica assess-state` - sessionless state capture

**Migration:**
- Hooks updated to use assess-state at compact boundaries
- CHECK remains for in-session decision gates
- No breaking changes to existing workflows

---

## Summary

**Formalized Semantics:**

| Command | Purpose | Session Binding | Output | Storage |
|---------|---------|-----------------|--------|---------|
| `check` | Decision gate during work | Required | Decision + vectors | Reflexes table |
| `assess-state` | Capture epistemic state | Optional | Vectors only | Snapshot JSON |
| `check-drift` | Compare states | Required | Drift analysis | None (read-only) |
| `preflight-submit` | Session start baseline | Required | Vectors | Reflexes table |
| `postflight-submit` | Session completion | Required | Vectors + deltas | Reflexes table |

**Key Insight:** CHECK is for sessions, assess-state is for states. Separation clarifies semantics.
