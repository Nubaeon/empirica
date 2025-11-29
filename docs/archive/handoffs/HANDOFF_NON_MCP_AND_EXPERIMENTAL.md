# Handoff: Non-MCP Commands + Experimental Docs

**From:** Rovo Dev (Session 126d5c66)  
**To:** Mini-Agent  
**Created:** 2025-01-XX  
**Priority:** High

---

## 🎯 Two Goals to Complete

### Goal 1: Test Non-MCP Commands (8f2885a0-df27-4ebd-836e-d77be79efd40)
**Status:** 0/6 subtasks  
**Purpose:** Validate all non-MCP CLI commands, fix broken ones

### Goal 2: Move Experimental Docs (35621dc5-edc7-4259-bd0c-4306144c3184)
**Status:** 0/7 subtasks  
**Purpose:** Organize experimental features (dashboards, modality switcher, benchmarking) into docs/experimental/

---

## 📋 GOAL 1: Non-MCP Commands Validation

### Context

**What we know:**
- MCP workflow commands are tested and working ✅
- Non-MCP commands (dashboards, utilities) haven't been tested
- Some might be broken or experimental

**What we need:**
- Test all non-MCP commands
- Fix broken ones or clearly mark as experimental
- Document what works

---

### Subtask 1: Identify Non-MCP Commands
**Task ID:** c8e54ded-a047-46a7-8a7d-5a785ccdae79

**How to do it:**
```bash
cd empirica/cli
# Look at COMMAND_MAP in cli_core.py
grep -A 50 "COMMAND_MAP = {" cli_core.py

# MCP commands (already tested):
# - bootstrap, session-*
# - preflight*, check*, postflight*
# - goals-*
# - handoff-*
# - get-epistemic-state, get-session-summary, etc.

# Non-MCP commands to find:
# - dashboard*
# - Any utility commands
# - Any plugin commands
```

**Document:** List all non-MCP commands in your evidence

---

### Subtask 2: Test Dashboard Commands
**Task ID:** 16964d20-96d0-4bd6-94eb-de579e79ff49

**Commands to test:**
```bash
empirica dashboard --help
empirica dashboard-server --help
empirica dashboard-export --help
# Try any other dashboard-related commands you found
```

**For each command:**
- ✅ Shows help? Document usage
- ❌ Errors? Note the error
- 🔍 Requires dependencies? Note what's needed

**Evidence:** "dashboard: [WORKS/BROKEN/EXPERIMENTAL] - [notes]"

---

### Subtask 3: Test Modality Switcher Commands
**Task ID:** ed6e4d45-e7a3-4094-9dd5-741bbd8aadab

**Search for:**
```bash
grep -i "modality\|switcher" empirica/cli/cli_core.py
empirica --help | grep -i modal
```

**Note:** We already removed `cascade` command. Are there others?

---

### Subtask 4: Test Utility Commands
**Task ID:** 1f953616-3422-4e80-9289-bb64a877cc30

**Common utilities to test:**
```bash
empirica --version
empirica validate --help
empirica config --help
empirica init --help
# etc.
```

---

### Subtask 5: Fix or Remove Broken Commands ⚠️ CRITICAL
**Task ID:** b18bff6e-b161-4051-8d8f-f504a8ac4302

**For each broken command, decide:**

**Option A: Fix it**
- If it's core functionality, fix the handler

**Option B: Mark as experimental**
- If it requires optional dependencies (dashboard UI, etc.)
- Add clear message: "This is an experimental feature. Install with: pip install empirica[experimental]"

**Option C: Remove it**
- If it's obsolete or doesn't work
- Comment out from COMMAND_MAP with explanation

**Document your decisions**

---

### Subtask 6: Create CLI_COMMANDS_NON_MCP.md
**Task ID:** 4e895666-2cc9-489c-be2d-2d4fa5bc2cc4

**File:** `CLI_COMMANDS_NON_MCP.md`

**Format:**
```markdown
# Non-MCP CLI Commands Status

**Generated:** [date]  
**Purpose:** Document all non-MCP commands and their status

## Dashboard Commands

### `empirica dashboard`
**Status:** [WORKING/BROKEN/EXPERIMENTAL]  
**Dependencies:** [none/dashboard UI/etc]  
**Usage:**
```bash
empirica dashboard --session-id UUID
```
**Notes:** [any important info]

### `empirica dashboard-server`
**Status:** [WORKING/BROKEN/EXPERIMENTAL]  
...

## Utility Commands

### `empirica --version`
**Status:** [WORKING/BROKEN]  
...

## Experimental/Removed

### `empirica cascade`
**Status:** REMOVED  
**Reason:** Was ModalitySwitcher plugin, now deprecated. Use MCP tools.
...

## Summary

Total non-MCP commands: X
- Working: Y
- Experimental (require extra install): Z
- Broken/Removed: W
```

---

## 📋 GOAL 2: Experimental Docs Organization

### Context

**The Problem:**
- Main docs reference experimental features (dashboards, modality switcher)
- These features are optional/modular
- Users might get confused thinking they're required
- Need clear separation: core vs experimental

**The Solution:**
- Create `docs/experimental/` folder
- Move experimental docs there
- Update main docs to mark these as optional

---

### Subtask 1: Identify Dashboard Docs
**Task ID:** 2f1646e4-1b78-44af-a2de-db72abf29ec5

**Search:**
```bash
cd docs
grep -ril "dashboard\|visualization\|UI" *.md production/*.md reference/*.md
# Also check for:
# - Dashboard setup guides
# - UI/visualization docs
# - Any mentions of web interface
```

**List all files found in evidence**

---

### Subtask 2: Identify Modality Switcher Docs
**Task ID:** 6e7e8c9a-7b6f-42e5-9f1f-fede776e7d5a

