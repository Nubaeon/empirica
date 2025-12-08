# 18. Monitoring & Logging

**Version:** Empirica v4.0  
**Status:** Production Ready

---

## Overview

Empirica provides comprehensive monitoring and logging across **3 output formats**: SQLite database, JSON sessions, and Reflex frames. This guide covers log locations, monitoring strategies, querying patterns, and production best practices.

---

## Three Output Formats

### Format Comparison

| Format | Purpose | Frequency | Use Case | Location |
|--------|---------|-----------|----------|----------|
| **SQLite** | Structured queries | Every assessment | Analytics, dashboards | `.empirica/{ai_id}/empirica.db` |
| **JSON** | Complete audit trail | End of cascade | Debugging, compliance | `.empirica/{ai_id}/sessions/` |
| **Reflex** | Real-time visibility | 6-7 per cascade | Tmux dashboard, monitoring | `.empirica_reflex_logs/{ai_id}/` |

### When to Use Each

**SQLite** → "How many investigations last week?"  
**JSON** → "Show me everything that happened in session X"  
**Reflex** → "What's the AI thinking right now?"

---

## SQLite Database Monitoring

### Database Schema

**Location:** `.empirica/{ai_id}/empirica.db`

**Tables:**
```sql
-- Session metadata
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    ai_id TEXT,
    task TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    outcome TEXT,
    total_cascades INTEGER
);

-- Cascade records
CREATE TABLE cascades (
    cascade_id TEXT PRIMARY KEY,
    session_id TEXT,
    task TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    investigation_triggered BOOLEAN,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 13-vector assessments
CREATE TABLE assessments (
    assessment_id TEXT PRIMARY KEY,
    cascade_id TEXT,
    created_at TIMESTAMP,
    
    -- 12 vectors
    confidence_score REAL,
    confidence_rationale TEXT,
    coherence_score REAL,
    coherence_rationale TEXT,
    necessity_score REAL,
    necessity_rationale TEXT,
    engagement_score REAL,
    engagement_rationale TEXT,
    attention_score REAL,
    attention_rationale TEXT,
    novelty_score REAL,
    novelty_rationale TEXT,
    risk_score REAL,
    risk_rationale TEXT,
    complexity_score REAL,
    complexity_rationale TEXT,
    ambiguity_score REAL,
    ambiguity_rationale TEXT,
    contextual_relevance_score REAL,
    contextual_relevance_rationale TEXT,
    epistemic_humility_score REAL,
    epistemic_humility_rationale TEXT,
    temporal_awareness_score REAL,
    temporal_awareness_rationale TEXT,
    uncertainty_score REAL,
    uncertainty_rationale TEXT,
    uncertainty_evidence TEXT,
    
    -- Meta
    weighted_score REAL,
    recommendation TEXT,
    should_investigate BOOLEAN,
    is_preflight BOOLEAN DEFAULT 0,
    is_postflight BOOLEAN DEFAULT 0,
    delta_uncertainty REAL,
    
    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
);
```

### Common Queries

#### Daily Statistics

```sql
-- Daily investigation rate
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_assessments,
    SUM(CASE WHEN should_investigate THEN 1 ELSE 0 END) as investigations,
    ROUND(100.0 * SUM(CASE WHEN should_investigate THEN 1 ELSE 0 END) / COUNT(*), 2) as investigation_rate
FROM assessments
WHERE created_at > datetime('now', '-7 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

#### Average Vector Scores

```sql
-- Average scores per vector
SELECT 
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    ROUND(AVG(coherence_score), 3) as avg_coherence,
    ROUND(AVG(necessity_score), 3) as avg_necessity,
    ROUND(AVG(engagement_score), 3) as avg_engagement,
    ROUND(AVG(uncertainty_score), 3) as avg_uncertainty
FROM assessments
WHERE created_at > datetime('now', '-24 hours');
```

#### Investigation Effectiveness

```sql
-- Measure learning from investigations
SELECT 
    cascade_id,
    (SELECT uncertainty_score FROM assessments WHERE cascade_id = a.cascade_id AND is_preflight = 1) as pre_uncertainty,
    (SELECT uncertainty_score FROM assessments WHERE cascade_id = a.cascade_id AND is_postflight = 1) as post_uncertainty,
    delta_uncertainty,
    CASE 
        WHEN delta_uncertainty < -0.2 THEN 'Significant Learning'
        WHEN delta_uncertainty < 0 THEN 'Some Learning'
        WHEN delta_uncertainty = 0 THEN 'No Change'
        ELSE 'Increased Uncertainty'
    END as outcome
