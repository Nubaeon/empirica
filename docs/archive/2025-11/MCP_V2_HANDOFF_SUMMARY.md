# MCP v2 Architecture - Handoff Summary

## 🎯 Project Status

**Architecture Decision:** Rewrite MCP server as thin CLI wrapper (~500 lines vs 5000)

**Reason:** Current MCP server has async/await bugs preventing tool execution. CLI-based approach is simpler, more reliable, and provides 75% token reduction.

**Work Distribution:**
- **Claude Code:** MCP server v2 architecture (holistic design)
- **Mini-agent:** CLI command implementation (detail work - 15 commands)

---

## ✅ Completed Work (Claude Code)

### 1. Comprehensive Analysis
- ✅ Diagnosed MCP async issue (`object dict can't be used in await expression`)
- ✅ Created diagnostic script (`debug_mcp_communication.py`)
- ✅ Analyzed token efficiency (CLI vs MCP schemas)
- ✅ Documented architecture decision (`MCP_CLI_ARCHITECTURE_ANALYSIS.md`)

### 2. Complete Mapping Specification
- ✅ Mapped all 40 MCP tools to CLI commands (`MCP_CLI_MAPPING_SPEC.md`)
- ✅ Identified 5 existing CLI commands (ready to use)
- ✅ Identified 5 commands needing `--output json` flag
- ✅ Identified 27 new CLI commands needed
- ✅ Prioritized tasks (P0: 10 commands for MVP)

### 3. Goal Creation for Mini-agent
- ✅ Created goal: `b9b8ba19-d8d1-4d76-91da-3ce3e29f17ef`
- ✅ Added 15 subtasks with priorities and estimates
- ✅ Ready for adoption by Mini-agent

---

## 🚀 Mini-agent Task

**Goal ID:** `b9b8ba19-d8d1-4d76-91da-3ce3e29f17ef`

**Objective:** Implement 15 CLI commands with `--output json` support

**Priority:** P0 (blocks MCP v2 server)

**Estimated:** 6-8 hours (24,500 tokens)

### Subtasks Breakdown

#### CRITICAL (6 commands) - Must have for MVP
1. `empirica preflight-submit --session-id=X --vectors='{}' --output json`
2. `empirica check --session-id=X --findings='[]' --unknowns='[]' --output json`
3. `empirica check-submit --session-id=X --vectors='{}' --decision=X --output json`
4. `empirica postflight-submit --session-id=X --vectors='{}' --output json`
5. `empirica goals-create --session-id=X --objective="..." --scope=X --output json`
6. `empirica goals-add-subtask --goal-id=X --description="..." --output json`

#### HIGH (6 commands) - Important for full functionality
7. `empirica goals-complete-subtask --task-id=X --evidence="..." --output json`
8. `empirica goals-progress --goal-id=X --output json`
9. `empirica goals-list --session-id=X --output json`
10. `empirica sessions-resume --ai-id=X --count=N --output json`
11. Add `--output json` to existing `empirica preflight` command
12. Add `--output json` to existing `empirica postflight` command

#### MEDIUM (3 commands) - Nice to have
13. Add `--output json` to existing `empirica calibration` command
14. Add `--output json` to existing `empirica checkpoint-load` command
15. Add `--output json` to existing `empirica checkpoint-diff` command

### How to Adopt Goal (Python API)

```python
import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/empirica')

from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
from empirica.data.session_database import SessionDatabase
from empirica.core.goals.repository import GoalRepository
from empirica.core.tasks.repository import TaskRepository

# 1. Bootstrap your session
config = bootstrap_metacognition("mini-agent", level=2)
db = SessionDatabase()
session_id = db.create_session(
    ai_id="mini-agent",
    bootstrap_level=2,
    components_loaded=len(config),
    user_id=None
)
db.close()

# 2. Adopt the goal
repo = GoalRepository()
goal = repo.get_goal('b9b8ba19-d8d1-4d76-91da-3ce3e29f17ef')
repo.save_goal(goal, session_id)  # Links goal to your session
repo.close()

# 3. Get subtasks
task_repo = TaskRepository()
subtasks = task_repo.get_goal_subtasks('b9b8ba19-d8d1-4d76-91da-3ce3e29f17ef')

for st in subtasks:
    print(f"{st.description} - Status: {st.status.value}")

task_repo.close()
```

### Implementation Pattern (for each command)

