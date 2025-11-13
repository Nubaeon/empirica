# Database & Reflex Log Integration Analysis

**Date:** 2024-11-13  
**Issue:** Reflex logs exist but aren't linked to session database  
**Impact:** Sentinel can monitor but can't query historical data easily

---

## Current State

### Reflex Logs ✅ WORKING
**Location:** `.empirica_reflex_logs/{agent_id}/{date}/`  
**Example:** `.empirica_reflex_logs/ec39a5ec-c6ec-48c6-b578-8b84fc6b32da/2025-11-13/`

**Files Found:** 6 reflex frame files
- `reflex_frame_20251113T152557_preflight.json`
- `reflex_frame_20251113T152711_check.json`
- Plus 4 more

**Content:** Complete 13-vector epistemic state  
**Quality:** EXCELLENT - All data needed for Sentinel

### Session Database ⚠️ PARTIALLY WORKING
**Location:** `.empirica/sessions/sessions.db`

**Sessions:** 10 total (5 from Minimax)
- `79124e38-f244-4405-96ab-3241565381bb`
- `ec39a5ec-c6ec-48c6-b578-8b84fc6b32da`

**Epistemic Assessments:** Only 1 in DB (from older session)
- `assess_bf640a6725f7` (cascade: 6f58250d1b6d, phase: preflight)
- Scores: engagement=0.7, know=0.55, uncertainty=0.6

**Problem:** Minimax's 6 reflex logs NOT in database!

---

## Root Cause Analysis

### Issue 1: MCP Server Not Writing Reflex Logs

**When Minimax calls MCP tools:**
```python
# submit_preflight_assessment in empirica_mcp_server.py (Line 1012-1030)
db = SessionDatabase()
assessment_id = db.log_preflight_assessment(...)  # ✅ Writes to DB
# ❌ BUT: Does NOT write to reflex logs!
```

**What's Missing:**
```python
# MCP server should ALSO do:
from empirica.core.canonical.reflex_logger import ReflexLogger

logger = ReflexLogger()
frame = ReflexFrame.from_assessment(assessment, ...)
logger.log_frame_sync(frame, agent_id=session_id)  # ❌ NOT HAPPENING
```

### Issue 2: Reflex Logs Using session_id as agent_id

**Current Structure:**
```
.empirica_reflex_logs/
  └── ec39a5ec-c6ec-48c6-b578-8b84fc6b32da/  ← session_id (should be ai_id!)
      └── 2025-11-13/
          └── reflex_frame_*.json
```

**Should Be:**
```
.empirica_reflex_logs/
  └── minimax/  ← ai_id
      └── 2025-11-13/  ← date
          └── ec39a5ec-c6ec-48c6-b578-8b84fc6b32da/  ← session_id
              └── reflex_frame_*.json
```

**Benefits:**
- Group all work by AI agent
- Easy to track AI performance over time
- Sessions organized under each AI
- Sentinel can track by AI or by session

### Issue 3: No Link Between DB and Reflex Logs

**Database has:** cascade_id, assessment_id  
**Reflex logs have:** frame_id, timestamp  
**No field in DB:** reflex_log_path

**Should Add to epistemic_assessments table:**
```sql
ALTER TABLE epistemic_assessments 
ADD COLUMN reflex_log_path TEXT;
```

This enables:
```python
# Get assessment from DB
assessment = db.get_assessment(assessment_id)

# Load detailed reflex frame
frame = load_json(assessment.reflex_log_path)
```

---

## Proposed Solution

### Fix 1: Update Reflex Logger Directory Structure

**File:** `empirica/core/canonical/reflex_logger.py`

**Current (Line 59):**
```python
def _get_agent_log_dir(self, agent_id: str, log_date: date = None) -> Path:
    """Directory structure: .empirica_reflex_logs/{agent_id}/{YYYY-MM-DD}/"""
    if log_date is None:
        log_date = date.today()
    
    agent_dir = self.base_log_dir / agent_id / log_date.isoformat()
    agent_dir.mkdir(parents=True, exist_ok=True)
    return agent_dir
```

**Should Be:**
```python
def _get_agent_log_dir(
    self, 
    agent_id: str, 
    session_id: Optional[str] = None,
    log_date: date = None
) -> Path:
    """
    Directory structure: .empirica_reflex_logs/{agent_id}/{YYYY-MM-DD}/{session_id}/
    
    Args:
        agent_id: AI identifier (e.g., "minimax", "claude", "gpt4")
        session_id: Session UUID (optional, for session-specific logs)
        log_date: Date for log organization
    
    Returns:
        Path to log directory
    """
    if log_date is None:
        log_date = date.today()
    
    if session_id:
        # With session: {agent_id}/{date}/{session_id}/
        agent_dir = self.base_log_dir / agent_id / log_date.isoformat() / session_id
    else:
        # Without session: {agent_id}/{date}/
        agent_dir = self.base_log_dir / agent_id / log_date.isoformat()
    
    agent_dir.mkdir(parents=True, exist_ok=True)
    return agent_dir
```

