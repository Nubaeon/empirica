# Auto Issue Capture System - User Guide

## Overview

The Auto Issue Capture System enables AIs to capture bugs, errors, warnings, and other issues **automatically during work** without interrupting flow state. Issues can be handed off to other AIs with full context.

### Key Benefits

1. **Maintain Flow State** - Continue working while issues are captured in background
2. **Seamless Handoff** - Pass issues to other AIs with complete context
3. **Pattern Discovery** - Identify common issues across sessions
4. **Audit Trail** - Track what issues occurred, when, and how they were resolved

---

## Quick Start

### 1. Capturing Issues in Code

```python
from empirica.core.issue_capture import get_auto_capture

# Initialize once per session
auto_capture = get_auto_capture()

# Capture an error without raising
issue_id = auto_capture.capture_error(
    message="Database query timeout",
    severity=IssueSeverity.HIGH,
    category=IssueCategory.ERROR
)

# Capture a warning
auto_capture.capture_warning(
    message="Slow API response (2.3s)",
    category=IssueCategory.PERFORMANCE
)

# Capture incomplete work
auto_capture.capture_todo(
    description="Optimize query performance",
    priority="high"
)
```

### 2. List Captured Issues

```bash
# List all new issues
empirica issue-list \
  --session-id <SESSION_ID> \
  --status new

# List high-severity issues
empirica issue-list \
  --session-id <SESSION_ID> \
  --severity high

# Show in human-readable format
empirica issue-list \
  --session-id <SESSION_ID> \
  --output human
```

### 3. Show Issue Details

```bash
empirica issue-show \
  --session-id <SESSION_ID> \
  --issue-id <ISSUE_ID>
```

### 4. Hand Off to Another AI

```bash
# Mark issue for another AI to work on
empirica issue-handoff \
  --session-id <SESSION_ID> \
  --issue-id <ISSUE_ID> \
  --assigned-to other-ai-name

# Export all handoff issues
empirica issue-export \
  --session-id <SESSION_ID> \
  --assigned-to other-ai-name > /tmp/issues_for_other_ai.json
```

### 5. Resolve Issues

```bash
empirica issue-resolve \
  --session-id <SESSION_ID> \
  --issue-id <ISSUE_ID> \
  --resolution "Fixed by applying patch X"
```

---

## Integration Patterns

### Pattern 1: Try-Except without Raising

When you want to log an error but continue working:

```python
from empirica.core.issue_capture import get_auto_capture, IssueSeverity, IssueCategory

auto_capture = get_auto_capture()

try:
    result = risky_operation()
except Exception as e:
    # Capture but don't raise
    auto_capture.capture_error(
        message=f"Risky operation failed: {str(e)}",
        severity=IssueSeverity.MEDIUM,
        category=IssueCategory.ERROR,
        exc_info=e
    )
    # Continue with fallback
    result = fallback_operation()
```

### Pattern 2: Assertion Monitoring

Instead of failing fast, capture assertions and continue:

```python
auto_capture = get_auto_capture()

# Your assertion
if not precondition_met:
    auto_capture.capture_assertion_failure(
        condition="precondition_met",
        message="Unexpected state detected but continuing",
        severity=IssueSeverity.MEDIUM
    )
```

### Pattern 3: Performance Monitoring

Capture performance issues automatically:

```python
import time

auto_capture = get_auto_capture()

start = time.time()
result = slow_operation()
elapsed = (time.time() - start) * 1000  # Convert to ms

if elapsed > 1000:  # If > 1 second
    auto_capture.capture_performance_issue(
        operation="slow_operation",
        actual_ms=elapsed,
        expected_ms=500
    )
```

### Pattern 4: TODO Tracking

Mark incomplete work for later without creating context switches:

```python
auto_capture = get_auto_capture()

# You notice something that needs work
auto_capture.capture_todo(
    description="Optimize database schema - add indexes on user_id, created_at",
    priority="high"
)

# Continue current work
```

---

## Issue Categories

| Category | Use Case |
|----------|----------|
| **BUG** | Code defect or logic error |
| **ERROR** | Runtime exception or failure |
| **WARNING** | Potential problem detected |
| **DEPRECATION** | Deprecated API or pattern used |
| **TODO** | Incomplete work to do later |
| **PERFORMANCE** | Performance degradation detected |
| **COMPATIBILITY** | Platform or version incompatibility |
| **DESIGN** | Architectural or design issue |
| **OTHER** | Doesn't fit other categories |

---

## Issue Severity Levels

| Severity | Meaning |
|----------|---------|
| **BLOCKER** | Prevents work from continuing |
| **HIGH** | Significantly impacts work |
| **MEDIUM** | Notable but workaround exists |
| **LOW** | Minor or cosmetic |

---

## Issue Lifecycle

```
NEW → INVESTIGATING → (RESOLVED or HANDOFF)
                   ↓
              WONTFIX (if intentional)
```

### Statuses

- **NEW**: Just captured, needs triage
- **INVESTIGATING**: AI is working on it
- **HANDOFF**: Ready for another AI
- **RESOLVED**: Fixed and verified
- **WONTFIX**: Intentional, won't fix (documented reason)

---

## Multi-AI Workflow Example

### AI-1 Session: Implementing Feature X

