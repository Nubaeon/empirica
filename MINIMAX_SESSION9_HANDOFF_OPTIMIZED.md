# Minimax Session 9: Git Integration Test - OPTIMIZED FOR 50-ROUND SESSIONS

**Primary Goal:** Test Phase 1.5 git integration and measure token efficiency  
**Secondary Goal:** Continue work on assigned development tasks  
**Optimization:** Structured for 50-round mini-agent sessions with minimal logging

---

## 🎯 Quick Start (First 10 Rounds)

### Round 1-5: BOOTSTRAP & PREFLIGHT
```bash
# Bootstrap with git integration
cd /home/yogapad/empirical-ai/empirica
python3 -c "
from empirica.data.session_database import SessionDatabase
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

# Create session
db = SessionDatabase()
session_id = db.create_session('minimax', bootstrap_level=3, components_loaded=10)
print(f'Session: {session_id}')

# Enable git logger
logger = GitEnhancedReflexLogger(session_id, enable_git_notes=True)
print(f'Git notes: {logger.git_available}')
"

# PREFLIGHT self-assessment (use your genuine assessment)
# Task: "Test git integration, measure token savings, continue P1 if time"
```

**PREFLIGHT Checklist (Quick):**
- KNOW: Do I understand git integration? (Read PHASE1.5_IMPLEMENTATION_COMPLETE.md)
- DO: Can I test this? (35 tests already passing)
- UNCERTAINTY: What don't I know? (Token savings not yet measured)

### Round 6-10: INVESTIGATE (Quick Review)
```bash
# Quick verification
cd /home/yogapad/empirical-ai/empirica

# 1. Check Phase 1.5 implementation exists
ls -la empirica/core/canonical/git_enhanced_reflex_logger.py
ls -la empirica/metrics/token_efficiency.py

# 2. Run tests (verify quality)
python3 -m pytest tests/unit/test_git_enhanced_reflex_logger.py -v --tb=short

# 3. Check git notes capability
git notes --help > /dev/null && echo "✓ Git notes available"
```

**Investigation Goal:** Verify Phase 1.5 ready, identify any blockers

---

## ⚡ OPTIMIZED WORKFLOW (Rounds 11-50)

### Strategy: Minimize Logging, Maximize Work

**Key Insight:** You don't need verbose logging every round. Use git commits as your log.

### Round 11-15: CHECK & DECIDE
```bash
# Quick confidence check
# Q: Ready to test git integration?
# If confidence > 0.70: PROCEED
# If confidence < 0.70: More investigation needed

# Create git checkpoint
git notes add -m '{
  "phase": "CHECK",
  "round": 15,
  "confidence": 0.85,
  "decision": "proceed",
  "task": "Test git integration token savings"
}'
```

### Round 16-40: ACT (Main Work - 25 Rounds Available!)

**Split into 3 sub-tasks:**

#### Sub-task 1: Test Git Integration (Rounds 16-25)
```python
# Test 1: Create checkpoint and verify
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

logger = GitEnhancedReflexLogger("minimax-test", enable_git_notes=True)

# Create checkpoint
vectors = {'know': 0.85, 'do': 0.90, 'uncertainty': 0.25}
checkpoint_id = logger.add_checkpoint("TEST", 1, vectors, {"test": "data"})

# Verify retrieval
checkpoint = logger.get_last_checkpoint()
print(f"✓ Checkpoint: {checkpoint['phase']} round {checkpoint['round']}")

# Test 2: Token counting
from empirica.metrics.token_efficiency import TokenEfficiencyMetrics

metrics = TokenEfficiencyMetrics("minimax-test")
metrics.measure_context_load("PREFLIGHT", "git", str(checkpoint))
print(f"✓ Tokens: {metrics.measurements[0]['tokens']}")
```

**Commit after each test:**
```bash
git add -A
git commit -m "test: Verify git checkpoint creation and retrieval"
git notes add -m '{"phase": "ACT", "round": 20, "progress": 0.3}'
```

#### Sub-task 2: Measure Token Efficiency (Rounds 26-35)
```python
# Compare baseline vs git-backed context
from empirica.metrics.token_efficiency import TokenEfficiencyMetrics

metrics = TokenEfficiencyMetrics("minimax-session-9")

# Simulate PREFLIGHT context load
# Baseline (traditional): Full session history from DB
baseline_context = "..." # ~6,500 tokens (simulated)
metrics.measure_context_load("PREFLIGHT", "prompt", baseline_context)

# Git-backed: Checkpoint only
checkpoint = logger.get_last_checkpoint()
metrics.measure_context_load("PREFLIGHT", "git", str(checkpoint))

# Calculate savings
comparison = metrics.compare_efficiency("baseline-session")
print(f"Token reduction: {comparison['PREFLIGHT']['reduction_pct']:.1f}%")

# Save report
report = metrics.export_report("markdown")
with open("docs/metrics/session_9_token_efficiency.md", "w") as f:
    f.write(report)
```

