# CASCADE Workflow API Reference

**Status:** Placeholder - needs expansion

## Overview

The CASCADE workflow defines the epistemic phases for AI self-assessment:

```
PREFLIGHT → CHECK → POSTFLIGHT
    │         │          │
 Baseline   Gate     Learning
```

## Core Functions

### preflight_submit()
Submit baseline epistemic assessment before work begins.

```python
from empirica.cli.command_handlers.workflow_commands import handle_preflight_submit_command
```

**Parameters:**
- `session_id` (str): Active session identifier
- `task_context` (str): Description of intended work
- `vectors` (dict): Epistemic vector assessments (know, uncertainty, context, engagement)
- `reasoning` (str): Explanation of current epistemic state

### check_submit()
Validate readiness to proceed with action (NOETIC → PRAXIC gate).

```python
from empirica.cli.command_handlers.workflow_commands import handle_check_submit_command
```

**Parameters:**
- `session_id` (str): Active session identifier
- `action_description` (str): What action is being considered
- `vectors` (dict): Current epistemic vectors
- `reasoning` (str): Why you believe you're ready (or not)

**Returns:**
- `decision`: "proceed" or "investigate"
- `metacog`: Gate status with bias-corrected vectors

### postflight_submit()
Record learning delta and create epistemic snapshot.

```python
from empirica.cli.command_handlers.workflow_commands import handle_postflight_submit_command
```

**Parameters:**
- `session_id` (str): Active session identifier
- `vectors` (dict): Final epistemic vectors
- `reasoning` (str): What was learned, what changed

**Side Effects:**
- Creates epistemic snapshot for session replay
- Updates Bayesian beliefs for calibration
- Syncs to Qdrant memory (if configured)

## CLI Commands

```bash
# PREFLIGHT
empirica preflight-submit --session-id <ID> --task-context "..." --vectors '{"know": 0.7}'

# CHECK
empirica check-submit --session-id <ID> --action "..." --vectors '{"know": 0.8}'

# POSTFLIGHT
empirica postflight-submit --session-id <ID> --vectors '{"know": 0.85}' --reasoning "..."
```

## See Also

- [NOETIC_PRAXIC_FRAMEWORK.md](../../architecture/NOETIC_PRAXIC_FRAMEWORK.md)
- [SENTINEL_ARCHITECTURE.md](../../architecture/SENTINEL_ARCHITECTURE.md)
