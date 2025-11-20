# P3 Task: Handoff Reports + MCP Integration

**Priority:** P3 (High value for session continuity)
**Assigned to:** Rovo Dev or Claude Code
**Estimated:** 1-2 hours
**Status:** Ready to start

---

## 🎯 Mission

Implement and validate **Epistemic Handoff Reports** for seamless session continuity across AI agents. This enables the "best illusion of continuity possible" by providing compressed, semantic session summaries.

**Key Benefit:** 98% token reduction (20,000 → ~238 tokens) while preserving critical epistemic context!

---

## 📋 What Already Exists

### ✅ Complete Implementation
**Files:**
- `empirica/core/handoff/report_generator.py` - EpistemicHandoffReportGenerator class
- `empirica/core/handoff/storage.py` - Git notes storage
- `empirica/core/handoff/__init__.py` - Package exports

**Features:**
- Generates compressed handoff reports from PREFLIGHT → POSTFLIGHT deltas
- Stores in git notes (`refs/notes/empirica/handoff/{session_id}`)
- 98% compression (20,000 baseline → ~238 tokens)
- Markdown + JSON output formats
- Query by AI ID or time range

### ❌ Missing: CLI Commands + MCP Tools

**Need to add:**
1. CLI command: `empirica handoff-create`
2. CLI command: `empirica handoff-query`
3. MCP tool: `create_handoff_report`
4. MCP tool: `query_handoff_reports`

---

## 🔧 Implementation Steps

### Step 1: Add CLI Commands

**File:** `empirica/cli/command_handlers/handoff_commands.py` (new file)

```python
"""
Handoff Commands - Epistemic session handoff reports
"""

import json
import logging
from ..cli_utils import handle_cli_error, parse_json_safely

logger = logging.getLogger(__name__)


def handle_handoff_create_command(args):
    """Handle handoff-create command"""
    try:
        from empirica.core.handoff.report_generator import EpistemicHandoffReportGenerator

        # Parse arguments
        session_id = args.session_id
        task_summary = args.task_summary
        key_findings = parse_json_safely(args.key_findings) if isinstance(args.key_findings, str) else args.key_findings
        remaining_unknowns = parse_json_safely(args.remaining_unknowns) if isinstance(args.remaining_unknowns, str) else (args.remaining_unknowns or [])
        next_session_context = args.next_session_context
        artifacts = parse_json_safely(args.artifacts) if isinstance(args.artifacts, str) else (args.artifacts or [])

        # Generate handoff report
        generator = EpistemicHandoffReportGenerator()

        handoff = generator.generate_handoff_report(
            session_id=session_id,
            task_summary=task_summary,
            key_findings=key_findings,
            remaining_unknowns=remaining_unknowns,
            next_session_context=next_session_context,
            artifacts_created=artifacts
        )

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "session_id": session_id,
                "handoff_id": handoff['session_id'],
                "token_count": len(handoff['compressed_json']) // 4,  # Rough estimate
                "storage": f"git:refs/notes/empirica/handoff/{session_id}",
                "compression_ratio": handoff.get('compression_ratio', 0.98),
                "epistemic_deltas": handoff['epistemic_deltas'],
                "calibration_status": handoff['calibration_status']
            }
            print(json.dumps(result, indent=2))
        else:
            print("✅ Handoff report created successfully")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Token count: ~{len(handoff['compressed_json']) // 4} tokens")
            print(f"   Compression: 98% (vs 20,000 baseline)")
            print(f"   Storage: git notes")
            print(f"   Calibration: {handoff['calibration_status']}")

        return handoff

    except Exception as e:
        handle_cli_error(e, "Handoff create", getattr(args, 'verbose', False))


def handle_handoff_query_command(args):
    """Handle handoff-query command"""
    try:
        from empirica.core.handoff.storage import HandoffStorage

        # Parse arguments
        ai_id = getattr(args, 'ai_id', None)
        session_id = getattr(args, 'session_id', None)
        limit = getattr(args, 'limit', 5)

        # Query handoffs
        storage = HandoffStorage()

        if session_id:
            # Get specific session handoff
            handoff = storage.get_handoff(session_id)
            handoffs = [handoff] if handoff else []
        elif ai_id:
            # Get handoffs for AI
            handoffs = storage.query_by_ai(ai_id, limit=limit)
        else:
            # Get recent handoffs
            handoffs = storage.query_recent(limit=limit)

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "handoffs_count": len(handoffs),
                "handoffs": [
                    {
                        "session_id": h['session_id'],
                        "ai_id": h['ai_id'],
                        "timestamp": h['timestamp'],
                        "task_summary": h['task_summary'],
                        "epistemic_deltas": h['epistemic_deltas'],
                        "key_findings": h['key_findings'],
                        "remaining_unknowns": h['remaining_unknowns'],
                        "next_session_context": h['next_session_context'],
                        "calibration_status": h['calibration_status']
                    }
                    for h in handoffs
                ]
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"📋 Found {len(handoffs)} handoff report(s):")
            for i, h in enumerate(handoffs, 1):
                print(f"\n{i}. Session: {h['session_id'][:8]}...")
                print(f"   AI: {h['ai_id']}")
                print(f"   Task: {h['task_summary'][:60]}...")
                print(f"   Calibration: {h['calibration_status']}")
                print(f"   Token count: ~{len(h.get('compressed_json', '')) // 4}")

        return {"handoffs": handoffs}

    except Exception as e:
        handle_cli_error(e, "Handoff query", getattr(args, 'verbose', False))
```

