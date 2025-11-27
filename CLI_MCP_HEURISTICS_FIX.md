# CLI and MCP Heuristics Remediation

**Date:** 2025-11-27  
**Issue:** Ensure Empirica CLI does not use heuristics and supports multi-AI tracking

## Changes Made

### 1. Added `--ai-id` Parameter to Preflight/Postflight Commands

**Problem:** The `--ai-id` parameter was missing from `preflight` and `postflight` commands, making it impossible to differentiate between different AI agents in sessions.

**Files Modified:**
- `empirica/cli/cli_core.py`
- `empirica/cli/command_handlers/cascade_commands.py`

**Changes:**

#### cli_core.py
- Added `--ai-id` parameter to `preflight_parser` (line 186)
  - Default: `'empirica_cli'`
  - Help text: "AI identifier for session tracking"
  
- Added `--ai-id` parameter to `postflight_parser` (line 201)
  - No default (optional)
  - Help text: "AI identifier for session tracking (should match preflight)"

#### cascade_commands.py
- Updated `handle_preflight_command()` to extract and use `ai_id`:
  - Line 87: `ai_id = getattr(args, 'ai_id', 'empirica_cli')`
  - Line 90: `assessor = CanonicalEpistemicAssessor(agent_id=ai_id)`
  - Line 238: `db.create_session(ai_id=ai_id, ...)`

- Updated `handle_postflight_command()` to extract and use `ai_id`:
  - Line 339: `ai_id = getattr(args, 'ai_id', None)`
  - Line 343: `assessor = CanonicalEpistemicAssessor(agent_id=ai_id if ai_id else session_id)`

**Usage:**
```bash
# Preflight with specific AI
empirica preflight "task" --ai-id claude-sonnet-4

# Postflight matching the AI
empirica postflight <session-id> --ai-id claude-sonnet-4 --summary "task complete"
```

---

### 2. Ensured MetacognitionMonitor Uses LLM Mode (No Heuristics)

**Problem:** The `MetacognitionMonitor` has a `mode` parameter that defaults to `'llm'`, but it wasn't being explicitly set when instantiated from CLI commands. This could lead to accidental heuristic usage if the default ever changed.

**Files Modified:**
- `empirica/cli/command_handlers/assessment_commands.py`
- `empirica/cli/command_handlers/investigation_commands.py`

**Changes:**

#### assessment_commands.py
- Line 143-144: Explicitly set `mode='llm'` when creating `MetacognitionMonitor`
  ```python
  # Use mode='llm' to ensure NO heuristics are used
  evaluator = MetacognitionMonitor(mode='llm')
  ```

#### investigation_commands.py
- Line 210-211: Explicitly set `mode='llm'` when creating `MetacognitionMonitor`
  ```python
  # Use mode='llm' to ensure NO heuristics are used
  evaluator = MetacognitionMonitor(mode='llm')
  ```

**Rationale:**
- The `MetacognitionMonitor` class supports two modes:
  - `'llm'`: Uses genuine AI self-assessment (correct)
  - `'heuristic'`: Uses deterministic heuristics (deprecated for CLI use)
- By explicitly setting `mode='llm'`, we ensure no heuristics are ever used
- This makes the code self-documenting and prevents future bugs

---

### 3. Verified Goal Orchestrator Has No Heuristics

**File Checked:**
- `empirica/core/canonical/canonical_goal_orchestrator.py`

**Findings:**
✅ **CONFIRMED: No heuristics used**

**Evidence:**
- Line 103: Explicit documentation: `"NO heuristics, NO keyword matching, NO hardcoded templates."`
- Line 305: Additional confirmation: `"1. **No Templates**: Don't use hardcoded goal templates. Generate based on understanding."`
- No hardcoded numeric returns found in goal generation methods
- All goal creation is LLM-powered based on epistemic assessment

**No changes needed** - the goal orchestrator is already heuristic-free.

---

## Testing

### Manual Testing Commands

```bash
# Test preflight with ai-id
empirica preflight "Test AI identification" --ai-id test-agent-1

# Test postflight with ai-id
empirica postflight <session-id> --ai-id test-agent-1 --summary "Task complete"

# Verify metacognitive assessment doesn't use heuristics
empirica metacognitive "Analyze this task" --verbose

# Check sessions are created with correct ai_id
sqlite3 .empirica/sessions/sessions.db "SELECT ai_id, session_id FROM sessions ORDER BY created_at DESC LIMIT 5;"
```

### Expected Results
1. Sessions should be created with the specified `ai_id`
2. Different AI agents can be tracked separately
3. No heuristic calculations should occur in metacognitive assessments
4. Goal orchestrator should only use LLM reasoning

---

## MCP Server Impact

The MCP server (`mcp_local/empirica_mcp_server.py`) already supports these features:
- `bootstrap_session` tool accepts `ai_id` parameter
- `execute_preflight` and `execute_postflight` are thin wrappers around CLI
- These changes improve MCP tool functionality automatically

**MCP Usage:**
```json
{
  "tool": "execute_preflight",
  "input": {
    "prompt": "Task description",
    "ai_id": "claude-sonnet-4"
  }
}
```

---

## Verification Checklist

- [x] Added `--ai-id` to preflight command parser
- [x] Added `--ai-id` to postflight command parser
- [x] Updated preflight handler to use `ai_id` for assessor
- [x] Updated preflight handler to use `ai_id` for session creation
- [x] Updated postflight handler to use `ai_id` for assessor
- [x] Explicitly set `mode='llm'` in assessment_commands.py
- [x] Explicitly set `mode='llm'` in investigation_commands.py
- [x] Verified goal orchestrator has no heuristics
- [x] All changes are backward compatible (defaults provided)

---

## Backward Compatibility

All changes are **fully backward compatible**:

1. **Preflight `--ai-id`**: Defaults to `'empirica_cli'` if not provided
2. **Postflight `--ai-id`**: Optional, falls back to `session_id` for compatibility
3. **MetacognitionMonitor mode**: Already defaulted to `'llm'`, now explicit
4. **Goal orchestrator**: No changes needed, already correct

Existing scripts and workflows will continue to work without modification.

---

## Summary

**Problem Solved:**
- ✅ Multi-AI tracking now supported via `--ai-id` parameter
- ✅ Guaranteed no heuristics in metacognitive assessments
- ✅ Goal orchestrator confirmed heuristic-free
- ✅ All changes are backward compatible

**Files Modified:** 4
- `empirica/cli/cli_core.py` (+2 lines)
- `empirica/cli/command_handlers/cascade_commands.py` (+6 lines, modified 4)
- `empirica/cli/command_handlers/assessment_commands.py` (+1 line)
- `empirica/cli/command_handlers/investigation_commands.py` (+1 line)

**Total Changes:** ~10 lines of code, high impact

**Ready for mini-agent testing:** ✅
