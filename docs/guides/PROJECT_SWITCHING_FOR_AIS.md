# Project Switching for AI Agents - Critical UX Guide

**Date:** 2025-12-23  
**Status:** CRITICAL - Must be understood by all AI agents  
**Problem:** AIs don't have clear signals when they've switched projects

---

## The Problem

When an AI agent:
1. Navigates to a new directory (`cd ../other-project`)
2. Creates a new project (`empirica project-init`)
3. Receives user instruction to "work on project X"

**The AI has NO CLEAR SIGNAL that context has switched.**

This causes:
- ❌ Writing findings/unknowns to wrong project
- ❌ Creating sessions linked to wrong project_id
- ❌ Bootstrap showing wrong context
- ❌ Confusion about which project is "active"

---

## How Project Linking Works (Current Implementation)

### Session Creation (Automatic Linking)

When `empirica session-create` runs:

```python
# 1. Session created in local .empirica/sessions/sessions.db
session_id = db.create_session(ai_id="myai")

# 2. Auto-detect project from git remote URL
git_url = subprocess.run(['git', 'remote', 'get-url', 'origin']).stdout

# 3. Find project in projects table by matching repo URL
cursor.execute("SELECT id FROM projects WHERE repos LIKE ?", (f'%{git_url}%',))
project_id = cursor.fetchone()['id']

# 4. Link session to project
cursor.execute("UPDATE sessions SET project_id = ? WHERE session_id = ?", 
               (project_id, session_id))
```

**Critical detail:** This looks up project in the **local database** (`.empirica/sessions/sessions.db`) where the command is run.

### Project Bootstrap (Context Loading)

When `empirica project-bootstrap --project-id <ID>` runs:

```python
# 1. Opens local database
db = SessionDatabase()  # Uses .empirica/sessions/sessions.db in CWD

# 2. Loads project context
project = db.projects.get_by_id(project_id)
sessions = db.get_sessions_for_project(project_id)
findings = db.get_project_findings(project_id)
```

**Key insight:** Everything is **project-local** and **directory-scoped**.

---

## Current State: What Works

✅ **Project Init** creates `.empirica/project.yaml` with `project_id`  
✅ **Session Create** auto-links to project via git remote URL  
✅ **Database** is project-local (`.empirica/sessions/sessions.db`)  
✅ **Findings/unknowns** are stored with `project_id`  

---

## Current State: What's Missing

❌ **No "you are here" banner** when AI switches directories  
❌ **No validation** that current project matches expected project  
❌ **No warning** when writing to different project than discussed  
❌ **No clear workflow** for "I'm switching to project X now"  

---

## Solution: Clear Project Context Signals

### 1. Add Project Context to All Command Outputs

**Every command should show:**
```
📁 Current Project: empirica-web (258aa934...)
📍 Location: /home/user/empirica-web
```

**Implementation:**
```python
def _print_project_context():
    """Print current project context (call at start of every command)"""
    try:
        git_root = get_git_root()
        if not git_root:
            print("⚠️  Not in a git repository - no project context")
            return
        
        project_yaml = git_root / '.empirica' / 'project.yaml'
        if not project_yaml.exists():
            print(f"⚠️  No .empirica/project.yaml found - run 'empirica project-init'")
            return
        
        with open(project_yaml) as f:
            config = yaml.safe_load(f)
            project_name = config.get('name', 'Unknown')
            project_id = config.get('project_id', 'Unknown')
        
        print(f"📁 Project: {project_name} ({project_id[:8]}...)")
        print(f"📍 Location: {git_root}")
        print()
    except Exception as e:
        logger.debug(f"Could not load project context: {e}")
```

### 2. Enhance Bootstrap to Show "You Are Here"

```bash
$ cd ../empirica-web && empirica project-bootstrap --project-id empirica-web

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 PROJECT CONTEXT SWITCH DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Current Project: Empirica Web
🆔 Project ID: 258aa934-a34b-4773-b1bb-96f429de6761
📍 Repository: https://github.com/Nubaeon/empirica-web.git
📊 Local Database: .empirica/sessions/sessions.db

⚠️  IMPORTANT: All commands now write to THIS project's database.
   Findings, sessions, goals → stored in empirica-web context.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Project Context: empirica-web
   Total sessions: 65
   ...
```

### 3. Add `empirica project-switch` Command

