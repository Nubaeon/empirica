# Reflex Frame Archival & Compression Strategy

**Purpose:** Prevent infinite growth of Reflex Frame logs while maintaining epistemic continuity

**Date:** 2025-10-29 (Updated for v2.0)

---

## Problem Statement

Reflex Frames create detailed JSON logs for temporal separation, epistemic synchronization, and tmux dashboard visualization. With the addition of auto-tracking in v2.0, logs are now generated in three formats:

1. **SQLite Database** - Structured data for queries
2. **JSON Session Exports** - Complete session records
3. **Reflex Frame Logs** - Real-time chain-of-thought for dashboard

Without management, these logs will:

1. **Grow indefinitely** - Every cascade creates multiple files
2. **Consume disk space** - JSON is verbose, especially with 13-vector assessments
3. **Slow down reads** - AI agents and dashboard reading old logs
4. **Reduce relevance** - Old reasoning patterns may not reflect current system state

**Goal:** Keep AI agents "on track" with recent, relevant epistemic patterns while gracefully degrading old data.

---

## Auto-Tracking Output Formats

### Format 1: SQLite Database
**Location:** `.empirica/{ai_id}/empirica.db`
**Purpose:** Fast queries, structured data, analytics
**Management:** Manual SQL cleanup or Python scripts
**Size:** ~10-50 KB per cascade (compressed in binary)

### Format 2: JSON Session Exports
**Location:** `.empirica/{ai_id}/sessions/{session_id}.json`
**Purpose:** Complete session audit trail
**Management:** Follows Tier strategy below
**Size:** ~50-200 KB per session

### Format 3: Reflex Frame Logs  
**Location:** `.empirica_reflex_logs/{ai_id}/{YYYY-MM-DD}/{frame_id}_{timestamp}.json`
**Purpose:** Real-time tmux dashboard, chain-of-thought visualization
**Management:** **Primary focus of archival strategy**
**Size:** ~10-30 KB per frame, 5-7 frames per cascade

**This document focuses on Format 3 (Reflex Frames) as it has the highest growth rate.**

---

## Archival Tiers

### Tier 1: HOT (Last 7 Days) - Full Fidelity

**Retention:** Keep ALL details
**Location:** `.empirica_reflex_logs/cascade/YYYY-MM-DD/`
**Format:** Full JSON with all epistemic vectors, reasoning, evidence

**Why:**
- Recent decisions most relevant for synchronization
- Full detail enables precise epistemic alignment
- Active debugging/iteration needs complete logs

**Example Size (Enhanced Cascade Workflow):**
- ~7-9 files per cascade:
  - 1 PREFLIGHT assessment frame
  - 1 Think/Plan frame
  - 1-3 Investigate frames (depending on complexity)
  - 1 Check frame
  - 1 Act frame
  - 1 POSTFLIGHT assessment frame
- ~80-150 KB per cascade (13-vector preflight + postflight assessments)
- ~100 cascades/day = 8-15 MB/day
- **7 days = 56-105 MB** (manageable)

---

### Tier 2: WARM (8-30 Days) - Compressed Summary

**Retention:** Compress to summary format
**Location:** `.empirica_reflex_logs/archive/YYYY-MM/compressed/`
**Format:** Compressed JSON with key decisions only

**Compression Strategy:**

**From Full JSON:**
```json
{
  "frameId": "preflight_abc123",
  "timestamp": "2025-10-29T12:34:56Z",
  "phase": "uncertainty",
  "aiId": "claude_copilot",
  "task": "Debug authentication bug in user_service.py",
  "epistemicVector": {
    "engagement": 0.85,
    "know": 0.4,
    "do": 0.8,
    "context": 0.3,
    "clarity": 0.7,
    "coherence": 0.65,
    "signal": 0.75,
    "density": 0.45,
    "state": 0.5,
    "change": 0.6,
    "completion": 0.3,
    "impact": 0.7,
    "uncertainty": 0.75,
    "overall_confidence": 0.48
  },
  "metaStateVector": {
    "think": 0.0,
    "uncertainty": 1.0,
    "investigate": 0.0,
    "check": 0.0,
    "act": 0.0
  },
  "recommendedAction": "investigate",
  "knowledgeGaps": ["code_content", "error_logs", "auth_flow"],
  "bayesianActive": true,
  "driftDetected": false,
  "context": {...}
}
```

