# Reasoning Reconstruction Examples

**Purpose:** Practical scripts demonstrating how to use Empirica's existing logs and database for reasoning reconstruction and knowledge transfer.

**No additional dependencies required** - These scripts work with Empirica v2.0 core components only.

---

## Overview

Empirica already provides everything needed for reasoning reconstruction:
- ✅ Temporal snapshots (reflex logs - JSON files)
- ✅ Structured database (SQLite with epistemic data)
- ✅ Delta calculations (learning measurement)
- ✅ Export/import capabilities

**These examples show you how to:**
1. Reconstruct reasoning from completed sessions
2. Extract learning patterns and key insights
3. Transfer knowledge between AI agents
4. Analyze calibration and decision points

---

## Examples

### Example 1: Basic Reasoning Reconstruction

**File:** `01_basic_reconstruction.sh`

**What it does:**
- Extracts epistemic snapshots from database
- Finds reflex log files
- Calculates learning deltas
- Identifies key learning moments
- Generates summary report

**Usage:**
```bash
# Find recent sessions
./01_basic_reconstruction.sh

# Analyze specific session
./01_basic_reconstruction.sh session_abc123
```

**Output:**
```
reasoning_analysis_session_abc123/
├── reflex_log_files.txt       # Locations of reflex logs
├── cascades_data.json          # Cascade details from database
├── learning_timeline.json      # Temporal progression
├── learning_deltas.json        # Overall learning metrics
├── key_learning_moments.json   # Significant changes (|delta| > 0.2)
└── summary_report.txt          # Executive summary
```

**When to use:**
- Understanding what an AI learned
- Auditing decision points
- Analyzing learning trajectories
- Identifying knowledge gaps

---

### Example 2: Knowledge Transfer

**File:** `02_knowledge_transfer.py`

**What it does:**
- Exports knowledge package from completed session
- Filters for significant learning (configurable delta threshold)
- Converts to learning context (markdown)
- Prepares for import by another AI

**Usage:**
```bash
# Export knowledge from AI-A's session
python3 02_knowledge_transfer.py export session_ai_a

# Convert to learning context for AI-B
python3 02_knowledge_transfer.py import knowledge_package_session_ai_a.json

# AI-B can now read learning_context_*.md as study material
```

**Output:**
```
knowledge_package_session_ai_a.json       # Structured knowledge
learning_context_session_ai_a.md          # Human/AI-readable context
```

**Knowledge Package Format:**
```json
{
  "format": "empirica_knowledge_package_v1",
  "exported_from_session": "session_ai_a",
  "key_learnings": [
    {
      "topic": "CASCADE testing methodology",
      "epistemic_progression": {
        "initial_state": {"know": 0.10, "uncertainty": 0.80},
        "final_state": {"know": 0.75, "uncertainty": 0.30},
        "deltas": {"know": +0.65, "uncertainty": -0.50}
      },
      "calibration_pattern": {
        "well_calibrated": true
      }
    }
  ],
  "reasoning_patterns": [
    {
      "pattern": "investigation_strategy",
      "recommendation": "Investigate when uncertainty > 0.7"
    }
  ]
}
```

**When to use:**
- Accelerating onboarding for new AI agents
- Sharing expertise across AI team
- Documenting organizational knowledge
- Creating training materials

---

## Advanced Queries

### Query 1: Find High-Uncertainty Decisions

**Using SQLite directly:**
```sql
SELECT 
    cascade_id,
    task,
    final_confidence,
    investigation_rounds
FROM cascades
WHERE final_confidence > 0.6  -- Proceeded despite uncertainty
  AND investigation_rounds >= 2  -- Required investigation
ORDER BY final_confidence DESC;
```

**When to use:** Audit critical decisions made under uncertainty

---

### Query 2: Identify Learning Patterns

**Using SQLite:**
```sql
SELECT 
    ea1.cascade_id,
    c.task,
    (ea2.know_score - ea1.know_score) as know_delta,
    (ea2.uncertainty_score - ea1.uncertainty_score) as unc_delta
FROM epistemic_assessments ea1
JOIN epistemic_assessments ea2 ON ea1.cascade_id = ea2.cascade_id
JOIN cascades c ON ea1.cascade_id = c.cascade_id
WHERE ea1.phase = 'preflight'
  AND ea2.phase = 'postflight'
  AND ABS(ea2.know_score - ea1.know_score) > 0.3  -- Significant learning
ORDER BY know_delta DESC;
```

**When to use:** Find most impactful learning experiences

---

### Query 3: Calibration Analysis

**Using SQLite:**
```sql
SELECT 
    calibration_status,
    COUNT(*) as count,
    AVG(final_confidence) as avg_confidence
FROM cascades
WHERE calibration_status IS NOT NULL
GROUP BY calibration_status;
```

**When to use:** Assess overall calibration quality

---

## Integration with Reflex Logs

### Finding Reflex Logs for a Session

**Structure:**
```
.empirica_reflex_logs/
└── <agent_id>/
    └── <date>/
        ├── <agent>_<phase>_<timestamp>.json
        ├── <agent>_<phase>_<timestamp>.json
        └── ...
```

**Extracting reasoning text:**
```bash
# Find all reflex logs for a session
find .empirica_reflex_logs -name "*.json" -newer <start_time> | \
    xargs grep -l "<session_id>"

# Extract reasoning from logs
cat <reflex_log>.json | jq -r '.reasoning_text'

# Get epistemic vectors
cat <reflex_log>.json | jq '.epistemic_vectors'
```

**When to use:** Deep reasoning analysis, temporal trail verification

---

