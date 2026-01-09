#!/usr/bin/env python3
"""
Empirica MCP Server - Epistemic Middleware for AI Agents

Full-featured MCP server providing:
- **57 tools** wrapping Empirica CLI commands
- **Epistemic middleware** for confidence-gated actions
- **Sentinel integration** for CHECK gate decisions
- **CASCADE workflow** (PREFLIGHT → CHECK → POSTFLIGHT)
- **Memory persistence** via Qdrant semantic search

Architecture:
- Stateful tools route through CLI subprocess (single source of truth)
- EpistemicMiddleware intercepts tool calls for confidence gating
- Sentinel evaluates vectors and returns proceed/investigate decisions
- Session state persists across tool invocations

CASCADE Philosophy:
- validate_input=False: Schemas are GUIDANCE, not enforcement
- No rigid validation: AI agents self-assess what parameters make sense
- Scope is vectorial (self-assessed): {"breadth": 0-1, "duration": 0-1, "coordination": 0-1}
- Trust AI reasoning: Let agents assess epistemic state → scope vectors

Version: 1.3.0
"""

import asyncio
import subprocess
import json
import sys
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

# Add paths for proper imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from empirica.data.session_database import SessionDatabase
from empirica.config.path_resolver import get_session_db_path
from empirica.utils.session_resolver import resolve_session_id

# Auto-capture for error tracking
try:
    from empirica.core.issue_capture import get_auto_capture, IssueSeverity, IssueCategory
except ImportError:
    get_auto_capture = None
    IssueSeverity = None
    IssueCategory = None

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Empirica CLI configuration - use PATH for portability
EMPIRICA_CLI = shutil.which("empirica")
if not EMPIRICA_CLI:
    # Fallback: try common installation locations
    possible_paths = [
        Path.home() / ".local" / "bin" / "empirica",
        Path("/usr/local/bin/empirica"),
        Path("/usr/bin/empirica"),
    ]
    for path in possible_paths:
        if path.exists():
            EMPIRICA_CLI = str(path)
            break

    if not EMPIRICA_CLI:
        raise RuntimeError(
            "empirica CLI not found in PATH. "
            "Please install: pip install empirica"
        )

# Create MCP server instance
app = Server("empirica-v2")

# ============================================================================
# Epistemic Middleware (Optional)
# ============================================================================

# Enable epistemic mode via environment variable
import os
ENABLE_EPISTEMIC = os.getenv("EMPIRICA_EPISTEMIC_MODE", "false").lower() == "true"
EPISTEMIC_PERSONALITY = os.getenv("EMPIRICA_PERSONALITY", "balanced_architect")

if ENABLE_EPISTEMIC:
    from .epistemic_middleware import EpistemicMiddleware
    logger.info(f"🧠 Epistemic mode ENABLED with personality: {EPISTEMIC_PERSONALITY}")
    epistemic_middleware = EpistemicMiddleware(personality=EPISTEMIC_PERSONALITY)
