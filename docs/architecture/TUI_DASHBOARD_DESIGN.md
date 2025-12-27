# Empirica TUI Dashboard - MIT Version

## Purpose
Simple terminal-based dashboard for monitoring AI activity in the current project. Prevents accidental writes to wrong database by showing active context clearly.

## Design Principles

1. **Single-Project Focus**: Monitor ONE project at a time (current git repo)
2. **SSH-Friendly**: Pure terminal UI, works over SSH
3. **Tmux-Compatible**: Designed for side pane or split screen
4. **Action Hooks**: Interactive prompts for epistemic uncertainty gates
5. **Zero Dependencies**: Uses Python textual (or rich) - no web server needed

## Target User: You in Tmux

```
┌─ Tmux Layout ──────────────────────────────┐
│                                            │
│  Pane 1: AI Working (empirica commands)   │
│  ────────────────────────────────────────  │
│                                            │
│  Pane 2: TUI Dashboard (monitoring)       │
│  ────────────────────────────────────────  │
│                                            │
└────────────────────────────────────────────┘
```

## Dashboard Layout (80x24 terminal)

```
┌─ EMPIRICA PROJECT MONITOR ───────────────────────────────┐
│ 📁 Project: empirica                                      │
│ 🗄️  Database: /empirical-ai/empirica/.empirica/sessions/ │
│ 📂 Git Repo: /home/yogapad/empirical-ai/empirica         │
│ 🆔 Active Session: abc123 (AI: claude-code)              │
│ ⏱️  Session Time: 00:15:32                                │
├───────────────────────────────────────────────────────────┤
│ 🎯 CURRENT ACTIVITY                                       │
│ Phase: CHECK (Cycle 2)                                    │
│ Confidence: ████████░░ 75% (MEDIUM)                       │
│ Status: Investigating authentication flow                 │
│ Time in phase: 3m 45s                                     │
├───────────────────────────────────────────────────────────┤
│ 📊 EPISTEMIC STATE                                        │
│ Engagement    ██████████ 0.85                             │
│ Know          ███████░░░ 0.70 ⬆ +0.15                     │
│ Context       ██████░░░░ 0.60 ⬆ +0.10                     │
│ Uncertainty   █████░░░░░ 0.45 ⬇ -0.20                     │
├───────────────────────────────────────────────────────────┤
│ 📝 RECENT COMMANDS (last 5)                               │
│ 14:32:15 finding-log "Found OAuth2 refresh pattern"      │
│ 14:30:42 check --confidence 0.75 → proceed               │
│ 14:28:10 unknown-log "MFA behavior unclear"              │
│ 14:25:33 preflight-submit --session-id abc123            │
│ 14:23:01 session-create --ai-id claude-code              │
├───────────────────────────────────────────────────────────┤
│ 💡 SUGGESTIONS                                            │
│ • Confidence at 75% - ready to proceed                    │
│ • 2 unknowns logged - consider investigation             │
├───────────────────────────────────────────────────────────┤
│ [Q] Quit  [R] Refresh  [C] Clear  [H] Help               │
└───────────────────────────────────────────────────────────┘
```

## Data Sources

### 1. Project Context (Static - Read Once)
```python
from empirica.config.path_resolver import debug_paths

context = debug_paths()
# Returns:
# - git_root: /path/to/repo
# - session_db: /path/to/sessions.db
# - empirica_root: /path/to/.empirica
```

### 2. Active Session (Poll Every 1s)
```sql
-- Query sessions table for most recent active session
SELECT session_id, ai_id, start_time, end_time, project_id
FROM sessions
WHERE end_time IS NULL
ORDER BY start_time DESC
LIMIT 1;
```

### 3. Latest Epistemic State (Poll Every 1s)
```sql
-- Query latest reflex for active session
SELECT phase, round_num, engagement, know, do, context,
       clarity, coherence, signal, density, state, change,
       completion, impact, uncertainty, timestamp
FROM reflexes
WHERE session_id = ?
ORDER BY timestamp DESC
LIMIT 1;
```

### 4. Recent Activity (Poll Every 1s)
```python
# Watch SQLite database for new inserts (via timestamp)
# OR tail JSON output from commands (if running with --output json)
# OR watch git notes for new epistemic checkpoints
```

## Action Hooks (Interactive Prompts)

### Trigger Conditions
Monitor epistemic state and show interactive prompts when:

1. **Low Confidence (<40%)** + **High Uncertainty (>60%)**
   ```
   ┌─ ⚠️  AI NEEDS INPUT ────────────────────────┐
   │ Confidence: 35% (LOW)                      │
   │ Uncertainty: 0.65 (HIGH)                   │
   │                                            │
   │ Suggested Actions:                         │
   │ [1] 🔍 Investigate Further (Recommended)   │
   │ [2] ⚡ Proceed with Caution                │
   │ [3] 💬 I Know This - Let Me Tell You       │
   │ [Esc] Let AI Decide                        │
   └────────────────────────────────────────────┘
   ```

