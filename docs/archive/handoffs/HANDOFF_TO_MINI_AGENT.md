# Handoff to Mini-Agent

**From:** Rovo Dev (Session 126d5c66)  
**To:** Mini-Agent  
**Date:** 2025-01-XX  
**Status:** Ready for execution

---

## 🎯 What's Done

✅ **Goal 1: Cleanup & Testing (100% complete)**
- Removed session-end command duplication
- Unified preflight/postflight parameters (both use `reasoning`)
- Created MCP tool validation tests
- **Tests are passing!** ✅

✅ **System Prompt Optimization**
- Created development-focused prompts
- Deployed to both Rovo Dev and Mini-Agent
- 52-64% token savings

✅ **Architecture Definition**
- Created `AI_VS_AGENT_EMPIRICA_PATTERNS.md`
- Defined AI (collaborative) vs Agent (acting) patterns
- Clear CASCADE usage for each role

---

## 📋 What Remains: Goal 2 (9 subtasks, 3-4 hours)

**Goal ID:** `e23d45b1-b865-484e-b107-2571e8dc3dde`  
**Status:** 1/10 complete (10%)  
**Your Task:** Review and update 9 main documentation files

### Subtasks (in priority order):

**Priority 1: User-Facing Start Docs**
1. ⏳ `00_START_HERE.md` - Add AI vs Agent distinction
2. ⏳ `01_a_AI_AGENT_START.md` - Remove session-end, add MCP guidance
3. ⏳ `01_b_MCP_AI_START.md` - Verify tool list, add param guidance

**Priority 2: Technical Quickstarts**
4. ⏳ `03_CLI_QUICKSTART.md` - Remove session-end, update postflight
5. ⏳ `04_MCP_QUICKSTART.md` - Verify tools, add governance concept

**Priority 3: Architecture & Troubleshooting**
6. ⏳ `05_ARCHITECTURE.md` - Add AI vs Agent patterns reference
7. ⏳ `06_TROUBLESHOOTING.md` - Add MCP parameter errors section

**Priority 4: Supporting Docs**
8. ⏳ `02_INSTALLATION.md` - Verify no breaking changes
9. ⏳ `ONBOARDING_GUIDE.md` - Ensure consistency

---

## 📚 Reference Materials

**Your Work Package:**
- `MINI_AGENT_WORK_PACKAGE.md` - Complete instructions (Task 3)

**Architecture Reference:**
- `AI_VS_AGENT_EMPIRICA_PATTERNS.md` - AI vs Agent patterns to integrate

**What to Look For in Each Doc:**
1. Remove `session-end` references (use `handoff-create`)
2. Add MCP parameter guidance (see below)
3. Verify CASCADE granularity (per-task, not per-prompt)
4. Add AI vs Agent distinction where appropriate

### Critical MCP Parameters to Add:

```python
# Common errors to prevent:
create_goal(scope="project_wide")  # ✅ enum: task_specific, session_scoped, project_wide
create_goal(success_criteria=["Tests pass"])  # ✅ array, not string
add_subtask(importance="high")  # ✅ NOT epistemic_importance
complete_subtask(task_id="uuid")  # ✅ NOT subtask_id
submit_postflight_assessment(reasoning="...")  # ✅ NOT changes (deprecated alias)
```

---

## 🛠️ How to Execute

### For Each Doc:

1. **Open and read** the file
2. **Search for issues:**
   ```bash
   # Find session-end references
   grep -n "session-end\|session_end" docs/00_START_HERE.md
   
   # Find wrong MCP params
   grep -n "epistemic_importance\|subtask_id" docs/00_START_HERE.md
   ```
3. **Make updates:**
   - Replace `session-end` with `handoff-create`
   - Add MCP parameter guidance if missing
   - Add AI vs Agent reference (link to `AI_VS_AGENT_EMPIRICA_PATTERNS.md`)
4. **Complete subtask:**
   ```bash
   empirica goals-complete-subtask --task-id <TASK_ID> --evidence "Updated doc, removed session-end, added MCP guidance"
   ```

### Subtask IDs:

| File | Task ID |
|------|---------|
| 00_START_HERE.md | `1b5c1be5-ceca-4ae1-a751-c2214e29aa24` |
| 01_a_AI_AGENT_START.md | `0c77b557-4fef-4c78-a79c-1be0d7e52a0e` |
| 01_b_MCP_AI_START.md | `98517669-d270-4d25-a5bd-6ae2e3ede689` |
| 02_INSTALLATION.md | `5e49c692-135e-40dd-9ba9-a5e2a533b0f6` |
| 03_CLI_QUICKSTART.md | `cb9b8fed-259e-4d28-95bd-a0ed6e044d0e` |
| 04_MCP_QUICKSTART.md | `8a229888-54e5-4cef-a319-3baae16d867b` |
| 05_ARCHITECTURE.md | `c7bc8395-14ce-4555-b625-869292f20060` |
| 06_TROUBLESHOOTING.md | `eac07ded-4005-414a-8a57-3e84cc103549` |
| ONBOARDING_GUIDE.md | `e1b1a0b1-0c5b-467c-96af-b89f65802fa4` |

---

## ✅ Success Criteria

**When you're done:**
- [ ] All 9 subtasks marked complete
- [ ] No `session-end` references remain: `grep -r "session-end" docs/*.md` returns empty
- [ ] MCP parameter guidance added consistently
- [ ] AI vs Agent concepts integrated
- [ ] All docs are consistent

---

## 💡 Quick Tips

**Don't overthink it:**
- This is cleanup work, not new architecture
- Follow the patterns in `MINI_AGENT_WORK_PACKAGE.md` Task 3
- Reference `AI_VS_AGENT_EMPIRICA_PATTERNS.md` for wording
- Use simplified CASCADE (ACT-focused) - no need for full PREFLIGHT/POSTFLIGHT

**If you get stuck:**
- Check `MINI_AGENT_WORK_PACKAGE.md` for detailed instructions
- Look at `AI_VS_AGENT_EMPIRICA_PATTERNS.md` for examples
- Search for patterns in other updated docs

**Estimated time:** 3-4 hours (20-30 min per doc)

---

## 📊 Context from Session 126d5c66

**What we discovered:**
- session-end was duplicate of handoff-create (removed)
- preflight/postflight used different param names (unified to `reasoning`)
- System prompts too verbose (optimized to 770 words)
- AI vs Agent distinction needed clear definition (created patterns)
- MCP tool parameters were causing errors (added guidance)

**What changed:**
- 6 code files modified
- 7 documentation files created
- 2 configs updated (both using dev compact prompt now)
- Tests passing (you completed this!)

**Epistemic Delta:**
- KNOW: +0.05, DO: +0.10, COMPLETION: +0.15
- UNCERTAINTY: -0.15 (very low remaining)
- Calibration: GOOD ✅

---

## 🚀 You're Ready!

Everything you need is prepared. Just work through the 9 docs systematically, complete each subtask, and you're done!

**Questions?** Check the work package or reference docs above.

**Good luck!** 🎉