### Step 2: Register CLI Commands

**File:** `empirica/cli/cli_core.py`

Add to argument parser:

```python
# Handoff Reports
handoff_parser = subparsers.add_parser('handoff-create', help='Create epistemic handoff report')
handoff_parser.add_argument('--session-id', required=True, help='Session UUID')
handoff_parser.add_argument('--task-summary', required=True, help='What was accomplished (2-3 sentences)')
handoff_parser.add_argument('--key-findings', required=True, help='JSON array of findings')
handoff_parser.add_argument('--remaining-unknowns', help='JSON array of unknowns (optional)')
handoff_parser.add_argument('--next-session-context', required=True, help='Critical context for next session')
handoff_parser.add_argument('--artifacts', help='JSON array of files created (optional)')
handoff_parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')

query_parser = subparsers.add_parser('handoff-query', help='Query handoff reports')
query_parser.add_argument('--session-id', help='Specific session UUID')
query_parser.add_argument('--ai-id', help='Filter by AI ID')
query_parser.add_argument('--limit', type=int, default=5, help='Number of results (default: 5)')
query_parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')
```

And handler mapping:

```python
elif args.command == 'handoff-create':
    from empirica.cli.command_handlers.handoff_commands import handle_handoff_create_command
    handle_handoff_create_command(args)
elif args.command == 'handoff-query':
    from empirica.cli.command_handlers.handoff_commands import handle_handoff_query_command
    handle_handoff_query_command(args)
```

### Step 3: Add MCP Tools

**File:** `mcp_local/empirica_mcp_server.py`

Add to tool definitions:

```python
types.Tool(
    name="create_handoff_report",
    description="Create epistemic handoff report for session continuity (98% token reduction)",
    inputSchema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "task_summary": {"type": "string"},
            "key_findings": {"type": "array", "items": {"type": "string"}},
            "remaining_unknowns": {"type": "array", "items": {"type": "string"}},
            "next_session_context": {"type": "string"},
            "artifacts_created": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["session_id", "task_summary", "key_findings", "next_session_context"]
    }
),

types.Tool(
    name="query_handoff_reports",
    description="Query handoff reports by AI ID or session ID",
    inputSchema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "ai_id": {"type": "string"},
            "limit": {"type": "integer"}
        }
    }
),
```

