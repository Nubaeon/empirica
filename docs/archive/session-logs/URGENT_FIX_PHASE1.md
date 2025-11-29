# URGENT: Phase 1 Git Automation Issue & Fix

**Date:** 2025-11-27  
**Issue:** Automatic checkpoints don't work with `--prompt-only` flag  
**Root Cause:** Code flow exits before checkpoint creation  
**Status:** IDENTIFIED - Fix options below

---

## 🐛 Root Cause Analysis

### The Problem

When mini-agent uses:
```bash
empirica preflight "task" --ai-id mini-agent --prompt-only
```

The function flow is:
1. Line 100: Check if `--prompt-only` flag is set
2. Line 110: **RETURN IMMEDIATELY** with prompt JSON
3. Line 257: Checkpoint code never reached ❌

### Why This Happens

The `--prompt-only` flag is designed for AI agents to:
1. Get the self-assessment prompt
2. Perform genuine self-assessment
3. Call `submit_preflight_assessment` with vectors

But mini-agent is stopping at step 1 and not calling `submit_preflight_assessment`.

---

## ✅ Solution Options

### Option 1: Use MCP Tools (RECOMMENDED)

Mini-agent should use the proper MCP workflow:

```python
# Step 1: Get prompt
result = execute_preflight(
    session_id="test",
    prompt="Task description"
)

# Step 2: Perform self-assessment (genuine)
vectors = {
    "engagement": 0.85,
    "know": 0.70,
    ...
}

# Step 3: Submit assessment (THIS creates checkpoint!)
submit_preflight_assessment(
    session_id="test",
    ai_id="mini-agent",
    vectors=vectors
)
```

The `submit_preflight_assessment` MCP tool is where checkpoints are created.

---

### Option 2: CLI with Full Assessment

Use CLI with `--assessment-json`:

```bash
# Step 1: Get prompt
empirica preflight "task" --ai-id mini-agent --prompt-only > /tmp/prompt.json

# Step 2: AI performs self-assessment (creates vectors JSON)

# Step 3: Submit with assessment
empirica preflight "task" --ai-id mini-agent --assessment-json /tmp/assessment.json
# ^ This creates checkpoint
```

---

### Option 3: Quick Code Fix (If needed)

Move checkpoint creation to happen even with `--prompt-only`:

```python
# At line 100, BEFORE the early return:
if hasattr(args, 'prompt_only') and args.prompt_only:
    # Create checkpoint even for prompt-only mode
    try:
        from empirica.core.canonical.empirica_git import auto_checkpoint
        auto_checkpoint(
            session_id=session_id,
            ai_id=ai_id,
            phase='PREFLIGHT_PROMPT',  # Different phase name
            vectors={},  # No vectors yet
            round_num=0,
            metadata={'prompt_only': True}
        )
    except Exception:
        pass
    
    # Then return prompt as before
    output = {...}
    print(json.dumps(output, indent=2))
    return
```

**Downside:** Creates checkpoint with no vectors (not very useful).

---

## 🎯 Recommended Fix for Mini-Agent

### The Issue

Mini-agent test used:
```bash
empirica preflight "test" --ai-id mini-agent --prompt-only
# Returns immediately, no checkpoint created
```

### The Solution

Mini-agent should use MCP tools OR complete the full CLI workflow:

**MCP Workflow (Best):**
```python
# This is the proper Empirica workflow for AIs
from empirica_mcp import execute_preflight, submit_preflight_assessment

# Get prompt
prompt_result = execute_preflight(
    session_id="test-session",
    prompt="Test task"
)

# Perform genuine self-assessment
assessment = perform_self_assessment(prompt_result['self_assessment_prompt'])

# Submit assessment (creates checkpoint automatically!)
submit_result = submit_preflight_assessment(
    session_id="test-session",
    ai_id="mini-agent",
    vectors=assessment['vectors']
)
```

**CLI Workflow (Alternative):**
```bash
# Get prompt
OUTPUT=$(empirica preflight "task" --ai-id mini-agent --prompt-only)

# Perform self-assessment (AI does this)
# ... creates vectors JSON ...

# Submit with assessment
empirica preflight "task" --ai-id mini-agent \
  --session-id test-session \
  --assessment-json '{"vectors": {...}}'
# ^ Creates checkpoint here
```

---

## 📊 Why MCP Tools Work

The MCP tools use a different code path:

```
MCP Tool: submit_preflight_assessment
  └─> Routes to CLI: empirica preflight-submit
      └─> Stores in database
      └─> Creates git checkpoint ✅
      └─> Returns confirmation
```

The `submit` commands are where checkpoints are created, not the initial `--prompt-only` call.

---

## 🔧 Immediate Fix for Tests

### Update Test 1 in MINI_AGENT_TEST_SUITE.md

**Current (Broken):**
```bash
empirica preflight "test" --ai-id mini-agent --prompt-only
# Returns immediately, no checkpoint
```

**Fixed:**
```bash
# Use MCP tools for proper workflow
python3 << 'EOF'
from empirica.cli.command_handlers.cascade_commands import handle_preflight_submit_command
import argparse

# Create mock args
args = argparse.Namespace(
    session_id='test-123',
    ai_id='mini-agent',
    vectors='{"engagement": 0.85, "know": 0.7, "do": 0.7, "uncertainty": 0.2}',
    output='json'
)

# This creates checkpoint
handle_preflight_submit_command(args)
EOF

# Verify checkpoint created
git notes --ref=empirica/checkpoints list
```

---

## 📝 Status

**Current State:**
- ✅ Checkpoint code works (tested manually)
- ✅ MCP tools work (they use submit commands)
- ❌ CLI `--prompt-only` skips checkpoint (by design)
- ❌ Mini-agent tests used wrong workflow

**Fix Required:**
- [ ] Mini-agent should use MCP workflow
- [ ] OR use CLI with --assessment-json
- [ ] Update test suite to use correct workflow

**No code changes needed** - this is a workflow documentation issue, not a bug.

---

## 💡 Key Insight

The Phase 1 implementation is **correct**. The issue is that:

1. `--prompt-only` is designed to return just the prompt (for AIs to self-assess)
2. Checkpoints are created when assessment is submitted
3. Mini-agent stopped after getting the prompt and never submitted

**Mini-agent needs to complete the full workflow:**
```
Get Prompt → Self-Assess → Submit Assessment (checkpoint created here)
```

Not just:
```
Get Prompt → Stop ❌
```

---

*This is a workflow/documentation issue, not a code bug!*
