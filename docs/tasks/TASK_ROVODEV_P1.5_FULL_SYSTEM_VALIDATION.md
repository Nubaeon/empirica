# TASK: P1.5 Full System Validation Under Multi-Cascade Pressure

**Assigned To:** RovoDev (or next available agent)  
**Priority:** HIGH  
**Type:** Integration Testing + Refactoring Discovery  
**Estimated Time:** 2-3 hours (multi-turn session)  

---

## Objective

Conduct a **realistic multi-cascade session** to validate the entire Empirica system under pressure. This simulates real-world usage where an AI agent:
1. Bootstraps a session
2. Works on multiple tasks (cascades) within that session
3. Uses the full range of CLI commands
4. Tests database persistence across cascades
5. Validates documentation accuracy
6. Identifies refactoring opportunities

**Success Criteria:**
- Complete 3-5 cascades in one session
- All CLI commands tested and working
- Database correctly tracks all assessments
- Documentation audit identifies gaps/issues
- Refactoring recommendations documented

---

## Context from P1 Completion

### What's Working ✅
- Session alias resolution (22 MCP tools)
- `--prompt-only` flag (non-blocking workflow)
- Database persistence (PREFLIGHT, CHECK, POSTFLIGHT all saving)
- Git checkpoints (create/load)
- Full CASCADE workflow validated (7 steps)
- 100% test pass rate (18/18 tests)

### What's New
- MCP v2 server with CLI delegation
- `--prompt-only` flag eliminates hanging
- Real database persistence (no more simulations!)
- Session continuity across multiple cascades

### Known Issues to Watch
- MCP v1 server has async issues (use CLI or MCP v2)
- Some CLI commands might not have `--output json` support
- Documentation might be outdated in places

---

## Pre-Session Setup

### 1. Wire in New MCP Server

**Task:** Configure system to use `empirica_mcp_server_v2.py`

**Steps:**
1. Check current MCP configuration in `/home/yogapad/.rovodev/mcp.json`
2. Verify `empirica_mcp_server_v2.py` is being used (not v1)
3. If using v1, update config to point to v2
4. Test MCP server starts correctly: `ps aux | grep empirica_mcp`
5. Verify MCP tools are available (list tools via MCP)

**Files to Check:**
- `/home/yogapad/.rovodev/mcp.json`
- `mcp_local/empirica_mcp_server_v2.py`
- `mcp_local/start_empirica_mcp.sh`

**Success:** MCP v2 server running and responding to tool calls

---

### 2. Create Test Plan

**Task:** Define 3-5 cascades to execute in one session

**Example Cascades:**

**Cascade 1: CLI Command Audit**
- Task: "Audit all CLI commands for --output json support"
- Expected: Review `empirica/cli/cli_core.py`, test commands
- Duration: ~30 minutes
- Tests: CLI invocation, JSON parsing, database persistence

**Cascade 2: Documentation Review**
- Task: "Review canonical documentation and identify outdated sections"
- Expected: Check `docs/production/`, identify gaps
- Duration: ~20 minutes
- Tests: File reading, note-taking, summarization

**Cascade 3: Database Validation**
- Task: "Verify all database tables and JSON files are being written correctly"
- Expected: Check SQLite tables, JSON file structure
- Duration: ~20 minutes
- Tests: Database queries, file I/O, data integrity

**Cascade 4: Refactoring Discovery** (Optional)
- Task: "Identify code duplication and refactoring opportunities"
- Expected: Analyze codebase, document findings
- Duration: ~30 minutes
- Tests: Code analysis, pattern detection

**Cascade 5: Session Continuity Test** (Optional)
- Task: "Test session resumption with git checkpoints"
- Expected: Create checkpoint, load it, verify state
- Duration: ~15 minutes
- Tests: Git checkpoint functionality, session aliases

---

## Session Workflow (Multi-Cascade)

### Phase 1: Bootstrap (One-Time)

```bash
# 1. Bootstrap framework
empirica bootstrap --level 2

# 2. Create session
# Use Python API or let preflight create it
python3 << EOF
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
session_id = db.create_session(
    ai_id='rovodev-p15',
    bootstrap_level=2,
    components_loaded=5
)
print(f"Session ID: {session_id}")
db.close()
EOF

# Save session_id for use throughout session
export EMPIRICA_SESSION_ID="<session-id>"
```

