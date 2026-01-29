---
name: empirica
description: "Use when the user says '/empirica on', '/empirica off', '/empirica status', or wants to toggle epistemic tracking on/off. Controls on-the-record vs off-the-record mode for the Sentinel enforcement system."
version: 1.0.0
---

# /empirica - Epistemic Tracking Toggle

Toggle Empirica's epistemic tracking on or off. Think of it as going **on-the-record** or **off-the-record**.

## Usage

- `/empirica off` - Pause epistemic tracking (off-the-record)
- `/empirica on` - Resume epistemic tracking (on-the-record)
- `/empirica status` - Show current tracking state

## What This Does

**When OFF (off-the-record):**
- Sentinel stops enforcing epistemic loops
- No PREFLIGHT required for praxic actions
- Findings/unknowns/dead-ends not tracked
- Statusline shows `OFF-RECORD`
- The *fact* that tracking was paused IS logged (timeline continuity)

**When ON (on-the-record):**
- Sentinel enforces epistemic loops normally
- PREFLIGHT required before praxic work
- Full tracking resumes
- Fresh PREFLIGHT needed to re-enter a loop

## Rules

**Critical constraint:** You CANNOT go off-the-record while inside an epistemic loop.
If a PREFLIGHT exists without a matching POSTFLIGHT, the loop must be closed first.

```
LOOP CLOSED ──/empirica off──► OFF-RECORD ──/empirica on──► NEEDS PREFLIGHT
     ▲                                                           │
     └────────────── POSTFLIGHT ◄── work ◄── PREFLIGHT ─────────┘
```

## Implementation

When the user invokes this skill, execute the following:

### For `/empirica off`:

1. **Check loop state** - Query the database for open loops:
```bash
empirica epistemics-list --session-id <CURRENT_SESSION_ID> --output json 2>/dev/null
```
Or directly check: is there a PREFLIGHT without a subsequent POSTFLIGHT?

2. **If loop is open** - DENY the toggle:
> Cannot go off-the-record while inside an epistemic loop.
> Close your loop first with POSTFLIGHT, then try again.

3. **If loop is closed** (or no PREFLIGHT exists) - Write the signal file:
```bash
python3 -c "
import json, time
from pathlib import Path
signal = {
    'paused_at': time.time(),
    'paused_at_iso': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    'reason': 'User requested /empirica off',
    'session_id': '<CURRENT_SESSION_ID>'
}
p = Path.home() / '.empirica' / 'sentinel_paused'
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(signal, indent=2))
print('done')
"
```

4. **Log the transition** as a finding:
```bash
empirica finding-log --session-id <SESSION_ID> --finding "Empirica tracking paused (off-the-record) at <TIMESTAMP>. Reason: user requested." --impact 0.3 --subject "empirica-toggle"
```

5. **Confirm to user:**
> Empirica is now **OFF-THE-RECORD**. Sentinel enforcement paused.
> Use `/empirica on` to resume tracking.

### For `/empirica on`:

1. **Check if actually paused** - Read the signal file:
```bash
cat ~/.empirica/sentinel_paused 2>/dev/null
```

2. **If not paused** - inform user:
> Empirica is already on-the-record. No change needed.

3. **If paused** - Remove the signal file and log resumption:
```bash
rm ~/.empirica/sentinel_paused
```

4. **Calculate gap duration** from the signal file's `paused_at` timestamp.

5. **Log the transition** as a finding:
```bash
empirica finding-log --session-id <SESSION_ID> --finding "Empirica tracking resumed (on-the-record). Was off-record for <DURATION>." --impact 0.3 --subject "empirica-toggle"
```

6. **Confirm to user:**
> Empirica is now **ON-THE-RECORD**. Sentinel enforcement resumed.
> Run PREFLIGHT to start a new epistemic loop.

### For `/empirica status`:

1. Check if `~/.empirica/sentinel_paused` exists
2. If paused: show paused_at timestamp and duration
3. If active: show current loop state (PREFLIGHT/POSTFLIGHT status)
