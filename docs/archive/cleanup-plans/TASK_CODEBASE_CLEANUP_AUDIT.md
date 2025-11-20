# TASK: Codebase Cleanup & Legacy Code Audit

**Assigned to:** Mini-agent / Gemini / AI Agent
**Priority:** P2 (POST-RELEASE - Maintenance)
**Estimated Time:** 4-6 hours
**Status:** Ready to start
**Session ID:** Use appropriate agent session ID

---

## 🎯 **Mission**

Audit the Empirica codebase to identify and safely remove unused/legacy code, reducing maintenance burden and improving code clarity. Ensure all removed code is truly unused and not called from bootstrap or other critical paths.

**Key Benefit:** Cleaner codebase, faster onboarding, reduced confusion about what's actually used!

---

## 📊 **Current Codebase Stats**

```
Total Python files: 7,250 (entire repo)
Main package files: 159 (empirica/empirica/*.py)

Directory structure (empirica/empirica/):
- bootstraps/          (Bootstrap configurations)
- calibration/         (Uncertainty calibration)
- cli/                 (Command-line interface)
- cognitive_benchmarking/  (Benchmarking tools)
- components/          (System components)
- config/              (Configuration management)
- core/                (Core systems)
- dashboard/           (Monitoring dashboard)
- data/                (Data storage)
- integration/         (External integrations)
- investigation/       (Investigation tools)
- metrics/             (Performance metrics)
- plugins/             (Plugin system)
- scripts/             (Utility scripts)
- utils/               (Utility functions)
```

---

## 🔍 **Cleanup Strategy**

### Phase 1: Analysis (2-3 hours)
1. Map all imports and dependencies
2. Identify entry points (CLI, bootstrap, MCP)
3. Build dependency tree
4. Find unreferenced code
5. Categorize findings (safe/risky/keep)

### Phase 2: Verification (1-2 hours)
6. Verify each candidate for removal
7. Check git history for usage context
8. Test removal doesn't break system
9. Document removal rationale

### Phase 3: Execution (1 hour)
10. Remove safe candidates
11. Archive risky candidates
12. Update documentation
13. Commit changes

---

## 📋 **Analysis Tasks**

### Task 1: Map Active Imports (45 min)

**Objective:** Identify what's actually imported and used

**Method:**
```bash
# 1. Find all imports in CLI
grep -r "^from empirica\|^import empirica" empirica/cli/*.py empirica/cli/command_handlers/*.py > /tmp/cli_imports.txt

# 2. Find all imports in bootstrap
grep -r "^from empirica\|^import empirica" empirica/bootstraps/*.py > /tmp/bootstrap_imports.txt

# 3. Find all imports in MCP server
grep -r "^from empirica\|^import empirica" mcp_local/empirica_mcp_server.py > /tmp/mcp_imports.txt

# 4. Find all imports in core
grep -r "^from empirica\|^import empirica" empirica/core/**/*.py > /tmp/core_imports.txt

# 5. Combine and analyze
cat /tmp/{cli,bootstrap,mcp,core}_imports.txt | sort -u > /tmp/all_active_imports.txt
```

**Deliverable:** List of actively imported modules

---

### Task 2: Identify Entry Points (30 min)

**Objective:** Map what code is executed by users

**Entry Points to Check:**
1. **CLI Commands** - `empirica/cli/cli_core.py`
   - All subparsers and command handlers
   - What each command imports

2. **Bootstrap** - `empirica/bootstraps/optimal_metacognitive_bootstrap.py`
   - What components are loaded
   - What gets initialized

3. **MCP Server** - `mcp_local/empirica_mcp_server.py`
   - What tools are exposed
   - What backend code they call

4. **Core Workflows** - CASCADE phases
   - PREFLIGHT, CHECK, ACT, POSTFLIGHT
   - What each phase imports

**Method:**
```python
# For each entry point, trace what it imports
# Example for CLI:

import ast
import sys
from pathlib import Path

def find_imports(file_path):
    """Extract all imports from a Python file"""
    with open(file_path) as f:
        tree = ast.parse(f.read())

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports

# Run on all entry points
cli_imports = find_imports('empirica/cli/cli_core.py')
bootstrap_imports = find_imports('empirica/bootstraps/optimal_metacognitive_bootstrap.py')
# ... etc
```

