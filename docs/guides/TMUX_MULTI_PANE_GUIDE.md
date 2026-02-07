# Running Multiple Claude Instances with Tmux

This guide explains how to run multiple Claude Code instances simultaneously, each with isolated project context.

---

## Why Tmux + Empirica?

When running multiple Claude instances (e.g., one working on API, another on frontend), Empirica automatically isolates their context:

- **Separate transactions** — Each pane has its own PREFLIGHT→POSTFLIGHT cycle
- **Separate goals** — Goals created in one pane don't interfere with another
- **Separate sessions** — Each pane can work on different projects

---

## How It Works

### Automatic Pane Detection

Empirica detects your tmux pane via `$TMUX_PANE` environment variable:

```
%0 → instance_id: tmux_0
%1 → instance_id: tmux_1
%4 → instance_id: tmux_4
```

Files are automatically namespaced:
- `.empirica/active_transaction_tmux_0.json`
- `~/.empirica/instance_projects/tmux_0.json`

### Instance-Aware Resolution

When you run Empirica commands, they resolve context from your specific pane:

```bash
# In tmux pane %0
empirica goals-list          # Shows goals for tmux_0 context

# In tmux pane %1
empirica goals-list          # Shows goals for tmux_1 context
```

---

## Setup Guide

### 1. Start Tmux Session

```bash
# Create named session
tmux new-session -s empirica-work

# Create additional panes
tmux split-window -h    # Vertical split
tmux split-window -v    # Horizontal split
```

### 2. Assign Projects to Panes

In each pane, set up the project context:

```bash
# Pane 0: API project
cd ~/projects/api
empirica session-create --ai-id claude-code
empirica project-switch api

# Pane 1: Frontend project
cd ~/projects/frontend
empirica session-create --ai-id claude-code
empirica project-switch frontend
```

### 3. Work Independently

Each pane now has isolated context:

```bash
# Pane 0: API work
empirica preflight-submit - << 'EOF'
{"session_id": "auto", "task_description": "Implement auth endpoint", "vectors": {"know": 0.7}}
EOF
empirica goals-create --objective "Add JWT validation"

# Pane 1: Frontend work (simultaneously)
empirica preflight-submit - << 'EOF'
{"session_id": "auto", "task_description": "Build login form", "vectors": {"know": 0.6}}
EOF
empirica goals-create --objective "Create login component"
```

---

## Verify Isolation

Check that each pane has its own context:

```bash
# Check instance ID
echo "Instance: $(python3 -c 'import os; print(os.getenv("TMUX_PANE", "not-tmux"))')"

# Check active project
cat ~/.empirica/instance_projects/tmux_$(echo $TMUX_PANE | tr -d '%').json 2>/dev/null | jq .project_path

# Check active transaction
cat .empirica/active_transaction_tmux_$(echo $TMUX_PANE | tr -d '%').json 2>/dev/null | jq .
```

---

## Common Workflows

### Multi-Project Work

```bash
# Pane layout:
# ┌─────────────────┬─────────────────┐
# │   API (tmux_0)  │ Frontend (tmux_1)│
# ├─────────────────┼─────────────────┤
# │  Tests (tmux_2) │   Docs (tmux_3)  │
# └─────────────────┴─────────────────┘

# Each pane tracks its own:
# - Active session
# - Active transaction
# - Goal progress
# - Epistemic vectors
```

### Parallel Investigation

```bash
# Spawn investigation in pane 1 while continuing work in pane 0
# Pane 0: Main work
empirica goals-create --objective "Implement feature X"

# Pane 1: Investigation
empirica goals-create --objective "Research approach for feature X"
# Findings from pane 1 are available to pane 0 via project-search
```

### Cross-Pane Handoff

```bash
# Pane 0: Create handoff
empirica handoff-create --to-ai claude-research --context "Please investigate auth patterns"

# Pane 1: Pick up handoff
empirica handoff-query --status pending
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `TMUX_PANE` | Auto-detected pane ID | `%0`, `%1`, `%4` |
| `EMPIRICA_INSTANCE_ID` | Override instance detection | `custom_instance` |

---

## Troubleshooting

### Wrong Project Context

If commands use wrong project:
```bash
# Check what Empirica thinks is active
python3 -c "from empirica.utils.session_resolver import get_active_project_path; print(get_active_project_path())"

# Force project switch
empirica project-switch <correct-project>
```

### Stale Transaction Files

If transaction seems stuck:
```bash
# Check transaction status
cat .empirica/active_transaction_tmux_$(echo $TMUX_PANE | tr -d '%').json

# Close orphaned transaction
empirica postflight-submit - << 'EOF'
{"session_id": "auto", "vectors": {"know": 0.5}, "summary": "Closing orphaned transaction"}
EOF
```

### Pane Not Detected

If outside tmux or pane detection fails:
```bash
# Manually set instance ID
export EMPIRICA_INSTANCE_ID=manual_1
```

---

## Related Documentation

- [Multi-Instance Isolation](../architecture/INSTANCE_ISOLATION.md) — Technical architecture
- [Project Switching](./PROJECT_SWITCHING_FOR_AIS.md) — Project context management
- [Session Management](../human/end-users/SESSION_GOAL_WORKFLOW.md) — Session and goal workflows
