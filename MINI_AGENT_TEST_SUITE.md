# Mini-Agent Test Suite: Phase 1 Git Automation

**Date:** 2025-11-27  
**Tester:** mini-agent  
**Focus:** Validate automatic git checkpoints and cross-AI coordination

---

## 🎯 Test Objectives

Validate that Phase 1 implementation works correctly:
1. Automatic git checkpoints during CASCADE
2. Goal storage in git notes
3. Cross-AI goal discovery and resume
4. Safe degradation without git
5. Sentinel hooks are callable

---

## 📋 Pre-Test Setup

```bash
# Ensure you're in a git repository
cd /path/to/empirica
git status  # Should show you're in a repo

# Ensure latest code
git pull origin main

# Create test session
export TEST_SESSION="test-$(date +%s)"
export TEST_AI="mini-agent"
```

---

## ✅ Test Suite

### Test 1: Automatic Checkpoint Creation (CRITICAL)

**Objective:** Verify checkpoints are created automatically during CASCADE

**Steps:**
```bash
# Run preflight
empirica preflight "Test automatic checkpoint creation" --ai-id $TEST_AI --session-id $TEST_SESSION

# Verify checkpoint was created in git notes
git notes --ref=empirica/checkpoints list

# Should see at least one checkpoint
# Show latest checkpoint
LATEST_COMMIT=$(git rev-parse HEAD)
git notes --ref=empirica/checkpoints show $LATEST_COMMIT

# Should display JSON with:
# - session_id
# - ai_id: "mini-agent"
# - phase: "PREFLIGHT"
# - vectors: {...}
```

**Expected Result:**
- ✅ Checkpoint created automatically
- ✅ JSON contains correct session_id and ai_id
- ✅ Vectors are present

**If Fails:**
- Check if in git repo: `git status`
- Check logs: Look for "Git checkpoint created" message
- Try with verbose: `empirica preflight "test" --ai-id test --verbose`

---

### Test 2: Checkpoint with --no-git Flag

**Objective:** Verify --no-git flag disables checkpoints

**Steps:**
```bash
# Get current checkpoint count
BEFORE=$(git notes --ref=empirica/checkpoints list | wc -l)

# Run with --no-git
empirica preflight "Test no-git flag" --ai-id $TEST_AI --no-git

# Check checkpoint count didn't increase
AFTER=$(git notes --ref=empirica/checkpoints list | wc -l)

echo "Before: $BEFORE, After: $AFTER"
# Should be equal
```

**Expected Result:**
- ✅ No new checkpoint created
- ✅ Command still succeeds
- ✅ No errors

---

### Test 3: Goal Storage in Git Notes

**Objective:** Verify goals are stored in git notes automatically

**Steps:**
```bash
# Create a goal
GOAL_OUTPUT=$(empirica goals-create \
  "Test cross-AI goal discovery" \
  --scope task_specific \
  --ai-id $TEST_AI \
  --session-id $TEST_SESSION \
  --output json)

echo "$GOAL_OUTPUT"

# Extract goal_id
GOAL_ID=$(echo "$GOAL_OUTPUT" | jq -r '.goal_id')
echo "Created goal: $GOAL_ID"

# Verify goal in git notes
git notes list | grep "empirica/goals/$GOAL_ID"

# Should see the goal note reference
# Show goal data
LATEST_COMMIT=$(git rev-parse HEAD)
git notes --ref=empirica/goals/$GOAL_ID show $LATEST_COMMIT

# Should display JSON with:
# - goal_id
# - ai_id: "mini-agent"
# - goal_data: {...}
# - lineage: [...]
```

**Expected Result:**
- ✅ Goal appears in git notes
- ✅ JSON contains correct goal data
- ✅ Lineage shows "created" action

**If Fails:**
- Check goal was created: `empirica goals-list --session-id $TEST_SESSION`
- Check git notes: `git notes list`
- Verify in git repo: `git status`

---

### Test 4: Cross-AI Goal Discovery

**Objective:** Verify goals can be discovered by other AIs

**Steps:**
```bash
# Discover goals created by mini-agent
empirica goals-discover --from-ai-id $TEST_AI

# Should list at least one goal (the one we just created)

# Try discovering with no filter
empirica goals-discover

# Should list all goals in git notes
```

**Expected Result:**
- ✅ Goal created in Test 3 is listed
- ✅ Shows correct ai_id, session_id, objective
- ✅ Lineage is displayed

**If Fails:**
- Verify goal was stored: Run Test 3 first
- Check git notes: `git notes list | grep empirica/goals`
- Try with JSON output: `empirica goals-discover --output json`

---

### Test 5: Goal Resume with Lineage

**Objective:** Verify goals can be resumed by different AI with lineage tracking

**Steps:**
```bash
# Resume the goal with a different AI
DIFFERENT_AI="test-agent-2"

empirica goals-resume $GOAL_ID --ai-id $DIFFERENT_AI

# Verify lineage was updated
git notes --ref=empirica/goals/$GOAL_ID show HEAD

# Should see lineage with 2 entries:
# 1. mini-agent - created
# 2. test-agent-2 - resumed
```

**Expected Result:**
- ✅ Resume succeeds
- ✅ Lineage shows both AIs
- ✅ Original AI and new AI both listed

---

### Test 6: Postflight Checkpoint

**Objective:** Verify postflight also creates checkpoints

