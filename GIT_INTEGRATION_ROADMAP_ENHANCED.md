# Empirica Git Integration: Enhanced Roadmap with Token Efficiency Measurement

**Vision:** Enable AI agents like Minimax to work with 80-90% token reduction by retrieving context from git instead of prompts.

**Status:** Phase 1.5 Ready - Git Notes Prototype with Measurement Framework

---

## 🎯 Executive Summary

### The Token Problem

**Current State (Prompt-Based Context):**
- PREFLIGHT loads full session history: ~6,500 tokens
- CHECK loads complete assessment: ~3,500 tokens per check
- Total per session: ~19,000 tokens

**Target State (Git-Based Context):**
- PREFLIGHT loads compressed checkpoint from git notes: 200-500 tokens
- CHECK loads vector diff only: ~400 tokens
- Total per session: ~3,000 tokens
- **Result: 84% token reduction**

### Why This Matters

1. **Cost Reduction:** $1.90 → $0.30 per session @ $0.10/1K tokens
2. **Longer Sessions:** More work within context windows
3. **Faster Performance:** Less latency from smaller prompts
4. **Reliable State:** Git is source of truth, not reconstructed context
5. **Measurable:** Can quantify efficiency gains with real data

---

## 📊 Phase 1.5: Git Notes Prototype (CURRENT PHASE)

**Timeline:** 1 week  
**Goal:** Validate 80-90% token savings with measurable baseline

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Empirica Workflow                         │
│  PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              GitEnhancedReflexLogger                         │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   SQLite DB  │◄────────┤ Git Notes    │                  │
│  │  (fallback)  │         │ (primary)    │                  │
│  └──────────────┘         └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Git Repository                             │
│  commits: code changes                                       │
│  notes:   epistemic state (compressed)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Tasks

### Task 1: Create GitEnhancedReflexLogger (Day 1-2)

**File:** `empirica/core/canonical/reflex_logger.py`

**Features:**
- Extends existing `ReflexLogger` (backward compatible)
- Hybrid approach: SQLite + git notes
- Opt-in via `enable_git_notes` flag (default: False)
- Automatic checkpoint on phase transitions

**Key Methods:**

```python
class GitEnhancedReflexLogger(ReflexLogger):
    """Git-enhanced reflex logger with token compression"""
    
    def __init__(self, session_id: str, enable_git_notes: bool = False):
        super().__init__()
        self.session_id = session_id
        self.enable_git_notes = enable_git_notes
        self.git_available = self._check_git_available()
    
    def _add_git_checkpoint(
        self, 
        phase: str, 
        round_num: int, 
        vectors: Dict[str, float],
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Add compressed checkpoint to git notes.
        
        Returns:
            note_id: Git note SHA if successful, None otherwise
        
        Checkpoint format (200-500 tokens):
        {
            "session_id": "abc123",
            "phase": "PREFLIGHT",
            "round": 5,
            "timestamp": "2024-11-14T12:00:00Z",
            "vectors": {
                "know": 0.85, "do": 0.90, "uncertainty": 0.25, ...
            },
            "overall_confidence": 0.847,
            "decision": "proceed",  # for CHECK phase
            "files_changed": ["file.py"],  # for ACT phase
            "token_count": 453  # self-measurement
        }
        """
        if not self.enable_git_notes or not self.git_available:
            return None
        
        checkpoint = self._create_checkpoint(phase, round_num, vectors, metadata)
        
        # Add to git notes (attached to HEAD commit)
        note_id = self._git_add_note(checkpoint)
        
        # Also save to SQLite (fallback)
        self._save_to_sqlite(checkpoint)
        
        return note_id
    
    def get_last_checkpoint(self, max_age_hours: int = 24) -> Optional[Dict]:
        """
        Load most recent checkpoint (git notes preferred, SQLite fallback).
        
        Returns compressed state (200-500 tokens) instead of full history.
        """
        # Try git notes first
        if self.enable_git_notes and self.git_available:
            checkpoint = self._git_get_latest_note()
            if checkpoint and self._is_fresh(checkpoint, max_age_hours):
                return checkpoint
        
        # Fallback to SQLite
        return self._load_from_sqlite()
    
    def get_vector_diff(self, since_checkpoint: Dict) -> Dict:
        """
        Compute vector delta since last checkpoint.
        
        Returns: ~400 tokens (vs ~3,500 for full assessment)
        """
        current = self.get_current_vectors()
        baseline = since_checkpoint.get("vectors", {})
        
        return {
            "delta": {k: current[k] - baseline.get(k, 0) for k in current},
            "baseline_round": since_checkpoint.get("round", 0),
            "current_round": self.current_round,
            "significant_changes": [
                k for k, v in current.items() 
                if abs(v - baseline.get(k, 0)) > 0.15
            ]
        }
```