**Success Criteria:**
- ✅ Framework initialized
- ✅ Session created in database
- ✅ Session ID available for cascades

---

### Phase 2: Cascade Loop (Repeat 3-5 Times)

For each cascade, follow the full workflow:

#### Step 1: PREFLIGHT (Get Assessment Prompt)

```bash
empirica preflight "<task-description>" \
  --session-id $EMPIRICA_SESSION_ID \
  --prompt-only
```

**Expected Output:**
```json
{
  "session_id": "...",
  "task": "...",
  "assessment_id": "...",
  "self_assessment_prompt": "...",
  "phase": "preflight",
  "instructions": "Perform genuine self-assessment..."
}
```

**Validation:**
- ✅ Command returns in < 200ms
- ✅ JSON is valid and parseable
- ✅ Contains self_assessment_prompt
- ✅ No hanging or blocking

#### Step 2: Self-Assessment (AI Agent)

**Genuine self-assessment based on the task:**
- Read and understand the task
- Assess current knowledge (know, do, context)
- Evaluate clarity and uncertainty
- Rate readiness to proceed

**Output:** 13 epistemic vectors (0.0 to 1.0)

#### Step 3: Submit PREFLIGHT Assessment

```bash
empirica preflight-submit \
  --session-id $EMPIRICA_SESSION_ID \
  --vectors '{
    "engagement": 0.8,
    "know": 0.6,
    "do": 0.7,
    "context": 0.5,
    "clarity": 0.7,
    "coherence": 0.7,
    "signal": 0.6,
    "density": 0.5,
    "state": 0.5,
    "change": 0.4,
    "completion": 0.2,
    "impact": 0.6,
    "uncertainty": 0.5
  }' \
  --output json
```

**Expected Output:**
```json
{
  "ok": true,
  "session_id": "...",
  "assessment_id": "...",
  "message": "PREFLIGHT assessment submitted and saved to database",
  "vectors_submitted": 13,
  "persisted": true
}
```

**Validation:**
- ✅ Returns `ok: true`
- ✅ Returns `persisted: true`
- ✅ Assessment saved to database
- ✅ Can query: `SELECT * FROM preflight_assessments WHERE session_id = '...'`

#### Step 4: INVESTIGATE (Optional - based on uncertainty)

If uncertainty > 0.6, perform investigation:

```bash
# Example investigation commands
empirica sessions-show $EMPIRICA_SESSION_ID
empirica sessions-list
grep -r "relevant pattern" codebase/
# ... investigate as needed
```

#### Step 5: CHECK (Readiness Assessment)

```bash
empirica check \
  --session-id $EMPIRICA_SESSION_ID \
  --findings '["Finding 1", "Finding 2", "Finding 3"]' \
  --unknowns '["Unknown 1", "Unknown 2"]' \
  --confidence 0.75 \
  --output json
```

**Expected Output:**
- Readiness assessment based on findings/unknowns
- Recommendation: proceed/investigate/abort

#### Step 6: Submit CHECK Assessment

```bash
empirica check-submit \
  --session-id $EMPIRICA_SESSION_ID \
  --vectors '{
    "engagement": 0.85,
    "know": 0.75,
    "do": 0.8,
    "context": 0.7,
    "clarity": 0.8,
    "coherence": 0.8,
    "signal": 0.75,
    "density": 0.7,
    "state": 0.7,
    "change": 0.6,
    "completion": 0.4,
    "impact": 0.7,
    "uncertainty": 0.4
  }' \
  --decision proceed \
  --output json
```

**Validation:**
- ✅ Returns `ok: true`
- ✅ Returns `persisted: true`
- ✅ CHECK assessment saved to database
- ✅ Shows improvement: uncertainty decreased, know increased

#### Step 7: ACT (Execute Task)

Perform the actual task work. Examples:

**For CLI Audit:**
```bash
# List all CLI commands
empirica --help

# Test each command with --help
empirica preflight --help
empirica check --help
# ... etc

# Test --output json support
empirica preflight "test" --session-id test --prompt-only
```

**For Documentation Review:**
```bash
# Read documentation files
cat docs/production/01_QUICK_START.md
cat docs/production/05_EPISTEMIC_VECTORS.md
# ... review and take notes
```