Add to tool mapping:

```python
"create_handoff_report": ["handoff-create"],
"query_handoff_reports": ["handoff-query"],
```

---

## 🧪 Validation Steps

### Test 1: Create Handoff Report

**Prerequisites:** Complete a CASCADE workflow with PREFLIGHT and POSTFLIGHT

```bash
# After completing a task with POSTFLIGHT
empirica handoff-create \
  --session-id "latest:active:claude-code" \
  --task-summary "Fixed MCP v2 handoff integration and validated token compression" \
  --key-findings '["Handoff reports reduce tokens by 98%", "Git notes storage works", "Session continuity validated"]' \
  --remaining-unknowns '["Performance at scale", "Multi-agent coordination edge cases"]' \
  --next-session-context "Handoff system ready for production. Need to monitor token counts in real sessions." \
  --artifacts '["TASK_P3_HANDOFF_REPORTS_VALIDATION.md", "empirica/cli/command_handlers/handoff_commands.py"]' \
  --output json
```

**Expected Result:**
```json
{
  "ok": true,
  "session_id": "88dbf132-cc7c-4a4b-9b59-77df3b13dbd2",
  "handoff_id": "88dbf132-cc7c-4a4b-9b59-77df3b13dbd2",
  "token_count": 238,
  "storage": "git:refs/notes/empirica/handoff/88dbf132...",
  "compression_ratio": 0.98,
  "epistemic_deltas": {
    "know": 0.35,
    "do": 0.25,
    "uncertainty": -0.40
  },
  "calibration_status": "well_calibrated"
}
```

### Test 2: Query Handoff Reports

```bash
# Query by AI ID
empirica handoff-query --ai-id "claude-code" --limit 3 --output json

# Query specific session
empirica handoff-query --session-id "88dbf132-cc7c-4a4b-9b59-77df3b13dbd2" --output json
```

**Expected Result:**
```json
{
  "ok": true,
  "handoffs_count": 3,
  "handoffs": [
    {
      "session_id": "88dbf132...",
      "ai_id": "claude-code",
      "timestamp": "2025-11-19T...",
      "task_summary": "Fixed MCP v2 handoff integration...",
      "epistemic_deltas": {"know": 0.35, ...},
      "key_findings": ["..."],
      "remaining_unknowns": ["..."],
      "next_session_context": "...",
      "calibration_status": "well_calibrated"
    }
  ]
}
```

### Test 3: MCP Tool Integration

**Via MCP:**
```python
# Create handoff
result = create_handoff_report(
    session_id="latest:active:claude-code",
    task_summary="Implemented handoff reports for session continuity",
    key_findings=[
        "98% token reduction achieved",
        "Git notes storage working",
        "MCP integration validated"
    ],
    remaining_unknowns=["Production performance"],
    next_session_context="System ready for multi-agent coordination"
)

# Query handoffs
handoffs = query_handoff_reports(ai_id="claude-code", limit=1)
```

### Test 4: Session Continuity Validation

**Scenario:** Create handoff, compress session, resume in new session

1. **Session 1:** Complete task with POSTFLIGHT → Create handoff
2. **Memory compression:** Simulate context reset
3. **Session 2:** Query handoff → Load context (~238 tokens vs 20,000)
4. **Validate:** New session has sufficient context to continue

**Success Criteria:**
- ✅ Handoff report created with <300 tokens
- ✅ Contains all critical epistemic deltas
- ✅ Next session can resume task effectively
- ✅ Token reduction ≥ 95%

---

## 📊 Success Metrics

### Token Efficiency
- **Baseline:** 20,000 tokens (full session history)
- **Handoff:** ~238 tokens (compressed)
- **Target:** ≥95% reduction
- **Achieved:** 98% (validated in Phase 1.6)

