# Decision Logging Implementation Guide

**Version:** 1.0  
**Date:** 2025-11-07  
**Purpose:** Practical guide for implementing structured decision logging with DB integration  
**Audience:** AI agents, developers

---

## Overview

This guide shows how to implement privacy-preserving decision logging that integrates with Empirica's existing infrastructure:
- SQLite session database
- Reflex logs (temporal separation)
- JSON exports
- Tmux monitoring

**Goal:** Capture "why" decisions were made with epistemic context, enabling reliable memory across compression cycles.

---

## Quick Start: Log a Decision

### Via Python API

```python
from empirica.data.session_database import SessionDatabase
from datetime import datetime
import json

# Initialize DB
db = SessionDatabase(db_path=".empirica/sessions/sessions.db")

# Create decision entry
decision = {
    "decision_id": "decision_20251107_jwt_rotation",
    "timestamp": datetime.utcnow().isoformat(),
    "decision": "Rotate JWT secret immediately",
    
    # Epistemic state (from PREFLIGHT or CHECK assessment)
    "epistemic_state": {
        "KNOW": 0.85,
        "CONTEXT": 0.70,
        "UNCERTAINTY": 0.15,
        "overall_confidence": 0.80
    },
    
    # Reasoning (abstracted, no sensitive data)
    "rationale": "JWT found in logs, logs unencrypted for 30d retention",
    "alternatives_considered": [
        {"option": "Wait for next release", "rejected_why": "Security risk too high"},
        {"option": "Rotate + encrypt logs", "rejected_why": "Encryption adds complexity"}
    ],
    
    # Caveats and validation
    "caveats": [
        "Assumption: logs retained 30d (unvalidated)",
        "May cause brief service disruption"
    ],
    "validation_criteria": [
        "New secret deployed successfully",
        "No authentication errors in monitoring",
        "Old tokens invalidated"
    ],
    
    # Reliability metrics
    "reasoning_quality": 0.92,
    "reasoning_fidelity": 0.94,
    "should_refresh_if": "Calibration drops below 0.70"
}

# Store in cascade metadata
cascade_id = f"decision_{decision['decision_id']}"
db.create_cascade(
    cascade_id=cascade_id,
    session_id=session_id,
    task=f"Decision: {decision['decision']}",
    started_at=datetime.utcnow()
)

db.conn.execute("""
    INSERT INTO cascade_metadata (cascade_id, metadata_key, metadata_value)
    VALUES (?, ?, ?)
""", (cascade_id, "decision_log", json.dumps(decision)))

db.conn.commit()
print(f"✅ Decision logged: {decision['decision_id']}")
```

### Via MCP Tools

```python
# In Claude Desktop or MCP client
execute_postflight(
    session_id="<uuid>",
    task_summary="Decided to rotate JWT secret immediately"
)

submit_postflight_assessment(
    session_id="<uuid>",
    vectors={
        "KNOW": 0.85,
        "CONTEXT": 0.70,
        "UNCERTAINTY": 0.15,
        # ... other vectors
    },
    changes_noticed="Confidence increased after investigating JWT security best practices"
)

# Decision automatically logged with epistemic context
```

---

## Decision Log Structure

### Minimal Decision (Quick Logging)

```python
{
    "decision": "Use SQLite for session tracking",
    "epistemic_confidence": 0.75,
    "rationale": "Lightweight, no external deps, queryable",
    "timestamp": "2025-11-07T10:30:00Z"
}
```

### Full Decision (Comprehensive Logging)