2. **Medium Confidence (40-70%)**
   ```
   ┌─ ⚡ AI SEEKING CONFIRMATION ───────────────┐
   │ Confidence: 65% (MEDIUM)                   │
   │ Ready to proceed?                          │
   │                                            │
   │ [Y] Yes, Proceed                           │
   │ [N] No, Investigate More                   │
   │ [R] Review Plan First                      │
   └────────────────────────────────────────────┘
   ```

3. **Goal Blocked**
   ```
   ┌─ 🛑 GOAL BLOCKED ──────────────────────────┐
   │ Goal: Implement OAuth2                     │
   │ Blocked: Missing API credentials           │
   │                                            │
   │ [1] 🔑 I'll Provide Credentials Now        │
   │ [2] 📋 Create Subtask for Later            │
   │ [3] 🧪 Use Mock Data                       │
   │ [4] ❌ Abandon Goal                        │
   └────────────────────────────────────────────┘
   ```

## Implementation

### Tech Stack
- **Python textual** - Modern TUI framework (reactive, component-based)
- **SQLite** - Direct database queries (no HTTP layer)
- **File watching** - Monitor database file for changes (inotify on Linux)

### File Structure
```
empirica/tui/
├── __init__.py
├── dashboard.py          # Main TUI app
├── widgets/
│   ├── project_header.py # Project context widget
│   ├── activity_panel.py # Current activity display
│   ├── vectors_panel.py  # Epistemic vectors bars
│   ├── commands_log.py   # Recent commands list
│   └── action_prompt.py  # Interactive prompt widget
└── monitors/
    ├── session_monitor.py  # Poll session DB
    └── db_watcher.py       # Watch for DB changes
```

### Main Command
```bash
# Launch dashboard for current project
empirica dashboard

# Launches TUI, detects current project automatically
# Shows: Project context, active session, epistemic state
# Polls database every 1s for updates
# Ctrl+C to exit
```

### Dashboard App (Textual)
```python
from textual.app import App
from textual.widgets import Header, Footer, Static
from empirica.data.session_database import SessionDatabase
from empirica.config.path_resolver import debug_paths

class EmpiricaDashboard(App):
    """Empirica TUI Dashboard"""

    def compose(self):
        yield Header()
        yield ProjectHeader()
        yield ActivityPanel()
        yield VectorsPanel()
        yield CommandsLog()
        yield Footer()

    def on_mount(self):
        # Set up 1s polling for database updates
        self.set_interval(1.0, self.refresh_data)

    def refresh_data(self):
        # Query latest session, epistemic state, commands
        # Update widgets
        pass
```

## Workflow Example

### User in Tmux
```bash
# Terminal 1 (AI working)
$ empirica session-create --ai-id claude-code --output json
$ empirica preflight-submit config.json
$ empirica finding-log "Discovered X"

# Terminal 2 (Dashboard monitoring)
$ empirica dashboard
# Shows:
# - Project: empirica
# - Session: abc123
# - Latest: finding-log executed
# - Vectors: know=0.70, uncertainty=0.45
```

### Action Hook Triggered
```
AI hits CHECK phase with confidence=0.35

Dashboard detects: confidence < 0.4

Shows interactive prompt:
┌─ ⚠️  LOW CONFIDENCE ────────────────────────┐
│ AI has low confidence (35%)                │
│ Investigate further or proceed?            │
│ [1] Investigate (Recommended)              │
│ [2] Proceed with Caution                   │
└────────────────────────────────────────────┘

User presses [1]

Dashboard writes JSON config to /tmp/action_response.json:
{
  "action": "investigate",
  "reason": "Low confidence",
  "timestamp": "2025-12-25T14:30:00Z"
}

AI reads action and continues investigation cycle
```

## Advantages Over Web Dashboard

1. ✅ **SSH-friendly** - Works over SSH with no port forwarding
2. ✅ **Tmux-compatible** - Fits in terminal split pane
3. ✅ **Zero overhead** - No web server, no WebSockets
4. ✅ **Direct DB access** - Fast, no HTTP layer
5. ✅ **Terminal native** - Keyboard shortcuts, vim-like navigation
6. ✅ **Copy-paste friendly** - Text mode, easy to copy session IDs

## Future Enhancements (Post-MVP)

1. **Multi-session view** - Show all active sessions in current project
2. **Historical playback** - Replay past session's epistemic trajectory
3. **Export to JSON** - Dump current state for debugging
4. **Custom themes** - Dark/light mode, color schemes
5. **Sound notifications** - Beep on low confidence (optional)

## Workspace Dashboard (Premium Feature)

For paying clients, extend to workspace-level:
- Monitor multiple projects simultaneously
- Show which AI is in which project
- Cross-project epistemic handoffs
- Requires workspace.db implementation

---

**Next Steps:**
1. Implement basic TUI with textual
2. Add session monitoring (poll database)
3. Add epistemic state display (vectors + bars)
4. Add action hooks (interactive prompts)
5. Test in tmux split pane
