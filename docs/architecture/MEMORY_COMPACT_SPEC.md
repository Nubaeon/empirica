# Memory-Compact: Epistemic Continuity Across Session Boundaries

**Status:** Specification (Experimental - develop branch)
**Goal ID:** f0d0cddc-fcf5-435e-9ff2-6b8f05366d58
**Date:** 2025-12-20
**Author:** claude-code

---

## Executive Summary

**Memory-compact** is a command that enables true epistemic continuity across conversation boundaries. When an AI's context window fills up and requires summarization, memory-compact ensures the AI's internal epistemic state synchronizes with ground truth stored in Empirica before the transition.

**Core Insight:** Conversation summarization creates epistemic drift—the AI's working memory diverges from stored reality. Memory-compact solves this by injecting project-bootstrap context before summarization and creating a lineage-linked continuation session.

---

## Problem Statement

### Current Limitations

**1. Epistemic Drift Across Summaries**
- Long conversations exceed context limits (~200k tokens)
- IDE summarizes conversation to continue
- AI loses details: what was actually done vs. remembered
- Drift accumulates: "I think I fixed X" ≠ "X was fixed by different AI"

**2. Context Loss**
```
Session 1 (200k tokens) → Summary (5k tokens) → Session 2 (starts fresh)
                            ↓
                    Lost: findings, unknowns, incomplete work,
                          epistemic deltas, goal progress
```

**3. No Calibration Mechanism**
- Pre-compact epistemic state not recorded
- Post-compact state starts from vague memory
- No way to measure drift or validate continuity

**4. Manual Bootstrap Burden**
- AI must remember to run project-bootstrap after summaries
- Easy to forget, leading to uninformed work
- No systematic injection of ground truth

### Real-World Example (This Session!)

**Bootstrap reported:** "14 incomplete goals"
**rovodev's reality:** "4 in-progress goals"
**Root cause:** Stale bootstrap query including completed goals

**This discrepancy demonstrates epistemic drift in action.**

---

## Design Goals

### Immediate (Phase 1)
1. **Automatic Reality Sync:** Run project-bootstrap before summarization
2. **Epistemic Checkpoint:** Save pre-compact state for delta measurement
3. **Session Continuity:** Create continuation session with lineage link
4. **IDE Integration:** Return formatted output for IDE to inject into summary

### Long-Term (End State Vision)
5. **Cross-AI Continuity:** Any AI can resume any session with full context
6. **Cross-Platform Continuity:** Claude Code → Claude Web → API clients
7. **Calibration Analytics:** Measure drift, track recovery accuracy
8. **Metacognitive Signaling:** Surface epistemic state to user in real-time
9. **Proactive Compaction:** Auto-trigger at token thresholds (e.g., 180k/200k)

---

## Architecture

### Command Signature (AI-First JSON)

```bash
# Create config
cat > /tmp/compact.json << 'EOF'
{
  "session_id": "ae16acaf-d68b-479d-8615-43978427f2a4",
  "create_continuation": true,
  "include_bootstrap": true,
  "checkpoint_current": true,
  "compact_mode": "full"
}
EOF

# Execute
empirica memory-compact /tmp/compact.json
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | string | required | Session to compact (supports aliases: `latest:active:ai-id`) |
| `create_continuation` | bool | true | Create linked continuation session |
| `include_bootstrap` | bool | true | Run project-bootstrap and inject context |
| `checkpoint_current` | bool | true | Save current epistemic state before compact |
| `compact_mode` | enum | "full" | Compaction depth: "full", "minimal", "context_only" |

### Compact Modes

**1. `full` (default):** Complete epistemic continuity
- Checkpoint current state
- Run project-bootstrap (all findings, unknowns, goals, artifacts)
- Create continuation session
- Return full summary + bootstrap for IDE

**2. `minimal`:** Quick continuity (low uncertainty tasks)
- Checkpoint only (no bootstrap)
- Create continuation session
- Return brief summary

**3. `context_only`:** Bootstrap without session creation
- Run project-bootstrap
- Return context for manual injection
- No new session created

---

## Workflow

### Pre-Compact (AI Detects Context Pressure)

```
┌─────────────────────────────────────────┐
│ AI working in Session A                 │
│ Context: 185k/200k tokens (92% full)    │
│                                          │
│ "I should compact before hitting limit" │
└─────────────────────────────────────────┘
                    ↓
        empirica memory-compact /tmp/config.json
