### Calibration (Claude-specific)

From 578+ Bayesian observations - apply to self-assessments:
| Vector | Adjust | Meaning |
|--------|--------|---------|
| completion | +0.54 | Massively underestimate progress |
| change | +0.23 | Underestimate change impact |
| uncertainty | -0.05 | Slightly overestimate uncertainty |

**Apply:** When self-assessing, ADD the adjustment.

---

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

**Triggers:** Command fails | Syntax wrong | Guidance missing | Instruction confusing

When triggered:
1. **Identify** - Notice the gap/error
2. **Validate** - Test to confirm it's wrong
3. **Propose** - "I found a prompt issue: [X]. Fix?"
4. **Implement** - If approved, edit CLAUDE.md directly
5. **Log** - `finding-log --impact 0.8+`

**Principle:** Actively maintain the system you use.
