---
description: "Toggle Empirica tracking: /empirica on | off | status"
allowed-tools: ["Bash(empirica *)", "Bash(python3 *)", "Bash(cat *)", "Bash(rm *)", "Read"]
---

# /empirica - Epistemic Tracking Toggle (Per-Instance)

**Arguments:** `on` | `off` | `status`

**Instance Isolation:** Each tmux pane / terminal gets its own pause state.
- Instance file: `~/.empirica/sentinel_paused_{instance_id}`
- Global file: `~/.empirica/sentinel_paused` (pauses ALL instances)

## For `/empirica off`:

1. Check loop state - is there a PREFLIGHT without a subsequent POSTFLIGHT?
```bash
empirica epistemics-list --session-id $EMPIRICA_SESSION_ID --output json 2>/dev/null
```

2. If loop is **open** (PREFLIGHT exists without matching POSTFLIGHT) - DENY:
> Cannot go off-the-record while inside an epistemic loop. Close your loop first with POSTFLIGHT, then try again.

3. If loop is **closed** - write the instance-specific signal file:
```bash
python3 -c "
import json, time, os
from pathlib import Path

# Get instance ID for per-instance isolation
def get_instance_id():
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        return f'tmux_{tmux_pane.lstrip(\"%\")}'
    try:
        import subprocess
        result = subprocess.run(['tty'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            tty = result.stdout.strip()
            if tty and tty != 'not a tty':
                return tty.replace('/dev/', '').replace('/', '-')
    except:
        pass
    return None

base = Path.home() / '.empirica'
instance_id = get_instance_id()
if instance_id:
    safe_id = instance_id.replace('/', '-').replace('%', '')
    pause_file = base / f'sentinel_paused_{safe_id}'
else:
    pause_file = base / 'sentinel_paused'

signal = {
    'paused_at': time.time(),
    'paused_at_iso': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    'reason': 'User requested /empirica off',
    'session_id': '$(echo $EMPIRICA_SESSION_ID)',
    'instance_id': instance_id
}
base.mkdir(parents=True, exist_ok=True)
pause_file.write_text(json.dumps(signal, indent=2))
print(f'Signal file written: {pause_file.name}')
"
```

4. Log the transition:
```bash
empirica finding-log --session-id $EMPIRICA_SESSION_ID --finding "Empirica tracking paused (off-the-record). Reason: user requested." --impact 0.3 --subject "empirica-toggle"
```

5. Confirm: **Empirica is now OFF-THE-RECORD (this instance only).** Sentinel enforcement paused. Use `/empirica on` to resume.

## For `/empirica on`:

1. Check if paused (instance-specific or global):
```bash
python3 -c "
import json, time, os
from pathlib import Path

def get_instance_id():
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        return f'tmux_{tmux_pane.lstrip(\"%\")}'
    try:
        import subprocess
        result = subprocess.run(['tty'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            tty = result.stdout.strip()
            if tty and tty != 'not a tty':
                return tty.replace('/dev/', '').replace('/', '-')
    except:
        pass
    return None

base = Path.home() / '.empirica'
global_file = base / 'sentinel_paused'
instance_id = get_instance_id()
instance_file = None
if instance_id:
    safe_id = instance_id.replace('/', '-').replace('%', '')
    instance_file = base / f'sentinel_paused_{safe_id}'

# Check instance-specific first
if instance_file and instance_file.exists():
    data = json.loads(instance_file.read_text())
    gap = int(time.time() - data.get('paused_at', time.time()))
    print(f'Was off-record for {gap // 60}m (instance: {instance_id})')
    instance_file.unlink()
    print('Instance signal file removed')
elif global_file.exists():
    # Note: We don't remove global file from /empirica on - that would unpause ALL instances
    print('Global pause is active. To unpause all instances, remove ~/.empirica/sentinel_paused')
    print('This instance cannot override global pause.')
else:
    print('Not paused')
"
```

2. If **not paused**: Empirica is already on-the-record. No change needed.

3. Log the transition (only if was paused):
```bash
empirica finding-log --session-id $EMPIRICA_SESSION_ID --finding "Empirica tracking resumed (on-the-record). Gap: <DURATION>." --impact 0.3 --subject "empirica-toggle"
```

4. Confirm: **Empirica is now ON-THE-RECORD.** Sentinel enforcement resumed. Run PREFLIGHT to start a new epistemic loop.

## For `/empirica status`:

1. Check pause state (both instance-specific and global):
```bash
python3 -c "
import json, time, os
from pathlib import Path

def get_instance_id():
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        return f'tmux_{tmux_pane.lstrip(\"%\")}'
    try:
        import subprocess
        result = subprocess.run(['tty'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            tty = result.stdout.strip()
            if tty and tty != 'not a tty':
                return tty.replace('/dev/', '').replace('/', '-')
    except:
        pass
    return None

base = Path.home() / '.empirica'
global_file = base / 'sentinel_paused'
instance_id = get_instance_id()

print(f'Instance: {instance_id or \"(no instance ID)\"}')
print()

# Check global first
if global_file.exists():
    try:
        data = json.loads(global_file.read_text())
        gap = int(time.time() - data.get('paused_at', time.time()))
        print(f'GLOBAL: OFF-RECORD (all instances paused {gap // 60}m ago)')
    except:
        print('GLOBAL: OFF-RECORD (pause file exists)')
else:
    print('GLOBAL: ON-RECORD')

# Check instance-specific
if instance_id:
    safe_id = instance_id.replace('/', '-').replace('%', '')
    instance_file = base / f'sentinel_paused_{safe_id}'
    if instance_file.exists():
        try:
            data = json.loads(instance_file.read_text())
            gap = int(time.time() - data.get('paused_at', time.time()))
            print(f'INSTANCE: OFF-RECORD (paused {gap // 60}m ago)')
        except:
            print('INSTANCE: OFF-RECORD (pause file exists)')
    else:
        print('INSTANCE: ON-RECORD')

# Summary
print()
if global_file.exists():
    print('=> Sentinel enforcement: PAUSED (global)')
elif instance_id:
    safe_id = instance_id.replace('/', '-').replace('%', '')
    if (base / f'sentinel_paused_{safe_id}').exists():
        print('=> Sentinel enforcement: PAUSED (this instance)')
    else:
        print('=> Sentinel enforcement: ACTIVE')
else:
    print('=> Sentinel enforcement: ACTIVE')
"
```
