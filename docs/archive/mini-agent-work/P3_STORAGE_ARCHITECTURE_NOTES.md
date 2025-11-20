# P3 Storage Architecture - Important Notes

**Date:** 2025-11-19
**Context:** Database initialization for fresh installs

---

## 🔍 **Database Initialization Strategy**

### How Tables Are Created

#### 1. Core Session Tables
**Created by:** `SessionDatabase` class (`empirica/data/session_database.py`)

**When:** First call to any session operation (bootstrap, preflight, etc.)

**Tables Created:**
- `sessions`
- `cascades`
- `epistemic_assessments`
- `preflight_assessments`
- `postflight_assessments`
- `check_phase_assessments`
- `bayesian_beliefs`
- `drift_monitoring`
- `investigation_tools`
- `goals`
- `subtasks`
- `success_criteria`
- etc.

**Code:**
```python
# empirica/data/session_database.py:46-60
def __init__(self, db_path: Optional[str] = None):
    if db_path is None:
        base_dir = Path.cwd() / '.empirica' / 'sessions'
        base_dir.mkdir(parents=True, exist_ok=True)  # Creates directory
        db_path = base_dir / 'sessions.db'

    self.conn = sqlite3.connect(str(self.db_path))
    self._create_tables()  # Creates all tables
```

#### 2. Handoff Reports Table
**Created by:** `DatabaseHandoffStorage` class (`empirica/core/handoff/storage.py`)

**When:** First time `DatabaseHandoffStorage()` is instantiated

**Table Created:**
- `handoff_reports`

**Code:**
```python
# empirica/core/handoff/storage.py:205-222
def __init__(self, db_path: Optional[str] = None):
    if db_path is None:
        base_dir = Path.cwd() / '.empirica' / 'sessions'
        base_dir.mkdir(parents=True, exist_ok=True)  # Creates directory
        db_path = base_dir / 'sessions.db'

    self.conn = sqlite3.connect(str(self.db_path))
    self._create_table()  # Creates handoff_reports table
```

---

## ✅ **Fresh Install Scenario (Correct Behavior)**

### Scenario 1: User installs Empirica, runs bootstrap

```bash
# Fresh install - no .empirica/ directory
empirica bootstrap --ai-id "claude-code"
```

**What happens:**
1. Bootstrap command calls `SessionDatabase()`
2. `.empirica/sessions/` directory created
3. `sessions.db` file created
4. All core tables created (sessions, cascades, etc.)
5. ✅ System ready to use

**Database state:**
- ✅ `.empirica/sessions/sessions.db` exists
- ✅ Core tables exist
- ❌ `handoff_reports` table does NOT exist yet (not needed until first handoff)

### Scenario 2: User creates first handoff (AFTER Mini-agent's fix)

```bash
# After completing PREFLIGHT→POSTFLIGHT
empirica handoff-create \
  --session-id "abc123" \
  --task-summary "..." \
  --key-findings '[...]' \
  --next-session-context "..."
```

**What happens (with HybridHandoffStorage):**
1. CLI instantiates `HybridHandoffStorage()`
2. `HybridHandoffStorage.__init__()` instantiates `DatabaseHandoffStorage()`
3. `DatabaseHandoffStorage.__init__()` calls `_create_table()`
4. `handoff_reports` table created (if not exists)
5. Handoff stored in BOTH git notes and database
6. ✅ System fully initialized

**Database state:**
- ✅ `.empirica/sessions/sessions.db` exists
- ✅ Core tables exist
- ✅ `handoff_reports` table NOW exists
- ✅ First handoff stored

---

## 🚨 **Current Problem (Before Mini-agent's Fix)**

### Scenario: User creates first handoff (CURRENT broken state)

```bash
empirica handoff-create --session-id "abc123" ...
```

**What happens (with current GitHandoffStorage only):**
1. CLI instantiates `GitHandoffStorage()` only
2. `DatabaseHandoffStorage()` is NEVER instantiated
3. `handoff_reports` table is NEVER created
4. Handoff stored in git notes only
5. ❌ Database empty

**Database state:**
- ✅ `.empirica/sessions/sessions.db` exists
- ✅ Core tables exist
- ❌ `handoff_reports` table does NOT exist
- ❌ No handoffs in database
- ⚠️ Query by AI ID broken (no database to query)

---

## ✅ **Solution: Mini-agent's HybridHandoffStorage Fix**

### After Fix Applied

**Code change:**
```python
# OLD (BROKEN):
from empirica.core.handoff.storage import GitHandoffStorage
storage = GitHandoffStorage()

# NEW (FIXED):
from empirica.core.handoff.storage import HybridHandoffStorage
storage = HybridHandoffStorage()
# This instantiates BOTH GitHandoffStorage AND DatabaseHandoffStorage
```

**Behavior on fresh install:**
1. User runs bootstrap → Core tables created
2. User creates first handoff → `HybridHandoffStorage()` instantiated
3. `DatabaseHandoffStorage()` instantiated as part of hybrid init
4. `handoff_reports` table created automatically
5. Handoff stored in BOTH git notes and database
6. ✅ Everything works!

---

## 📋 **Key Design Principles**

### 1. Lazy Table Creation
Tables are created **when first needed**, not at bootstrap:
- ✅ Reduces bootstrap time
- ✅ Only creates tables actually used
- ✅ Safe for upgrades (IF NOT EXISTS)