**Safety Features:**
- Falls back to SQLite if git unavailable
- Non-destructive (adds data, never removes)
- Validates git repo exists before operations
- Handles merge conflicts gracefully

---

### Task 2: Token Measurement Framework (Day 2)

**File:** `empirica/metrics/token_efficiency.py` (NEW)

**Purpose:** Measure actual token usage before/after git integration

```python
class TokenEfficiencyMetrics:
    """Measure and compare token usage across sessions"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.measurements = []
    
    def measure_context_load(
        self, 
        phase: str, 
        method: str,  # "prompt" or "git"
        content: str
    ) -> Dict:
        """
        Measure token count for context loading.
        
        Returns:
            {
                "phase": "PREFLIGHT",
                "method": "git",
                "tokens": 453,
                "timestamp": "2024-11-14T12:00:00Z",
                "content_type": "checkpoint"
            }
        """
        token_count = self._count_tokens(content)
        
        measurement = {
            "phase": phase,
            "method": method,
            "tokens": token_count,
            "timestamp": datetime.utcnow().isoformat(),
            "content_type": self._classify_content(content)
        }
        
        self.measurements.append(measurement)
        return measurement
    
    def compare_efficiency(self, baseline_session: str) -> Dict:
        """
        Compare token usage between sessions.
        
        Returns efficiency report with % reduction.
        """
        baseline = self._load_measurements(baseline_session)
        current = self.measurements
        
        comparison = {}
        for phase in ["PREFLIGHT", "CHECK", "ACT", "POSTFLIGHT"]:
            baseline_tokens = self._sum_tokens(baseline, phase)
            current_tokens = self._sum_tokens(current, phase)
            
            reduction = (baseline_tokens - current_tokens) / baseline_tokens
            
            comparison[phase] = {
                "baseline_tokens": baseline_tokens,
                "current_tokens": current_tokens,
                "reduction_pct": reduction * 100,
                "tokens_saved": baseline_tokens - current_tokens
            }
        
        # Overall summary
        total_baseline = sum(c["baseline_tokens"] for c in comparison.values())
        total_current = sum(c["current_tokens"] for c in comparison.values())
        total_reduction = (total_baseline - total_current) / total_baseline
        
        comparison["TOTAL"] = {
            "baseline_tokens": total_baseline,
            "current_tokens": total_current,
            "reduction_pct": total_reduction * 100,
            "tokens_saved": total_baseline - total_current,
            "cost_savings_usd": (total_baseline - total_current) * 0.0001  # $0.10/1K
        }
        
        return comparison
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (simple approximation)"""
        # For production: use tiktoken or actual LLM tokenizer
        return len(text.split()) * 1.3  # Rough approximation
    
    def export_report(self, format: str = "json") -> str:
        """Export measurements for analysis"""
        if format == "json":
            return json.dumps(self.measurements, indent=2)
        elif format == "csv":
            return self._to_csv()
        elif format == "markdown":
            return self._to_markdown_table()
```