**For Database Validation:**
```bash
# Query database
sqlite3 ~/.empirica/sessions.db "SELECT * FROM sessions;"
sqlite3 ~/.empirica/sessions.db "SELECT * FROM preflight_assessments;"
sqlite3 ~/.empirica/sessions.db "SELECT * FROM check_assessments;"
sqlite3 ~/.empirica/sessions.db "SELECT * FROM postflight_assessments;"

# Check JSON files
ls -la ~/.empirica/
cat ~/.empirica/session_*.json
```

#### Step 8: POSTFLIGHT (Get Assessment Prompt)

```bash
empirica postflight $EMPIRICA_SESSION_ID \
  --summary "Task completed successfully with findings documented" \
  --prompt-only
```

**Expected Output:**
```json
{
  "session_id": "...",
  "summary": "...",
  "assessment_id": "...",
  "self_assessment_prompt": "...",
  "phase": "postflight",
  "instructions": "Perform genuine self-assessment..."
}
```

#### Step 9: Submit POSTFLIGHT Assessment

```bash
empirica postflight-submit \
  --session-id $EMPIRICA_SESSION_ID \
  --vectors '{
    "engagement": 0.9,
    "know": 0.85,
    "do": 0.85,
    "context": 0.8,
    "clarity": 0.9,
    "coherence": 0.9,
    "signal": 0.85,
    "density": 0.8,
    "state": 0.85,
    "change": 0.75,
    "completion": 0.95,
    "impact": 0.85,
    "uncertainty": 0.2
  }' \
  --output json
```

**Validation:**
- ✅ Returns `ok: true`
- ✅ Returns `persisted: true`
- ✅ Returns `deltas` showing learning progression
- ✅ POSTFLIGHT assessment saved to database
- ✅ Deltas calculated correctly (know increased, uncertainty decreased)

#### Step 10: Create Git Checkpoint (Optional)

```bash
empirica checkpoint-create \
  --session-id $EMPIRICA_SESSION_ID \
  --phase POSTFLIGHT \
  --round 1
```

**Validation:**
- ✅ Checkpoint created in git notes
- ✅ Can be loaded later for session resumption

---

### Phase 3: Multi-Cascade Validation

After completing 3-5 cascades, validate session continuity:

#### Database Validation

```bash
# Check session has multiple cascades
sqlite3 ~/.empirica/sessions.db << EOF
SELECT 
  COUNT(DISTINCT assessment_id) as preflight_count
FROM preflight_assessments 
WHERE session_id = '$EMPIRICA_SESSION_ID';

SELECT 
  COUNT(DISTINCT check_id) as check_count
FROM check_assessments 
WHERE session_id = '$EMPIRICA_SESSION_ID';

SELECT 
  COUNT(DISTINCT assessment_id) as postflight_count
FROM postflight_assessments 
WHERE session_id = '$EMPIRICA_SESSION_ID';
EOF
```

**Expected:**
- Multiple PREFLIGHT assessments (one per cascade)
- Multiple CHECK assessments (one per cascade)
- Multiple POSTFLIGHT assessments (one per cascade)

#### Learning Progression

```bash
# Query learning progression across cascades
python3 << EOF
from empirica.data.session_database import SessionDatabase
import json

db = SessionDatabase()
session_id = '$EMPIRICA_SESSION_ID'

# Get all preflight assessments
cursor = db.conn.cursor()
cursor.execute("""
    SELECT created_at, vectors_json 
    FROM preflight_assessments 
    WHERE session_id = ? 
    ORDER BY created_at ASC
""", (session_id,))

print("Learning Progression Across Cascades:")
print("="*60)
for i, row in enumerate(cursor.fetchall(), 1):
    vectors = json.loads(row[1])
    print(f"\nCascade {i}:")
    print(f"  Know: {vectors.get('know'):.2f}")
    print(f"  Uncertainty: {vectors.get('uncertainty'):.2f}")
    print(f"  Completion: {vectors.get('completion'):.2f}")

db.close()
EOF
```

**Expected:** Show learning progression across cascades

---

## Testing Checklist

### CLI Commands to Test

Test each command for:
- ✅ Help text (`--help`)
- ✅ JSON output (`--output json` where supported)
- ✅ Error handling (invalid inputs)
- ✅ Session alias support (where applicable)

