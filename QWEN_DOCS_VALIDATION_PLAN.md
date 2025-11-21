# Qwen Documentation Validation Plan

**Purpose:** Validate all production docs match current architecture  
**Date:** 2025-11-21  
**For:** Qwen (systematic validator)  
**Why:** Subtle changes not caught by pattern matching - minefield for users

---

## 🎯 Mission for Qwen

**Task:** Go through EVERY production doc file and verify it matches the current working system.

**Problem:** 
- Pattern matching showed docs are "current" (use correct table names, CLI commands exist)
- BUT: Subtle inconsistencies remain from architecture evolution
- Examples: outdated workflows, wrong function signatures, deprecated patterns
- Users/agents will hit these landmines

**Goal:** Production docs must be 100% accurate for launch.

---

## 📋 Validation Strategy

### Phase 1: Establish Ground Truth (1 hour)

**Build reference of what ACTUALLY works:**

```bash
# 1. Extract all CLI commands
python3 -m empirica.cli --help > /tmp/cli_commands.txt
for cmd in bootstrap preflight check postflight investigate-log act-log session-end goals-create goals-add-subtask goals-complete-subtask handoff-create handoff-query checkpoint-create checkpoint-load sessions-list; do
  echo "=== $cmd ===" >> /tmp/cli_reference.txt
  python3 -m empirica.cli $cmd --help >> /tmp/cli_reference.txt 2>&1
done

# 2. Extract database schema
sqlite3 .empirica/sessions/sessions.db ".schema" > /tmp/db_schema.sql
sqlite3 .empirica/sessions/sessions.db "SELECT name FROM sqlite_master WHERE type='table';" > /tmp/db_tables.txt

# 3. List MCP tools (from mcp_local/empirica_mcp_server.py)
grep -E "^@server\.(call_)?tool\(" mcp_local/empirica_mcp_server.py -A 5 > /tmp/mcp_tools.txt

# 4. Extract CASCADE workflow (from empirica/core/cascade.py)
grep -E "class|def (execute|submit)" empirica/core/cascade.py > /tmp/cascade_workflow.txt

# 5. Get 13 epistemic vectors
grep -E "EPISTEMIC_VECTORS|twelve.*vector" empirica/ -r > /tmp/vectors.txt
```

### Phase 2: Systematic Doc Validation (4-6 hours)

**For EACH markdown file in docs/, validate:**

#### A. Command Accuracy
- [ ] All `empirica <command>` examples use correct syntax
- [ ] All command flags exist and are spelled correctly
- [ ] Example outputs match actual command output format
- [ ] No references to removed/renamed commands

#### B. Code Example Accuracy
- [ ] Python imports work (`from empirica.cli import ...`)
- [ ] MCP tool names match actual tool names
- [ ] Function signatures match implementation
- [ ] Example code would actually run

#### C. Workflow Accuracy
- [ ] CASCADE flow is: PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT
- [ ] No references to removed phases
- [ ] Session creation workflow matches bootstrap command
- [ ] Goal creation workflow matches current API

#### D. Database/Schema Accuracy
- [ ] Table names correct (subtasks not tasks)
- [ ] Column names match schema
- [ ] SQL examples would actually work
- [ ] No references to removed tables (reflexes, etc.)

#### E. Concept Accuracy
- [ ] 13 epistemic vectors listed correctly
- [ ] Drift monitor described accurately
- [ ] Bayesian beliefs explanation matches implementation
- [ ] Git checkpoints vs handoff reports distinction clear

#### F. File Path Accuracy
- [ ] References to code files use correct paths
- [ ] Cross-references between docs work
- [ ] Example config files exist where claimed
- [ ] No broken links

---

## 🗂️ Files to Validate (96 production docs)

### Priority 1: User-facing guides (CRITICAL - validate first)

```
docs/00_START_HERE.md
docs/01_a_AI_AGENT_START.md
docs/01_b_MCP_AI_START.md
docs/02_INSTALLATION.md
docs/03_CLI_QUICKSTART.md
docs/04_MCP_QUICKSTART.md
docs/05_ARCHITECTURE.md
docs/06_TROUBLESHOOTING.md
docs/ONBOARDING_GUIDE.md
docs/ALL_PLATFORMS_INSTALLATION.md
docs/ALL_PLATFORMS_QUICK_REFERENCE.md
docs/README.md
```