FROM assessments a
WHERE is_postflight = 1
    AND created_at > datetime('now', '-7 days')
ORDER BY delta_uncertainty ASC
LIMIT 20;
```

#### High Uncertainty Tasks

```sql
-- Find tasks with high uncertainty
SELECT 
    c.task,
    a.uncertainty_score,
    a.uncertainty_rationale,
    a.should_investigate,
    a.created_at
FROM assessments a
JOIN cascades c ON a.cascade_id = c.cascade_id
WHERE a.uncertainty_score > 0.7
    AND a.created_at > datetime('now', '-7 days')
ORDER BY a.uncertainty_score DESC
LIMIT 10;
```

### CLI Database Queries

```bash
# Note: 'query' command is planned for future release
# Use sqlite3 directly or Python API for now:

# Custom SQL queries
sqlite3 .empirica/*/empirica.db "SELECT * FROM assessments WHERE uncertainty_score > 0.8"

# Or use Python API for programmatic access
python3 << EOF
from empirica.data import SessionDatabase
db = SessionDatabase()
sessions = db.list_sessions(limit=10)
for session in sessions:
    print(session)
EOF
```

---

## JSON Session Logging

### Session File Structure

**Location:** `.empirica/{ai_id}/sessions/{session_id}.json`

**Format:**
```json
{
  "session_id": "dc8e7460-7c01-45aa-b1bb-848124acd13f",
  "ai_id": "claude_copilot",
  "task": "Review code changes",
  "created_at": "2025-10-29T18:00:00Z",
  "completed_at": "2025-10-29T18:05:32Z",
  "cascades": [
    {
      "cascade_id": "cascade_001",
      "task": "Review code changes",
      "created_at": "2025-10-29T18:00:00Z",
      "assessments": [
        {
          "assessment_id": "assess_001",
          "timestamp": "2025-10-29T18:00:01Z",
          "is_preflight": true,
          "vectors": {
            "CONFIDENCE": {
              "score": 0.65,
              "rationale": "Familiar codebase but new changes",
              "evidence": ["past_reviews", "code_knowledge"]
            },
            "COHERENCE": {
              "score": 0.75,
              "rationale": "Assessment is internally consistent"
            },
            "UNCERTAINTY": {
              "score": 0.45,
              "rationale": "Some uncertainty about edge cases",
              "evidence": ["incomplete_context", "new_patterns"]
            }
            // ... all 12 vectors
          },
          "weighted_score": 0.68,
          "recommendation": "INVESTIGATE",
          "should_investigate": true
        }
      ],
      "investigation": {
        "triggered": true,
        "tools_used": ["code_analyzer", "test_runner"],
        "findings": ["edge_case_missing", "test_coverage_low"],
        "duration_seconds": 45
      },
      "post_flight": {
        "assessment_id": "assess_002",
        "timestamp": "2025-10-29T18:01:30Z",
        "is_postflight": true,
        "vectors": {
          "UNCERTAINTY": {
            "score": 0.25,
            "rationale": "Investigation resolved edge cases"
          }
          // ... all 12 vectors
        },
        "delta_uncertainty": -0.20,
        "learning_outcome": "Significant"
      }
    }
  ],
  "summary": {
    "total_cascades": 1,
    "investigations_triggered": 1,
    "avg_delta_uncertainty": -0.20,
    "outcome": "success"
  }
}
```

### Analyzing JSON Sessions

```bash
# List all sessions
empirica sessions list

# View specific session
empirica sessions-show dc8e7460-7c01-45aa-b1bb-848124acd13f

# Export session
empirica sessions export dc8e7460-7c01-45aa-b1bb-848124acd13f > session.json

# Search sessions
empirica sessions search --task "code review" --window 7d

# Compare sessions
empirica sessions compare session1.json session2.json
```

### JSON Query with jq

```bash
# Extract all uncertainty scores
jq '.cascades[].assessments[].vectors.UNCERTAINTY.score' session.json

# Find investigations
jq '.cascades[] | select(.investigation.triggered == true)' session.json

# Calculate avg delta uncertainty
jq '[.cascades[].post_flight.delta_uncertainty] | add / length' session.json

# Extract rationales
jq '.cascades[].assessments[] | .vectors | to_entries | .[] | {vector: .key, rationale: .value.rationale}' session.json
```

---

## Reflex Frame Logging

### Reflex Frame Structure

**Location:** `.empirica_reflex_logs/{ai_id}/cascade/{cascade_id}/`

**Files per Cascade:**
```
cascade_abc123/
├── 01_preflight_assessment.json      # Pre-investigation state
├── 02_investigation_trigger.json     # Why investigating
├── 03_tool_selection.json            # Tools chosen
├── 04_investigation_execution.json   # Investigation process
├── 05_evidence_synthesis.json        # Findings
├── 06_postflight_assessment.json     # Post-investigation state
└── 07_delta_analysis.json            # Learning summary
```

**Example Reflex Frame:**
```json
{
  "frame_type": "preflight_assessment",
  "timestamp": "2025-10-29T18:00:01Z",
  "cascade_id": "cascade_abc123",
  "ai_id": "claude_copilot",
  "task": "Review code changes",
  "assessment": {
    "UNCERTAINTY": {
      "score": 0.45,
      "rationale": "Some uncertainty about edge cases",
      "evidence": ["incomplete_context", "new_patterns"]
    },
    "CONFIDENCE": {
      "score": 0.65,
      "rationale": "Familiar codebase but new changes"
    }
    // ... all 12 vectors
  },
  "decision": {
    "weighted_score": 0.68,
    "recommendation": "INVESTIGATE",
    "should_investigate": true,
    "reasoning": "Uncertainty above threshold, investigation needed"
  }
}
```

### Monitoring Reflex Frames

```bash
# Note: 'reflex' commands are planned for future release
# For now, reflex frames are stored as JSON files in .empirica/*/reflex_frames/

