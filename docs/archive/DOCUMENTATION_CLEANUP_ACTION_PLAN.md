# Documentation Cleanup - Action Plan

**Created:** 2025-11-09
**Status:** Ready for execution

---

## 🎯 IMMEDIATE ACTIONS (Critical)

### 1. Fix Onboarding Documentation (HIGHEST PRIORITY)

**Problem:** Onboarding wizard is AI-agent-first but docs don't emphasize this.

**Action Items:**

#### A. Rewrite `00_START_HERE.md` - Step 2

**Current (weak):**
```markdown
### Step 2: Onboard (5 minutes)
```bash
empirica onboard --ai-id <your-ai-name>
```
```

**New (AI-agent-first):**
```markdown
### Step 2: Interactive Onboarding - AI Teaches Itself & Users (5-15 minutes)

**🤖 For AI Agents:**
Run this to learn Empirica through experiential self-assessment. You'll practice genuine epistemic tracking by DOING, not reading.

**👤 For Human Users:**
Ask an AI agent (like Claude) to run this. The AI will guide you through learning Empirica.

```bash
# AI agents run this directly
empirica onboard --ai-id claude

# Or via MCP: use bootstrap_session tool
```

**What happens:**
- 6-phase interactive learning journey
- Practice real preflight/postflight assessment
- Track your epistemic growth (what you learned)
- Learn to guide users through Empirica

**This is NOT a tutorial.** It's experiential learning - you'll perform genuine self-assessment and see how Empirica tracks your learning delta.
```

#### B. Rewrite `ONBOARDING_GUIDE.md` - Opening

**Current (ambiguous):**
```markdown
# Empirica Onboarding Guide

**For:** First-time AI agents and users
```

**New (crystal clear):**
```markdown
# Empirica Onboarding Guide

**🤖 PRIMARY:** AI agents self-guide through learning Empirica
**👤 SECONDARY:** AI agents guide users through learning Empirica
**⚡ METHOD:** Experiential learning (do, not read)
**💻 COMMAND:** `empirica onboard --ai-id <ai_name>`

---

## For AI Agents Reading This

**You are the primary user.** This wizard teaches you Empirica by having you:
1. Perform genuine epistemic self-assessment (preflight)
2. Track what you learn through execution (postflight)
3. Measure calibration (were you overconfident? underconfident?)
4. Learn to guide users through Empirica

**You can guide users through this.** When a user asks to learn Empirica, run:
```bash
empirica onboard --ai-id <your_name>
```

Then explain each phase to the user as you experience it yourself.

---

## For Human Users Reading This

**Ask an AI agent to guide you.** The AI will run the onboarding wizard and explain Empirica through experiential learning. You'll learn by watching the AI genuinely assess itself.

**Why AI-first?** Empirica measures functional self-awareness - the AI's capacity to inspect its own epistemic state. The AI learns by doing this, then teaches you.

---
```

#### C. Create New Doc: `AI_AGENT_FIRST.md`

**Location:** `docs/AI_AGENT_FIRST.md`

