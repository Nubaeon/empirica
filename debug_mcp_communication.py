#!/usr/bin/env python3
"""
Debug script for MCP communication issues.

Usage:
    python3 debug_mcp_communication.py

Tests:
1. Direct Python API calls (should work)
2. MCP tool availability (via stdio)
3. Actual tool invocation via MCP protocol

This helps isolate whether the issue is:
- Python environment (imports, dependencies)
- MCP server startup
- MCP protocol communication
- Tool implementation
"""

import sys
import json
import subprocess
from pathlib import Path

print("=" * 80)
print("🔧 Empirica MCP Communication Diagnostics")
print("=" * 80)

# Test 1: Direct Python API
print("\n📦 Test 1: Direct Python API Calls")
print("-" * 80)

try:
    sys.path.insert(0, str(Path(__file__).parent))

    from empirica.data.session_database import SessionDatabase
    print("✅ SessionDatabase imported")

    # Test actual database operation
    db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
    sessions = db.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    db.close()
    print(f"✅ Database accessible ({sessions} sessions found)")

    from empirica.core.goals.repository import GoalRepository
    print("✅ GoalRepository imported")

    # Test goal repository
    repo = GoalRepository()
    # Just test that we can query - get_session_goals requires session_id
    test_goal = repo.get_goal("test-nonexistent-id")  # Returns None, but tests DB access
    repo.close()
    print(f"✅ GoalRepository functional (database accessible)")

    print("\n✅ Direct Python API: WORKING")

except Exception as e:
    print(f"\n❌ Direct Python API: FAILED")
    print(f"   Error: {e}")
    sys.exit(1)

# Test 2: MCP Server Startup
print("\n🚀 Test 2: MCP Server Startup")
print("-" * 80)

mcp_server_path = Path(__file__).parent / "mcp_local" / "empirica_mcp_server.py"
venv_python = Path(__file__).parent / ".venv-mcp" / "bin" / "python3"

if not mcp_server_path.exists():
    print(f"❌ MCP server not found: {mcp_server_path}")
    sys.exit(1)

if not venv_python.exists():
    print(f"❌ Venv python not found: {venv_python}")
    sys.exit(1)

print(f"✅ MCP server found: {mcp_server_path}")
print(f"✅ Venv python found: {venv_python}")

# Test 3: MCP Protocol Communication
print("\n🔌 Test 3: MCP Protocol Communication")
print("-" * 80)

try:
    # Start MCP server as subprocess
    env = {
        "PYTHONPATH": str(Path(__file__).parent),
        "LD_LIBRARY_PATH": "",
        "EMPIRICA_ENABLE_MODALITY_SWITCHER": "false"
    }

    proc = subprocess.Popen(
        [str(venv_python), str(mcp_server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )

    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "debug-client",
                "version": "1.0.0"
            }
        }
    }

    print(f"📤 Sending initialize request...")
    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()

    # Read response (with timeout)
    import select
    ready = select.select([proc.stdout], [], [], 5.0)

    if ready[0]:
        response_line = proc.stdout.readline()
        print(f"📥 Received response: {response_line[:200]}...")

        response = json.loads(response_line)
        if "result" in response:
            print("✅ MCP server initialized successfully")
            print(f"   Server: {response['result'].get('serverInfo', {})}")
            print(f"   Capabilities: {list(response['result'].get('capabilities', {}).keys())}")
        else:
            print(f"⚠️  Unexpected response: {response}")
    else:
        print("❌ No response from MCP server (timeout)")
        stderr = proc.stderr.read()
        if stderr:
            print(f"   Server stderr: {stderr}")

    # Send tools/list request
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }

    print(f"\n📤 Requesting tool list...")
    proc.stdin.write(json.dumps(list_tools_request) + "\n")
    proc.stdin.flush()

    ready = select.select([proc.stdout], [], [], 5.0)
    if ready[0]:
        response_line = proc.stdout.readline()
        response = json.loads(response_line)

        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} MCP tools:")
            for tool in tools[:5]:  # Show first 5
                print(f"   - {tool['name']}: {tool['description'][:60]}...")
            if len(tools) > 5:
                print(f"   ... and {len(tools) - 5} more")
        else:
            print(f"⚠️  Unexpected response: {response}")
    else:
        print("❌ No response to tools/list (timeout)")

    # Test bootstrap_session tool
    print(f"\n📤 Testing bootstrap_session tool...")
    bootstrap_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "bootstrap_session",
            "arguments": {
                "ai_id": "debug-test",
                "session_type": "development",
                "bootstrap_level": 2
            }
        }
    }

    proc.stdin.write(json.dumps(bootstrap_request) + "\n")
    proc.stdin.flush()

    ready = select.select([proc.stdout], [], [], 10.0)
    if ready[0]:
        response_line = proc.stdout.readline()
        print(f"   Raw response: {response_line[:300]}...")
        response = json.loads(response_line)

        if "result" in response:
            content = response["result"].get("content", [])
            if content:
                text_content = content[0].get("text", "")
                print(f"   Content text: {text_content[:200]}...")
                if text_content:
                    result_data = json.loads(text_content)
                    if result_data.get("ok"):
                        print(f"✅ bootstrap_session tool working!")
                        print(f"   Session ID: {result_data.get('session_id', 'N/A')[:8]}...")
                        print(f"   Components: {len(result_data.get('components_loaded', []))}")
                    else:
                        print(f"⚠️  Tool returned error: {result_data.get('error')}")
                else:
                    print(f"⚠️  Empty text content")
            else:
                print(f"⚠️  Empty response content")
        elif "error" in response:
            print(f"❌ MCP Error: {response['error']}")
        else:
            print(f"⚠️  Unexpected response: {response}")
    else:
        print("❌ No response to bootstrap_session (timeout)")
        stderr = proc.stderr.read()
        if stderr:
            print(f"   Server stderr: {stderr}")

    proc.terminate()
    proc.wait(timeout=2)

    print("\n✅ MCP Protocol Communication: WORKING")

except Exception as e:
    print(f"\n❌ MCP Protocol Communication: FAILED")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    if proc:
        proc.terminate()

# Summary
print("\n" + "=" * 80)
print("📊 Diagnostic Summary")
print("=" * 80)
print("""
If all tests passed:
✅ Your MCP setup is working correctly

If Direct Python API works but MCP fails:
🔧 Issue is in MCP communication layer
   - Check MCP client configuration
   - Verify stdio transport is working
   - Check for JSON parsing errors in client

If Direct Python API fails:
🔧 Issue is in Python environment
   - Check PYTHONPATH includes empirica directory
   - Verify all dependencies installed in venv
   - Check for import conflicts

Common fixes:
1. Restart MCP client (Rovo Dev, Mini-agent, etc.)
2. Verify mcp.json has correct paths
3. Check venv has all dependencies: pip install -r requirements.txt
4. Ensure PYTHONPATH is set in MCP server env
""")