**To Compressed Summary:**
```json
{
  "id": "abc123_20251029",
  "task_summary": "Debug auth bug",
  "confidence": 0.48,
  "uncertainty": 0.75,
  "action": "investigate",
  "critical_vectors": {
    "know": 0.4,
    "context": 0.3,
    "completion": 0.3
  },
  "enhancements": {
    "bayesian": true,
    "investigation": true,
    "drift": false
  },
  "delta_uncertainty": -0.50,
  "outcome": "identified_bug",
  "timestamp": "2025-10-29T12:34:56Z"
}
```

**Compression Ratio:** ~85-90% size reduction

**What's Kept:**
- Task summary (not full text)
- Final decision (action + confidence + uncertainty)
- Critical low vectors (only if <0.5)
- **Δuncertainty** (pre/post-flight delta)
- Enhancement activation flags
- Outcome (if available)

**What's Discarded:**
- Detailed rationales
- Full evidence chains
- Intermediate investigation steps
- Per-phase breakdowns

---

### Tier 3: COLD (31-90 Days) - Aggregate Statistics

**Retention:** Daily aggregates only
**Location:** `.empirica_reflex_logs/archive/YYYY-MM/aggregated/`
**Format:** Daily summary statistics

**Aggregate Format:**
```json
{
  "date": "2025-10-29",
  "total_cascades": 87,
  "actions": {
    "proceed": 62,
    "investigate": 18,
    "clarify": 7
  },
  "avg_confidence": 0.78,
  "avg_uncertainty": 0.35,
  "avg_delta_uncertainty": -0.28,
  "enhancements": {
    "bayesian_activations": 23,
    "investigations_triggered": 18,
    "drift_detections": 2
  },
  "common_knowledge_gaps": ["code_content", "context", "requirements"],
  "performance": {
    "avg_time": 14.5,
    "cache_hit_rate": 0.62
  }
}
```

**Compression Ratio:** ~99% size reduction

**What's Kept:**
- Daily statistics
- Aggregate patterns
- Enhancement usage rates
- Performance metrics

**What's Discarded:**
- Individual cascades
- Specific tasks
- Detailed assessments

---

### Tier 4: ARCHIVE (>90 Days) - Delete or Long-term Storage

**Options:**

**Option A: Delete**
- Most practical for production
- Keep only statistics
- Rely on recent patterns for synchronization

**Option B: Long-term Archive**
- Compress to .tar.gz
- Store in separate archive location
- For compliance/audit needs only
- Not accessed during normal synchronization

---

## Archival Schedule

### Daily (2 AM UTC):
1. Compress yesterday's Tier 1 logs if older than 7 days
2. Move to Tier 2 (compressed summaries)
3. Update Tier 2 index

### Weekly (Sunday 3 AM UTC):
1. Aggregate Tier 2 logs older than 30 days
2. Create daily aggregates (Tier 3)
3. Delete original Tier 2 files after aggregation

### Monthly (1st, 4 AM UTC):
1. Delete or archive Tier 3 logs older than 90 days
2. Generate monthly summary report
3. Update synchronization index

---

## Synchronization Index

**Purpose:** Enable AI agents to quickly find relevant logs without scanning everything

**Location:** `.empirica_reflex_logs/sync_index.json`

**Format:**
```json
{
  "last_updated": "2025-10-29T18:00:00",
  "ai_id": "claude_copilot",
  "version": "2.0",
  "tiers": {
    "hot": {
      "date_range": ["2025-10-22", "2025-10-29"],
      "total_cascades": 687,
      "location": ".empirica_reflex_logs/{ai_id}/"
    },
    "warm": {
      "date_range": ["2025-09-29", "2025-10-21"],
      "total_cascades": 1842,
      "location": ".empirica_reflex_logs/archive/{ai_id}/2025-10/compressed/"
    },
    "cold": {
      "date_range": ["2025-07-29", "2025-09-28"],
      "location": ".empirica_reflex_logs/archive/{ai_id}/aggregated/"
    }
  },
  "recent_patterns": {
    "common_tasks": ["debug", "code_review", "refactor", "architecture"],
    "avg_confidence": 0.76,
    "avg_uncertainty": 0.38,
    "avg_delta_uncertainty": -0.25,
    "investigation_rate": 0.21,
    "bayesian_activation_rate": 0.34
  },
  "database_stats": {
    "total_sessions": 156,
    "total_cascades": 687,
    "total_assessments": 2145,
    "db_size_mb": 4.2
  }
}
```

