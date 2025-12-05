# Handoff to Claude Sonnet: Production Documentation Updates

**Date:** December 5, 2025
**From:** Claude Code (Code Lead)
**To:** Claude Sonnet (High-Reasoning Architect)
**Status:** Ready for Implementation
**Priority:** HIGH (unblocks production docs)

---

## TL;DR

**Your Task:** Update 5 critical production docs to remove deprecated API references and fix broken examples

**Why:** Current docs reference removed bootstrap classes + old schema. Users will fail when following examples.

**What's Affected:** 205+ lines across 5 files in `/docs/production/`

**Timeline:** 8-10 hours (straightforward find-replace + example updates)

**Complexity:** Medium (most are systematic replacements)

---

## The Problem

Current production documentation has **outdated examples** because we removed the bootstrap system and migrated the database schema, but docs weren't updated.

### Impact
- Users following `03_BASIC_USAGE.md` will fail at session setup
- Users following `13_PYTHON_API.md` will try to import removed classes
- Users trying to deploy with `17_PRODUCTION_DEPLOYMENT.md` will use deprecated init patterns
- Database users reading `12_SESSION_DATABASE.md` will expect 12 tables, find 8

### Examples of Broken Code

**From `03_BASIC_USAGE.md` (LINE ~50):**
```python
# OLD (BROKEN - class removed)
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

bootstrap = ExtendedMetacognitiveBootstrap(session_id="test")
bootstrap.load()
```

**Should be:**
```python
# NEW (CORRECT)
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session = db.get_session("test")  # Session already created by empirica session-create
```

---

## Files to Update (Priority Order)

### FILE 1: `production/03_BASIC_USAGE.md` (CRITICAL)

**Lines Affected:** ~50 lines across 5 sections
**Issue:** Bootstrap class examples + old session creation

**Search/Replace Patterns:**

```
1. Find: "ExtendedMetacognitiveBootstrap"
   Replace: "SessionDatabase"

2. Find: "OptimalMetacognitiveBootstrap"
   Replace: "SessionDatabase"

3. Find: "bootstrap.load()"
   Replace: "db = SessionDatabase()"

4. Find: "from empirica.bootstraps import"
   Replace: "from empirica.data.session_database import"

5. Find: "# Initialize with bootstrap"
   Replace: "# Query existing session"
```

**Specific Examples to Update:**

| Location | OLD | NEW |
|----------|-----|-----|
| Section: "Getting Started" | Bootstrap initialization | Use `empirica session-create` command |
| Section: "Python API" | `bootstrap.load(session_id)` | Query with `SessionDatabase()` |
| Section: "Vectors" | Reference to `reflex_logger.py` | Reference to `git_enhanced_reflex_logger.py` |
| Code Block 1 | "from empirica.bootstraps" | "from empirica.data.session_database" |
| Code Block 2 | "ExtendedMetacognitiveBootstrap(...)" | "SessionDatabase().get_session(...)" |

---

### FILE 2: `production/13_PYTHON_API.md` (CRITICAL)

**Lines Affected:** ~80 lines in "Bootstrap Configuration" section
**Issue:** Entire bootstrap section is about removed functionality

**Action:** DELETE bootstrap section entirely

**Sections to Remove:**
- "Bootstrap Configuration" (lines ~45-120)
- "Advanced Bootstrap Setup" (lines ~130-180)
- All code examples using `ExtendedMetacognitiveBootstrap` or `OptimalMetacognitiveBootstrap`

**What to Keep:**
- SessionDatabase API section (update references)
- CASCADE workflow examples (good as-is)
- Python integration patterns

**Replace Removed Section With:**

```markdown
## Session Management

Sessions are now created via CLI and queried programmatically:

### Creating Sessions
Use the CLI command:
```bash
empirica session-create --ai-id claude-code
```

### Querying Sessions
```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session = db.get_session(session_id)
vectors = db.get_latest_vectors(session_id)
db.close()
```

See `03_BASIC_USAGE.md` for full examples.
```

---

### FILE 3: `production/12_SESSION_DATABASE.md` (HIGH)

**Lines Affected:** ~40 lines describing schema
**Issue:** References 12 tables, now only 8; lists deprecated tables

**Update Required:**

| Item | OLD | NEW |
|------|-----|-----|
| Opening: "12 tables" | "The Empirica database contains 12 tables:" | "The Empirica database contains 8 core tables:" |
| Table list | Include: epistemic_assessments, preflight_assessments, postflight_assessments, check_phase_assessments, cascade_metadata | Remove deprecated ones, keep: reflexes, sessions, cascades, divergence_tracking, drift_monitoring, bayesian_beliefs, investigation_tools, investigation_logs, act_logs |
| Schema details | Reference to "reflex_logger.py" | Reference to "git_enhanced_reflex_logger.py" |
| Example queries | Old table names in queries | Update to reflexes table with phase filter |

**Critical Section to Rewrite:**

**OLD (Lines 15-50):**
```markdown
### Table: epistemic_assessments
Stores 12-vector epistemic states (deprecated system)...

### Table: preflight_assessments
Stores PREFLIGHT phase assessments...
```

