# Mini-Agent Testing Guide: Phase 1, 2, and 3

**Last Updated:** 2025-11-27  
**Status:** Ready for testing with correct assessment format

---

## 🎯 Overview

This guide provides mini-agent with complete instructions for testing:
- **Phase 1:** Git automation (checkpoint creation)
- **Phase 2:** Cryptographic identity (EEP-1 signing)
- **Phase 3:** Cross-session goal discovery

---

## 📋 Prerequisites

1. **Identity created:**
   ```bash
   empirica identity-create --ai-id mini-agent
   ```

2. **Git repository initialized:**
   ```bash
   git init  # if not already initialized
   ```

3. **Empirica installed:**
   ```bash
   pip install -e .
   ```

---

## 🔍 Critical Fix: Assessment JSON Format

### ❌ WRONG Format (Old - Causes Parse Error)
```json
{
  "vectors": {
    "engagement": 0.85,
    "know": 0.70,
    ...
  }
}
```

### ✅ CORRECT Format (Required by `parse_llm_response()`)
```json
{
  "engagement": {
    "score": 0.85,
    "rationale": "Your genuine reasoning about engagement"
  },
  "foundation": {
    "know": {
      "score": 0.70,
      "rationale": "Your genuine reasoning about knowledge"
    },
    "do": {
      "score": 0.75,
      "rationale": "Your genuine reasoning about capability"
    },
    "context": {
      "score": 0.80,
      "rationale": "Your genuine reasoning about context"
    }
  },
  "comprehension": {
    "clarity": {"score": 0.85, "rationale": "..."},
    "coherence": {"score": 0.82, "rationale": "..."},
    "signal": {"score": 0.78, "rationale": "..."},
    "density": {"score": 0.40, "rationale": "..."}
  },
  "execution": {
    "state": {"score": 0.75, "rationale": "..."},
    "change": {"score": 0.70, "rationale": "..."},
    "completion": {"score": 0.60, "rationale": "..."},
    "impact": {"score": 0.65, "rationale": "..."}
  },
  "uncertainty": {
    "score": 0.25,
    "rationale": "Your genuine reasoning about uncertainty"
  }
}
```

**See:** `docs/examples/assessment_format_example.json` for full example with detailed rationales.

---

## 🧪 Phase 1: Git Automation Testing

### Test 1: Basic Checkpoint Creation

**Objective:** Verify checkpoints are created in git notes after CASCADE phases

**Steps:**

1. **Get preflight prompt:**
   ```bash
   SESSION_ID="test-phase1-$(date +%s)"
   empirica preflight "Test Phase 1 checkpoint" \
       --ai-id mini-agent \
       --session-id "$SESSION_ID" \
       --prompt-only > /tmp/prompt.json
   ```

2. **Perform genuine self-assessment:**
   Create `/tmp/assessment.json` with nested format (see above).
   
   **Quick test version:**
   ```bash
   cp docs/examples/assessment_format_example.json /tmp/assessment.json
   ```

3. **Submit assessment (creates checkpoint):**
   ```bash
   empirica preflight "Test Phase 1 checkpoint" \
       --ai-id mini-agent \
       --session-id "$SESSION_ID" \
       --assessment-json /tmp/assessment.json \
       --json
   ```

4. **Verify checkpoint created:**
   ```bash
   # Check for checkpoint in git notes
   git notes --ref=empirica/checkpoints show HEAD 2>/dev/null
   
   # Or search all commits
   git notes --ref=empirica/checkpoints list
   ```

**Success Criteria:**
- ✅ No parse errors
- ✅ Checkpoint appears in git notes
- ✅ Checkpoint contains session_id
- ✅ Checkpoint contains vectors

### Test 2: Using Helper Script

**Quick test:**
```bash
bash test_working_checkpoint.sh
```

**Expected output:**
```
🧪 Phase 1 Checkpoint Test - CORRECT Workflow
Session: test-working-1234567890

Step 1: Getting prompt...
✓ Prompt received

Step 2: Creating assessment...
✓ Assessment created

Step 3: Submitting assessment (checkpoint created here)...
✓ Assessment submitted

Step 4: Verifying checkpoint creation...
Total checkpoints: X
✅ Checkpoint found on HEAD!
```

---

## 🔐 Phase 2: Identity & Signing Testing

### Test 3: Signed Assessment

**Objective:** Verify EEP-1 cryptographic signing of assessments

**Steps:**

1. **Create identity (if not exists):**
   ```bash
   empirica identity-create --ai-id mini-agent
   ```

2. **Verify identity exists:**
   ```bash
   empirica identity-list
   # Should show: mini-agent with public key
   ```

