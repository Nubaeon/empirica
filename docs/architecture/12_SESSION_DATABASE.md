# 12. Session Database & Reflex Logs

**Empirica v4.0 - Unified Storage Architecture**

**Storage Architecture:** See `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`  

---

## Overview

Empirica uses **3-layer atomic storage architecture** for epistemic tracking:

1. **Session Database (SQLite)** - Primary storage, queryable structured data
2. **Git Notes** - Compressed checkpoints (~97.5% token reduction)
3. **Reflex Logs (JSON)** - Full audit trail, temporal separation

**Why three?** Each layer serves a distinct purpose with complementary strengths. All three write atomically.

---

## The Dual Storage Model

### Session Database (SQLite)

**Location:** `.empirica/sessions/sessions.db`

**Purpose:**
- Structured queryable data
- Session continuity
- Calibration analytics
- Performance metrics
- Cascade history

**Key Features:**
- SQL queries for analysis
- Referential integrity
- Efficient joins
- Production-ready
- Cross-session queries

### Reflex Logs (JSON)

**Location:** `.empirica_reflex_logs/`

**Purpose:**
- **Temporal separation** - prevent prompt pollution
- Audit trail for genuine assessments
- Learning delta validation
- Epistemic history preservation

**Key Features:**
- Immutable epistemic trail
- No prompt contamination
- Human-readable JSON
- Chronological ordering
- Privacy-preserving

---

## Getting Started

### Auto-Initialization

**The database automatically initializes on first use.** No manual setup required!

```python
from empirica.data.session_database import SessionDatabase

# This creates the database and all tables automatically
db = SessionDatabase()
# ✅ Database created at: .empirica/sessions/sessions.db
# ✅ All tables initialized (including unified reflexes table)
# ✅ Ready to use immediately
```

**What happens on first run:**
1. Creates `.empirica/sessions/` directory
2. Creates `sessions.db` SQLite file
3. Initializes all tables with proper schema
4. Migrates any old table data to unified `reflexes` table
5. Returns ready-to-use database connection

**For production systems:**
```python
# Custom path (optional)
db = SessionDatabase(db_path="/var/empirica/data/sessions.db")

# Default path (recommended)
db = SessionDatabase()  # Uses .empirica/sessions/sessions.db
```

**No migration needed:** Database schema is created on first use, not during package installation.

---

## Internal Architecture (v4.1+)

### Repository Pattern

**As of v4.1, SessionDatabase uses a modular repository pattern internally:**

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()

# Standard usage (recommended) - facade pattern
goal_id = db.create_goal(session_id, "My goal")
project_id = db.create_project("My project")
finding_id = db.log_finding(project_id, session_id, "Learned X")

# Direct repository access (advanced) - for contributors
goal_id = db.goals.create_goal(session_id, "My goal")
project_id = db.projects.create_project("My project")
finding_id = db.breadcrumbs.log_finding(project_id, session_id, "Learned X")
```

**Internal repositories:**
- **`db.goals`** - GoalRepository (8 methods: goal/subtask CRUD)
- **`db.branches`** - BranchRepository (4 methods: investigation branching)
- **`db.breadcrumbs`** - BreadcrumbRepository (10 methods: findings/unknowns/mistakes)
- **`db.projects`** - ProjectRepository (7 methods: project operations)

**Design:**
- **Composition over inheritance** - All repositories share single SQLite connection
- **Facade pattern** - SessionDatabase delegates to repositories transparently
- **Zero breaking changes** - All existing code continues to work unchanged
- **Transactional consistency** - Shared connection ensures atomic operations

**For users:** Use the standard `db.method()` pattern. Repository details are internal implementation.

**For contributors:** See `empirica/data/repositories/` for domain-specific implementations.

---

## Why Temporal Separation Matters

**The Problem:**
Without temporal separation, reflex frames in context → prompt pollution → confabulated self-assessment.

**The Solution:**
```
Assessment Cycle:
1. AI genuinely assesses → creates reflex frame
2. Frame logged to JSON (OUTSIDE prompt context)
3. Database records structured data
4. Next assessment: clean context, no pollution

