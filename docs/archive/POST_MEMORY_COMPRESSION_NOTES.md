# Post-Memory Compression Notes
**Created:** 2025-11-09
**Context:** Documentation cleanup session - critical fixes and gaps identified

---

## ⚠️ CRITICAL DOCUMENTATION GAP - MUST FIX

### The Onboarding Wizard Problem

**What it is:**
- `empirica/bootstraps/onboarding_wizard.py` - 6-phase interactive learning system
- Command: `empirica onboard --ai-id <ai_name>`
- Teaches through **experiential learning** (doing, not reading)

**What it does (AI-FIRST):**
1. **AI agents self-guide** through learning Empirica
2. **AI agents guide USERS** through learning Empirica (AI teaches human)
3. Tracks epistemic growth with preflight→postflight delta
4. 6 phases: Bootstrap → Self-Assessment → Workflow → Calibration → User Interaction → Validation

**THE PROBLEM:**
- Docs are too user-centric
- Not obvious that AI agents can autonomously use this
- Not clear AI can guide users (AI-teaches-human pattern)
- Buried in docs/ instead of front-and-center

**WHERE IT'S MENTIONED (poorly):**
- `00_START_HERE.md` - mentions it in step 2 but doesn't emphasize AI-first
- `ONBOARDING_GUIDE.md` - good but says "For: First-time AI agents and users" (needs stronger AI-agent focus)

**WHAT NEEDS FIXING:**

1. **00_START_HERE.md** - Rewrite step 2 to emphasize:
   ```
   ### Step 2: AI-Guided Onboarding (5 minutes)

   **For AI Agents:** Run this to learn Empirica yourself
   **For Users:** An AI agent can guide you through this

   ```bash
   empirica onboard --ai-id <your-ai-name>
   ```

   This is EXPERIENTIAL learning - you'll practice genuine self-assessment,
   not just read theory. AI agents use this to:
   - Self-guide through Empirica capabilities
   - Guide users through Empirica (AI teaches human)
   - Track epistemic growth (preflight→postflight delta)
   ```

2. **ONBOARDING_GUIDE.md** - Rewrite intro:
   ```markdown
   # Empirica Onboarding Guide

   **Primary Use:** AI agents self-guide through learning Empirica
   **Secondary Use:** AI agents guide users through learning Empirica
   **Method:** Experiential learning (do, not read)
   **Command:** `empirica onboard --ai-id <ai_name>`

   ## For AI Agents Reading This:

   This wizard teaches you how to use Empirica by having you perform
   genuine epistemic self-assessment. You'll learn by DOING:
   - Assess your state before tasks (preflight)
   - Track what you learn (postflight)
   - Measure calibration (were you overconfident?)

   You can also use this to GUIDE USERS through Empirica.

   ## For Users Reading This:

   Ask an AI agent to run the onboarding wizard. The AI will guide
   you through learning Empirica experientially.
   ```

3. **Create new doc:** `docs/AI_AGENT_FIRST.md`
   - Explain that Empirica is designed AI-agent-first
   - Humans benefit but the primary user is the AI
   - Onboarding wizard is the entry point
   - Link to SKILL.md for advanced agent usage

---

## ✅ COMPLETED IN THIS SESSION

### 1. Moved Files from Experimental → Production (5 files)
- `08_BAYESIAN_GUARDIAN.md`
- `09_DRIFT_MONITOR.md`
- `10_PLUGIN_SYSTEM.md`
- `11_DASHBOARD_MONITORING.md`
- `14_CUSTOM_PLUGINS.md`

### 2. Created New Documentation
- `12_SESSION_DATABASE.md` (650+ lines)
  - Session Database schema (12 tables)
  - Reflex Logs architecture
  - Temporal separation explanation
  - Privacy & data management

### 3. Fixed "13 vectors" → "12 vectors" (CRITICAL)

**The Correction:**
- OLD (misleading): "13 vectors"
- NEW (accurate): "12 vectors + explicit UNCERTAINTY tracking"

**Why it matters:**
- 12 vectors: 11 epistemic + 1 gate (ENGAGEMENT)
- UNCERTAINTY: Explicit meta-tracking (NOT implicit in confidence calculation)

**Files fixed (20+ occurrences):**
- `mcp_local/empirica_mcp_server.py` (9 occurrences)
- `production/05_EPISTEMIC_VECTORS.md`
- `production/00_COMPLETE_SUMMARY.md`
- `production/03_BASIC_USAGE.md`
- `production/06_CASCADE_FLOW.md`
- `production/15_CONFIGURATION.md`
- `production/18_MONITORING_LOGGING.md` (5 occurrences)
- `production/23_SESSION_CONTINUITY.md` (5 occurrences)

### 4. Fixed Import Paths (2 occurrences)
- `production/10_PLUGIN_SYSTEM.md`:
  - `from metacognitive_cascade.investigation_plugin` → `from empirica.investigation`
  - `from metacognitive_cascade.metacognitive_cascade` → `from empirica.core.metacognitive_cascade`

### 5. Deleted Redundant File
- `production/12_MCP_INTEGRATION.md` (outdated, conflicts with `04_MCP_QUICKSTART.md`)

### 6. Verified Implementations Match Docs
- ✅ CLI: `empirica` command (not `empirica-cli`) - 41 commands
- ✅ MCP: 21 tools (17 core + 4 optional modality switcher)
- ✅ Database: 12 tables (not 13)

---

## 📋 PRODUCTION VS DEV ASSESSMENT COMPLETED

### Production Website Files (~46 files)

**Root-level (8 files):**
- 00_START_HERE.md
- 02_INSTALLATION.md
- 03_CLI_QUICKSTART.md
- 04_MCP_QUICKSTART.md
- 05_ARCHITECTURE.md
- 06_TROUBLESHOOTING.md
- CLAUDE_CODE_ONBOARDING_SEQUENCE.md
- README.md

