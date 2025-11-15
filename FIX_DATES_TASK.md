# Fix All Dates: 2024 → 2025

**Assigned To:** Minimax OR Qwen (whoever finishes hardening first)  
**Priority:** HIGH - Dates are wrong in documentation  
**Estimated Time:** 30-45 minutes

---

## 🎯 Task

Replace all incorrect 2024 dates with correct 2025 dates throughout documentation.

**Correct dates:**
- Today: **November 15, 2025**
- Launch: **November 20, 2025** (5 days away!)
- Development period: November 2024 → November 2025 (1 year)

---

## 📋 Files to Fix

### Root Files (High Priority)
```bash
cd /home/yogapad/empirical-ai/empirica

# Fix these files:
1. AGENT_WORK_COMPLETE_SUMMARY.md
   - Line 3: 2025-11-15 → 2025-11-15
   - Line 152: 2025-11-14 → 2025-11-14
   - Line 311: November 20, 2025 → November 20, 2025

2. ARCHITECTURE_DECISIONS_2024_11_14.md
   - Filename: Keep as is (historical record)
   - Line 3: 2025-11-14 → 2025-11-14
   - Lines 470, 475: 2025-11-14/15 → 2025-11-14/15

3. CHECKPOINT_SESSION_2024_11_14_COMPLETE.md
   - Filename: Keep as is (historical record)
   - Line 295: 2025-11-14 → 2025-11-14
   - Line 340: 2025-11-14 → 2025-11-14
   - Line 698: 2025-11-14 → 2025-11-14

4. COPILOT_CLAUDE_NEXT_TASKS.md
   - Line 3: 2025-11-14 → 2025-11-14

5. DOCUMENTATION_AUDIT_COMPLETE.md
   - Line 3: 2025-11-14 → 2025-11-14

6. DOCUMENTATION_AUDIT_REPORT.md
   - Lines 1, 4: 2025-11-14 → 2025-11-14

7. DOCUMENTATION_PLAN_V1.md
   - Line 3: 2025-11-15 → 2025-11-15
   - Line 16: November 20, 2025 → November 20, 2025
   - Line 292: 2024-12-01 → 2025-11-20

8. HARDENING_SANITIZATION_TASKS.md
   - Line 3: 2025-11-15 → 2025-11-15

9. MINIMAX_NEXT_STEPS.md
   - Line 3: 2025-11-14 → 2025-11-14

10. SYSTEM_PROMPTS_UPDATED.md
    - Check for any 2024 dates

11. SESSION_COMPLETE_2024_11_14.md
    - Filename: Keep as is (historical)
    - Update internal dates: 2024 → 2025
```

---

## 🔧 How to Fix

### Method 1: Find and Replace (Careful!)
```bash
# DO NOT do blanket replace! Some 2024 dates are historical references.
# Instead, target specific patterns:

# Fix date headers
sed -i 's/\*\*Date:\*\* 2024-11/\*\*Date:\*\* 2025-11/g' *.md

# Fix target dates
sed -i 's/November 20, 2025/November 20, 2025/g' *.md
sed -i 's/2024-12-01/2025-11-20/g' *.md

# Fix recent dates
sed -i 's/2025-11-14/2025-11-14/g' *.md
sed -i 's/2025-11-15/2025-11-15/g' *.md

# Verify changes
git diff *.md | less
```

### Method 2: Manual Review (Safer)
```bash
# Review each file with dates
grep -n "2024" *.md

# Edit each file individually
# Change dates based on context:
# - Session dates: 2024 → 2025
# - Launch date: Dec 1, 2024 → Nov 20, 2025
# - Current dates: 2025-11-14/15 → 2025-11-14/15
```

---

## ⚠️ Important Notes

### DO Change:
- ✅ Current session dates (Nov 14-15, 2024 → 2025)
- ✅ Launch date (Dec 1, 2024 → Nov 20, 2025)
- ✅ Planning timeline dates
- ✅ Status report dates
- ✅ Agent coordination dates

### DO NOT Change (Historical):
- ❌ Commit dates that reference actual git history
- ❌ Dates in archived session notes (they're historical records)
- ❌ Dates in quoted text or examples
- ❌ Dates that are clearly historical references

### When in Doubt:
- Check context: Is this referencing past work or current/future work?
- Past work → Keep as historical reference
- Current/future work → Update to 2025

---

## 📊 Verification

After making changes:

```bash
# 1. Check what was changed
git diff *.md

# 2. Ensure no broken references
grep -n "2024" *.md | grep -v "historical\|archive\|reference"

# 3. Verify launch date is correct
grep -n "launch\|Launch\|LAUNCH" *.md | grep "20"

# Should show: November 20, 2025 (or 2025-11-20)
```

---

## 🎯 Success Criteria

- ✅ All current dates show 2025
- ✅ Launch date shows November 20, 2025
- ✅ No broken references
- ✅ Git diff looks reasonable
- ✅ Historical dates preserved where appropriate

---

## 📝 Deliverable

**Git commit:**
```bash
git add *.md
git commit -m "fix: Correct dates from 2024 to 2025 - launch Nov 20, 2025"
git push origin master
```

**Comment in commit:**
```
Corrected documentation dates:
- Current date: November 15, 2025
- Launch date: November 20, 2025 (5 days away)
- Updated all active documentation
- Preserved historical dates in archived sessions
```

---

## ⏰ Timeline

**Do this:** After completing current hardening/testing task, before final documentation
**Estimated:** 30-45 minutes
**Priority:** HIGH (wrong dates look unprofessional)

---

**Just run through the files and fix the dates. Quick task, important for credibility.** 📅