# View reflex frames directory
ls -lah .empirica/*/reflex_frames/

# View latest reflex frame
ls -t .empirica/*/reflex_frames/*.json | head -1 | xargs cat | jq '.'

# List recent frames
ls -lt .empirica/*/reflex_frames/*.json | head -10

# View specific cascade frames
find .empirica/*/reflex_frames/ -name "*cascade_abc123*.json" -exec cat {} \; | jq '.'

# Search frames for pattern
grep -r "high uncertainty" .empirica/*/reflex_frames/
```

### Tmux Dashboard Integration

```bash
# Start tmux dashboard
empirica tmux start

# Dashboard shows:
# - Current cascade
# - Real-time vector scores
# - Investigation status
# - Pre/post-flight comparison
# - Δuncertainty live tracking
```

**Dashboard Layout:**
```
┌─────────────────────────────────────────────────┐
│ EMPIRICA LIVE DASHBOARD - claude_copilot       │
├─────────────────────────────────────────────────┤
│ Current Task: Review code changes               │
│ Cascade: cascade_abc123                         │
│                                                 │
│ 🧠 PRE-FLIGHT ASSESSMENT                        │
│ ├─ UNCERTAINTY: 0.45 🟡                         │
│ ├─ CONFIDENCE: 0.65 🟢                          │
│ ├─ COHERENCE: 0.75 🟢                           │
│ └─ NECESSITY: 0.80 🟢                           │
│                                                 │
│ 🔍 INVESTIGATION: IN PROGRESS                   │
│ └─ Tools: code_analyzer, test_runner            │
│                                                 │
│ 📊 POST-FLIGHT (pending)                        │
│ └─ Δuncertainty: (calculating...)               │
└─────────────────────────────────────────────────┘
```

---

## Log Levels & Verbosity

### Log Levels

```bash
# ERROR - Only errors
export EMPIRICA_LOG_LEVEL=ERROR

# WARNING - Warnings + errors
export EMPIRICA_LOG_LEVEL=WARNING

# INFO - Normal operation (default)
export EMPIRICA_LOG_LEVEL=INFO

# DEBUG - Detailed debugging
export EMPIRICA_LOG_LEVEL=DEBUG
```

### Verbose Mode

```bash
# Enable verbose output
empirica --verbose cascade "task"

# Or environment variable
export EMPIRICA_VERBOSE=true
```

### Quiet Mode

```bash
# Suppress non-critical output
empirica cascade "task" --json

# Or environment variable
export EMPIRICA_QUIET=true
```

---

## Production Monitoring

### Health Checks

```bash
# Check system health
empirica health

# Output:
# ✅ Database: OK (4.2 MB)
# ✅ Sessions: 156 total
# ✅ Reflex logs: 687 cascades
# ✅ Auto-tracking: Active
# ⚠️ Disk usage: 85% (consider archival)
```

### Performance Metrics

```bash
# Performance report
empirica performance-report --window 7d

# Metrics:
# - Avg cascade duration
# - Avg investigation time
# - Database query latency
# - Assessment LLM latency
# - Reflex frame write latency
```

### Alerts & Notifications

```bash
# Setup monitoring alerts
cat > monitoring_config.yaml << EOF
alerts:
  high_investigation_rate:
    threshold: 0.5
    window: 24h
    action: email
    
  database_size:
    threshold: 100MB
    action: archive
  
  failed_assessments:
    threshold: 5
    window: 1h
    action: page
    
  low_learning:
    # Δuncertainty not improving
    threshold: -0.05
    window: 7d
    action: review
EOF

empirica monitor --config monitoring_config.yaml --daemon
```

---

## Log Rotation & Archival

### Reflex Frame Archival

```bash
# Archive old reflex frames
# Note: archive-reflex command is planned for future release
# For now, use manual archival:

# Create archive directory
mkdir -p .empirica_reflex_logs/archive/

# Find and compress old reflex frames (7+ days old)
find .empirica/*/reflex_frames/ -type f -mtime +7 -exec gzip {} \;
find .empirica/*/reflex_frames/ -name "*.gz" -exec mv {} .empirica_reflex_logs/archive/ \;

# See REFLEX_FRAME_ARCHIVAL_STRATEGY.md for details
```

### Database Maintenance

```bash
# Vacuum database (reclaim space)
sqlite3 .empirica/claude_copilot/empirica.db "VACUUM;"

# Archive old sessions
# Note: archive-sessions command is planned for future release
# For now, use manual export and cleanup:

# Export old sessions to JSON
mkdir -p archive/sessions/
empirica sessions-list --older-than 90d | while read session_id; do
  empirica sessions-export "$session_id" > "archive/sessions/${session_id}.json"
done

# Clean archived records from database
sqlite3 .empirica/claude_copilot/empirica.db \
  "DELETE FROM sessions WHERE created_at < datetime('now', '-90 days');"
```

### Automated Rotation

```bash
# Cron job for weekly maintenance
cat > /etc/cron.weekly/empirica_maintenance << 'EOF'
#!/bin/bash
cd /path/to/empirica

# Archive reflex frames (manual - see above for commands)
find .empirica/*/reflex_frames/ -type f -mtime +7 -exec gzip {} \;

