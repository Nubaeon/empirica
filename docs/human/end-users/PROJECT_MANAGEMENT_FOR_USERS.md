# Project Management Guide for Empirica Users

## Understanding Empirica's Project-Centric Design

Empirica is designed around **projects** - each project has its own:
- ✅ **Database** (`.empirica/sessions/sessions.db`)
- ✅ **Git repository** (auto-detected from git remote)
- ✅ **Epistemic context** (findings, unknowns, goals)
- ✅ **Configuration** (`.empirica/config.yaml`)

## Basic Project Operations

### 1. Initialize a New Project

```bash
# Navigate to your git repository
cd your-project

# Initialize Empirica (creates .empirica/ directory)
empirica project-init
```

**What this does:**
- Creates `.empirica/config.yaml` with project settings
- Registers project in local database
- Links project to git repository URL

### 2. Switch Between Projects

```bash
# Simply change directories
cd ../other-project

# Empirica automatically detects project from git remote
empirica project-bootstrap  # Shows current project context
```

**How it works:**
- Empirica reads `.git/config` to find repository URL
- Matches URL to project in database
- Loads project-specific context

### 3. List All Projects

```bash
empirica project-list
```

Shows all projects with:
- Project ID (for API commands)
- Description
- Session count
- Active status

### 4. Get Project Context

```bash
empirica project-bootstrap --project-id <PROJECT_ID>
```

Returns:
- Recent findings (what was learned)
- Open unknowns (what's unclear)
- Dead ends (what didn't work)
- Reference documents

## Advanced Project Management

### Project-Specific Commands

All commands automatically use the current project:

```bash
# Create session (auto-linked to current project)
empirica session-create --ai-id myagent

# Log finding (auto-linked to current project)
empirica finding-log --session-id <ID> --finding "..."

# Create goal (auto-linked to current project)
empirica goals-create --session-id <ID> --objective "..."
```

### Manual Project Specification

Override auto-detection:

```bash
empirica session-create --ai-id myagent --project-id <PROJECT_ID>
```

## Database & Migration

### How Database Works

Each project has its own SQLite database:
- Location: `.empirica/sessions/sessions.db`
- Contains: sessions, findings, unknowns, goals, checkpoints
- **Isolated per-project**: No shared data between projects

### Database Schema Updates

Empirica handles migrations automatically:

```bash
# When you run any command, Empirica checks schema version
# If outdated, it runs migrations automatically
# No manual intervention needed
```

### Schema Migration Process

1. **Check version**: Empirica compares current schema with required version
2. **Run migrations**: Applies SQL migrations from `empirica/data/migrations/`
3. **Update version**: Records new schema version in database

**You never need to run migrations manually!**

## Best Practices

### 1. One Project Per Repository

```bash
# ✅ GOOD: One git repo = One Empirica project
my-project/          # Git repo
  .git/               # Git files
  .empirica/          # Empirica project data
  src/                # Your code
```

### 2. Clear Project Descriptions

```bash
# Set descriptive project name during init
empirica project-init --description "My Awesome AI Project"
```

### 3. Regular Context Loading

```bash
# Always load context when starting work
echo '{"session_id": "...", "vectors": {...}}' | empirica preflight-submit -
empirica project-bootstrap
```

### 4. Project Isolation

```bash
# Each project has separate:
# - Database (no shared data)
# - Configuration
# - Epistemic history
# - Git notes (optional)
```

## Troubleshooting

### "Project not found" Error

**Cause**: Git remote URL doesn't match any registered project

**Fix**:
```bash
# Option 1: Reinitialize project
empirica project-init --force

# Option 2: Specify project manually
empirica session-create --project-id <PROJECT_ID>
```

### Database Corruption

**Cause**: Rare, but can happen with abrupt shutdowns

**Fix**:
```bash
# Backup database
cp .empirica/sessions/sessions.db .empirica/sessions/sessions.db.backup

# Reinitialize (creates new database)
rm -rf .empirica/sessions/
empirica project-init
```

## Multi-Project Workflows

### Working on Multiple Projects

```bash
# Project A
cd project-a
empirica project-bootstrap  # Shows Project A context
# ... work on Project A ...

# Project B
cd ../project-b
empirica project-bootstrap  # Shows Project B context
# ... work on Project B ...
```

### Cross-Project Coordination

```bash
# Share findings between projects
echo '{"finding": "...", "project_id": "PROJECT_B_ID"}' | empirica finding-log -
```

## Security & Privacy

### Data Isolation

- ✅ Each project database is **completely isolated**
- ✅ No shared data between projects
- ✅ `.empirica/` is in `.gitignore` (never committed)
- ✅ Git notes are optional (you control what's shared)

### Backup Recommendations

```bash
# Backup project data
cp -r .empirica/ empirica-backup-$(date +%Y%m%d)/

# Restore from backup
cp -r empirica-backup-*/.empirica/ .
```

## Summary

**Key Points:**
1. ✅ **Auto-switching**: Empirica detects projects from git remote
2. ✅ **Auto-migrations**: Database schema updates automatically
3. ✅ **Isolation**: Each project has separate database/config
4. ✅ **No manual DB management**: Empirica handles everything
5. ✅ **Context loading**: Always bootstrap when starting work

**Need help?** Check `empirica project-list` and `empirica project-bootstrap --help`