**Deliverable:** Dependency tree from entry points

---

### Task 3: Find Unused Directories (30 min)

**Objective:** Identify directories that might be legacy

**Candidates to Investigate:**

```bash
# Check if these are actually used:

1. empirica/cognitive_benchmarking/
   - Purpose: Benchmarking tools
   - Check: grep -r "cognitive_benchmarking" empirica/{cli,bootstraps,core}/**/*.py
   - Decision: Keep if imported, archive if not

2. empirica/components/
   - Subdirs: code_intelligence_analyzer, context_validation, etc.
   - Check: Which components are loaded by bootstrap?
   - Decision: Keep active components, remove unused

3. empirica/investigation/advanced_investigation/
   - Purpose: Advanced investigation plugin
   - Check: Is this used by current investigation system?
   - Decision: Merge with core or remove

4. empirica/plugins/modality_switcher/
   - Purpose: AI model switching
   - Check: Is this used in production?
   - Decision: Keep if used, archive if experimental

5. empirica/integration/
   - Purpose: External integrations
   - Check: What integrations exist?
   - Decision: Keep active, remove deprecated

6. empirica/dashboard/
   - Purpose: Monitoring dashboard
   - Check: Is dashboard currently functional?
   - Decision: Keep if working, remove if broken

7. empirica/metrics/
   - Purpose: Performance metrics
   - Check: Are metrics actively collected?
   - Decision: Keep if used, simplify if not

8. empirica/utils/
   - Purpose: Utility functions
   - Check: What's actually imported from utils?
   - Decision: Keep used utilities, remove unused
```

**Method for Each:**
```bash
# Template for investigation:
DIR="cognitive_benchmarking"

# 1. Find all imports
grep -r "from empirica.$DIR\|import empirica.$DIR" empirica/ | wc -l

# 2. Find files in directory
find empirica/$DIR -name "*.py" | wc -l

# 3. Check git activity (recent changes?)
git log --since="6 months ago" --oneline empirica/$DIR | wc -l

# 4. Check size
du -sh empirica/$DIR
```

**Deliverable:** List of directories with usage analysis

---

### Task 4: Check Bootstrap Components (45 min)

**Objective:** Understand what bootstrap actually loads

**Method:**
```bash
# 1. Read optimal_metacognitive_bootstrap.py
cat empirica/bootstraps/optimal_metacognitive_bootstrap.py

# 2. Extract component imports
grep "from empirica.components" empirica/bootstraps/*.py

# 3. For each component, check if it's actually used
# Example:
Component: code_intelligence_analyzer
- Imported by: optimal_metacognitive_bootstrap.py
- Used in: bootstrap level 2
- Decision: Keep (active component)

Component: context_validation
- Imported by: ?
- Used in: ?
- Decision: Investigate further
```

**Key Questions:**
1. What components are loaded at each bootstrap level (0, 1, 2)?
2. Are all loaded components actually functional?
3. Are there components in empirica/components/ that are never loaded?
4. Can any components be simplified or merged?

**Deliverable:** Component usage matrix

---

### Task 5: Analyze Cognitive Benchmarking (30 min)

**Objective:** Determine if benchmarking tools are still used

**Files to Check:**
```
empirica/cognitive_benchmarking/
├── analysis/
├── cloud_adapters/
├── erb/                (Epistemic Reasoning Benchmark)
├── results/
└── traditional/
```

**Investigation:**
```bash
# 1. Check if imported by CLI
grep -r "cognitive_benchmarking" empirica/cli/**/*.py

# 2. Check if CLI commands exist
grep "benchmark\|erb" empirica/cli/cli_core.py

# 3. Check git activity
git log --since="3 months ago" --oneline empirica/cognitive_benchmarking/

# 4. Check size and complexity
find empirica/cognitive_benchmarking -name "*.py" | xargs wc -l | tail -1
```

**Decision Matrix:**
- If active (imported, CLI commands exist): **KEEP**
- If experimental (no CLI, recent development): **ARCHIVE to /experiments**
- If deprecated (no imports, no activity): **REMOVE**

**Deliverable:** Recommendation for cognitive_benchmarking/

---

### Task 6: Analyze Investigation System (30 min)