## Privacy Considerations

### Anonymizing Knowledge Packages

**Export with anonymization:**
```bash
# In 02_knowledge_transfer.py, use anonymize=True
python3 02_knowledge_transfer.py export session_abc123 package.json 0.3 --anonymize
```

**What gets removed:**
- Session IDs
- AI identifiers
- Task-specific content (if sensitive)

**What's preserved:**
- Epistemic deltas
- Learning patterns
- Calibration metrics
- Reasoning structures

**When to use:** Sharing knowledge across organizations, publishing research

---

## Use Cases

### 1. Medical AI Auditing

**Scenario:** Hospital audits AI treatment recommendation

**Process:**
```bash
# 1. Reconstruct reasoning
./01_basic_reconstruction.sh medical_ai_session_20251110

# 2. Review decision timeline
cat reasoning_analysis_*/learning_timeline.json | \
    jq '.[] | select(.uncertainty > 0.7)'

# 3. Check calibration
cat reasoning_analysis_*/learning_deltas.json | \
    jq '.deltas | {confidence, uncertainty}'
```

**Result:** Complete audit trail with timestamps, uncertainty levels, and reasoning progression

---

### 2. Multi-AI Team Knowledge Sharing

**Scenario:** 5 AI agents working on different system components

**Process:**
```bash
# AI-1 completes authentication module
python3 02_knowledge_transfer.py export ai1_auth_session

# AI-2 about to start on related security module
python3 02_knowledge_transfer.py import knowledge_package_ai1_auth.json

# AI-2 reads learning_context_*.md before starting
# (Provides context but AI-2 still needs to learn)
```

**Result:** Accelerated learning, shared expertise, organizational knowledge capture

---

### 3. Research: Epistemic Patterns

**Scenario:** Studying AI learning patterns

**Process:**
```bash
# Export multiple sessions
for session in session_*; do
    ./01_basic_reconstruction.sh $session
done

# Analyze patterns
cat reasoning_analysis_*/learning_deltas.json | \
    jq -s '[.[] | .deltas]' | \
    jq 'group_by(.know > 0) | map({group: .[0].know > 0, count: length})'
```

**Result:** Statistical analysis of learning patterns

---

## Extending These Examples

### Adding Semantic Search (Future)

**If you implement the semantic extension:**

```python
# Current: Manual jq filtering
cat timeline.json | jq '.[] | select(.task | contains("temporal"))'

# Future: Semantic search
empirica query-reasoning "temporal separation" --session session_abc
```

**The data is already there** - semantic search just adds a query layer

---

### Custom Analysis Scripts

**Template:**
```python
from empirica.data.session_database import SessionDatabase
import json

db = SessionDatabase()
cursor = db.conn.cursor()

# Your custom query
cursor.execute("""
    -- Your SQL here
""")

results = cursor.fetchall()

# Your analysis
# ...

db.close()
```

---

## Testing These Examples

### Quick Test

**1. Create a test session:**
```bash
cd /home/yogapad/empirical-ai/empirica
source .venv-empirica/bin/activate

# Bootstrap a session
empirica bootstrap --ai-id test-agent

# Note the session_id
```

**2. Run reconstruction:**
```bash
cd examples/reasoning_reconstruction
./01_basic_reconstruction.sh <session_id>
```

**3. Verify output:**
```bash
ls reasoning_analysis_<session_id>/
cat reasoning_analysis_<session_id>/summary_report.txt
```

---

## Requirements

**Core Empirica only:**
- Python 3.8+
- SQLite3 (built-in)
- jq (for JSON parsing in bash scripts)

**No additional dependencies:**
- ✅ No vector databases
- ✅ No embedding models
- ✅ No external services

**Installation:**
```bash
# Empirica already installed
cd /home/yogapad/empirical-ai/empirica

# Install jq (if not present)
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS
```

---

## Troubleshooting

### "No sessions found"

**Problem:** Database is empty

**Solution:**
```bash
# Create a session first
empirica bootstrap --ai-id my-agent

# Or check database location
ls .empirica/sessions/sessions.db
```

---

### "Reflex logs not found"

**Problem:** Reflex logging may not be enabled

**Solution:**
```bash
# Check if directory exists
ls .empirica_reflex_logs/

# If not, reflex logging is disabled
# Sessions can still be reconstructed from database
```

---

### "No significant learning found"

**Problem:** Delta threshold too high

**Solution:**
```bash
# Lower the threshold
python3 02_knowledge_transfer.py export session_abc 0.1  # Instead of default 0.3
```

---

## Future Enhancements

**These examples demonstrate the foundation.** When semantic extension is added:

- `empirica query-reasoning` - Semantic search over reasoning
- `empirica visualize-learning` - Learning curve visualization
- `empirica compare-sessions` - Cross-session pattern analysis
- `empirica audit-decision` - Automated decision reconstruction

**But the core functionality works today!**

---

## Questions?

**Core Empirica:** See main documentation (`../docs/README.md`)  
**Semantic Extension:** See `../docs/production/SEMANTIC_REASONING_EXTENSION.md`  
**Issues:** Check database with `sqlite3 .empirica/sessions/sessions.db`

---

## Summary

**What works now:**
- ✅ Reasoning reconstruction from database + logs
- ✅ Learning delta calculation
- ✅ Knowledge package export/import
- ✅ Manual semantic analysis (jq, SQL, python)

**What these examples prove:**
- Everything needed for reasoning reconstruction already exists
- No semantic layer required for basic use
- Semantic extension would add convenience, not capability

**Ready to use Empirica v2.0 for reasoning reconstruction today!** 🚀
