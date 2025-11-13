# Empirica Dashboard

Terminal-based monitoring for epistemic snapshot memory quality.

## Quick Start

### Command Line
```bash
# Monitor current session
python3 empirica/dashboard/snapshot_monitor.py

# Monitor specific session
python3 empirica/dashboard/snapshot_monitor.py <session_id>
```

### From Python
```python
from empirica.dashboard.snapshot_monitor import launch_dashboard

# Use current session
launch_dashboard()

# Use specific session
launch_dashboard(session_id="abc-123-def")
```

## Dashboard Features

### Display Sections

1. **Header**
   - Session ID (8-char preview)
   - AI Model (e.g., claude-sonnet-4)
   - Current cascade phase (PREFLIGHT, INVESTIGATE, ACT, etc.)
   - Transfer count (number of AI hops)

2. **Compression Status**
   - Token budget usage (simulated 200k context)
   - Compression ratio (typically 95%+)
   - Memory reliability score with color coding
   - Fidelity metrics (≥0.90 threshold)
   - Information loss tracking (≤15% tolerance)

3. **Snapshot Timeline**
   - Up to 5 recent snapshots (toggle to 20 with 'f')
   - Timestamp, phase, and AI for each
   - Key vector values (KNOW, CONTEXT, UNCERTAINTY)
   - Delta visualization (changes from previous state)
   - Reliability warnings when <80%

4. **Command Bar**
   - Interactive keyboard shortcuts

### Interactive Commands

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit dashboard |
| `r` | Refresh | Force immediate refresh |
| `f` | Full | Toggle between 5 and 20 snapshots |
| `e` | Export | Export current snapshot to JSON |
| `d` | Details | Show all 13 vectors with bars |

### Color Coding

Memory reliability is color-coded for instant visual feedback:

- 🔵 **Blue (90-100%)**: EXCELLENT - Snapshot highly reliable
- 🟢 **Green (80-89%)**: GOOD - Snapshot reliable
- 🟡 **Yellow (70-79%)**: FAIR - Monitor closely
- 🟠 **Magenta (60-69%)**: DEGRADED - Refresh recommended
- 🔴 **Red (<60%)**: CRITICAL - Must refresh

## Details View

Press `d` to toggle detailed metrics view showing:

- All 13 epistemic vectors with progress bars
- Grouped by category:
  - **Gate**: ENGAGEMENT
  - **Foundation**: KNOW, DO, CONTEXT
  - **Comprehension**: CLARITY, COHERENCE, SIGNAL, DENSITY
  - **Execution**: STATE, CHANGE, COMPLETION, IMPACT
  - **Meta-Epistemic**: UNCERTAINTY

## Requirements

- Python 3.8+
- Terminal with ANSI color support
- Minimum 80x24 terminal size
- curses library (included in standard Python)
  - Windows users: `pip install windows-curses`

## Architecture

```
SnapshotMonitor
├── EpistemicSnapshotProvider (data access)
├── EmpericaTracker (session management)
└── SessionDatabase (persistence)
```

## Example Output

```
┌─ EMPIRICA SNAPSHOT MEMORY TRACKER ───────────────────────┐
│ Session: b0faec86...    Model: claude-sonnet-4           │
│ Phase: ACT              Memory: 2 transfers              │
├──────────────────────────────────────────────────────────┤
│ CONTEXT COMPRESSION STATUS                               │
│ Token Budget: 50,000 / 200,000 (25% used)                │
│ ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 🟢 PLENTY       │
│                                                           │
│ Compression: 96% (18,000 → 720 tokens)                   │
│ Reliability: ████████████████░░░░ 80% 🟢 GOOD            │
│ Fidelity: 0.85 ✅ (≥0.90 threshold)                      │
│ Info Loss: 15% (≤15% tolerance) ✅                       │
│                                                           │
│ SNAPSHOT TIMELINE (3 snapshots)                          │
│ 23:02 ACT [test_claude] <- CURRENT                       │
│       KNOW 0.80 | CONTEXT 0.85 | UNCERTAINTY 0.30        │
│       D COMPLETION +0.25 UP | D UNCERTAINTY -0.15 DOWN   │
│ 23:02 INVESTIGATE [test_claude]                          │
│       KNOW 0.70 | CONTEXT 0.80 | UNCERTAINTY 0.45        │
│       D KNOW +0.15 UP | D CONTEXT +0.15 UP               │
│ 23:02 PREFLIGHT [test_claude]                            │
│       KNOW 0.55 | CONTEXT 0.65 | UNCERTAINTY 0.60        │
├─ COMMANDS ──────────────────────────────────────────────┤
│ [Q]uit [R]efresh [F]ull [E]xport [D]etails              │
└──────────────────────────────────────────────────────────┘
```

## Integration

The dashboard integrates with:

1. **Phase 1**: Core snapshot data structures
2. **EpistemicSnapshotProvider**: Snapshot retrieval and management
3. **EmpericaTracker**: Session tracking and current state
4. **SessionDatabase**: Persistent storage

## Troubleshooting

### No session found
- Start an Empirica session first, or provide a session ID
- Use: `EmpericaTracker.get_instance(ai_id="your_ai")`

### Terminal too small
- Resize terminal to at least 80x24
- Some content may be truncated on smaller terminals

### Colors not showing
- Ensure terminal supports ANSI colors
- Try a different terminal emulator

### curses error on Windows
- Install: `pip install windows-curses`

## Next Steps

- **Phase 3**: MCP Tools Integration (snapshot_create, snapshot_get_latest, etc.)
- **Phase 4**: Adapter Integration (cross-AI context transfer)
- **Phase 5**: Domain Vector Plugin System

## Contributing

The dashboard is modular and extensible:

- Add new display sections in `draw_*` methods
- Extend color schemes in `get_color_for_reliability`
- Add new commands in the `main_loop` key handler

## License

Part of the Empirica framework.
