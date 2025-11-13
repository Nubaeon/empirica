# Dashboard Monitoring

**Empirica v2.0 - Real-Time Tmux Visualization**

---

## Overview

The tmux dashboard provides real-time visualization of:
- Current cascade phase
- 12D epistemic vector states
- Confidence progression
- Investigation progress
- Bayesian discrepancies
- Drift alerts

**Optional Feature:** System works without dashboard.

---

## Prerequisites

### Install Tmux

```bash
# Ubuntu/Debian
sudo apt install tmux

# macOS
brew install tmux

# Verify
tmux -V  # Should show version
```

---

## Quick Start

### Auto-Start Dashboard

```python
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

cascade = CanonicalEpistemicCascade(
    enable_action_hooks=True,
    auto_start_dashboard=True  # Auto-start tmux
)

result = await cascade.run_epistemic_cascade(task, context)
```

### Manual Start

```bash
cd tmux_dashboard
./start_agi_dashboard.sh
```

Then run cascade in same terminal.

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│ EMPIRICA DASHBOARD                                      │
│                                                         │
│ Phase: INVESTIGATE (Round 2/3)                         │
│ Task: Analyze authentication system                    │
│ Confidence: 0.68 → 0.75                               │
│                                                         │
│ ╔══════════════════════════════════════════════════╗  │
│ ║ 12D EPISTEMIC VECTORS                            ║  │
│ ╠══════════════════════════════════════════════════╣  │
│ ║ ENGAGEMENT: ████████████████░░░░░░ 0.85 ✓       ║  │
│ ║                                                  ║  │
│ ║ FOUNDATION (35%):                                ║  │
│ ║   KNOW:    ████████████░░░░░░░░░░ 0.65          ║  │
│ ║   DO:      ██████████████░░░░░░░░ 0.70          ║  │
│ ║   CONTEXT: ██████████░░░░░░░░░░░░ 0.55          ║  │
│ ║                                                  ║  │
│ ║ COMPREHENSION (25%):                             ║  │
│ ║   CLARITY:    ████████████████░░░░ 0.80         ║  │
│ ║   COHERENCE:  ██████████████████░░ 0.90         ║  │
│ ║   SIGNAL:     ██████████████░░░░░░ 0.75         ║  │
│ ║   DENSITY:    ████████░░░░░░░░░░░░ 0.45         ║  │
│ ║                                                  ║  │
│ ║ EXECUTION (25%):                                 ║  │
│ ║   STATE:      ██████████████░░░░░░ 0.70         ║  │
│ ║   CHANGE:     ████████████░░░░░░░░ 0.65         ║  │
│ ║   COMPLETION: ██████████░░░░░░░░░░ 0.55         ║  │
│ ║   IMPACT:     ██████████████░░░░░░ 0.72         ║  │
│ ╚══════════════════════════════════════════════════╝  │
│                                                         │
│ Investigation:                                          │
│   Round 2/3: workspace_scan                            │
│   Confidence gain: +0.07                               │
│                                                         │
│ Bayesian: ✓ Active                                     │
│   Discrepancies: None                                  │
│                                                         │
│ Drift Monitor: ✓ Active                                │
│   Status: Normal                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Configuration

### Enable/Disable Dashboard

```python
# Enable with auto-start
cascade = CanonicalEpistemicCascade(
    enable_action_hooks=True,
    auto_start_dashboard=True
)

# Enable but manual start
cascade = CanonicalEpistemicCascade(
    enable_action_hooks=True,
    auto_start_dashboard=False
)

# Disable completely
cascade = CanonicalEpistemicCascade(
    enable_action_hooks=False
)
```

---

## Dashboard Updates

### What Gets Updated

1. **Phase Transitions**
   - THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT
   - Real-time phase indicator

2. **12D Vector Visualization**
   - Progress bars for each vector
   - Color coding (red/yellow/green)
   - Gate status (✓ or ✗)

3. **Confidence Progression**
   - Initial → current → target
   - Shows improvement over rounds

4. **Investigation Progress**
   - Current round number
   - Tools being used
   - Confidence gains