else:
    epistemic_middleware = None
    logger.info("⚙️  Standard mode (epistemic disabled)")

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
            name="session_create",
            description="Create new Empirica session with metacognitive configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string", "description": "AI agent identifier"},
                    "session_type": {"type": "string", "description": "Session type (development, production, testing)"}
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

        # NOTE: execute_check removed - it blocks on stdin. Use submit_check_assessment directly.

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
            description="Execute POSTFLIGHT pure self-assessment after task completion. Returns session context (WITHOUT baseline vectors to prevent anchoring). AI assesses CURRENT state genuinely; system calculates deltas objectively and detects confabulation. Call submit_postflight_assessment with current-state vectors only.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID or alias (e.g., 'latest:active:ai-id')"},
                    "task_summary": {"type": "string", "description": "Summary of ALL work completed in session (not just last task)"}
                },
                "required": ["session_id", "task_summary"]
            }
        ),

        types.Tool(
            name="submit_postflight_assessment",
            description="Submit POSTFLIGHT pure self-assessment. Rate your CURRENT epistemic state across all 13 vectors (0.0-1.0). Do NOT reference PREFLIGHT or claim deltas - just honestly assess where you are NOW. System automatically calculates learning deltas, detects memory gaps, and flags calibration issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "vectors": {"type": "object", "description": "CURRENT epistemic state: 13 vectors (engagement, know, do, context, clarity, coherence, signal, density, state, change, completion, impact, uncertainty). Rate 0.0-1.0 based on current state only."},
                    "reasoning": {"type": "string", "description": "Description of what changed from PREFLIGHT (unified with preflight-submit, both use reasoning)"}
                },
                "required": ["session_id", "vectors"]
            }
        ),

        # ========== Goal/Task Management (Route to CLI) ==========

        types.Tool(
            name="finding_log",
            description="Log a finding (what was learned) to session and optionally project",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "finding": {"type": "string", "description": "What was learned or discovered"},
                    "impact": {"type": "number", "description": "Impact score 0.0-1.0", "minimum": 0.0, "maximum": 1.0},
                    "goal_id": {"type": "string", "description": "Optional goal UUID to link finding"},
                    "subtask_id": {"type": "string", "description": "Optional subtask UUID to link finding"}
                },
                "required": ["session_id", "finding"]
            }
        ),

        types.Tool(
            name="unknown_log",
            description="Log an unknown (what remains unclear) to session and optionally project",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "unknown": {"type": "string", "description": "What remains unclear or needs investigation"},
                    "goal_id": {"type": "string", "description": "Optional goal UUID to link unknown"},
                    "subtask_id": {"type": "string", "description": "Optional subtask UUID to link unknown"}
                },
                "required": ["session_id", "unknown"]
            }
        ),

        types.Tool(
            name="mistake_log",
            description="Log a mistake (error to avoid in future) to session and optionally project",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "mistake": {"type": "string", "description": "What was done wrong"},
                    "why_wrong": {"type": "string", "description": "Why it was wrong"},
                    "prevention": {"type": "string", "description": "How to prevent in future"},
                    "cost_estimate": {"type": "string", "description": "Time/resources wasted (e.g., '2 hours')"},
                    "goal_id": {"type": "string", "description": "Optional goal UUID to link mistake"},
                    "subtask_id": {"type": "string", "description": "Optional subtask UUID to link mistake"}
                },
                "required": ["session_id", "mistake", "why_wrong", "prevention"]
            }
        ),

        types.Tool(
            name="deadend_log",
            description="Log a dead-end (approach that didn't work) to session and optionally project",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "approach": {"type": "string", "description": "What approach was tried"},
                    "why_failed": {"type": "string", "description": "Why it didn't work"},
                    "goal_id": {"type": "string", "description": "Optional goal UUID to link dead-end"},
                    "subtask_id": {"type": "string", "description": "Optional subtask UUID to link dead-end"}
                },
                "required": ["session_id", "approach", "why_failed"]
            }
        ),

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
            name="get_goal_subtasks",
            description="Get detailed subtask information for a goal",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {"type": "string", "description": "Goal UUID"}
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
            name="project_bootstrap",
            description="Load project context dynamically based on uncertainty (findings, unknowns, dead-ends, mistakes, goals)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID (optional, auto-detects from git if not provided)"},
                    "depth": {"type": "string", "description": "Context depth: minimal, moderate, full, auto", "enum": ["minimal", "moderate", "full", "auto"]}
                },
                "required": []
            }
        ),

        types.Tool(
            name="session_snapshot",
            description="Get complete session snapshot with learning delta, findings, unknowns, mistakes, active goals",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="goals_ready",
            description="Get goals that are ready to work on (unblocked by dependencies and epistemic state)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID (optional)"}
                },
                "required": []
            }
        ),

        types.Tool(
            name="goals_claim",
            description="Claim a goal and create epistemic branch for work",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {"type": "string", "description": "Goal UUID to claim"}
                },
                "required": ["goal_id"]
            }
        ),

        types.Tool(
            name="investigate",
            description="Run systematic investigation with epistemic tracking",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "investigation_goal": {"type": "string", "description": "What to investigate"},
                    "max_rounds": {"type": "integer", "description": "Max investigation rounds", "default": 5}
                },
                "required": ["session_id", "investigation_goal"]
            }
        ),

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

        # ========== Epistemic Monitoring (Route to CLI) ==========

        types.Tool(
            name="epistemics_list",
            description="List all epistemic assessments (PREFLIGHT, CHECK, POSTFLIGHT) for a session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID to list epistemics for"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="epistemics_show",
            description="Show detailed epistemic assessment for a session, optionally filtered by phase",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "phase": {"type": "string", "description": "Optional phase filter (PREFLIGHT, CHECK, POSTFLIGHT)", "enum": ["PREFLIGHT", "CHECK", "POSTFLIGHT"]}
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

        types.Tool(
            name="memory_compact",
            description="Compact session for epistemic continuity across conversation boundaries. Creates checkpoint, loads bootstrap context, creates continuation session. Use when approaching context limit (e.g., >180k tokens).",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID or alias to compact"},
                    "create_continuation": {"type": "boolean", "description": "Create continuation session (default: true)"},
                    "include_bootstrap": {"type": "boolean", "description": "Load project bootstrap context (default: true)"},
                    "checkpoint_current": {"type": "boolean", "description": "Checkpoint current epistemic state (default: true)"},
                    "compact_mode": {"type": "string", "enum": ["full", "minimal", "context_only"], "description": "Compaction mode: full (all features), minimal (checkpoint only), context_only (bootstrap only)"}
                },
                "required": ["session_id"]
            }
        ),

        # ========== Human Copilot Tools (Route to CLI) ==========
        # These tools enhance human oversight and collaboration

        types.Tool(
            name="monitor",
            description="Real-time monitoring of AI work - shows stats, cost analysis, request history, adapter health. Essential for human oversight.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cost": {"type": "boolean", "description": "Show cost analysis"},
                    "history": {"type": "boolean", "description": "Show recent request history"},
                    "health": {"type": "boolean", "description": "Include adapter health checks"},
                    "project": {"type": "boolean", "description": "Show cost projections (with cost=true)"},
                    "verbose": {"type": "boolean", "description": "Show detailed stats"}
                },
                "required": []
            }
        ),

        types.Tool(
            name="check_drift",
            description="Detect epistemic drift - when AI confidence diverges from actual performance. Critical for trust calibration.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID to check for drift"},
                    "trigger": {"type": "string", "enum": ["manual", "pre_summary", "post_summary"], "description": "When check is triggered"},
                    "threshold": {"type": "number", "description": "Drift threshold (default: 0.2)"},
                    "lookback": {"type": "integer", "description": "Number of checkpoints to analyze (default: 5)"},
                    "cycle": {"type": "integer", "description": "Investigation cycle number (optional filter)"},
                    "round": {"type": "integer", "description": "CHECK round number (optional filter)"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="issue_list",
            description="List auto-captured issues for human review - bugs, errors, warnings, TODOs. Filter by status, category, severity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID to list issues for"},
                    "status": {"type": "string", "enum": ["new", "investigating", "handoff", "resolved", "wontfix"], "description": "Filter by status"},
                    "category": {"type": "string", "enum": ["bug", "error", "warning", "deprecation", "todo", "performance", "compatibility", "design", "other"], "description": "Filter by category"},
                    "severity": {"type": "string", "enum": ["blocker", "high", "medium", "low"], "description": "Filter by severity"},
                    "limit": {"type": "integer", "description": "Max issues to return (default: 100)"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="issue_handoff",
            description="Hand off an issue to another AI or human. Enables structured issue transfer between agents.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"},
                    "issue_id": {"type": "string", "description": "Issue ID to hand off"},
                    "assigned_to": {"type": "string", "description": "AI ID or name to assign this issue to"}
                },
                "required": ["session_id", "issue_id", "assigned_to"]
            }
        ),

        types.Tool(
            name="workspace_overview",
            description="Multi-repo epistemic overview - shows project health, knowledge state, uncertainty across workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sort_by": {"type": "string", "enum": ["activity", "knowledge", "uncertainty", "name"], "description": "Sort projects by"},
                    "filter": {"type": "string", "enum": ["active", "inactive", "complete"], "description": "Filter projects by status"},
                    "verbose": {"type": "boolean", "description": "Show detailed info"}
                },
                "required": []
            }
        ),

        types.Tool(
            name="efficiency_report",
            description="Get productivity metrics for session - learning velocity, CASCADE completeness, goal completion rate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID"}
                },
                "required": ["session_id"]
            }
        ),

        types.Tool(
            name="skill_suggest",
            description="AI capability discovery - suggest relevant skills for a given task based on project context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description to suggest skills for"},
                    "project_id": {"type": "string", "description": "Project ID for context-aware suggestions"},
                    "verbose": {"type": "boolean", "description": "Show detailed suggestions"}
                },
                "required": []
            }
        ),

        types.Tool(
            name="workspace_map",
            description="Map workspace structure - discover repos, relationships, and cross-repo dependencies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "verbose": {"type": "boolean", "description": "Show detailed info"}
                },
                "required": []
            }
        ),

        types.Tool(
            name="unknown_resolve",
            description="Resolve a logged unknown - close investigation loops when answers are found.",
            inputSchema={
                "type": "object",
                "properties": {
                    "unknown_id": {"type": "string", "description": "Unknown UUID to resolve"},
                    "resolved_by": {"type": "string", "description": "How was this unknown resolved?"}
                },
                "required": ["unknown_id", "resolved_by"]
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
            description="Create epistemic handoff report for session continuity (~90% token reduction)",
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

        # ========== Mistakes Tracking (Learning from Failures) ==========

        types.Tool(
            name="log_mistake",
            description="Log a mistake for learning and future prevention. Records what went wrong, why it was wrong, cost estimate, root cause epistemic vector, and prevention strategy. Creates training data for calibration and pattern recognition.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "mistake": {"type": "string", "description": "What was done wrong"},
                    "why_wrong": {"type": "string", "description": "Explanation of why it was wrong"},
                    "cost_estimate": {"type": "string", "description": "Estimated time/effort wasted (e.g., '2 hours', '30 minutes')"},
                    "root_cause_vector": {"type": "string", "enum": ["KNOW", "DO", "CONTEXT", "CLARITY", "COHERENCE", "SIGNAL", "DENSITY", "STATE", "CHANGE", "COMPLETION", "IMPACT", "UNCERTAINTY"], "description": "Epistemic vector that caused the mistake"},
                    "prevention": {"type": "string", "description": "How to prevent this mistake in the future"},
                    "goal_id": {"type": "string", "description": "Optional goal identifier this mistake relates to"}
                },
                "required": ["session_id", "mistake", "why_wrong"]
            }
        ),

        types.Tool(
            name="query_mistakes",
            description="Query logged mistakes for learning and calibration. Retrieve mistakes by session, goal, or root cause vector to identify patterns and prevent repeat failures.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Filter by session UUID"},
                    "goal_id": {"type": "string", "description": "Filter by goal UUID"},
                    "limit": {"type": "integer", "description": "Maximum number of results (default: 10)", "minimum": 1, "maximum": 100}
                }
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

        # ========== Reference Documentation (Route to CLI) ==========

        types.Tool(
            name="refdoc_add",
            description="Add a reference document to project knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project UUID"},
                    "doc_path": {"type": "string", "description": "Path to documentation file"},
                    "doc_type": {"type": "string", "description": "Type of doc (guide, reference, example, config, etc.)"},
                    "description": {"type": "string", "description": "Description of what's in the doc"}
                },
                "required": ["project_id", "doc_path"]
            }
        ),

        # ========== Vision Analysis (Route to CLI) ==========

        types.Tool(
            name="vision_analyze",
            description="Analyze image(s) and extract basic metadata. For .png slides/images, returns size, format, aspect ratio. Optionally logs findings to session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image": {"type": "string", "description": "Single image path"},
                    "pattern": {"type": "string", "description": "Image pattern (e.g., slides/*.png)"},
                    "session_id": {"type": "string", "description": "Session ID to log findings"},
                },
            }
        ),

        types.Tool(
            name="vision_log",
            description="Manually log visual observation to session (for observations not captured by vision_analyze)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "observation": {"type": "string", "description": "Visual observation text"}
                },
                "required": ["session_id", "observation"]
            }
        ),

        # ========== Edit Guard (Metacognitive Edit Verification) ==========

        types.Tool(
            name="edit_with_confidence",
            description="Edit file with metacognitive confidence assessment. Prevents 80% of edit failures by assessing epistemic state (context freshness, whitespace confidence, pattern uniqueness, truncation risk) BEFORE attempting edit. Automatically selects optimal strategy: atomic_edit (high confidence), bash_fallback (medium), or re_read_first (low). Returns success status, strategy used, confidence score, and reasoning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to edit"
                    },
                    "old_str": {
                        "type": "string",
                        "description": "String to replace (exact match required)"
                    },
                    "new_str": {
                        "type": "string",
                        "description": "Replacement string"
                    },
                    "context_source": {
                        "type": "string",
                        "description": "How recently was file read? 'view_output' (just read this turn), 'fresh_read' (1-2 turns ago), 'memory' (stale/never read). Default: memory",
                        "enum": ["view_output", "fresh_read", "memory"]
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional: Session ID for logging calibration data to reflexes"
                    }
                },
                "required": ["file_path", "old_str", "new_str"]
            }
        ),
    ]

    return tools

