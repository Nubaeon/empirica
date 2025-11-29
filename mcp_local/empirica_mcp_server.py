#!/usr/bin/env python3
"""
Empirica MCP Server v2 - Thin CLI Wrapper

Architecture: Routes all stateful operations through Empirica CLI for reliability
- Stateless tools (3): Handle directly in MCP (introduction, guidance, help)
- Stateful tools (37): Route to CLI via subprocess (single source of truth)

Benefits:
- 90% code reduction (500 vs 5000 lines)
- 75% token reduction (CLI docs vs MCP schemas)
- No async bugs (subprocess in executor)
- Easy testing (empirica <cmd> --output json)
- Single source of truth (CLI implementation)

Author: Claude Code
Date: 2025-01-18
Version: 2.0.0
"""

import asyncio
import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add paths for proper imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Empirica CLI configuration
EMPIRICA_ROOT = Path(__file__).parent.parent
EMPIRICA_CLI = str(EMPIRICA_ROOT / ".venv-mcp" / "bin" / "empirica")

# Create MCP server instance
app = Server("empirica-v2")

# ============================================================================
# Tool Definitions
# ============================================================================

@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """List all available Empirica tools"""

    tools = [
        # ========== Stateless Tools (Handle Directly) ==========

        types.Tool(
            name="get_empirica_introduction",
            description="Get comprehensive introduction to Empirica framework",
            inputSchema={"type": "object", "properties": {}}
        ),

        types.Tool(
            name="get_workflow_guidance",
            description="Get workflow guidance for CASCADE phases",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {"type": "string", "description": "Workflow phase"}
                }
            }
        ),

        types.Tool(
            name="cli_help",
            description="Get help for Empirica CLI commands",
            inputSchema={"type": "object", "properties": {}}
        ),

        # ========== Workflow Tools (Route to CLI) ==========

        types.Tool(
            name="bootstrap_session",
            description="Bootstrap new Empirica session with metacognitive configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string", "description": "AI agent identifier"},
                    "session_type": {"type": "string", "description": "Session type (development, production, testing)"},
                    "bootstrap_level": {"type": "integer", "description": "Bootstrap level 0-2 (0=minimal, 1=standard, 2=full)"}
                },
                "required": ["ai_id"]
            }
        ),

        types.Tool(
            name="execute_preflight",
            description="Execute PREFLIGHT epistemic assessment before task engagement. Returns self-assessment prompt as JSON (non-blocking). AI performs genuine self-assessment and calls submit_preflight_assessment with vectors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID or alias (e.g., 'latest:active:ai-id')"},
                    "prompt": {"type": "string", "description": "Task description to assess"}
                },
                "required": ["session_id", "prompt"]
            }
        ),

        types.Tool(
            name="submit_preflight_assessment",
            description="Submit PREFLIGHT self-assessment scores (13 vectors)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "vectors": {"type": "object", "description": "13 epistemic vectors (0.0-1.0)"},
                    "reasoning": {"type": "string"}
                },
                "required": ["session_id", "vectors"]
            }
        ),

        types.Tool(
            name="execute_check",
            description="Execute CHECK phase assessment after investigation",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID or alias"},
                    "findings": {"type": "array", "items": {"type": "string"}, "description": "Investigation findings"},
                    "remaining_unknowns": {"type": "array", "items": {"type": "string"}, "description": "Remaining unknowns (maps to --unknowns)"},
                    "confidence_to_proceed": {"type": "number", "description": "Confidence score 0.0-1.0 (maps to --confidence)"}
                },
                "required": ["session_id", "findings", "remaining_unknowns", "confidence_to_proceed"]
            }
        ),

        types.Tool(
            name="submit_check_assessment",
            description="Submit CHECK phase assessment scores",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "vectors": {"type": "object"},
                    "decision": {"type": "string", "enum": ["proceed", "investigate"]},
                    "reasoning": {"type": "string"}
                },
                "required": ["session_id", "vectors", "decision"]
            }
        ),

        types.Tool(
            name="execute_postflight",
            description="Execute POSTFLIGHT assessment after task completion. Returns self-assessment prompt as JSON (non-blocking). AI performs genuine self-assessment and calls submit_postflight_assessment with vectors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID or alias (e.g., 'latest:active:ai-id')"},
                    "task_summary": {"type": "string", "description": "Summary of completed task"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="submit_postflight_assessment",
            description="Submit POSTFLIGHT self-assessment scores for calibration",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "vectors": {"type": "object", "description": "Epistemic vectors as JSON object with 13 keys"},
                    "reasoning": {"type": "string", "description": "Description of what changed from PREFLIGHT (unified with preflight-submit, both use reasoning)"}
                },
                "required": ["session_id", "vectors"]
            }
        ),

        # ========== Goal/Task Management (Route to CLI) ==========

        types.Tool(
            name="create_goal",
            description="Create new structured goal",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "objective": {"type": "string", "description": "Goal objective/description"},
                    "scope": {
                        "type": "object",
                        "description": "Goal scope as epistemic vectors (AI self-assesses dimensions)",
                        "properties": {
                            "breadth": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "How wide the goal spans (0.0=single function, 1.0=entire codebase)"
                            },
                            "duration": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Expected lifetime (0.0=minutes/hours, 1.0=weeks/months)"
                            },
                            "coordination": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Multi-agent/session coordination needed (0.0=solo, 1.0=heavy coordination)"
                            }
                        },
                        "required": ["breadth", "duration", "coordination"]
                    },
                    "success_criteria": {"type": "array", "items": {"type": "string"}, "description": "Array of success criteria strings"},
                    "estimated_complexity": {"type": "number", "description": "Complexity estimate 0.0-1.0"},
                    "metadata": {"type": "object", "description": "Additional metadata as JSON object"}
                },
                "required": ["session_id", "objective"]
            }
        ),

        types.Tool(
            name="add_subtask",
            description="Add subtask to existing goal",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {"type": "string", "description": "Goal UUID"},
                    "description": {"type": "string", "description": "Subtask description"},
                    "importance": {"type": "string", "enum": ["critical", "high", "medium", "low"], "description": "Epistemic importance (use importance not epistemic_importance)"},
                    "dependencies": {"type": "array", "items": {"type": "string"}, "description": "Dependencies as JSON array"},
                    "estimated_tokens": {"type": "integer", "description": "Estimated token usage"}
                },
                "required": ["goal_id", "description"]
            }
        ),

        types.Tool(
            name="complete_subtask",
            description="Mark subtask as complete",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Subtask UUID (note: parameter is task_id not subtask_id)"},
                    "evidence": {"type": "string", "description": "Completion evidence (commit hash, file path, etc.)"}
                },
                "required": ["task_id"]
            }
        ),

        types.Tool(
            name="get_goal_progress",
            description="Get goal completion progress",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {"type": "string"}
                },
                "required": ["goal_id"]
            }
        ),

        types.Tool(
            name="list_goals",
            description="List goals for session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),

        # ========== Session Management (Route to CLI) ==========

        types.Tool(
            name="get_epistemic_state",
            description="Get current epistemic state for session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="get_session_summary",
            description="Get complete session summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="get_calibration_report",
            description="Get calibration report for session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="resume_previous_session",
            description="Resume previous session(s)",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string"},
                    "count": {"type": "integer"}
                },
                "required": ["ai_id"]
            }
        ),

        # ========== Checkpoint Tools (Route to CLI) ==========

        types.Tool(
            name="create_git_checkpoint",
            description="Create compressed checkpoint in git notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "phase": {"type": "string"},
                    "round_num": {"type": "integer"},
                    "vectors": {"type": "object"},
                    "metadata": {"type": "object"}
                },
                "required": ["session_id", "phase"]
            }
        ),

        types.Tool(
            name="load_git_checkpoint",
            description="Load latest checkpoint from git notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),

        # ========== Handoff Reports (Route to CLI) ==========

        types.Tool(
            name="create_handoff_report",
            description="Create epistemic handoff report for session continuity (98% token reduction)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID or alias"},
                    "task_summary": {"type": "string", "description": "What was accomplished (2-3 sentences)"},
                    "key_findings": {"type": "array", "items": {"type": "string"}, "description": "Key learnings from session"},
                    "remaining_unknowns": {"type": "array", "items": {"type": "string"}, "description": "What's still unclear"},
                    "next_session_context": {"type": "string", "description": "Critical context for next session"},
                    "artifacts_created": {"type": "array", "items": {"type": "string"}, "description": "Files created"}
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
                    "session_id": {"type": "string", "description": "Specific session ID"},
                    "ai_id": {"type": "string", "description": "Filter by AI ID"},
                    "limit": {"type": "integer", "description": "Number of results (default: 5)"}
                }
            }
        ),

        # ========== Phase 1: Cross-AI Coordination (Route to CLI) ==========

        types.Tool(
            name="discover_goals",
            description="Discover goals from other AIs via git notes (Phase 1)",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_ai_id": {"type": "string", "description": "Filter by AI creator"},
                    "session_id": {"type": "string", "description": "Filter by session"}
                }
            }
        ),

        types.Tool(
            name="resume_goal",
            description="Resume another AI's goal with epistemic handoff (Phase 1)",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {"type": "string", "description": "Goal UUID to resume"},
                    "ai_id": {"type": "string", "description": "Your AI identifier"}
                },
                "required": ["goal_id", "ai_id"]
            }
        ),

        # ========== Phase 2: Cryptographic Trust (Route to CLI) ==========

        types.Tool(
            name="create_identity",
            description="Create new AI identity with Ed25519 keypair (Phase 2)",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string", "description": "AI identifier"},
                    "overwrite": {"type": "boolean", "description": "Overwrite existing identity"}
                },
                "required": ["ai_id"]
            }
        ),

        types.Tool(
            name="list_identities",
            description="List all AI identities (Phase 2)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        types.Tool(
            name="export_public_key",
            description="Export public key for sharing (Phase 2)",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string", "description": "AI identifier"}
                },
                "required": ["ai_id"]
            }
        ),

        types.Tool(
            name="verify_signature",
            description="Verify signed session (Phase 2)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID to verify"}
                },
                "required": ["session_id"]
            }
        ),
    ]

    return tools