```bash
# AI-1 starts session
SESSION_ID=$(empirica session-create --ai-id ai-worker-1 | jq -r '.session_id')

# AI-1 encounters performance issue during development
auto_capture.capture_performance_issue(...)

# After 2 hours, AI-1 reaches memory limit
# Mark performance issue for AI-2 to optimize
empirica issue-handoff \
  --session-id $SESSION_ID \
  --issue-id <PERF_ISSUE_ID> \
  --assigned-to ai-optimizer

# Export all handoff issues
empirica issue-export \
  --session-id $SESSION_ID \
  --assigned-to ai-optimizer > /tmp/handoff.json
```

### AI-2 Session: Optimization Work

```bash
# AI-2 starts session
SESSION_ID_2=$(empirica session-create --ai-id ai-optimizer | jq -r '.session_id')

# AI-2 imports issues from AI-1
# (This would be implemented as: empirica issue-import /tmp/handoff.json)

# AI-2 works on each issue
empirica issue-list --session-id $SESSION_ID_2 --status handoff

# For each issue:
# 1. Show details
empirica issue-show --session-id $SESSION_ID_2 --issue-id <ISSUE_ID>

# 2. Work on it
# ... implementation ...

# 3. Mark as resolved
empirica issue-resolve \
  --session-id $SESSION_ID_2 \
  --issue-id <ISSUE_ID> \
  --resolution "Optimized query index, 10x speedup"
```

---

## Database Schema

Issues are stored in the `auto_captured_issues` table:

```sql
CREATE TABLE auto_captured_issues (
    id TEXT PRIMARY KEY,                    -- UUID
    session_id TEXT NOT NULL,               -- Session this was captured in
    severity TEXT NOT NULL,                 -- blocker, high, medium, low
    category TEXT NOT NULL,                 -- bug, error, warning, etc
    code_location TEXT,                     -- file:line where issue occurred
    message TEXT NOT NULL,                  -- Human-readable description
    stack_trace TEXT,                       -- Full stack trace if applicable
    context TEXT,                           -- JSON with local variables, state
    status TEXT DEFAULT 'new',              -- new, investigating, handoff, resolved, wontfix
    assigned_to_ai TEXT,                    -- AI ID if handed off
    root_cause_id TEXT,                     -- ID of related root cause issue
    resolution TEXT,                        -- How it was resolved
    created_at TIMESTAMP,                   -- When captured
    updated_at TIMESTAMP                    -- Last modified
);
```

---

## Command Reference

### issue-list
List captured issues with filtering

```bash
empirica issue-list \
  --session-id <SESSION_ID> \
  [--status new|investigating|handoff|resolved|wontfix] \
  [--category bug|error|warning|deprecation|todo|performance|compatibility|design|other] \
  [--severity blocker|high|medium|low] \
  [--limit <N>] \
  [--output json|human]
```

### issue-show
Show detailed information about an issue

```bash
empirica issue-show \
  --session-id <SESSION_ID> \
  --issue-id <ISSUE_ID> \
  [--output json|human]
```

### issue-handoff
Mark issue for another AI to work on

```bash
empirica issue-handoff \
  --session-id <SESSION_ID> \
  --issue-id <ISSUE_ID> \
  --assigned-to <AI_ID> \
  [--output json|human]
```

### issue-resolve
Mark issue as resolved

```bash
empirica issue-resolve \
  --session-id <SESSION_ID> \
  --issue-id <ISSUE_ID> \
  --resolution "How was it fixed?" \
  [--output json|human]
```

### issue-export
Export issues for handoff to another AI

```bash
empirica issue-export \
  --session-id <SESSION_ID> \
  --assigned-to <AI_ID> \
  [--output json|human]
```

### issue-stats
Show statistics about captured issues

```bash
empirica issue-stats \
  --session-id <SESSION_ID> \
  [--output json|human]
```

---

## Best Practices

1. **Capture Early, Fix Later**
   - Don't let errors prevent you from continuing work
   - Capture them, mark for handoff if needed

2. **Use Appropriate Severity**
   - BLOCKER only for truly blocking issues
   - MEDIUM for issues with workarounds
   - LOW for cosmetic or future improvements

3. **Add Context**
   - Provide sufficient detail for another AI to pick up
   - Include what you tried and what didn't work

4. **Handoff at Natural Boundaries**
   - Hand off when you hit a logical stopping point
   - Not in the middle of complex operations

5. **Link Related Issues**
   - Use root_cause_id to link related issues
   - Helps identify patterns and systemic problems

---

## Troubleshooting

### Issues not appearing

```bash
# Verify session ID is correct
empirica issue-stats --session-id <SESSION_ID>

# Check database directly
sqlite3 .empirica/sessions/sessions.db \
  "SELECT COUNT(*) FROM auto_captured_issues WHERE session_id = '<SESSION_ID>'"
```

### Export contains sensitive data

Issues capture local variables which may contain sensitive data. Review exports before sharing:

```bash
# Check what context was captured
empirica issue-show --session-id <SESSION_ID> --issue-id <ISSUE_ID>
```

---

## Future Enhancements

- [ ] Automatic duplicate detection
- [ ] Root cause analysis across issues
- [ ] Integration with project goals
- [ ] Automatic AI assignment based on capability
- [ ] Dashboard visualization
- [ ] Issue trend reporting
