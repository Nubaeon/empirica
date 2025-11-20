#!/usr/bin/env python3
"""
Test 2: MCP Tool Registration (Phase 2 Validation) - Simplified
Verify MCP tools are registered with correct names from corrected document.
Based on docs/current_work/MINIMAX_PHASE2_CORRECTED_TASKS.md
"""

import re

def main():
    print("🔧 Test 2: MCP Tool Registration (Simplified)")
    print("=" * 50)
    
    try:
        # Read MCP server file
        with open('mcp_local/empirica_mcp_server.py', 'r') as f:
            content = f.read()
        
        print("🔍 Analyzing MCP server file...")
        
        # Define the CORRECT Phase 2 tools from the corrected document
        phase2_tools = [
            'query_git_progress',     # ✅ CORRECT NAME (not query_goal_timeline)
            'get_team_progress',      # ✅ CORRECT NAME 
            'get_unified_timeline'    # ✅ CORRECT NAME (not query_commits_by_date)
        ]
        
        # Define the INCORRECT tool names from the original document
        incorrect_names = [
            'query_goal_timeline',    # ❌ Wrong name (should be query_git_progress)
            'query_commits_by_date'   # ❌ Wrong name (should be get_unified_timeline)
        ]
        
        print("\n🔍 Verifying Phase 2 tool names...")
        found_correct = []
        found_incorrect = []
        
        # Check for correct tool names
        for tool_name in phase2_tools:
            # Look for tool registration pattern
            pattern = rf'types\.Tool\(\s*name="{tool_name}"'
            if re.search(pattern, content):
                found_correct.append(tool_name)
                print(f"✅ CORRECT tool registered: {tool_name}")
            else:
                print(f"❌ Missing CORRECT tool: {tool_name}")
        
        # Check for incorrect tool names (should NOT be present)
        for tool_name in incorrect_names:
            pattern = rf'types\.Tool\(\s*name="{tool_name}"'
            if re.search(pattern, content):
                found_incorrect.append(tool_name)
                print(f"⚠️  WRONG tool name found: {tool_name} (should be corrected)")
        
        # Summary
        print("\n" + "=" * 50)
        total_correct = len(found_correct)
        total_expected = len(phase2_tools)
        
        if total_correct == total_expected and not found_incorrect:
            print(f"✅ ALL PHASE 2 MCP TOOLS REGISTERED WITH CORRECT NAMES!")
            print(f"   Expected: {total_expected} tools")
            print(f"   Found: {total_correct} correct tools")
            print(f"   Zero wrong tools: ✅")
            return True
        else:
            print("❌ MCP TOOL REGISTRATION ISSUES:")
            print(f"   Correct tools found: {total_correct}/{total_expected}")
            print(f"   Wrong tools found: {len(found_incorrect)}")
            if found_incorrect:
                print(f"   Wrong tools: {found_incorrect}")
            return False
            
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\nTest 2 Result: {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)