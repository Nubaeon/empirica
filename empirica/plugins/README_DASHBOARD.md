# Dashboard Spawner - Quick Start

**For AIs:** One-line dashboard visibility

**For Users:** Just run in tmux (optional)

---

## AI Usage

```python
from empirica.plugins.dashboard_spawner import spawn_dashboard_if_possible

# That's it! Works if tmux available, silent otherwise
spawn_dashboard_if_possible()
```

---

## What It Does

- **Detects tmux:** Checks if running in tmux session
- **Spawns dashboard:** Creates split pane with real-time monitor
- **Silent failure:** If no tmux, everything still works fine
- **Non-intrusive:** Doesn't change Empirica behavior

---

## For End-Users

**You don't need to do anything.**

If you want dashboard visibility:
1. Run in tmux: `tmux`
2. AI will auto-spawn dashboard
3. See real-time updates in right pane

If not in tmux:
- Empirica works fine without dashboard
- No errors, no problems

---

## Full Documentation

See: `docs/plugins/DASHBOARD_VISIBILITY.md`

---

**Dashboard = Transparency, not requirement**