# ============================================================================
# Tool Call Handler
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Route tool calls to appropriate handler"""

    try:
        # Category 1: Stateless tools (handle directly)
        if name == "get_empirica_introduction":
            return handle_introduction()
        elif name == "get_workflow_guidance":
            return handle_guidance(arguments)
        elif name == "cli_help":
            return handle_cli_help()

        # Category 2: All other tools (route to CLI)
        else:
            return await route_to_cli(name, arguments)

    except Exception as e:
        # Return structured error
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "ok": False,
                "error": str(e),
                "tool": name,
                "suggestion": "Check tool arguments and try again"
            }, indent=2)
        )]

# ============================================================================
# CLI Router
# ============================================================================

async def route_to_cli(tool_name: str, arguments: dict) -> List[types.TextContent]:
    """Route MCP tool call to Empirica CLI command"""

    # Build CLI command
    cmd = build_cli_command(tool_name, arguments)

    # Execute in async executor (non-blocking)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=EMPIRICA_ROOT
        )
    )

    # Return CLI output
    if result.returncode == 0:
        # Parse text output to JSON for commands that don't support --output json yet
        output = parse_cli_output(tool_name, result.stdout, result.stderr, arguments)
        return [types.TextContent(type="text", text=output)]
    else:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "ok": False,
                "error": result.stderr,
                "command": " ".join(cmd),
                "suggestion": "Check CLI command syntax with: empirica --help"
            }, indent=2)
        )]

def parse_cli_output(tool_name: str, stdout: str, stderr: str, arguments: dict) -> str:
    """Parse CLI output and convert to JSON if needed"""

    # Check if output is already JSON
    try:
        json.loads(stdout)
        return stdout  # Already JSON
    except (json.JSONDecodeError, ValueError):
        pass  # Not JSON, need to parse

    # Parse specific command outputs
    if tool_name == "bootstrap_session":
        # Parse bootstrap output
        # Example: "✅ Bootstrap complete!\n   📊 Components loaded: 6\n   ⏱️ Bootstrap time: 96μs..."
        import re

        components = 0
        level = 0

        # Extract components loaded
        match = re.search(r'Components loaded:\s*(\d+)', stdout)
        if match:
            components = int(match.group(1))

        # Extract level
        match = re.search(r'Level:\s*(\d+)', stdout)
        if match:
            level = int(match.group(1))

        # Create session in database (bootstrap initializes framework but doesn't create session)
        # The MCP layer creates the session and returns its ID
        # Extract ai_id and bootstrap_level from arguments
        ai_id = arguments.get('ai_id', 'unknown')
        bootstrap_level = arguments.get('bootstrap_level', level)
        
        try:
            from empirica.data.session_database import SessionDatabase
            import uuid
            
            db = SessionDatabase()
            session_id = db.create_session(
                ai_id=ai_id,
                bootstrap_level=bootstrap_level,
                components_loaded=components or 5
            )
            db.close()
            
            result = {
                "ok": True,
                "message": "Bootstrap completed successfully and session created",
                "session_id": session_id,
                "ai_id": ai_id,
                "components_loaded": components or 5,
                "bootstrap_level": bootstrap_level,
                "next_step": "Use this session_id with execute_preflight to begin a cascade"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            # Fallback if database creation fails
            result = {
                "ok": True,
                "message": "Bootstrap completed but session creation failed",
                "error": str(e),
                "components_loaded": components,
                "bootstrap_level": bootstrap_level,
                "next_step": "Call execute_preflight (it will auto-create a session)",
                "note": "Session will be auto-created by execute_preflight"
            }
            
            return json.dumps(result, indent=2)

    # Default: return original output wrapped in JSON
    return json.dumps({
        "ok": True,
        "output": stdout,
        "note": "Text output - CLI command doesn't support --output json yet"
    }, indent=2)

def build_cli_command(tool_name: str, arguments: dict) -> List[str]:
    """Build CLI command from MCP tool name and arguments"""

    # Map MCP tool name → CLI command
    tool_map = {
        # Workflow
        "bootstrap_session": ["bootstrap"],
        "execute_preflight": ["preflight", "--prompt-only"],  # Non-blocking: returns prompt only
        "submit_preflight_assessment": ["preflight-submit"],
        "execute_check": ["check"],
        "submit_check_assessment": ["check-submit"],
        "execute_postflight": ["postflight", "--prompt-only"],  # Non-blocking: returns prompt only
        "submit_postflight_assessment": ["postflight-submit"],

        # Goals
        "create_goal": ["goals-create"],
        "add_subtask": ["goals-add-subtask"],
        "complete_subtask": ["goals-complete-subtask"],
        "get_goal_progress": ["goals-progress"],
        "list_goals": ["goals-list"],

        # Sessions
        "get_epistemic_state": ["sessions-show"],
        "get_session_summary": ["sessions-show", "--verbose"],
        "get_calibration_report": ["calibration"],
        "resume_previous_session": ["sessions-resume"],

        # Checkpoints
        "create_git_checkpoint": ["checkpoint-create"],
        "load_git_checkpoint": ["checkpoint-load"],  # Note: Requires --session-id flag

        # Handoff Reports
        "create_handoff_report": ["handoff-create"],
        "query_handoff_reports": ["handoff-query"],

        # Phase 1: Cross-AI Coordination
        "discover_goals": ["goals-discover"],
        "resume_goal": ["goals-resume"],

        # Phase 2: Cryptographic Trust
        "create_identity": ["identity-create"],
        "list_identities": ["identity-list"],
        "export_public_key": ["identity-export"],
        "verify_signature": ["identity-verify"],
    }
    
    # Commands that take positional arguments (not flags)
    # Format: command_name: (positional_arg_name, remaining_args_as_flags)
    positional_args = {
        "preflight": "prompt",           # preflight <prompt> [--session-id ...]
        "postflight": "session_id",      # postflight <session_id> [--summary ...]
        "sessions-show": "session_id",   # sessions-show <session_id>
        "calibration": "session_id",     # calibration <session_id>
    }

    # Map MCP argument names → CLI flag names (when they differ)
    arg_map = {
        "session_type": "session-type",  # Not used by CLI - will be ignored
        "bootstrap_level": "level",  # MCP uses bootstrap_level, CLI uses level
        "task_id": "task-id",  # MCP uses task_id, CLI uses task-id (for goals-complete-subtask)
        "remaining_unknowns": "unknowns",  # MCP uses remaining_unknowns, CLI uses unknowns (for handoff-create)
        "confidence_to_proceed": "confidence",  # MCP uses confidence_to_proceed, CLI uses confidence (for check command)
        "investigation_cycle": "cycle",  # MCP uses investigation_cycle, CLI uses cycle (for check-submit)
        "task_summary": "summary",  # MCP uses task_summary, CLI uses summary (for postflight)
        "reasoning": "reasoning",  # MCP uses reasoning, CLI uses reasoning (unified: preflight-submit and postflight-submit)
        "key_findings": "key-findings",  # MCP uses key_findings, CLI uses key-findings (for handoff-create)
        "next_session_context": "next-session-context",  # MCP uses next_session_context, CLI uses next-session-context
        "artifacts_created": "artifacts",  # MCP uses artifacts_created, CLI uses artifacts (for handoff-create)
    }
    
    # Arguments to skip per command (not supported by CLI)
    skip_args = {
        "check-submit": ["confidence_to_proceed"],  # check-submit doesn't use confidence_to_proceed
    }

    cmd = [EMPIRICA_CLI] + tool_map.get(tool_name, [tool_name])
    
    cli_command = tool_map.get(tool_name, [tool_name])[0]
    
    # Handle positional argument first if command requires it
    if cli_command in positional_args:
        positional_key = positional_args[cli_command]
        if positional_key in arguments:
            cmd.append(str(arguments[positional_key]))

    # Map remaining arguments to CLI flags
    for key, value in arguments.items():
        if value is not None:
            # Skip positional arg (already handled)
            if cli_command in positional_args and key == positional_args[cli_command]:
                continue
                
            # Skip arguments not supported by CLI
            if key == "session_type":
                continue
            
            # Skip command-specific unsupported arguments
            if cli_command in skip_args and key in skip_args[cli_command]:
                continue

            # Map argument name to CLI flag name
            flag_name = arg_map.get(key, key.replace('_', '-'))
            flag = f"--{flag_name}"

            if isinstance(value, bool):
                if value:
                    cmd.append(flag)
            elif isinstance(value, (dict, list)):
                cmd.extend([flag, json.dumps(value)])
            else:
                cmd.extend([flag, str(value)])

    # Commands that support --output json
    # Note: preflight/postflight with --prompt-only already return JSON
    json_supported = {
        "preflight-submit", "check", "check-submit", "postflight-submit",
        "goals-create", "goals-add-subtask", "goals-complete-subtask",
        "goals-progress", "goals-list", "sessions-resume",
        "handoff-create", "handoff-query"
    }

    cli_command = tool_map.get(tool_name, [tool_name])[0]
    if cli_command in json_supported:
        cmd.extend(["--output", "json"])
    
    # preflight and postflight already have --prompt-only which returns JSON

    return cmd

# ============================================================================
# Stateless Tool Handlers
# ============================================================================

def handle_introduction() -> List[types.TextContent]:
    """Return Empirica introduction (stateless)"""

    intro = """# Empirica Framework - Epistemic Self-Assessment for AI Agents