```python
{
    # Identity
    "decision_id": "decision_20251107_sqlite_choice",
    "timestamp": "2025-11-07T10:30:00Z",
    "session_id": "<uuid>",
    "cascade_id": "cascade_abc123",
    
    # Decision
    "decision": "Use SQLite for session tracking",
    "category": "architecture",  # architecture | implementation | security | performance
    
    # Epistemic state (from assessment)
    "epistemic_state": {
        "KNOW": 0.80,
        "DO": 0.75,
        "CONTEXT": 0.70,
        "CLARITY": 0.85,
        "COHERENCE": 0.80,
        "SIGNAL": 0.75,
        "DENSITY": 0.70,
        "STATE": 0.75,
        "CHANGE": 0.60,
        "COMPLETION": 0.70,
        "IMPACT": 0.65,
        "ENGAGEMENT": 0.80,
        "UNCERTAINTY": 0.20,
        "overall_confidence": 0.75
    },
    
    # Reasoning (privacy-preserving)
    "rationale": "Lightweight, no external deps, queryable, sufficient for current scale",
    "alternatives_considered": [
        {
            "option": "PostgreSQL",
            "pros": ["More scalable", "Better concurrency"],
            "cons": ["External dependency", "Overkill for current needs"],
            "rejected_why": "Unnecessary complexity for current scale"
        },
        {
            "option": "JSON files only",
            "pros": ["Simple", "No DB dependency"],
            "cons": ["Not queryable", "Hard to analyze"],
            "rejected_why": "Need structured queries for calibration analysis"
        }
    ],
    
    # Quality metrics
    "reasoning_quality": 0.85,
    "reasoning_fidelity": 0.90,
    "evidence_strength": 0.80,
    "assumption_risk": 0.15,
    
    # Caveats and validation
    "caveats": [
        "May need migration to Postgres if >10k sessions/day",
        "Concurrent writes limited by SQLite"
    ],
    "assumptions": [
        {"assumption": "Session volume < 1k/day", "validated": false},
        {"assumption": "Single-process access", "validated": true}
    ],
    "validation_criteria": [
        "Query performance < 100ms for recent sessions",
        "No write conflicts in production",
        "Storage < 100MB for 1000 sessions"
    ],
    
    # Degradation tracking
    "time_since_decision": 0,  # Updated on query
    "context_switches_since": 0,  # Updated on query
    "estimated_fidelity": 0.90,  # Degrades over time
    "should_refresh": false,  # True if fidelity < 0.75
    
    # Status
    "status": "implemented",  # proposed | implemented | validated | deprecated
    "last_validated": null,
    "deprecated_reason": null
}
```

---

## Integration with Existing Systems

### 1. Store in Session Database

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()

# Option A: Store as cascade metadata (recommended)
db.conn.execute("""
    INSERT INTO cascade_metadata (cascade_id, metadata_key, metadata_value)
    VALUES (?, 'decision_log', ?)
""", (cascade_id, json.dumps(decision)))

# Option B: Create dedicated decisions table (future enhancement)
# db.conn.execute("""
#     CREATE TABLE IF NOT EXISTS decisions (
#         decision_id TEXT PRIMARY KEY,
#         session_id TEXT,
#         cascade_id TEXT,
#         timestamp TEXT,
#         decision TEXT,
#         epistemic_state TEXT,
#         rationale TEXT,
#         reasoning_quality REAL,
#         status TEXT,
#         FOREIGN KEY (session_id) REFERENCES sessions(session_id)
#     )
# """)
```

### 2. Write to Reflex Logs

```python
from canonical.reflex_logger import ReflexLogger

logger = ReflexLogger()

# Log decision as reflex frame
decision_frame = {
    "phase": "decision",
    "decision_id": decision["decision_id"],
    "decision": decision["decision"],
    "epistemic_state": decision["epistemic_state"],
    "rationale": decision["rationale"],
    "timestamp": datetime.utcnow().isoformat()
}

logger.log_frame(
    ai_id="claude",
    frame_type="decision",
    frame_data=decision_frame
)
```

### 3. Export to JSON

```python
from empirica.data.session_json_handler import SessionJSONHandler

json_handler = SessionJSONHandler()

# Export decision as part of session summary
json_handler.write_decision(
    session_id=session_id,
    decision=decision
)
```

### 4. Display in Tmux (Optional)

```python
# If tmux available, update decision pane
import subprocess

decision_summary = f"""
DECISION: {decision['decision']}
Confidence: {decision['epistemic_state']['overall_confidence']:.2f}
Rationale: {decision['rationale'][:50]}...
"""

try:
    subprocess.run([
        'tmux', 'send-keys', '-t', 'empirica:decision',
        f'echo "{decision_summary}"', 'Enter'
    ], check=False)
except:
    pass  # Tmux not available, skip
```

---

## Querying Decisions

### Get Recent Decisions

```python
from empirica.data.session_database import SessionDatabase
import json

db = SessionDatabase()

# Query recent decisions
cursor = db.conn.execute("""
    SELECT cm.metadata_value, c.started_at
    FROM cascade_metadata cm
    JOIN cascades c ON cm.cascade_id = c.cascade_id
    WHERE cm.metadata_key = 'decision_log'
    ORDER BY c.started_at DESC
    LIMIT 10
""")