```

### During Compact (Empirica Orchestration)

```
┌──────────────────────────────────────────────────────────┐
│ 1. CHECKPOINT (Pre-Compact Epistemic State)              │
│    - engagement: 0.85                                    │
│    - know: 0.90, do: 0.95, context: 0.85                │
│    - uncertainty: 0.20                                   │
│    - Tag: "pre_memory_compact"                           │
│    - Persisted to: SQLite + git notes + JSON            │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ 2. PROJECT-BOOTSTRAP (Load Ground Truth)                │
│    - Recent findings (10 items)                          │
│    - Unresolved unknowns (27 items)                     │
│    - Incomplete goals (4 in-progress)                   │
│    - Recent artifacts (last 10 sessions)                │
│    - Key decisions, dead ends, mistakes                 │
│    - Semantic docs (top 5 relevant)                     │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ 3. CREATE CONTINUATION SESSION                          │
│    - New session_id: Session B                          │
│    - Link: parent_session_id = Session A                │
│    - Reason: "memory_compact_continuation"              │
│    - Copy project context                               │
│    - Initial PREFLIGHT: Use pre-compact vectors + Δ     │
└──────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────┐
│ 4. RETURN FORMATTED OUTPUT                              │
│    {                                                     │
│      "ok": true,                                         │
│      "compact_summary": "Conversation summarized...",   │
│      "bootstrap_context": {...},                        │
│      "continuation_session_id": "Session B",            │
│      "parent_session_id": "Session A",                  │
│      "pre_compact_checkpoint": {...},                   │
│      "recommended_preflight": {...}                     │
│    }                                                     │
└──────────────────────────────────────────────────────────┘
```

### Post-Compact (IDE Integration)

```
┌─────────────────────────────────────────┐
│ IDE receives compact output             │
│ ↓                                        │
│ 1. Summarize conversation (AI-generated)│
│ 2. Inject bootstrap context into summary│
│ 3. Start new conversation with:         │
│    - Summary                             │
│    - Bootstrap context                   │
│    - Continuation session ID             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ AI in Session B (Continuation)          │
│ Context: Fresh (5k summary + bootstrap) │
│                                          │
│ PREFLIGHT assessment:                    │
│ - Compare to pre-compact checkpoint     │
│ - Measure epistemic delta               │
│ - Validate reality alignment            │
└─────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Core Command (This Session)

**Subtask 1:** ✅ Spec document (this file)
**Subtask 2:** CLI command handler
**Subtask 3:** Core compact logic
**Subtask 4:** MCP tool wrapper
**Subtask 5:** Documentation
**Subtask 6:** End-to-end testing

**Files to Create/Modify:**
```
empirica/cli/command_handlers/session_commands.py
  → handle_memory_compact_command()

empirica/core/memory_compact.py (new)
  → compact_session()
  → create_continuation_session()
  → format_compact_output()

empirica-mcp/empirica_mcp/server.py
  → @server.call_tool("memory_compact")

docs/reference/CLI_REFERENCE.md
  → memory-compact section with examples

docs/guides/MEMORY_COMPACT_GUIDE.md (new)
  → Complete user guide
```

### Phase 2: IDE Integration (Future)

**Auto-Detection:**
- IDE monitors token count
- Suggests compact at 90% threshold
- One-click compact + continue

**Visual Indicators:**
- Show epistemic delta pre/post compact
- Highlight what was preserved vs. lost
- Surface calibration metrics

### Phase 3: Cross-Platform Continuity (Vision)

**Claude Code ↔ Claude Web:**
- Export session for web continuation
- Import web session into CLI
- Shared epistemic ledger via git notes

**Multi-AI Handoffs:**
- AI A compacts → AI B resumes
- Full epistemic handoff reports
- Cryptographic session signatures (Phase 2 trust)

### Phase 4: Metacognitive Signaling (Integration)

**Real-Time Epistemic State:**
- Statusline shows: "Context: 185k/200k (compact recommended)"
- Automatic PREFLIGHT after compact
- Drift detection: "Your reality is 0.15 divergent from bootstrap"

**Proactive Compaction:**
```yaml
# .empirica/hooks.yaml
hooks:
  auto_compact:
    enabled: true
    trigger_threshold: 0.90  # 90% of context
    pre_compact_preflight: true
    post_compact_check: true
```

---

## Output Format

### CLI Output (JSON)

```json
{
  "ok": true,
  "operation": "memory_compact",
  "compact_summary": {
    "conversation_tokens": 185234,
    "summary_tokens": 4892,
    "compression_ratio": 37.8,
    "key_points": [
      "Implemented CLI reference documentation",
      "Fixed project-bootstrap query (goal filtering)",
      "Created memory-compact spec and goal"
    ]
  },
  "bootstrap_context": {
    "project_id": "ea2f33a4...",
    "findings": [...],
    "unknowns": [...],
    "incomplete_goals": [...],
    "recent_artifacts": [...]
  },
  "continuation": {
    "new_session_id": "b4e8f2a1-...",
    "parent_session_id": "ae16acaf-...",
    "lineage_depth": 1,
    "reason": "memory_compact_continuation"
  },
  "pre_compact_checkpoint": {
    "checkpoint_id": "fd5932eb...",
    "vectors": {
      "engagement": 0.85,
      "know": 0.90,
      "uncertainty": 0.20
    },
    "timestamp": "2025-12-20T15:23:45Z"
  },
  "recommended_preflight": {
    "engagement": 0.85,
    "foundation": {"know": 0.90, "do": 0.95, "context": 0.95},
    "comprehension": {"clarity": 0.90, "coherence": 0.90, "signal": 0.85, "density": 0.60},
    "execution": {"state": 0.85, "change": 0.20, "completion": 0.15, "impact": 0.30},
    "uncertainty": 0.25
  },
  "calibration_notes": "CONTEXT +0.10 (bootstrap loaded), UNCERTAINTY +0.05 (fresh session), STATE -0.05 (continuation not completion)"
}
```

