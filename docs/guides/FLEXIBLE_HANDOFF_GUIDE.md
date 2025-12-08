# Flexible Epistemic Handoff Guide

**Status:** Implemented ✅  
**Date:** 2025-12-08  
**Version:** 1.0

## Overview

Empirica now supports **three types of epistemic handoffs** to enable flexible multi-agent coordination and workflow patterns.

## Handoff Types

### 1. Investigation Handoff (PREFLIGHT → CHECK)

**Use case:** Specialist handoff after investigation phase

**Workflow:**
```bash
AI-1 (Investigator):
  empirica preflight → investigate → check → handoff-create

AI-2 (Executor):
  empirica handoff-query → act → postflight
```

**Epistemic deltas:** PREFLIGHT → CHECK (learning from investigation)

**Example scenarios:**
- Architecture review → Implementation
- Security audit → Remediation  
- Feasibility study → Execution
- Code exploration → Refactoring

### 2. Complete Handoff (PREFLIGHT → POSTFLIGHT)

**Use case:** Full workflow completion

**Workflow:**
```bash
AI-1:
  empirica preflight → work → postflight → handoff-create

AI-2:
  empirica handoff-query → start new work
```

**Epistemic deltas:** PREFLIGHT → POSTFLIGHT (full cycle learning)

**Example scenarios:**
- Feature implementation complete
- Bug fix verified
- Documentation updated
- Session fully complete

### 3. Planning Handoff (No assessments)

**Use case:** Documentation-only handoff

**Workflow:**
```bash
empirica handoff-create --planning-only --session-id <id> [args]
```

**Epistemic deltas:** None (documentation only)

**Example scenarios:**
- Planning documents
- Design decisions
- Meeting notes
- Context sharing without CASCADE workflow

## CLI Usage

The CLI **auto-detects** handoff type based on available assessments:

```bash
# Auto-detects type based on what exists
empirica handoff-create \
  --session-id <SESSION_ID> \
  --task-summary "What was accomplished" \
  --key-findings '["Finding 1", "Finding 2"]' \
  --remaining-unknowns '["Unknown 1"]' \
  --next-session-context "Context for next AI" \
  --output json
```

**Detection logic:**
1. If `--planning-only` flag → Planning handoff
2. If PREFLIGHT + POSTFLIGHT exist → Complete handoff
3. If PREFLIGHT + CHECK exist → Investigation handoff
4. Otherwise → Error (need at least PREFLIGHT + CHECK or --planning-only)

## Output Format

All handoff types return:

```json
{
  "ok": true,
  "session_id": "...",
  "handoff_type": "investigation|complete|planning",
  "handoff_subtype": "investigation|complete|planning",
  "epistemic_deltas": { /* PREFLIGHT→CHECK or PREFLIGHT→POSTFLIGHT */ },
  "epistemic_note": "PREFLIGHT → CHECK deltas (investigation phase)",
  "calibration_status": "well_calibrated|moderate|poor",
  "has_epistemic_deltas": true|false
}
```

## Multi-Agent Coordination Patterns

### Pattern 1: Parallel Investigation → Merge

```bash
# AI-1: Domain A investigation
AI1_SESSION=$(empirica session-create --ai-id investigator-1 --output json | jq -r .session_id)
empirica preflight --session-id $AI1_SESSION
# ... investigate domain A ...
empirica check --session-id $AI1_SESSION
empirica handoff-create --session-id $AI1_SESSION  # Investigation handoff

# AI-2: Domain B investigation  
AI2_SESSION=$(empirica session-create --ai-id investigator-2 --output json | jq -r .session_id)
empirica preflight --session-id $AI2_SESSION
# ... investigate domain B ...
empirica check --session-id $AI2_SESSION
empirica handoff-create --session-id $AI2_SESSION  # Investigation handoff

# AI-3: Merge and execute
empirica handoff-query --session-id $AI1_SESSION  # Get findings from AI-1
empirica handoff-query --session-id $AI2_SESSION  # Get findings from AI-2
# ... execute based on combined findings ...
```

### Pattern 2: Investigation → Execution Split

```bash
# Investigation specialist
INVEST_SESSION=$(empirica session-create --ai-id investigator --output json | jq -r .session_id)
empirica preflight --session-id $INVEST_SESSION
# ... thorough investigation ...
empirica check --session-id $INVEST_SESSION --confidence 0.75
empirica handoff-create --session-id $INVEST_SESSION  # Investigation handoff

# Execution specialist
EXEC_SESSION=$(empirica session-create --ai-id executor --output json | jq -r .session_id)
empirica handoff-query --session-id $INVEST_SESSION  # Get findings/unknowns
# ... implement based on investigation ...
empirica postflight --session-id $EXEC_SESSION
```

## Benefits

### ✅ Multi-Agent Coordination
- Investigation specialists can hand off to execution specialists
- Clear separation of concerns (research vs implementation)
- Epistemic state preserved across specialists

### ✅ Parallel Work
- Multiple AIs can investigate different domains
- Findings/unknowns tracked separately
- Merge results without duplication

### ✅ Real Workflow Patterns
- Architecture reviews that lead to implementation
- Security audits that trigger remediation
- Feasibility studies that inform execution
- Long-running investigations with handoffs

### ✅ CHECK Already Captures State
- CHECK tracks uncertainty reduction through investigation
- Findings/unknowns explicitly recorded
- Decision point for proceed vs investigate more

## Querying Handoffs

Query any handoff type the same way:

```bash
# Query by session
empirica handoff-query --session-id <SESSION_ID> --output json

# Query by AI (all handoffs from that AI)
empirica handoff-query --ai-id <AI_ID> --limit 5 --output json
```

**Returns:**
- `handoff_subtype`: "investigation" | "complete" | "planning"
- `epistemic_deltas`: Learning from investigation or full cycle
- `key_findings`: Validated knowledge
- `remaining_unknowns`: Investigation breadcrumbs
- `next_session_context`: Critical context for next AI

## Implementation Details

### Code Changes
- `empirica/cli/command_handlers/handoff_commands.py`: Added handoff type detection
- `empirica/core/handoff/report_generator.py`: Support flexible start/end assessments
- `empirica/data/session_database.py`: Uses existing `get_check_phase_assessments()`

### Storage
All handoff types stored identically:
- Git notes: `refs/notes/empirica/handoff/{session_id}`
- Database: `handoff_reports` table (if exists)
- Token efficient: ~200-600 tokens (98.8% reduction)

## Examples

See test results in commit `f61289eb`:
- Complete handoff test: Session `fe10d107-5d60-4615-8b5d-01c6dba4aa97`
- Investigation handoff test: Session `79056dbf-ede3-4c94-9fdd-70071a9e10b2`

Both tests passing ✅