decisions = []
for row in cursor.fetchall():
    decision = json.loads(row[0])
    decision['logged_at'] = row[1]
    decisions.append(decision)

print(f"Found {len(decisions)} recent decisions")
for d in decisions:
    print(f"  - {d['decision']} (confidence: {d['epistemic_state']['overall_confidence']:.2f})")
```

### Check Decision Reliability

```python
def check_decision_reliability(decision_id: str) -> dict:
    """Check if decision needs refresh based on degradation"""
    
    db = SessionDatabase()
    
    # Get decision
    cursor = db.conn.execute("""
        SELECT cm.metadata_value, c.started_at
        FROM cascade_metadata cm
        JOIN cascades c ON cm.cascade_id = c.cascade_id
        WHERE cm.metadata_key = 'decision_log'
        AND cm.metadata_value LIKE ?
    """, (f'%{decision_id}%',))
    
    row = cursor.fetchone()
    if not row:
        return {"error": "Decision not found"}
    
    decision = json.loads(row[0])
    decision_time = datetime.fromisoformat(row[1])
    
    # Calculate degradation
    time_elapsed = datetime.utcnow() - decision_time
    hours_elapsed = time_elapsed.total_seconds() / 3600
    
    # Estimate fidelity degradation (3% per context switch, ~1 switch per hour)
    estimated_switches = int(hours_elapsed)
    degradation = 0.03 * estimated_switches
    current_fidelity = max(0.0, decision['reasoning_fidelity'] - degradation)
    
    # Calculate reliability
    reliability = (
        decision['epistemic_state']['overall_confidence'] * 0.4 +
        decision['reasoning_quality'] * 0.3 +
        current_fidelity * 0.3
    )
    
    should_refresh = (
        reliability < 0.75 or
        hours_elapsed > 4 or
        estimated_switches > 10
    )
    
    return {
        "decision_id": decision_id,
        "decision": decision['decision'],
        "original_confidence": decision['epistemic_state']['overall_confidence'],
        "reasoning_quality": decision['reasoning_quality'],
        "original_fidelity": decision['reasoning_fidelity'],
        "current_fidelity": current_fidelity,
        "reliability": reliability,
        "hours_elapsed": hours_elapsed,
        "estimated_switches": estimated_switches,
        "should_refresh": should_refresh,
        "recommendation": "Re-validate decision" if should_refresh else "Decision still reliable"
    }
```

---

## Best Practices

### 1. Log Decisions at Key Points

**When to log:**
- ✅ After major architectural decisions
- ✅ After resolving complex bugs (decision on fix approach)
- ✅ After discovering critical insights
- ✅ Before context switches (checkpoint current state)
- ✅ When epistemic state changes significantly

**When NOT to log:**
- ❌ Trivial decisions (variable names, formatting)
- ❌ Obvious choices (use standard library vs reinvent)
- ❌ Decisions with no alternatives

### 2. Keep Rationale Privacy-Preserving

**Good (abstracted):**
```python
"rationale": "API security risk detected, rotation needed"
```

**Bad (sensitive data):**
```python
"rationale": "JWT secret 'sk_live_abc123xyz' found in logs at line 42 of auth.py"
```

### 3. Link to Reasoning Chains

```python
decision = {
    "decision": "Rotate JWT secret",
    "reasoning_ref": "sha256:abc123...",  # Reference to reflex log
    "cascade_id": "cascade_xyz789",  # Link to full cascade
    "epistemic_state": {...}  # Snapshot at decision time
}
```

### 4. Update Decision Status

```python
# After validation
db.conn.execute("""
    UPDATE cascade_metadata
    SET metadata_value = json_set(metadata_value, '$.status', 'validated')
    WHERE metadata_key = 'decision_log'
    AND metadata_value LIKE ?
""", (f'%{decision_id}%',))
```

---

## See Also

- **`MEMORY_COMPRESSION.md`** - Memory compression strategy
- **`DECISIONS.md`** - Example decision log
- **`EMPIRICA_SYSTEM_OVERVIEW.md`** - Complete system architecture
- **`docs/production/18_MONITORING_LOGGING.md`** - 3-format logging system

---

**Last Updated:** 2025-11-07  
**Status:** ✅ Implementation guide complete  
**Integration:** ✅ DB + Reflex logs + JSON + Tmux

