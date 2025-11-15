# Minimax Session 9: Git Integration Test

**Objective:** Test Phase 1.5 git integration and validate 80-90% token reduction hypothesis.

**Date:** 2025-11-15  
**Status:** Ready for Testing  
**Prerequisites:** Phase 1.5 implementation complete

---

## 🎯 Mission

Validate that git-backed context retrieval achieves **80-90% token reduction** compared to prompt-based context loading.

**Success Criteria:**
- ✅ Token reduction ≥ 80% across full workflow
- ✅ Checkpoints stored in git notes successfully
- ✅ Vector diffs calculated correctly
- ✅ SQLite fallback works when needed
- ✅ TokenEfficiencyMetrics generates accurate reports

---

## 📋 Modified Workflow

### PREFLIGHT Phase

**Standard Workflow (Baseline - DO NOT USE):**
```python
# Old way: Load full session history (~6,500 tokens)
session_history = db.get_session_history(session_id)
# ... perform assessment with full context ...
```

**Git-Enhanced Workflow (NEW - USE THIS):**
```python
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
from empirica.metrics.token_efficiency import TokenEfficiencyMetrics

# Initialize git-enhanced logger
git_logger = GitEnhancedReflexLogger(
    session_id="minimax-session-9",
    enable_git_notes=True
)

# Initialize metrics tracker
metrics = TokenEfficiencyMetrics(session_id="minimax-session-9")

# Load compressed checkpoint instead of full history (~450 tokens)
checkpoint = git_logger.get_last_checkpoint(max_age_hours=24)

if checkpoint:
    print(f"✓ Loaded checkpoint: {checkpoint['phase']} round {checkpoint['round']}")
    print(f"✓ Token count: {checkpoint['token_count']}")
    
    # Measure token efficiency
    metrics.measure_context_load(
        phase="PREFLIGHT",
        method="git",
        content=json.dumps(checkpoint),
        content_type="checkpoint"
    )
else:
    print("No recent checkpoint, starting fresh")

# Perform self-assessment as normal
assessment = {
    "know": 0.75,
    "do": 0.80,
    "context": 0.70,
    "uncertainty": 0.35,
    # ... other vectors ...
}

# Create checkpoint
git_logger.add_checkpoint(
    phase="PREFLIGHT",
    round_num=1,
    vectors=assessment,
    metadata={"task": "your task description"}
)

print("✓ PREFLIGHT checkpoint created")
```

---

### CHECK Phase

**Git-Enhanced Workflow:**
```python
# Load vector diff instead of full history (~400 tokens vs ~3,500)
last_checkpoint = git_logger.get_last_checkpoint()

if last_checkpoint:
    # Get only what changed
    vector_diff = git_logger.get_vector_diff(
        since_checkpoint=last_checkpoint,
        current_vectors=current_assessment_vectors
    )
    
    print(f"✓ Vector diff calculated: {len(vector_diff['significant_changes'])} significant changes")
    
    # Measure efficiency
    metrics.measure_context_load(
        phase="CHECK",
        method="git",
        content=json.dumps(vector_diff),
        content_type="diff"
    )

# Make decision
decision = "proceed"  # or "investigate", "clarify", etc.

# Create checkpoint
git_logger.add_checkpoint(
    phase="CHECK",
    round_num=3,
    vectors=current_vectors,
    metadata={"decision": decision}
)
```

---

### ACT Phase

**Git-Enhanced Workflow:**
```python
# Make changes and commit
# ... your code changes ...

# Commit changes to git
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "feat: your changes"], check=True)

# Add checkpoint to the commit
git_logger.add_checkpoint(
    phase="ACT",
    round_num=5,
    vectors={"know": 0.85, "do": 0.90},
    metadata={
        "files_changed": ["file1.py", "file2.py"],
        "action": "implemented feature X"
    }
)

# Measure (estimated based on checkpoint size)
metrics.measure_context_load(
    phase="ACT",
    method="git",
    content=json.dumps(git_logger.get_last_checkpoint()),
    content_type="checkpoint"
)
```

---

### POSTFLIGHT Phase

