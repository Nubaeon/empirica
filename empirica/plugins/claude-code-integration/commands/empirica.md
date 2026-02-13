---
description: "Toggle Empirica tracking: /empirica on | off | status"
allowed-tools: ["Bash(empirica *)", "Bash(python3 *)", "Bash(cat *)", "Bash(rm *)", "Read"]
---

# /empirica - Epistemic Tracking Toggle

**Arguments:** `on` | `off` | `status`

## For `/empirica off`:

1. Check loop state - is there a PREFLIGHT without a subsequent POSTFLIGHT?
```bash
empirica epistemics-list --session-id $EMPIRICA_SESSION_ID --output json 2>/dev/null
```

2. If loop is **open** (PREFLIGHT exists without matching POSTFLIGHT) - DENY:
> Cannot go off-the-record while inside an epistemic loop. Close your loop first with POSTFLIGHT, then try again.

3. If loop is **closed** - write the signal file:
```bash
python3 -c "
import json, time
from pathlib import Path
signal = {
    'paused_at': time.time(),
    'paused_at_iso': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    'reason': 'User requested /empirica off',
    'session_id': '$(echo $EMPIRICA_SESSION_ID)'
}
p = Path.home() / '.empirica' / 'sentinel_paused'
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(signal, indent=2))
print('Signal file written')
"
```

4. Log the transition:
```bash
empirica finding-log --session-id $EMPIRICA_SESSION_ID --finding "Empirica tracking paused (off-the-record). Reason: user requested." --impact 0.3 --subject "empirica-toggle"
```

5. Confirm: **Empirica is now OFF-THE-RECORD.** Sentinel enforcement paused. Use `/empirica on` to resume.

## For `/empirica on`:

1. Check if paused:
```bash
cat ~/.empirica/sentinel_paused 2>/dev/null
```

2. If **not paused**: Empirica is already on-the-record. No change needed.

3. If **paused** - read gap duration, remove signal file, log:
```bash
python3 -c "
import json, time
from pathlib import Path
p = Path.home() / '.empirica' / 'sentinel_paused'
if p.exists():
    data = json.loads(p.read_text())
    gap = int(time.time() - data.get('paused_at', time.time()))
    minutes = gap // 60
    print(f'Was off-record for {minutes}m')
    p.unlink()
    print('Signal file removed')
else:
    print('Not paused')
"
```

4. Log the transition:
```bash
empirica finding-log --session-id $EMPIRICA_SESSION_ID --finding "Empirica tracking resumed (on-the-record). Gap: <DURATION>." --impact 0.3 --subject "empirica-toggle"
```

5. Confirm: **Empirica is now ON-THE-RECORD.** Sentinel enforcement resumed. Run PREFLIGHT to start a new epistemic loop.

## For `/empirica status`:

1. Check pause state and current loop:
```bash
python3 -c "
import json, time
from pathlib import Path
p = Path.home() / '.empirica' / 'sentinel_paused'
if p.exists():
    data = json.loads(p.read_text())
    gap = int(time.time() - data.get('paused_at', time.time()))
    print(f'OFF-RECORD (paused {gap // 60}m ago)')
else:
    print('ON-RECORD (tracking active)')
"
```