Result: Genuine epistemic measurement, not pattern matching
```

**Critical Principle:**
> Epistemic weights ≠ internal weights. We measure knowledge state, we don't modify model parameters.

---

## Session Database Schema

### Core Tables Overview

**Epistemic Data (Unified):**
1. **reflexes** - 🆕 Unified epistemic vectors (PREFLIGHT, CHECK, POSTFLIGHT)

**Session Management:**
2. **sessions** - Session metadata
3. **cascades** - Cascade executions

**Investigation & Decision Quality (v4.0):**
4. **goals** - 🆕 Goal tracking with scope vectors
5. **subtasks** - 🆕 Investigation tracking (findings/unknowns/dead_ends)

**Tracking & Analysis:**
6. **divergence_tracking** - Calibration tracking
7. **drift_monitoring** - Behavioral integrity
8. **bayesian_beliefs** - Evidence-based belief tracking
9. **investigation_tools** - Tool usage
10. **cascade_metadata** - Cascade key-value data
11. **epistemic_snapshots** - Point-in-time states

**Migration Note:** The old tables (`epistemic_assessments`, `preflight_assessments`, 
`check_phase_assessments`, `postflight_assessments`) have been unified into the `reflexes` 
table. Data migration happens automatically on first database access.

---

### Table 1: sessions

**Purpose:** Track AI sessions from bootstrap to completion

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    ai_id TEXT NOT NULL,
    user_id TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    bootstrap_level INTEGER,  -- Legacy, no behavioral effect in v4.0
    components_loaded INTEGER,
    status TEXT,  -- 'active', 'completed', 'aborted'
    total_cascades INTEGER DEFAULT 0,
    total_investigations INTEGER DEFAULT 0,
    session_metadata JSON
);
```

**Use Cases:**
- Resume previous sessions
- Track AI agent activity
- Session analytics
- Handoff between AIs

---

### Table 2: reflexes (UNIFIED v4.0) ✅

**Purpose:** Unified storage for all CASCADE phases (PREFLIGHT, CHECK, POSTFLIGHT)