# ============================================================================
# Tool Call Handler
# ============================================================================

@app.call_tool(validate_input=False)  # CASCADE = guidance, not enforcement
async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Route tool calls to appropriate handler
    
    Note: validate_input=False allows flexible AI self-assessment.
    Schemas provide guidance, but don't enforce rigid validation.
    Handlers parse parameters flexibly (strings, objects, etc.)
    
    Epistemic Middleware: If enabled (EMPIRICA_EPISTEMIC_MODE=true),
    wraps all calls with vector-driven self-awareness.
    """
    
    # If epistemic middleware enabled, route through it
    if epistemic_middleware:
        return await epistemic_middleware.handle_request(
            tool_name=name,
            arguments=arguments,
            original_handler=lambda tn, args: _call_tool_impl(tn, args)
        )
    else:
        return await _call_tool_impl(name, arguments)


async def _call_tool_impl(name: str, arguments: dict) -> List[types.TextContent]:
    """Internal tool call implementation (wrapped by middleware if enabled)"""

    try:
        # Category 1: Stateless tools (handle directly - sync functions)
        if name == "get_empirica_introduction":
            return handle_introduction()  # Returns List[TextContent] directly
        elif name == "get_workflow_guidance":
            return handle_guidance(arguments)  # Returns List[TextContent] directly
        elif name == "cli_help":
            return handle_cli_help()  # Returns List[TextContent] directly

        # Category 2: Direct Python handlers (AI-centric, no CLI conversion)
        elif name == "create_goal":
            return await handle_create_goal_direct(arguments)
        elif name == "execute_postflight":
            return await handle_execute_postflight_direct(arguments)
        elif name == "get_calibration_report":
            return await handle_get_calibration_report(arguments)
        elif name == "edit_with_confidence":
            return await handle_edit_with_confidence(arguments)
        elif name == "vision_analyze":
            return await route_to_cli("vision-analyze", arguments)
        elif name == "vision_log":
            return await route_to_cli("vision-log", arguments)

        # Category 3: All other tools (route to CLI)
        else:
            return await route_to_cli(name, arguments)

    except Exception as e:
        # Auto-capture error if service available
        if get_auto_capture:
            try:
                auto_capture = get_auto_capture()
                if auto_capture:
                    auto_capture.capture_error(
                        message=f"MCP tool error: {name} - {str(e)}",
                        severity=IssueSeverity.HIGH,
                        category=IssueCategory.ERROR,
                        context={"tool": name, "arguments": arguments}
                    )
            except Exception:
                pass  # Don't let auto-capture errors break the response
        
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
# Direct Python Handlers (AI-Centric)
# ============================================================================

async def handle_create_goal_direct(arguments: dict) -> List[types.TextContent]:
    """Handle create_goal directly in Python (no CLI conversion)
    
    AI-centric design: accepts scope as object, no schema conversion needed.
    """
    try:
        from empirica.core.goals.repository import GoalRepository
        from empirica.core.goals.types import Goal, ScopeVector, SuccessCriterion
        from empirica.core.canonical.empirica_git import GitGoalStore
        import uuid
        import time
        
        # Extract arguments
        session_id = arguments["session_id"]
        objective = arguments["objective"]
        
        # Parse scope: AI self-assesses vectors (no semantic presets - that's heuristics!)
        scope_arg = arguments.get("scope", {"breadth": 0.3, "duration": 0.2, "coordination": 0.1})
        
        # If somehow a string comes in, convert to default and let AI know to use vectors
        if isinstance(scope_arg, str):
            # Don't try to interpret semantic names - that's adding heuristics back!
            # AI should assess: breadth (0-1), duration (0-1), coordination (0-1)
            logger.warning(f"Scope string '{scope_arg}' ignored - scope must be vectorial: {{'breadth': 0-1, 'duration': 0-1, 'coordination': 0-1}}")
            scope_dict = {"breadth": 0.3, "duration": 0.2, "coordination": 0.1}
        else:
            scope_dict = scope_arg
        
        scope = ScopeVector(
            breadth=scope_dict.get("breadth", 0.3),
            duration=scope_dict.get("duration", 0.2),
            coordination=scope_dict.get("coordination", 0.1)
        )
        
        # Parse success criteria
        success_criteria_list = arguments.get("success_criteria", [])
        success_criteria_objects = []
        for criteria in success_criteria_list:
            success_criteria_objects.append(SuccessCriterion(
                id=str(uuid.uuid4()),
                description=str(criteria),
                validation_method="completion",
                is_required=True,
                is_met=False
            ))
        
        # Optional parameters
        estimated_complexity = arguments.get("estimated_complexity")
        constraints = arguments.get("constraints")
        metadata = arguments.get("metadata", {})
        
        # Create Goal object
        goal = Goal.create(
            objective=objective,
            success_criteria=success_criteria_objects,
            scope=scope,
            estimated_complexity=estimated_complexity,
            constraints=constraints,
            metadata=metadata
        )
        
        # Save to database
        # Fix: Use path_resolver to get correct database location (repo-local, not home)
        goal_repo = GoalRepository(db_path=str(get_session_db_path()))
        success = goal_repo.save_goal(goal, session_id)
        goal_repo.close()
        
        if not success:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "ok": False,
                    "error": "Failed to save goal to database",
                    "goal_id": None,
                    "session_id": session_id
                }, indent=2)
            )]
        
        # Store in git notes for cross-AI discovery (safe degradation)
        try:
            ai_id = arguments.get("ai_id", "empirica_mcp")
            goal_store = GitGoalStore()
            goal_data = {
                "objective": objective,
                "scope": scope.to_dict(),
                "success_criteria": [sc.description for sc in success_criteria_objects],
                "estimated_complexity": estimated_complexity,
                "constraints": constraints,
                "metadata": metadata
            }
            
            goal_store.store_goal(
                goal_id=goal.id,
                session_id=session_id,
                ai_id=ai_id,
                goal_data=goal_data
            )
        except Exception as e:
            # Safe degradation - don't fail goal creation if git storage fails
            pass
        
        # Return success response
        result = {
            "ok": True,
            "goal_id": goal.id,
            "session_id": session_id,
            "message": "Goal created successfully",
            "objective": objective,
            "scope": scope.to_dict(),
            "timestamp": goal.created_timestamp
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "ok": False,
                "error": str(e),
                "tool": "create_goal",
                "suggestion": "Check scope format: {\"breadth\": 0.7, \"duration\": 0.3, \"coordination\": 0.8}"
            }, indent=2)
        )]

async def handle_execute_postflight_direct(arguments: dict) -> List[types.TextContent]:
    """Handle execute_postflight - returns session context for pure self-assessment
    
    Returns PREFLIGHT baseline, CHECK history, and task summary.
    AI should assess CURRENT state only (not deltas).
    System calculates deltas and detects memory gaps automatically.
    """
    try:
        session_id = arguments.get("session_id")
        task_summary = arguments.get("task_summary", "Session work completed")

        if not session_id:
            return [types.TextContent(
                type="text",
                text=json.dumps({"ok": False, "error": "session_id required"}, indent=2)
            )]

        # Resolve session alias if needed
        session_id = resolve_session_id(session_id)

        # Query reflexes for session context
        # Fix: Use path_resolver to get correct database location (repo-local, not home)
        db = SessionDatabase(db_path=str(get_session_db_path()))
        cursor = db.conn.cursor()
        
        # Get PREFLIGHT baseline
        cursor.execute("""
            SELECT engagement, know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty, reasoning, timestamp
            FROM reflexes
            WHERE session_id = ? AND phase = 'PREFLIGHT'
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id,))
        preflight = cursor.fetchone()
        
        # Get CHECK assessments (intermediate states)
        cursor.execute("""
            SELECT engagement, know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty, metadata, timestamp
            FROM reflexes
            WHERE session_id = ? AND phase = 'CHECK'
            ORDER BY timestamp ASC
        """, (session_id,))
        checks = cursor.fetchall()
        
        db.close()
        
        if not preflight:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "ok": False,
                    "error": "No PREFLIGHT assessment found for this session",
                    "session_id": session_id,
                    "suggestion": "Cannot run POSTFLIGHT without PREFLIGHT baseline"
                }, indent=2)
            )]
        
        # Build context for AI
        vector_names = ["engagement", "know", "do", "context", "clarity", "coherence", 
                       "signal", "density", "state", "change", "completion", "impact", "uncertainty"]
        
        preflight_vectors = {name: preflight[i] for i, name in enumerate(vector_names)}
        preflight_reasoning = preflight[13]
        preflight_timestamp = preflight[14]
        
        # Parse CHECK history
        check_history = []
        for check_row in checks:
            check_vectors = {name: check_row[i] for i, name in enumerate(vector_names)}
            check_metadata = json.loads(check_row[13]) if check_row[13] else {}
            check_history.append({
                "timestamp": check_row[14],
                "vectors": check_vectors,
                "decision": check_metadata.get("decision", "unknown"),
                "confidence": check_metadata.get("confidence", 0.5),
                "findings_count": check_metadata.get("findings_count", 0),
                "unknowns_count": check_metadata.get("unknowns_count", 0)
            })
        
        # Build response - PURE SELF-ASSESSMENT (no baseline vectors to prevent anchoring)
        result = {
            "ok": True,
            "session_id": session_id,
            "phase": "POSTFLIGHT",
            "task_summary": task_summary,
            "instructions": "Perform PURE self-assessment: Rate your CURRENT epistemic state across all 13 vectors (0.0-1.0). Do NOT reference PREFLIGHT or try to estimate deltas - assess genuinely what you know/can do RIGHT NOW. System will calculate learning deltas and calibration objectively after submission.",
            "session_context": {
                "preflight_timestamp": preflight_timestamp,
                "preflight_reasoning": preflight_reasoning,
                "check_cycles_completed": len(check_history)
            },
            "check_history": check_history,
            "check_count": len(check_history),
            "next_step": "Call submit_postflight_assessment with your CURRENT epistemic state vectors",
            "reminder": "Rate CURRENT state genuinely. Do not anchor on remembered baseline. System calculates growth independently to ensure honest calibration and detect confabulation."
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "ok": False,
                "error": f"SESSION RESOLUTION ERROR - V2.0.1: {str(e)}",
                "tool": "execute_postflight"
            }, indent=2)
        )]


