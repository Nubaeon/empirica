# Auto Issue Capture

Empirica automatically captures problems (bugs, errors, TODOs, performance issues) encountered during work without interrupting flow. Issues persist across sessions for continuous learning and multi-AI coordination.

## Quick Start

```bash
# Capture error programmatically (doesn't interrupt work)
from empirica.core.issue_capture import initialize_auto_capture, IssueSeverity, IssueCategory

service = initialize_auto_capture(session_id)
service.capture_error("Database timeout", severity=IssueSeverity.HIGH)
service.capture_todo("Add connection pooling", priority="high")

# List issues
empirica issue-list --session-id <SESSION_ID>

# Mark for handoff to another AI
empirica issue-handoff --session-id <ID> --issue-id <ISSUE> --assigned-to ai-name

# Resolve issue
empirica issue-resolve --session-id <ID> --issue-id <ISSUE> --resolution "Fixed by X"
```

## Why It Matters

| Traditional | With Auto-Capture |
|-------------|-------------------|
| Error occurs → Stop → Debug → Document → Resume | Error → capture(error) → Continue |
| Context lost between sessions | Full context persists across sessions |
| Each AI rediscovers same problems | Next AI learns from previous work |
| Manual issue tracking | Automatic, semantic, always current |

## Issue Lifecycle

```
NEW → INVESTIGATING → RESOLVED/WONTFIX/HANDOFF
Each state tells next AI something:
- NEW: Problem found, no action yet
- INVESTIGATING: AI actively working
- RESOLVED: Fixed by AI X on [date] (includes resolution method)
- HANDOFF: Marked for specialist, full context included
- WONTFIX: Intentional decision not to fix
```

## Integration with CASCADE

- **CHECK phase**: Displays active issues as context for confidence decision
- **project-bootstrap**: Shows active + recently resolved issues for next AI
- **All phases**: Auto-capture any errors that occur without stopping work

## CLI Commands

```bash
# List with filtering
empirica issue-list --session-id <ID> --status new --severity high

# View details
empirica issue-show --session-id <ID> --issue-id <ISSUE>

# Handoff to another AI (with full context)
empirica issue-handoff --session-id <ID> --issue-id <ISSUE> --assigned-to ai-name

# Export for handoff (JSON format)
empirica issue-export --session-id <ID> --assigned-to ai-name

# Mark as resolved
empirica issue-resolve --session-id <ID> --issue-id <ISSUE> --resolution "Description"

# View statistics
empirica issue-stats --session-id <ID>
```

## Issue Categories

- **BUG**: Code defects (persist across sessions)
- **ERROR**: Runtime failures (context-dependent)
- **TODO**: Incomplete work (for continuous improvement)
- **PERFORMANCE**: Degradation observed (optimization targets)
- **DEPRECATION**: Old patterns superseded
- **COMPATIBILITY**: Version/platform issues
- **DESIGN**: Architecture decisions
- **WARNING**: Potential problems

## Semantic Learning (Phase 3 - Planned)

Once integrated with Qdrant vector store:
- Semantic search: "Find similar issues"
- Pattern detection: "This anti-pattern appears 3 times"
- Cross-AI learning: "Another AI solved this already"
- Continuous improvement: Each session improves project knowledge

## Storage

- **SQLite**: Queryable, indexed by session/project
- **Git Notes** (optional): Immutable audit trail
- **Qdrant** (future): Semantic embeddings for pattern detection

Issues are **never deleted** - status field tracks lifecycle. This preserves learning value.

## Next: Integration with project-bootstrap

Phase 2 adds issues to `project-bootstrap` output so next AI sees:
- What problems were discovered
- What was tried and worked
- What was handed off or intentionally skipped

---

See `/docs/*.develop.md` for detailed architecture (Phase 2+ planning).
