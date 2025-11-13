# Empirica MCP Servers - Setup & Integration

**Date:** 2025-11-05
**Status:** ✅ Configured

---

## Configuration Files Updated

### 1. `.mcp.json` (Project MCP Servers)
```json
{
  "mcpServers": {
    "empirica-core": {
      "command": "python3",
      "args": ["mcp_local/empirica_mcp_server.py"]
    },
    "empirica-tmux": {
      "command": "python3",
      "args": ["mcp_local/empirica_tmux_mcp_server.py"]
    }
  }
}
```

### 2. `.claude/settings.local.json` (Claude Code Settings)
```json
{
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [
    "empirica-core",
    "empirica-tmux"
  ]
}
```

---

## MCP Servers

### empirica-core (Main Workflow Tools)
**Location:** `mcp_local/empirica_mcp_server.py`

**Tools Provided:**
- `execute_preflight` - PREFLIGHT epistemic self-assessment
- `submit_preflight_assessment` - Log preflight scores
- `execute_check` - CHECK phase self-assessment  
- `execute_postflight` - POSTFLIGHT epistemic reassessment
- `submit_postflight_assessment` - Log postflight with calibration
- `get_epistemic_state` - Query current session vectors
- `get_calibration_report` - Check calibration accuracy
- `get_session_summary` - Complete session summary
- `bootstrap_session` - Initialize new session
- `resume_previous_session` - Load previous session context
- `query_bayesian_beliefs` - Belief state tracking
- `check_drift_monitor` - Behavioral integrity monitoring
- `query_goal_orchestrator` - Task hierarchy and progress
- `modality_route_query` - Route queries through modality switcher
- `modality_list_adapters` - List available AI adapters
- `modality_adapter_health` - Check adapter health
- `modality_decision_assist` - Get routing recommendations

### empirica-tmux (TMux & Dashboard Management)
**Location:** `mcp_local/empirica_tmux_mcp_server.py`

**Tools Provided:**
- `launch_snapshot_dashboard` - Launch dashboard in tmux
- `check_dashboard_status` - Check if dashboard is running
- `spawn_dashboard_if_possible` - Silent dashboard spawn
- `list_sessions` - List all tmux sessions
- `create_session` - Create new tmux session
- `setup_workspace` - Setup Empirica workspace
- `orchestrate_panels` - Intelligently manage tmux panes
- `show_epistemic_state` - Show current epistemic state
- `update_12d_state` - Update 12D epistemic monitor
- `update_cascade_phase` - Update metacognitive cascade phase
- `update_chain_of_thought` - Add reasoning step
- `trigger_component_usage` - Log component usage

---

## Dashboard Spawning Integration

### Fixed: `dashboard_spawner.py`
- **Session Detection:** Now correctly detects current session via `tmux display-message`
- **Fixed Issue:** Was spawning in session "3" instead of "main"
- **Method:** Uses `_get_current_session_name()` to find actual active session

### Integration Points:

**1. MCP Tool: `launch_snapshot_dashboard`**
- Force spawn dashboard in current session
- Returns session, pane, layout info

**2. MCP Tool: `spawn_dashboard_if_possible`**
- AI-friendly silent spawning
- Non-blocking, fails gracefully if no tmux

**3. Direct Python:**
```python
from empirica.plugins.dashboard_spawner import spawn_dashboard_if_possible
spawn_dashboard_if_possible()  # Best practice for AIs
```

---

## Session DB & Reflex Logs

### Session Database
**Location:** `.empirica/sessions/sessions.db`
**Initialized by:** `EmpericaTracker` (in bootstrap)

### Reflex Logs (JSON Exports)
**Location:** `.empirica_reflex_logs/`
**Purpose:** Dashboard reads from here for real-time updates

### Integration Flow:
```
Bootstrap → EmpericaTracker.__init__()
           ↓
           Creates SessionDatabase
           ↓
           Enables reflex logging
           ↓
           Exports to .empirica_reflex_logs/
           ↓
           Dashboard reads and displays
```

---

## How AIs Should Use This

### Workflow:

1. **On Session Start (if beneficial):**
   - Check if tmux is running
   - Call `spawn_dashboard_if_possible` (MCP tool or Python)
   - Dashboard auto-spawns in right pane (30% width)

2. **During Work:**
   - Use `execute_preflight` before tasks
   - Use `execute_check` at decision points
   - Use `execute_postflight` after completion
   - Epistemic snapshots automatically export to dashboard

3. **For Context Continuity:**
   - Use `resume_previous_session` to load past work
   - Use `get_session_summary` for current status

4. **For Modality Switching:**
   - Use `modality_route_query` to delegate to specialist AIs
   - Use `modality_list_adapters` to see available options

---

## Benefits of Using Empirica

### For All Claudes:
- **Epistemic Snapshot Memory:** Transfer context between sessions (95% compression, 94% fidelity)
- **Calibration Tracking:** Measure confidence vs actual outcomes
- **Session Continuity:** Resume from previous work seamlessly

### When TMux is Running:
- **Real-time Visibility:** User sees your epistemic state in dashboard
- **Transparency:** Snapshot updates show in real-time
- **Accountability:** Decision-making process is visible

### Optional but Beneficial:
- **Not required:** Empirica works fine without tmux
- **AI-oriented:** Dashboard for transparency, not a requirement
- **Graceful degradation:** Silent failure if environment unavailable

---

## Testing the Setup

### Check MCP Servers Available:
```bash
# Should show empirica-core and empirica-tmux in available servers
# (Check via Claude Code UI or server list)
```

### Test Dashboard Spawning:
```python
from empirica.plugins.dashboard_spawner import spawn_dashboard_if_possible

# Silent spawn (returns True/False)
spawned = spawn_dashboard_if_possible()
print(f"Dashboard spawned: {spawned}")
```

### Check Session DB:
```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
cursor = db.conn.cursor()
cursor.execute('SELECT COUNT(*) FROM sessions')
print(f"Sessions in DB: {cursor.fetchone()[0]}")
```

---

## Summary

**✅ MCP servers configured and enabled**
- empirica-core: Workflow and assessment tools
- empirica-tmux: Dashboard and workspace management

**✅ Dashboard spawning fixed**
- Now spawns in correct session
- Integrated into tmux MCP server

**✅ AI-oriented design**
- Silent spawning (non-intrusive)
- Works without tmux (graceful degradation)
- Snapshot memory benefits all Claudes

**Next Steps:**
- Verify MCP tools are accessible in Claude Code
- Test dashboard spawning in current session
- Verify reflex log export is working