**AI Agent Usage:**
1. Read sync index to understand what's available
2. Focus on Tier 1 (hot) for recent patterns
3. Sample Tier 2 (warm) if needed for broader context
4. Use Tier 3 (cold) statistics for long-term trends
5. Query SQLite database for specific investigations

---

## Database Management

### SQLite Database Cleanup

**Database:** `.empirica/{ai_id}/empirica.db`

**Tables:**
- `sessions` - Session metadata
- `cascades` - Cascade records
- `assessments` - 13-vector assessments

**Cleanup Strategy:**

**1. Vacuum Regularly:**
```sql
-- Reclaim space from deleted records
VACUUM;
```

**2. Archive Old Sessions:**
```sql
-- Export to JSON before deleting
-- Then delete sessions older than 90 days
DELETE FROM sessions 
WHERE created_at < datetime('now', '-90 days');
```

**3. Maintain Indices:**
```sql
-- Keep indices optimized
REINDEX;
ANALYZE;
```

**4. Monitor Size:**
```bash
sqlite3 .empirica/claude_copilot/empirica.db \
  "SELECT page_count * page_size / 1024 / 1024 as size_mb FROM pragma_page_count(), pragma_page_size();"
```

**Recommended Cron:**
```cron
# Weekly database maintenance (Sunday 4 AM)
0 4 * * 0 /path/to/db_maintenance.sh
```

---

## Implementation

### Phase 1: Archive Tool (Immediate)

**Script:** `archive_reflex_frames.py`

