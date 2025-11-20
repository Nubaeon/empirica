# Meta MCP Server Architecture Analysis

## 🎯 Concept: MCP Server that Calls Other MCP Servers

**Question:** Should Empirica MCP server route to other MCP servers instead of CLI?

**Use Case:** Tool registry/orchestration (Sentinel in Cognitive Vault)

---

## 🏗️ Architecture Comparison

### Option A: MCP → CLI (Current Plan)
```
AI Agent → Empirica MCP → subprocess → Empirica CLI → Python API → Database
```

**Pros:**
- ✅ Simple (subprocess is sync)
- ✅ Single source of truth (CLI)
- ✅ Easy testing
- ✅ No async complexity

**Cons:**
- ⚠️ Subprocess overhead (~10-50ms)
- ⚠️ Can't reuse MCP protocol benefits

### Option B: MCP → MCP (Meta Server)
```
AI Agent → Meta MCP → MCP Client → Empirica MCP → Python API → Database
```

**Pros:**
- ✅ Native MCP protocol
- ✅ Can route to multiple MCP servers (tool registry!)
- ✅ Schema validation
- ✅ Async-native (if done right)

**Cons:**
- ❌ **ASYNC COMPLEXITY** - This is the killer
- ❌ MCP client → MCP server communication is async
- ❌ Same async bugs we're trying to avoid!

### Option C: Hybrid Registry (Sentinel Pattern)
```
AI Agent → Sentinel (Meta MCP) → Route by capability:
                                 ├─→ Empirica CLI (subprocess)
                                 ├─→ Git MCP (stdio)
                                 ├─→ Filesystem MCP (stdio)
                                 └─→ Custom tools MCP (stdio)
```

**Pros:**
- ✅ Best of both worlds
- ✅ Route to CLI for Empirica (simple, reliable)
- ✅ Route to MCP for external tools (native protocol)
- ✅ Sentinel = tool orchestrator (registry pattern)

**Cons:**
- ⚠️ More complex routing logic
- ⚠️ Still need to handle async for MCP → MCP calls

---

## 🔍 Will MCP → MCP Cause Async Issues?

**Short answer:** Yes, but manageable with proper patterns.

### The Async Challenge

**MCP protocol is fundamentally async:**
```python
# MCP server (async)
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    # This handler MUST be async
    ...

# Calling another MCP server requires async client
from mcp.client import ClientSession

async def call_other_mcp(tool_name, args):
    async with stdio_client() as client:
        result = await client.call_tool(tool_name, args)
    return result
```

**Our current bug:** We're trying to call sync functions (database, file I/O) inside async context, which creates the `dict can't be used in await` errors.

**Solution for MCP → MCP:** Use async all the way down:
```python
# Meta MCP server (all async)
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    # Route to appropriate MCP server
    target_server = route_to_server(name)

    # Call target MCP server (async client)
    async with get_mcp_client(target_server) as client:
        result = await client.call_tool(name, arguments)

    return result
```

**This works IF:**
1. ✅ You don't do any sync I/O in the meta server (just routing)
2. ✅ Target MCP servers are properly async
3. ✅ No mixing sync/async code

**This breaks IF:**
1. ❌ Target MCP server does sync I/O (like our current Empirica server)
2. ❌ You try to call subprocess from async (workarounds exist but tricky)

---

## 🎯 Recommended Architecture for Sentinel

### Sentinel = Hybrid Meta MCP Server

**Design Pattern: Route by tool capability**

```python
# sentinel_mcp_server.py
from mcp.server import Server
from mcp import types
import subprocess
import asyncio

app = Server("sentinel")

