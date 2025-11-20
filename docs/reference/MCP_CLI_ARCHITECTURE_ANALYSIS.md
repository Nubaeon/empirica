# MCP vs CLI Architecture Analysis for AI Agents

## 🎯 Core Question

**For AI agents using Empirica, what's better:**
- Option A: Direct MCP tools (current broken async approach)
- Option B: MCP → CLI wrapper (subprocess calls)
- Option C: Pure CLI invocation (no MCP)

## 📊 AI Memory & Token Considerations

### Does AI "forget" CLI commands vs MCP tools?

**Short answer: No meaningful difference**

**Why:**
1. **System prompts persist** - Whether you document MCP tools or CLI commands, they appear in the system prompt
2. **Context window is the bottleneck** - Not the interface type
3. **Tool discovery** - Both MCP and CLI have help/discovery mechanisms

**Token comparison:**

**MCP Tool Schema (per tool):**
```json
{
  "name": "bootstrap_session",
  "description": "Bootstrap new Empirica session...",
  "inputSchema": {
    "type": "object",
    "properties": {
      "ai_id": {"type": "string", "description": "..."},
      "session_type": {"type": "string", "description": "..."},
      "bootstrap_level": {"type": "integer", "description": "..."}
    }
  }
}
```
**~200 tokens per tool** × 37 tools = **~7,400 tokens** (tool schemas only, sent on every MCP initialization)

**CLI Documentation:**
```markdown
## Bootstrap Session
empirica bootstrap --ai-id=<id> --session-type=<type> --level=<0-2> --output json
```
**~50 tokens per command** × 37 commands = **~1,850 tokens** (in system prompt, not sent per-call)

**Key insight:** MCP tool schemas are verbose JSON, CLI commands are terse bash-style.

## 🏗️ Architecture Comparison

### Current State (Broken)

```
AI Agent → MCP stdio → empirica_mcp_server.py (async) → Python imports → Database
                                    ↑
                              (async/await bugs)
```

**Issues:**
- ❌ Async/await errors (`dict can't be used in await`)
- ❌ ~5000 lines of duplicated logic in MCP server
- ❌ Maintaining two codebases (CLI + MCP server)
- ❌ MCP server bypasses CLI entirely (different code paths)

### Option A: Fix Async in MCP Server

```
AI Agent → MCP stdio → empirica_mcp_server.py (fixed async) → Python imports → Database
```

**Pros:**
- ✅ Native MCP protocol (might be faster?)
- ✅ No subprocess overhead

**Cons:**
- ❌ ~5000 lines to maintain separately from CLI
- ❌ Two code paths for same operations (CLI vs MCP)
- ❌ Async bugs are tricky and will recur
- ❌ Testing is harder (need MCP client vs simple bash)

### Option B: MCP → CLI Wrapper

```
AI Agent → MCP stdio → Thin MCP wrapper → subprocess → empirica CLI → Python API → Database
```

**Pros:**
- ✅ **Single source of truth** (CLI is the implementation)
- ✅ MCP server is ~500 lines (just argument mapping)
- ✅ No async issues (subprocess.run is sync)
- ✅ Easy testing (`empirica bootstrap --output json` works directly)
- ✅ CLI already has all the logic
- ✅ Humans and AIs use same code path

**Cons:**
- ⚠️ Subprocess overhead (~10-50ms per call)
- ⚠️ Need `--output json` flag on all CLI commands

### Option C: Pure CLI (No MCP)

```
AI Agent → Bash tool → empirica CLI → Python API → Database
```

**Pros:**
- ✅ Simplest possible (no MCP layer at all)
- ✅ Works with any AI that has bash access
- ✅ Zero maintenance on MCP side

**Cons:**
- ❌ Loses MCP schema validation
- ❌ Loses MCP tool discovery
- ❌ Loses IDE integration (if that matters)
- ❌ AI has to parse bash output vs structured JSON

## 🤖 What Works Best for AI Agents?

### Token Efficiency

| Interface | Tool Discovery | Per-Call Overhead | Total Tokens |
|-----------|---------------|-------------------|--------------|
| MCP tools | ~7,400 tokens (schemas) | ~50 tokens (call) | High |
| CLI via MCP | ~1,850 tokens (docs) | ~100 tokens (subprocess + parse) | Medium |
| Pure CLI | ~1,850 tokens (docs) | ~50 tokens (bash call) | Low |

**Winner: Pure CLI or CLI-via-MCP (both ~75% token reduction vs pure MCP)**

### Reliability

| Interface | Code Complexity | Bug Surface | Maintenance |
|-----------|----------------|-------------|-------------|
| MCP tools | ~5000 lines | Async bugs, JSON serialization | High |
| CLI via MCP | ~500 lines (wrapper) + CLI | Subprocess failures | Low |
| Pure CLI | ~0 lines (just CLI) | CLI bugs only | Lowest |

**Winner: Pure CLI (simplest, most reliable)**

### AI Developer Experience

| Interface | Discoverability | Error Messages | Testing |
|-----------|----------------|----------------|---------|
| MCP tools | Excellent (tool list) | Structured JSON | Need MCP client |
| CLI via MCP | Good (tool list + help) | Structured JSON | `empirica <cmd> --output json` |
| Pure CLI | Good (help text) | Human-readable text | `empirica <cmd>` |