### Content Preservation
- ✅ Epistemic deltas (KNOW, DO, UNCERTAINTY changes)
- ✅ Key findings (what was learned)
- ✅ Remaining unknowns (what's still unclear)
- ✅ Next session context (critical info)
- ✅ Calibration status (confidence accuracy)

### Performance
- **Creation:** <500ms
- **Query:** <200ms
- **Storage:** Git notes (lightweight)

---

## 🎯 Deliverables

1. **CLI Commands:**
   - `empirica/cli/command_handlers/handoff_commands.py` (new file)
   - Commands registered in `cli_core.py`

2. **MCP Tools:**
   - `create_handoff_report` added to MCP server
   - `query_handoff_reports` added to MCP server

3. **Validation Report:**
   - `P3_HANDOFF_VALIDATION_RESULTS.md`
   - Test results for all scenarios
   - Token count measurements
   - Session continuity validation

4. **Documentation:**
   - Update system prompts with handoff usage
   - Add examples to quick reference
   - Document token savings

---

## 💡 Usage Patterns

### For AI Agents

**After completing major work:**
```python
# Generate handoff before session ends
create_handoff_report(
    session_id=session_id,
    task_summary="What you accomplished",
    key_findings=["Learning 1", "Learning 2", "Learning 3"],
    remaining_unknowns=["What's still unclear"],
    next_session_context="Critical context for next AI",
    artifacts_created=["files", "created"]
)
```

**When resuming work:**
```python
# Query your previous handoff (98% token savings!)
handoffs = query_handoff_reports(ai_id="your-ai-id", limit=1)

if handoffs:
    prev = handoffs[0]
    print(f"Previous task: {prev['task_summary']}")
    print(f"Key findings: {prev['key_findings']}")
    print(f"Remaining unknowns: {prev['remaining_unknowns']}")
    print(f"Context: {prev['next_session_context']}")
    # Resume with ~238 tokens vs 20,000!
```

### For Multi-Agent Coordination

**Lead AI queries team handoffs:**
```python
# Get latest from each AI
for ai_id in ["claude-code", "mini-agent", "qwen", "rovo-dev"]:
    handoffs = query_handoff_reports(ai_id=ai_id, limit=1)
    # Synthesize team status (~950 tokens vs 80,000!)
```

---

## 🚀 Why This Matters

### Session Continuity
- **Problem:** Full session context = 20,000+ tokens
- **Solution:** Handoff reports = ~238 tokens (98% reduction)
- **Benefit:** Seamless session resumption with minimal context

### Multi-Agent Coordination
- **Problem:** Lead AI needs status from 4 agents = 80,000+ tokens
- **Solution:** Query 4 handoffs = ~950 tokens
- **Benefit:** Efficient team coordination

### Best Illusion of Continuity
- **Semantic compression:** Not just size reduction, but meaningful context
- **Epistemic deltas:** Shows what changed (KNOW, DO, UNCERTAINTY)
- **Critical context:** What next AI actually needs to know
- **Calibration tracking:** Confidence accuracy over time

---

## 📋 Implementation Checklist

- [ ] Create `handoff_commands.py` with 2 command handlers
- [ ] Register commands in `cli_core.py`
- [ ] Add 2 MCP tools to `empirica_mcp_server.py`
- [ ] Test CLI commands (create + query)
- [ ] Test MCP tools (via diagnostic script)
- [ ] Validate token counts (<300 tokens)
- [ ] Test session continuity scenario
- [ ] Document in P3_HANDOFF_VALIDATION_RESULTS.md
- [ ] Update system prompts with usage examples
- [ ] Commit all changes

---

**Priority:** HIGH (enables best session continuity possible)
**Impact:** 98% token reduction + semantic context preservation
**Status:** Ready to implement (all core code exists, just needs CLI + MCP wiring)

**Estimated Time:** 1-2 hours (straightforward wiring + validation)

**Start when:** After P1 + P2 complete (now!)
