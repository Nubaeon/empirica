# Error Helper Application Progress

**Started:** November 18, 2025  
**Goal:** Apply structured error responses across MCP server  
**Current Status:** 11/48 error points (23%)

---

## Summary

Created `create_error_response()` helper function that adds:
- `error_type`: Classification (session_not_found, invalid_alias, etc.)
- `reason`: Why the error occurred
- `suggestion`: First thing to try
- `alternatives`: Other options
- `recovery_commands`: Exact commands to fix
- `context`: Additional debugging info

---

## Error Points Completed (11)

### Batch 1: Initial Implementation (6 points)
1. ✅ `get_session_summary` - invalid_alias
2. ✅ `get_session_summary` - session_not_found
3. ✅ `get_calibration_report` - invalid_alias
4. ✅ `get_calibration_report` - insufficient_data
5. ✅ `resume_previous_session` - invalid_input (missing session_id)
6. ✅ `resume_previous_session` - session_not_found (specific session)

### Batch 2: Additional Session Errors (5 points)
7. ✅ `get_epistemic_state` - invalid_alias
8. ✅ `get_epistemic_state` - session_not_found
9. ✅ `load_git_checkpoint` - invalid_alias
10. ✅ `resume_previous_session` (last mode) - session_not_found
11. ✅ `resume_previous_session` (last_n mode) - session_not_found
12. ✅ `query_handoff_reports` - session_not_found

---

## Remaining Error Points (37)

### High Priority (Session/Input Related)
- `execute_preflight` failures
- `execute_check` failures
- `execute_postflight` failures
- Goal/subtask not found errors
- Input validation errors

### Medium Priority (Component Errors)
- Component initialization failures
- Git operation failures
- Database operation failures

### Lower Priority (Generic Errors)
- Generic exception handlers
- Timeout errors
- Unknown tool errors

---

## Error Type Distribution

**Currently Supported:**
- `session_not_found` (7 instances)
- `invalid_alias` (4 instances)
- `insufficient_data` (1 instance)
- `invalid_input` (1 instance)

**Needed for Remaining Errors:**
- `component_unavailable` - For initialization failures
- `git_unavailable` - For git operation failures
- `database_error` - For database operation failures
- `timeout` - For timeout errors
- `invalid_input` - More validation errors

---

## Pattern Recognition

### Easy to Apply (Common Pattern)
```python
# Old
return [types.TextContent(type="text", text=json.dumps({
    "ok": False,
    "error": "Some error message"
}, indent=2))]

# New
error_response = create_error_response(
    "error_type",
    "Some error message",
    {"context": "info"}
)
return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
```

### Requires Reasoning
Each error needs semantic analysis to determine:
1. Correct `error_type` classification
2. Appropriate recovery suggestions
3. Relevant context information

**Cannot be fully automated** - requires understanding of what each error means.

---

## Next Candidates for Application

### Immediate (Similar Patterns)
1. Goal not found errors
2. Subtask not found errors
3. No checkpoint found errors
4. No assessment found errors

### Batch Processing Possible
All "Session not found" patterns are similar - could batch process remaining ones.
All "Invalid alias" patterns are similar - could batch process.

---

## Impact So Far

### Before (Example)
```json
{
  "ok": false,
  "error": "Session not found: abc123"
}
```

### After (Example)
```json
{
  "ok": false,
  "error": "Session not found: abc123",
  "error_type": "session_not_found",
  "reason": "The session ID could not be found in the database",
  "suggestion": "Use 'latest:active:rovodev' alias or bootstrap a new session",
  "alternatives": [
    "bootstrap_session() to create a new session",
    "resume_previous_session(ai_id='rovodev') to load recent session"
  ],
  "recovery_commands": [
    "bootstrap_session(ai_id='your_id', session_type='development', bootstrap_level=2)"
  ],
  "context": {
    "session_id": "abc123"
  }
}
```

**Improvement:** User gets actionable guidance instead of bare error message.

---

## Commits

1. `2d07b56` - Initial error helper + 6 applications
2. `e252b62` - 5 additional applications

---

## Recommendations

### Continue Applying?
**Pros:**
- Improves user experience significantly
- Consistent error handling
- Clear recovery paths

**Cons:**
- Requires semantic reasoning per error (not automatable)
- 37 errors remaining
- Time investment vs other priorities

### Strategy Options
1. **Complete all 48** - Full consistency, best UX
2. **Focus on high-priority** - User-facing errors only
3. **Batch similar patterns** - Session/alias errors done, move to goals/subtasks
4. **Stop here** - 23% coverage, pattern established for future work

### Recommended: Option 3 (Batch Similar Patterns)
Apply to remaining goal/subtask errors (similar patterns), then document template for future errors.

**Estimated:** 10-15 more error points, ~5 iterations

---

**Status:** Paused at 23% coverage, awaiting direction
