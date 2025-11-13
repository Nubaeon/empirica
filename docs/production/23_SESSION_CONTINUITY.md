# Session Continuity System

## Overview

The Session Continuity system enables AI agents (especially Claude) to maintain context and learning across session restarts. Instead of starting fresh each time, the AI can load previous session data, understand past decisions, and build on previous work.

## Status

**Current**: Phase 1 - Manual Loading (Complete ✅)  
**Next**: Phase 2 - Epistemic-Driven Loading (Planned)

## What Problem Does This Solve?

### Before Continuity
- AI starts fresh each session
- Repeats investigations already done
- Loses context about architectural decisions
- Fragments understanding across sessions
- Cannot learn from own patterns

### After Continuity
- AI loads previous work before starting
- Understands decision history and rationales
- Builds on previous investigations
- Maintains coherent project understanding
- Learns from own behavioral patterns

## Quick Start

### List Available Sessions
```bash
python empirica_continuity/continuity_manager.py list
```

Output:
```
Available sessions:
  3c00cfef-7b29... | 2025-10-31 00:44:18 |  1 cascades | conf=0.92
  b0e152be-9dcf... | 2025-10-31 00:44:11 |  1 cascades | conf=N/A
  ...
```

### Resume from Specific Session
```bash
# Copy session ID from list
python bootstrap.py --resume 3c00cfef-7b29-4d8f-acb9-c9b0a64517f2
```

### Load Recent Sessions
```bash
# Load 3 most recent sessions
python bootstrap.py --load-recent 3

# Load with more detail
python bootstrap.py --load-recent 5 --context-detail medium
```

## How It Works

### Data Storage

Sessions are stored in SQLite database: `empirica/.empirica/sessions/sessions.db`

**Stored Data**:
- Session metadata (AI ID, timestamps, bootstrap level)
- Cascades (tasks, phase completions, confidence)
- Epistemic assessments (12-vector assessments at each phase)
- Divergence tracking (delegate/trustee tensions)
- Drift monitoring (behavioral patterns)

### Loading Process

1. **Query Database**: Retrieve session(s) by ID or recency
2. **Load Relations**: Fetch cascades, assessments, divergences
3. **Format for AI**: Convert to human-readable text
4. **Display**: Show context before bootstrap initialization
5. **Continue**: AI proceeds with loaded context

### Detail Levels

**Summary** (default, ~1KB per session):
```
================================================================================
SESSION: 3c00cfef-7b29-4d8f-acb9-c9b0a64517f2
================================================================================
AI: test_claude_resume
Started: 2025-10-31 00:44:18
Total Cascades: 1
Avg Confidence: 0.92

CASCADES (1)
[1] Implement session resume MCP tool
    Phases: THINK → PLAN → INVESTIGATE → CHECK → ACT
    Final Confidence: 0.92
    Investigation Rounds: 3
```

**Medium** (~2-3KB per session):
- Everything in summary
- Epistemic assessment overviews
- Engagement and confidence scores
- Investigation tool usage

**Full** (~5-10KB per session):
- Everything in medium
- All 12-vector assessments with rationales
- Divergence details and resolutions
- Complete epistemic trajectories

## CLI Reference

### continuity_manager.py

**List sessions**:
```bash
python empirica_continuity/continuity_manager.py list
```

**Load specific session**:
```bash
python empirica_continuity/continuity_manager.py load <session_id> [detail_level]
```

**Load recent sessions**:
```bash
python empirica_continuity/continuity_manager.py recent [n] [detail_level]
```

**Detail levels**: `summary` | `medium` | `full`

### bootstrap.py Integration

**Resume from session**:
```bash
python bootstrap.py --resume <session_id>
```

**Load recent sessions**:
```bash
python bootstrap.py --load-recent <n>
```

**Control detail**:
```bash
python bootstrap.py --load-recent 3 --context-detail medium
```

**All flags**:
- `--level`: Bootstrap level (minimal/standard/full)
- `--ai-id`: AI identifier
- `--resume`: Resume from session ID
- `--load-recent`: Load N recent sessions
- `--context-detail`: Detail level (summary/medium/full)

## Python API

```python
from empirica_continuity import ContinuityManager

# Initialize
cm = ContinuityManager()

# List available sessions
summaries = cm.list_available_sessions(limit=10)
for s in summaries:
    print(s)

# Load specific session
session = cm.load_session('3c00cfef-7b29-4d8f-acb9-c9b0a64517f2')

# Load recent sessions
recent = cm.load_recent_sessions(n=5)

# Format for AI consumption
formatted = cm.format_session_for_ai(session, detail_level='summary')
print(formatted)

# Format multiple sessions
multi = cm.format_multiple_sessions(recent, detail_level='summary')
print(multi)

# Clean up
cm.close()
```