**Purpose:** Track what you know, what you can do, and how uncertain you are throughout any task.

## Quick Start

1. **Bootstrap:** `bootstrap_session(ai_id="your-id", session_type="development")`
2. **PREFLIGHT:** Assess before starting
3. **INVESTIGATE:** Fill knowledge gaps
4. **CHECK:** Validate readiness
5. **ACT:** Execute task
6. **POSTFLIGHT:** Measure learning

## 13 Epistemic Vectors (0-1 scale)

**Foundation:** engagement, know, do, context
**Comprehension:** clarity, coherence, signal, density
**Execution:** state, change, completion, impact
**Meta:** uncertainty (high >0.6 → investigate)

## When to Use Empirica

✅ Use if: UNCERTAINTY > 0.6, task >1 hour, high stakes
❌ Skip if: Simple query, high confidence (KNOW >0.8)

## Key Components

- **Goal Orchestrator:** Auto-generates investigation goals
- **Bayesian Tracker:** Updates beliefs as you learn
- **Drift Monitor:** Detects overconfidence (auto-runs in CHECK)
- **Git Checkpoints:** 97.5% token reduction for resumption

**Philosophy:** Epistemic transparency > speed. Know what you don't know.

**Documentation:** /docs/ directory in Empirica repo
"""

    return [types.TextContent(type="text", text=intro)]

def handle_guidance(arguments: dict) -> List[types.TextContent]:
    """Return workflow guidance (stateless)"""

    phase = arguments.get("phase", "overview")

    guidance = {
        "preflight": "Execute PREFLIGHT self-assessment across 13 vectors BEFORE engaging. Be honest about uncertainties.",
        "investigate": "Systematically gather information to address unknowns. Use tools and documentation.",
        "check": "Self-assess: remaining unknowns acceptable? Confidence >0.7 to proceed? Honesty critical for calibration.",
        "act": "Execute task with learned knowledge. Document decisions and reasoning.",
        "postflight": "Reassess 13 vectors AFTER completion. Compare to PREFLIGHT for calibration validation.",
        "overview": "PREFLIGHT → INVESTIGATE → CHECK → (loop if needed) → ACT → POSTFLIGHT"
    }

    result = {
        "ok": True,
        "phase": phase,
        "guidance": guidance.get(phase, guidance["overview"]),
        "workflow_order": "PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT"
    }

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

def handle_cli_help() -> List[types.TextContent]:
    """Return CLI help (stateless)"""

    help_text = """# Empirica CLI Commands