**Steps:**
```bash
# Run postflight
empirica postflight $TEST_SESSION \
  --ai-id $TEST_AI \
  --summary "Test completed successfully"

# Verify checkpoint was created
LATEST_COMMIT=$(git rev-parse HEAD)
git notes --ref=empirica/checkpoints show $LATEST_COMMIT | jq '.phase'

# Should show "POSTFLIGHT"
```

**Expected Result:**
- ✅ Checkpoint created
- ✅ Phase is "POSTFLIGHT"
- ✅ Contains delta/calibration data

---

### Test 7: Safe Degradation (No Git Repo)

**Objective:** Verify commands work outside git repo

**Steps:**
```bash
# Move to non-git directory
cd /tmp/empirica-test-$$ || mkdir -p /tmp/empirica-test-$$ && cd /tmp/empirica-test-$$

# Run preflight (should work, just skip git)
empirica preflight "Test outside git repo" --ai-id $TEST_AI

# Should succeed without errors
# Check for debug message about skipping git
```

**Expected Result:**
- ✅ Command succeeds
- ✅ No git errors
- ✅ Safe degradation works

**Cleanup:**
```bash
cd /path/to/empirica
rm -rf /tmp/empirica-test-*
```

---

### Test 8: Sentinel Hooks (Python API)

**Objective:** Verify Sentinel hooks can be registered and called

**Steps:**
```bash
# Create test script
cat > /tmp/test_sentinel.py << 'EOF'
from empirica.core.canonical.empirica_git import SentinelHooks, SentinelDecision

# Test evaluator
def test_evaluator(checkpoint_data):
    print(f"Sentinel evaluating: {checkpoint_data.get('phase')}")
    vectors = checkpoint_data.get('vectors', {})
    
    if vectors.get('uncertainty', 0) > 0.8:
        return SentinelDecision.INVESTIGATE
    
    return SentinelDecision.PROCEED

# Register
SentinelHooks.register_evaluator(test_evaluator)

# Test evaluation
test_checkpoint = {
    'session_id': 'test',
    'ai_id': 'test',
    'phase': 'PREFLIGHT',
    'vectors': {'uncertainty': 0.9}
}

decision = SentinelHooks.evaluate_checkpoint(test_checkpoint)
print(f"Decision: {decision}")

assert decision == SentinelDecision.INVESTIGATE, "Should return INVESTIGATE"
print("✓ Sentinel hooks working correctly")
EOF

python3 /tmp/test_sentinel.py

# Should print:
# Sentinel evaluating: PREFLIGHT
# Decision: SentinelDecision.INVESTIGATE
# ✓ Sentinel hooks working correctly
```

**Expected Result:**
- ✅ Evaluator can be registered
- ✅ Returns correct decision
- ✅ No errors

---

## 📊 Test Results Summary

**Create this section after running tests:**

```
Test Results:
├─ Test 1: Automatic Checkpoint      [ PASS / FAIL ]
├─ Test 2: --no-git Flag              [ PASS / FAIL ]
├─ Test 3: Goal Storage               [ PASS / FAIL ]
├─ Test 4: Goal Discovery             [ PASS / FAIL ]
├─ Test 5: Goal Resume                [ PASS / FAIL ]
├─ Test 6: Postflight Checkpoint      [ PASS / FAIL ]
├─ Test 7: Safe Degradation           [ PASS / FAIL ]
└─ Test 8: Sentinel Hooks             [ PASS / FAIL ]

Overall: X/8 tests passed
```

---

## 🐛 Common Issues & Fixes

### Issue 1: "Not in git repository"
**Fix:** Ensure you're in a git repo: `git status`

### Issue 2: "Permission denied" on git notes
**Fix:** Check git config: `git config notes.rewrite.refs`

### Issue 3: "Module not found"
**Fix:** Reinstall empirica: `pip install -e .`

### Issue 4: Checkpoints not appearing
**Fix:** 
- Check you didn't use --no-git flag
- Verify in git repo
- Look for debug messages

### Issue 5: Goals not discoverable
**Fix:**
- Verify goal was stored: `git notes list | grep empirica/goals`
- Try: `git fetch` to pull latest goals from remote

---

## 📝 Report Format

**Please create a report with:**

1. **Environment:**
   - OS: [Linux/Mac/Windows]
   - Python version: [3.x]
   - Git version: [x.x]
   - In git repo: [Yes/No]

2. **Test Results:** (Use table above)

3. **Issues Found:** 
   - Description
   - Steps to reproduce
   - Error messages
   - Screenshots if applicable

4. **Recommendations:**
   - What worked well
   - What needs fixing
   - Suggestions for improvement

---

## ✅ Success Criteria

Phase 1 is considered VALIDATED if:
- [ ] 7/8 tests pass (Test 7 is optional if always in git)
- [ ] Checkpoints created automatically
- [ ] Goals discoverable cross-AI
- [ ] Sentinel hooks callable
- [ ] Safe degradation works

---

## 🚀 Next Steps After Testing

**If All Tests Pass:**
- Merge Phase 1 to main
- Begin Phase 2 (Cryptographic trust)
- Integrate with cognitive_vault Sentinel

**If Some Tests Fail:**
- Document failures
- Create fix plan
- Re-test after fixes

---

**Estimated Testing Time:** 15-20 minutes  
**Tester:** mini-agent  
**Report Due:** After completion  
**Format:** Markdown or JSON

---

*Generated: 2025-11-27*  
*Phase: 1 Validation*  
*Status: Ready for Testing*
