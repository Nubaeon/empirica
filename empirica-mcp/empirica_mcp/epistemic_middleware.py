"""
Epistemic Middleware - Wraps MCP tool calls with epistemic self-awareness

Architecture:
1. Tool call arrives → assess epistemic state
2. Route to appropriate mode based on vectors
3. Execute mode behavior
4. Update vectors from results
5. Return enriched response with epistemic context
"""

import json
from typing import List, Dict, Any, Optional
from mcp import types

from .epistemic import (
    EpistemicStateMachine,
    VectorRouter,
    EpistemicModes,
    get_personality
)


class EpistemicMiddleware:
    """
    Epistemic MCP middleware - adds vector-driven self-awareness
    
    Usage:
        middleware = EpistemicMiddleware(personality="balanced_architect")
        
        # On tool call:
        result = await middleware.handle_request(
            tool_name="session_create",
            arguments={"ai_id": "test"},
            original_handler=original_handler_func
        )
    """
    
    def __init__(
        self,
        personality: str = "balanced_architect",
        session_id: Optional[str] = None,
        enable_epistemic: bool = True
    ):
        self.enable_epistemic = enable_epistemic
        self.session_id = session_id
        
        # Initialize epistemic components
        personality_profile = get_personality(personality)
        self.state_machine = EpistemicStateMachine()
        self.router = VectorRouter(personality_profile.thresholds)
        self.modes = EpistemicModes()
        
        # Track request count for state evolution
        self.request_count = 0
    
    async def handle_request(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        original_handler
    ) -> List[types.TextContent]:
        """
        Epistemic request handler - wraps original tool call
        
        Flow:
        1. Assess request → update vectors
        2. Route based on vectors → get mode
        3. Execute mode behavior (might modify/augment request)
        4. Call original handler
        5. Update vectors from result
        6. Return enriched response
        """
        
        # Bypass epistemic if disabled
        if not self.enable_epistemic:
            return await original_handler(tool_name, arguments)
        
        # Skip epistemic for known/safe tools
        # These are standard CLI tools with clear semantics
        # IMPORTANT: Tool names must match exactly what's defined in server.py
        safe_tools = {
            # Stateless tools (handled directly, no CLI)
            'get_empirica_introduction',
            'get_workflow_guidance',
            'cli_help',
            # Session management
            'session_create',
            'session_snapshot',
            'resume_previous_session',  # NOT session_resume
            'memory_compact',
            # CASCADE workflow tools
            'execute_preflight',
            'submit_preflight_assessment',  # NOT preflight_submit
            'execute_check',
            'submit_check_assessment',
            'execute_postflight',
            'submit_postflight_assessment',  # NOT postflight_submit
            # Goal management
            'create_goal',  # NOT goals_create
            'add_subtask',
            'complete_subtask',  # NOT goals_complete
            'get_goal_progress',
            'get_goal_subtasks',
            'list_goals',
            'goals_ready',
            'goals_claim',
            # Breadcrumb logging (session-scoped)
            'finding_log',
            'unknown_log',
            'mistake_log',
            'deadend_log',
            'log_mistake',  # Alternative mistake logging
            # Project operations
            'project_bootstrap',
            # Checkpoint operations
            'create_git_checkpoint',
            'load_git_checkpoint',
            # Handoff operations
            'create_handoff_report',
            'query_handoff_reports',
            # Identity operations
            'create_identity',
            'list_identities',
            'export_public_key',
            'verify_signature',
            # Investigation
            'investigate',
            'discover_goals',
            'resume_goal',
            # Vision
            'vision_analyze',
            'vision_log',
            # Edit verification
            'edit_with_confidence',
            # Reference docs
            'refdoc_add',
            # Calibration
            'get_calibration_report',
            'get_epistemic_state',
            'get_session_summary',
            # Epistemic monitoring
            'epistemics_list',
            'epistemics_show',
            # Human copilot tools
            'monitor',
            'check_drift',
            'issue_list',
            'issue_handoff',
            'workspace_overview',
            'efficiency_report',
            'skill_suggest',
            'workspace_map',
            'unknown_resolve',
        }
        
        # Skip epistemic for safe tools - they have well-defined semantics
        if tool_name in safe_tools:
            self.request_count += 1
            return await original_handler(tool_name, arguments)
        
        self.request_count += 1
        
        # Step 1: Assess request
        request_summary = f"{tool_name}: {json.dumps(arguments, indent=2)[:200]}"
        vectors = self.state_machine.assess_request(request_summary)
        
        # Step 2: Route based on vectors
        routing = self.router.route(vectors, request_summary)
        
        # Step 3: Execute mode behavior
        mode_result = await self._execute_mode(routing.mode, tool_name, arguments)
        
        # Step 4: Call original handler
        try:
            original_result = await original_handler(tool_name, arguments)
            success = True
        except Exception as e:
            original_result = [types.TextContent(
                type="text",
                text=json.dumps({"ok": False, "error": str(e)}, indent=2)
            )]
            success = False
        
        # Step 5: Update vectors from result
        self.state_machine.update_from_action(
            action_type=routing.mode,
            result={"success": success, "data": original_result}
        )
        
        # Step 6: Return enriched response
        return self._enrich_response(original_result, vectors, routing, mode_result)
    
    async def _execute_mode(
        self,
        mode: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute mode-specific behavior"""
        
        session_id = arguments.get("session_id", self.session_id or "unknown")
        
        if mode == "load_context":
            return await self.modes.load_context(
                session_id=session_id,
                project_id=arguments.get("project_id")
            )
        elif mode == "investigate":
            return await self.modes.investigate(
                session_id=session_id,
                query=f"{tool_name} request"
            )
        elif mode == "confident_implementation":
            return await self.modes.confident_implementation(
                session_id=session_id,
                task=tool_name
            )
        elif mode == "cautious_implementation":
            return await self.modes.cautious_implementation(
                session_id=session_id,
                task=tool_name
            )
        elif mode == "clarify":
            return await self.modes.clarify(
                session_id=session_id,
                unclear_request=f"{tool_name}: {arguments}"
            )
        else:
            return {"success": True, "mode": "unknown"}
    
    def _enrich_response(
        self,
        original_result: List[types.TextContent],
        vectors: Dict[str, float],
        routing: Any,
        mode_result: Dict[str, Any]
    ) -> List[types.TextContent]:
        """
        Enrich response with epistemic context
        
        Adds:
        - Current epistemic vectors
        - Routing decision
        - Mode guidance (if applicable)
        """
        
        # Build epistemic metadata
        epistemic_context = {
            "epistemic_state": {
                "vectors": {
                    "know": vectors["know"],
                    "uncertainty": vectors["uncertainty"],
                    "context": vectors["context"],
                    "clarity": vectors["clarity"]
                },
                "routing": {
                    "mode": routing.mode,
                    "confidence": routing.confidence,
                    "reasoning": routing.reasoning
                }
            }
        }
        
        # If mode has guidance, prepend it
        enriched_parts = []
        
        if "guidance" in mode_result:
            enriched_parts.append(types.TextContent(
                type="text",
                text=f"🧠 **Epistemic Guidance**\n\n{mode_result['guidance']}\n\n"
            ))
        
        # Add original result
        enriched_parts.extend(original_result)
        
        # Add epistemic context as JSON
        enriched_parts.append(types.TextContent(
            type="text",
            text=f"\n\n---\n**Epistemic Context:**\n```json\n{json.dumps(epistemic_context, indent=2)}\n```"
        ))
        
        return enriched_parts
    
    def get_state(self) -> Dict[str, Any]:
        """Get current epistemic state"""
        return {
            "vectors": self.state_machine.get_state(),
            "request_count": self.request_count,
            "session_id": self.session_id
        }