```sql
CREATE TABLE reflexes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    phase TEXT NOT NULL,  -- 'PREFLIGHT', 'CHECK', 'POSTFLIGHT'
    round INTEGER DEFAULT 1,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 13 epistemic vectors (all REAL 0.0-1.0)
    engagement REAL,
    know REAL,
    do REAL,
    context REAL,
    clarity REAL,
    coherence REAL,
    signal REAL,
    density REAL,
    state REAL,
    change REAL,
    completion REAL,
    impact REAL,
    uncertainty REAL,
    
    -- Metadata
    reflex_data TEXT,  -- JSON with phase-specific data
    reasoning TEXT,
    evidence TEXT,
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**Key Features:**
- ✅ **Single table** for all CASCADE phases (no more scattered tables)
- ✅ **13 canonical vectors** consistently stored
- ✅ **Phase filtering** via WHERE clause
- ✅ **Round tracking** for multiple CHECK cycles
- ✅ **Automatic migration** from old tables

**Replaces deprecated tables:**
- `epistemic_assessments` ❌ (migrated to reflexes)
- `preflight_assessments` ❌ (migrated to reflexes)
- `postflight_assessments` ❌ (migrated to reflexes)
- `check_phase_assessments` ❌ (migrated to reflexes)

---

### Table 3: cascades

**Purpose:** Track each CASCADE execution workflow (metadata only, not epistemic data)

```sql
CREATE TABLE cascades (
    cascade_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    task TEXT NOT NULL,
    context JSON,

    final_action TEXT,  -- 'proceed', 'investigate', 'clarify', 'reset', 'stop'
    final_confidence REAL,
    investigation_rounds INTEGER DEFAULT 0,
    duration_ms INTEGER,

    -- Feature flags
    engagement_gate_passed BOOLEAN,
    bayesian_active BOOLEAN,
    drift_monitored BOOLEAN,

    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**Tracks:**
- Cascade lifecycle
- Investigation iterations
- Decision outcomes
- Feature usage

---

### Table 3: reflexes 🆕

**Purpose:** Unified storage for all epistemic vectors across CASCADE phases

```sql
CREATE TABLE reflexes (
    reflex_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    cascade_id TEXT,
    
    -- Phase tracking
    phase TEXT NOT NULL,  -- 'PREFLIGHT', 'CHECK', 'POSTFLIGHT'
    round INTEGER DEFAULT 1,  -- For multiple CHECKs
    timestamp REAL NOT NULL,
    
    -- 13 Epistemic Vectors (0.0 - 1.0)
    -- GATE
    engagement REAL,
    
    -- FOUNDATION (35%)
    know REAL,
    do REAL,
    context REAL,
    
    -- COMPREHENSION (25%)
    clarity REAL,
    coherence REAL,
    signal REAL,
    density REAL,
    
    -- EXECUTION (25%)
    state REAL,
    change REAL,
    completion REAL,
    impact REAL,
    
    -- META (explicit uncertainty)
    uncertainty REAL,
    
    -- Additional data
    reflex_data TEXT,  -- JSON metadata (phase-specific)
    reasoning TEXT,    -- Natural language notes
    evidence TEXT,     -- Supporting evidence
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
);
```

**Key Features:**
- ✅ **Unified storage** - All phases in one table
- ✅ **Phase filtering** - Query by PREFLIGHT, CHECK, POSTFLIGHT
- ✅ **Round tracking** - Multiple CHECK phases per cascade
- ✅ **Metadata storage** - JSON field for phase-specific data
- ✅ **Automatic migration** - Old data migrated transparently

**Query Examples:**

```python
# Get latest PREFLIGHT vectors
db.get_latest_vectors(session_id, phase="PREFLIGHT")

# Get all CHECK phases
db.get_vectors_by_phase(session_id, phase="CHECK")

# Get POSTFLIGHT
db.get_latest_vectors(session_id, phase="POSTFLIGHT")

# Raw SQL query by phase
cursor.execute("""
    SELECT * FROM reflexes 
    WHERE session_id = ? AND phase = 'PREFLIGHT'
    ORDER BY timestamp DESC LIMIT 1
""", (session_id,))
```

**Phase-Specific Metadata (stored in reflex_data JSON):**

**PREFLIGHT:**
```json
{
  "prompt_summary": "Implement user authentication",
  "uncertainty_notes": "Unclear about JWT vs session tokens"
}
```

**CHECK:**
```json
{
  "decision": "investigate",
  "confidence": 0.75,
  "gaps_identified": ["Token refresh mechanism unclear"],
  "next_investigation_targets": ["Research JWT refresh tokens"],
  "findings": ["Found auth.py handles login", "JWT library installed"],
  "remaining_unknowns": ["Token expiration handling"]
}
```

**POSTFLIGHT:**
```json
{
  "task_summary": "Implemented JWT authentication with refresh",
  "postflight_confidence": 0.9,
  "calibration_accuracy": "well-calibrated"
}
```

---

### Table 4: goals 🆕

**Purpose:** Track investigation goals with scope assessment (v4.0)

```sql
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    objective TEXT NOT NULL,
    scope TEXT NOT NULL,              -- JSON: {breadth, duration, coordination}
    estimated_complexity REAL,
    created_timestamp REAL NOT NULL,
    completed_timestamp REAL,
    is_completed BOOLEAN DEFAULT 0,
    goal_data TEXT NOT NULL,          -- JSON: additional metadata
    status TEXT DEFAULT 'in_progress', -- 'in_progress' | 'complete' | 'blocked'
    
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**Note:** Scope is stored as JSON for flexibility. Individual vectors (breadth, duration, coordination) are packed into the `scope` field.

**Purpose:** Goals enable **decision quality, continuity, and audit trails** for complex investigations.

**When to Use:**
- High uncertainty investigations
- Multi-session work requiring handoff
- CHECK phase decision-making support

**Scope Vectors Explained:**

| Vector | 0.0 | 0.5 | 1.0 |
|--------|-----|-----|-----|
| **breadth** | Single file | Few modules | Entire codebase |
| **duration** | Minutes | Hours | Months |
| **coordination** | Solo work | Some coordination | Heavy multi-agent |

**Example Usage:**

```python
# Create goal with scope assessment
goal_id = db.create_goal(
    session_id=session_id,
    objective="Understand OAuth2 authentication flow",
    scope_breadth=0.6,      # Touches auth/, api/, config/
    scope_duration=0.4,     # Few hours
    scope_coordination=0.3  # Mostly solo, some docs
)
# Note: Method packs scope_breadth/duration/coordination into JSON 'scope' field

# Query goals for session
cursor.execute("""
    SELECT id, objective, scope, status FROM goals 
    WHERE session_id = ? AND status = 'in_progress'
""", (session_id,))

# Parse scope JSON
for row in cursor.fetchall():
    goal_id, objective, scope_json, status = row
    scope = json.loads(scope_json)
    print(f"Breadth: {scope['breadth']}, Duration: {scope['duration']}")
```

---

### Table 5: subtasks 🆕

**Purpose:** Track investigation progress with findings/unknowns/dead_ends (v4.0)

```sql
CREATE TABLE subtasks (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'in_progress' | 'completed'
    epistemic_importance TEXT NOT NULL DEFAULT 'medium',  -- 'critical' | 'high' | 'medium' | 'low'
    estimated_tokens INTEGER,
    actual_tokens INTEGER,
    completion_evidence TEXT,
    notes TEXT,
    created_timestamp REAL NOT NULL,
    completed_timestamp REAL,
    subtask_data TEXT NOT NULL,  -- JSON: {findings: [], unknowns: [], dead_ends: []}
    
    FOREIGN KEY (goal_id) REFERENCES goals(id)
);
```

**Note:** Investigation tracking (findings, unknowns, dead_ends) is stored as JSON in the `subtask_data` field.

**Investigation Tracking Fields:**

1. **findings** - What you discovered
   - Example: `["Auth endpoint: /oauth/authorize", "PKCE required"]`
   - Used for: Documentation, handoff, implementation reference

2. **unknowns** - What remains unclear (for CHECK decisions)
   - Example: `["Token expiration times?", "MFA impact on refresh?"]`
   - Used for: CHECK phase decision-making via `query_unknowns_summary()`

3. **dead_ends** - Paths explored but blocked
   - Example: `["JWT extension blocked by security policy"]`
   - Used for: Avoiding duplicate work, audit trail

**Example Usage:**

```python
# Create subtask (creates subtask_data JSON with empty arrays)
subtask_id = db.create_subtask(
    goal_id=goal_id,
    description="Map OAuth2 endpoints and flow",
    importance='high'
)

# Log discoveries (updates subtask_data JSON)
db.update_subtask_findings(subtask_id, [
    "Auth endpoint: /oauth/authorize",
    "Token endpoint: /oauth/token",
    "PKCE required"
])

# Log remaining questions (for CHECK - updates subtask_data JSON)
db.update_subtask_unknowns(subtask_id, [
    "Token expiration times not documented",
    "MFA impact on refresh unclear"
])

# Log blocked paths (updates subtask_data JSON)
db.update_subtask_dead_ends(subtask_id, [
    "Tried JWT - blocked by security policy"
])

# Query subtask data
cursor.execute("SELECT id, subtask_data FROM subtasks WHERE id = ?", (subtask_id,))
row = cursor.fetchone()
subtask_data = json.loads(row[1])
print(f"Findings: {subtask_data['findings']}")
print(f"Unknowns: {subtask_data['unknowns']}")

# Query for CHECK decision
unknowns = db.query_unknowns_summary(session_id)
print(f"Total unknowns: {unknowns['total_unknowns']}")
# Decision: If unknowns are blockers → investigate more
#           If unknowns are low-impact → proceed
```

**Get Complete Goal Tree:**

```python
# Get all goals with nested subtasks
goal_tree = db.get_goal_tree(session_id)

# Returns:
[
    {
        'goal_id': 'uuid',
        'objective': 'Understand OAuth2 flow',
        'status': 'in_progress',
        'scope_breadth': 0.6,
        'scope_duration': 0.4,
        'scope_coordination': 0.3,
        'subtasks': [
            {
                'subtask_id': 'uuid',
                'description': 'Map endpoints',
                'importance': 'high',
                'status': 'complete',
                'findings': [...],
                'unknowns': [...],
                'dead_ends': [...]
            }
        ]
    }
]
```

**Integration with CHECK Phase:**

```sql
-- Query unknowns for CHECK decision
SELECT 
    g.objective,
    COUNT(CASE WHEN s.unknowns != '[]' THEN 1 END) as unknown_count
FROM goals g
LEFT JOIN subtasks s ON g.goal_id = s.goal_id
WHERE g.session_id = ? AND g.status = 'in_progress'
GROUP BY g.goal_id;
```

**Use Cases:**
- **Decision Quality:** CHECK queries unknowns to inform readiness
- **Continuity:** Next AI sees findings/unknowns/dead_ends
- **Audit Trail:** Complete investigation path visible

---

### ~~Table 6: preflight_assessments~~ (DEPRECATED)

**⚠️ DEPRECATED:** This table has been replaced by `reflexes` (phase='PREFLIGHT').

**Migration:** Data automatically migrated to `reflexes` on first database access.

**Old Purpose:** Pre-task epistemic state

```sql
CREATE TABLE preflight_assessments (
    preflight_id TEXT PRIMARY KEY,
    cascade_id TEXT NOT NULL,
    assessment_id TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,

    predicted_confidence REAL,
    predicted_investigation_need BOOLEAN,

    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id),
    FOREIGN KEY (assessment_id) REFERENCES epistemic_assessments(assessment_id)
);
```

---

### ~~Table 5: postflight_assessments~~ (DEPRECATED)

**⚠️ DEPRECATED:** This table has been replaced by `reflexes` (phase='POSTFLIGHT').

**Migration:** Data automatically migrated to `reflexes` on first database access.

**Old Purpose:** Post-task reassessment + calibration

---

### ~~Table 6: check_phase_assessments~~ (DEPRECATED)

**⚠️ DEPRECATED:** This table has been replaced by `reflexes` (phase='CHECK').

**Migration:** Data automatically migrated to `reflexes` on first database access.

**Old Purpose:** Mid-task confidence checks

---

### Table 7: bayesian_beliefs

**Purpose:** Evidence-based belief tracking

```sql
CREATE TABLE bayesian_beliefs (
    belief_id TEXT PRIMARY KEY,
    cascade_id TEXT NOT NULL,
    context_key TEXT NOT NULL,
    vector_name TEXT NOT NULL,

    belief_mean REAL,
    belief_variance REAL,

    evidence_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP,

    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
);
```

**Tracks:**
- Evidence accumulation
- Belief updates
- Variance reduction
- Discrepancy detection

---

### Table 7: drift_monitoring

**Purpose:** Behavioral integrity tracking

```sql
CREATE TABLE drift_monitoring (
    drift_id TEXT PRIMARY KEY,
    cascade_id TEXT NOT NULL,
    monitored_at TIMESTAMP NOT NULL,

    synthesis_history JSON,

    sycophancy_drift_detected BOOLEAN,
    sycophancy_severity REAL,

    tension_avoidance_detected BOOLEAN,
    acknowledgment_rate REAL,

    recommendation TEXT,

    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
);
```

---

### Table 8: investigation_tools

**Purpose:** Track investigation tool usage

```sql
CREATE TABLE investigation_tools (
    tool_usage_id TEXT PRIMARY KEY,
    cascade_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    executed_at TIMESTAMP NOT NULL,

    success BOOLEAN,
    vector_addressed TEXT,
    confidence_gain REAL,

    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
);
```

---

## Reflex Frame Format

### JSON Structure

```json
{
  "frame_id": "reflex_20251109_143022_abc123",
  "timestamp": "2025-11-09T14:30:22.123456",
  "session_id": "session_xyz",
  "cascade_id": "cascade_001",
  "phase": "uncertainty",

  "assessment": {
    "engagement": {
      "score": 0.85,
      "rationale": "Clear task, good collaboration potential",
      "evidence": null
    },
    "know": {
      "score": 0.65,
      "rationale": "Moderate knowledge of authentication patterns",
      "evidence": "Familiar with OAuth2, limited JWT experience"
    },
    "do": {
      "score": 0.75,
      "rationale": "Can execute code review and suggest fixes",
      "evidence": null
    },
    "context": {
      "score": 0.55,
      "rationale": "Need to see codebase structure first",
      "evidence": "No prior knowledge of this specific implementation"
    },
    "clarity": {
      "score": 0.80,
      "rationale": "Task is well-defined and specific",
      "evidence": null
    },
    "coherence": {
      "score": 0.90,
      "rationale": "Request is logically coherent",
      "evidence": null
    },
    "signal": {
      "score": 0.70,
      "rationale": "Clear signal, minimal noise in requirements",
      "evidence": null
    },
    "density": {
      "score": 0.45,
      "rationale": "Appropriate complexity, not overwhelming",
      "evidence": null
    },
    "state": {
      "score": 0.60,
      "rationale": "Partial understanding of current state",
      "evidence": null
    },
    "change": {
      "score": 0.70,
      "rationale": "Can track changes effectively",
      "evidence": null
    },
    "completion": {
      "score": 0.65,
      "rationale": "Clear path to completion visible",
      "evidence": null
    },
    "impact": {
      "score": 0.70,
      "rationale": "Can predict consequences of changes",
      "evidence": null
    },
    "uncertainty": {
      "score": 0.45,
      "rationale": "Moderate uncertainty, investigation recommended",
      "evidence": null
    }
  },

  "overall_confidence": 0.68,
  "recommended_action": "investigate",
  "engagement_gate_passed": true,

  "metadata": {
    "task": "Review authentication module for security issues",
    "context_keys": ["security_review", "code_analysis"]
  }
}
```

### Filename Convention

```
reflex_YYYYMMDD_HHMMSS_<short_id>.json
```

**Examples:**
- `reflex_20251109_143022_abc123.json`
- `reflex_20251109_150145_xyz789.json`

---

## Privacy & Data Management

### What Gets Stored

**Session Database:**
- ✅ Session metadata (AI ID, timestamps)
- ✅ Epistemic vectors (scores + rationales)
- ✅ Cascade decisions
- ✅ Performance metrics
- ❌ **NO user data** (unless explicitly provided)
- ❌ **NO conversation content** (only task descriptions)

**Reflex Logs:**
- ✅ Pure epistemic assessments
- ✅ Task descriptions
- ✅ Vector measurements
- ❌ **NO personal information**
- ❌ **NO sensitive content**

### .gitignore Protection

**Both locations excluded by default:**

```gitignore
# Session data (gitignored for privacy)
.empirica/sessions/
.empirica/chat_sessions/
.empirica/exports/

