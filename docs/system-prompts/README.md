# System Prompts - README

**Unified system prompt architecture for Empirica v2.0**

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
   - ~1200 tokens (added goal/subtask tracking)
   - Use this for everything
   - **NEW:** Goal tree tracking for decision quality + continuity + audit

2. **CUSTOMIZATION_GUIDE.md**
   - When to customize (rare cases)
   - How to customize safely
   - Examples and validation checklist

3. **MIGRATION_GUIDE.md**
   - Migrating from old/deprecated prompts
   - What changed in v2.0
   - Common migration issues

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
- v2.0 features (MCO, Decision Logic, ScopeVector, Drift Monitor)
- Model-agnostic (works for all AIs)
- Actively maintained

---

## What's New in v2.0

### Architecture Changes

1. **Session Structure Clarification**
   - **Session-level**: BOOTSTRAP (once per session)
   - **Goal-level**: PREFLIGHT → CASCADE → POSTFLIGHT
   - **CASCADE**: Implicit work (investigate → plan → act) with explicit CHECK gates
   - **Calibration**: PREFLIGHT and POSTFLIGHT deltas measure learning; CHECK provides intermediate points for retrospective analysis

2. **MCO Architecture**
   - 5 YAML configs (personas, cascade_styles, goal_scopes, model_profiles, protocols)
   - 6 personas (researcher, implementer, reviewer, coordinator, learner, expert)
   - Dynamic configuration loading

3. **Decision Logic**
   - Automatic comprehension + foundation checks
   - Three outcomes: CREATE_GOAL, INVESTIGATE_FIRST, ASK_CLARIFICATION

4. **ScopeVector Goals**
   - 3D numeric dimensions (breadth, duration, coordination)
   - Replaces categorical enums

5. **Git Integration**
   - ~85% token reduction (checkpoints)
   - ~90% token reduction (handoffs)
   - Cross-AI discovery via git notes

6. **Drift Monitor**
   - Automatic at CHECK phase
   - Compares to last 5 checkpoints
   - Flags drops >0.2, critical if >0.5

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

### Q: How do I update to v2.0?
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

**Last Updated:** 2025-11-30  
**Version:** 2.0  
**Maintainer:** Empirica Core Team