```python
#!/usr/bin/env python3
"""
Reflex Frame Archival Tool

Automatically compresses and archives old Reflex Frames
based on configured retention tiers.
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

class ReflexFrameArchiver:
    def __init__(self, logs_dir: str = ".empirica_reflex_logs"):
        self.logs_dir = Path(logs_dir)
        self.cascade_dir = self.logs_dir / "cascade"
        self.archive_dir = self.logs_dir / "archive"

        # Create archive structure
        (self.archive_dir / "compressed").mkdir(parents=True, exist_ok=True)
        (self.archive_dir / "aggregated").mkdir(parents=True, exist_ok=True)

    def compress_to_summary(self, full_json: Dict[str, Any]) -> Dict[str, Any]:
        """Compress full Reflex Frame to summary format"""

        # Extract key information
        summary = {
            "id": full_json.get("assessment_id", "unknown"),
            "task_summary": full_json.get("task", "")[:100],  # First 100 chars
            "confidence": full_json.get("overall_confidence", 0.0),
            "action": full_json.get("action", "unknown"),
            "timestamp": full_json.get("timestamp", "")
        }

        # Keep only low vectors (potential issues)
        key_vectors = {}
        for tier in ["foundation", "comprehension", "execution"]:
            if tier in full_json:
                for vector, data in full_json[tier].items():
                    if isinstance(data, dict) and data.get("score", 1.0) < 0.5:
                        key_vectors[vector] = data["score"]

        if key_vectors:
            summary["key_vectors"] = key_vectors

        # Enhancement flags
        summary["enhancements"] = {
            "bayesian": full_json.get("bayesian_active", False),
            "investigation": full_json.get("investigation_rounds", 0) > 0,
            "drift": full_json.get("drift_detected", False)
        }

        return summary

    def archive_old_logs(self, days_hot: int = 7, days_warm: int = 30):
        """Archive logs older than specified days"""

        now = datetime.now()
        hot_cutoff = now - timedelta(days=days_hot)
        warm_cutoff = now - timedelta(days=days_warm)

        print(f"Archiving logs older than {days_hot} days...")

        # Process each date directory
        for date_dir in self.cascade_dir.glob("20*"):
            try:
                date = datetime.strptime(date_dir.name, "%Y-%m-%d")

                if date < warm_cutoff:
                    # Tier 3: Aggregate
                    print(f"  Aggregating {date_dir.name} (Tier 3)...")
                    self._aggregate_to_stats(date_dir)
                    shutil.rmtree(date_dir)

                elif date < hot_cutoff:
                    # Tier 2: Compress
                    print(f"  Compressing {date_dir.name} (Tier 2)...")
                    self._compress_to_summaries(date_dir)
                    shutil.rmtree(date_dir)

                else:
                    # Tier 1: Keep as-is
                    print(f"  Keeping {date_dir.name} (Tier 1 - Hot)")

            except ValueError:
                # Invalid date format, skip
                continue

        print("Archival complete!")

    def _compress_to_summaries(self, date_dir: Path):
        """Compress full logs to summary JSON"""

        summaries = []
        for json_file in date_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    full_data = json.load(f)
                    summary = self.compress_to_summary(full_data)
                    summaries.append(summary)
            except Exception as e:
                print(f"    Warning: Failed to compress {json_file.name}: {e}")

        # Save compressed summaries
        if summaries:
            month_dir = self.archive_dir / "compressed" / date_dir.name[:7]  # YYYY-MM
            month_dir.mkdir(parents=True, exist_ok=True)

            output_file = month_dir / f"{date_dir.name}.json"
            with open(output_file, 'w') as f:
                json.dump(summaries, f, indent=2)

            print(f"    Saved {len(summaries)} summaries to {output_file}")

    def _aggregate_to_stats(self, date_dir: Path):
        """Aggregate logs to daily statistics"""

        stats = {
            "date": date_dir.name,
            "total_cascades": 0,
            "actions": {},
            "avg_confidence": 0.0,
            "enhancements": {
                "bayesian_activations": 0,
                "investigations_triggered": 0,
                "drift_detections": 0
            }
        }

        confidences = []

        for json_file in date_dir.glob("*_act_*.json"):  # Only final ACT phase
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    stats["total_cascades"] += 1

                    # Count actions
                    action = data.get("action", "unknown")
                    stats["actions"][action] = stats["actions"].get(action, 0) + 1

                    # Track confidence
                    conf = data.get("overall_confidence", 0.0)
                    confidences.append(conf)

                    # Track enhancements
                    if data.get("bayesian_active"):
                        stats["enhancements"]["bayesian_activations"] += 1
                    if data.get("investigation_rounds", 0) > 0:
                        stats["enhancements"]["investigations_triggered"] += 1
                    if data.get("drift_detected"):
                        stats["enhancements"]["drift_detections"] += 1

            except Exception as e:
                print(f"    Warning: Failed to process {json_file.name}: {e}")

        if confidences:
            stats["avg_confidence"] = sum(confidences) / len(confidences)

        # Save aggregated stats
        if stats["total_cascades"] > 0:
            month_dir = self.archive_dir / "aggregated" / date_dir.name[:7]
            month_dir.mkdir(parents=True, exist_ok=True)

            output_file = month_dir / f"{date_dir.name}.json"
            with open(output_file, 'w') as f:
                json.dump(stats, f, indent=2)

            print(f"    Saved stats for {stats['total_cascades']} cascades to {output_file}")

if __name__ == "__main__":
    archiver = ReflexFrameArchiver()
    archiver.archive_old_logs(days_hot=7, days_warm=30)
```

### Phase 2: Synchronization Helper (Future)

**Tool:** `sync_helper.py`

- Reads sync index
- Provides filtered log access for AI agents
- Samples across tiers for epistemic synchronization
- Prevents AI from reading excessive old logs

---

## Configuration

**Environment Variables:**
```bash
EMPIRICA_LOGS_DIR=".empirica_reflex_logs"
EMPIRICA_HOT_DAYS=7        # Tier 1 retention
EMPIRICA_WARM_DAYS=30      # Tier 2 retention
EMPIRICA_COLD_DAYS=90      # Tier 3 retention
EMPIRICA_AUTO_ARCHIVE=true # Enable automatic archival
```

**Cron Job:**
```cron
# Daily archival at 2 AM
0 2 * * * /path/to/archive_reflex_frames.py
```

---

## Monitoring

### Key Metrics:
1. **Storage Growth Rate:** MB/day of new logs
2. **Compression Ratio:** Size reduction from Tier 1 → Tier 2
3. **Synchronization Impact:** AI agent read times before/after archival
4. **Pattern Continuity:** Can AI agents still synchronize effectively?

### Alerts:
- Storage exceeds 1 GB (investigate retention settings)
- Compression fails (backup before archival)
- Sync index becomes stale (update failed)
- **Database size > 100 MB** (run cleanup)
- **Reflex logs older than 7 days not archived** (archival script failed)