## What Gets Loaded

For each session, the AI sees:

### Session Level
- AI identifier
- Start/end timestamps
- Bootstrap level used
- Total cascades executed
- Average confidence
- Drift detection status
- Session notes (if any)

### Cascade Level
- Task description
- Context (task-specific data)
- Phase completions (PREFLIGHT → ... → POSTFLIGHT)
- Final action and confidence
- Investigation rounds
- Duration
- Engagement gate status

### Epistemic Level (medium/full detail)
- 12-vector assessments per phase:
  - **Foundation**: know, do, context
  - **Comprehension**: clarity, coherence, signal, density
  - **Execution**: state, change, completion, impact
  - **Meta**: uncertainty (explicit tracking)
  - Engagement dimension
- Confidence trajectories
- Recommended actions per phase

### Divergence Level (full detail)
- Delegate vs. trustee perspectives
- Divergence scores and reasons
- Synthesis strategies
- Tension acknowledgments
- Resolution approaches

## Use Cases

### Daily Work Resume
**Scenario**: You're working on a multi-day project

**Workflow**:
1. End of day: Session auto-saved
2. Next day: `python bootstrap.py --load-recent 1`
3. AI sees: Previous day's work, decisions, open questions
4. Result: Seamless continuation

### Context Recovery
**Scenario**: You need to remember why something was done

**Workflow**:
1. List sessions: Find relevant session ID
2. Load with full detail: See complete reasoning
3. Understand: Epistemic assessments show the "why"

### Pattern Analysis
**Scenario**: Want to understand AI's behavioral patterns

**Workflow**:
1. Load multiple sessions: `--load-recent 10`
2. Review: See investigation patterns, confidence trends
3. Learn: Notice when AI investigates vs. proceeds

### Investigation Efficiency
**Scenario**: Avoid repeating previous investigations

**Workflow**:
1. Load recent sessions before starting
2. Check: What tools were already used?
3. Skip: Don't re-investigate what was already explored

## Future Phases

### Phase 2: Epistemic-Driven Loading (Planned)
- Use 12-vector assessments to find similar cascades
- Load based on meta-uncertainty (what AI is uncertain about)
- Smart relevance scoring
- "Load sessions where I had similar uncertainty patterns"

### Phase 3: Semantic Pattern Matching (Planned)
- Vector embeddings for semantic search
- Find tasks by meaning, not just keywords
- Cross-reference: semantic + epistemic + temporal
- "Find sessions where I worked on authentication"

### Phase 4: Governance Layer (Planned)
- Filter noise, extract signal
- Compress older sessions (summaries only)
- Decay function (detail fades with time)
- "Show me high-value moments, not all data"

### Phase 5: Adaptive Learning (Planned)
- Track which loaded context actually helps
- Self-improving loader
- Learn loading patterns
- "I learned that loading X helps with Y tasks"

### Phase 6: Cross-Session Synthesis (Future)
- Generate meta-knowledge from multiple sessions
- Belief evolution tracking
- Collaborative continuity (multi-AI)
- "Based on 20 sessions, here's what I've learned about..."

See `empirica_continuity/CONTINUITY_PLAN.md` for complete roadmap.

## Performance

**Current metrics**:
- Single session load: ~5-10ms
- Format for display: ~5ms
- Bootstrap overhead: ~50-100ms
- Negligible impact on startup

**Storage**:
- ~1-2KB per session (JSON export)
- ~10-20KB in SQLite (with relations)
- 100 sessions: ~2MB total
- Very lightweight

## Best Practices

### When to Load Context

**✅ Load Context When**:
- Resuming multi-day work
- Need to remember previous decisions
- Want to avoid repeating investigations
- Building on previous sessions
- Analyzing patterns

**❌ Don't Load Context When**:
- Completely new project (no relevant history)
- Fresh exploration needed (old context might bias)
- Quick one-off tasks
- Testing/debugging the continuity system itself

### How Much to Load

**General Guidelines**:
- **1 session**: Direct continuation of previous work
- **3 sessions**: Resume after weekend/break
- **5 sessions**: Understand recent project context
- **10+ sessions**: Pattern analysis, not daily work

**Detail Level**:
- **Summary**: Daily resume (fast, concise)
- **Medium**: Understanding decisions
- **Full**: Deep investigation, debugging

### Workflow Integration