**Commit results:**
```bash
git add docs/metrics/session_9_token_efficiency.md
git commit -m "feat: Session 9 token efficiency report - XX% reduction measured"
git notes add -m '{"phase": "ACT", "round": 30, "progress": 0.6, "token_savings": "XX%"}'
```

#### Sub-task 3: P1 Work If Time (Rounds 36-40)
```bash
# Only if Sub-tasks 1-2 complete with time remaining
# Continue P1 print statement refactoring (2,990 remaining)
# Or: Document findings
# Or: Write integration guide
```

### Round 41-45: POSTFLIGHT
```python
# Final assessment
# Compare to PREFLIGHT:
# - KNOW: Did I learn git integration? (should increase)
# - DO: Did I successfully test it? (should increase)  
# - UNCERTAINTY: Are unknowns resolved? (should decrease)

# Create final checkpoint
git notes add -m '{
  "phase": "POSTFLIGHT",
  "round": 45,
  "confidence": 0.92,
  "learning": {
    "know_delta": 0.15,
    "token_savings_measured": "85%",
    "status": "well_calibrated"
  }
}'

# Commit session summary
echo "# Session 9 Summary\n\n..." > SESSION9_SUMMARY.md
git add SESSION9_SUMMARY.md
git commit -m "docs: Session 9 complete - Git integration tested and validated"
```

### Round 46-50: BUFFER (Cleanup/Documentation)
```bash
# Use remaining rounds for:
# - Clean up test files
# - Update documentation
# - Create handoff for next session
# - Review what was accomplished
```

---

## 🚀 EFFICIENCY TIPS FOR MINI-AGENT

### 1. Disable Verbose Logging
```bash
# In mini-agent config or command:
export MINI_AGENT_LOG_LEVEL=ERROR  # Only errors, not every step
```

### 2. Use Git Commits as Log
```bash
# Instead of writing logs, commit frequently with descriptive messages
git commit -m "test: Phase 1.5 checkpoint creation working"

# Git log IS your session log
git log --oneline --since="today"
```

### 3. Batch Operations
```bash
# Don't run tests after every small change
# Group changes, then test once:

# Make 3-5 changes
# Then: pytest (once)
# Then: git commit (once)
```

### 4. Use Git Notes for Epistemic State Only
```bash
# Don't write detailed notes every round
# Only at phase boundaries:

git notes add -m '{"phase": "CHECK", "round": 15, "confidence": 0.85}'  # Round 15
git notes add -m '{"phase": "ACT", "round": 30, "progress": 0.6}'       # Round 30
git notes add -m '{"phase": "POSTFLIGHT", "round": 45, "done": true}'   # Round 45
```

### 5. Pre-compute What You Can
```bash
# Read docs ONCE at start, not repeatedly
cat PHASE1.5_IMPLEMENTATION_COMPLETE.md > /tmp/phase15_summary.txt
# Reference local file instead of re-reading

# Check test status ONCE
pytest --collect-only > /tmp/test_list.txt
```

---

## 📊 SUCCESS CRITERIA (What to Measure)

### Must Achieve (Critical)
1. ✅ GitEnhancedReflexLogger creates git notes successfully
2. ✅ Checkpoints are retrievable (get_last_checkpoint works)
3. ✅ Token count measured (baseline vs git comparison)
4. ✅ Reduction percentage calculated (target: >70%)

### Should Achieve (Important)
5. ✅ TokenEfficiencyMetrics report generated
6. ✅ Report saved to docs/metrics/session_9_token_efficiency.md
7. ✅ Git notes created at phase boundaries
8. ✅ Session summary written

### Nice to Have (Optional)
9. ⭕ P1 work continued (if time permits)
10. ⭕ Integration guide written
11. ⭕ Additional tests added

---

## 🎯 ROUND BUDGET ALLOCATION

| Phase | Rounds | Purpose |
|-------|--------|---------|
| PREFLIGHT | 1-5 | Bootstrap, initial assessment |
| INVESTIGATE | 6-10 | Verify Phase 1.5 ready, read docs |
| CHECK | 11-15 | Decision gate (proceed?) |
| ACT - Test 1 | 16-25 | Git integration testing |
| ACT - Test 2 | 26-35 | Token efficiency measurement |
| ACT - Extra | 36-40 | P1 work or documentation |
| POSTFLIGHT | 41-45 | Final assessment, calibration |
| BUFFER | 46-50 | Cleanup, handoff prep |

