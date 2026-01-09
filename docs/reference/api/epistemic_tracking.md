# Epistemic Tracking API Reference

**Status:** Placeholder - needs expansion

## Overview

Epistemic tracking captures and persists AI self-assessment data across sessions.

## Core Components

### EpistemicStateSnapshot

Universal cross-AI context transfer protocol.

```python
from empirica.data.epistemic_snapshot import EpistemicStateSnapshot, ContextSummary
```

**Key Attributes:**
- `snapshot_id` (str): Unique identifier
- `session_id` (str): Parent session
- `vectors` (dict): 13-dimensional epistemic state
- `delta` (dict): Changes from previous snapshot
- `context_summary` (ContextSummary): Semantic + narrative context
- `compression_ratio` (float): Token reduction achieved
- `fidelity_score` (float): How well snapshot represents full context

### EpistemicSnapshotProvider

Creates and persists epistemic snapshots.

```python
from empirica.data.snapshot_provider import EpistemicSnapshotProvider

provider = EpistemicSnapshotProvider()
snapshot = provider.create_snapshot_from_session(
    session_id="...",
    context_summary=ContextSummary(...),
    cascade_phase="POSTFLIGHT"
)
provider.save_snapshot(snapshot)
```

### Bayesian Beliefs

Calibration tracking for epistemic vectors.

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
beliefs = db.get_bayesian_beliefs(ai_id="claude-code")
# Returns calibration adjustments per vector
```

## 13 Epistemic Vectors

| Vector | Category | Description |
|--------|----------|-------------|
| KNOW | Foundation | What you know |
| DO | Foundation | What you can do |
| CONTEXT | Foundation | Understanding of current state |
| CLARITY | Comprehension | How clear is understanding |
| COHERENCE | Comprehension | Internal consistency |
| SIGNAL | Comprehension | Strength of evidence |
| DENSITY | Comprehension | Information richness |
| STATE | Execution | Current progress state |
| CHANGE | Execution | What changed |
| COMPLETION | Execution | How complete is work |
| IMPACT | Execution | Effect of actions |
| ENGAGEMENT | Gate | Readiness to proceed |
| UNCERTAINTY | Meta | Confidence bounds |

## CLI Commands

```bash
# View epistemic state
empirica epistemics-show --session-id <ID>

# List all epistemic assessments
empirica epistemics-list --session-id <ID>
```

## See Also

- [EPISTEMIC_BUS.md](../../architecture/EPISTEMIC_BUS.md)
- [SELF_MONITORING.md](../../architecture/SELF_MONITORING.md)
