---
name: empirica
description: "This skill should be used when the user says '/empirica', '/empirica status', '/empirica on', '/empirica off', asks 'how do I use empirica', 'what empirica commands are there', 'show empirica status', or needs a quick reference for Empirica's core commands and workflow state."
version: 2.0.0
---

# /empirica - Quick Reference & Status

Quick access to Empirica status and core commands. For detailed CASCADE workflow guidance, use `/empirica-framework`.

## Usage

- `/empirica` or `/empirica status` - Show current tracking state and session info
- `/empirica on` - Resume epistemic tracking (on-the-record)
- `/empirica off` - Pause epistemic tracking (off-the-record)

---

## Status Check

When invoked without arguments (or with `status`), display:

1. **Session state** - Active session ID, project, transaction status
2. **CASCADE phase** - Current phase (PREFLIGHT/CHECK/POSTFLIGHT)
3. **Loop state** - Open or closed
4. **Tracking mode** - On-the-record or off-the-record

```bash
# Get session info
empirica session-snapshot --session-id <SESSION_ID> --output json

# Check for open transaction
cat ~/.empirica/active_transaction_*.json 2>/dev/null | jq '.status'

# Check if paused
cat ~/.empirica/sentinel_paused 2>/dev/null
```

---

## Quick Command Reference

### Session & Project

| Command | Purpose |
|---------|---------|
| `empirica session-create --ai-id claude-code` | Start new session |
| `empirica project-bootstrap --session-id <ID>` | Load project context |
| `empirica project-switch <name>` | Switch active project |
| `empirica project-list` | List all projects |

### CASCADE Workflow

| Command | Purpose |
|---------|---------|
| `empirica preflight-submit -` | Measure baseline (JSON stdin) |
| `empirica check-submit -` | Gate noetic→praxic transition |
| `empirica postflight-submit -` | Measure learning delta |

### Noetic Artifacts (Breadcrumbs)

| Command | Purpose |
|---------|---------|
| `empirica finding-log --finding "..."` | Log what was learned |
| `empirica unknown-log --unknown "..."` | Log what's unclear |
| `empirica deadend-log --approach "..."` | Log failed approach |

### Goals & Subtasks

| Command | Purpose |
|---------|---------|
| `empirica goals-create --objective "..."` | Create goal |
| `empirica goals-add-subtask --goal-id <ID>` | Add subtask |
| `empirica goals-complete-subtask --subtask-id <ID>` | Complete subtask |
| `empirica goals-list` | List active goals |

For full command details: `empirica --help` or `/empirica-framework`

---

## Tracking Toggle (On/Off)

Toggle between on-the-record (full tracking) and off-the-record (paused) mode.

### Going Off-Record (`/empirica off`)

**Constraint:** Cannot go off-record while inside an epistemic loop (open PREFLIGHT without POSTFLIGHT).

1. Check loop state:
```bash
empirica epistemics-list --session-id <SESSION_ID> --output json 2>/dev/null
```

2. If loop is open → DENY:
> Cannot go off-the-record while inside an epistemic loop.
> Close your loop first with POSTFLIGHT, then try again.

3. If loop is closed → Write signal file:
```bash
python3 -c "
import json, time
from pathlib import Path
signal = {
    'paused_at': time.time(),
    'paused_at_iso': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    'reason': 'User requested /empirica off',
    'session_id': '<SESSION_ID>'
}
p = Path.home() / '.empirica' / 'sentinel_paused'
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(signal, indent=2))
"
```

4. Log transition and confirm:
```bash
empirica finding-log --session-id <ID> --finding "Tracking paused (off-the-record)" --impact 0.3
```
> Empirica is now **OFF-THE-RECORD**. Sentinel enforcement paused.

### Going On-Record (`/empirica on`)

1. Check if paused: `cat ~/.empirica/sentinel_paused 2>/dev/null`
2. If not paused → Already on-the-record
3. If paused → Remove signal file, log resumption:
```bash
rm ~/.empirica/sentinel_paused
empirica finding-log --session-id <ID> --finding "Tracking resumed (on-the-record)" --impact 0.3
```
> Empirica is now **ON-THE-RECORD**. Run PREFLIGHT to start a new epistemic loop.

---

## Related Skills

- **`/empirica-framework`** - Detailed CASCADE workflow, 13 vectors, calibration, multi-agent operations
- **`/ewm-interview`** - Create personalized workflow protocol

---

## Notes

- CLAUDE.md contains core behavioral configuration (always loaded)
- This skill provides quick reference and status (loaded on `/empirica`)
- `/empirica-framework` provides detailed procedural knowledge (loaded on demand)
