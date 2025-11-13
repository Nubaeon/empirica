# Documentation Organization Plan - 2025-10-31

**Current State:**
- **51 MD files** in root directory (/)
- **63 MD files** in docs/ directory
- **Total:** 114 markdown files need organization

**Goal:** Organize into semantic folders, keep only essential docs in root

---

## 📋 Root Directory - Keep These (Essential)

### Keep in Root (9 files)
1. **README.md** ⭐ - Main project README
2. **CONTRIBUTING.md** - How to contribute
3. **CURRENT_STATUS_v2.1.md** ⭐ - Current status (living doc)
4. **REMAINING_TASKS.md** ⭐ - Task tracking (living doc)
5. **QUICK_REFERENCE.md** - Quick start guide
6. **LICENSE** - License file (if exists)
7. **CONTINUITY_WORKS_DEMO.md** - Recent demo (2025-10-31)
8. **DOCUMENTATION_AUDIT_2025_10_31.md** - Recent audit (2025-10-31)
9. **SESSION_2025_10_31_DOCUMENTATION_CLEANUP.md** - Recent session (2025-10-31)

---

## 📁 Move to docs/deprecated/ (Historical/Old)

### Session Summaries (6 files) → `docs/deprecated/session_summaries/`
1. SESSION_ACCOMPLISHMENTS_20251030.md
2. SESSION_COMPLETE_2025_10_30.md
3. SESSION_RESUME_COMPLETE.md
4. COMPLETE_SESSION_FINAL.md
5. SESSION_CONTINUITY_DESIGN.md (old design, superseded)

### Implementation Status (Old) (8 files) → `docs/deprecated/implementation_status/`
1. EMPIRICA_INTEGRATION_STATUS.md
2. ENHANCED_CASCADE_IMPLEMENTATION_STATUS.md
3. ENHANCED_CASCADE_IMPLEMENTATION_SUMMARY.md
4. ENHANCED_CASCADE_READY.md
5. COMPONENT_AUDIT_STATUS.md
6. PHASE_1_2_FIXES_APPLIED.md
7. PHASE_3_IMPLEMENTATION_COMPLETE.md
8. FIXES_APPLIED.md

### Old Specs/Plans (7 files) → `docs/deprecated/specs_and_plans/`
1. EMPIRICA_SYSTEM_SPECIFICATION_COMPLETE.md
2. IMPLEMENTATION_PLAN.md
3. FOLDER_STRUCTURE_CLARIFICATION.md
4. BOOTSTRAP_VS_SKILLS_EVALUATION.md
5. CRITICAL_FIXES_NEEDED.md (old)
6. DOCS_UPDATED_PHASE_1_2.md (old)
7. WORKFLOW_COMPONENTS_IMPLEMENTATION.md (old)

### MCP Integration History (5 files) → `docs/deprecated/mcp_integration/`
1. MCP_ASSUMPTIONS_DOCUMENTED.md
2. MCP_IMPLEMENTATION_SUMMARY.md
3. MCP_INTEGRATION_STATUS.md
4. MCP_INTEGRATION_SUMMARY.md
5. QUICK_MCP_SETUP.md (superseded by production docs)

---

## 📁 Move to docs/guides/ (Reference Guides)

### Development Guides (4 files) → `docs/guides/development/`
1. AI_COMPONENT_GUIDE.md
2. AI_DEVELOPMENT_GUIDE.md
3. AI_VALIDATION_INSTRUCTIONS.md
4. MULTI_AI_COLLABORATION_GUIDE.md

### Setup/Configuration (3 files) → `docs/guides/setup/`
1. EMPIRICA_MCP_INTEGRATION_SPEC.md (current spec)
2. QWEN_GEMINI_TESTING_GUIDE.md
3. ADAPTIVE_SESSION_LOADING_ANALYSIS.md

### Engineering Guidelines (2 files) → `docs/guides/engineering/`
1. SEMANTIC_ENGINEERING_GUIDELINES.md
2. SEMANTIC_ONTOLOGY.md

### Learning/Training (2 files) → `docs/guides/learning/`
1. COMPLETE_LEARNING_DOCUMENTATION.md
2. "AI Self awareness - full reference.md"

### TMUX Guides (3 files) → `docs/guides/tmux/`
1. TMUX_DEBUGGING_PROTOCOL.md
2. TMUX_EXTENSION_SIMPLIFIED.md
3. TMUX_SELF_ORCHESTRATION_GUIDE.md

### Protocols (1 file) → `docs/guides/protocols/`
1. UVL_PROTOCOL.md

---

## 📁 Move to docs/architecture/ (Architecture Docs)

### From Root (1 file) → `docs/architecture/`
1. CASCADE_FIXED_INTERACTIVE_MODE.md

---

## 📁 Organize docs/ Directory (63 files)

### Keep in docs/ (Core References) - Move to docs/reference/
1. ARCHITECTURE_MAP.md ⭐
2. EMPIRICA_CASCADE_WORKFLOW_SPECIFICATION.md ⭐
3. DIRECTORY_STRUCTURE.md

### Session Summaries → `docs/deprecated/session_summaries_docs/`
All the session completion files in docs/:
- 13TH_VECTOR_SESSION_SUMMARY.md
- 13TH_VECTOR_UNCERTAINTY_COMPLETE.md
- ACTION_HOOKS_FINAL_COMPLETE.md
- ACTION_HOOKS_INTEGRATION_COMPLETE.md
- AUTO_TRACKING_INTEGRATION.md
- AUTO_TRACKING_REFLEX_LOGS_COMPLETE.md
- BAYESIAN_DRIFT_INTEGRATION_COMPLETE.md
- BOOTSTRAP_FIX_COMPLETE.md
- BOOTSTRAP_FIXES_COMPLETE.md
- BOOTSTRAP_REFACTOR_COMPLETE.md
- CANONICAL_GOAL_ORCHESTRATOR_COMPLETE.md
- COMPLETE_INTEGRATION_SUMMARY.md
- (etc... ~30+ completion docs)