### 2. Database Path Convention
All components use the same database:
```python
base_dir = Path.cwd() / '.empirica' / 'sessions'
db_path = base_dir / 'sessions.db'
```

This ensures:
- ✅ Single database file (not multiple DBs)
- ✅ Consistent location across components
- ✅ Easy to backup (one file)

### 3. CREATE TABLE IF NOT EXISTS
Every table creation uses `IF NOT EXISTS`:
```sql
CREATE TABLE IF NOT EXISTS handoff_reports (...)
```

This ensures:
- ✅ Safe to call multiple times
- ✅ No errors on upgrades
- ✅ Idempotent initialization

### 4. Directory Creation
Every component creates its directory if missing:
```python
base_dir.mkdir(parents=True, exist_ok=True)
```

This ensures:
- ✅ Works on fresh install
- ✅ No manual setup required
- ✅ Safe on existing installs

---

## 🎯 **For Mini-Agent: What This Means**

### Your HybridHandoffStorage Implementation

When you create `HybridHandoffStorage`:

```python
class HybridHandoffStorage:
    def __init__(self, repo_path=None, db_path=None):
        self.git_storage = GitHandoffStorage(repo_path)
        self.db_storage = DatabaseHandoffStorage(db_path)  # ← This line!
```

**That line** (`DatabaseHandoffStorage(db_path)`) will:
1. Create `.empirica/sessions/` directory if needed
2. Connect to `sessions.db`
3. Create `handoff_reports` table if it doesn't exist
4. Create indexes on `ai_id`, `timestamp`, `created_at`

**On fresh install:**
- ✅ No errors
- ✅ Table created automatically
- ✅ Ready to store handoffs

**On existing install:**
- ✅ No errors (IF NOT EXISTS)
- ✅ Connects to existing table
- ✅ Ready to store handoffs

### No Additional Setup Required!

You don't need to:
- ❌ Add table creation to `SessionDatabase`
- ❌ Create migration script for schema
- ❌ Manually initialize database
- ❌ Add any special init code

**Just instantiate `DatabaseHandoffStorage()` and it handles everything!**

---

## 🧪 **Testing Fresh Install**

To test your implementation on a fresh install:

```bash
# 1. Backup existing database
mv .empirica/sessions/sessions.db .empirica/sessions/sessions.db.backup

# 2. Remove handoff_reports table specifically (or whole DB for full test)
sqlite3 .empirica/sessions/sessions.db "DROP TABLE IF EXISTS handoff_reports"

# 3. Test bootstrap (creates core tables)
empirica bootstrap --ai-id "test-fresh-install"

# 4. Verify core tables exist
sqlite3 .empirica/sessions/sessions.db ".tables"
# Should see: sessions, cascades, epistemic_assessments, etc.
# Should NOT see: handoff_reports (not created yet)

# 5. Test handoff create (should create handoff_reports table)
empirica handoff-create \
  --session-id "test-123" \
  --task-summary "Testing fresh install" \
  --key-findings '["Test"]' \
  --next-session-context "Test"

# 6. Verify handoff_reports table NOW exists
sqlite3 .empirica/sessions/sessions.db ".tables"
# Should NOW see: handoff_reports

# 7. Verify handoff stored
sqlite3 .empirica/sessions/sessions.db "SELECT COUNT(*) FROM handoff_reports"
# Should return: 1

# 8. Restore backup
mv .empirica/sessions/sessions.db.backup .empirica/sessions/sessions.db
```

---

## 📊 **Architecture Diagram**

```
Fresh Install Flow:
==================

1. empirica bootstrap
   ↓
   SessionDatabase.__init__()
   ↓
   Creates: .empirica/sessions/sessions.db
   ↓
   Creates: sessions, cascades, epistemic_assessments, etc.
   ↓
   ✅ Bootstrap complete


2. empirica handoff-create (with HybridHandoffStorage)
   ↓
   HybridHandoffStorage.__init__()
   ↓
   ├─ GitHandoffStorage.__init__()
   │  └─ Ready to use git notes
   │
   └─ DatabaseHandoffStorage.__init__()
      ↓
      Connects to: sessions.db (already exists from step 1)
      ↓
      Creates: handoff_reports table (if not exists)
      ↓
      Creates: indexes on ai_id, timestamp, created_at
      ↓
      ✅ Database ready to store handoffs
   ↓
   store_handoff() called
   ↓
   ├─ Stores in git notes
   └─ Stores in database
   ↓
   ✅ Handoff stored in BOTH locations
```

---

## 🎯 **Summary for Mini-Agent**

**Q:** "What happens in a fresh install if the DB is not created yet?"

**A:**
1. **Core DB** is created by `SessionDatabase` on first bootstrap/session operation
2. **Handoff table** is created by `DatabaseHandoffStorage` on first handoff operation
3. **Your code** (`HybridHandoffStorage`) will instantiate `DatabaseHandoffStorage`, which creates the table
4. **No special init required** - it just works!

**Your implementation is safe for fresh installs because:**
- ✅ `CREATE TABLE IF NOT EXISTS` prevents errors
- ✅ `mkdir(parents=True, exist_ok=True)` creates directories
- ✅ Lazy initialization defers table creation until needed
- ✅ Same database path convention across all components

**Just write the code as specified in the task - it will work on fresh installs!** 💪

---

**Document Purpose:** Explain database initialization for context
**Audience:** Mini-agent + Future developers
**Status:** Reference documentation for P3 implementation
