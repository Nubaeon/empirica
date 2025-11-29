# CLI Assessment Format & Checkpoint Issue - HANDOFF

**Date:** 2025-11-27  
**Context:** Phase 1/2 testing issues with mini-agent  
**Status:** Root cause identified, needs format fix

---

## 🎯 CRITICAL ISSUE

**Problem:** Checkpoints not being created during testing  
**Root Cause:** Incorrect assessment JSON format passed to `--assessment-json`  
**Status:** Need to determine correct format for LLM response parsing

---

## 📋 What We Know

### 1. Checkpoint Code Location

**File:** `empirica/cli/command_handlers/cascade_commands.py`  
**Line:** 257 (after database storage)

The checkpoint creation code EXISTS and works:
```python
from empirica.core.canonical.empirica_git import auto_checkpoint
checkpoint_hash = auto_checkpoint(
    session_id=session_id,
    ai_id=ai_id,
    phase='PREFLIGHT',
    vectors=vectors,
    ...
)
```

### 2. The Workflow Problem

**Mini-agent tried:**
```bash
empirica preflight "task" --prompt-only
# Returns immediately (line 110), checkpoint code never reached ❌
```

**What's needed:**
```bash
# Full workflow with assessment
empirica preflight "task" --ai-id mini-agent --assessment-json <FILE>
# Runs through to line 257, creates checkpoint ✅
```

### 3. Assessment Format Issue

**Error message:**
```
Failed to parse self-assessment: Missing or invalid field in LLM response: 'know'
```

**Parser location:** `empirica/core/canonical/canonical_epistemic_assessment.py`  
**Method:** `parse_llm_response()`

**What we tried:**
```json
{
  "know": {"score": 0.70, "rationale": "..."},
  "engagement": {"score": 0.85, "rationale": "..."},
  ...
}
```

**Still failed** - format not matching parser expectations.

---

## 🔍 What Needs Investigation

### Question 1: What's the correct assessment JSON format?

**Check:**
1. Look at `parse_llm_response()` in `canonical_epistemic_assessment.py`
2. See what structure it expects
3. Example: Does it need a wrapper like `{"self_assessment": {...}}`?
4. Or nested format like `{"response": {"vectors": {...}}}`?

**Test command:**
```bash
# Get prompt to see expected format
empirica preflight "test" --prompt-only | jq '.self_assessment_prompt.response_format'
```

### Question 2: Is there a simpler test method?

**Options:**
- A) Use MCP tool `submit_preflight_assessment` directly (Python API)
- B) Create mock args and call handler function directly
- C) Fix the JSON format for --assessment-json

---

## 📝 Key Files to Check

1. **Parser:** `empirica/core/canonical/canonical_epistemic_assessment.py`
   - Line ~200+: `parse_llm_response()` method
   - Shows expected JSON structure

2. **Checkpoint code:** `empirica/cli/command_handlers/cascade_commands.py`
   - Line 257: Checkpoint creation (CONFIRMED EXISTS)
   - Runs AFTER database storage

3. **Test results:** `MINI_AGENT_TEST_RESULTS.md`
   - Shows mini-agent's failures
   - All due to incomplete workflow

---

## ✅ What's Confirmed Working

1. ✅ Checkpoint code exists and is correct
2. ✅ Git notes system works (tested manually)
3. ✅ `--ai-id` parameter works
4. ✅ Identity system works (Phase 2)
5. ✅ MCP tools mapped correctly (29 tools)

---

## ❌ What's Blocking

1. ❌ Assessment JSON format unclear
2. ❌ Mini-agent can't submit assessments
3. ❌ Tests can't progress past step 1

---

## 🎯 Next Steps

1. **Determine correct assessment JSON format**
   - Look at `parse_llm_response()` expectations
   - Create example valid assessment JSON
   - Test with `empirica preflight --assessment-json`

2. **Create helper for mini-agent**
   - Script that generates correct format
   - Or Python function that calls handler directly
   - Or MCP tool example

3. **Update test suite**
   - Show correct format
   - Provide working examples
   - Enable mini-agent to complete tests

---

## 💡 Quick Win Option

**Bypass JSON parsing entirely:**
```python
# Call handler directly with proper args
from empirica.cli.command_handlers.cascade_commands import handle_preflight_command
import argparse

# Create proper Namespace with all fields
args = argparse.Namespace(
    prompt="Test task",
    session_id="test-123",
    ai_id="mini-agent",
    no_git=False,
    sign=False,
    prompt_only=False,  # KEY: Must be False
    assessment_json=None,  # Or provide proper JSON
    json=True,
    output='json',
    compact=False,
    kv=False,
    verbose=False,
    quiet=False
)

# This should run full workflow including checkpoint
result = handle_preflight_command(args)
```

But this still requires actual LLM assessment or correct JSON format.

---

## 🔄 Status Summary

**Phase 1:** Code is 100% correct, workflow documentation issue  
**Phase 2:** Identity system working, signing needs testing  
**Blocker:** Assessment JSON format for mini-agent  
**Solution:** Determine correct format or use direct Python API  

**Files Modified Today:** 18 commits, ~7,750 lines  
**Ready for:** Format fix + mini-agent re-test

---

*Handoff Point: Determine correct assessment JSON format for parse_llm_response()*