**production/ folder (25 files):**
- ALL FILES (00-23 + README) - production ready

**skills/ (1 file):**
- SKILL.md - AI agent skill for using Empirica

**guides/ selected (8 files):**
- MCP_CONFIGURATION_EXAMPLES.md
- CLI_WORKFLOW_COMMANDS_COMPLETE.md
- TRY_EMPIRICA_NOW.md
- CRITICAL_NO_HEURISTICS_PRINCIPLE.md
- CLI_GENUINE_SELF_ASSESSMENT.md
- MODALITY_SWITCHING_USAGE_GUIDE.md (mark experimental)
- setup/CLAUDE_CODE_MCP_SETUP.md
- setup/MCP_SERVERS_SETUP.md

**guides/examples/ (1 file):**
- mcp_configs/mcp_config_rovodev.json

**reference/ selected (4 files):**
- QUICK_REFERENCE.md
- BOOTSTRAP_QUICK_REFERENCE.md
- CHANGELOG.md
- DIRECTORY_STRUCTURE.md

### Dev-Only Files (~50+ files)

**Keep in empirica-dev:**
- architecture/ (9 files - all dev)
- phase_0/ (5 files - all dev)
- guides/development/ (4 files)
- guides/engineering/ (2 files)
- guides/learning/ (2 files)
- research/ (1 file)
- vision/ (2 files)
- sessions/ (session records)
- Internal analysis docs

---

## 🔧 TODO AFTER MEMORY COMPRESSION

### High Priority

1. **Fix onboarding documentation** (CRITICAL)
   - Rewrite 00_START_HERE.md step 2
   - Rewrite ONBOARDING_GUIDE.md intro
   - Create AI_AGENT_FIRST.md
   - Make it OBVIOUS AI agents can self-guide AND guide users

2. **Remove duplicate content**
   - Delete `guides/EMPIRICA_MCP_INSTALLATION.md` (redundant with 02_INSTALLATION.md + 04_MCP_QUICKSTART.md)
   - Delete `guides/MCP_CLI_INTEGRATION_COMPLETE.md` (session notes, not docs)

3. **Create modality switcher folder**
   - Move `guides/MODALITY_SWITCHING_USAGE_GUIDE.md` → `guides/experimental/modality_switcher/`
   - Mark as "Experimental - Phase 1+"
   - Clear warning about governance layer recommendation

4. **Clarify ONBOARDING_GUIDE.md location**
   - Currently in docs/ root
   - Should be in production/ OR
   - Should be referenced more prominently from 00_START_HERE.md

### Medium Priority

5. **Delete empty folders**
   - `guides/tmux/` (empty)

6. **Consolidate references**
   - Multiple docs reference non-existent files
   - Update or remove broken references

7. **Create migration script**
   - Script to organize production vs dev files
   - Manifest of what goes where

---

## 📚 KEY CONCEPTS TO REMEMBER

### Vector System (CORRECT)
- **12 vectors** in confidence calculation:
  - 1 gate: ENGAGEMENT
  - 3 foundation: KNOW, DO, CONTEXT
  - 4 comprehension: CLARITY, COHERENCE, SIGNAL, DENSITY
  - 4 execution: STATE, CHANGE, COMPLETION, IMPACT
- **UNCERTAINTY:** Explicit meta-tracking (NOT one of the 12)

### Command Names (CORRECT)
- CLI command: `empirica` (NOT `empirica-cli`)
- Onboarding: `empirica onboard --ai-id <name>`
- 41 total commands across 10 categories

### MCP Tools (CORRECT)
- 21 total: 17 core + 4 optional modality switcher
- All descriptions updated to "12 vectors"

### Database (CORRECT)
- 12 tables (not 13)
- Dual storage: SQLite + Reflex Logs (JSON)
- Temporal separation prevents prompt pollution

---

## 🚨 MEMORY COMPRESSION SURVIVAL NOTES

**If you're reading this after memory compression:**

1. **The onboarding wizard is THE critical gap**
   - It's AI-agent-first (not user-first)
   - AI agents can self-guide AND guide users
   - Not emphasized enough in docs
   - READ: `empirica/bootstraps/onboarding_wizard.py`
   - READ: `ONBOARDING_GUIDE.md`
   - FIX: `00_START_HERE.md`

2. **12 vectors, not 13**
   - We fixed 20+ occurrences in this session
   - UNCERTAINTY is explicit meta-tracking, separate from the 12

3. **Production docs are ready**
   - 25 files in production/ folder (00-23 + README)
   - All accurate as of 2025-11-09
   - Complete sequence, no gaps

4. **Duplicates still exist**
   - guides/ has some redundant content vs production/
   - Mark for deletion (see list above)

5. **Modality switcher needs own folder**
   - Currently in guides/
   - Should be guides/experimental/modality_switcher/
   - Mark as experimental (Phase 1+)

---

## 📍 WHERE WE LEFT OFF

**Task:** Documentation cleanup and production vs dev assessment
**Status:** ✅ Assessment complete, fixes applied, gaps identified
**Next:** Fix onboarding documentation (AI-agent-first emphasis)

**Key files to update next:**
1. `00_START_HERE.md` - step 2 rewrite
2. `ONBOARDING_GUIDE.md` - intro rewrite
3. Create `AI_AGENT_FIRST.md`
4. Organize modality switcher docs
5. Remove duplicates

---

**Session Duration:** ~3 hours
**Files Modified:** 20+ files
**Lines Changed:** 1000+ lines
**Critical Fixes:** Vector count, imports, onboarding clarity

**Next AI Agent:** Read this file first before continuing documentation work!