### Priority 2: Production guides (HIGH - core features)

```
docs/production/01_QUICK_START.md
docs/production/02_INSTALLATION.md
docs/production/03_BASIC_WORKFLOW.md
docs/production/04_CASCADE_FLOW.md
docs/production/05_EPISTEMIC_VECTORS.md
docs/production/06_CASCADE_FLOW.md (duplicate?)
docs/production/07_GOAL_ORCHESTRATOR.md
docs/production/08_BAYESIAN_BELIEFS.md
docs/production/09_DRIFT_MONITOR.md
docs/production/10_PLUGIN_SYSTEM.md
... (all 29 files in production/)
```

### Priority 3: User guides (HIGH - AI agent prompts)

```
docs/user-guides/GENERIC_EMPIRICA_SYSTEM_PROMPT.md
docs/user-guides/CLAUDE.md
docs/user-guides/GEMINI.md
docs/user-guides/QWEN.md
docs/user-guides/MINIMAX.md
docs/user-guides/ROVODEV.md
... (all user-guides/*.md)
```

### Priority 4: Reference docs (MEDIUM)

```
docs/reference/ARCHITECTURE_OVERVIEW.md
docs/reference/CALIBRATION_SYSTEM.md
docs/reference/EMPIRICA_CASCADE_WORKFLOW_SPECIFICATION.md
docs/reference/QUICK_REFERENCE.md
... (all reference/*.md)
```

### Priority 5: Setup guides (MEDIUM)

```
docs/guides/setup/CLAUDE_CODE_MCP_SETUP.md
docs/guides/setup/QWEN_GEMINI_TESTING_GUIDE.md
... (all guides/setup/*.md)
```

### Priority 6: Everything else (LOW)

```
docs/guides/*
docs/examples/*
docs/architecture/* (if any remain)
docs/skills/*
docs/integrations/*
```

---

## 🔍 Validation Checklist Template

**For each file, create a report:**

```markdown
## [FILENAME]

**Status:** ✅ VALID | ⚠️ NEEDS FIXES | ❌ OUTDATED

### Issues Found:
1. Line X: Command `empirica old-command` → should be `empirica new-command`
2. Line Y: Refers to "tasks table" → should be "subtasks table"
3. Line Z: Example code imports non-existent function
4. Section "Foo": Describes removed feature

### Recommended Fixes:
- [ ] Update command syntax
- [ ] Fix table references
- [ ] Correct import statements
- [ ] Remove outdated section OR mark as deprecated

### Validation Results:
- Command accuracy: ✅/❌
- Code examples: ✅/❌
- Workflow accuracy: ✅/❌
- Schema accuracy: ✅/❌
- Concept accuracy: ✅/❌
- Path accuracy: ✅/❌

**Overall:** [PASS/FAIL/NEEDS_WORK]
```

---

## 🛠️ Validation Tools for Qwen

### Script 1: Test CLI commands in docs

```python
#!/usr/bin/env python3
"""Extract and test all CLI commands from markdown files."""
import re
import subprocess
from pathlib import Path

def extract_cli_commands(md_file):
    """Find all 'empirica <command>' examples."""
    content = Path(md_file).read_text()
    # Match: empirica command --flags
    pattern = r'empirica\s+[a-z-]+(?:\s+--[a-z-]+)*'
    return re.findall(pattern, content)

def test_command(cmd):
    """Test if command syntax is valid."""
    try:
        result = subprocess.run(
            cmd.split() + ['--help'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

# Run on all docs
for doc in Path('docs').rglob('*.md'):
    cmds = extract_cli_commands(doc)
    for cmd in cmds:
        valid = test_command(cmd)
        if not valid:
            print(f"❌ {doc}: {cmd} (invalid)")
```

### Script 2: Validate SQL in docs