**Git-Enhanced Workflow:**
```python
# Load initial checkpoint for comparison
initial_checkpoint = git_logger.get_last_checkpoint(phase="PREFLIGHT")

# Calculate epistemic delta
if initial_checkpoint:
    initial_vectors = initial_checkpoint["vectors"]
    final_vectors = {
        "know": 0.90,
        "do": 0.92,
        "uncertainty": 0.20,
        # ...
    }
    
    epistemic_delta = {
        k: round(final_vectors.get(k, 0) - initial_vectors.get(k, 0), 3)
        for k in final_vectors
    }
    
    print("Epistemic Growth:")
    for vector, delta in epistemic_delta.items():
        if abs(delta) > 0.15:
            print(f"  {vector}: {delta:+.2f} ({'📈' if delta > 0 else '📉'})")

# Create final checkpoint
git_logger.add_checkpoint(
    phase="POSTFLIGHT",
    round_num=10,
    vectors=final_vectors,
    metadata={"summary": "session complete"}
)

# Measure POSTFLIGHT token usage
metrics.measure_context_load(
    phase="POSTFLIGHT",
    method="git",
    content=json.dumps(git_logger.get_last_checkpoint()),
    content_type="checkpoint"
)

# Generate efficiency report
print("\n" + "="*60)
print("TOKEN EFFICIENCY REPORT")
print("="*60)

report = metrics.compare_efficiency()

print(f"\nBaseline Total:  {report['total']['baseline_tokens']:,} tokens")
print(f"Actual Total:    {report['total']['actual_tokens']:,} tokens")
print(f"Reduction:       {report['total']['reduction_absolute']:,} tokens ({report['total']['reduction_percentage']:.1f}%)")
print(f"Cost Savings:    ${report['total']['cost_savings_usd']:.4f}")

if report['success_criteria']['target_met']:
    print(f"\n✅ SUCCESS: {report['success_criteria']['achieved_reduction_pct']:.1f}% reduction (target: 80%)")
else:
    print(f"\n❌ Below target: {report['success_criteria']['achieved_reduction_pct']:.1f}% reduction (target: 80%)")

# Export detailed report
metrics.export_report(
    format="markdown",
    output_path="docs/metrics/minimax_session_9_token_efficiency.md"
)

print(f"\n✓ Detailed report saved to: docs/metrics/minimax_session_9_token_efficiency.md")

# Save measurements for future analysis
metrics.save_measurements()
```

---

## 🔧 Git Commands Reference

### View Git Notes
```bash
# View note on current commit
git notes show HEAD

# View note on specific commit
git notes show <commit-sha>

# List all commits with notes
git log --notes

# List note objects
git notes list
```

### Manual Checkpoint Inspection
```bash
# Pretty-print current checkpoint
git notes show HEAD | python -m json.tool

# Count checkpoint tokens (approximate)
git notes show HEAD | wc -w | awk '{print int($1 * 1.3)}'
```

### Troubleshooting
```bash
# If notes conflict, force overwrite
git notes add -f -m '{"your": "checkpoint"}'

# Remove a note
git notes remove HEAD

# Copy notes between commits
git notes copy <source-commit> <dest-commit>
```

---

## 📊 Expected Results

### Token Compression Targets

| Phase | Baseline (Prompt) | Target (Git) | Reduction |
|-------|-------------------|--------------|-----------|
| PREFLIGHT | 6,500 tokens | 450 tokens | -93% |
| CHECK | 3,500 tokens | 400 tokens | -89% |
| ACT | 1,500 tokens | 500 tokens | -67% |
| POSTFLIGHT | 5,500 tokens | 850 tokens | -85% |
| **TOTAL** | **17,000 tokens** | **~2,200 tokens** | **-87%** |

### Checkpoint Format Example

```json
{
  "session_id": "minimax-session-9",
  "phase": "PREFLIGHT",
  "round": 1,
  "timestamp": "2025-11-15T14:30:00Z",
  "vectors": {
    "know": 0.75,
    "do": 0.80,
    "context": 0.70,
    "clarity": 0.85,
    "engagement": 0.90,
    "uncertainty": 0.35,
    "coherence": 0.75,
    "signal": 0.80,
    "density": 0.65,
    "state": 0.70,
    "change": 0.60,
    "completion": 0.30,
    "impact": 0.75
  },
  "overall_confidence": 0.750,
  "meta": {
    "task": "Implement feature X"
  },
  "token_count": 453
}
```

