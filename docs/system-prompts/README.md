# System Prompts - Architecture v1.2.1

**Multi-AI system prompt management for Empirica**

---

## Architecture Overview

Empirica uses a **canonical core + model deltas** architecture:

```
CANONICAL_CORE.md          <- AI-agnostic source of truth (128 lines)
      |
      + model_deltas/
      |     claude.md      <- Claude-specific additions
      |     (qwen.md)      <- (add as needed)
      |     (gemini.md)    <- (add as needed)
      |
      v
sync_system_prompts.py     <- Generates model-specific variants
      |
      v
CLAUDE.md, QWEN.md, GEMINI.md, COPILOT_INSTRUCTIONS.md, ROVODEV.md
```

---

## Quick Start

### For AI Agents

Use the appropriate model-specific prompt:

| Model | File | Notes |
|-------|------|-------|
| Claude Code | `CLAUDE.md` | Core + Claude delta (semantic search, handoffs) |
| Qwen | `QWEN.md` | Core only |
| Gemini | `GEMINI.md` | Core only |
| GitHub Copilot | `COPILOT_INSTRUCTIONS.md` | Core only |
| Rovo Dev | `ROVODEV.md` | Core only |

### Installation

```bash
# Sync prompts from canonical core
python3 scripts/sync_system_prompts.py

# Install to system locations
./scripts/install_system_prompts.sh
```

---

## Files in This Directory

### Source of Truth

1. **CANONICAL_CORE.md** - AI-agnostic core prompt (~128 lines)
   - All shared workflow: CASCADE, vectors, breadcrumbs
   - Edit this to change behavior for ALL AIs

2. **model_deltas/** - Model-specific additions
   - `claude.md` - Semantic search triggers, epistemic continuity, self-improvement
   - Add others as needed (qwen.md, gemini.md, etc.)

### Generated (DO NOT EDIT DIRECTLY)

3. **CLAUDE.md** - Generated from core + claude.md delta
4. **QWEN.md** - Generated from core only
5. **GEMINI.md** - Generated from core only
6. **COPILOT_INSTRUCTIONS.md** - Generated from core only
7. **ROVODEV.md** - Generated from core only

### Reference

8. **CUSTOMIZATION_GUIDE.md** - When and how to customize
9. **INSTALLATION.md** - Detailed installation instructions
10. **QUICK_REFERENCE_WEB.md** - Web-friendly quick reference

---

## Workflow

### Making Changes

1. **For ALL AIs:** Edit `CANONICAL_CORE.md`
2. **For specific AI:** Edit/create `model_deltas/<model>.md`
3. **Regenerate:** `python3 scripts/sync_system_prompts.py`
4. **Install:** `./scripts/install_system_prompts.sh`

### Live Tuning (Claude)

`~/.claude/CLAUDE.md` is kept separate for live tuning during development.
It may diverge from the repo version. Sync manually when stable.

---

## Key Concepts

### CASCADE Workflow
```
PREFLIGHT → NOETIC → CHECK → PRAXIC → POSTFLIGHT
```

### 13 Epistemic Vectors
- Foundation: know, do, context
- Comprehension: clarity, coherence, signal, density
- Execution: state, change, completion, impact
- Meta: engagement, uncertainty

### Breadcrumbs
```bash
empirica finding-log --finding "..." --impact 0.7
empirica unknown-log --unknown "..."
empirica deadend-log --approach "..." --why-failed "..."
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.2.1 | 2026-01-01 | Canonical core + model deltas architecture |
| v4.0 | 2025-12 | Single canonical prompt (deprecated) |

---

**Syncs with:** Empirica v1.2.1