# Clean old sessions (manual - see above for commands)  
# Export sessions first, then delete from DB

# Vacuum database
sqlite3 .empirica/*/empirica.db "VACUUM; REINDEX; ANALYZE;"

# Generate weekly report
empirica report --window 7d --email team@company.com
EOF

chmod +x /etc/cron.weekly/empirica_maintenance
```

---

## Debugging with Logs

### Debug Failed Assessments

```bash
# Find failed assessments
# Note: 'query' command is planned for future release
sqlite3 .empirica/*/empirica.db "
  SELECT * FROM assessments 
  WHERE recommendation = 'ERROR' 
  ORDER BY created_at DESC 
  LIMIT 10
"

# View full session context
empirica sessions-show <session_id>

# Check reflex frames (manual inspection)
# Reflex frames are stored in .empirica/*/reflex_frames/
```

### Trace Cascade Flow

```bash
# Follow cascade through all 3 formats

# 1. Database record
# Note: Use sqlite3 directly for now
sqlite3 .empirica/*/empirica.db "SELECT * FROM cascades WHERE cascade_id = '<cascade_id>'"

# 2. Session JSON
empirica sessions-show <session_id>

# 3. Reflex frames (manual inspection)
# Check .empirica/*/reflex_frames/ directory
ls -la .empirica/*/reflex_frames/ | grep <cascade_id>
```

### Investigation Analysis

```bash
# Use the investigate command with a target
empirica investigate <file_or_directory>

# Example: Investigate a specific file
empirica investigate auth.py --context "security review"

# View investigation results in session database
empirica sessions-list --recent 10
empirica sessions-show <session_id>
```

---

## Custom Logging

### Python API

```python
from empirica.auto_tracker import track_cascade
import logging

# Configure Python logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('empirica_custom.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('empirica.custom')

# Use with auto-tracking
@track_cascade(task_name="custom_task", ai_id="my_agent")
def my_function(context):
    logger.info("Starting custom task")
    
    # Your logic here
    result = process_task(context)
    
    logger.debug(f"Intermediate result: {result}")
    
    return result
```

### Custom Reflex Frames

```python
from empirica.data.reflex_frame_logger import ReflexFrameLogger

logger = ReflexFrameLogger(ai_id="my_agent")

# Log custom frame
logger.log_custom_frame(
    frame_type="custom_analysis",
    cascade_id="cascade_123",
    data={
        "analysis_type": "security_scan",
        "findings": ["issue1", "issue2"],
        "severity": "high"
    }
)
```

---

## Log Analysis Tools

### Generate Reports

```bash
# Weekly summary report
empirica report --type weekly --window 7d --format pdf

# Investigation effectiveness report
empirica report --type investigation-effectiveness --window 30d

# Uncertainty trends report
empirica report --type uncertainty-trends --window 90d

# Custom report
empirica report --custom report_template.yaml --output custom_report.html
```

### Visualization

```bash
# Generate charts
empirica visualize --metric investigation-rate --window 30d --output chart.png

# Uncertainty heatmap
empirica visualize --metric uncertainty-heatmap --window 7d

# Vector correlations
empirica visualize --metric vector-correlations --window 30d
```

---

## Best Practices

### Production Logging

✅ **DO:**
- Enable all 3 formats (SQLite + JSON + Reflex)
- Set appropriate log levels (INFO in production)
- Archive old logs regularly
- Monitor disk usage
- Encrypt sensitive logs
- Backup database weekly
- Use structured logging

❌ **DON'T:**
- Disable auto-tracking in production
- Let logs grow unbounded
- Log sensitive data (PII, secrets)
- Use DEBUG level in production
- Ignore failed assessments
- Skip monitoring setup

### Development Logging

✅ **DO:**
- Use DEBUG level
- Enable verbose mode
- Watch reflex frames live
- Query database frequently
- Test archival strategy
- Validate log rotation

### Monitoring Strategy

1. **Real-time:** Tmux dashboard for active monitoring
2. **Daily:** Check investigation rate, avg Δuncertainty
3. **Weekly:** Review performance metrics, archive logs
4. **Monthly:** Analyze trends, tune thresholds
5. **Quarterly:** Comprehensive audit, capacity planning

---

## Troubleshooting

### Logs Not Writing

```bash
# Check permissions
ls -la .empirica/
ls -la .empirica_reflex_logs/

# Check disk space
df -h

# Verify auto-tracking enabled
echo $EMPIRICA_AUTO_TRACK

# Test logging
empirica test-logging
```

### Database Errors

```bash
# Check database integrity
sqlite3 .empirica/*/empirica.db "PRAGMA integrity_check;"

# Rebuild indices
sqlite3 .empirica/*/empirica.db "REINDEX; ANALYZE;"

# Backup and recreate
cp empirica.db empirica.db.backup
empirica session-create --level standard
```

### Missing Reflex Frames

```bash
# Verify path
echo $EMPIRICA_REFLEX_PATH

# Check recent cascades
# View recent reflex frames
ls -lt .empirica/*/reflex_frames/*.json | head -5

# Test frame writing
empirica test-reflex-logging

# Check for archival
ls .empirica_reflex_logs/archive/
```

---

## Next Steps

- **Configuration:** See `15_CONFIGURATION.md`
- **Archival Strategy:** See `REFLEX_FRAME_ARCHIVAL_STRATEGY.md`
- **Dashboard:** See `11_DASHBOARD_MONITORING.md`
- **Troubleshooting:** See `21_TROUBLESHOOTING.md`

---

**Last Updated:** 2025-10-29  
**Version:** 2.0
