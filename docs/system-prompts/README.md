# System Prompts - README

**Unified system prompt architecture for Empirica v4.0**

---

## Quick Start

**Use this prompt for all AI agents:**

📄 **[CANONICAL_SYSTEM_PROMPT.md](CANONICAL_SYSTEM_PROMPT.md)**

Copy the prompt from this file and paste it into your AI's system prompt field. No customization needed for 99% of cases.

---

## Files in This Directory

### Active (v4.0)

1. **CANONICAL_SYSTEM_PROMPT.md** ⭐
   - Single source of truth
   - Works for all AI models
   - ~1200 tokens (includes goal/subtask tracking)
   - Use this for everything

2. **CUSTOMIZATION_GUIDE.md**
   - When to customize (rare cases)
   - How to customize safely
   - Examples and validation checklist

### Reference

3. **COMPLETE_MCP_TOOL_REFERENCE.md**
   - Detailed tool documentation
   - Parameter specifications
   - Usage examples

4. **OPTIMIZATION_ANALYSIS.md**
   - Token optimization research
   - Compression strategies
   - Historical context

### Deprecated

All other prompts moved to `archive/system-prompts-deprecated/`:
- `ai-agents/` - Model-specific prompts (no longer needed)
- `development/` - Development variants (consolidated)
- `comprehensive/` - Old generic prompts (replaced)

---

## Migration Guide

### From Old Prompts → Canonical

**If you're using:**
- `ai-agents/CLAUDE.md`
- `ai-agents/QWEN.md`
- `ai-agents/MINIMAX.md`
- `development/SYSTEM_PROMPT_DEV_*.md`
- `comprehensive/GENERIC_EMPIRICA_SYSTEM_PROMPT.md`

**Switch to:**
- `CANONICAL_SYSTEM_PROMPT.md`

**Why?**
- Single source of truth (easier maintenance)
- Latest features (MCO, Decision Logic, ScopeVector, Drift Monitor)
- Model-agnostic (works for all AIs)
- Actively maintained

---

## Key Features

### Architecture

1. **CASCADE Workflow**
   - PREFLIGHT → (CHECK) → POSTFLIGHT
   - Explicit epistemic self-assessment
   - CHECK phase as decision gate

2. **Goals & Subtasks**
   - ScopeVector dimensions (breadth, duration, coordination)
   - Track findings, unknowns, dead ends
   - Decision quality + continuity

3. **MCO (Multi-Agent Coordination)**
   - 6 personas (researcher, implementer, reviewer, coordinator, learner, expert)
   - Dynamic configuration via YAML

4. **Git Integration**
   - 85% token reduction (checkpoints)
   - 90% token reduction (handoffs)
   - Cross-AI discovery

5. **Drift Monitor**
   - Automatic at CHECK phase
   - Flags epistemic drops >0.2

---

## Directory Structure

```
docs/system-prompts/
├── CANONICAL_SYSTEM_PROMPT.md      ⭐ Use this
├── CUSTOMIZATION_GUIDE.md          📖 When to customize
├── README.md                        📄 This file
├── COMPLETE_MCP_TOOL_REFERENCE.md  📚 Tool docs
├── OPTIMIZATION_ANALYSIS.md        🔬 Research
└── archive/
    └── system-prompts-deprecated/  🗄️ Old prompts
        ├── ai-agents/
        ├── development/
        ├── comprehensive/
        └── quick-reference/
```

---

## FAQ

### Q: Which prompt should I use?
**A:** `CANONICAL_SYSTEM_PROMPT.md` for 99% of cases.

### Q: Do I need different prompts for different AI models?
**A:** No. The canonical prompt works for all models (Claude, Gemini, Qwen, GPT-4, etc.).

### Q: Can I customize the prompt?
**A:** Rarely needed. See `CUSTOMIZATION_GUIDE.md` for specific cases.

### Q: What happened to the old prompts?
**A:** Moved to `archive/system-prompts-deprecated/` for reference.

### Q: How do I update to the latest version?
**A:** Replace your current prompt with `CANONICAL_SYSTEM_PROMPT.md`.

### Q: Where are the MCP tool details?
**A:** See `COMPLETE_MCP_TOOL_REFERENCE.md`.

---

## Support

**Issues?** Check:
1. Canonical prompt (`CANONICAL_SYSTEM_PROMPT.md`)
2. Customization guide (`CUSTOMIZATION_GUIDE.md`)
3. Tool reference (`COMPLETE_MCP_TOOL_REFERENCE.md`)
4. Main docs (`../`)

---

**Version:** Empirica v4.0