**Update log_frame method:**
```python
async def log_frame(
    self,
    frame: ReflexFrame,
    agent_id: str = "default",
    session_id: Optional[str] = None  # NEW
) -> Path:
    """Log a ReflexFrame with optional session grouping"""
    log_dir = self._get_agent_log_dir(agent_id, session_id)
    filename = self._generate_log_filename(frame.frame_id)
    log_path = log_dir / filename
    
    # Serialize and write
    frame_json = frame.to_json(indent=2)
    async with aiofiles.open(log_path, 'w') as f:
        await f.write(frame_json)
    
    return log_path
```

---

### Fix 2: MCP Server Write to Both DB and Reflex Logs

**File:** `mcp_local/empirica_mcp_server.py`

**Update submit_preflight_assessment (Line 1012):**
```python
elif name == "submit_preflight_assessment":
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.core.canonical.reflex_logger import ReflexLogger
        from empirica.core.canonical.reflex_frame import ReflexFrame, VectorState, EpistemicAssessment, Action
        
        session_id = arguments.get("session_id")
        vectors = arguments.get("vectors", {})
        reasoning = arguments.get("reasoning", "")
        
        # Get AI ID from session
        db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
        session_info = db.get_session(session_id)
        ai_id = session_info.get('ai_id', 'unknown')
        
        # ... existing vector flattening code ...
        
        # Create cascade
        cascade_id = db.create_cascade(...)
        
        # Log to DATABASE
        assessment_id = db.log_preflight_assessment(
            session_id=session_id,
            cascade_id=cascade_id,
            prompt_summary=reasoning[:200],
            vectors=flat_vectors,
            uncertainty_notes=f"UNCERTAINTY={flat_vectors.get('uncertainty', 0.5)}"
        )
        
        # NEW: Also log to REFLEX LOGS
        logger = ReflexLogger()
        
        # Create EpistemicAssessment object
        assessment = EpistemicAssessment(
            assessment_id=assessment_id,
            task="PREFLIGHT assessment",
            engagement=VectorState(flat_vectors.get('engagement', 0.5), reasoning),
            engagement_gate_passed=flat_vectors.get('engagement', 0.5) >= 0.6,
            know=VectorState(flat_vectors.get('know', 0.5), ""),
            do=VectorState(flat_vectors.get('do', 0.5), ""),
            context=VectorState(flat_vectors.get('context', 0.5), ""),
            # ... all 13 vectors ...
            uncertainty=VectorState(flat_vectors.get('uncertainty', 0.5), ""),
            overall_confidence=sum(flat_vectors.get(k, 0.5) for k in ['engagement', 'know', 'do', 'context']) / 4,
            recommended_action=Action.PROCEED
        )
        
        # Create and log reflex frame
        frame = ReflexFrame.from_assessment(
            assessment,
            frame_id=f"preflight_{assessment_id[:8]}",
            task="PREFLIGHT assessment",
            context={"phase": "preflight", "reasoning": reasoning}
        )
        
        reflex_log_path = logger.log_frame_sync(
            frame,
            agent_id=ai_id,
            session_id=session_id
        )
        
        # Update DB with reflex log path
        db.cursor.execute(
            "UPDATE epistemic_assessments SET reflex_log_path = ? WHERE assessment_id = ?",
            (str(reflex_log_path), assessment_id)
        )
        db.conn.commit()
        
        db.close()
        
        return [types.TextContent(type="text", text=json.dumps({
            "ok": True,
            "message": "PREFLIGHT assessment logged to database AND reflex logs",
            "session_id": session_id,
            "cascade_id": cascade_id,
            "assessment_id": assessment_id,
            "reflex_log_path": str(reflex_log_path),
            "next_phase": "THINK → PLAN → INVESTIGATE"
        }, indent=2))]
```

**Repeat for:**
- `submit_check_assessment`
- `submit_postflight_assessment`

---

### Fix 3: Add reflex_log_path to Database Schema

**File:** `empirica/data/session_database.py`

**Update schema (Line 198):**
```python
CREATE TABLE IF NOT EXISTS epistemic_assessments (
    assessment_id TEXT PRIMARY KEY,
    cascade_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    
    engagement REAL NOT NULL,
    # ... all existing fields ...
    
    uncertainty REAL NOT NULL,
    uncertainty_rationale TEXT,
    uncertainty_evidence TEXT,
    
    overall_confidence REAL NOT NULL,
    recommended_action TEXT NOT NULL,
    
    reflex_log_path TEXT,  # NEW: Link to reflex frame file
    
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
)
```

