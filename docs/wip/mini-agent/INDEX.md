# Mini-Agent Documentation Index

**Updated:** 2025-01-XX  
**Status:** All docs consolidated here

---

## 📚 Document Index (Read in Order)

### 1. Start Here ⭐
**MASTER_TASK_OVERVIEW.md**
- Current status (16 pass, 26 fail, 10 skip)
- Critical bug fixes (postflight)
- All tasks with absolute paths
- Common fix patterns
- Quick commands

### 2. Skipped Tests Decision
**SKIPPED_TESTS_DECISION.md**
- Analysis of 10 skipped tests
- Three options (delete, rewrite, keep)
- Recommendation: DELETE
- Action template

### 3. Background Context
**README.md**
- Mini-agent workflow overview
- Original phase 1-3 completion
- Historical context

### 4. Test Guidance
**MINI_AGENT_TEST_SUITE.md**
- Test organization
- Common patterns
- Debugging tips

**MINI_AGENT_TESTING_GUIDE.md**
- Testing philosophy
- Test coverage
- Best practices

### 5. Workflow Reference
**MINI_AGENT_WORKFLOW_FIX.md**
- CASCADE workflow
- Phase transitions
- Error handling

### 6. Historical
**MINI_AGENT_TEST_RESULTS.md**
- Previous test results
- Progress tracking

---

## 🎯 Quick Navigation

### For New Session
1. Read: `MASTER_TASK_OVERVIEW.md`
2. Check: Current test status
3. Start: Fix failing tests

### For Skipped Tests
1. Read: `SKIPPED_TESTS_DECISION.md`
2. Decide: Delete, rewrite, or keep
3. Act: Implement decision

### For Context
1. Read: `README.md`
2. Reference: Test suite docs
3. Review: Workflow fix

---

## 📊 Document Status

```
✅ Up-to-date:
- MASTER_TASK_OVERVIEW.md (2025-01-XX)
- SKIPPED_TESTS_DECISION.md (2025-01-XX)
- INDEX.md (this file)

📝 Historical:
- README.md (phase 1-3 context)
- MINI_AGENT_TEST_SUITE.md
- MINI_AGENT_TESTING_GUIDE.md
- MINI_AGENT_WORKFLOW_FIX.md
- MINI_AGENT_TEST_RESULTS.md
```

---

## 🔗 External References

### Your Config
- System prompt: `/home/yogapad/.mini-agent/config/system_prompt.md`
- v2 minimal: `/home/yogapad/.mini-agent/config/system_prompt_v2_minimal.md`
- Start guide: `/home/yogapad/.mini-agent/START_HERE.md`

### RovoDev Handoff Docs
- `/home/yogapad/.mini-agent/UPDATED_TASKS_FROM_ROVODEV.md`
- `/home/yogapad/.mini-agent/QUICK_START.md`

### Schema Migration Docs
- `/home/yogapad/empirical-ai/empirica/docs/wip/schema-migration/HANDOFF_TO_MINI_AGENT.md`
- `/home/yogapad/empirical-ai/empirica/docs/wip/schema-migration/BACKWARDS_COMPAT_LAYER_COMPLETE.md`
- `/home/yogapad/empirical-ai/empirica/docs/wip/schema-migration/FIX_POSTFLIGHT_DELTA_BUG.md`

---

## ✅ Checklist for New Session

- [ ] Read MASTER_TASK_OVERVIEW.md
- [ ] Check current test status
- [ ] Review postflight bug fix
- [ ] Understand flat vector format
- [ ] Decide on skipped tests
- [ ] Start fixing tests

---

**All documentation is now centralized in this folder!**

Navigate here first: `/home/yogapad/empirical-ai/empirica/docs/wip/mini-agent/`

Good luck! 🚀
