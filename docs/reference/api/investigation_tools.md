# Investigation Tools API Reference

**Status:** Placeholder - needs expansion

## Overview

Investigation tools support the NOETIC phase - exploring, hypothesizing, and gathering evidence before action.

## Core Commands

### investigate

Launch investigation with optional branching.

```bash
empirica investigate --session-id <ID> --question "How does X work?"
```

**Parameters:**
- `--session-id`: Active session
- `--question`: Investigation focus
- `--depth`: How deep to investigate (shallow/medium/deep)
- `--create-branch`: Create git branch for investigation

### investigate-create-branch

Create isolated branch for exploratory work.

```bash
empirica investigate-create-branch --session-id <ID> --name "explore-auth"
```

### investigate-checkpoint-branch

Save investigation state as checkpoint.

```bash
empirica investigate-checkpoint-branch --session-id <ID> --message "Found auth flow"
```

### investigate-merge-branches

Merge investigation findings back to main.

```bash
empirica investigate-merge-branches --session-id <ID> --branch "explore-auth"
```

## Agent Spawning

Spawn specialized investigation agents.

```bash
empirica agent-spawn --session-id <ID> --task "Research authentication patterns" --persona researcher
```

**Available Personas:**
- `researcher` - Deep investigation
- `critic` - Challenge assumptions
- `synthesizer` - Combine findings

## Logging Investigation Results

### Finding Log

```bash
empirica finding-log --session-id <ID> --finding "Discovered X" --impact 0.8
```

### Unknown Log

```bash
empirica unknown-log --session-id <ID> --unknown "Need to understand Y"
```

### Dead End Log

```bash
empirica deadend-log --session-id <ID> --approach "Tried Z" --why-failed "Because..."
```

## Python API

```python
from empirica.cli.command_handlers.workflow_commands import (
    handle_investigate_command,
    handle_finding_log_command,
    handle_unknown_log_command
)
```

## See Also

- [NOETIC_PRAXIC_FRAMEWORK.md](../../architecture/NOETIC_PRAXIC_FRAMEWORK.md)
- [HANDOFF_SYSTEM.md](../../architecture/HANDOFF_SYSTEM.md)