---

## ✅ Success Criteria Checklist

### Functional Requirements
- [ ] GitEnhancedReflexLogger creates git notes successfully
- [ ] Checkpoints retrieved from git notes correctly
- [ ] Vector diff calculation works
- [ ] SQLite fallback works when git unavailable
- [ ] TokenEfficiencyMetrics measures tokens accurately

### Performance Requirements
- [ ] PREFLIGHT checkpoint ≤ 500 tokens (target: ~450)
- [ ] CHECK vector diff ≤ 450 tokens (target: ~400)
- [ ] ACT checkpoint ≤ 600 tokens (target: ~500)
- [ ] POSTFLIGHT checkpoint ≤ 900 tokens (target: ~850)
- [ ] **Total session ≤ 3,000 tokens (target: ~2,200)**

### Efficiency Requirements
- [ ] Overall token reduction ≥ 80%
- [ ] Cost savings ≥ $0.001 per session (at scale)
- [ ] All measurements recorded correctly
- [ ] Report generation works (JSON, Markdown, CSV)

---

## 🐛 Troubleshooting Guide

### Issue: Git notes not showing

**Symptoms:** `git notes show HEAD` returns nothing

**Solutions:**
1. Check if you committed first: `git log -1`
2. Verify note was created: `git notes list`
3. Try forcing note creation: `git_logger.add_checkpoint(...)`  with `enable_git_notes=True`

### Issue: Token count seems wrong

**Symptoms:** Checkpoint shows unexpected token count

**Causes:**
- Token counting approximation (word count * 1.3) is rough
- Large metadata increases size

**Solutions:**
1. Use: `git notes show HEAD | python -m json.tool` to inspect
2. Minimize metadata (only essential fields)
3. Verify `token_count` field in checkpoint

### Issue: SQLite fallback not working

**Symptoms:** Cannot retrieve checkpoint

**Solutions:**
1. Check: `.empirica_reflex_logs/checkpoints/<session-id>/`
2. Verify files exist: `ls -la .empirica_reflex_logs/checkpoints/`
3. Check logs for errors

### Issue: Efficiency report shows <80% reduction

**Causes:**
- Metadata too large
- Not using compressed checkpoints
- Loading full history instead of checkpoints

**Solutions:**
1. Verify using `git_logger.get_last_checkpoint()` not `db.get_session_history()`
2. Check checkpoint size: `git notes show HEAD | wc -c`
3. Review measurements: `metrics.measurements`

---

## 📈 Next Steps After Session 9

### If Success (≥80% reduction):
1. Document actual token counts achieved
2. Compare with theoretical predictions
3. Plan Phase 2: Integration with production workflows
4. Consider: What other components benefit from git-backed state?

### If Below Target (<80% reduction):
1. Analyze where tokens are being spent
2. Identify optimization opportunities
3. Consider: More aggressive checkpoint compression
4. Validate measurements are accurate

---

## 🎓 Learning Objectives

By completing Minimax Session 9, you will:

1. **Understand git notes** - How to use git as a metadata store
2. **Validate token efficiency** - Empirical evidence for architectural decisions
3. **Practice Empirica workflow** - PREFLIGHT→POSTFLIGHT with real measurements
4. **Build intuition** - What does "compressed context" feel like in practice?

---

## 📝 Deliverables

After completing Session 9, provide:

1. **Token Efficiency Report** (Markdown)
   - Location: `docs/metrics/minimax_session_9_token_efficiency.md`
   - Contents: Per-phase breakdown, total reduction %, cost savings

2. **Git Notes Validation**
   - Command: `git log --notes --oneline -10`
   - Verify: All phases have checkpoints attached

3. **Session Summary**
   - What worked well?
   - What was surprising?
   - Suggestions for improvement?

4. **Calibration Check**
   - Was PREFLIGHT assessment accurate?
   - Did UNCERTAINTY decrease as expected?
   - Were epistemic deltas meaningful?

---

**Good luck! Let's prove the hypothesis. 🚀**

**Ready to start:** 2025-11-15  
**Expected completion:** 1-2 hours  
**Impact:** Validates foundation for scalable git integration