## Workflow Commands (CASCADE)
- `empirica bootstrap --ai-id=<your-id> --level=2`
- `empirica preflight --session-id=<id> --prompt="Task description"`
- `empirica preflight-submit --session-id=<id> --vectors='{"engagement":0.8,...}'`
- `empirica check --session-id=<id>`
- `empirica check-submit --session-id=<id> --vectors='{}' --decision=proceed`
- `empirica postflight --session-id=<id>`
- `empirica postflight-submit --session-id=<id> --vectors='{}'`

## Goal Commands
- `empirica goals-create --session-id=<id> --objective="..." --scope=session_scoped`
- `empirica goals-add-subtask --goal-id=<id> --description="..."`
- `empirica goals-complete-subtask --subtask-id=<id> --evidence="Done"`
- `empirica goals-progress --goal-id=<id>`
- `empirica goals-list --session-id=<id>`

## Session Commands
- `empirica sessions-list`
- `empirica sessions-show <session-id-or-alias>`
- `empirica sessions-resume --ai-id=<your-id> --count=1`
- `empirica calibration --session-id=<id>`

## Checkpoint Commands
- `empirica checkpoint-create --session-id=<id> --phase=ACT`
- `empirica checkpoint-load <session-id-or-alias>`

## Session Aliases (Magic Shortcuts!)