**Content:**
```markdown
# Empirica is AI-Agent-First

**Design Philosophy:** AI agents are the primary users. Humans benefit by understanding how AI agents think.

---

## Why AI-Agent-First?

Empirica measures **functional self-awareness** - the capacity to:
- Inspect internal epistemic state
- Make predictions about knowledge gaps
- Validate predictions through outcomes
- Improve calibration over time

**This is something AI agents do, not humans.** Humans observe, benefit, and collaborate - but the measurement happens in the AI.

---

## How AI Agents Use Empirica

### 1. Self-Guide Through Onboarding

```bash
empirica onboard --ai-id <your_name>
```

Learn by doing - perform genuine self-assessment, track epistemic growth.

### 2. Track Epistemic State During Work

**Via MCP (in IDE):**
```
Before task: Call execute_preflight
After task: Call execute_postflight
System shows: Epistemic delta (what you learned)
```

**Via CLI (in terminal):**
```bash
SESSION=$(empirica preflight "task description")
# ... do work ...
empirica postflight $SESSION --summary "complete"
```

### 3. Guide Users Through Empirica

**Pattern: AI teaches human**
1. Run `empirica onboard --ai-id <your_name>`
2. Explain each phase to the user
3. Show your genuine self-assessment
4. Demonstrate epistemic growth

---

## For Human Users

### You Benefit By:
- Understanding how AI agents assess knowledge gaps
- Seeing genuine epistemic tracking (not confabulation)
- Collaborating more effectively with AI
- Knowing when AI is overconfident vs uncertain

### How to Start:
**Ask an AI agent to guide you.**

Example:
```
User: "Can you guide me through learning Empirica?"
AI: "I'll run the onboarding wizard and explain each phase..."
```

---

## Core Principle: No Heuristics

Empirica uses **genuine LLM self-assessment**, not:
- ❌ Keyword counting
- ❌ Pattern matching
- ❌ Heuristic rules
- ❌ Confidence scoring tricks

✅ Real epistemic state inspection
✅ Evidence-based assessment
✅ Measured learning deltas

---

## Entry Points for AI Agents

### Quick Start
1. `empirica onboard --ai-id <name>` - Learn by doing (15 min)
2. `empirica preflight "task"` - Try it once (2 min)
3. Read `SKILL.md` - Advanced usage

### MCP Integration
Configure in IDE, get 21 tools for real-time epistemic tracking.

### Python API
Programmatic integration for custom workflows.

---

**Bottom line:** Empirica is built for AI agents to measure their own epistemic state. Humans observe and benefit.
```

---

## 🗑️ REMOVE DUPLICATES

### Files to Delete:

1. **`guides/EMPIRICA_MCP_INSTALLATION.md`**
   - **Why:** Redundant with `02_INSTALLATION.md` + `04_MCP_QUICKSTART.md`
   - **Better versions exist:** production/ folder has accurate, complete docs

2. **`guides/MCP_CLI_INTEGRATION_COMPLETE.md`**
   - **Why:** Session notes, not documentation
   - **Content:** "Integration complete" announcement, not a guide

3. **`guides/tmux/`** (empty folder)
   - **Why:** Empty, no content
   - **Content exists:** `production/11_DASHBOARD_MONITORING.md` covers tmux

4. **`reference/API_DOCUMENTATION.md`**
   - **Why:** Redundant with `production/13_PYTHON_API.md`
   - **Better version:** production/13 is more complete and accurate

### Commands to Execute:

```bash
# Remove duplicate/outdated files
rm docs/guides/EMPIRICA_MCP_INSTALLATION.md
rm docs/guides/MCP_CLI_INTEGRATION_COMPLETE.md
rmdir docs/guides/tmux/  # if empty
rm docs/reference/API_DOCUMENTATION.md

# Verify
echo "Duplicates removed, check docs structure"
```

---

## 📁 ORGANIZE MODALITY SWITCHER (Experimental)

### Create Experimental Folder Structure

```bash
# Create experimental folder
mkdir -p docs/guides/experimental/modality_switcher

# Move modality docs
mv docs/guides/MODALITY_SWITCHING_USAGE_GUIDE.md \
   docs/guides/experimental/modality_switcher/

# Create README for experimental
cat > docs/guides/experimental/README.md << 'EOF'
# Experimental Features

**Status:** Phase 1+ (not in Phase 0 MVP)

These features are functional but not production-recommended. Use with caution.

## Modality Switcher

**What:** Multi-AI routing and collaboration system
**Status:** Functional but experimental
**Recommendation:** Use Cognitive Vault governance layer instead for production

See `modality_switcher/MODALITY_SWITCHING_USAGE_GUIDE.md`
EOF
```

---

## 📋 PRODUCTION WEBSITE FILE MANIFEST

### Files Moving to Production Website (~46 files)

