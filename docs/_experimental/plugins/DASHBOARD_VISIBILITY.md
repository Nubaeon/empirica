# Dashboard Visibility Plugin
## AI Orchestration Transparency (Optional)

**Purpose:** Give users visibility into AI orchestration
**Requirement:** Optional - Empirica works fine without it
**For:** AIs doing cognitive orchestration, not end-users

---

## 🎯 Design Philosophy

**Empirica works without tmux/dashboard.** This plugin is purely for transparency:

- Users see what AI is thinking (via dashboard)
- AIs can spawn dashboards automatically (if tmux available)
- Silent failure (if no tmux, everything still works)
- Non-intrusive (doesn't change Empirica behavior)

---

## 🤖 For AIs: How to Use

### **Simple: Auto-Spawn on Orchestration**

```python
# When you start cognitive orchestration, give user visibility
from empirica.plugins.dashboard_spawner import spawn_dashboard_if_possible

# Silent spawn (works if tmux available, silent otherwise)
spawn_dashboard_if_possible()

# Continue with your work (dashboard updates automatically)
from empirica.plugins.modality_switcher import PluginRegistry

registry = PluginRegistry()
result = registry.route_to_adapter("minimax", payload, token_meta)
# Dashboard shows this in real-time!
```

### **Check Before Spawning**

```python
from empirica.plugins.dashboard_spawner import check_dashboard_status, spawn_dashboard

# Check if dashboard already running
status = check_dashboard_status()

if status["status"] != "running":
    # Spawn only if not already running
    result = spawn_dashboard()

    if result["spawned"]:
        print(f"Dashboard spawned: {result['message']}")
```

### **Force Spawn (Replace Existing)**

```python
from empirica.plugins.dashboard_spawner import spawn_dashboard

# Force spawn even if already running
result = spawn_dashboard(force=True)
```

---

## 📋 API Reference

### **spawn_dashboard_if_possible()**

AI-friendly convenience function. Silent success/failure.

```python
spawned: bool = spawn_dashboard_if_possible()
# Returns: True if spawned, False otherwise (not an error!)
```

**Use when:**
- Starting cognitive orchestration
- User requested visibility
- Multi-AI collaboration

**Behavior:**
- ✅ Spawns if tmux available
- ✅ Silent if no tmux (not an error)
- ✅ Skips if already running
- ✅ Non-blocking

### **check_dashboard_status()**

Check if dashboard is running.

```python
status: Dict = check_dashboard_status()

# Possible statuses:
# - "running": Dashboard active
# - "not_running": Tmux available but no dashboard
# - "not_available": Not in tmux
# - "degraded": Tmux available but libtmux missing
```

### **spawn_dashboard(force=False)**

Spawn dashboard with control.

```python
result: Dict = spawn_dashboard(force=False)

# Result fields:
{
    "spawned": bool,
    "reason": str,  # Why it spawned or didn't
    "method": str,  # "libtmux" or "subprocess"
    "session": str,
    "pane": str,
    "message": str
}
```

---

## 🔧 How It Works

### **Auto-Detection**

1. Check if in tmux (`$TMUX` env var)
2. Check if libtmux available
3. Find Empirica root directory
4. Get current tmux session/window
5. Spawn dashboard if appropriate

### **Spawning Strategy**

**Single pane:** Split horizontally (dashboard on right 30%)
```
┌──────────────────┬──────────┐
│                  │          │
│   Main Pane      │Dashboard │
│                  │          │
│      70%         │   30%    │
└──────────────────┴──────────┘
```

**Multiple panes:** Use pane 1 (replace existing process)

### **Silent Failure**

If any of these fail, **Empirica still works**:
- Not in tmux → Skip dashboard
- libtmux not installed → Skip dashboard
- Dashboard already running → Skip spawn
- Error spawning → Log and continue

---

## 🎓 Example: AI Cognitive Orchestration

```python
"""
AI Orchestration with Dashboard Visibility

Scenario: Claude Code orchestrates 4 specialist AIs
"""

from empirica.plugins.dashboard_spawner import spawn_dashboard_if_possible
from empirica.plugins.modality_switcher import PluginRegistry
from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider

# Give user visibility into orchestration
spawn_dashboard_if_possible()
# User now sees dashboard (if in tmux), or nothing changes (if not)

# Start orchestration
registry = PluginRegistry()
provider = EpistemicSnapshotProvider()

# Task decomposition
tasks = [
    ("security_audit", "minimax", "abductive reasoning"),
    ("performance_profile", "qwen", "inductive analysis"),
    ("cost_analysis", "gemini", "deductive calculation")
]

results = []

for task_name, adapter, reasoning_type in tasks:
    print(f"Routing {task_name} to {adapter}...")

    # Create snapshot
    snapshot = provider.create_snapshot(...)

    # Route to specialist AI
    payload = AdapterPayload(
        system=f"You are a {reasoning_type} specialist.",
        user_query=task_name,
        epistemic_snapshot=snapshot
    )

    result = registry.route_to_adapter(adapter, payload, {})
    results.append(result)

    # Dashboard shows this in real-time!
    # User sees: "Snapshot transferred to minimax"

# Synthesize results
synthesis = synthesize_results(results)

print(f"Orchestration complete. User saw it all via dashboard!")
```

---

## 🚫 What NOT to Do

### **❌ Don't require dashboard**

```python
# BAD: Fails if no tmux
if not check_dashboard_status()["status"] == "running":
    raise Error("Dashboard required!")
```

```python
# GOOD: Works either way
spawn_dashboard_if_possible()  # Best effort
# Continue regardless
```

### **❌ Don't force users into tmux**

```python
# BAD: User must use tmux
assert os.environ.get('TMUX'), "Must run in tmux!"
```

```python
# GOOD: Tmux is optional
if spawn_dashboard_if_possible():
    logger.info("Dashboard available for visibility")
else:
    logger.debug("Running without dashboard (still works fine)")
```

### **❌ Don't make it complex**

```python
# BAD: Complex setup for users
print("Please run: tmux new-session -s empirica")
print("Then run: ./launch-empirica.sh")
```

```python
# GOOD: Simple for AIs
spawn_dashboard_if_possible()  # One line, works or silent
```

---

## 📝 For End-Users

**You don't need to do anything.** The AI will spawn the dashboard if:
- You're in tmux
- libtmux is installed

**If not in tmux:** Empirica works fine without dashboard.

**If you want the dashboard:**
```bash
# Option 1: Just run in tmux
tmux
# AI will auto-spawn dashboard

# Option 2: Manually launch dashboard (in separate pane)
cd /path/to/empirica
python3 empirica/dashboard/snapshot_monitor.py
```

---

## 🔍 Troubleshooting

### **Dashboard not spawning?**

```python
from empirica.plugins.dashboard_spawner import check_dashboard_status

status = check_dashboard_status()
print(status)

# Possible reasons:
# - not_in_tmux: Run `tmux` first
# - libtmux_not_available: Run `pip install libtmux`
# - already_running: Dashboard already active
```

### **Want to force respawn?**

```python
from empirica.plugins.dashboard_spawner import spawn_dashboard

# Kill old, spawn new
result = spawn_dashboard(force=True)
print(result)
```

---

## ✅ Best Practices (for AIs)

### **1. Spawn at Orchestration Start**

```python
# When you start complex orchestration
spawn_dashboard_if_possible()
# User gets visibility for entire session
```

### **2. Don't Spawn for Simple Tasks**

```python
# Single adapter call? Skip dashboard
result = registry.route_to_adapter("qwen", payload, {})
# No need for dashboard visibility
```

### **3. Spawn for Multi-AI Workflows**

```python
# Multiple AIs collaborating? Spawn dashboard
spawn_dashboard_if_possible()

for specialist in ["minimax", "qwen", "gemini"]:
    result = route_to_specialist(specialist, ...)
    # User sees each transfer in dashboard
```

---

## 🎯 Summary

**For AIs:**
```python
from empirica.plugins.dashboard_spawner import spawn_dashboard_if_possible
spawn_dashboard_if_possible()  # One line, that's it!
```

**For Users:**
- Run in tmux (optional)
- See AI orchestration in real-time (if in tmux)
- Everything works fine without it

**Design:**
- Non-intrusive
- Silent failure
- Empirica works without it
- Just for transparency

---

**The dashboard is a window into AI orchestration, not a requirement.**

