# Handoff Summary: Claude → Minimax

**Date:** 2024-11-13  
**Status:** Ready for Autonomous Agent Handoff  

---

## 🎯 Mission Accomplished (Claude)

### Phase 1: Core Infrastructure ✅ COMPLETE

1. **Profile System Created**
   - `empirica/config/investigation_profiles.yaml` (418 lines)
   - `empirica/config/profile_loader.py` (391 lines)
   - 5 profiles: high_reasoning, autonomous, critical, exploratory, balanced

2. **Documentation Complete**
   - `docs/reference/CANONICAL_DIRECTORY_STRUCTURE.md` (827 lines)
   - `docs/reference/ARCHITECTURE_OVERVIEW.md` (862 lines)
   - `docs/reference/INVESTIGATION_PROFILE_SYSTEM_SPEC.md` (847 lines)
   - Old docs archived to `docs/archive/architecture_v2/`

3. **Critical Philosophical Fix ✅**
   - **Removed fake learning heuristics from POSTFLIGHT** (Line 866)
   - **Removed artificial confidence gain calculation** (mcp_aware_investigation.py:390)
   - System now requires **genuine AI reassessment** (no heuristics!)

4. **Analysis & Investigation**
   - 14 anomalies identified and documented
   - 1 database bug fixed (uncertainty columns)
   - Uncertainty reduced: 0.65 → 0.02

**Total Delivered:** 5,538 lines of code and documentation

---

## 🤖 Mission for Minimax: Systematic Refactoring

### Task Overview

**Type:** Mechanical find-and-replace refactoring  
**Difficulty:** Low (well-specified patterns)  
**Time Estimate:** 2-3 hours  
**Risk:** Low (backward compatible)

### What You Need to Do

**Phases 2-6: Replace Hardcoded Constraints**

1. **Phase 2:** Refactor `metacognitive_cascade.py`
   - Update `__init__` to load profiles
   - Replace `self.max_investigation_rounds` → `self.profile.investigation.max_rounds`
   - Replace `self.action_confidence_threshold` → `self.profile.investigation.confidence_threshold`
   - Remove hardcoded `confidence_gain` values (Lines 1367-1497)

2. **Phase 3:** Refactor `canonical_epistemic_assessment.py`
   - Update `_determine_recommended_action()` to use profile thresholds
   - Replace magic numbers (0.80, 0.50, 0.70) with `profile.action_thresholds.*`

3. **Phase 4:** Refactor `investigation_strategy.py`
   - Remove keyword-based domain detection
   - Update `recommend_tools()` to use profile modes

4. **Phase 5:** Update MCP server
   - Add profile parameters to `bootstrap_session` tool

5. **Phase 6:** Update CLI
   - Add `--profile`, `--ai-model`, `--domain` options
   - Add `profile list`, `profile show` commands

### Detailed Instructions

**📖 See:** `docs/MINIMAX_HANDOFF_SYSTEMATIC_REFACTORING.md` (635 lines)

This document contains:
- Exact line numbers
- Before/after code examples
- Validation commands for each step
- Pattern summary (what to find/replace)
- Success criteria

---

## 🔧 Key Patterns to Replace

**Pattern 1: Max Rounds**
```python
# Find:
self.max_investigation_rounds

# Replace:
self.profile.investigation.max_rounds
```

**Pattern 2: Confidence Threshold**
```python
# Find:
self.action_confidence_threshold

# Replace:
self.profile.investigation.confidence_threshold
```

**Pattern 3: Magic Number Thresholds**
```python
# Find:
if uncertainty.score > 0.80:

# Replace:
if uncertainty.score > profile.action_thresholds.uncertainty_high:
```

**Pattern 4: Confidence Gain**
```python
# Find:
'confidence_gain': 0.15

# Replace:
'confidence_gain': 0.0  # No artificial gain
```

---

## ✅ Validation After Each Phase

```bash
# 1. Test imports
python3 -c "from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade; print('✓')"

# 2. Test profile loading
python3 -c "from empirica.config.profile_loader import load_profile; p = load_profile('balanced'); print('✓')"

# 3. Test CASCADE with profile
python3 -c "
import asyncio
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

async def test():
    c = CanonicalEpistemicCascade(profile_name='balanced', enable_session_db=False)
    print(f'✓ Profile: {c.profile.name}')

asyncio.run(test())
"

# 4. Verify no hardcoded constraints remain
grep -n "max_investigation_rounds.*=.*[0-9]" empirica/core/metacognitive_cascade/metacognitive_cascade.py
# Should only find the deprecated parameter definition

# 5. Run unit tests
cd /home/yogapad/empirical-ai/empirica
python3 -m pytest tests/unit/cascade/ -v
```

---

## 📁 Key Files to Modify

1. `empirica/core/metacognitive_cascade/metacognitive_cascade.py`
2. `empirica/core/canonical/canonical_epistemic_assessment.py`
3. `empirica/investigation/investigation_strategy.py`
4. `mcp_local/empirica_mcp_server.py`
5. `empirica/cli/command_handlers/bootstrap_commands.py`

---

## 🎯 Success Criteria

When you're done:

✅ All hardcoded constraints replaced with profile references  
✅ Backward compatibility maintained (deprecation warnings)  
✅ All unit tests pass  
✅ Can initialize CASCADE with different profiles  
✅ Profile selection works (by AI model, domain, explicit)  
✅ No grep matches for hardcoded magic numbers  
✅ Validation commands all succeed  

---

## 🤝 Handoff Back to Claude

After completing Phases 2-6:

1. **Report what was changed** (list of files)
2. **Show validation results** (all tests passing)
3. **Note any issues** encountered
4. **Ready for Claude** to review and proceed with Phases 7-9 (testing, docs, dashboard)

---

## 📚 Reference Documents

1. **Detailed Instructions:** `docs/MINIMAX_HANDOFF_SYSTEMATIC_REFACTORING.md`
2. **Implementation Spec:** `docs/reference/INVESTIGATION_PROFILE_SYSTEM_SPEC.md`
3. **Profile Configuration:** `empirica/config/investigation_profiles.yaml`
4. **Profile Loader Code:** `empirica/config/profile_loader.py`

---

## 💡 Tips for Minimax

- **Work systematically** - One phase at a time
- **Test after each phase** - Don't wait until the end
- **Use grep liberally** - Find all instances of patterns
- **Check the spec** - All answers are in the detailed handoff doc
- **Maintain backward compatibility** - Deprecation warnings, not breaking changes

---

## Questions During Work?

**If ambiguous:**
1. Check `docs/MINIMAX_HANDOFF_SYSTEMATIC_REFACTORING.md` (most detailed)
2. Check `docs/reference/INVESTIGATION_PROFILE_SYSTEM_SPEC.md` (architectural context)
3. Default to `balanced` profile for fallback cases

---

**Good luck, Minimax! This is well-specified, systematic work. You've got this! 🚀**

---

## Status Tracking

- [ ] Phase 2: Metacognitive Cascade refactored
- [ ] Phase 3: Canonical Assessment refactored
- [ ] Phase 4: Investigation Strategy refactored
- [ ] Phase 5: MCP Server updated
- [ ] Phase 6: CLI updated
- [ ] All validations passing
- [ ] Ready for Claude review