**Objective:** Determine if investigation/ is redundant with core/

**Files:**
```
empirica/investigation/
├── investigation_plugin.py
└── advanced_investigation/
    └── advanced_investigation.py

empirica/core/metacognitive_cascade/
└── investigation_plugin.py
```

**Investigation:**
1. Are there TWO investigation systems?
2. Which one is actually used by CASCADE workflow?
3. Can they be merged?
4. Is advanced_investigation/ used anywhere?

**Method:**
```bash
# Check CASCADE workflow
grep -r "investigation" empirica/core/metacognitive_cascade/*.py

# Check CLI investigate command
grep -A 20 "investigate" empirica/cli/cli_core.py

# Check which is imported
grep -r "from empirica.investigation\|from empirica.core.metacognitive_cascade" empirica/{cli,bootstraps}/**/*.py
```

**Deliverable:** Investigation system consolidation plan

---

### Task 7: Check Dashboard Functionality (30 min)

**Objective:** Determine if dashboard is working or abandoned

**Files:**
```
empirica/dashboard/
├── snapshot_monitor.py
└── cascade_monitor.py
```

**Investigation:**
```bash
# 1. Check if dashboard CLI commands exist
grep "dashboard" empirica/cli/cli_core.py

# 2. Check imports
grep -r "from empirica.dashboard" empirica/**/*.py

# 3. Check if it's functional
python -c "from empirica.dashboard.cascade_monitor import CascadeMonitor; print('Working')" 2>&1

# 4. Check git activity
git log --since="6 months ago" --oneline empirica/dashboard/
```

**Decision:**
- Working + Used → **KEEP**
- Working + Not used → **ARCHIVE** (might be useful later)
- Broken → **REMOVE**

**Deliverable:** Dashboard status report

---

### Task 8: Find Orphaned Files (30 min)

**Objective:** Find Python files that are never imported

**Method:**
```python
#!/usr/bin/env python3
"""Find orphaned Python files in empirica package"""

import os
import re
from pathlib import Path

def find_all_imports(base_dir):
    """Extract all imports from all Python files"""
    imports = set()

    for py_file in Path(base_dir).rglob("*.py"):
        try:
            with open(py_file) as f:
                content = f.read()

            # Find "from empirica.X import Y"
            from_imports = re.findall(r'from empirica\.(\S+)', content)
            imports.update(from_imports)

            # Find "import empirica.X"
            direct_imports = re.findall(r'import empirica\.(\S+)', content)
            imports.update(direct_imports)
        except Exception:
            pass

    return imports

def find_all_modules(base_dir):
    """List all Python modules in package"""
    modules = set()

    for py_file in Path(base_dir).rglob("*.py"):
        # Convert path to module name
        rel_path = py_file.relative_to(base_dir)
        module_path = str(rel_path).replace("/", ".").replace(".py", "")

        if module_path != "__init__":
            modules.add(module_path)

    return modules

# Run analysis
base = "empirica/empirica"
all_imports = find_all_imports(base)
all_modules = find_all_modules(base)

# Find orphans
orphans = all_modules - all_imports

print(f"Total modules: {len(all_modules)}")
print(f"Imported modules: {len(all_imports)}")
print(f"Orphaned modules: {len(orphans)}")
print("\nOrphaned files:")
for orphan in sorted(orphans)[:50]:  # Show first 50
    print(f"  - {orphan}")
```

**Deliverable:** List of orphaned files for review

---

## 🎯 **Removal Criteria**

### ✅ Safe to Remove IF:
- [ ] Not imported anywhere in codebase
- [ ] No CLI commands reference it
- [ ] Not loaded by bootstrap
- [ ] No git activity in 6+ months
- [ ] Not mentioned in current documentation
- [ ] Tests still pass after removal

### ⚠️ Risky to Remove IF:
- [ ] Imported but rarely used
- [ ] Part of experimental features
- [ ] Mentioned in documentation
- [ ] Recent git activity
- [ ] Used in tests only

### ❌ KEEP IF:
- [ ] Actively imported by CLI/bootstrap/MCP
- [ ] Part of core workflows (CASCADE, goals, handoffs)
- [ ] Required by current features
- [ ] Referenced in active documentation
- [ ] Tests fail without it