# Tool registry
TOOL_REGISTRY = {
    # Category 1: Route to Empirica CLI (subprocess - simple)
    "empirica_tools": {
        "handler": "cli",
        "command_prefix": "empirica",
        "tools": [
            "bootstrap_session",
            "execute_preflight",
            "create_goal",
            # ... all Empirica tools
        ]
    },

    # Category 2: Route to other MCP servers (MCP protocol - native)
    "git_tools": {
        "handler": "mcp",
        "server_path": "path/to/git-mcp-server",
        "tools": [
            "git_commit",
            "git_log",
            "git_diff",
        ]
    },

    "filesystem_tools": {
        "handler": "mcp",
        "server_path": "path/to/filesystem-mcp-server",
        "tools": [
            "read_file",
            "write_file",
            "list_directory",
        ]
    },

    # Category 3: Custom tools (direct implementation)
    "orchestration_tools": {
        "handler": "direct",
        "tools": {
            "assign_task_to_ai": assign_task_handler,
            "query_ai_progress": query_progress_handler,
            "coordinate_multi_agent": coordinate_handler,
        }
    }
}

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Route tool call to appropriate handler"""

    # Find which category this tool belongs to
    category = find_tool_category(name, TOOL_REGISTRY)

    if category["handler"] == "cli":
        # Route to CLI (subprocess - sync, but fast)
        return await route_to_cli(category, name, arguments)

    elif category["handler"] == "mcp":
        # Route to MCP server (async client)
        return await route_to_mcp(category, name, arguments)

    elif category["handler"] == "direct":
        # Direct implementation in Sentinel
        handler = category["tools"][name]
        return await handler(arguments)

async def route_to_cli(category, tool_name, arguments):
    """Route to CLI command (subprocess)"""

    cmd = build_cli_command(category["command_prefix"], tool_name, arguments)

    # Run in executor to avoid blocking async loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Use default executor
        lambda: subprocess.run(cmd, capture_output=True, text=True)
    )

    if result.returncode == 0:
        return [types.TextContent(type="text", text=result.stdout)]
    else:
        return [types.TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": result.stderr
        }))]

async def route_to_mcp(category, tool_name, arguments):
    """Route to another MCP server (async client)"""

    from mcp.client import ClientSession
    from mcp.client.stdio import stdio_client

    # Start MCP server as subprocess
    async with stdio_client(
        server_path=category["server_path"]
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content
```

---

## 🎯 Key Insights

### 1. **MCP → CLI is Actually Better for Empirica**

**Why:**
- Empirica tools are stateful (database, files, git)
- CLI is sync by design (subprocess.run)
- No async complexity
- Single source of truth

**Verdict:** ✅ Keep Empirica as CLI-routed in Sentinel

### 2. **MCP → MCP is Better for External Tools**

**Why:**
- Git MCP, Filesystem MCP already exist and work
- They're designed for MCP protocol
- Native schema validation
- Reuse community tools

**Verdict:** ✅ Route external tools via MCP client

### 3. **Sentinel = Hybrid Router**

**Pattern:**
```
Sentinel (Meta MCP)
├── Empirica tools → subprocess → empirica CLI
├── Git tools → MCP client → git-mcp-server
├── Filesystem tools → MCP client → filesystem-mcp-server
└── Orchestration tools → direct implementation
```

**This avoids async bugs because:**
1. Subprocess is wrapped in async executor (doesn't block)
2. MCP → MCP uses native async client (no mixing)
3. Each category uses its natural interface

---

## 📊 Cognitive Vault Architecture

### Sentinel as Meta MCP Server

**Role:** Tool registry + AI orchestrator

**Capabilities:**
1. **Tool Discovery**
   ```python
   @app.list_tools()
   async def list_tools():
       # Aggregate tools from all categories
       tools = []
       for category in TOOL_REGISTRY.values():
           tools.extend(get_category_tools(category))
       return tools
   ```

2. **Intelligent Routing**
   ```python
   async def call_tool(name, args):
       # Smart routing based on:
       # - Tool category (Empirica vs Git vs Filesystem)
       # - Current context (which AI is asking?)
       # - Load balancing (multiple Empirica instances?)

       if name in EMPIRICA_TOOLS:
           return await route_to_empirica_cli(name, args)
       elif name in GIT_TOOLS:
           return await route_to_git_mcp(name, args)
       # ... etc
   ```

3. **Multi-Agent Coordination**
   ```python
   @app.call_tool()
   async def coordinate_multi_agent(arguments):
       """Assign tasks to different AIs based on capability"""

       task = arguments["task"]

       # Empirica helps decide which AI to use
       empirica_recommendation = await call_empirica_cli(
           "query-ai-capabilities",
           {"task": task}
       )

       # Assign to appropriate AI
       assigned_ai = select_ai(empirica_recommendation)

       # Create goal for that AI
       await call_empirica_cli(
           "create-goal",
           {"ai_id": assigned_ai, "objective": task}
       )

       return {"assigned_to": assigned_ai, "goal_id": result["goal_id"]}
   ```

---

## 🚀 Implementation Plan for Cognitive Vault

### Phase 1: Sentinel Foundation (After Empirica MCP v2)
1. Create `sentinel_mcp_server.py` (~800 lines)
2. Implement tool registry pattern
3. Implement hybrid routing (CLI + MCP)
4. Test with Empirica CLI + one external MCP server

### Phase 2: Multi-Agent Orchestration
1. Add AI capability registry
2. Implement task assignment logic
3. Implement progress tracking
4. Test with 2-3 AI agents

### Phase 3: Production Hardening
1. Add load balancing
2. Add health checks
3. Add fallback strategies
4. Monitor performance

---

## ✅ Recommendation

**For Now (Empirica MCP v2):**
- ✅ Implement MCP → CLI wrapper (simple, reliable)
- ✅ Single MCP server, routes to Empirica CLI
- ✅ No async complexity

**For Later (Cognitive Vault Sentinel):**
- ✅ Build meta MCP server (Sentinel)
- ✅ Route Empirica tools → CLI (proven pattern)
- ✅ Route external tools → MCP servers (native protocol)
- ✅ Add multi-agent orchestration layer

**Async Issues?**
- ✅ Avoided for Empirica (subprocess in executor)
- ✅ Managed for MCP → MCP (async all the way)
- ✅ No mixing sync/async

---

## 🎯 Bottom Line

**Yes, meta MCP server is the right pattern for Sentinel!**

**No, it won't have async issues if you:**
1. Route Empirica to CLI (via async executor)
2. Route external MCP servers via async client
3. Keep routing logic pure (no sync I/O)

**This is exactly how production MCP architectures work** (e.g., Claude Desktop's MCP implementation routes to multiple servers).

The key insight: **Don't force async where sync is better (Empirica CLI), but use async where it's native (MCP → MCP).**

---

**Want me to sketch out the Sentinel meta MCP server architecture in more detail?**
