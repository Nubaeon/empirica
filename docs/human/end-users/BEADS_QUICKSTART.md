## BEADS Integration (Optional Issue Tracking)

Empirica can optionally integrate with **BEADS** (Dependency-Aware Issue Tracker) to track goals as issues with automatic dependency management.

### What is BEADS?

- Dependency-aware issue tracking (tracks blockers automatically)
- Git-friendly (syncs to `.beads/issues.jsonl`)
- Agent-optimized (JSON output, ready work detection)
- Works alongside Empirica's epistemic tracking

### Installation

```bash
pip install beads-project
cd your-project
bd init
```

### Usage

**Create goal with BEADS tracking:**
```bash
empirica goals-create \
  --session-id <SESSION> \
  --objective "Implement OAuth2 authentication" \
  --success-criteria "Auth works" \
  --use-beads

# Output includes beads_issue_id
{
  "ok": true,
  "goal_id": "uuid-here",
  "beads_issue_id": "empirica-abc",  # ← Automatically created!
  ...
}
```

**Add subtasks with dependencies:**
```bash
empirica goals-add-subtask \
  --goal-id <GOAL_ID> \
  --description "Map OAuth2 endpoints" \
  --importance high \
  --use-beads

# Subtask automatically linked as dependency in BEADS
```

**Find ready work (BEADS + Epistemic):**
```bash
empirica goals-ready --session-id <SESSION>

# Combines:
# - BEADS: What's unblocked by dependencies?
# - Empirica: What am I epistemically ready for?
# Result: Tasks you can actually do right now
```

### Per-Project Configuration

Enable BEADS by default for a project:

```yaml
# .empirica/project.yaml
beads:
  default_enabled: true  # Goals use BEADS unless --no-beads
```

Priority order:
1. `--use-beads` flag (always wins)
2. Config file `"use_beads": true`
3. Project default `default_enabled: true`
4. Default: opt-in (false)

### Why Use BEADS?

**Without BEADS:**
- Goals tracked in database only
- No dependency awareness
- Manual tracking of what's blocked

**With BEADS:**
- Goals synced to issue tracker
- Automatic dependency tracking
- `bd ready` shows unblocked work
- Git-friendly (version controlled issues)
- `goals-ready` combines dependencies + epistemic state

### Example Workflow

```bash
# 1. Create goal with BEADS
empirica goals-create \
  --session-id $SESSION \
  --objective "Add OAuth2 support" \
  --use-beads

# 2. Add subtasks (auto-linked as dependencies)
empirica goals-add-subtask --goal-id $GOAL --description "Research OAuth2 spec" --use-beads
empirica goals-add-subtask --goal-id $GOAL --description "Implement token refresh" --use-beads

# 3. Check ready work
bd ready  # Shows: "Research OAuth2 spec" (no blockers)
          # Hides: "Implement token refresh" (blocked by research)

# 4. Work on unblocked task
empirica preflight --session-id $SESSION
# ... do work ...
empirica postflight --session-id $SESSION

# 5. Complete task
bd close empirica-abc --reason "Research complete"

# 6. Next task becomes unblocked automatically
bd ready  # Now shows: "Implement token refresh"
```

### When to Use BEADS

**Use BEADS when:**
- Multiple sessions working on same project
- Complex dependencies between tasks
- Want git-trackable issue history
- Need dependency-aware work queues

**Skip BEADS when:**
- Single-session exploratory work
- No external dependencies
- Prefer simpler setup

### Learn More

- BEADS GitHub: https://github.com/cased/beads
- `bd --help` for CLI reference
- `empirica goals-ready --help` for filtering options