**Usage in Minimax Session:**

```python
# In session instructions
metrics = TokenEfficiencyMetrics(session_id="minimax-session-6")

# Measure PREFLIGHT context load
checkpoint = git_logger.get_last_checkpoint()
metrics.measure_context_load("PREFLIGHT", "git", json.dumps(checkpoint))

# Compare with baseline
report = metrics.compare_efficiency(baseline_session="minimax-session-5")
print(report["TOTAL"]["reduction_pct"])  # Expected: 80-90%
```

---

### Task 3: Minimax Integration Instructions (Day 3)

**File:** `MINIMAX_SESSION9_GIT_PROTOTYPE_TEST.md` (NEW)

**Primary Goal:** Complete assigned development tasks (e.g., P3 implementation)

**Secondary Goal:** Measure token efficiency with git integration

**Workflow Changes:**

```markdown
## Modified Empirica Workflow with Git Integration

### PREFLIGHT
1. Load checkpoint from git notes (instead of full history)
   ```python
   checkpoint = git_logger.get_last_checkpoint()
   # checkpoint is ~400 tokens vs ~6,500 tokens
   ```

2. Self-assess as normal

3. Create git checkpoint
   ```bash
   git notes add -m '{"phase": "PREFLIGHT", "round": 1, "vectors": {...}}'
   ```

4. Measure tokens
   ```python
   metrics.measure_context_load("PREFLIGHT", "git", checkpoint)
   ```

### INVESTIGATE
- Load context diffs only (not full history)
- Create checkpoint after investigation

### CHECK
1. Load vector diff from last checkpoint
   ```python
   diff = git_logger.get_vector_diff(last_checkpoint)
   # diff is ~400 tokens vs ~3,500 tokens
   ```

2. Self-assess decision

3. Create checkpoint
   ```bash
   git notes add -m '{"phase": "CHECK", "round": 5, "decision": "proceed", ...}'
   ```

### ACT
1. Make code changes

2. Commit with descriptive message
   ```bash
   git commit -m "feat: Add token metrics framework"
   ```

3. Attach epistemic state to commit
   ```bash
   git notes add -m '{"phase": "ACT", "round": 8, "confidence": 0.95, ...}'
   ```

### POSTFLIGHT
1. Load PREFLIGHT checkpoint for calibration

2. Calculate epistemic delta
   ```python
   preflight = git_logger.get_checkpoint_by_phase("PREFLIGHT")
   delta = postflight_vectors - preflight["vectors"]
   ```

3. Create final checkpoint

4. Generate efficiency report
   ```python
   report = metrics.compare_efficiency("minimax-session-5")
   # Save to: docs/metrics/session_9_token_efficiency.md
   ```
```

**Success Criteria:**
- [ ] All workflow phases use git-based context
- [ ] Token measurements captured for each phase
- [ ] Efficiency report generated
- [ ] 70-90% token reduction achieved
- [ ] Primary task completed successfully

---

## 📈 Measurement & Validation

### Baseline Establishment (Session 5 Data)

**Prompt-Based Context (Current):**
```
Phase          | Tokens | Source
---------------|--------|------------------
PREFLIGHT      | 6,500  | Full session history from SQLite
INVESTIGATE    | 2,000  | Query results + context
CHECK (each)   | 3,500  | Complete assessment state
ACT (each)     | 1,500  | Code context + plan
POSTFLIGHT     | 5,500  | Full session for calibration
---------------|--------|------------------
TOTAL/SESSION  | 19,000 | (Baseline)
```

**Estimated Cost:** $1.90/session @ $0.10/1K tokens

---

### Target Performance (Git-Based Context)

