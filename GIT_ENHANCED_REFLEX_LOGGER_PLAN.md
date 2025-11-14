# 🔧 Git-Enhanced Reflex Logger Implementation Plan

**Goal:** Implement `GitEnhancedReflexLogger` to achieve 80-90% token compression

---

## 📊 Current State vs Target

### Current: SQLite-Based (Session 5 Baseline)
```python
# PREFLIGHT loads full history from SQLite
history = db.load_session_history(session_id)  # ~6,500 tokens

# CHECK loads complete assessment
assessment = db.load_last_assessment()  # ~3,500 tokens/check

# Total: ~19,000 tokens/session
```

### Target: Git Notes Compression
```python
# PREFLIGHT loads compressed checkpoint from git
checkpoint = git.notes.show("HEAD")  # 200-500 tokens (compressed!)

# CHECK loads vector diff only
diff = current_vectors - checkpoint_vectors  # ~400 tokens

# Total: ~3,000 tokens/session (84% savings)
```

---

## 🏗️ Implementation Architecture

### 1. Create `GitEnhancedReflexLogger` (Extend Existing)

**File:** `empirica/core/canonical/reflex_logger.py`

**Class Structure:**
```python
class GitEnhancedReflexLogger(ReflexLogger):
    """
    Extends ReflexLogger with git notes integration for token compression.
    
    Key Features:
    - Backward compatible (SQLite fallback)
    - Opt-in via enable_git_notes flag
    - Automatic checkpoint creation on phase transitions
    - Compressed session state (200-500 tokens vs 6,500 tokens)
    """
    
    def __init__(self, session_id: str, enable_git_notes: bool = False):
        super().__init__(session_id)
        self.enable_git_notes = enable_git_notes
        self.git_available = self._check_git_available()
    
    def _check_git_available(self) -> bool:
        """Check if we're in a git repo with commit history"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                check=True
            )
            return result.returncode == 0
        except:
            return False
    
    def _add_git_checkpoint(self, phase: str, round_num: int, vectors: dict):
        """
        Attach epistemic state to current commit via git notes.
        
        Note structure (200-500 tokens):
        {
            "session_id": "...",
            "phase": "CHECK",
            "round": 25,
            "timestamp": "2025-01-14T10:00:00",
            "vectors": {
                "KNOW": 0.85,
                "DO": 0.80,
                ...12 more vectors
            },
            "confidence": 0.85,
            "uncertainty": 0.20
        }
        """
        if not self.enable_git_notes or not self.git_available:
            return  # Fallback to SQLite only
        
        note_data = {
            "session_id": self.session_id,
            "phase": phase,
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "vectors": vectors,
            "confidence": self._calculate_confidence(vectors),
            "uncertainty": vectors.get("UNCERTAINTY", 0.0)
        }
        
        try:
            # Add note to current commit
            subprocess.run([
                "git", "notes", "add", "-m", json.dumps(note_data)
            ], check=True, capture_output=True)
            
            logger.debug(f"Added git checkpoint: {phase} round {round_num}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to add git note: {e}")
            # Continue - SQLite still works as fallback
    
    def get_last_checkpoint(self) -> dict:
        """
        Load compressed checkpoint from git notes (200-500 tokens).
        Falls back to SQLite if git notes unavailable.
        
        Token Comparison:
        - Git notes: 200-500 tokens (JSON note)
        - SQLite: 6,500 tokens (full history)
        - Savings: 92-97%
        """
        if self.enable_git_notes and self.git_available:
            try:
                result = subprocess.run([
                    "git", "notes", "show", "HEAD"
                ], capture_output=True, text=True, check=True)
                
                if result.returncode == 0:
                    checkpoint = json.loads(result.stdout)
                    logger.debug("Loaded checkpoint from git notes")
                    return checkpoint
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                logger.warning(f"Git notes unavailable, falling back to SQLite: {e}")
        
        # Fallback to SQLite (backward compatibility)
        return self._load_from_sqlite()
    
    def log_phase_transition(self, phase: str, round_num: int, vectors: dict):
        """
        Override to add git checkpointing on phase transitions.
        
        Phases that create checkpoints:
        - PREFLIGHT (initial state)
        - CHECK (investigation completion)
        - ACT (action taken - on git commit)
        - POSTFLIGHT (final state)
        """
        # Standard SQLite logging (for backward compatibility)
        super().log_phase_transition(phase, round_num, vectors)
        
        # Add git checkpoint if enabled
        if phase in ["PREFLIGHT", "CHECK", "ACT", "POSTFLIGHT"]:
            self._add_git_checkpoint(phase, round_num, vectors)
```

