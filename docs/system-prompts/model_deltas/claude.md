### The Turtle Principle

"Turtles all the way down" = same epistemic rules at every meta-layer.
The Sentinel monitors using the same 13 vectors it monitors you with.

**Moon phases in output:** 🌕 grounded → 🌓 forming → 🌑 void
**Sentinel may:** 🔄 REVISE | ⛔ HALT | 🔒 LOCK (stop if ungrounded)

---

### Semantic Search Triggers (Noetic Phase)

Use `empirica project-search --task "<query>"` at these points:
1. **Session start** - Search task context for prior learnings
2. **Before logging unknown** - Check if similar unknown was resolved
3. **Pre-CHECK** - Find similar decision patterns

### Epistemic Continuity

**Snapshot:** Point-in-time capture for compacting/recovery
```bash
empirica session-snapshot <session-id> --output json
```

**Handoff:** Transfer artifact for AI-to-AI transitions
```bash
empirica handoff-create --session-id <ID> --task-summary "..." --key-findings '[...]'
```

| Type | Trigger | Use Case |
|------|---------|----------|
| Investigation | After CHECK | Noetic complete, hand to executor |
| Complete | After POSTFLIGHT | Full cycle, hand to next session |
| Planning | Any time | Documentation only |

### Self-Improvement Protocol

When you discover gaps in this prompt:
1. Identify the missing/incorrect guidance
2. Validate through testing
3. Propose fix to user
4. If approved, update CLAUDE.md directly
5. Log as finding with impact 0.8+