**Search:**
```bash
grep -ril "ModalitySwitcher\|modality.*switch\|cascade.*plugin" docs/*.md docs/*/
grep -ril "epistemic.*cascade" docs/*.md docs/*/ | grep -v "CASCADE workflow"
# Note: CASCADE workflow is core, ModalitySwitcher plugin is experimental
```

---

### Subtask 3: Identify Cognitive Benchmarking Docs
**Task ID:** 583c8892-452d-403a-82f0-742d637a60ed

**Search:**
```bash
grep -ril "benchmark\|cognitive.*test\|performance.*eval" docs/*.md docs/*/
# Look for benchmarking framework, cognitive tests, etc.
```

---

### Subtask 4: Create Experimental Folder
**Task ID:** 7fb72828-22b3-4e9f-838a-58c9ceb82c7d

**Structure:**
```bash
mkdir -p docs/experimental
mkdir -p docs/experimental/dashboard
mkdir -p docs/experimental/modality_switcher
mkdir -p docs/experimental/benchmarking  # if needed
```

---

### Subtask 5: Move Experimental Docs ⚠️ CRITICAL
**Task ID:** 900e47f6-5642-486e-94b8-37c752d58b63

**How to move:**
```bash
# For each identified experimental doc:
git mv docs/some_dashboard_doc.md docs/experimental/dashboard/
# OR if not in git yet:
mv docs/some_dashboard_doc.md docs/experimental/dashboard/

# Update internal links in moved docs
# Update references in main docs
```

**Organize by feature:**
- Dashboard docs → `docs/experimental/dashboard/`
- Modality switcher → `docs/experimental/modality_switcher/`
- Benchmarking → `docs/experimental/benchmarking/`

---

### Subtask 6: Update Main Docs References
**Task ID:** cf7b6e5e-1f25-4d62-9836-9934d32d88cb

**Find references:**
```bash
grep -rn "dashboard\|ModalitySwitcher" docs/*.md docs/production/*.md
```

**Update pattern:**
```markdown
## OLD:
See the dashboard documentation for visualization.

## NEW:
See the [dashboard documentation](experimental/dashboard/) for visualization (optional feature).

## OR:
**Note:** Dashboards are an optional experimental feature. See [docs/experimental/](experimental/) for setup.
```

---

### Subtask 7: Create Experimental README
**Task ID:** 6d03a523-da63-4a7a-90be-fd5ae901955b

**File:** `docs/experimental/README.md`

**Content:**
```markdown
# Experimental Features

This directory contains documentation for **optional, experimental** Empirica features that require additional setup or dependencies.

## ⚠️ What "Experimental" Means

- **Optional:** Core Empirica works without these
- **Additional dependencies:** May require extra installation steps
- **Subject to change:** APIs may evolve
- **Community-driven:** Often contributed features

## 🧪 Available Experimental Features

### Dashboard & Visualization
**Location:** `dashboard/`  
**Purpose:** Web UI for visualizing epistemic states and CASCADE flows  
**Requires:** `pip install empirica[dashboard]`  
**Status:** Beta

[Link to dashboard/README.md]

### Modality Switcher (Deprecated)
**Location:** `modality_switcher/`  
**Purpose:** Original CASCADE implementation (pre-MCP)  
**Status:** Deprecated - Use MCP tools instead  
**Kept for:** Historical reference

[Link to modality_switcher/README.md]

### Cognitive Benchmarking
**Location:** `benchmarking/`  
**Purpose:** Benchmark framework for epistemic assessments  
**Requires:** Additional benchmark datasets  
**Status:** Experimental

[Link to benchmarking/README.md]

## 💡 Using Experimental Features

### Installation
```bash
# Install core Empirica (no experimental features)
pip install empirica

# Install with specific experimental feature
pip install empirica[dashboard]

# Install all experimental features
pip install empirica[experimental]
```

### Documentation Structure
- Core features: `docs/` (main directory)
- Experimental features: `docs/experimental/` (this directory)

## 🚀 Contributing Experimental Features

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on adding new experimental features.

## ⚡ Migration to Core

When an experimental feature becomes stable:
1. Move docs from `experimental/` to main `docs/`
2. Update installation (remove [feature] requirement)
3. Add to core test suite
4. Announce in changelog
```

---

## 🎯 Success Criteria

### Goal 1 (Non-MCP Commands):
- [ ] All non-MCP commands identified
- [ ] All commands tested
- [ ] Broken commands fixed or marked experimental
- [ ] CLI_COMMANDS_NON_MCP.md created

### Goal 2 (Experimental Docs):
- [ ] docs/experimental/ folder created
- [ ] All experimental docs moved
- [ ] Main docs updated (mark features as optional)
- [ ] Experimental README created

### Overall:
- [ ] No confusion about what's core vs experimental
- [ ] Clear installation instructions for experimental features
- [ ] Website content can reference core features without confusion

---

## 📊 Estimated Time

**Goal 1 (Non-MCP):** 2-3 hours
- Testing commands: 1 hour
- Fixing issues: 1 hour
- Documentation: 30 min

**Goal 2 (Experimental):** 2 hours
- Identifying docs: 30 min
- Moving/organizing: 1 hour
- Writing README: 30 min

**Total:** 4-5 hours

---

## 🚨 Important Notes

**Why this matters:**
- Website will be public-facing
- Users need to know what's core vs optional
- Clear separation prevents confusion
- Installation instructions must be accurate

**Integration with previous work:**
- You already validated MCP commands ✅
- This completes CLI validation
- Then we can finalize website content

**After completion:**
- We'll have complete CLI documentation
- We'll know exactly what features are core
- Website validation will be accurate
- Ready for public launch!

---

**Ready to start! Work through Goal 1 first (non-MCP commands), then Goal 2 (experimental docs).**