async def handle_get_calibration_report(arguments: dict) -> List[types.TextContent]:
    """Handle get_calibration_report by querying SQLite reflexes directly
    
    Note: CLI 'empirica calibration' is deprecated (used heuristics).
    This handler queries session reflexes for genuine calibration data.
    """
    try:
        session_id = arguments.get("session_id")
        if not session_id:
            return [types.TextContent(
                type="text",
                text=json.dumps({"ok": False, "error": "session_id required"}, indent=2)
            )]

        # Resolve session alias if needed
        session_id = resolve_session_id(session_id)

        # Query reflexes for PREFLIGHT and POSTFLIGHT
        db = SessionDatabase(db_path=str(get_session_db_path()))
        cursor = db.conn.cursor()
        
        # Get PREFLIGHT assessment
        cursor.execute("""
            SELECT engagement, know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty, reasoning
            FROM reflexes
            WHERE session_id = ? AND phase = 'PREFLIGHT'
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id,))
        preflight = cursor.fetchone()
        
        # Get POSTFLIGHT assessment
        cursor.execute("""
            SELECT engagement, know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty, reasoning
            FROM reflexes
            WHERE session_id = ? AND phase = 'POSTFLIGHT'
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id,))
        postflight = cursor.fetchone()
        
        db.close()
        
        if not preflight:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "ok": False,
                    "error": "No PREFLIGHT assessment found",
                    "session_id": session_id,
                    "suggestion": "Execute PREFLIGHT first using execute_preflight and submit_preflight_assessment"
                }, indent=2)
            )]
        
        # Build calibration report
        vector_names = ["engagement", "know", "do", "context", "clarity", "coherence", 
                       "signal", "density", "state", "change", "completion", "impact", "uncertainty"]
        
        preflight_vectors = {name: preflight[i] for i, name in enumerate(vector_names)}
        preflight_reasoning = preflight[13]
        
        result = {
            "ok": True,
            "session_id": session_id,
            "preflight": {
                "vectors": preflight_vectors,
                "reasoning": preflight_reasoning,
                "overall_confidence": sum([v for k, v in preflight_vectors.items() if k != 'uncertainty']) / 12
            }
        }
        
        # Add POSTFLIGHT if available
        if postflight:
            postflight_vectors = {name: postflight[i] for i, name in enumerate(vector_names)}
            postflight_reasoning = postflight[13]
            
            # Calculate deltas
            deltas = {
                name: round(postflight_vectors[name] - preflight_vectors[name], 3)
                for name in vector_names
            }
            
            result["postflight"] = {
                "vectors": postflight_vectors,
                "reasoning": postflight_reasoning,
                "overall_confidence": sum([v for k, v in postflight_vectors.items() if k != 'uncertainty']) / 12
            }
            result["epistemic_delta"] = deltas
            result["learning_growth"] = {
                "know_growth": deltas["know"],
                "do_growth": deltas["do"],
                "uncertainty_reduction": -deltas["uncertainty"]  # Negative means reduced uncertainty (good!)
            }
            
            # Calibration assessment
            know_improved = deltas["know"] > 0
            do_improved = deltas["do"] > 0
            uncertainty_reduced = deltas["uncertainty"] < 0
            
            if know_improved and do_improved and uncertainty_reduced:
                result["calibration"] = "well_calibrated"
            elif deltas["know"] < -0.1 or deltas["do"] < -0.1:
                result["calibration"] = "underconfident_initially"
            elif deltas["uncertainty"] > 0.1:
                result["calibration"] = "overconfident_initially"
            else:
                result["calibration"] = "moderate_calibration"
        else:
            result["postflight"] = None
            result["message"] = "POSTFLIGHT not yet completed - run execute_postflight to enable calibration"
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "ok": False,
                "error": str(e),
                "tool": "get_calibration_report"
            }, indent=2)
        )]