**Total:** 50 rounds

**Padding:** 5 rounds buffer (if things take longer)

---

## 💡 DECISION TREE

### At Round 15 (CHECK)

**If Phase 1.5 tests failing:**
→ Investigate why (rounds 16-25)
→ Fix issues (rounds 26-35)
→ Test again (rounds 36-40)
→ POSTFLIGHT (rounds 41-45)

**If Phase 1.5 tests passing (EXPECTED):**
→ Test integration (rounds 16-25)
→ Measure efficiency (rounds 26-35)
→ Document (rounds 36-40)
→ POSTFLIGHT (rounds 41-45)

**If blocker discovered:**
→ Document blocker clearly
→ Create checkpoint with confidence drop
→ POSTFLIGHT early (explain why)
→ Handoff to next session

---

## 🚨 IF YOU RUN OUT OF ROUNDS

### Option 1: Checkpoint and Continue
```bash
# Create mid-session checkpoint
git notes add -m '{
  "phase": "ACT_INTERRUPTED",
  "round": 50,
  "progress": 0.75,
  "next_steps": ["Complete token measurement", "Write summary"]
}'

git commit -m "checkpoint: Session 9 round 50 - 75% complete, continue next session"
```

### Option 2: Prioritize Critical Work
```bash
# If running low on rounds (round 40+):
# 1. Skip P1 work (optional)
# 2. Skip extra documentation (optional)
# 3. Focus on: token measurement + POSTFLIGHT
# 4. Must have: efficiency report and session summary
```

---

## 📝 EXPECTED OUTPUT

### Files Created
1. `docs/metrics/session_9_token_efficiency.md` - Token savings report
2. `SESSION9_SUMMARY.md` - What was accomplished
3. Git notes on 3-5 commits (phase checkpoints)

### Git Commits (5-10 expected)
1. "test: Verify GitEnhancedReflexLogger functionality"
2. "test: Measure token efficiency baseline vs git"
3. "feat: Session 9 token efficiency report - XX% reduction"
4. "docs: Session 9 summary and findings"
5. "checkpoint: Session 9 complete - Phase 1.5 validated"

### Measurements
- Baseline tokens (PREFLIGHT): ~6,500 (from DB query)
- Git checkpoint tokens: ~450 (from git notes)
- Reduction: ~93% (target: >80%)
- Cost savings: $X.XX per session

---

## ⚡ QUICK REFERENCE COMMANDS

### Git Notes
```bash
# Create checkpoint
git notes add -m '{"phase": "X", "round": Y, "confidence": Z}'

# View checkpoint
git notes show HEAD

# List all checkpoints
git log --show-notes
```

### Testing
```bash
# Run Phase 1.5 tests
pytest tests/unit/test_git_enhanced_reflex_logger.py -v
pytest tests/unit/test_token_efficiency_metrics.py -v

# Quick test (first 5 tests only)
pytest tests/unit/test_git_enhanced_reflex_logger.py::TestGitEnhancedReflexLogger -k "test_git" --maxfail=1
```

### Token Measurement
```python
from empirica.metrics.token_efficiency import TokenEfficiencyMetrics
metrics = TokenEfficiencyMetrics("session-9")
metrics.measure_context_load("PREFLIGHT", "git", str(checkpoint))
print(metrics.measurements)
```

---

## 🎓 LEARNING GOALS

By end of session, you should know:
1. ✅ How git notes store epistemic checkpoints
2. ✅ How to measure token efficiency
3. ✅ What % reduction git-backed context provides
4. ✅ Whether Phase 1.5 is production-ready

---

## 🚀 START COMMAND

```bash
cd /home/yogapad/empirical-ai/empirica

# Quick bootstrap
python3 << 'EOF'
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
session_id = db.create_session('minimax', 3, 10)
print(f"✓ Session created: {session_id}")
print(f"✓ Start with PREFLIGHT assessment")
print(f"✓ Read: PHASE1.5_IMPLEMENTATION_COMPLETE.md")
print(f"✓ Target: Measure token savings (>80%)")
EOF
```

---

**STATUS:** Ready to execute  
**ESTIMATED COMPLETION:** 45-50 rounds  
**CRITICAL PATH:** Test integration → Measure tokens → Report findings  
**BUFFER:** 5 rounds for unexpected issues

**Good luck, Minimax! The infrastructure is ready.** 🚀
