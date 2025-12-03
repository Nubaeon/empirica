# Deprecated Global Database

## File: sessions.db.deprecated

**Original Location:** `~/.empirica/sessions.db`  
**Deprecated:** 2025-12-03  
**Reason:** Consolidated to project-local database only

### Why Deprecated?

Empirica now uses **project-local** storage only:
- ✅ `./.empirica/sessions/sessions.db` (current working directory)
- ❌ `~/.empirica/sessions.db` (global - deprecated)

This eliminates confusion between multiple databases and ensures sessions are project-scoped.

### Data

- **Sessions:** 131 sessions (Nov 2024 - Nov 2025)
- **Size:** 954KB
- **Status:** Read-only archive

### If You Need This Data

To view old sessions:
```bash
sqlite3 empirica-dev/archive/old-databases/sessions.db.deprecated
.tables
SELECT session_id, ai_id, start_time FROM sessions ORDER BY start_time DESC LIMIT 10;
```

To migrate specific sessions to current database:
```bash
# Export from old DB
sqlite3 sessions.db.deprecated ".dump sessions" > old_sessions.sql

# Import to new DB (careful - may have ID conflicts)
sqlite3 ./.empirica/sessions/sessions.db < old_sessions.sql
```