5. **Bayesian Status**
   - Active/inactive
   - Discrepancies detected
   - Overconfidence/underconfidence alerts

6. **Drift Alerts**
   - Sycophancy detection
   - Tension avoidance detection
   - Behavioral patterns

---

## Action Hooks API

### log_cascade_phase()

```python
from empirica.integration import log_cascade_phase

log_cascade_phase(
    phase='investigate',
    task='Analyze authentication',
    metadata={
        'round': 2,
        'confidence': 0.75,
        'tools_used': ['workspace_scan']
    }
)
```

### log_12d_state()

```python
from empirica.integration import log_12d_state

log_12d_state({
    'engagement': 0.85,
    'know': 0.65,
    'do': 0.70,
    'context': 0.55,
    # ... all 12 vectors
    'overall_confidence': 0.72
})
```

### log_thought()

```python
from empirica.integration import log_thought

log_thought("Investigating workspace structure to improve CONTEXT vector")
```

---

## Customization

### Dashboard Theme

Edit `tmux_dashboard/theme.conf`:

```bash
# Colors
set -g status-style bg=colour235,fg=colour245

# Borders
set -g pane-border-style fg=colour238
set -g pane-active-border-style fg=colour39

# Progress bar colors
# Green: >= 0.70
# Yellow: 0.50-0.69
# Red: < 0.50
```

### Layout

Edit `tmux_dashboard/layout.sh`:

```bash
# Adjust pane sizes
tmux split-window -h -p 60  # 60% width for main panel
tmux split-window -v -p 30  # 30% height for bottom panel
```

---

## Troubleshooting

### Dashboard Not Appearing

**Issue:** Dashboard doesn't show

**Causes:**
1. Tmux not installed
2. Not in tmux session
3. Action hooks disabled

**Solution:**
```bash
# Check tmux
which tmux

# Start tmux session
tmux new -s empirica

# Enable hooks
cascade = CanonicalEpistemicCascade(enable_action_hooks=True)
```

### Updates Not Showing

**Issue:** Dashboard frozen, no updates

**Causes:**
1. Cascade crashed
2. Action hooks failed
3. Tmux pane not refreshing

**Solution:**
```bash
# Refresh tmux
Ctrl+b r  # Refresh pane

# Check cascade logs
# Look for "🔗 Action Hooks enabled"
```

### Permission Errors

**Issue:** Can't write to tmux

**Solution:**
```bash
# Check tmux socket permissions
ls -la /tmp/tmux-*

# Restart tmux server
tmux kill-server
tmux new -s empirica
```

---

## Dashboard Without Tmux

If tmux not available (e.g., Windows), use console logging:

```python
cascade = CanonicalEpistemicCascade(
    enable_action_hooks=False  # Disable tmux
)

# Monitor via print statements in cascade
# Or use custom logging handler
```

---

## Performance Impact

**Dashboard overhead:** < 1ms per update
**Network:** None (local only)
**CPU:** Negligible (tmux rendering)

**Recommendation:** Keep enabled in development, optional in production.

---

## Advanced Usage

### Multiple Cascades

Monitor multiple cascades in different panes:

```bash
# Create multi-pane layout
tmux new-session -s empirica
tmux split-window -h
tmux split-window -v

# Run cascades in different panes
# Each gets its own dashboard section
```

### Remote Monitoring

Monitor cascades on remote server:

```bash
# SSH with tmux
ssh user@server
tmux attach -t empirica

# Dashboard updates in real-time
```

### Recording Sessions

Record dashboard for later review:

```bash
# Start recording
tmux pipe-pane -o 'cat >> ~/empirica_session.log'

# Stop recording
tmux pipe-pane
```

---

## Next Steps

- **Cascade Flow:** [06_CASCADE_FLOW.md](06_CASCADE_FLOW.md)
- **Python API:** [13_PYTHON_API.md](13_PYTHON_API.md)
- **Troubleshooting:** [21_TROUBLESHOOTING.md](21_TROUBLESHOOTING.md)

---

**Real-time visualization for development and debugging!** 📊