**Winner: CLI via MCP (combines MCP discovery + CLI simplicity)**

## 🎯 Recommendation: Hybrid Approach

**Split tools into two categories:**

### Category 1: Stateless/Fast → Pure MCP
**Keep in MCP server (no CLI call):**
- `get_empirica_introduction` - Just returns markdown text
- `get_workflow_guidance` - Just returns guidance
- `cli_help` - Just returns help text

**Why:** No database, no async, just string returns. Fast and simple.

**Implementation:** ~200 lines in MCP server

### Category 2: Stateful/Complex → CLI Wrapper
**Route through CLI:**
- All CASCADE workflow tools (bootstrap, preflight, check, postflight)
- All goal/task management tools
- All checkpoint tools
- All database operations

**Why:** Complex logic, already implemented in CLI, battle-tested.

**Implementation:** ~300 lines in MCP server (thin wrappers)

### Example: Hybrid MCP Server

```python
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    # Category 1: Handle directly (stateless, fast)
    if name == "get_empirica_introduction":
        intro_text = "# Empirica Framework\n\n..."  # Static content
        return [types.TextContent(type="text", text=intro_text)]

    if name == "get_workflow_guidance":
        guidance = {...}  # Static dict
        return [types.TextContent(type="text", text=json.dumps(guidance))]

    # Category 2: Route through CLI (stateful, complex)
    elif name in CLI_ROUTED_TOOLS:
        return await route_to_cli(name, arguments)

async def route_to_cli(tool_name: str, arguments: dict) -> list[types.TextContent]:
    """Route tool call to empirica CLI"""

    # Map MCP tool name → CLI command
    cli_map = {
        "bootstrap_session": ["bootstrap"],
        "execute_preflight": ["preflight"],
        "submit_preflight_assessment": ["preflight-submit"],
        "create_goal": ["goals-create"],
        "add_subtask": ["goals-add-subtask"],
        "complete_subtask": ["goals-complete-subtask"],
        # ... etc
    }

    cmd = ["empirica"] + cli_map[tool_name]

    # Map arguments to CLI flags
    for key, value in arguments.items():
        if key == "session_id":
            cmd += ["--session-id", value]
        elif key == "ai_id":
            cmd += ["--ai-id", value]
        # ... etc

    cmd += ["--output", "json"]  # Critical: get structured output

    # Execute CLI command
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=EMPIRICA_ROOT)

    if result.returncode == 0:
        return [types.TextContent(type="text", text=result.stdout)]
    else:
        return [types.TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": result.stderr,
            "command": " ".join(cmd)
        }))]
```

**Total MCP server size:** ~500 lines (vs 5000 currently)

## 📈 Long-term AI Usage Pattern

### Observation from Real Sessions

**AI agents typically:**
1. **Bootstrap once** at session start
2. **Execute CASCADE workflow** 2-5 times per task
3. **Query state occasionally** (get_epistemic_state, get_goal_progress)
4. **Create checkpoints** every ~30 minutes

**Token impact:**
- MCP tool schemas: Sent on **every** MCP connection (~7,400 tokens each time)
- CLI documentation: In system prompt **once** (~1,850 tokens total)

**With memory compression (Claude Code, long sessions):**
- MCP: Re-sends schemas after each compression
- CLI: Docs persist in system prompt

**Winner: CLI approach** (lower token load over long sessions)

## 🚀 Implementation Plan

### Phase 1: Add `--output json` to All CLI Commands (1-2 hours)
```bash
empirica bootstrap --ai-id=test --level=2 --output json
# Returns: {"ok": true, "session_id": "...", "components": [...]}

empirica goals-create --session-id=X --objective="..." --output json
# Returns: {"ok": true, "goal_id": "..."}
```

### Phase 2: Create Thin MCP Wrapper (2-3 hours)
- ~500 lines total
- Maps MCP tool calls → CLI commands
- Handles argument conversion
- Returns CLI JSON output

### Phase 3: Test & Deploy (1 hour)
- Test each tool via MCP
- Update system prompts
- Deploy to Rovo Dev, Mini-agent, Claude Code

**Total effort:** ~4-6 hours (vs weeks debugging async issues)

## 🎯 Final Recommendation

**Implement Option B: Hybrid MCP → CLI Wrapper**

**Rationale:**
1. ✅ **75% token reduction** vs pure MCP
2. ✅ **Single source of truth** (CLI is implementation)
3. ✅ **No async bugs** (subprocess is sync)
4. ✅ **Easy testing** (test CLI directly)
5. ✅ **Best for AIs** (combines MCP discovery + CLI simplicity)
6. ✅ **Production-ready** (battle-tested CLI code)

**AIs won't "forget" CLI commands** - they're documented in system prompts just like MCP tools. The interface doesn't matter for memory, but token efficiency and reliability do.

---

**Next Steps:**
1. Add `--output json` flag to all CLI commands
2. Rewrite MCP server as thin CLI wrapper (~500 lines)
3. Test with diagnostic script
4. Deploy to all agents