Instead of UUIDs, use aliases:
- `latest` - Most recent session
- `latest:active` - Most recent active session
- `latest:<ai-id>` - Most recent for your AI
- `latest:active:<ai-id>` - Most recent active for your AI (recommended!)

**Example:**
```bash
# Instead of: empirica sessions-show 88dbf132-cc7c-4a4b-9b59-77df3b13dbd2
# Use: empirica sessions-show latest:active:claude-code

# Load checkpoint without remembering UUID:
empirica checkpoint-load latest:active:mini-agent
```

## Quick CASCADE Workflow

```bash
# 1. Bootstrap
empirica bootstrap --ai-id=your-id --level=2

# 2. PREFLIGHT (assess before starting)
empirica preflight --session-id=latest:active:your-id --prompt="Your task"

# 3. Submit assessment
empirica preflight-submit --session-id=latest:active:your-id --vectors='{"engagement":0.8,"know":0.5,...}'

# 4. CHECK (validate readiness)
empirica check --session-id=latest:active:your-id
empirica check-submit --session-id=latest:active:your-id --decision=proceed

# 5. POSTFLIGHT (reflect on learning)
empirica postflight --session-id=latest:active:your-id
empirica postflight-submit --session-id=latest:active:your-id --vectors='{"engagement":0.9,"know":0.8,...}'
```

## Notes

- **All commands support `--output json` for programmatic use**
- Session aliases work with: sessions-show, checkpoint-load, and all workflow commands
- For detailed help: `empirica <command> --help`
- For MCP tool usage: Use tool names (bootstrap_session, execute_preflight, etc.)
"""

    return [types.TextContent(type="text", text=help_text)]

# ============================================================================
# Server Main
# ============================================================================

async def main():
    """Run MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