```python
# In empirica/cli/command_handlers/workflow_commands.py

def handle_preflight_submit_command(args):
    """Handle preflight-submit command"""
    from empirica.data.session_database import SessionDatabase

    # Parse arguments
    session_id = args.session_id
    vectors = json.loads(args.vectors) if isinstance(args.vectors, str) else args.vectors
    reasoning = args.reasoning

    # Call Python API
    db = SessionDatabase()
    # ... submit preflight logic ...
    db.close()

    # Format output
    result = {
        "ok": True,
        "session_id": session_id,
        "message": "PREFLIGHT assessment submitted",
        # ... more fields ...
    }

    # Output based on format
    if args.output == 'json':
        print(json.dumps(result, indent=2))
    else:
        print(f"✅ PREFLIGHT submitted for session {session_id[:8]}...")
```

### Spec Reference

**Full specification:** `MCP_CLI_MAPPING_SPEC.md`

**Key sections:**
- Complete tool → CLI mapping table
- Implementation patterns
- Testing requirements

---

## 📋 Claude Code Next Steps

**Pending:** Rewrite MCP server v2 as thin CLI wrapper

**Blocked by:** Mini-agent CLI commands (need commands to route to)

**Can Start:** Design MCP server v2 architecture while waiting

**Estimated:** 4-6 hours (after CLI commands ready)

### MCP Server v2 Structure

```
empirica_mcp_server_v2.py (~500 lines)
├── Tool definitions (37 tools)
├── Stateless handlers (3 tools - handle directly)
│   ├── get_empirica_introduction
│   ├── get_workflow_guidance
│   └── cli_help
└── CLI router (34 tools - route to CLI)
    ├── build_cli_command(tool_name, arguments)
    ├── execute_cli_command(cmd)
    └── parse_cli_output(stdout)
```

**Key function:**
```python
def build_cli_command(tool_name: str, arguments: dict) -> list[str]:
    """Map MCP tool call to CLI command"""

    tool_map = {
        "bootstrap_session": ["bootstrap"],
        "execute_preflight": ["preflight"],
        "submit_preflight_assessment": ["preflight-submit"],
        # ... etc
    }

    cmd = ["empirica"] + tool_map[tool_name]

    # Map arguments to CLI flags
    for key, value in arguments.items():
        if isinstance(value, dict) or isinstance(value, list):
            cmd.extend([f"--{key.replace('_', '-')}", json.dumps(value)])
        else:
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])

    cmd.extend(["--output", "json"])  # Always get JSON

    return cmd
```

---

## 🎯 Success Criteria

### Phase 1: CLI Commands (Mini-agent)
- ✅ All 6 CRITICAL commands implemented
- ✅ All commands tested individually
- ✅ JSON output validated
- ✅ Help text updated

### Phase 2: MCP Server v2 (Claude Code)
- ✅ Server ~500 lines (vs 5000 currently)
- ✅ All 37 tools working via CLI
- ✅ No async errors
- ✅ Diagnostic script passes

### Phase 3: Integration Test
- ✅ `python3 debug_mcp_communication.py` → all green
- ✅ `bootstrap_session` works
- ✅ `execute_preflight` → `submit_preflight_assessment` → `execute_postflight` flow works
- ✅ `create_goal` → `add_subtask` → `complete_subtask` flow works

---

## 📊 Benefits of This Approach

| Metric | Old (Pure MCP) | New (CLI Wrapper) | Improvement |
|--------|----------------|-------------------|-------------|
| **Code size** | ~5000 lines | ~500 lines | 90% reduction |
| **Token overhead** | ~7,400 tokens | ~1,850 tokens | 75% reduction |
| **Maintenance** | Dual codebase | Single (CLI) | Simpler |
| **Testing** | Need MCP client | `empirica <cmd>` | Easier |
| **Reliability** | Async bugs | Sync subprocess | More stable |
| **Production** | Risky | Battle-tested CLI | Ready |

---

## 📝 Handoff Instructions for Mini-agent

1. **Read specs:**
   - `MCP_CLI_MAPPING_SPEC.md` - Complete mapping and patterns
   - `MCP_FIX_FOR_MINIMAX.md` - Python API usage (for adoption)

2. **Adopt goal:**
   - Goal ID: `b9b8ba19-d8d1-4d76-91da-3ce3e29f17ef`
   - Use Python API (MCP tools broken - this is what we're fixing!)

3. **Implement commands:**
   - Start with 6 CRITICAL commands
   - Follow pattern in spec
   - Test each command with `--output json`

4. **Mark subtasks complete:**
   - Use `task_repo.complete_subtask(task_id, evidence="commit hash")`

5. **Notify when done:**
   - Claude Code can then implement MCP server v2

---

## 🚀 Timeline

**Mini-agent:** 6-8 hours (CLI commands)
**Claude Code:** 4-6 hours (MCP server v2) - starts after Mini-agent completes CRITICAL commands
**Integration:** 1-2 hours (testing)

**Total:** 11-16 hours

**Parallel opportunity:** Claude Code can design MCP v2 while Mini-agent implements first few commands

---

**Status:** Ready for Mini-agent to begin! 🎯
