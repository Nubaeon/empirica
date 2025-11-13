# Database & Reflex Log Issue - Quick Summary

**Problem:** Reflex logs exist but aren't integrated with session database

---

## 🔍 What We Found

**✅ Reflex Logs Working:**
- 6 files from Minimax sessions
- Complete 13-vector data
- Sufficient for Sentinel monitoring

**⚠️ Database Partially Working:**
- Sessions exist (10 total, 5 from Minimax)
- Only 1 old epistemic assessment in DB
- Minimax's 6 recent assessments NOT in DB

**❌ No Integration:**
- Reflex logs and DB not linked
- Can't query historical data easily
- Directory structure needs improvement

---

## 🐛 Root Causes

### 1. MCP Server Not Writing Reflex Logs
```python
# MCP server only writes to DB:
db.log_preflight_assessment(...)  # ✅

# But doesn't write reflex logs:
logger.log_frame_sync(...)  # ❌ MISSING
```

### 2. Wrong Directory Structure
**Current:** `.empirica_reflex_logs/{session_id}/{date}/`  
**Should be:** `.empirica_reflex_logs/{ai_id}/{date}/{session_id}/`

**Benefits of correct structure:**
- Group all work by AI (minimax, claude, etc.)
- Easy to track AI performance over time
- Sessions organized under each AI

### 3. No Link Between DB and Reflex Logs
**Need:** `reflex_log_path` column in `epistemic_assessments` table

---

## 🔧 Fixes Needed

**Priority 1: Fix Directory Structure** (30 min)
- Update `reflex_logger.py` to use `{ai_id}/{date}/{session_id}/`

**Priority 2: Add DB Column** (15 min)
- Add `reflex_log_path TEXT` to `epistemic_assessments` table
- Add migration function

**Priority 3: Update MCP Server** (1 hour)
- Write to BOTH DB and reflex logs
- Link them via reflex_log_path
- Apply to preflight, check, postflight

**Total Time:** ~2 hours

---

## 💡 Current Workaround

**Sentinel can read reflex logs directly:**
```python
import json
from pathlib import Path

# Get latest state
log_dir = Path(f".empirica_reflex_logs/{session_id}/2025-11-13/")
files = sorted(log_dir.glob("*.json"))
with open(files[-1]) as f:
    state = json.load(f)
```

**Works but:**
- Requires file system access
- No SQL queries
- Hard to analyze across sessions

---

## ✅ After Fixes

**Unified Access:**
```python
# Query from DB
assessments = db.query_assessments(ai_id='minimax')

# Load detailed frames
for assessment in assessments:
    frame = load_json(assessment.reflex_log_path)
```

**Better Organization:**
```
.empirica_reflex_logs/
  ├── minimax/2025-11-13/session-abc/reflex_*.json
  ├── claude/2025-11-13/session-def/reflex_*.json
  └── gpt4/2025-11-13/session-ghi/reflex_*.json
```

**Sentinel Capabilities:**
- SQL queries across sessions
- Track AI performance over time
- Analyze epistemic trajectories
- Historical pattern detection

---

**Status:** Analysis complete, fixes documented in DATABASE_REFLEX_LOG_ANALYSIS.md (483 lines)

**Ready to implement?** The fixes will enable full Sentinel monitoring and historical analysis.