**NEW (Lines 15-50):**
```markdown
### Table: reflexes (Canonical)
Single unified table for all CASCADE phases:
- phase: 'PREFLIGHT', 'CHECK', 'POSTFLIGHT'
- 13 epistemic vectors
- Metadata (JSON)
- Git notes reference

Example query:
```sql
SELECT * FROM reflexes
WHERE session_id = ? AND phase = 'PREFLIGHT'
ORDER BY timestamp DESC LIMIT 1;
```
```

---

### FILE 4: `production/15_CONFIGURATION.md` (HIGH)

**Lines Affected:** ~35 lines in "Bootstrap Configuration" section
**Issue:** Configuration for removed bootstrap system

**Action:** DELETE bootstrap configuration section

**Sections to Remove:**
- "Bootstrap Configuration" (entire section)
- "Environment Variables for Bootstrap" (if exists)
- "Bootstrap-level Settings" (if exists)

**What to Keep:**
- MCO configuration section (already correct)
- Session configuration
- Logging configuration
- Threshold configuration

**Note:** If file is entirely bootstrap config, consider deprecating entire file to `/empirica-dev/`.

---

### FILE 5: `production/17_PRODUCTION_DEPLOYMENT.md` (HIGH)

**Lines Affected:** ~50 lines in "Initialization" section
**Issue:** Deployment guide uses deprecated bootstrap initialization

**Search/Replace Patterns:**

```
1. Find: "Bootstrap initialization" section
   Replace: "Session creation via CLI"

2. Find: "ExtendedMetacognitiveBootstrap"
   Replace: "empirica session-create command"

3. Find: "bootstrap.load()" steps
   Replace: "empirica session-create steps"

4. Find: "Set EMPIRICA_BOOTSTRAP_LEVEL environment variable"
   Replace: "Use --bootstrap-level flag or omit (defaults to 1)"
```

**Specific Updates:**

| Section | OLD Pattern | NEW Pattern |
|---------|------------|-------------|
| "Before Deploying" | Run bootstrap init | Verify empirica CLI installed |
| "Initialize Session" | Bootstrap class example | `empirica session-create --ai-id <agent>` |
| "Verify Setup" | Check bootstrap status | Check session table in database |
| "Troubleshooting" | Bootstrap errors | Session creation errors |

---

## Pattern Summary (For Finding All Issues)

### Search Terms to Find All Deprecated References

```bash
# Find bootstrap references
grep -r "ExtendedMetacognitiveBootstrap" docs/production/
grep -r "OptimalMetacognitiveBootstrap" docs/production/
grep -r "from empirica.bootstraps" docs/production/
grep -r "bootstrap.load()" docs/production/

# Find old table references
grep -r "epistemic_assessments" docs/production/
grep -r "preflight_assessments" docs/production/
grep -r "postflight_assessments" docs/production/
grep -r "cascade_metadata" docs/production/

# Find old reflex logger references
grep -r "reflex_logger.py" docs/production/
grep -r "reflex_logger import" docs/production/
```

---

## Verification Checklist

After each file update:

- [ ] All bootstrap imports removed or replaced
- [ ] All removed class references updated
- [ ] All schema references updated (12→8 tables)
- [ ] Example code can actually run
- [ ] No broken cross-references (links still work)
- [ ] Formatting preserved (markdown structure intact)

---

## Related Work (Coordinate With Others)

- **Sonnet (Code):** Also updating session_database.py, CASCADE commands (schema migration)
- **Qwen (Tests):** Will update 4 test files simultaneously
- **Code Lead:** Will consolidate data flow audit docs

---

## Success Metrics

✅ All 5 files updated
✅ No bootstrap references remain in production docs
✅ No deprecated table references in examples
✅ Example code is accurate
✅ Documentation review passes
✅ No warnings about missing classes/tables

---

## Files You'll Be Editing

```
/home/yogapad/empirical-ai/empirica/docs/production/03_BASIC_USAGE.md
/home/yogapad/empirical-ai/empirica/docs/production/12_SESSION_DATABASE.md
/home/yogapad/empirical-ai/empirica/docs/production/13_PYTHON_API.md
/home/yogapad/empirical-ai/empirica/docs/production/15_CONFIGURATION.md
/home/yogapad/empirical-ai/empirica/docs/production/17_PRODUCTION_DEPLOYMENT.md
```

---

## Questions Before You Start

1. **Scope:** Should you also update secondary docs (19_API_REFERENCE, 21_TROUBLESHOOTING)?
2. **Format:** Keep exact same markdown structure or can you reorganize sections?
3. **Examples:** Should all examples be runnable, or can some be pseudo-code?
4. **Review:** Do you want intermediate PRs per file or one final PR?

---

## Next Steps

1. Review this handoff
2. Run grep searches to identify all deprecated references
3. Update files in order (1→5)
4. Test that markdown renders correctly
5. Submit for review

Good luck! These docs are critical for new users. 🚀
