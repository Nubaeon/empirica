# CLI vs MCP: The Real Story

## I Was Wrong - CLI Works Fine for AI Agents!

The **Empirica CLI is NOT just for humans**. AI agents can use it directly. The MCP tools are literally just thin wrappers that call the CLI.

### How MCP Tools Work

```python
# MCP Server Code (mcp_local/empirica_mcp_server.py)
tool_map = {
    "execute_preflight": ["preflight", "--prompt-only"],
    "submit_preflight_assessment": ["preflight-submit"],
    ...
}

# When you call execute_preflight(), it literally just runs:
subprocess.run(["empirica", "preflight", "--prompt-only", ...])
```

**MCP tools = Convenience wrappers around CLI commands. That's it.**

## The REAL Issue with Rovodev

Claude rovodev was getting errors NOT because they used CLI instead of MCP, but because:

1. **The `--assessment-json` workflow has a bug** - it hangs even with correct JSON format
2. **The two-step workflow (--prompt-only + preflight-submit) works perfectly**
3. **MCP tools use the working two-step workflow**

## Three Ways to Do PREFLIGHT

### Option 1: MCP Tools (Recommended)

```python
# Step 1: Get prompt
result = execute_preflight(
    session_id="abc123",
    prompt="Implement authentication"
)

# Step 2: Submit assessment
submit_preflight_assessment(
    session_id="abc123",
    vectors={ /* nested structure */ },
    reasoning="..."
)
```

**Behind the scenes:** Calls `empirica preflight --prompt-only` then `empirica preflight-submit`

### Option 2: CLI Two-Step (Equivalent to MCP)

```bash
# Step 1: Get prompt
empirica preflight "Implement authentication" \\
  --ai-id rovodev \\
  --session-id abc123 \\
  --prompt-only

# Returns JSON with self_assessment_prompt

# Step 2: Submit assessment (via preflight-submit CLI)
empirica preflight-submit \\
  --session-id abc123 \\
  --vectors '{"engagement": {...}, "foundation": {...}, ...}' \\
  --reasoning "..."
```

**This is EXACTLY what MCP tools do!**

### Option 3: CLI One-Step (Currently Broken)

```bash
# This SHOULD work but currently hangs:
empirica preflight "task" \\
  --ai-id rovodev \\
  --assessment-json assessment.json
```

**Status:** ⚠️ Has a hanging bug, even with correct JSON format

## Why MCP Tools Exist

MCP tools provide:
1. **Parameter validation** - Schema checks before calling CLI
2. **JSON parsing** - Handles JSON input/output automatically
3. **Error handling** - Better error messages
4. **Convenience** - Don't need to remember CLI flag names

But fundamentally: **MCP tools = CLI commands with a nice interface**

## The Real Solution for Rovodev

**Option A: Use MCP Tools (Easiest)**
```python
execute_preflight(session_id="...", prompt="...")
submit_preflight_assessment(session_id="...", vectors={...})
```

**Option B: Use CLI Two-Step (Equivalent)**
```bash
empirica preflight "task" --prompt-only --ai-id rovodev --session-id sid
empirica preflight-submit --session-id sid --vectors '{...}'
```

**Both work perfectly! MCP is just more convenient.**

## What Needs to be Fixed

The `--assessment-json` workflow should work but doesn't. The bug is in:
`empirica/cli/command_handlers/cascade_commands.py` around line 133-156

Even when provided with correct JSON format, it still hangs waiting for something.

## Bottom Line

1. ✅ CLI works great for AI agents
2. ✅ MCP tools work great (they call CLI)
3. ⚠️ `--assessment-json` has a bug
4. ✅ Two-step workflow (--prompt-only + preflight-submit) works perfectly
5. 💡 Use whichever interface you prefer - they're equivalent!

The documentation I created earlier was based on a false premise that "CLI is for humans only." That's not true. The actual issue is that the one-step `--assessment-json` workflow has a bug.

**For rovodev:** Either use MCP tools OR use CLI two-step. Both work identically.