---

## Integration with Auto-Tracking

**Auto-tracking writes to 3 destinations:**
1. SQLite (always) - For queries
2. JSON sessions (on cascade end) - For audit
3. Reflex logs (realtime) - For dashboard

**Archival focuses on #3 (Reflex logs)** because:
- Highest write frequency (6-7 files per cascade)
- Largest total size (verbose JSON)
- Used by tmux dashboard (needs recent data only)

**Database (#1) managed separately:**
- Binary format (already compressed)
- Efficient queries (indexed)
- Manual cleanup or scheduled scripts

**Session JSON (#2) archived with same Tier strategy:**
- Follows Reflex log archival
- Compressed alongside Reflex frames
- Part of same date-based directories

---

## Benefits

1. **Bounded Storage:** Predictable disk usage (~100-300 MB typical including DB)
2. **Fast Synchronization:** AI agents read recent, relevant logs only
3. **Historical Context:** Aggregates preserve long-term patterns
4. **Graceful Degradation:** Older data compressed, not deleted immediately
5. **Audit Trail:** Statistics preserved for analysis
6. **Dashboard Performance:** Tmux reads only recent reflex logs
7. **Database Efficiency:** SQLite remains queryable, manageable size

---

## Trade-offs

**Pro:**
- Keeps AI agents focused on recent patterns
- Prevents disk space issues
- Maintains performance as logs grow

**Con:**
- Lose detailed reasoning from old cascades
- Can't replay exact historical decisions
- Aggregation may miss subtle patterns

**Mitigation:**
- Keep Tier 1 (hot) long enough for active work (7 days)
- Tier 2 (warm) preserves key decisions (30 days)
- Tier 3 (cold) maintains statistical context (90 days)

---

## Implementation Priority

**Now:**
- Manual archival script (archive_reflex_frames.py)
- Test on current logs with 13-vector data
- Validate compression doesn't lose critical data (especially Δuncertainty)
- Database maintenance script

**Soon:**
- Automated cron job
- Sync index generation (including DB stats)
- AI agent sync helper
- Dashboard integration with archived data

**Future:**
- Smart compression (ML-based important log detection)
- Distributed archival (cloud storage for cold tier)
- Advanced analytics on archived patterns
- Automated Δuncertainty trend analysis

---

## Enhanced Cascade Workflow Integration (v2.1)

### Workflow Components

**NEW in v2.1:** Enhanced Cascade Workflow introduces dedicated preflight/postflight components that generate structured reflex frames:

**Preflight Assessor** (`empirica/workflow/preflight_assessor.py`):
- Logs to: `preflight_assessments` table + reflex frame
- Captures baseline epistemic state BEFORE any work
- Frame type: `"preflight_assessment"`
- 13 vectors measured at task start

**Postflight Assessor** (`empirica/workflow/postflight_assessor.py`):
- Logs to: `postflight_assessments` table + reflex frame  
- Captures final epistemic state AFTER completion
- Frame type: `"postflight_assessment"`
- 13 vectors measured + Δ improvements calculated

**Cascade Workflow Orchestrator** (`empirica/workflow/cascade_workflow_orchestrator.py`):
- Coordinates 7-phase workflow
- Logs each phase transition to reflex frames
- Integrates Goal Orchestrator, Bayesian Guardian, Drift Monitor

### Session JSON Export Enhancement

**Auto-exported to:** `.empirica/exports/{session_id}/session_{timestamp}.json`

Now includes:
```json
{
  "session_metadata": {...},
  "cascades": [
    {
      "cascade_id": "...",
      "task": "...",
      "phases": ["preflight", "think", "plan", "investigate", "check", "act", "postflight"],
      "preflight_vectors": {13 vectors},
      "postflight_vectors": {13 vectors},
      "delta_vectors": {calculated improvements},
      "investigation_rounds": 2,
      "calibration_accurate": true,
      "reflex_frames": [...]
    }
  ]
}
```

**Archival Implications:**
- Preflight/postflight frames are CRITICAL for calibration validation
- These should be preserved longer in Tier 1 (HOT) 
- Δ vectors enable learning from past calibration accuracy
- Future: Cognitive Vault governance uses Δ anomalies for audits

---

**Status:** Design complete, ready for implementation  
**Version:** 2.1 (updated for Enhanced Cascade Workflow + preflight/postflight)
