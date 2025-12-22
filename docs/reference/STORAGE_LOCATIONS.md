# Empirica Storage Locations Reference

**Version:** 2.0  
**Last Updated:** 2025-12-01  
**Status:** ✅ Canonical Reference

---

## Overview

Empirica uses **two distinct storage scopes** for different types of data:

1. **Global (Home Directory)** - User-level configuration and shared resources
2. **Project-local (Current Working Directory)** - Project-specific session data

---

## Canonical Storage Locations

### Global Storage (`~/.empirica/`)

**Location:** `$HOME/.empirica/` (expands to user's home directory)

**Purpose:** User-level configuration, credentials, and shared resources that persist across all projects.

**Contents:**

```
~/.empirica/
├── config.yaml              # User configuration (global settings)
├── credentials.yaml         # API keys and secrets (NEVER commit!)
├── calibration/             # Calibration data (learning patterns)
├── onboarding/              # Onboarding session exports
├── usage_monitor.json       # Usage statistics (modality switcher)
└── mcp_server.pid          # MCP server process ID
```

**Files:**
- `config.yaml` - Global configuration (modality switcher, adapters, thresholds)
- `credentials.yaml` - API credentials (OpenRouter, Gemini, etc.)
- `calibration/` - Adaptive uncertainty calibration data
- `onboarding/` - Onboarding wizard session exports
- `usage_monitor.json` - Modality switcher usage tracking
- `mcp_server.pid` - MCP server process tracking

**Code References:**
```python
# Config
Path.home() / ".empirica" / "config.yaml"

# Credentials
Path.home() / ".empirica" / "credentials.yaml"

# Calibration
os.path.expanduser("~/.empirica/calibration")

# Onboarding
Path.home() / ".empirica" / "onboarding"

# MCP PID
Path.home() / ".empirica" / "mcp_server.pid"

# Usage monitor
Path.home() / ".empirica" / "usage_monitor.json"
```

---

### Project-Local Storage (`.empirica/`)

**Location:** `./.empirica/` (relative to current working directory)

**Purpose:** Project-specific session data, goals, tasks, and checkpoints. Each project maintains its own isolated data.

**Contents:**

```
./.empirica/
└── sessions/
    └── sessions.db          # SQLite database (all session data)
```

**Database Tables:**
- `sessions` - Session metadata
- `cascades` - Cascade executions
- `epistemic_assessments` - 13-vector assessments
- `preflight_assessments` - PREFLIGHT phase data
- `check_phase_assessments` - CHECK phase data
- `postflight_assessments` - POSTFLIGHT phase data
- `reflexes` - Checkpoint system (Phase 1.5)
- `goals` - Goal tracking (Phase 1)
- `subtasks` - Task decomposition
- `handoff_reports` - Session handoffs (Phase 1.6)
- `divergence_tracking` - Delegate/trustee divergence
- `drift_monitoring` - Long-term behavioral patterns
- `bayesian_beliefs` - Evidence-based belief tracking
- `investigation_tools` - Investigation tool usage
- `cascade_metadata` - Custom metadata
- `epistemic_snapshots` - State snapshots

**Code References:**
```python
# Default path (project-local)
Path.cwd() / ".empirica" / "sessions" / "sessions.db"

# SessionDatabase initialization
db = SessionDatabase()  # Defaults to ./.empirica/sessions/sessions.db

# Explicit path
db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
```

---

## Why Two Scopes?

### Global Storage Rationale
**User-level configuration should be shared across projects:**
- API credentials (don't duplicate secrets)
- Adapter preferences (consistent across projects)
- Calibration data (learning persists)
- Onboarding progress (one-time setup)

### Project-Local Storage Rationale
**Session data should be project-scoped:**
- Isolation (project A doesn't see project B's sessions)
- Git-friendly (can `.gitignore` `.empirica/` per project)
- Clean separation (delete project = delete sessions)
- Multi-project workflows (work on multiple projects simultaneously)

---

## Migration Notes

### Pre-v2.0 Behavior
Some early code incorrectly used `~/.empirica/sessions/` for session storage. This caused:
- Tests failing (expected home directory)
- Session data confusion (home vs project)
- Multi-project conflicts

### v2.0 Fix (December 2024)
**Standardized on project-local storage:**
- ✅ Fixed test fixtures (`test_checkpoint_bugs_regression.py`, `test_e2e_workflows.py`)
- ✅ Verified all `SessionDatabase()` calls use project-local default
- ✅ Documented canonical locations in this file

### If You Have Data in `~/.empirica/sessions/`
**Migrating old data:**
```bash
# If you have sessions in the old location:
if [ -d ~/.empirica/sessions ]; then
    echo "⚠️  Found old session database in home directory"
    echo "   Moving to project-local storage..."
    
    # Create project-local directory
    mkdir -p .empirica/sessions
    
    # Copy database
    cp ~/.empirica/sessions/sessions.db .empirica/sessions/
    
    # Backup old location
    mv ~/.empirica/sessions ~/.empirica/sessions.backup
    
    echo "✅ Migration complete!"
fi
```

---

## Environment Variables

### Override Database Location (Advanced)
```bash
# Force custom database path (for testing or special workflows)
export EMPIRICA_DB_PATH="/custom/path/sessions.db"
```

**Note:** Not currently implemented, but reserved for future use.

---

## Best Practices

### For Users
1. **Never commit credentials:** Add `~/.empirica/credentials.yaml` to global gitignore
2. **Gitignore project data:** Add `.empirica/` to project `.gitignore`
3. **Backup important sessions:** Export sessions before deleting projects
4. **Use git notes for coordination:** Goals/handoffs stored in git notes (not database)

### For Developers
1. **Always use `SessionDatabase()` without args** - Defaults are correct
2. **Only override `db_path` for tests** - Use `tmp_path` fixtures
3. **Document any new global storage** - Update this file
4. **Test both locations** - Verify global/project separation

---

## Code Examples

### Correct Usage
```python
# ✅ Project-local session database (default)
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()  # Uses ./.empirica/sessions/sessions.db
db.create_session(session_id="abc", ai_id="copilot")

# ✅ Global configuration
from pathlib import Path

config_path = Path.home() / ".empirica" / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)
```

### Incorrect Usage
```python
# ❌ Don't use home directory for sessions
db = SessionDatabase(db_path=str(Path.home() / ".empirica" / "sessions" / "sessions.db"))

# ❌ Don't use project-local for config
config_path = Path.cwd() / ".empirica" / "config.yaml"  # Should be Path.home()
```

---

## Testing Considerations

### Test Fixtures
```python
@pytest.fixture
def db_path(tmp_path):
    """Provide temporary database for testing"""
    # Use tmp_path for isolated tests
    db_file = tmp_path / "test_sessions.db"
    return db_file

@pytest.fixture
def project_db():
    """Use actual project database (integration tests)"""
    db_path = Path.cwd() / ".empirica" / "sessions" / "sessions.db"
    if db_path.exists():
        return db_path
    else:
        pytest.skip("Project database doesn't exist")
```

---

## Related Documentation

- **Architecture:** `docs/architecture/GIT_CHECKPOINT_ARCHITECTURE.md`
- **Session Database:** `empirica/data/session_database.py` (docstring)
- **Git Notes Storage:** `docs/guides/git/empirica_git.md`
- **Configuration:** `docs/production/15_CONFIGURATION.md`

---

## Version History

**v2.0 (2025-12-01):**
- Standardized on project-local session storage (`./.empirica/`)
- Fixed test fixtures to use `Path.cwd()` instead of `Path.home()`
- Documented canonical locations
- Added migration guide

**v1.x (Pre-2024):**
- Mixed behavior (some code used home directory)
- Tests expected `~/.empirica/sessions/`
- Inconsistent across codebase

---

## Troubleshooting

### Git Notes Not Being Created (Fixed in v0.9.1)

**Symptom:** `storage_layers.git_notes = false` in CASCADE command output

**Root Cause:** Git subprocess command missing `-F -` flag to read from stdin

**Fixed in:** v0.9.1 (commit daff2801, 2025-12-11)

**Solution:** Updated `GitEnhancedReflexLogger` to use `-F -` flag in git notes commands.

**Verification:**
```bash
# Check if git notes are being created
git notes --ref empirica/session/<SESSION_ID>/PREFLIGHT/1 show HEAD

# Should display JSON checkpoint data
```

**See Also:**
- Full technical details: `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md` (Troubleshooting section)
- Bug fix changelog: `docs/reference/CHANGELOG.md` (v0.9.1)

---

**📌 Remember:** Config is global, data is project-local!