```python
#!/usr/bin/env python3
"""Test SQL examples from docs against actual database."""
import re
import sqlite3
from pathlib import Path

def extract_sql(md_file):
    """Find SQL code blocks."""
    content = Path(md_file).read_text()
    # Match SQL in code blocks
    pattern = r'```sql\n(.*?)```'
    return re.findall(pattern, content, re.DOTALL)

def test_sql(query, db_path):
    """Test if SQL would execute."""
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(query)
        return True
    except Exception as e:
        return False, str(e)

# Run on all docs
db = '.empirica/sessions/sessions.db'
for doc in Path('docs').rglob('*.md'):
    queries = extract_sql(doc)
    for q in queries:
        valid = test_sql(q, db)
        if not valid:
            print(f"❌ {doc}: SQL error")
```

### Script 3: Check table references

```bash
#!/bin/bash
# Find all references to database tables in docs
# Cross-reference with actual schema

echo "Checking table references in docs..."

# Get actual tables
actual_tables=$(sqlite3 .empirica/sessions/sessions.db "SELECT name FROM sqlite_master WHERE type='table';")

# Check each doc
for file in docs/**/*.md; do
  # Look for table references
  grep -iE "FROM (tasks|reflexes|epistemic_reflex)" "$file" && echo "❌ $file: Uses removed table"
  grep -iE "FROM subtasks" "$file" > /dev/null || echo "⚠️  $file: No subtasks reference (might need one)"
done
```

---

## 📊 Expected Output

### Summary Report

```
EMPIRICA DOCUMENTATION VALIDATION REPORT
Generated: 2025-11-21
Validator: Qwen

Files Validated: 96
Status Breakdown:
  ✅ Valid: X files
  ⚠️  Needs fixes: Y files
  ❌ Outdated: Z files

Priority 1 (User-facing): X/12 valid
Priority 2 (Production): Y/29 valid
Priority 3 (User guides): Z/34 valid

Critical Issues: [count]
Medium Issues: [count]
Minor Issues: [count]

Top Issues:
1. [Most common problem across files]
2. [Second most common]
3. [Third most common]

Recommended Actions:
1. Fix Priority 1 issues immediately (blocking launch)
2. Address Priority 2 issues before 1.0
3. Schedule Priority 3 fixes for 1.1
```

### Detailed Issue List

```
CRITICAL ISSUES (block launch):
- docs/03_CLI_QUICKSTART.md:45 - Wrong command syntax
- docs/production/04_CASCADE_FLOW.md:120 - Incorrect workflow
- docs/user-guides/CLAUDE.md:89 - Non-existent MCP tool

MEDIUM ISSUES (fix before 1.0):
- docs/05_ARCHITECTURE.md:200 - Outdated diagram
- docs/reference/QUICK_REFERENCE.md:50 - Missing new features

MINOR ISSUES (fix in 1.1):
- docs/guides/PROFILE_MANAGEMENT.md:30 - Typo
- docs/examples/basic_usage.md:15 - Could be clearer
```

---

## 🎯 Success Criteria

**Documentation is production-ready when:**

1. ✅ All Priority 1 files are 100% accurate
2. ✅ All Priority 2 files have no critical issues
3. ✅ All CLI command examples work
4. ✅ All SQL examples are valid
5. ✅ All code imports resolve
6. ✅ All workflows match implementation
7. ✅ No references to removed features
8. ✅ Cross-references work

---

## 🤝 Handoff to Qwen

**What Qwen needs:**

1. This plan (QWEN_DOCS_VALIDATION_PLAN.md)
2. Access to empirica repo
3. Ground truth files (Phase 1 output)
4. Validation scripts (provided above)
5. 4-6 hours of focused time

**What Qwen should produce:**

1. Validation report (summary + detailed)
2. List of files needing fixes (prioritized)
3. Specific line-by-line fixes needed
4. Pull request with corrections (if authorized)
5. Updated docs that are launch-ready

**Validation approach:**

- Systematic (file by file)
- Test-driven (run examples, verify SQL)
- Evidence-based (compare to ground truth)
- Prioritized (critical issues first)

---

## 📝 Qwen's Workflow

```
1. Read this plan thoroughly
2. Run Phase 1 (establish ground truth)
3. Start with Priority 1 files
4. For each file:
   a. Read entirely
   b. Run validation checks
   c. Document issues
   d. Propose fixes
5. Generate summary report
6. Create detailed issue list
7. (Optional) Submit fixes as PR
8. Hand back to team for review
```

---

**Ready for Qwen to begin validation!** 🚀

This is systematic, measurable, and will ensure docs are truly production-ready.