**Git Notes Compression:**
```
Phase          | Tokens | Source                    | Reduction
---------------|--------|---------------------------|----------
PREFLIGHT      |    450 | Last checkpoint (git)     | -93%
INVESTIGATE    |    800 | Focused git log queries   | -60%
CHECK (each)   |    400 | Vector diff only          | -89%
ACT (each)     |    500 | Git diff + checkpoint     | -67%
POSTFLIGHT     |    850 | PREFLIGHT checkpoint only | -85%
---------------|--------|---------------------------|----------
TOTAL/SESSION  |  3,000 | (Target)                  | -84%
```

**Estimated Cost:** $0.30/session @ $0.10/1K tokens

**Savings:** $1.60/session, $160/100 sessions

---

### Validation Metrics

**Quantitative (Must Measure):**
1. **Token count per phase** (baseline vs git)
2. **Total tokens per session** (target: <4,000)
3. **Token reduction percentage** (target: >80%)
4. **Cost savings** (calculated from token reduction)
5. **Latency per phase** (git load time vs SQLite query time)

**Qualitative (Must Observe):**
1. **Context completeness:** Does git checkpoint have sufficient context?
2. **Workflow disruption:** Does git integration slow down Minimax?
3. **Error resilience:** Does fallback to SQLite work smoothly?
4. **Developer experience:** Is git integration transparent?

**Success Thresholds:**
- ✅ **Excellent:** >85% token reduction, <50ms latency overhead
- ✅ **Good:** 70-85% reduction, <100ms latency
- ⚠️ **Acceptable:** 50-70% reduction, <200ms latency
- ❌ **Insufficient:** <50% reduction or >200ms latency

---

## 🏗️ Implementation Details

### Git Notes Structure

**Standard Checkpoint Format:**
```json
{
  "session_id": "minimax-session-9",
  "ai_id": "minimax",
  "phase": "CHECK",
  "round": 15,
  "timestamp": "2024-11-14T12:34:56Z",
  "commit_sha": "abc123def456",
  
  "vectors": {
    "engagement": 0.95,
    "know": 0.85,
    "do": 0.90,
    "context": 0.80,
    "clarity": 0.90,
    "coherence": 0.85,
    "signal": 0.85,
    "density": 0.40,
    "state": 0.90,
    "change": 0.85,
    "completion": 0.70,
    "impact": 0.85,
    "uncertainty": 0.25
  },
  
  "overall_confidence": 0.847,
  "decision": "proceed",
  
  "context_summary": {
    "task": "Implement token metrics framework",
    "files_modified": ["empirica/metrics/token_efficiency.py"],
    "issues_resolved": [],
    "blockers": []
  },
  
  "meta": {
    "token_count": 453,
    "compressed": true,
    "storage": "git_notes",
    "fallback_available": true
  }
}
```

**Token Count:** ~450 tokens (compressed vs ~6,500 uncompressed)

---

### Git Commands Reference

**Add checkpoint after phase:**
```bash
# Create checkpoint JSON
cat > checkpoint.json << EOF
{
  "phase": "PREFLIGHT",
  "round": 1,
  "vectors": {...}
}
EOF

# Attach to current commit
git notes add -F checkpoint.json

# Or inline
git notes add -m '{"phase": "CHECK", "round": 5, ...}'
```

**Retrieve last checkpoint:**
```bash
# Get notes from HEAD
git notes show HEAD

# Get notes from specific commit
git notes show abc123

# List all notes
git notes list
```

**Query checkpoint history:**
```bash
# Find all PREFLIGHT checkpoints
git log --all --notes --grep="PREFLIGHT"

# Get checkpoints from last 5 commits
git log -5 --format="%H" | xargs -I {} git notes show {}
```

---

### Integration with Existing Code

**Metacognitive Cascade Changes:**