**Add migration:**
```python
def _run_migrations(self):
    """Run schema migrations"""
    cursor = self.conn.cursor()
    
    # Migration 1: Add reflex_log_path if missing
    cursor.execute("PRAGMA table_info(epistemic_assessments)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'reflex_log_path' not in columns:
        cursor.execute(
            "ALTER TABLE epistemic_assessments ADD COLUMN reflex_log_path TEXT"
        )
        self.conn.commit()
        print("✓ Added reflex_log_path column to epistemic_assessments")
```

---

## Benefits After Fixes

### 1. Unified Data Access
```python
# Sentinel can query from DB
assessments = db.query_assessments(session_id=session_id)

# Then load detailed reflex frames
for assessment in assessments:
    frame = load_json(assessment.reflex_log_path)
    # Full 13-vector data with rationale
```

### 2. Better Organization
```
.empirica_reflex_logs/
  ├── minimax/
  │   └── 2025-11-13/
  │       ├── session-abc123/
  │       │   ├── reflex_frame_152557_preflight.json
  │       │   └── reflex_frame_152711_check.json
  │       └── session-def456/
  │           └── reflex_frame_160015_preflight.json
  ├── claude/
  │   └── 2025-11-13/
  │       └── session-ghi789/
  │           └── reflex_frame_143022_preflight.json
  └── gpt4/
      └── 2025-11-13/
          └── session-jkl012/
              └── reflex_frame_141533_preflight.json
```

### 3. Sentinel Queries
```python
# Track Minimax over time
minimax_sessions = get_all_sessions(ai_id='minimax')

# Track specific session
session_frames = get_reflex_logs(
    ai_id='minimax',
    session_id='ec39a5ec-c6ec-48c6-b578-8b84fc6b32da'
)

# Analyze trajectory
preflight = db.get_assessment(session_id, phase='preflight')
check = db.get_assessment(session_id, phase='check')
delta = calculate_epistemic_delta(preflight, check)
```

### 4. Historical Analysis
```python
# All Minimax work
all_minimax = db.query_assessments(ai_id='minimax')

# Minimax on specific date
today_minimax = get_reflex_logs(
    ai_id='minimax',
    date='2025-11-13'
)

# Cross-session patterns
pattern = analyze_confidence_trajectory(ai_id='minimax', days=7)
```

---

## Implementation Priority

**Priority 1: Fix Reflex Logger Directory Structure** (30 min)
- Update `_get_agent_log_dir()` to include session_id
- Update `log_frame()` to accept session_id
- Test with new logs

**Priority 2: Add reflex_log_path to DB Schema** (15 min)
- Add column to epistemic_assessments
- Add migration function
- Test migration on existing DB

**Priority 3: Update MCP Server to Write Both** (1 hour)
- Update submit_preflight_assessment
- Update submit_check_assessment
- Update submit_postflight_assessment
- Test full workflow

**Total Estimated Time:** ~2 hours

---

## Current Workaround for Sentinel

**Until fixes are implemented, Sentinel can:**

1. **Read reflex logs directly:**
```python
import json
from pathlib import Path

def get_latest_epistemic_state(session_id):
    """Get latest epistemic state from reflex logs"""
    log_dir = Path(f".empirica_reflex_logs/{session_id}/2025-11-13/")
    
    if not log_dir.exists():
        return None
    
    # Find latest file
    files = sorted(log_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    
    with open(files[-1]) as f:
        return json.load(f)

# Use it
state = get_latest_epistemic_state('ec39a5ec-c6ec-48c6-b578-8b84fc6b32da')
print(f"Latest confidence: {state['overallConfidence']}")
```

2. **Track trajectories:**
```python
def get_epistemic_trajectory(session_id, date='2025-11-13'):
    """Get all assessments in order"""
    log_dir = Path(f".empirica_reflex_logs/{session_id}/{date}/")
    
    frames = []
    for file in sorted(log_dir.glob("*.json")):
        with open(file) as f:
            frames.append(json.load(f))
    
    return frames

# Analyze
trajectory = get_epistemic_trajectory('ec39a5ec-c6ec-48c6-b578-8b84fc6b32da')
for i, frame in enumerate(trajectory):
    print(f"{i+1}. {frame['phase']}: confidence={frame['overallConfidence']}")
```

**This works but requires file system access instead of SQL queries.**

---

## Conclusion

**Current State:**
- ✅ Reflex logs have all the data
- ⚠️ Database has some data but not linked
- ❌ No unified access

**After Fixes:**
- ✅ Reflex logs organized by ai_id/date/session_id
- ✅ Database fully populated
- ✅ DB links to reflex logs (reflex_log_path)
- ✅ Sentinel can query SQL OR read detailed frames
- ✅ Historical analysis enabled

**Implementation:** ~2 hours to unify the system

---

**Recommendation:** Implement fixes in order (1 → 2 → 3) to enable full Sentinel capabilities.
