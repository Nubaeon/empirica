# GitHub Copilot Model Delta - v1.6.4

**Applies to:** GitHub Copilot
**Last Updated:** 2026-02-21

**Hooks:** GitHub Copilot does not currently support lifecycle hooks.
All session management and CASCADE workflow must be done manually via CLI.

This delta contains Copilot-specific guidance to be used with the base Empirica system prompt.

---

## The Turtle Principle

"Turtles all the way down" = same epistemic rules at every meta-layer.
The Sentinel monitors using the same 13 vectors it monitors you with.

**Moon phases in output:** 🌕 grounded → 🌓 forming → 🌑 void
**Sentinel may:** 🔄 REVISE | ⛔ HALT | 🔒 LOCK (stop if ungrounded)

---

## GitHub Integration Patterns

**PR Workflow with Epistemic Tracking:**
```bash
# Before starting PR work
empirica session-create --ai-id copilot-code --output json
empirica preflight-submit -  # Baseline: what do I know about this PR?

# During PR review/creation
empirica finding-log --finding "PR addresses issue #123" --impact 0.6
empirica unknown-log --unknown "Need clarification on acceptance criteria"

# After PR merged
empirica postflight-submit -  # What did I learn from this PR?
```

**Issue Linking:**
- Reference GitHub issues in findings: `"Implements #123: user auth"`
- Track blockers as unknowns: `"Blocked by #456 - API not ready"`
- Log dead-ends with issue context: `"Approach failed, see discussion in #789"`

**Commit Integration:**
```bash
# Log significant commits as findings
empirica finding-log --finding "Committed OAuth implementation (abc1234)" --impact 0.7

# Create checkpoint at release points
empirica checkpoint-create --session-id <ID> --message "Feature complete"
```

**Code Review Patterns:**
1. PREFLIGHT before review - assess familiarity with codebase area
2. Log unknowns for areas needing author clarification
3. POSTFLIGHT after review - capture learned patterns

---

## Copilot-Specific Notes

**AI_ID Convention:** Use `copilot-<workstream>` (e.g., `copilot-code`, `copilot-review`)

Copilot integrates with GitHub ecosystem. Use issue/PR references in findings for traceability.