**Recommended Pattern**:
```bash
# Morning: Resume yesterday's work
python bootstrap.py --load-recent 1 --context-detail summary

# After break: Catch up on recent work  
python bootstrap.py --load-recent 3 --context-detail summary

# Deep dive: Understand specific decision
python empirica_continuity/continuity_manager.py load <id> full
```

## Troubleshooting

### No Sessions Found

**Problem**: `list` shows no sessions

**Solution**:
- Check database exists: `ls empirica/.empirica/sessions/sessions.db`
- Run at least one cascade to create sessions
- Verify database path in ContinuityManager

### Session Load Fails

**Problem**: `load` returns None or error

**Solution**:
- Verify session ID is complete (not truncated from `list`)
- Check database integrity: `sqlite3 <db_path> ".schema"`
- Ensure no concurrent writes to database

### Too Much Context

**Problem**: Loaded context is overwhelming

**Solution**:
- Use `summary` detail level instead of `full`
- Load fewer sessions (1-3 instead of 10+)
- Load specific sessions (by ID) instead of all recent

### Not Enough Detail

**Problem**: Need more information than summary provides

**Solution**:
- Use `medium` or `full` detail level
- Load session standalone with `continuity_manager.py` for analysis
- Query database directly for specific data

## Testing

**Run validation suite**:
```bash
python empirica_continuity/test_continuity.py
```

**Expected output**:
```
✅ ALL TESTS PASSED - Phase 1 Continuity Working!

📊 Phase 1 Features Validated:
   ✓ Session listing
   ✓ Session loading by ID
   ✓ Recent session loading
   ✓ AI-readable formatting
   ✓ Multiple session handling
   ✓ Epistemic data preservation
```

## Architecture

### Components

```
empirica_continuity/
├── __init__.py                  # Package exports
├── continuity_manager.py        # Core implementation
├── CONTINUITY_PLAN.md          # Complete roadmap
├── README.md                    # User documentation
├── test_continuity.py          # Validation suite
└── PHASE1_COMPLETE.md          # Completion report
```

### Data Flow

```
SQLite sessions.db
    ↓
ContinuityManager.load_session()
    ↓  
Session dict (with relations)
    ↓
format_session_for_ai()
    ↓
Formatted text
    ↓
Bootstrap displays
    ↓
AI reads and proceeds
```

### Integration Points

1. **Bootstrap** (`bootstrap.py`):
   - `--resume` flag → load single session
   - `--load-recent` flag → load N recent
   - `--context-detail` flag → control verbosity

2. **Session Database** (`empirica/data/session_database.py`):
   - Source of truth for all session data
   - Automatic cascade/assessment tracking
   - No changes needed (reads existing data)

3. **MCP Server** (future):
   - Tool for Claude to request context
   - "Load sessions related to X"
   - "Show me similar cascades"

## Security & Privacy

**Local Storage Only**:
- All data in local SQLite database
- No cloud sync, no external services
- User has full control

**Sensitive Data**:
- Sessions may contain task details, context
- Stored locally in `empirica/.empirica/sessions/`
- User responsible for filesystem security

**Cleanup**:
- Delete database to clear all history
- Export/archive old sessions as needed
- No automatic data transmission

## FAQ

**Q: Does this slow down startup?**  
A: Minimal impact (~50-100ms). Negligible for daily use.

**Q: How much storage does it use?**  
A: Very lightweight. ~2MB for 100 sessions. Grows slowly.

**Q: Can I delete old sessions?**  
A: Yes, but manual SQL deletion for now. Cleanup tools planned for Phase 4.

**Q: Does it work with all AI agents?**  
A: Yes. Any AI using Empirica can benefit. Designed with Claude in mind.

**Q: What if I don't want continuity?**  
A: Simply don't use `--resume` or `--load-recent` flags. Completely optional.

**Q: Can I see what will be loaded before loading?**  
A: Yes. Use `continuity_manager.py load <id>` to preview.

**Q: How do I know what to load?**  
A: Start with `--load-recent 1` for direct continuation. Experiment with 3-5 for broader context.

**Q: What detail level should I use?**  
A: `summary` for daily work. `medium` for decision review. `full` for deep analysis.

## Support

- **Documentation**: `empirica_continuity/README.md`
- **Planning**: `empirica_continuity/CONTINUITY_PLAN.md`
- **Testing**: `empirica_continuity/test_continuity.py`
- **Status**: `empirica_continuity/PHASE1_COMPLETE.md`

---

**Status**: Phase 1 Complete ✅  
**Version**: 1.0.0-phase1  
**Last Updated**: 2025-10-31  
**Next**: Phase 2 - Epistemic-Driven Loading