**For explicit switching:**
```bash
$ empirica project-switch empirica-web

✅ Switched to project: Empirica Web
📍 Location: /home/user/empirica-web
🆔 Project ID: 258aa934...

📊 Quick Status:
   • 65 sessions recorded
   • 91 findings logged
   • 2 open BEADS issues
   • Last activity: 2 hours ago

💡 Next steps:
   • empirica session-create --ai-id myai
   • empirica project-bootstrap --project-id empirica-web
```

### 4. Session Creation Warning

**When creating session in new location:**
```bash
$ cd ../new-project
$ empirica session-create --ai-id myai

⚠️  PROJECT CONTEXT CHANGE DETECTED

Previous project: empirica-web (258aa934...)
Current location: /home/user/new-project

❓ This session will be linked to: new-project
   Is this correct? [y/N]:
```

---

## Workflow for AI Agents

### When User Says "Work on project X"

**Step 1: Navigate to project**
```bash
cd ../project-x  # or wherever it is
```

**Step 2: Verify project context**
```bash
empirica project-bootstrap --project-id project-x
```
This will show:
- ✅ "You are here" banner
- ✅ Project name and ID
- ✅ Recent findings/unknowns
- ✅ Available skills

**Step 3: Create session (auto-links to current project)**
```bash
empirica session-create --ai-id myai
```

**Step 4: Work with confidence**
Now all `finding-log`, `unknown-log`, `goals-create`, etc. write to **this project's database**.

---

## Implementation Checklist

- [ ] Add `_print_project_context()` utility function
- [ ] Call it at start of all command handlers
- [ ] Enhance bootstrap output with "you are here" banner
- [ ] Add project-switch command
- [ ] Add session-create project change warning
- [ ] Document in system prompt
- [ ] Test with empirica-web (current case)

---

## For System Prompts

**Add this guidance:**

> **🚨 CRITICAL: Project Context Awareness**
>
> When you switch directories or the user says "work on project X":
>
> 1. **ALWAYS run bootstrap first:**
>    ```bash
>    empirica project-bootstrap --project-id <project>
>    ```
>
> 2. **Verify the "📁 Current Project" banner matches expectations**
>
> 3. **If mismatch detected:**
>    - Stop immediately
>    - Alert user: "I'm in directory X but expected project Y"
>    - Ask for clarification
>
> 4. **All subsequent commands write to the current project's database**
>    - Findings → current project
>    - Sessions → current project
>    - Goals → current project
>
> **DO NOT assume project context from conversation history alone.**  
> **ALWAYS verify with bootstrap.**

---

## Edge Cases

### Case 1: User has multiple repos for same project

**Current:** `session-create` matches by git URL → finds first match  
**Solution:** Use `project.yaml` as source of truth, not just git URL

### Case 2: AI switches directories mid-session

**Current:** No signal, continues writing to old project  
**Solution:** Each command checks `CWD` and warns if changed

### Case 3: Workspace-init creates multiple projects

**Current:** Creates `.empirica-project/PROJECT_CONFIG.yaml` in each repo  
**Solution:** Each repo becomes its own isolated project context

---

## Technical Details

### Database Scoping

```
~/.empirica/                     # Global config/credentials
    config.yaml                  # Global settings
    credentials.yaml             # API keys

/path/to/project-a/.empirica/    # Project A data
    config.yaml                  # Project settings
    project.yaml                 # Project metadata (has project_id)
    sessions/
        sessions.db              # All project A data

/path/to/project-b/.empirica/    # Project B data
    config.yaml                  # Project settings
    project.yaml                 # Project metadata (has project_id)
    sessions/
        sessions.db              # All project B data (separate!)
```

**Key insight:** Each project has its own `sessions.db`. The `project_id` in `project.yaml` links to a record in that local DB's `projects` table.

### How get_session_db_path() Works

```python
def get_session_db_path():
    """Returns path to local sessions.db in CWD or parent"""
    # 1. Check CWD for .empirica/sessions/sessions.db
    # 2. Walk up parent dirs until .git found
    # 3. Return .empirica/sessions/sessions.db in that git root
    # 4. If none found, return ~/.empirica/session_data.db (fallback)
```

**This means:** Database is **directory-scoped**, not **project-scoped** from global state.

---

## Summary for AI Agents

🎯 **Golden Rule:** When you change directories, you change project context.

✅ **Always verify context with bootstrap**  
✅ **Trust the "📁 Current Project" banner**  
✅ **All data writes go to CWD's .empirica/sessions/sessions.db**  
✅ **Session auto-links to project via git remote URL**  

❌ **Don't assume project from conversation**  
❌ **Don't write to old project after switching dirs**  
❌ **Don't skip bootstrap when starting work**