---

## 🔗 Integration Points

### 1. Metacognitive Cascade Integration

**File:** `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

**Changes Required:**
```python
# Initialize with git notes enabled
self.reflex_logger = GitEnhancedReflexLogger(
    session_id=session_id,
    enable_git_notes=True  # Opt-in
)

# PREFLIGHT: Load compressed checkpoint
def preflight(self):
    checkpoint = self.reflex_logger.get_last_checkpoint()
    # Use checkpoint (200-500 tokens) vs full history (6,500 tokens)
    self._restore_from_checkpoint(checkpoint)

# ACT: Add checkpoint after git commit
def act(self):
    # ... perform action ...
    if action_commits_to_git:
        self.reflex_logger._add_git_checkpoint("ACT", round_num, vectors)
```

### 2. Git Commit Hook Integration

**Strategy:** Auto-checkpoint on code commits

**File:** `empirica/integration/empirica_action_hooks.py`

```python
def post_commit_hook(commit_sha: str, session_id: str):
    """
    Called after git commit to attach epistemic state.
    Maps git commits to Empirica cognitive state.
    """
    reflex_logger = GitEnhancedReflexLogger(session_id, enable_git_notes=True)
    current_vectors = reflex_logger.get_current_vectors()
    reflex_logger._add_git_checkpoint("ACT", round_num, current_vectors)
```

---

## 🧪 Testing Strategy

### Phase 1: Unit Tests

**File:** `tests/test_git_enhanced_reflex_logger.py`

```python
def test_git_notes_creation():
    """Test git note is created with correct structure"""
    logger = GitEnhancedReflexLogger("test-session", enable_git_notes=True)
    logger._add_git_checkpoint("CHECK", 25, mock_vectors)
    
    # Verify note exists
    result = subprocess.run(["git", "notes", "show", "HEAD"], ...)
    assert result.returncode == 0
    
    # Verify structure
    note = json.loads(result.stdout)
    assert note["phase"] == "CHECK"
    assert note["round"] == 25
    assert "vectors" in note

def test_checkpoint_loading():
    """Test checkpoint loads from git notes"""
    logger = GitEnhancedReflexLogger("test-session", enable_git_notes=True)
    checkpoint = logger.get_last_checkpoint()
    
    assert checkpoint is not None
    assert "vectors" in checkpoint
    assert len(checkpoint["vectors"]) == 13

def test_sqlite_fallback():
    """Test falls back to SQLite when git unavailable"""
    logger = GitEnhancedReflexLogger("test-session", enable_git_notes=True)
    logger.git_available = False  # Simulate no git
    
    checkpoint = logger.get_last_checkpoint()
    # Should still work via SQLite
    assert checkpoint is not None
