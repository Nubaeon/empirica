#!/usr/bin/env python3
"""
Test 2: MCP Tool Registration (Phase 2 Validation)
Verify MCP tools are registered with correct names from corrected document.
Based on docs/current_work/MINIMAX_PHASE2_CORRECTED_TASKS.md
"""

import sys
import subprocess
import json
from pathlib import Path

def main():
    print("🔧 Test 2: MCP Tool Registration")
    print("=" * 50)
    
    try:
        # Import and inspect MCP server directly
        print("🔍 Testing MCP server import...")
        
        # Add mcp_local to Python path
        sys.path.insert(0, str(Path(__file__).parent / "mcp_local"))
        
        # Import the MCP server module to inspect registered tools
        from empirica_mcp_server import EmpiricaMCPServer
        
        # Create server instance to get registered tools
        server = EmpiricaMCPServer()
        
        # Get list of all registered tools
        tools = []
        for tool_name in dir(server):
            if not tool_name.startswith('_') and callable(getattr(server, tool_name)):
                tools.append(tool_name)
        
        print(f"✅ MCP server loaded successfully")
        print(f"   Total tools found: {len(tools)}")
        
        # Define the CORRECT Phase 2 tools from the corrected document
        phase2_tools = [
            'query_git_progress',     # ✅ CORRECT NAME (not query_goal_timeline)
            'get_team_progress',      # ✅ CORRECT NAME 
            'get_unified_timeline'    # ✅ CORRECT NAME (not query_commits_by_date)
        ]
        
        print("\n🔍 Verifying Phase 2 tool names...")
        missing_tools = []
        wrong_tools = []
        
        for tool_name in phase2_tools:
            if tool_name in tools:
                print(f"✅ MCP tool registered: {tool_name}")
            else:
                missing_tools.append(tool_name)
                print(f"❌ Missing MCP tool: {tool_name}")
        
        # Check for potentially wrong names from original incorrect document
        incorrect_names = ['query_goal_timeline', 'query_commits_by_date']
        for incorrect_name in incorrect_names:
            if incorrect_name in tools:
                wrong_tools.append(incorrect_name)
                print(f"⚠️  WRONG tool name found: {incorrect_name} (should be corrected)")
        
        # Summary
        print("\n" + "=" * 50)
        if not missing_tools and not wrong_tools:
            print("✅ ALL PHASE 2 MCP TOOLS REGISTERED WITH CORRECT NAMES!")
            print(f"   Expected: {len(phase2_tools)} tools")
            print(f"   Found: {len([t for t in phase2_tools if t in tools])} tools")
            return True
        else:
            print("❌ MCP TOOL REGISTRATION ISSUES:")
            if missing_tools:
                print(f"   Missing tools: {missing_tools}")
            if wrong_tools:
                print(f"   Wrong tools: {wrong_tools}")
            return False
            
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)