### Analysis/Planning Docs → `docs/deprecated/analysis/`
- ARCHITECTURE_ALIGNMENT_ANALYSIS.md
- BOOTSTRAP_INTEGRATION_ANALYSIS.md
- BOOTSTRAP_VALIDATION_REPORT.md
- COGNITIVE_VAULT_ANALYSIS.md
- COMPONENT_ANALYSIS_AND_PRUNING_PLAN.md
- DEEP_COMPONENT_ANALYSIS.md
- EMPIRICA_LIVE_TEST_ANALYSIS.md
- (etc...)

### Integration/Refactor Docs → `docs/deprecated/integration/`
- CANONICAL_INTEGRATION_STATUS.md
- EMPIRICA_CANONICAL_REFACTOR_PLAN.md
- FINAL_INTEGRATION_PLAN.md
- BAYESIAN_INTEGRATION_GUIDE.md
- (etc...)

---

## 🎯 Proposed Final Structure

```
/empirica/
├── README.md                    ⭐ Keep - Main README
├── CONTRIBUTING.md              ⭐ Keep - How to contribute
├── CURRENT_STATUS_v2.1.md       ⭐ Keep - Current status
├── REMAINING_TASKS.md           ⭐ Keep - Task tracking
├── QUICK_REFERENCE.md           ⭐ Keep - Quick start
├── CONTINUITY_WORKS_DEMO.md     ⭐ Keep - Recent demo (Oct 31)
├── DOCUMENTATION_AUDIT_2025_10_31.md  ⭐ Keep - Recent audit
├── SESSION_2025_10_31_DOCUMENTATION_CLEANUP.md  ⭐ Keep - This session
├── resume_session.py            ⭐ Keep - CLI tool
│
├── docs/
│   ├── production/              ✅ Already organized (35 files)
│   ├── empirica_skills/         ✅ Already organized (3 files)
│   │
│   ├── reference/               🆕 Core references
│   │   ├── ARCHITECTURE_MAP.md
│   │   ├── EMPIRICA_CASCADE_WORKFLOW_SPECIFICATION.md
│   │   └── DIRECTORY_STRUCTURE.md
│   │
│   ├── guides/                  🆕 User guides
│   │   ├── development/         (4 files)
│   │   ├── setup/               (3 files)
│   │   ├── engineering/         (2 files)
│   │   ├── learning/            (2 files)
│   │   ├── tmux/                (3 files)
│   │   └── protocols/           (1 file)
│   │
│   ├── architecture/            🆕 Architecture deep dives
│   │   └── CASCADE_FIXED_INTERACTIVE_MODE.md
│   │
│   └── deprecated/              🆕 Historical docs
│       ├── session_summaries/        (6 root files)
│       ├── session_summaries_docs/   (~30 docs files)
│       ├── implementation_status/    (8 files)
│       ├── specs_and_plans/          (7 files)
│       ├── mcp_integration/          (5 files)
│       ├── analysis/                 (~15 files)
│       └── integration/              (~10 files)
│
├── deprecated/                  ✅ Already exists
│   └── session_summaries_2025_10_30/  (5 files we just moved)
│
└── ... (code directories)
```

---

## 📊 Summary

**Root Directory:**
- **Before:** 51 MD files
- **After:** 8 MD files (essential only)
- **Moved:** 43 files to docs/

**docs/ Directory:**
- **Before:** 63 MD files (flat)
- **After:** Organized into semantic folders
  - docs/reference/ (3 files)
  - docs/guides/ (15 files in 6 subdirs)
  - docs/architecture/ (1 file)
  - docs/deprecated/ (~80 historical files in 6 subdirs)

**Total Reduction in Root:** 51 → 8 files (84% reduction)

---

## 🚀 Implementation Steps

### Step 1: Create New Directories
```bash
mkdir -p docs/reference
mkdir -p docs/guides/{development,setup,engineering,learning,tmux,protocols}
mkdir -p docs/architecture
mkdir -p docs/deprecated/{session_summaries,session_summaries_docs,implementation_status,specs_and_plans,mcp_integration,analysis,integration}
```

### Step 2: Move Root Files to docs/
```bash
# To docs/deprecated/session_summaries/
mv SESSION_ACCOMPLISHMENTS_20251030.md docs/deprecated/session_summaries/
mv SESSION_COMPLETE_2025_10_30.md docs/deprecated/session_summaries/
# ... (etc for all categorized files)
```

### Step 3: Move docs/ Files to Subdirectories
```bash
# To docs/reference/
mv docs/ARCHITECTURE_MAP.md docs/reference/
mv docs/EMPIRICA_CASCADE_WORKFLOW_SPECIFICATION.md docs/reference/
mv docs/DIRECTORY_STRUCTURE.md docs/reference/

# To docs/deprecated/session_summaries_docs/
mv docs/13TH_VECTOR_SESSION_SUMMARY.md docs/deprecated/session_summaries_docs/
# ... (etc for ~30 completion docs)
```

### Step 4: Create README files
Create README.md in each subdirectory explaining what's there and what supersedes it.

---

**Next:** Execute this plan? Or adjust categories first?