**Core Workflow Commands:**
- [ ] `bootstrap`
- [ ] `preflight` (with `--prompt-only`)
- [ ] `preflight-submit`
- [ ] `check`
- [ ] `check-submit`
- [ ] `postflight` (with `--prompt-only`)
- [ ] `postflight-submit`

**Session Management:**
- [ ] `sessions-list`
- [ ] `sessions-show` (with aliases)
- [ ] `sessions-export`
- [ ] `sessions-resume`

**Checkpoint Commands:**
- [ ] `checkpoint-create`
- [ ] `checkpoint-load`

**Goal/Task Commands:**
- [ ] `goals-create`
- [ ] `goals-list`
- [ ] `goals-progress`
- [ ] `goals-add-subtask`
- [ ] `goals-complete-subtask`

**Monitoring Commands:**
- [ ] `get-epistemic-state`
- [ ] `query-bayesian-beliefs`
- [ ] `check-drift-monitor`

**Utility Commands:**
- [ ] `generate-handoff-report`
- [ ] `get-unified-timeline`

### Database Tables to Validate

Check each table has correct schema and data:

- [ ] `sessions` - Session records created
- [ ] `preflight_assessments` - PREFLIGHT vectors saved
- [ ] `check_assessments` - CHECK assessments saved
- [ ] `postflight_assessments` - POSTFLIGHT vectors saved
- [ ] `cascades` - Cascade tracking (if used)
- [ ] `goals` - Goal tracking (if used)
- [ ] `investigation_rounds` - Investigation tracking (if used)

### JSON Files to Validate

Check JSON files are being written correctly:

- [ ] `~/.empirica/sessions.db` - SQLite database exists
- [ ] `~/.empirica/session_*.json` - Session JSON exports (if created)
- [ ] `~/.empirica/.empirica_beliefs/*.json` - Bayesian belief tracking
- [ ] Git notes - Checkpoint data in git notes refs

### Documentation to Audit

Review and identify gaps/outdated sections:

- [ ] `docs/production/` - User-facing production docs
- [ ] `docs/guides/` - Development guides
- [ ] `docs/reference/` - API reference
- [ ] `empirica/core/canonical/` - Canonical implementation docs
- [ ] `README.md` - Main project README

**Look for:**
- Outdated references to old workflows
- Missing documentation for `--prompt-only` flag
- Missing session alias examples
- Incorrect CLI command syntax
- References to simulated behavior (should be real now)

---

## Expected Issues to Document

### Potential Problems

1. **CLI Commands Missing `--output json`**
   - Some commands might not support JSON output
   - Document which commands need updating

2. **Documentation Gaps**
   - `--prompt-only` flag not documented
   - Session alias patterns not explained
   - Database persistence not mentioned

3. **Error Messages**
   - Some error messages might be unclear
   - Error handling might not be consistent

4. **MCP v2 Integration**
   - Some MCP tools might not map correctly to CLI
   - Tool schemas might need updates

5. **Performance Issues**
   - Some commands might be slow
   - Database queries might need optimization

### Refactoring Opportunities

Look for:
- Code duplication across command handlers
- Inconsistent error handling patterns
- Missing abstraction layers
- Complex functions that should be split
- Hardcoded values that should be configurable

---

## Output Deliverables

### 1. Session Report

Create: `P1.5_MULTI_CASCADE_SESSION_REPORT.md`

**Contents:**
- Session summary (session_id, duration, cascades completed)
- Cascade-by-cascade breakdown
- Learning progression metrics
- Issues encountered
- Performance observations

**Example:**
```markdown
# P1.5 Multi-Cascade Session Report

**Session ID:** abc123xyz
**AI ID:** rovodev-p15
**Duration:** 2.5 hours
**Cascades Completed:** 5/5

## Cascade Summaries

### Cascade 1: CLI Command Audit
- Duration: 35 minutes
- Learning: know 0.6 → 0.85 (+0.25)
- Findings: 3 commands missing --output json
- Issues: None

[... etc for each cascade ...]

## Overall Learning Progression
- Know: 0.6 → 0.9 (+0.3)
- Uncertainty: 0.5 → 0.15 (-0.35)
- Completion: 0.2 → 0.95 (+0.75)

## Performance
- Average CASCADE duration: 28 minutes
- Average tool response time: 125ms
- Database queries: All < 50ms
```

