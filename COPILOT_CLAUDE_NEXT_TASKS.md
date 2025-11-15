# Copilot Claude - Next Tasks (Production Hardening)

**Date:** 2025-11-14  
**Status:** Ready to start  
**Priority:** HIGH - Required for v1.0 release  
**Coordination:** With Claude (co-lead) via git commits

---

## 🎯 Your New Mission: Phase 1.5 Production Hardening

You've successfully added MCP git integration tools (commit 7cc197b). Now we need to integrate them into the production workflow so users can actually use them.

### What You Did (Phase 1.5 MCP Layer) ✅
- ✅ Added 5 MCP tools to `empirica_mcp_server.py`
- ✅ `create_git_checkpoint` - Create checkpoints in git notes
- ✅ `load_git_checkpoint` - Load checkpoints (~450 tokens)
- ✅ `get_vector_diff` - Calculate vector changes
- ✅ `measure_token_efficiency` - Track token usage
- ✅ `generate_efficiency_report` - Generate reports

**Result:** MCP layer complete, 277 lines added

---

## 🚀 What's Needed Now: Integration into Production

### Gap Analysis
The git integration tools exist at the MCP layer but aren't integrated into:
1. ❌ CLI commands (users can't use from command line)
2. ❌ Metacognitive cascade (not automatic during workflow)
3. ❌ Bootstrap (not enabled by default)
4. ❌ Documentation (users don't know how to use)

**Your task:** Make Phase 1.5 accessible to users, not just via MCP tools.

---

## 📋 Task List

### Task 1: CLI Integration ⚠️ HIGH PRIORITY
**Goal:** Users can use git checkpoints from CLI

**Files to modify:**
- `empirica/cli/command_handlers/session_commands.py`
- `empirica/cli/cli_core.py`

**New commands to add:**

#### 1.1: `empirica checkpoint create`
```python
# Add to session_commands.py

def create_checkpoint_command(session_id: str, phase: str, metadata: dict = None):
    """
    Create git checkpoint for current session.
    
    Usage:
        empirica checkpoint create --session-id abc123 --phase preflight
    
    Result:
        Checkpoint created in git notes (~46 tokens)
        Returns checkpoint ID
    """
    from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
    
    logger = GitEnhancedReflexLogger(enable_git_notes=True)
    
    # Get current epistemic state
    # Create checkpoint
    checkpoint_id = logger.create_git_checkpoint(
        session_id=session_id,
        phase=phase,
        vectors=current_vectors,
        metadata=metadata or {}
    )
    
    print(f"✅ Checkpoint created: {checkpoint_id}")
    print(f"   Estimated tokens: ~46 (97.5% reduction)")
    return checkpoint_id
```

#### 1.2: `empirica checkpoint load`
```python
def load_checkpoint_command(session_id: str, max_age_hours: int = 24):
    """
    Load latest checkpoint for session.
    
    Usage:
        empirica checkpoint load --session-id abc123
    
    Result:
        Returns compressed epistemic state (~450 tokens vs 6,500)
    """
    from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
    
    logger = GitEnhancedReflexLogger(enable_git_notes=True)
    
    checkpoint = logger.load_git_checkpoint(
        session_id=session_id,
        max_age_hours=max_age_hours
    )
    
    if checkpoint:
        print(f"✅ Checkpoint loaded")
        print(f"   Created: {checkpoint['created_at']}")
        print(f"   Phase: {checkpoint['phase']}")
        print(f"   Vectors: {len(checkpoint['vectors'])} loaded")
        print(f"   Token savings: ~97.5%")
    else:
        print("⚠️  No checkpoint found")
    
    return checkpoint
```

#### 1.3: `empirica efficiency report`
```python
def efficiency_report_command(session_id: str, format: str = "markdown"):
    """
    Generate token efficiency report.
    
    Usage:
        empirica efficiency report --session-id abc123 --format markdown
    
    Result:
        Report showing baseline vs optimized token usage
    """
    from empirica.metrics.token_efficiency import TokenEfficiencyMetrics
    
    metrics = TokenEfficiencyMetrics()
    report = metrics.generate_efficiency_report(
        session_id=session_id,
        format=format
    )
    
    if format == "markdown":
        print(report)
    elif format == "json":
        import json
        print(json.dumps(report, indent=2))
    
    return report
```

**Integration:**
```python
# In cli_core.py, add subcommand group

@cli.group()
def checkpoint():
    """Git checkpoint commands for Phase 1.5"""
    pass

@checkpoint.command("create")
@click.option("--session-id", required=True)
@click.option("--phase", required=True)
def create_checkpoint(session_id, phase):
    create_checkpoint_command(session_id, phase)

@checkpoint.command("load")
@click.option("--session-id", required=True)
def load_checkpoint(session_id):
    load_checkpoint_command(session_id)

@cli.group()
def efficiency():
    """Token efficiency commands"""
    pass

@efficiency.command("report")
@click.option("--session-id", required=True)
@click.option("--format", default="markdown")
def efficiency_report(session_id, format):
    efficiency_report_command(session_id, format)
```

**Success Criteria:**
- ✅ `empirica checkpoint create` works
- ✅ `empirica checkpoint load` works
- ✅ `empirica efficiency report` works
- ✅ All commands have `--help` text
- ✅ Error handling for missing git

---

### Task 2: Metacognitive Cascade Integration ⚠️ HIGH PRIORITY
**Goal:** Automatic checkpointing during CASCADE workflow

**Files to modify:**
- `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

**What to add:**

```python
# In MetacognitiveCascade class

def __init__(self, ..., enable_git_checkpoints: bool = False):
    self.enable_git_checkpoints = enable_git_checkpoints
    
    if enable_git_checkpoints:
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        self.git_logger = GitEnhancedReflexLogger(enable_git_notes=True)
    else:
        self.git_logger = None

async def execute_preflight(self, task: str, context: dict):
    # ... existing preflight logic ...
    
    # After preflight complete
    if self.git_logger:
        checkpoint_id = self.git_logger.create_git_checkpoint(
            session_id=self.session_id,
            phase="preflight",
            vectors=preflight_vectors,
            metadata={"task": task}
        )
        logger.info(f"📌 Git checkpoint created: {checkpoint_id} (~46 tokens)")
    
    return result

async def execute_check(self, findings: list, ...):
    # ... existing check logic ...
    
    # After CHECK complete
    if self.git_logger:
        checkpoint_id = self.git_logger.create_git_checkpoint(
            session_id=self.session_id,
            phase="check",
            vectors=check_vectors,
            metadata={
                "findings": len(findings),
                "confidence": confidence_to_proceed
            }
        )
        logger.info(f"📌 Git checkpoint created: {checkpoint_id}")
    
    return result

# Similar for postflight
```

**Success Criteria:**
- ✅ Checkpoints created automatically at each phase
- ✅ Only when `enable_git_checkpoints=True`
- ✅ Doesn't break existing workflow if disabled
- ✅ Logs checkpoint creation clearly

---

### Task 3: Bootstrap Integration 🔵 MEDIUM PRIORITY
**Goal:** Users can enable git checkpoints at bootstrap

**Files to modify:**
- `empirica/bootstraps/optimal_metacognitive_bootstrap.py`

**What to add:**

```python
def __init__(
    self, 
    ai_id: str = "empirica_ai", 
    level: str = "standard",
    llm_callback=None,
    enable_git_checkpoints: bool = False  # NEW
):
    self.ai_id = ai_id
    self.level = self._normalize_level(level)
    self.llm_callback = llm_callback
    self.enable_git_checkpoints = enable_git_checkpoints  # NEW
    self.components = {}
    self.bootstrap_start_time = time.time()

def bootstrap(self):
    # ... existing bootstrap logic ...
    
    # When creating metacognitive cascade
    if 'metacognitive_cascade' in components_to_load:
        self.components['metacognitive_cascade'] = MetacognitiveCascade(
            session_id=self.session_id,
            ai_id=self.ai_id,
            enable_git_checkpoints=self.enable_git_checkpoints  # Pass through
        )
        
        if self.enable_git_checkpoints:
            print("   📌 Git checkpoints: ENABLED (97.5% token reduction)")
        else:
            print("   📌 Git checkpoints: DISABLED (use --enable-git-checkpoints)")
```

**Usage:**
```python
# Users can now enable at bootstrap
components = bootstrap_metacognition(
    ai_id="my-agent",
    level="minimal",
    enable_git_checkpoints=True  # Enable Phase 1.5!
)
```

**Success Criteria:**
- ✅ Bootstrap accepts `enable_git_checkpoints` parameter
- ✅ Passes to metacognitive cascade
- ✅ Logs status clearly
- ✅ Defaults to False (opt-in)

---

### Task 4: Documentation 📚 MEDIUM PRIORITY
**Goal:** Users know how to use Phase 1.5

**Files to create/update:**

#### 4.1: Create `docs/guides/GIT_CHECKPOINTS_GUIDE.md`
```markdown
# Using Git Checkpoints (Phase 1.5)

## Overview
Phase 1.5 provides **97.5% token reduction** through git-enhanced context loading.

## Enabling Git Checkpoints

### Via Bootstrap
```python
from empirica.bootstraps import bootstrap_metacognition

components = bootstrap_metacognition(
    ai_id="my-agent",
    level="minimal",
    enable_git_checkpoints=True  # Enable!
)
```

### Via CLI
```bash
# Create checkpoint manually
empirica checkpoint create --session-id abc123 --phase preflight

# Load checkpoint
empirica checkpoint load --session-id abc123

# Generate efficiency report
empirica efficiency report --session-id abc123
```

## How It Works
- Checkpoints stored in git notes (~46 tokens)
- Baseline session history: ~1,821 tokens
- Reduction: 97.5%
- SQLite fallback if git unavailable

## Requirements
- Git installed and available
- Repository initialized (git init)
- No special configuration needed

## Troubleshooting
[Add common issues and solutions]
```

#### 4.2: Update `docs/production/03_BASIC_USAGE.md`
Add section on enabling git checkpoints.

#### 4.3: Update README.md
Already done! ✅ (mentions 97.5% reduction)

**Success Criteria:**
- ✅ Guide created with examples
- ✅ Production docs updated
- ✅ Examples work when copy-pasted

---

### Task 5: Testing 🧪 MEDIUM PRIORITY
**Goal:** Verify everything works

**Test file:** `tests/integration/test_git_checkpoints_integration.py`

```python
def test_cli_checkpoint_create():
    """Test CLI checkpoint creation"""
    result = subprocess.run([
        "empirica", "checkpoint", "create",
        "--session-id", test_session_id,
        "--phase", "preflight"
    ], capture_output=True)
    
    assert result.returncode == 0
    assert "Checkpoint created" in result.stdout.decode()

def test_cascade_auto_checkpoint():
    """Test automatic checkpointing in cascade"""
    cascade = MetacognitiveCascade(
        session_id="test",
        enable_git_checkpoints=True
    )
    
    # Execute preflight
    result = await cascade.execute_preflight("Test task", {})
    
    # Verify checkpoint created
    checkpoint = git_logger.load_git_checkpoint("test")
    assert checkpoint is not None
    assert checkpoint['phase'] == 'preflight'

def test_bootstrap_with_git():
    """Test bootstrap with git checkpoints enabled"""
    components = bootstrap_metacognition(
        "test-agent",
        "minimal",
        enable_git_checkpoints=True
    )
    
    cascade = components['metacognitive_cascade']
    assert cascade.enable_git_checkpoints == True
```

**Success Criteria:**
- ✅ All tests pass
- ✅ CLI commands tested
- ✅ Cascade integration tested
- ✅ Bootstrap integration tested

---

## 📊 Estimated Effort

- **Task 1 (CLI):** 3 hours
- **Task 2 (Cascade):** 2 hours
- **Task 3 (Bootstrap):** 1 hour
- **Task 4 (Docs):** 2 hours
- **Task 5 (Testing):** 2 hours

**Total:** ~10 hours of focused work

---

## 🎯 Success Criteria (Overall)

**Production hardening complete when:**
1. ✅ Users can enable git checkpoints via bootstrap
2. ✅ Users can use CLI commands for checkpointing
3. ✅ Cascade automatically creates checkpoints when enabled
4. ✅ Documentation guides users through setup
5. ✅ Tests validate all integration points
6. ✅ No breaking changes to existing workflow
7. ✅ Error handling for missing git

---

## 🔄 Coordination

### Progress Tracking
Update: `COPILOT_CLAUDE_PROGRESS.md` (already exists from previous handoff)

Add section:
```markdown
## Phase 1.5 Production Hardening
- [ ] Task 1: CLI integration
- [ ] Task 2: Cascade integration
- [ ] Task 3: Bootstrap integration
- [ ] Task 4: Documentation
- [ ] Task 5: Testing
```

### Git Commits
```bash
# Commit format
git commit -m "feat: Add CLI checkpoint commands (Task 1)"
git commit -m "feat: Integrate git checkpoints into CASCADE (Task 2)"
git commit -m "feat: Enable git checkpoints in bootstrap (Task 3)"
git commit -m "docs: Add git checkpoints user guide (Task 4)"
git commit -m "test: Add git checkpoint integration tests (Task 5)"
```

---

## 📝 Notes

### Why This Matters
Phase 1.5 is validated (97.5% token reduction measured) but only accessible via MCP tools. Users need CLI and automatic integration to actually benefit from it.

### What You're Building On
- ✅ MCP layer complete (your work)
- ✅ Core GitEnhancedReflexLogger exists
- ✅ TokenEfficiencyMetrics exists
- ✅ Validation complete (Session 9)

You're making it **usable in production**.

### After This Task
Phase 1.5 will be:
- ✅ Accessible via CLI
- ✅ Automatic in CASCADE
- ✅ Documented for users
- ✅ Tested and validated
- ✅ Ready for v1.0 release

---

**This is the final piece to make Phase 1.5 production-ready! 🚀**

**Questions? Check with co-leads via progress report or git commits.**