3. **Export public key:**
   ```bash
   empirica identity-export --ai-id mini-agent > mini-agent-pubkey.pem
   cat mini-agent-pubkey.pem
   ```

4. **Submit signed assessment:**
   ```bash
   SESSION_ID="test-phase2-$(date +%s)"
   
   empirica preflight "Test Phase 2 signing" \
       --ai-id mini-agent \
       --session-id "$SESSION_ID" \
       --assessment-json /tmp/assessment.json \
       --sign \
       --json
   ```

5. **Verify signature in output:**
   Look for `signature` field in JSON output:
   ```json
   {
     "signature": {
       "signature_hex": "...",
       "public_key_hex": "...",
       "cascade_trace_hash": "...",
       "timestamp": "..."
     }
   }
   ```

**Success Criteria:**
- ✅ Identity created with Ed25519 keypair
- ✅ Signature appears in output
- ✅ Public key matches identity
- ✅ Cascade trace hash included

---

## 🔗 Phase 3: Goal Discovery Testing

### Test 4: Goal Creation and Discovery

**Objective:** Verify cross-session goal discovery via git notes

**Steps:**

1. **Create a goal:**
   ```bash
   empirica goal-create \
       --ai-id mini-agent \
       --objective "Test goal discovery" \
       --scope project_wide \
       --success-criteria "Goal discoverable by other AI" \
       --success-criteria "Goal has valid metadata"
   ```

2. **List goals:**
   ```bash
   empirica goal-list --ai-id mini-agent
   ```

3. **Discover goals from other AIs:**
   ```bash
   # Should show goals from all AIs
   empirica goal-discover --ai-id mini-agent
   ```

4. **Discover from specific AI:**
   ```bash
   empirica goal-discover --from-ai-id other-agent
   ```

**Success Criteria:**
- ✅ Goal created in git notes
- ✅ Goal discoverable via `goal-discover`
- ✅ Goal metadata includes ai_id
- ✅ Cross-AI discovery works

---

## 🛠️ MCP Tool Equivalents

For programmatic access (e.g., via MCP server):

### Phase 1: Checkpoints

**CLI:**
```bash
empirica preflight "task" --ai-id ID --assessment-json FILE
```

**MCP:**
```python
# Tool: execute_preflight
{
  "session_id": "test-123",
  "prompt": "task"
}

# Tool: submit_preflight_assessment
{
  "session_id": "test-123",
  "vectors": {...},  # Nested format
  "reasoning": "..."
}
```

### Phase 2: Signing

**CLI:**
```bash
empirica identity-create --ai-id mini-agent
empirica preflight "task" --sign
```

**MCP:**
```python
# Tool: create_identity
{
  "ai_id": "mini-agent"
}

# Tool: submit_preflight_assessment (auto-signs if identity exists)
{
  "session_id": "test-123",
  "vectors": {...},
  "reasoning": "..."
}
```

### Phase 3: Goals

**CLI:**
```bash
empirica goal-create --ai-id ID --objective "..." --scope project_wide
empirica goal-discover --from-ai-id other-agent
```

**MCP:**
```python
# Tool: create_goal
{
  "session_id": "test-123",
  "objective": "...",
  "scope": "project_wide",
  "success_criteria": ["..."]
}

# Tool: discover_goals
{
  "from_ai_id": "other-agent"
}
```

---

## 📊 Complete Test Sequence

**Run all phases:**

```bash
#!/bin/bash
set -e

echo "🧪 COMPLETE EMPIRICA TESTING: Phases 1, 2, 3"
echo ""

# Setup
AI_ID="mini-agent"
SESSION_BASE="test-complete-$(date +%s)"

# Phase 1: Git Automation
echo "=== PHASE 1: Git Automation ==="
SESSION_1="${SESSION_BASE}-phase1"

empirica preflight "Phase 1 test" \
    --ai-id "$AI_ID" \
    --session-id "$SESSION_1" \
    --assessment-json docs/examples/assessment_format_example.json \
    --json

git notes --ref=empirica/checkpoints show HEAD
echo "✅ Phase 1 complete"
echo ""

# Phase 2: Identity & Signing
echo "=== PHASE 2: Identity & Signing ==="
SESSION_2="${SESSION_BASE}-phase2"

empirica identity-create --ai-id "$AI_ID" 2>/dev/null || echo "Identity exists"

empirica preflight "Phase 2 test" \
    --ai-id "$AI_ID" \
    --session-id "$SESSION_2" \
    --assessment-json docs/examples/assessment_format_example.json \
    --sign \
    --json | grep -q "signature"

echo "✅ Phase 2 complete"
echo ""

# Phase 3: Goal Discovery
echo "=== PHASE 3: Goal Discovery ==="

empirica goal-create \
    --ai-id "$AI_ID" \
    --objective "Complete Phase 1-3 testing" \
    --scope project_wide \
    --success-criteria "All phases tested" \
    --success-criteria "Checkpoints verified"

empirica goal-discover --ai-id "$AI_ID"

echo "✅ Phase 3 complete"
echo ""

echo "🎉 ALL PHASES COMPLETE!"
```

