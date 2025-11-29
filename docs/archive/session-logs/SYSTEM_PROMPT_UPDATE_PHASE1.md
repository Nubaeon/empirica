# System Prompt Update: Phase 1 Git Automation

**Add this section to all AI agent system prompts**

---

## 🆕 Phase 1: Git Automation & Cross-AI Coordination (NEW!)

### Automatic Git Checkpoints

CASCADE phases now **automatically create git checkpoints** for you:

```bash
# PREFLIGHT auto-creates checkpoint
empirica preflight "task" --ai-id your-ai-name
# → Checkpoint stored in git notes automatically

# POSTFLIGHT auto-creates checkpoint
empirica postflight <session-id> --ai-id your-ai-name
# → Checkpoint + calibration stored automatically

# Disable if needed
empirica preflight "task" --no-git
```

**What's stored:**
- 13 epistemic vectors (engagement, know, do, uncertainty, etc.)
- Phase and round number
- Session metadata
- 97.5% token compressed (50K → 1.25K)

**Location:** `refs/notes/empirica/checkpoints/<commit-hash>`

---

### Goal Storage in Git Notes

When you create goals, they're **automatically stored for cross-AI discovery**:

```bash
# Create goal (auto-stores in git)
empirica goals-create \
  --objective "Implement feature X" \
  --scope project_wide \
  --ai-id your-ai-name

# Goal automatically stored in git notes
# Other AIs can discover it!
```

**What's stored:**
- Goal objective, scope, success criteria
- Your epistemic state when creating goal
- Lineage (who created/resumed the goal)

**Location:** `refs/notes/empirica/goals/<goal-id>`

---

### Cross-AI Goal Discovery (NEW COMMANDS!)

You can now discover and resume goals from other AIs:

```bash
# Discover goals from another AI
empirica goals-discover --from-ai-id other-agent

# Example output:
# 1. Goal ID: a1b2c3d4...
#    Created by: claude-code
#    Objective: Implement authentication
#    Lineage: 
#      • claude-code - created
#      • mini-agent - resumed

# Resume another AI's goal
empirica goals-resume <goal-id> --ai-id your-ai-name

# Shows epistemic handoff:
# - Original AI's confidence levels
# - Their knowledge state
# - Their uncertainty
```

**New Commands:**
- `empirica goals-discover --from-ai-id <ai>`
- `empirica goals-resume <goal-id> --ai-id <your-ai>`

---

### When to Use

**Use Cross-AI Discovery When:**
- ✅ Another AI started work but didn't finish
- ✅ You want to see what other AIs are working on
- ✅ You need to coordinate with another AI
- ✅ You want to continue someone else's investigation

**Example Workflow:**
```bash
# Discover what claude-code was working on
empirica goals-discover --from-ai-id claude-code

# Found a relevant goal? Resume it!
empirica goals-resume <goal-id> --ai-id mini-agent

# System shows you:
# - Original objective
# - Claude's confidence levels (know: 0.7, uncertainty: 0.3)
# - What they learned
# - Where they left off

# Now continue with your own preflight
empirica preflight "Continue authentication work" --ai-id mini-agent
```

---

### Sentinel Integration (Cognitive Vault)

Checkpoints are automatically evaluated by the **Sentinel system** for routing decisions:

**Sentinel Decisions:**
- `PROCEED` - Continue with current AI
- `INVESTIGATE` - Need deeper investigation
- `HANDOFF` - Route to different AI
- `ESCALATE` - Human review needed
- `BLOCK` - Stop immediately

**You don't need to do anything** - Sentinel evaluates in background based on your epistemic vectors.

---

### Best Practices

**1. Always Use --ai-id:**
```bash
empirica preflight "task" --ai-id your-ai-name  # ✅ GOOD
empirica preflight "task"                       # ⚠️ Uses default 'empirica_cli'
```

**2. Check for Existing Goals Before Creating:**
```bash
# Before creating new goal, check if it exists
empirica goals-discover --from-ai-id other-ai
# Avoid duplicate work!
```

**3. Resume with Context:**
```bash
# When resuming, review original AI's state
empirica goals-resume <goal-id> --ai-id your-ai
# Shows their epistemic state - use this context!
```

**4. Use --no-git When Testing:**
```bash
# During quick tests, skip git overhead
empirica preflight "quick test" --no-git
```

---

### Architecture Notes

**Storage Layers:**
1. **SQLite** (`.empirica/sessions/sessions.db`) - Session metadata, vectors
2. **JSON Logs** (`.empirica_reflex_logs/`) - Detailed workflow logs
3. **Git Notes** (NEW!) - Compressed checkpoints & goals for cross-AI sharing

**Why Git Notes?**
- Distributed coordination (other AIs can `git pull`)
- Version controlled (full audit trail)
- 97.5% token savings (compressed state)
- Automatic lineage tracking

---

### Migration Notes

**No changes needed to existing code!**

Old commands still work:
```bash
empirica preflight "task"  # Works, uses default ai_id
empirica goals-create "goal"  # Works, stores in both SQLite and git
```

New features are **additive only** - safe degradation if git unavailable.

---

### Troubleshooting

**"Not in git repository"**
- Auto-checkpoints only work in git repos
- Safe degradation: Commands still work, just no git storage
- To enable: `git init` in your workspace

**"Git notes not found"**
- Run: `git fetch origin refs/notes/*:refs/notes/*`
- Check: `git notes list`

**"Goals not discoverable"**
- Verify goal was stored: `git notes list | grep empirica/goals`
- May need: `git push origin refs/notes/empirica/*` to share

---

**Phase 1 Complete:** Git automation ready for multi-AI coordination! 🚀
