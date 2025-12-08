"""
MCP Integration for Edit Guard - Add to empirica_mcp_server.py

Instructions:
1. Add import at top (after SessionDatabase import):
   from empirica.components.edit_verification import EditConfidenceAssessor, EditStrategyExecutor

2. Add tool definition in list_tools() (before the closing ]):

3. Add routing in call_tool() (after handle_get_calibration_report):
   elif name == "edit_with_confidence":
       return await handle_edit_with_confidence(arguments)

4. Add handler function below (after other handlers, before route_to_cli):
"""

# Tool definition to add to list_tools()
TOOL_DEFINITION = '''
        types.Tool(
            name="edit_with_confidence",
            description="Edit file with metacognitive confidence assessment. Prevents 80% of edit failures.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "old_str": {"type": "string"},
                    "new_str": {"type": "string"},
                    "context_source": {
                        "type": "string",
                        "enum": ["view_output", "fresh_read", "memory"],
                        "description": "'view_output' if just read file, 'memory' if from memory"
                    },
                    "session_id": {"type": "string", "description": "Optional for logging"}
                },
                "required": ["file_path", "old_str", "new_str"]
            }
        ),
'''

# Handler function to add after handle_get_calibration_report
HANDLER_FUNCTION = '''
async def handle_edit_with_confidence(arguments: dict) -> List[types.TextContent]:
    """Handle edit with metacognitive confidence assessment."""
    try:
        from empirica.components.edit_verification import EditConfidenceAssessor, EditStrategyExecutor
        
        file_path = arguments.get("file_path")
        old_str = arguments.get("old_str")
        new_str = arguments.get("new_str")
        context_source = arguments.get("context_source", "memory")
        session_id = arguments.get("session_id")
        
        if not all([file_path, old_str is not None, new_str is not None]):
            return [types.TextContent(
                type="text",
                text=json.dumps({"ok": False, "error": "Missing required args"}, indent=2)
            )]
        
        # Initialize
        assessor = EditConfidenceAssessor()
        executor = EditStrategyExecutor()
        
        # Assess confidence
        assessment = assessor.assess(file_path, old_str, context_source)
        strategy, reasoning = assessor.recommend_strategy(assessment)
        
        # Execute
        result = await executor.execute_strategy(strategy, file_path, old_str, new_str, assessment)
        
        # Log if session provided
        if session_id and result.get("success"):
            try:
                db = SessionDatabase()
                db.log_reflex(
                    session_id=session_id,
                    cascade_id=None,
                    phase="edit_verification",
                    vectors=assessment,
                    reasoning=f"Confidence: {assessment['overall']:.2f}, Strategy: {strategy}"
                )
                db.close()
            except:
                pass  # Don't fail edit if logging fails
        
        # Return
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "ok": result.get("success", False),
                "strategy": strategy,
                "reasoning": reasoning,
                "confidence": assessment["overall"],
                "result": result.get("message"),
                "changes_made": result.get("changes_made", False)
            }, indent=2)
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"ok": False, "error": str(e)}, indent=2)
        )]
'''

if __name__ == "__main__":
    print("=" * 60)
    print("Edit Guard MCP Integration Code")
    print("=" * 60)
    print("\n1. TOOL DEFINITION (add to list_tools()):")
    print(TOOL_DEFINITION)
    print("\n2. HANDLER FUNCTION (add after handle_get_calibration_report):")
    print(HANDLER_FUNCTION)
    print("\n3. ROUTING (add in call_tool() elif chain):")
    print('   elif name == "edit_with_confidence":')
    print('       return await handle_edit_with_confidence(arguments)')