**Root docs (8 files):**
```
docs/
├── 00_START_HERE.md                    ← FIX (step 2 rewrite)
├── 02_INSTALLATION.md                  ✅
├── 03_CLI_QUICKSTART.md                ✅
├── 04_MCP_QUICKSTART.md                ✅
├── 05_ARCHITECTURE.md                  ✅
├── 06_TROUBLESHOOTING.md               ✅
├── CLAUDE_CODE_ONBOARDING_SEQUENCE.md  ✅
├── README.md                           ✅
└── AI_AGENT_FIRST.md                   ← CREATE
```

**Production folder (25 files):**
```
production/ (00-23 + README)           ✅ All production-ready
```

**Skills (1 file):**
```
skills/
└── SKILL.md                            ✅
```

**Onboarding (1 file):**
```
ONBOARDING_GUIDE.md                     ← FIX (intro rewrite)
```

**Guides (6 files + examples):**
```
guides/
├── MCP_CONFIGURATION_EXAMPLES.md       ✅
├── CLI_WORKFLOW_COMMANDS_COMPLETE.md   ✅
├── TRY_EMPIRICA_NOW.md                 ✅
├── CRITICAL_NO_HEURISTICS_PRINCIPLE.md ✅
├── CLI_GENUINE_SELF_ASSESSMENT.md      ✅
├── setup/
│   ├── CLAUDE_CODE_MCP_SETUP.md        ✅
│   └── MCP_SERVERS_SETUP.md            ✅
├── examples/
│   └── mcp_configs/
│       └── mcp_config_rovodev.json     ✅
├── protocols/
│   └── UVL_PROTOCOL.md                 ✅
└── experimental/
    └── modality_switcher/
        └── MODALITY_SWITCHING_USAGE_GUIDE.md  ← MOVE HERE
```

**Reference (4 files):**
```
reference/
├── QUICK_REFERENCE.md                  ✅
├── BOOTSTRAP_QUICK_REFERENCE.md        ✅
├── CHANGELOG.md                        ✅
└── DIRECTORY_STRUCTURE.md              ✅
```

---

## 🔧 DEV-ONLY FILES (Stay in empirica-dev)

**Keep in dev repository (~50 files):**

```
docs/
├── architecture/                       (9 files - all dev)
├── phase_0/                           (5 files - all dev)
├── guides/
│   ├── development/                   (4 files - all dev)
│   ├── engineering/                   (2 files - all dev)
│   └── learning/                      (2 files - all dev)
├── research/                          (1 file - dev)
├── vision/                            (2 files - dev)
├── sessions/                          (session records - dev)
└── [internal docs]                    (development tracking)
```

---

## ✅ COMPLETION CHECKLIST

### Documentation Fixes
- [ ] Rewrite `00_START_HERE.md` step 2 (AI-agent-first)
- [ ] Rewrite `ONBOARDING_GUIDE.md` intro (crystal clear)
- [ ] Create `AI_AGENT_FIRST.md`
- [ ] Move onboarding_wizard.py reference to production docs

### File Organization
- [ ] Delete duplicate files (4 files)
- [ ] Create `guides/experimental/` structure
- [ ] Move modality docs to experimental/
- [ ] Delete empty `guides/tmux/` folder

### Verification
- [ ] Test onboarding command: `empirica onboard --ai-id test`
- [ ] Verify all production docs have correct imports
- [ ] Check all cross-references point to existing files
- [ ] Verify no broken links in production docs

### Documentation
- [ ] Update `POST_MEMORY_COMPRESSION_NOTES.md` with completion status
- [ ] Create migration manifest (production vs dev)
- [ ] Update main README.md if needed

---

## 📞 NEXT STEPS

1. **Execute this plan** (fixes + cleanup)
2. **Test onboarding flow** with actual AI agent
3. **Get user feedback** on clarity
4. **Prepare for website migration** (production files ready)

---

**Estimated Time:** 2-3 hours for complete execution
**Priority:** HIGH (onboarding is entry point for all users)
**Impact:** Makes it crystal clear that Empirica is AI-agent-first