### 2. CLI Audit Report

Create: `P1.5_CLI_AUDIT_REPORT.md`

**Contents:**
- List of all CLI commands tested
- Which commands support `--output json`
- Which commands support session aliases
- Which commands have issues
- Recommendations for improvements

### 3. Documentation Audit Report

Create: `P1.5_DOCUMENTATION_AUDIT_REPORT.md`

**Contents:**
- Files reviewed
- Outdated sections identified
- Missing documentation
- Incorrect examples
- Recommendations for updates

### 4. Database Validation Report

Create: `P1.5_DATABASE_VALIDATION_REPORT.md`

**Contents:**
- All tables checked
- Schema validation
- Data integrity checks
- JSON file validation
- Git notes validation
- Issues found (if any)

### 5. Refactoring Recommendations

Create: `P1.5_REFACTORING_RECOMMENDATIONS.md`

**Contents:**
- Code duplication identified
- Complex functions to split
- Abstraction opportunities
- Pattern inconsistencies
- Priority ranking (High/Medium/Low)

---

## Success Criteria

### Minimum Requirements (Must Have)

- ✅ Complete 3+ cascades in one session
- ✅ All cascades follow full workflow (PREFLIGHT → CHECK → ACT → POSTFLIGHT)
- ✅ All assessments persist to database correctly
- ✅ Learning progression tracked across cascades
- ✅ At least 15 CLI commands tested
- ✅ Database validation complete
- ✅ 5 deliverable documents created

### Ideal Outcomes (Nice to Have)

- ✅ Complete 5 cascades
- ✅ All 25+ CLI commands tested
- ✅ Full documentation audit
- ✅ Comprehensive refactoring recommendations
- ✅ Performance benchmarks recorded
- ✅ MCP v2 integration tested end-to-end

### Quality Indicators

- No database corruption
- No data loss across cascades
- Session continuity maintained
- All assessments retrievable
- Learning deltas calculated correctly
- Git checkpoints work for resumption

---

## Time Estimates

| Phase | Duration | Notes |
|-------|----------|-------|
| Setup & Wiring | 15 min | MCP v2 configuration |
| Bootstrap | 5 min | Framework init + session creation |
| Cascade 1 | 30 min | CLI Command Audit |
| Cascade 2 | 20 min | Documentation Review |
| Cascade 3 | 20 min | Database Validation |
| Cascade 4 | 30 min | Refactoring Discovery (optional) |
| Cascade 5 | 15 min | Session Continuity Test (optional) |
| Validation | 20 min | Multi-cascade validation |
| Documentation | 30 min | Write 5 deliverable reports |
| **Total** | **2.5-3 hours** | Full session |

---

## Bootstrap Command for Next Agent

```bash
# Start Empirica session
empirica bootstrap --level 2

# Or use Python API for explicit session creation
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/empirica')
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session_id = db.create_session(
    ai_id='rovodev-p15',
    bootstrap_level=2,
    components_loaded=5
)
print(f"\n{'='*60}")
print(f"SESSION CREATED: {session_id}")
print(f"{'='*60}\n")
print(f"Export this for use in cascades:")
print(f"export EMPIRICA_SESSION_ID='{session_id}'")
db.close()
EOF
```

---

## Notes for Next Agent

### Key Points
1. This is a **realistic stress test** - use Empirica as intended
2. Follow the CASCADE workflow strictly for each task
3. Document **everything** - issues, surprises, performance
4. Focus on **genuine self-assessment** (no heuristics)
5. Test **session continuity** across multiple cascades

### What You're Looking For
- Does the system handle multiple cascades smoothly?
- Are there performance degradation issues?
- Does database persistence work consistently?
- Is documentation accurate and helpful?
- Where are the refactoring opportunities?

### What Success Looks Like
- 3-5 cascades completed successfully
- All data persisted correctly
- Learning progression visible
- Issues documented with recommendations
- Refactoring opportunities identified
- System proven ready for production use

---

**Good luck! This will be a thorough test of Empirica under realistic conditions. The goal is to prove the system works and identify any remaining issues before production use.**