```

### Phase 2: Integration Test (Benchmarking Session)

**Test:** Run MiniMax session with git notes enabled, measure token usage

**Baseline (Session 5):**
- PREFLIGHT: 6,500 tokens
- CHECK (x2): 7,000 tokens
- ACT: 3,500 tokens
- POSTFLIGHT: 2,000 tokens
- **TOTAL: 19,000 tokens**

**Expected (Session 6 with Git Notes):**
- PREFLIGHT: 900 tokens (6x reduction)
- CHECK: 800 tokens (9x reduction)
- ACT: 800 tokens (4x reduction)
- POSTFLIGHT: 500 tokens (4x reduction)
- **TOTAL: 3,000 tokens (6x reduction)**

**Validation:**
- If savings < 70%: Investigate compression issues
- If savings 70-80%: Good, document findings
- If savings > 80%: Excellent, proceed to Phase 2

---

## 📊 Token Compression Analysis

### PREFLIGHT Compression

**Current (SQLite):**
```python
# Load full session history
history = db.execute("""
    SELECT * FROM reflex_frames 
    WHERE session_id = ? 
    ORDER BY round_num
""")  # Returns 50+ rows × 500 tokens = 6,500 tokens
```

**With Git Notes:**
```python
# Load last checkpoint only
checkpoint = json.loads(git.notes.show("HEAD"))
# Single JSON object: 200-500 tokens
# Compression: 6,500 → 500 = 13x reduction
```

### CHECK Compression

**Current (SQLite):**
```python
# Load complete epistemic assessment
assessment = db.get_last_assessment()
# Full 13-vector assessment + context = 3,500 tokens
```

**With Git Notes:**
```python
# Load last checkpoint and compute diff
last = json.loads(git.notes.show("HEAD"))
current = self.compute_current_vectors()
diff = {k: current[k] - last["vectors"][k] for k in current}
# Just the diff: ~400 tokens
# Compression: 3,500 → 400 = 8x reduction
```

---

## 🚀 Rollout Plan

### Step 1: Implementation (Day 1-2)
- [ ] Create `GitEnhancedReflexLogger` class
- [ ] Add `_add_git_checkpoint()` method
- [ ] Add `get_last_checkpoint()` with fallback
- [ ] Add `_check_git_available()` safety
- [ ] Update `log_phase_transition()` override

### Step 2: Testing (Day 2-3)
- [ ] Write unit tests
- [ ] Test checkpoint creation
- [ ] Test checkpoint loading
- [ ] Test SQLite fallback
- [ ] Test in non-git environment

### Step 3: Integration (Day 3-4)
- [ ] Update `metacognitive_cascade.py` to use new logger
- [ ] Add `enable_git_notes` flag (default: False for safety)
- [ ] Test with existing sessions (should work via fallback)
- [ ] Enable for new session and verify

### Step 4: Benchmarking (Day 4-5)
- [ ] Run Session 6 with git notes enabled
- [ ] Measure token usage at each phase
- [ ] Compare vs Session 5 baseline
- [ ] Document findings
- [ ] Calculate actual compression ratio

### Step 5: Decision Point (Day 5)
- ✅ **If savings > 80%:** Proceed to Phase 2 (git-native storage)
- 🔄 **If savings 70-80%:** Iterate on compression strategy
- ❌ **If savings < 70%:** Investigate issues, may need different approach

---

## 🎯 Success Criteria

### Must Have ✅
- [ ] No regressions (SQLite fallback works)
- [ ] Git notes created at phase transitions
- [ ] Checkpoint loading works
- [ ] Token savings > 70%

### Should Have 📊
- [ ] Token savings > 80%
- [ ] Clean integration with existing code
- [ ] Comprehensive tests
- [ ] Documentation

### Nice to Have 🚀
- [ ] Token savings > 85%
- [ ] Auto-checkpoint on git commits
- [ ] CLI tool to view git notes
- [ ] Visualization of epistemic trajectory via git log

---

## 🔍 Monitoring & Validation

### Token Usage Tracking
```python
# Add to reflex_logger
def track_token_usage(self, phase: str, method: str, tokens: int):
    """Track token usage for compression analysis"""
    self.token_log.append({
        "phase": phase,
        "method": method,  # "git_notes" or "sqlite"
        "tokens": tokens,
        "timestamp": datetime.now()
    })

# At end of session
def generate_compression_report(self):
    """Compare git notes vs SQLite token usage"""
    git_tokens = sum(t["tokens"] for t in self.token_log if t["method"] == "git_notes")
    sqlite_tokens = sum(t["tokens"] for t in self.token_log if t["method"] == "sqlite")
    compression_ratio = sqlite_tokens / git_tokens if git_tokens > 0 else 0
    
    return {
        "git_tokens": git_tokens,
        "sqlite_tokens": sqlite_tokens,
        "compression_ratio": compression_ratio,
        "savings_percent": (1 - git_tokens/sqlite_tokens) * 100
    }
```

---

## 📚 Git Notes Command Reference

### Basic Operations
```bash
# Add note to current commit
git notes add -m '{"session": "abc", "phase": "CHECK", ...}'

# Show note for current commit
git notes show HEAD

# Show note for specific commit
git notes show <commit-sha>

# List all notes
git log --notes

# Remove note
git notes remove HEAD

# Edit note
git notes edit HEAD
```

### Query Operations (Future: Sentinel)
```bash
# Find sessions
git log --notes --grep="session_id"

# Show epistemic trajectory
git log --notes --format="%H %s %N"

# Compare cognitive states
git diff HEAD~1 HEAD --notes

# Find high-uncertainty commits
git log --notes | grep -A5 "UNCERTAINTY.*0\.[8-9]"
```

---

## 🎉 Expected Impact

### Token Savings (Per Session)
- **Baseline:** 19,000 tokens
- **With Git Notes:** 3,000 tokens
- **Savings:** 16,000 tokens (84%)

### Cost Savings (At Scale)
- **Per 100 sessions:** 1.6M tokens saved
- **At $0.10/1K tokens:** $160 saved per 100 sessions
- **For high-volume users:** $50-100/month savings

### Performance Benefits
- **Faster PREFLIGHT:** Load 500 tokens vs 6,500 tokens
- **Faster CHECK:** Load 400 tokens vs 3,500 tokens
- **Less API latency:** Fewer DB queries
- **Better scalability:** Git scales better than SQLite for large histories

---

**Ready to implement after Session 8 completes P2!** 🚀