**File:** `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

```python
class MetacognitiveCascade:
    def __init__(self, session_id: str, enable_git_notes: bool = False):
        self.session_id = session_id
        
        # Use GitEnhancedReflexLogger if enabled
        if enable_git_notes:
            self.reflex_logger = GitEnhancedReflexLogger(
                session_id=session_id,
                enable_git_notes=True
            )
        else:
            self.reflex_logger = ReflexLogger()
        
        # Initialize token metrics
        self.token_metrics = TokenEfficiencyMetrics(session_id)
    
    def preflight(self, task_description: str) -> Dict:
        """PREFLIGHT with git checkpoint loading"""
        
        # Load compressed checkpoint instead of full history
        checkpoint = self.reflex_logger.get_last_checkpoint()
        
        # Measure tokens
        if checkpoint:
            self.token_metrics.measure_context_load(
                "PREFLIGHT", 
                "git", 
                json.dumps(checkpoint)
            )
        
        # Continue with normal PREFLIGHT assessment
        assessment = self._execute_preflight(task_description, checkpoint)
        
        # Save checkpoint
        self.reflex_logger._add_git_checkpoint(
            phase="PREFLIGHT",
            round_num=self.round,
            vectors=assessment["vectors"]
        )
        
        return assessment
    
    def check(self) -> Dict:
        """CHECK with vector diff loading"""
        
        # Load vector diff (not full assessment)
        last_checkpoint = self.reflex_logger.get_last_checkpoint()
        vector_diff = self.reflex_logger.get_vector_diff(last_checkpoint)
        
        # Measure tokens (diff is ~400 tokens vs ~3,500 full)
        self.token_metrics.measure_context_load(
            "CHECK",
            "git",
            json.dumps(vector_diff)
        )
        
        # Execute CHECK decision
        decision = self._execute_check(vector_diff)
        
        # Save checkpoint with decision
        self.reflex_logger._add_git_checkpoint(
            phase="CHECK",
            round_num=self.round,
            vectors=decision["vectors"],
            metadata={"decision": decision["decision"]}
        )
        
        return decision
```

---

## 🎯 Success Criteria & Decision Points

### Phase 1.5 Completion Criteria

**Must Achieve:**
- [ ] GitEnhancedReflexLogger implemented and tested
- [ ] Token measurement framework working
- [ ] Minimax session completed with git integration
- [ ] Efficiency report generated with measurements
- [ ] >70% token reduction documented

**Decision Point After Phase 1.5:**

| Result | Next Action |
|--------|-------------|
| **>85% reduction** | ✅ Proceed to Phase 2 (full git-native storage) |
| **70-85% reduction** | ✅ Proceed with optimizations |
| **50-70% reduction** | ⚠️ Investigate bottlenecks, may proceed with caution |
| **<50% reduction** | ❌ Reconsider approach, may fallback to SQLite-only |

---

## 🚀 Rollout Timeline

### Week 1: Implementation & Testing (Days 1-5)

**Day 1:**
- [ ] Create `GitEnhancedReflexLogger` class
- [ ] Implement `_add_git_checkpoint()`
- [ ] Implement `get_last_checkpoint()`

**Day 2:**
- [ ] Create `TokenEfficiencyMetrics` class
- [ ] Add measurement methods
- [ ] Write unit tests

**Day 3:**
- [ ] Update `metacognitive_cascade.py` integration
- [ ] Create Minimax session 9 instructions
- [ ] Test git notes manually

**Day 4:**
- [ ] Run Minimax session 9 with git integration
- [ ] Collect token measurements
- [ ] Monitor for issues

**Day 5:**
- [ ] Generate efficiency report
- [ ] Compare with baseline
- [ ] Document findings
- [ ] Make go/no-go decision

---

## 📊 Expected Results

### Token Compression Breakdown

**PREFLIGHT Compression:**
```
Before (SQLite full history):
- Session metadata: 500 tokens
- Previous assessments (5): 2,500 tokens
- Investigation history: 1,500 tokens
- Context notes: 2,000 tokens
TOTAL: 6,500 tokens

After (Git checkpoint):
- Compressed vectors: 200 tokens
- Task summary: 100 tokens
- Decision state: 50 tokens
- Metadata: 100 tokens
TOTAL: 450 tokens