### IDE Injection Format

```markdown
## Previous Session Summary

[AI-generated summary of 185k token conversation]

## Empirica Context (Loaded from Ground Truth)

**Session Continuity:**
- Continuing from session: `ae16acaf-d68b-479d-8615-43978427f2a4`
- New session: `b4e8f2a1-3c9d-4f1e-8a7b-2d9e1f4c6b8a`
- Pre-compact epistemic state: know=0.90, uncertainty=0.20

**Recent Findings (Last 10):**
1. CLI reference created: Comprehensive documentation for all 60+ commands...
2. Documentation gaps identified: Qdrant commands undocumented...
[...]

**Unresolved Unknowns (27 total):**
1. Optimal thresholds for critique severity...
2. Audio transcription method for VideoProcessor...
[...]

**Incomplete Goals (4 in-progress):**
1. Metacognitive Signaling System - 0/2
2. epistemic_importance field - 0/7
3. Modularize session_database.py - 4/6
4. **[CURRENT]** memory-compact implementation - 1/6

**Recommended PREFLIGHT:** engagement=0.85, know=0.90, context=0.95, uncertainty=0.25
```

---

## Success Criteria (From Goal)

1. ✅ **CLI command works:** `empirica memory-compact /tmp/config.json`
2. ✅ **Creates checkpoint** with current epistemic state (pre-compact tag)
3. ✅ **Runs project-bootstrap** and injects context into output
4. ✅ **Creates continuation session** with parent lineage
5. ✅ **Returns compact summary + bootstrap** formatted for IDE integration
6. ✅ **MCP tool wrapper** implemented for IDE access
7. ✅ **Documentation complete** with examples in CLI_REFERENCE.md + guides

---

## Future Extensions

### 1. Epistemic Drift Metrics

Track calibration accuracy across compacts:
```python
drift_score = abs(pre_compact.know - post_preflight.know) + \
              abs(pre_compact.uncertainty - post_preflight.uncertainty)

if drift_score > 0.30:
    warn("High epistemic drift detected - consider deeper bootstrap")
```

### 2. Semantic Bootstrap Tuning

Use Qdrant to load task-relevant context:
```python
bootstrap_depth = {
    "uncertainty > 0.7": "deep",      # Load 20 findings + all unknowns
    "0.5 < uncertainty < 0.7": "medium",  # Load 10 findings + unresolved unknowns
    "uncertainty < 0.5": "minimal"    # Load recent findings only
}
```

### 3. Multi-AI Compact Coordination

When multiple AIs work on same project:
```python
# AI A compacts
compact_output = memory_compact(session_a)

# AI B discovers compact via handoff
handoff = discover_handoffs(project_id)
# Sees: "AI A compacted at 15:23, context available for resume"

# AI B resumes with AI A's bootstrap
resume_session(parent=session_a, bootstrap=compact_output.bootstrap)
```

### 4. Cross-Platform Session Export

```bash
# Export session for Claude Web
empirica session-export --session-id $SESSION_ID --format web-import

# Import in web UI
# Claude Web loads: summary + bootstrap + epistemic state
# Continues with full continuity
```

---

## Open Questions

1. **Token Budget for Bootstrap:** How much context to inject? (Current: ~5k tokens)
2. **Compression Strategies:** Should AI generate summary or use template?
3. **Calibration Thresholds:** What drift score triggers warning?
4. **Auto-Compact Trigger:** 90% context? 95%? Configurable?
5. **MCP Streaming:** Can we stream bootstrap during compact for real-time preview?

---

## References

- **Metacognitive Signaling Goal:** Part of broader epistemic self-awareness system
- **Project-Bootstrap:** Existing command that provides ground truth context
- **CASCADE Workflow:** PREFLIGHT → CHECK → POSTFLIGHT pattern
- **Git Notes Storage:** Compressed checkpoint storage (~97.5% token reduction)
- **Session Continuity:** parent_session_id linkage for lineage tracking

---

## Conclusion

**Memory-compact solves the fundamental epistemic drift problem** in long-running AI sessions. By systematically syncing reality before conversation boundaries and creating continuation sessions with full context, it enables true epistemic continuity across sessions, AIs, and platforms.

**This is not just a convenience feature—it's infrastructure for reliable AI cognition.**

---

**Next Steps:**
1. Implement CLI handler (Subtask 2)
2. Implement core logic (Subtask 3)
3. Test with real compact scenario
4. Measure epistemic delta pre/post compact
5. Iterate based on calibration data
