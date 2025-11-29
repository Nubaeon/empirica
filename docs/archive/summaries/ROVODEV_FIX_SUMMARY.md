# Fix for Claude rovodev Empirica Issues

**Date**: 2025-11-28
**Issue**: Claude rovodev getting assessment parsing errors
**Status**: ✅ **FIXED**

## The Problem

Claude rovodev was getting these errors:

```
❌ Failed to parse self-assessment: Missing or invalid field in LLM response: 'score'
❌ Failed to parse self-assessment: Missing or invalid field in LLM response: 'know'
```

### Root Cause

Claude rovodev was trying to use the **Empirica CLI directly** (`empirica preflight`) instead of using **MCP tools** (`execute_preflight`).

The CLI is designed for human users, not AI agents. When AI agents try to use the CLI:
1. They don't get the self-assessment prompt in the right format
2. They try to pass assessments that don't match the expected nested structure
3. The parser rejects the malformed assessment

## The Fix

### Created Documentation

1. **`/home/yogapad/.rovodev/EMPIRICA_MCP_USAGE.md`**
   - Complete guide to using Empirica MCP tools correctly
   - Shows exact vector structure required (nested with foundation/comprehension/execution)
   - Full examples of PREFLIGHT → CHECK → POSTFLIGHT flow

2. **`/home/yogapad/.mini-agent/config/EMPIRICA_MCP_CRITICAL.md`**
   - Critical quick-reference guide
   - Common mistakes and how to avoid them
   - Troubleshooting section

3. **Updated `/home/yogapad/.mini-agent/config/system_prompt.md`**
   - Added critical notice at the top pointing to the MCP guide
   - Ensures agents see this before trying to use Empirica

### What Changed

**Before (WRONG):**
```bash
# Trying to use CLI directly
empirica preflight "task" --ai-id rovodev
empirica preflight "task" --assessment-json '{...}'
```

**After (CORRECT):**
```python
# Use MCP tools
result = execute_preflight(
    session_id="abc123",
    prompt="task description"
)

# Read result['self_assessment_prompt'] and assess yourself!

submit_preflight_assessment(
    session_id="abc123",
    vectors={
        "engagement": {
            "score": 0.85,
            "rationale": "Genuine reasoning",
            "evidence": "Supporting facts"
        },
        "foundation": {
            "know": {"score": 0.70, "rationale": "...", "evidence": "..."},
            "do": {"score": 0.75, "rationale": "...", "evidence": "..."},
            "context": {"score": 0.80, "rationale": "...", "evidence": "..."}
        },
        "comprehension": {
            "clarity": {"score": 0.85, "rationale": "...", "evidence": "..."},
            "coherence": {"score": 0.70, "rationale": "...", "evidence": "..."},
            "signal": {"score": 0.65, "rationale": "...", "evidence": "..."},
            "density": {"score": 0.60, "rationale": "...", "evidence": "..."}
        },
        "execution": {
            "state": {"score": 0.70, "rationale": "...", "evidence": "..."},
            "change": {"score": 0.65, "rationale": "...", "evidence": "..."},
            "completion": {"score": 0.00, "rationale": "...", "evidence": "..."},
            "impact": {"score": 0.75, "rationale": "...", "evidence": "..."}
        },
        "uncertainty": {
            "score": 0.40,
            "rationale": "Genuine uncertainty assessment",
            "evidence": "What you're unsure about"
        }
    },
    reasoning="Why this assessment makes sense"
)
```

## Required Vector Structure

The parser expects this EXACT nested structure:

```json
{
  "engagement": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
  "foundation": {
    "know": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
    "do": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
    "context": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." }
  },
  "comprehension": {
    "clarity": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
    "coherence": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
    "signal": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
    "density": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." }
  },
  "execution": {
    "state": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
    "change": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
    "completion": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." },
    "impact": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." }
  },
  "uncertainty": { "score": 0.0-1.0, "rationale": "...", "evidence": "..." }
}
```

**Key points:**
1. **Nested structure**: `foundation`, `comprehension`, `execution` are tiers
2. **Each vector has**: `score` (number), `rationale` (string), `evidence` (optional string)
3. **Not flat**: Don't do `{know: 0.7, do: 0.8, ...}`
4. **Not simple scores**: Don't do `{engagement: 0.85, foundation: {know: 0.70}}`

## Why This Happened

The PersonaHarness implementation didn't cause this issue, but it highlighted the confusion:
- Personas use the same assessment format
- The MCP tools are the correct interface for AI agents
- The CLI is for human users typing commands

The error messages made it seem like a bug, but it was actually a usage issue: trying to use the CLI when MCP tools should be used.

## How to Verify Fix

Claude rovodev should now:
1. Call `bootstrap_session(ai_id="rovodev", ...)`
2. Call `execute_preflight(session_id="...", prompt="task")`
3. Read the `self_assessment_prompt` from the result
4. Perform genuine self-assessment
5. Call `submit_preflight_assessment(session_id="...", vectors={...})`

And avoid:
- ❌ `empirica preflight "task"` (CLI command)
- ❌ Flat vector structure
- ❌ Missing score/rationale/evidence structure

## Files Changed

1. Created `/home/yogapad/.rovodev/EMPIRICA_MCP_USAGE.md` - Full MCP usage guide
2. Created `/home/yogapad/.mini-agent/config/EMPIRICA_MCP_CRITICAL.md` - Critical quick reference
3. Updated `/home/yogapad/.mini-agent/config/system_prompt.md` - Added critical notice at top

## Next Steps

1. Claude rovodev should restart their session to pick up the new system prompt
2. When using Empirica, they should reference `/home/yogapad/.rovodev/EMPIRICA_MCP_USAGE.md`
3. Always use MCP tools, never CLI commands directly

## Testing

To verify the fix works, rovodev should:

```python
# This should now work correctly:
session = bootstrap_session(ai_id="rovodev", session_type="development")
result = execute_preflight(session_id=session["session_id"], prompt="Test task")
# Read result["self_assessment_prompt"] carefully!
submit_preflight_assessment(
    session_id=session["session_id"],
    vectors={ /* properly nested structure */ },
    reasoning="Test reasoning"
)
```

If they see:
- ✅ "Decision: investigate" or "Decision: proceed" → SUCCESS
- ❌ "Missing or invalid field" → Still using wrong format

## Summary

**The issue was NOT caused by PersonaHarness.**

The issue was that AI agents were trying to use human-oriented CLI commands instead of the AI-oriented MCP tools. The solution is documentation and system prompt updates to guide agents to use MCP tools correctly.

All documentation is now in place for both mini-agent and rovodev to use Empirica correctly via MCP tools.
