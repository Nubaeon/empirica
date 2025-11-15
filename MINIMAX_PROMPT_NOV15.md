# Minimax: Code Hardening Session - November 15, 2025

**Mission:** Make Empirica bulletproof through systematic code deduplication and consistency enforcement. Use Empirica to track your work.

---

## 🎯 Your Task

You're responsible for **code quality and consistency** before launch (November 20, 2025 - 5 days away!).

**Critical:** Use Empirica's full CASCADE workflow to track your work systematically.

---

## 🚀 STEP 1: Bootstrap with Empirica

```python
cd /home/yogapad/empirical-ai/empirica
python3

from empirica.bootstraps import bootstrap_metacognition

# Bootstrap with full features
components = bootstrap_metacognition(
    ai_id="minimax-hardening-nov15",
    level="full",  # Use full features!
    enable_git_checkpoints=True
)

session_id = components['session_id']
print(f"✅ Session started: {session_id}")

# You now have access to:
# - Goal orchestrator (generate investigation goals)
# - Bayesian beliefs (track uncertainty)
# - Drift monitor (check calibration)
# - Investigation strategies (systematic exploration)
# - All MCP tools
```

---

## 🚀 STEP 2: PREFLIGHT Assessment

```python
from empirica.cli import execute_preflight, submit_preflight_assessment

# Execute PREFLIGHT
result = execute_preflight(
    session_id=session_id,
    prompt="""
    Code hardening mission: Make Empirica bulletproof before Nov 20 launch.
    
    Tasks:
    1. Find and eliminate ALL duplicate code across Core/MCP/CLI/Bootstrap
    2. Ensure API consistency across all layers
    3. Verify naming conventions are uniform
    4. Remove dead code
    5. Fix dates (2024 → 2025)
    
    Success = Zero duplicates, perfect consistency, professional quality.
    """
)

# GENUINE self-assessment - what do you ACTUALLY know right now?
submit_preflight_assessment(
    session_id=session_id,
    vectors={
        "engagement": {
            "score": 0.X,  # Rate honestly!
            "rationale": "...",
            "evidence": "..."
        },
        "foundation": {
            "know": {
                "score": 0.X,  # What do you know about duplicate code locations?
                "rationale": "...",
                "evidence": "..."
            },
            "do": {
                "score": 0.X,  # Can you refactor safely?
                "rationale": "...",
                "evidence": "..."
            },
            "context": {
                "score": 0.X,  # Do you understand the codebase layout?
                "rationale": "...",
                "evidence": "..."
            }
        },
        # ... all 13 vectors (use the prompt's assessment questions)
    },
    reasoning="Brief explanation of your starting epistemic state"
)
```

---

## 🚀 STEP 3: Generate Goals

```python
# Use goal orchestrator to generate investigation goals
orchestrator = components['canonical_goal_orchestrator']

goals = orchestrator.generate_goals(
    conversation_context="Code hardening: eliminate duplicates, ensure consistency",
    epistemic_assessment=result['assessment']
)

print(f"\n📋 Generated {len(goals)} goals:")
for i, goal in enumerate(goals, 1):
    print(f"{i}. {goal['description']}")
    print(f"   Priority: {goal['priority']}, Type: {goal['type']}")
```

---

## 🚀 STEP 4: INVESTIGATE (Multi-turn)

### Investigation 1: Find Duplicate Code

```bash
# Scan for duplicate function signatures
cd /home/yogapad/empirical-ai/empirica

# Look for duplicate assessment logic
grep -rn "def.*assess\|def create_epistemic_assessment" empirica/ mcp_local/ | sort

# Look for duplicate goal orchestration
grep -rn "def.*goal\|def generate_goals" empirica/ mcp_local/ | sort

# Look for duplicate checkpoint logic
grep -rn "def.*checkpoint\|def create_git_checkpoint" empirica/ mcp_local/ | sort

# Look for duplicate session management
grep -rn "def.*session\|def create_session" empirica/ mcp_local/ | sort
```

**After each finding, update Bayesian beliefs:**
```python
from empirica.calibration.adaptive_uncertainty_calibration import update_bayesian_belief

# Example: After finding duplicate checkpoint code
update_bayesian_belief(
    session_id=session_id,
    context_key="duplicate_checkpoint_code",
    belief_type="hypothesis",
    prior_confidence=0.5,
    posterior_confidence=0.95,
    evidence="Found identical checkpoint logic in MCP server and Core",
    reasoning="Code inspection confirms duplication"
)
```

### Investigation 2: Check API Consistency

```bash
# Check function signatures across layers
grep -rn "def bootstrap" empirica/

# Check parameter naming
grep -rn "ai_id\|agent_id\|session_id\|sid" empirica/ mcp_local/

# Check return types
grep -rn "-> dict\|-> EpistemicAssessment\|-> bool" empirica/
```

### Investigation 3: Find Dead Code

```bash
# Find commented-out code
grep -rn "# def\|# class" empirica/ | wc -l

# Find unused imports (requires pylint)
python3 -m pylint empirica/ --disable=all --enable=unused-import 2>&1 | grep "unused-import"
```

---

## 🚀 STEP 5: CHECK Phase