# Reflex logs (gitignored for privacy)
.empirica_reflex_logs/
```

**Why?**
- Session data is personal to the AI agent
- May contain task-specific context
- Not part of codebase
- Should not be committed

### Cleanup & Maintenance

**When to clean:**
- After project completion
- When switching contexts
- Before sharing repository
- Privacy requirements

**How to clean:**

```bash
# Remove all session data
rm -rf .empirica/sessions/*.db

# Remove reflex logs
rm -rf .empirica_reflex_logs/*.json

# Keep directory structure
touch .empirica/sessions/.gitkeep
touch .empirica_reflex_logs/.gitkeep
```

**Export before cleanup:**

```bash
# Export session to JSON for continuity
empirica sessions-export <session_id> > session_backup.json

# Or export all
empirica sessions-list --json > all_sessions.json
```

---

## Querying Session Data

### CLI Queries

```bash
# List all sessions
empirica sessions-list

# Show session details
empirica sessions-show <session_id>

# Export session
empirica sessions-export <session_id>

# Monitor current activity
empirica monitor
```

### Python API Queries

```python
from empirica.data.session_database import SessionDatabase

# Connect to database
db = SessionDatabase()

# Get session
session = db.get_session(session_id)
print(f"Started: {session['start_time']}")
print(f"Cascades: {session['total_cascades']}")

# Get all cascades for session
cascades = db.get_session_cascades(session_id)
for cascade in cascades:
    print(f"Task: {cascade['task']}")
    print(f"Confidence: {cascade['final_confidence']}")
    print(f"Action: {cascade['final_action']}")

# Get assessments for cascade
assessments = db.get_cascade_assessments(cascade_id)

# Query by confidence range
cursor = db.conn.cursor()
cursor.execute("""
    SELECT cascade_id, task, final_confidence
    FROM cascades
    WHERE final_confidence BETWEEN 0.7 AND 0.8
    ORDER BY started_at DESC
""")
moderate_confidence_cascades = cursor.fetchall()

# Close when done
db.close()
```

### Advanced Queries

**Find all investigations:**
```python
cursor.execute("""
    SELECT c.cascade_id, c.task, c.investigation_rounds, c.final_confidence
    FROM cascades c
    WHERE c.investigation_rounds > 0
    ORDER BY c.investigation_rounds DESC
""")
```

**Calibration analysis (using reflexes table):**
```python
# Compare PREFLIGHT vs POSTFLIGHT vectors for learning deltas
cursor.execute("""
    SELECT
        pre.session_id,
        pre.cascade_id,
        pre.uncertainty as preflight_uncertainty,
        post.uncertainty as postflight_uncertainty,
        (pre.uncertainty - post.uncertainty) as uncertainty_reduction,
        json_extract(post.reflex_data, '$.calibration_accuracy') as calibration_status
    FROM reflexes pre
    JOIN reflexes post ON pre.cascade_id = post.cascade_id
    WHERE pre.phase = 'PREFLIGHT' 
      AND post.phase = 'POSTFLIGHT'
      AND json_extract(post.reflex_data, '$.calibration_accuracy') = 'overconfident'
""")
```

**Vector trend analysis (using reflexes table):**
```python
cursor.execute("""
    SELECT
        DATE(timestamp, 'unixepoch') as date,
        AVG(know) as avg_know,
        AVG(do) as avg_do,
        AVG(context) as avg_context,
        AVG(uncertainty) as avg_uncertainty
    FROM reflexes
    WHERE phase = 'PREFLIGHT'
    GROUP BY DATE(timestamp, 'unixepoch')
    ORDER BY date
""")
```

---

## Integration with Workflows

### Automatic Tracking

When using cascade API:

```python
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
from empirica.data.session_database import SessionDatabase

# Initialize
db = SessionDatabase()
session_id = db.create_session(ai_id="my_agent")

cascade = CanonicalEpistemicCascade(enable_session_db=True)

# Run cascade - automatically tracked
result = await cascade.run_epistemic_cascade(
    task="Analyze code",
    context={'session_id': session_id}
)

# Data automatically saved to:
# 1. Session database (structured)
# 2. Reflex logs (JSON)
```

### Manual Tracking

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()

# Create session
session_id = db.create_session(
    ai_id="claude",
    bootstrap_level=2,
    components_loaded=30
)

# Create cascade
cascade_id = db.create_cascade(
    session_id=session_id,
    task="Review auth code",
    context={'domain': 'security'}
)

# Log assessment
db.log_epistemic_assessment(
    cascade_id=cascade_id,
    assessment=assessment_obj,
    phase='preflight'
)

# Complete cascade
db.complete_cascade(
    cascade_id=cascade_id,
    final_action='proceed',
    final_confidence=0.82,
    investigation_rounds=1,
    duration_ms=3500
)

db.close()
```

---

## Session Continuity

### Resume Previous Session

```python
from empirica.data.session_json_handler import SessionJSONHandler

handler = SessionJSONHandler()

# Load previous session context
previous_context = handler.load_session_context(session_id)

print(f"Previous session: {previous_context['session_id']}")
print(f"Cascades completed: {len(previous_context['cascades'])}")
print(f"Last task: {previous_context['cascades'][-1]['task']}")
print(f"Learning outcomes: {previous_context['learning_summary']}")

# Use context to inform new session
new_session_id = db.create_session(
    ai_id="claude",
    bootstrap_level=2,
    previous_session_id=session_id  # Link sessions
)
```

### Export for Handoff

```python
# Export complete session to JSON
export_path = handler.export_session(db, session_id)
# Creates: .empirica/exports/session_<session_id>.json

# Another AI can load this:
import json
with open(export_path) as f:
    handoff_context = json.load(f)

# New AI understands previous context
print(f"Taking over from session: {handoff_context['session_metadata']}")
```

---

## Performance Considerations

### Indexes

All tables have appropriate indexes for common queries:

**Session Management:**
- `idx_sessions_ai` - Sessions by AI ID
- `idx_sessions_start` - Time-based session queries
- `idx_cascades_session` - Cascades by session
- `idx_cascades_confidence` - Confidence-based queries

**Epistemic Data:**
- `idx_reflexes_session` - Reflexes by session
- `idx_reflexes_phase` - Phase-based queries (PREFLIGHT/CHECK/POSTFLIGHT)

**Goals & Subtasks (v4.0):**
- `idx_goals_session` - Goals by session
- `idx_goals_status` - Filter by goal status (in_progress/complete/blocked)
- `idx_subtasks_goal` - Subtasks by goal
- `idx_subtasks_status` - Filter by subtask status

**Tracking & Analysis:**
- `idx_divergence_cascade` - Divergence by cascade
- `idx_beliefs_cascade` - Beliefs by cascade
- `idx_tools_cascade` - Tool usage by cascade
- `idx_cascade_metadata_lookup` - Metadata key-value lookups
- `idx_snapshots_session` - Snapshots by session
- `idx_snapshots_ai` - Snapshots by AI
- `idx_snapshots_cascade` - Snapshots by cascade
- `idx_snapshots_created` - Time-based snapshot queries

---

### Database Size

**Typical sizes:**
- 1,000 cascades: ~5-10 MB
- 10,000 cascades: ~50-100 MB
- Reflex logs: ~2-5 KB per assessment
- Goals/subtasks: ~1-3 KB per goal (v4.0)

**Optimization:**
- SQLite auto-vacuums
- Indexes on foreign keys and common queries
- Efficient queries with appropriate indexes

### Cleanup Strategy

**Production recommendation:**

```python
# Archive old sessions
def archive_old_sessions(days=30):
    """Archive sessions older than N days"""
    cutoff = datetime.now() - timedelta(days=days)

    old_sessions = db.get_sessions_before(cutoff)

    for session in old_sessions:
        # Export to JSON
        handler.export_session(db, session['session_id'])

        # Delete from database
        db.delete_session(session['session_id'])
```

---

## Troubleshooting

### Database Not Found

**Issue:** `SessionDatabase` can't find `.empirica/sessions/sessions.db`

**Fix:**
```bash
# Initialize directories
mkdir -p .empirica/sessions
mkdir -p .empirica_reflex_logs

# Or run bootstrap
empirica bootstrap
```

### Reflex Logs Not Writing

**Issue:** No JSON files in `.empirica_reflex_logs/`

**Check:**
```python
# Verify reflex logging enabled
cascade = CanonicalEpistemicCascade(
    enable_reflex_logging=True  # Ensure this is True
)
```

### Permission Errors

**Issue:** Cannot write to database/logs

**Fix:**
```bash
# Check permissions
ls -la .empirica/sessions/
ls -la .empirica_reflex_logs/

# Fix permissions
chmod -R u+rw .empirica
chmod -R u+rw .empirica_reflex_logs
```

---

## Next Steps

- **Python API:** [13_PYTHON_API.md](13_PYTHON_API.md)
- **Session Continuity:** [23_SESSION_CONTINUITY.md](23_SESSION_CONTINUITY.md)
- **Monitoring:** [18_MONITORING_LOGGING.md](18_MONITORING_LOGGING.md)

---

**Dual storage = queryable structure + temporal separation!** 📊


---

**Note:** Empirica uses goals (with vectorial scope and subtasks) and git notes (checkpoints, goals, handoffs) for automatic session continuity and cross-AI coordination. See [Storage Architecture](../architecture/STORAGE_ARCHITECTURE_COMPLETE.md) and [Cross-AI Coordination](26_CROSS_AI_COORDINATION.md).