REDUCTION: 93%
```

**CHECK Compression:**
```
Before (Full assessment):
- Current vectors: 800 tokens
- Baseline comparison: 1,000 tokens
- Investigation findings: 1,000 tokens
- Decision context: 700 tokens
TOTAL: 3,500 tokens

After (Vector diff):
- Delta vectors: 150 tokens
- Significant changes: 100 tokens
- Decision state: 100 tokens
- Checkpoint reference: 50 tokens
TOTAL: 400 tokens

REDUCTION: 89%
```

---

## 🔄 Future Phases (Post-Validation)

### Phase 2: Full Git-Native Storage (If >85% savings)
- Replace SQLite with Git as primary storage
- Implement git log parsing for session history
- Add git branch support for parallel investigations
- Full backward compatibility layer

### Phase 3: Multi-Agent Git Workflows
- Git branches for agent handoffs
- Merge strategies for collaborative work
- Conflict resolution for parallel agents
- Git notes for agent communication

### Phase 4: Advanced Features
- Semantic search over git history (vector DB integration)
- Time-travel debugging (replay from any checkpoint)
- Cross-session learning (query all sessions)
- Organizational memory (persistent git repo)

---

## 📝 Documentation Requirements

### For Developers:
- [ ] `GitEnhancedReflexLogger` API documentation
- [ ] `TokenEfficiencyMetrics` usage guide
- [ ] Integration guide for metacognitive cascade
- [ ] Git notes format specification

### For AI Agents (Minimax):
- [ ] Modified workflow instructions
- [ ] Git commands reference
- [ ] Checkpoint creation guide
- [ ] Troubleshooting guide

### For End Users:
- [ ] High-level overview of git integration
- [ ] Performance benefits explanation
- [ ] Opt-in/opt-out instructions
- [ ] FAQ

---

## ⚠️ Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Git not available** | Low | High | SQLite fallback always available |
| **Token savings <70%** | Medium | Medium | Iterate on compression strategy |
| **Git commands slow** | Low | Medium | Cache checkpoints, async operations |
| **Minimax workflow disruption** | Medium | High | Thorough testing, rollback plan |
| **Checkpoint corruption** | Low | High | Validate JSON, multiple backups |
| **Measurement overhead** | Low | Low | Make metrics opt-in for production |

---

## 🎓 Learning Objectives

### What We'll Learn:
1. **Actual token reduction** (baseline vs git)
2. **Performance impact** (latency, throughput)
3. **UX impact** (does it help or hinder Minimax?)
4. **Compression limits** (how small can we go?)
5. **Edge cases** (what breaks, when?)

### Success Indicators:
- ✅ Minimax completes session with no blocking issues
- ✅ Token measurements show clear reduction
- ✅ Workflow feels natural (no cognitive overhead)
- ✅ Fallback mechanisms work when needed
- ✅ Report provides actionable data

---

## 📌 Next Steps

### Immediate (This Week):
1. **Create GitEnhancedReflexLogger** (2 days)
2. **Create TokenEfficiencyMetrics** (1 day)
3. **Test with Minimax Session 9** (1 day)
4. **Generate efficiency report** (1 day)
5. **Make Phase 2 decision** (go/no-go)

### Short-term (Next 2 Weeks):
- If successful: Plan Phase 2 (full git-native storage)
- If unsuccessful: Investigate bottlenecks, iterate
- Document lessons learned
- Update architecture documentation

### Long-term (1-2 Months):
- Phase 2: Full git integration
- Phase 3: Multi-agent workflows
- Phase 4: Advanced features (semantic search, time-travel)

---

**Status:** Ready to implement  
**Owner:** Claude + Minimax  
**Timeline:** Week of 2024-11-14  
**Success Metric:** >80% token reduction with working implementation

**File:** `/home/yogapad/empirical-ai/empirica/GIT_INTEGRATION_ROADMAP_ENHANCED.md`