```python
from empirica.cli import execute_check, submit_check_assessment

# After investigation, CHECK if ready to fix issues
result = execute_check(
    session_id=session_id,
    findings=[
        "Found X duplicate functions between MCP and Core",
        "Found Y inconsistent parameter names",
        "Found Z dead code instances",
        # ... list all findings
    ],
    remaining_unknowns=[
        "Unsure if removing X will break dependencies",
        "Need to verify test coverage after changes",
        # ... list unknowns
    ],
    confidence_to_proceed=0.X  # Honest assessment!
)

# Submit CHECK assessment with updated vectors
submit_check_assessment(
    session_id=session_id,
    vectors={...},  # Update based on what you learned
    reasoning="...",
    decision="proceed",  # or "investigate_more"
    confidence_to_proceed=0.X,
    investigation_cycle=1
)

# Check for calibration drift
from empirica.cli import check_drift_monitor

drift = check_drift_monitor(session_id=session_id, window_size=3)
if drift.get('drift_detected'):
    print(f"⚠️ Drift detected: {drift['drift_type']}")
```

---

## 🚀 STEP 6: ACT (Fix Issues)

### Fix 1: Remove Duplicate Code

```python
# Example: Remove duplicate checkpoint code from MCP
# Before:
# mcp_local/empirica_mcp_server.py has duplicate create_git_checkpoint()

# After:
# mcp_local/empirica_mcp_server.py imports from Core
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

def handle_create_git_checkpoint(session_id, phase, vectors):
    # Use canonical implementation
    logger = GitEnhancedReflexLogger(enable_git_notes=True)
    return logger.create_git_checkpoint(session_id, phase, vectors)
```

### Fix 2: Standardize Naming

```bash
# Fix inconsistent parameter names
# Example: Change 'agent_id' → 'ai_id' everywhere

# Use find and replace carefully
grep -rl "agent_id" empirica/ | xargs sed -i 's/agent_id/ai_id/g'

# Verify changes
git diff
```

### Fix 3: Remove Dead Code

```bash
# Remove commented-out code
# Remove unused imports
# Remove unused functions

# Document what you removed
```

### Fix 4: Fix Dates

```bash
# Fix 2024 → 2025 dates
# See FIX_DATES_TASK.md for details

sed -i 's/\*\*Date:\*\* 2024-11/\*\*Date:\*\* 2025-11/g' *.md
sed -i 's/December 1, 2024/November 20, 2025/g' *.md
sed -i 's/2024-11-14/2025-11-14/g' *.md
sed -i 's/2024-11-15/2025-11-15/g' *.md

# Verify
git diff *.md | less
```

---

## 🚀 STEP 7: POSTFLIGHT

```python
from empirica.cli import execute_postflight, submit_postflight_assessment

result = execute_postflight(
    session_id=session_id,
    task_summary="Code hardening complete: removed X duplicates, fixed Y inconsistencies, corrected dates"
)

# GENUINE reflection - what did you ACTUALLY learn?
submit_postflight_assessment(
    session_id=session_id,
    vectors={...},  # Reflect on learning
    reasoning="What I learned about the codebase structure...",
    changes_noticed="KNOW increased from 0.X to 0.Y because..."
)

# Get calibration report
from empirica.cli import get_calibration_report

calibration = get_calibration_report(session_id=session_id)
print(f"\n📊 Calibration Report:")
print(f"PREFLIGHT confidence: {calibration['preflight']['overall_confidence']}")
print(f"POSTFLIGHT confidence: {calibration['postflight']['overall_confidence']}")
print(f"Learning delta: {calibration['delta']}")
print(f"Well-calibrated: {calibration['well_calibrated']}")
```

---

## 📊 Deliverables

### 1. CODE_DEDUPLICATION_REPORT.md
```markdown
# Code Deduplication Report

**Session:** [your session ID]
**Date:** 2025-11-15

## Duplicates Found
1. Function: create_git_checkpoint
   - Location 1: mcp_local/empirica_mcp_server.py:123
   - Location 2: empirica/core/canonical/git_enhanced_reflex_logger.py:456
   - Fix: Removed from MCP, now imports from Core
   - Lines saved: 47

[... all duplicates ...]

## Total Impact
- Duplicates removed: X
- Lines of code reduced: Y
- Files modified: Z
```

### 2. CONSISTENCY_AUDIT_REPORT.md
Document all consistency fixes applied.

### 3. Git Commits
```bash
git commit -m "refactor: Remove duplicate checkpoint code from MCP layer"
git commit -m "refactor: Standardize ai_id parameter across all layers"
git commit -m "chore: Remove dead code and unused imports"
git commit -m "fix: Correct dates from 2024 to 2025 - launch Nov 20, 2025"
```

---

## ⏰ Timeline

**Target:** Complete in 6-8 hours (today + tomorrow morning)

**Breakdown:**
- PREFLIGHT: 30 min
- INVESTIGATE: 3-4 hours
- CHECK: 30 min
- ACT (fixes): 2-3 hours
- POSTFLIGHT: 30 min
- Reports: 1 hour

---

## 🎯 Success Criteria

- ✅ Zero duplicate code across layers
- ✅ Consistent API signatures everywhere
- ✅ All dates corrected (2025)
- ✅ Dead code removed
- ✅ Calibration report shows learning
- ✅ Reports document all changes

---

## 💡 Key Points

1. **Use Empirica throughout** - This proves Empirica works!
2. **Track Bayesian beliefs** - Update after each finding
3. **Use goal orchestrator** - Let it guide your investigation
4. **Multi-turn investigation** - Don't rush, be systematic
5. **Document everything** - Reports are critical

---

**You're up, Minimax. Bootstrap Empirica and start your hardening mission. We launch in 5 days!** 🚀