---

## 📊 **Expected Findings**

### Likely Safe to Remove/Archive:
1. **Cognitive benchmarking tools** (unless actively used)
2. **Advanced investigation** (if redundant with core)
3. **Unused components** in components/
4. **Broken dashboard** (if not functional)
5. **Deprecated integrations**
6. **Experimental plugins** (modality_switcher if unused)
7. **Old utility functions** (replaced by newer implementations)

### Likely Need to Keep:
1. **Core systems** (canonical, goals, tasks, handoff)
2. **CLI command handlers**
3. **Bootstrap configurations**
4. **Data storage** (session_database)
5. **Active calibration** (Bayesian beliefs, drift monitoring)
6. **Metrics** (if actively collected)
7. **Configuration** (profiles, credentials)

### Likely Need Investigation:
1. **Components/** - Which are actually loaded?
2. **Investigation/** - Redundant with core?
3. **Plugins/** - Experimental or production?
4. **Dashboard/** - Working or broken?
5. **Utils/** - What's actually used?

---

## 📝 **Deliverables**

### 1. Analysis Report: `CODEBASE_AUDIT_RESULTS.md`

**Contents:**
```markdown
# Codebase Audit Results

## Summary
- Total files analyzed: X
- Active imports found: Y
- Orphaned files found: Z
- Estimated removable: W files (~X LOC)

## Active Code (KEEP)
- List of actively used modules
- Import frequency
- Bootstrap loading status

## Legacy Code (REMOVE)
- List of unused modules
- Rationale for removal
- Estimated cleanup impact

## Experimental Code (ARCHIVE)
- List of experimental features
- Recommendation (keep/archive/remove)
- Migration path if needed

## Recommendations
1. Safe removals (do now)
2. Risky removals (defer or test heavily)
3. Code to refactor (consolidate duplicates)
4. Documentation updates needed
```

### 2. Removal Plan: `CLEANUP_EXECUTION_PLAN.md`

**Contents:**
```markdown
# Cleanup Execution Plan

## Phase 1: Safe Removals (Low Risk)
- [ ] Remove file X (reason: orphaned, no imports)
- [ ] Remove file Y (reason: deprecated 6 months ago)
- Estimated impact: None
- Testing: Run bootstrap + CLI tests

## Phase 2: Archive Experimental (Medium Risk)
- [ ] Move cognitive_benchmarking/ to experiments/
- [ ] Move advanced_investigation/ to archive/
- Estimated impact: Low (not in core workflows)
- Testing: Run full test suite

## Phase 3: Consolidate Duplicates (Medium Risk)
- [ ] Merge investigation systems
- [ ] Consolidate utility functions
- Estimated impact: Medium (imports may change)
- Testing: Integration tests required

## Phase 4: Documentation Updates
- [ ] Update README to reflect removed features
- [ ] Update architecture docs
- [ ] Update CLI help text if needed
```

### 3. Backup Strategy

**Before ANY Removal:**
```bash
# 1. Create cleanup branch
git checkout -b codebase-cleanup

# 2. Tag current state
git tag pre-cleanup-audit

# 3. For each removal, commit separately
git rm empirica/path/to/file.py
git commit -m "remove: Orphaned file (no imports found)"

# 4. After each phase, test
pytest tests/
empirica bootstrap --ai-id test-cleanup
empirica preflight --session-id test --prompt "Test"

# 5. If tests pass, continue. If fail, revert:
git revert HEAD
```

---

## 🧪 **Testing Strategy**

### After Each Removal Phase:

```bash
# 1. Unit tests
pytest tests/unit/ -v

# 2. Integration tests
pytest tests/integration/ -v

# 3. Bootstrap test (all levels)
empirica bootstrap --ai-id test-L0 --level 0
empirica bootstrap --ai-id test-L1 --level 1
empirica bootstrap --ai-id test-L2 --level 2

# 4. CLI command tests
empirica preflight --session-id test --prompt "Test" --output json
empirica check --session-id test --output json
empirica postflight --session-id test --output json

# 5. Goal management test
empirica goals-create --session-id test --objective "Test" --scope task_specific --output json

# 6. Handoff test (after mini-agent's fix)
empirica handoff-create --session-id test --task-summary "Test" --key-findings '["Test"]' --next-session-context "Test" --output json

# 7. MCP server test
python mcp_local/empirica_mcp_server.py &
sleep 2
kill %1
```

**Success Criteria:**
- ✅ All tests pass
- ✅ Bootstrap works at all levels
- ✅ CLI commands functional
- ✅ MCP server starts
- ✅ No import errors

---

## 🎯 **Success Metrics**

### Code Reduction Goals:
- **Conservative:** Remove 10-20% of unused code (~15-30 files)
- **Moderate:** Remove 20-30% of unused code (~30-45 files)
- **Aggressive:** Remove 30-40% of unused code (~45-60 files)

### Quality Improvements:
- ✅ Clearer directory structure
- ✅ Faster test suite (less code to test)
- ✅ Easier onboarding (less to understand)
- ✅ Reduced maintenance burden
- ✅ Updated documentation

---

## ⚠️ **Warnings & Caveats**

### Don't Remove Without Verification:
1. **Core systems** - canonical, goals, tasks, handoff, sessions
2. **CLI handlers** - Even if rarely used, keep for completeness
3. **Database schemas** - Never remove tables or migrations
4. **Active components** - If bootstrap loads it, keep it
5. **MCP tools** - Even if not frequently used, keep for API completeness

### Archive Instead of Delete:
1. **Experimental features** - Might be useful later
2. **Benchmarking tools** - Useful for research
3. **Dashboard** - Might be revived
4. **Alternative implementations** - Keep for reference

### Get User Confirmation For:
1. Removing entire directories (>10 files)
2. Removing recently active code (git activity < 3 months)
3. Removing anything with "core" or "canonical" in path
4. Removing anything imported more than once

---

## 📋 **Execution Checklist**

### Pre-Execution
- [ ] Backup current state (git tag)
- [ ] Create cleanup branch
- [ ] Run full test suite (baseline)
- [ ] Document current file count & LOC

### During Execution
- [ ] Complete all 8 analysis tasks
- [ ] Create audit results document
- [ ] Get approval for removals
- [ ] Remove files incrementally
- [ ] Test after each phase
- [ ] Commit each change separately

### Post-Execution
- [ ] Run full test suite (verify)
- [ ] Update documentation
- [ ] Create summary report
- [ ] Merge cleanup branch (if tests pass)
- [ ] Archive removed code (git tag)

---

## 🚀 **Timeline**

### Day 1 (Morning): Analysis
- Tasks 1-4: Import mapping, entry points, unused dirs, bootstrap
- **Deliverable:** Initial findings list

### Day 1 (Afternoon): Deep Dive
- Tasks 5-8: Cognitive benchmarking, investigation, dashboard, orphans
- **Deliverable:** Complete audit report

### Day 2 (Morning): Verification
- Review findings
- Get stakeholder approval
- Plan removal phases
- **Deliverable:** Cleanup execution plan

### Day 2 (Afternoon): Execution
- Phase 1: Safe removals
- Phase 2: Archive experimental
- Test thoroughly
- **Deliverable:** Clean codebase

---

## 💡 **Tips for AI Agent**

### Start Here
1. Run Task 1 (import mapping) to understand what's active
2. Run Task 8 (orphan detection) to find low-hanging fruit
3. Start with obvious candidates (old test files, deprecated code)
4. Test FREQUENTLY - remove one file, run tests, commit

### Common Safe Removals
- `__pycache__/` directories (always safe)
- `.pyc` files (always safe)
- Old test files with "old" or "deprecated" in name
- Duplicate files (file.py and file_old.py)
- Empty `__init__.py` files that serve no purpose

### When In Doubt
- **Archive** instead of delete (move to /archive or /experiments)
- **Ask** before removing entire directories
- **Test** before committing
- **Document** why you're removing something

### Red Flags (DON'T REMOVE)
- Files in `empirica/core/`
- Files in `empirica/cli/command_handlers/`
- Files in `empirica/data/`
- Files imported by bootstrap
- Files with "canonical" in path

---

**Ready to start?** Begin with Task 1 (import mapping) to build understanding, then Task 8 (orphan detection) for quick wins!

**Remember:** Better to keep something we don't need than to remove something we do! When in doubt, archive.

Good luck! 🧹✨