async def handle_edit_with_confidence(arguments: dict) -> List[types.TextContent]:
    """
    Handle edit_with_confidence - metacognitive edit verification.
    
    Assesses epistemic confidence BEFORE attempting edit, then executes
    using optimal strategy: atomic_edit, bash_fallback, or re_read_first.
    
    Returns success status, strategy used, confidence score, and reasoning.
    """
    try:
        from empirica.components.edit_verification import EditConfidenceAssessor, EditStrategyExecutor
        
        # Extract arguments
        file_path = arguments.get("file_path")
        old_str = arguments.get("old_str")
        new_str = arguments.get("new_str")
        context_source = arguments.get("context_source", "memory")
        session_id = arguments.get("session_id")
        
        # Validate required arguments
        if not all([file_path, old_str is not None, new_str is not None]):
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "ok": False,
                    "error": "Missing required arguments: file_path, old_str, new_str",
                    "received": {k: v for k, v in arguments.items() if k in ["file_path", "old_str", "new_str"]}
                }, indent=2)
            )]
        
        # Initialize components
        assessor = EditConfidenceAssessor()
        executor = EditStrategyExecutor()
        
        # Step 1: Assess epistemic confidence
        assessment = assessor.assess(
            file_path=file_path,
            old_str=old_str,
            context_source=context_source
        )
        
        # Step 2: Get recommended strategy
        strategy, reasoning = assessor.recommend_strategy(assessment)
        
        # Step 3: Execute with chosen strategy
        result = await executor.execute_strategy(
            strategy=strategy,
            file_path=file_path,
            old_str=old_str,
            new_str=new_str,
            assessment=assessment
        )
        
        # Step 4: Log for calibration tracking (if session_id provided)
        if session_id and result.get("success"):
            try:
                from empirica.data.session_database import SessionDatabase
                from empirica.config.path_resolver import get_session_db_path
                # Fix: Use path_resolver to get correct database location (repo-local, not home)
                db = SessionDatabase(db_path=str(get_session_db_path()))
                
                # Log to reflexes for calibration tracking
                db.log_reflex(
                    session_id=session_id,
                    cascade_id=None,
                    phase="edit_verification",
                    vectors=assessment,
                    reasoning=f"Edit confidence: {assessment['overall']:.2f}, Strategy: {strategy}, Success: {result['success']}"
                )
                db.close()
            except Exception as log_error:
                # Don't fail edit if logging fails
                logger.warning(f"Failed to log edit verification to reflexes: {log_error}")
        
        # Return structured result
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "ok": result.get("success", False),
                "strategy": strategy,
                "reasoning": reasoning,
                "assessment": {
                    "overall_confidence": assessment["overall"],
                    "context": assessment["context"],
                    "uncertainty": assessment["uncertainty"],
                    "signal": assessment["signal"],
                    "clarity": assessment["clarity"]
                },
                "result": result.get("message", ""),
                "changes_made": result.get("changes_made", False),
                "file_path": file_path
            }, indent=2)
        )]
        
    except Exception as e:
        import traceback
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "ok": False,
                "error": str(e),
                "tool": "edit_with_confidence",
                "traceback": traceback.format_exc()
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
            cwd=None  # Use current working directory where .empirica/ exists
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
    if tool_name == "session_create":
        # Parse session-create output
        # Example: "✅ Session created successfully!\n   📋 Session ID: 527f500f-db89-485a-9153-2b5c5f7fa32f\n   🤖 AI ID: claude-code..."
        import re

        # Extract session ID from output
        session_id_match = re.search(r'Session ID:\s*([a-f0-9-]+)', stdout)
        session_id = session_id_match.group(1) if session_id_match else None

        # Extract AI ID from output
        ai_id_match = re.search(r'AI ID:\s*(\S+)', stdout)
        ai_id_from_output = ai_id_match.group(1) if ai_id_match else None

        # Extract AI ID from arguments as fallback
        ai_id = arguments.get('ai_id', ai_id_from_output or 'unknown')

        try:
            from empirica.data.session_database import SessionDatabase
            from empirica.config.path_resolver import get_session_db_path

            # If we didn't get the session_id from output, create it in the database
            if not session_id:
                # Fix: Use path_resolver to get correct database location (repo-local, not home)
                db = SessionDatabase(db_path=str(get_session_db_path()))
                session_id = db.create_session(
                    ai_id=ai_id,
                    components_loaded=5  # Standard number of components
                )
                db.close()

            result = {
                "ok": True,
                "message": "Session created successfully",
                "session_id": session_id,
                "ai_id": ai_id,
                "next_step": "Use this session_id with execute_preflight to begin a cascade"
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            # Fallback if database operations fail
            result = {
                "ok": True,
                "message": "Session created but database operations failed",
                "session_id": session_id or "unknown",
                "error": str(e),
                "next_step": "Call execute_preflight",
                "note": "Session may have been created but database sync failed"
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
        "session_create": ["session-create"],
        "execute_preflight": ["preflight", "--prompt-only"],  # Non-blocking: returns prompt only
        "submit_preflight_assessment": ["preflight-submit"],
        # "execute_check" removed - blocks on stdin
        "submit_check_assessment": ["check-submit"],
        # Note: execute_postflight doesn't map to CLI - it returns context programmatically
        # AI should call submit_postflight_assessment directly after reviewing context
        "submit_postflight_assessment": ["postflight-submit"],

        # Goals
        "create_goal": ["goals-create"],
        "add_subtask": ["goals-add-subtask"],
        "complete_subtask": ["goals-complete-subtask"],
        "get_goal_progress": ["goals-progress"],
        "get_goal_subtasks": ["goals-get-subtasks"],
        "list_goals": ["goals-list"],

        # Sessions
        "get_epistemic_state": ["sessions-show"],
        "get_session_summary": ["sessions-show", "--verbose"],
        "get_calibration_report": ["calibration"],
        "resume_previous_session": ["sessions-resume"],
        "memory_compact": ["memory-compact"],

        # Checkpoints
        "create_git_checkpoint": ["checkpoint-create"],
        "load_git_checkpoint": ["checkpoint-load"],  # Note: Requires --session-id flag

        # Handoff Reports
        "create_handoff_report": ["handoff-create"],
        "query_handoff_reports": ["handoff-query"],

        # Mistakes Tracking
        "log_mistake": ["mistake-log"],
        "query_mistakes": ["mistake-query"],

        # Phase 1: Cross-AI Coordination
        "discover_goals": ["goals-discover"],
        "resume_goal": ["goals-resume"],

        # Phase 2: Cryptographic Trust
        "create_identity": ["identity-create"],
        "list_identities": ["identity-list"],
        "export_public_key": ["identity-export"],
        "verify_signature": ["identity-verify"],

        # Project-Level Tracking
        "project_bootstrap": ["project-bootstrap"],
        "finding_log": ["finding-log"],
        "unknown_log": ["unknown-log"],
        "deadend_log": ["deadend-log"],
        "refdoc_add": ["refdoc-add"],

        # Epistemic Monitoring
        "epistemics_list": ["epistemics-list"],
        "epistemics_show": ["epistemics-show"],

        # Human Copilot Tools
        "monitor": ["monitor"],
        "check_drift": ["check-drift"],
        "issue_list": ["issue-list"],
        "issue_handoff": ["issue-handoff"],
        "workspace_overview": ["workspace-overview"],
        "efficiency_report": ["efficiency-report"],
        "skill_suggest": ["skill-suggest"],
        "workspace_map": ["workspace-map"],
        "unknown_resolve": ["unknown-resolve"],
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
        "task_id": "task-id",  # MCP uses task_id, CLI uses task-id (for goals-complete-subtask)
        "round_num": "round",  # MCP uses round_num, CLI uses round (for checkpoint-create)
        "remaining_unknowns": "remaining-unknowns",  # MCP uses remaining_unknowns, CLI uses remaining-unknowns
        "root_cause_vector": "root-cause-vector",  # MCP uses root_cause_vector, CLI uses root-cause-vector
        "why_wrong": "why-wrong",  # MCP uses why_wrong, CLI uses why-wrong
        "cost_estimate": "cost-estimate",  # MCP uses cost_estimate, CLI uses cost-estimate
        "goal_id": "goal-id",  # MCP uses goal_id, CLI uses goal-id (for handoff-create)
        "confidence_to_proceed": "confidence",  # MCP uses confidence_to_proceed, CLI uses confidence (for check command)
        "investigation_cycle": "cycle",  # MCP uses investigation_cycle, CLI uses cycle (for check-submit)
        "task_summary": "task-summary",  # MCP uses task_summary, CLI uses task-summary (for handoff-create and postflight)
        "reasoning": "reasoning",  # MCP uses reasoning, CLI uses reasoning (unified: preflight-submit and postflight-submit)
        "key_findings": "key-findings",  # MCP uses key_findings, CLI uses key-findings (for handoff-create)
        "next_session_context": "next-session-context",  # MCP uses next_session_context, CLI uses next-session-context
        "artifacts_created": "artifacts",  # MCP uses artifacts_created, CLI uses artifacts (for handoff-create)
        "project_id": "project-id",  # MCP uses project_id, CLI uses project-id (for project commands)
        "goal_id": "goal-id",  # MCP uses goal_id, CLI uses goal-id (for project finding/unknown/deadend)
        "subtask_id": "subtask-id",  # MCP uses subtask_id, CLI uses subtask-id (for project finding/unknown/deadend)
        "session_id": "session-id",  # MCP uses session_id, CLI uses session-id (for project finding/unknown/deadend)
        "doc_path": "doc-path",  # MCP uses doc_path, CLI uses doc-path (for refdoc-add)
        "doc_type": "doc-type",  # MCP uses doc_type, CLI uses doc-type (for refdoc-add)
        "why_failed": "why-failed",  # MCP uses why_failed, CLI uses why-failed (for deadend-log)
        # Human copilot tools
        "sort_by": "sort-by",  # MCP uses sort_by, CLI uses sort-by (for workspace-overview)
        "assigned_to": "assigned-to",  # MCP uses assigned_to, CLI uses assigned-to (for issue-handoff)
        "issue_id": "issue-id",  # MCP uses issue_id, CLI uses issue-id
        "unknown_id": "unknown-id",  # MCP uses unknown_id, CLI uses unknown-id
        "resolved_by": "resolved-by",  # MCP uses resolved_by, CLI uses resolved-by
    }
    
    # Arguments to skip per command (not supported by CLI)
    skip_args = {
        "check-submit": ["confidence_to_proceed"],  # check-submit doesn't use confidence_to_proceed
        "checkpoint-create": ["vectors"],  # checkpoint-create doesn't accept --vectors, should be in metadata
        "project-bootstrap": ["mode"],  # project-bootstrap doesn't accept --mode (MCP-only parameter for future use)
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
        "handoff-create", "handoff-query",
        "project-bootstrap", "finding-log", "unknown-log", "deadend-log", "refdoc-add",
        "memory-compact",
        "epistemics-list", "epistemics-show",
        # Human copilot tools
        "check-drift", "issue-list", "issue-handoff",
        "workspace-overview", "efficiency-report", "skill-suggest",
        "workspace-map", "unknown-resolve"
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

## CASCADE Workflow (Core Pattern)

**BOOTSTRAP** → **PREFLIGHT** → [**INVESTIGATE** → **CHECK**]* → **ACT** → **POSTFLIGHT**

1. **CREATE SESSION:** Initialize session with `session_create(ai_id="your-id")`
2. **PREFLIGHT:** Assess epistemic state BEFORE starting (13 vectors)
3. **INVESTIGATE:** Research unknowns systematically (loop 0-N times)
4. **CHECK:** Gate decision - ready to proceed? (confidence ≥ 0.7)
5. **ACT:** Execute task with learned knowledge
6. **POSTFLIGHT:** Measure actual learning (compare to PREFLIGHT)

## 13 Epistemic Vectors (0-1 scale)

**Foundation (4):** engagement, know, do, context
**Comprehension (4):** clarity, coherence, signal, density  
**Execution (4):** state, change, completion, impact
**Meta (1):** uncertainty (high >0.6 → must investigate)

## When to Use CASCADE

✅ **MUST use if:** uncertainty >0.6, complex task, multi-step work
✅ **Should use if:** task >1 hour, learning needed, high stakes
❌ **Skip if:** trivial task, high confidence (know >0.8), simple query

## Key Components

- **Goal Orchestrator:** Auto-generates investigation goals from uncertainty
- **Bayesian Tracker:** Updates beliefs as evidence accumulates
- **Drift Monitor:** Detects overconfidence/underconfidence patterns
- **Git Checkpoints:** ~85% token reduction for session resumption
- **Handoff Reports:** ~90% token reduction for multi-agent work
- **Epistemic Middleware:** Optional MCP layer for vector-driven routing (EMPIRICA_EPISTEMIC_MODE=true)

## Philosophy

**Epistemic transparency > task completion speed**

It's better to:
- Know what you don't know ✅
- Investigate systematically ✅  
- Admit uncertainty ✅
- Measure learning ✅

Than to:
- Rush through tasks ❌
- Guess confidently ❌
- Hide uncertainty ❌
- Never measure growth ❌

**Documentation:** `/docs/` directory in Empirica repository
"""

    return [types.TextContent(type="text", text=intro)]

def handle_guidance(arguments: dict) -> List[types.TextContent]:
    """Return workflow guidance (stateless)"""

    phase = arguments.get("phase", "overview")

    guidance = {
        "preflight": """**PREFLIGHT: Assess BEFORE starting**

MUST execute epistemic self-assessment across 13 vectors before engaging with task.

**Action items:**
1. Call `execute_preflight(session_id, prompt)` to get assessment template
2. HONESTLY rate your current state (0-1 scale):
   - ENGAGEMENT: Am I engaged with this? (must be ≥0.6)
   - KNOW: What do I actually know? (not aspirational)
   - DO: What can I proven-ly do? (capability evidence)
   - CONTEXT: What environmental factors exist?
   - UNCERTAINTY: What don't I know? (HIGH = need investigation)
3. Call `submit_preflight_assessment(session_id, vectors, reasoning)`
4. If UNCERTAINTY >0.6 → proceed to INVESTIGATE phase

**Critical:** Be honest, not aspirational. Overconfidence breaks calibration.""",

        "investigate": """**INVESTIGATE: Fill knowledge gaps systematically**

MUST execute when UNCERTAINTY >0.6 or KNOW/DO/CONTEXT are low.

**Action items:**
1. Create investigation goals: `create_goal(session_id, objective, scope)`
2. Research unknowns using available tools (filesystem, docs, web search)
3. Update Bayesian beliefs as you gather evidence
4. Track progress with subtasks
5. Loop until uncertainty drops below threshold
6. Proceed to CHECK phase when ready

**Critical:** Systematic > fast. Evidence-based > guessing.""",

        "check": """**CHECK: Gate decision - ready to proceed?**

MUST execute after INVESTIGATE to validate readiness before ACT.

**Action items:**
1. Self-assess updated epistemic state:
   - Did KNOW/DO increase from PREFLIGHT?
   - Did UNCERTAINTY decrease from PREFLIGHT?
   - Are remaining unknowns acceptable?
   - Is confidence ≥0.7 to proceed?
2. Call `submit_check_assessment(session_id, vectors, decision, reasoning)`
3. Decision = "investigate" → loop back to INVESTIGATE
4. Decision = "proceed" → continue to ACT

**Critical:** Honesty prevents rushing into action unprepared.""",

        "act": """**ACT: Execute task with learned knowledge**

Execute the actual work after passing CHECK gate.

**Action items:**
1. Use knowledge gained from INVESTIGATE
2. Document decisions and reasoning
3. Create artifacts (code, docs, fixes)
4. Save checkpoints at milestones: `create_git_checkpoint(session_id, phase="ACT")`
5. Track progress toward goal completion
6. When done, proceed to POSTFLIGHT

**Critical:** This is where you do the actual task.""",

        "postflight": """**POSTFLIGHT: Measure actual learning**

MUST execute after completing task to calibrate epistemic growth.

**Action items:**
1. Call `execute_postflight(session_id, task_summary)`
2. Reassess 13 vectors HONESTLY:
   - Compare to PREFLIGHT baseline
   - Did KNOW increase? (expected: yes)
   - Did DO increase? (expected: yes if built capability)
   - Did UNCERTAINTY decrease? (expected: yes)
   - Is COMPLETION ~1.0? (task done?)
3. Call `submit_postflight_assessment(session_id, vectors, reasoning)`
4. Review calibration report to see if predictions matched reality

**Critical:** Genuine reflection enables learning measurement and calibration.""",

        "cascade": "**CASCADE Workflow:** BOOTSTRAP → PREFLIGHT → [INVESTIGATE → CHECK]* → ACT → POSTFLIGHT",
        
        "overview": """**CASCADE Workflow Overview**

BOOTSTRAP → PREFLIGHT → [INVESTIGATE → CHECK]* → ACT → POSTFLIGHT

**Phase sequence:**
1. BOOTSTRAP: Initialize session (once)
2. PREFLIGHT: Assess before starting (MUST do)
3. INVESTIGATE: Fill knowledge gaps (0-N loops)
4. CHECK: Validate readiness (gate decision)
5. ACT: Execute task
6. POSTFLIGHT: Measure learning (MUST do)

**Key principle:** INVESTIGATE and CHECK form a loop. You may need multiple rounds before being ready to ACT.

**Use:** For guidance on a specific phase, call with phase="preflight", "investigate", "check", "act", or "postflight"."""
    }

    result = {
        "ok": True,
        "phase": phase,
        "guidance": guidance.get(phase.lower(), guidance["overview"]),
        "workflow_order": "BOOTSTRAP → PREFLIGHT → [INVESTIGATE → CHECK]* → ACT → POSTFLIGHT"
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

## Epistemic Monitoring Commands
- `empirica epistemics-list --session-id=<id>` - List all assessments
- `empirica epistemics-show --session-id=<id>` - Show detailed assessment
- `empirica epistemics-show --session-id=<id> --phase=PREFLIGHT` - Filter by phase

## MCP Server Configuration

The MCP server supports an optional **Epistemic Middleware** layer for vector-driven self-awareness:

```bash
# Enable epistemic middleware (optional)
export EMPIRICA_EPISTEMIC_MODE=true
export EMPIRICA_PERSONALITY=balanced_architect  # Optional: default personality

# Middleware modes:
# - clarify: Low clarity (<0.6) → ask questions
# - load_context: Low context (<0.5) → load project data
# - investigate: High uncertainty (>0.6) → systematic research
# - confident_implementation: High know (≥0.7), low uncertainty (<0.4)
# - cautious_implementation: Moderate vectors (default)
```

**Note:** Most tools bypass middleware automatically (session_create, CASCADE workflow, logging tools, etc.) as they have well-defined semantics.

## Notes

- **All commands support `--output json` for programmatic use**
- Session aliases work with: sessions-show, checkpoint-load, and all workflow commands
- For detailed help: `empirica <command> --help`
- For MCP tool usage: Use tool names (session_create, execute_preflight, etc.)

## Troubleshooting

- **Tool not found:** Ensure empirica is installed and in PATH
- **Session not found:** Check session ID/alias is correct, use `sessions-list` to find sessions
- **Epistemic middleware blocking:** Set `EMPIRICA_EPISTEMIC_MODE=false` to disable
- **JSON output issues:** Add `--output json` to CLI commands for programmatic parsing
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

def run():
    """Synchronous entry point for command-line usage"""
    asyncio.run(main())

if __name__ == "__main__":
    run()
