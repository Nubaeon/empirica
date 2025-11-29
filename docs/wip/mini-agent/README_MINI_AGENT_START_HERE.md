# 🚀 Mini-Agent: Start Here

**Quick Start Guide for Phase 1/2/3 Testing**

---

## ⚡ Fastest Path to Testing

### Step 1: Run Quick Test (30 seconds)

```bash
bash test_working_checkpoint.sh
```

**Expected output:**
```
🧪 Phase 1 Checkpoint Test - CORRECT Workflow
✓ Prompt received
✓ Assessment created
✓ Assessment submitted
```

---

### Step 2: Verify System Working

```bash
# Check session database
ls -lh .empirica/sessions/sessions.db

# Check git notes
git notes --ref=empirica/checkpoints list
```

---

### Step 3: Review Documentation

1. **`MINI_AGENT_TESTING_GUIDE.md`** - Complete testing guide (all phases)
2. **`MCP_CLI_MAPPING_COMPLETE.md`** - Tool/command reference
3. **`docs/examples/assessment_format_example.json`** - Copy/paste ready

---

## 🎯 What Was Fixed

**Issue:** Assessment format mismatch causing parse errors

**Solution:** Updated format from flat → nested structure

**Files ready:**
- ✅ Working test scripts
- ✅ Complete documentation (49.8 KB)
- ✅ Format examples
- ✅ MCP-CLI mappings

---

## 📋 Testing Phases

### Phase 1: Git Automation
```bash
empirica preflight "task" \
    --ai-id mini-agent \
    --assessment-json docs/examples/assessment_format_example.json \
    --json
```

### Phase 2: Identity & Signing
```bash
empirica identity-create --ai-id mini-agent
empirica preflight "task" --sign --assessment-json FILE
```

### Phase 3: Goal Discovery
```bash
empirica goal-create --ai-id mini-agent --objective "..." --scope project_wide
empirica goal-discover --ai-id mini-agent
```

---

## 🔑 Key Format Difference

**CLI requires nested format:**
```json
{
  "engagement": {"score": 0.85, "rationale": "..."},
  "foundation": {
    "know": {"score": 0.70, "rationale": "..."}
  }
}
```

**MCP accepts flat format:**
```json
{
  "vectors": {
    "engagement": 0.85,
    "know": 0.70
  }
}
```

See `docs/examples/assessment_format_example.json` for complete example.

---

## 📚 Full Documentation

- `MINI_AGENT_TESTING_GUIDE.md` - Testing workflows
- `MCP_CLI_MAPPING_COMPLETE.md` - Command reference  
- `FINAL_SUMMARY_FOR_MINI_AGENT.md` - Quick summary
- `HANDOFF_COMPLETE_READY_FOR_MINI_AGENT.md` - Full context

---

## ✅ Status

**All phases ready for testing!**

Start with: `bash test_working_checkpoint.sh`

Then proceed to: `MINI_AGENT_TESTING_GUIDE.md`

---

*Everything is ready. Good luck with testing!* 🎉