---

## 🐛 Troubleshooting

### Issue: "Missing or invalid field in LLM response: 'know'"

**Cause:** Using old flat format instead of nested format

**Fix:** Use nested format with `engagement`, `foundation`, `comprehension`, `execution`, `uncertainty` keys

**Example:**
```bash
# Wrong - will fail
echo '{"vectors": {"know": 0.7, ...}}' > assessment.json

# Correct - will work
echo '{"foundation": {"know": {"score": 0.7, "rationale": "..."}}}' > assessment.json
```

### Issue: "Checkpoint not found"

**Cause:** No commits exist or checkpoint attached to wrong commit

**Fix:**
```bash
# Check HEAD
git notes --ref=empirica/checkpoints show HEAD

# Check recent commits
git log --oneline -5 | while read commit; do
    git notes --ref=empirica/checkpoints show $commit 2>/dev/null || true
done
```

### Issue: "Identity not found"

**Cause:** Identity not created

**Fix:**
```bash
empirica identity-create --ai-id mini-agent
empirica identity-list  # Verify
```

---

## 📚 Additional Resources

- **Assessment Format:** `docs/examples/assessment_format_example.json`
- **Parser Code:** `empirica/core/canonical/canonical_epistemic_assessment.py` (lines 585-788)
- **CLI Handler:** `empirica/cli/command_handlers/cascade_commands.py` (lines 78-393)
- **Handoff Doc:** `HANDOFF_CLI_ASSESSMENT_FORMAT.md`
- **Test Results:** `MINI_AGENT_TEST_RESULTS.md`

---

## ✅ Success Checklist

Mini-agent should verify:

### Phase 1: Git Automation
- [ ] Checkpoint created after preflight
- [ ] Checkpoint contains correct session_id
- [ ] Checkpoint contains all 13 vectors
- [ ] Checkpoint retrievable via git notes

### Phase 2: Identity & Signing
- [ ] Identity created with keypair
- [ ] Public key exportable
- [ ] Assessment signed with --sign flag
- [ ] Signature verifiable

### Phase 3: Goal Discovery
- [ ] Goals created in git notes
- [ ] Goals discoverable by same AI
- [ ] Goals discoverable by other AIs
- [ ] Goal metadata correct

---

**Ready for testing!** 🚀

Use `test_working_checkpoint.sh` for quick Phase 1 validation, then proceed to Phases 2 and 3.

---

## Schema Migration Context (For Mini-Agent)

### What Changed
Rovo Dev completed 5 phases of schema migration:
1. **Converters**: OLD ↔ NEW conversion (21 tests)
2. **Assessor**: Returns NEW schema internally (14 tests)
3. **CASCADE**: Uses NEW schema internally (42 tests)
4. **PersonaHarness**: Uses NEW schema for priors
5. **CLI/MCP**: No changes needed (wrappers handle it)

### Wrapper Pattern
All components use wrappers for backwards compatibility:
```python
def old_method() -> OldSchema:
    new_result = new_method()  # Uses NEW schema
    return convert_new_to_old(new_result)  # Backwards compat
```

### Key Files
- `empirica/core/schemas/assessment_converters.py` - Converters
- `empirica/core/canonical/canonical_epistemic_assessment.py` - Assessor (has parse_llm_response_new)
- `empirica/core/metacognitive_cascade/metacognitive_cascade.py` - CASCADE (has _assess_epistemic_state_new)
- `empirica/core/persona/harness/persona_harness.py` - PersonaHarness (has _apply_priors_new)

### Testing Notes
- All tests still use OLD schema (via wrappers)
- Mock fixtures in `tests/unit/cascade/conftest.py`
- 77 tests pass, 0 failures
- 10 tests skipped (need your attention!)

### What NOT to Break
- Don't remove OLD schema yet (Phase 9)
- Don't change wrapper return types
- Tests expect OLD schema externally
- Internal NEW schema usage is hidden

### Migration Docs
See `docs/wip/schema-migration/` for complete details:
- `README.md` - Overview
- `HALFWAY_MILESTONE.md` - Current status
- Individual phase docs for specifics

---
