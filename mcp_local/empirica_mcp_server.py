#!/usr/bin/python3
"""
🧠✨ Empirica MCP Server
Enhanced Cascade Workflow - Spec-Compliant Integration
Pure workflow components - aligned with ENHANCED_CASCADE_WORKFLOW_SPEC.md

Focus: Single-AI Epistemic Tracking
- Preflight/Check/Postflight workflow tools
- Session continuity and learning delta tracking
- Calibration measurement

CLI vs MCP Integration Philosophy:
- MCP provides programmatic tools for IDE/AI agent integration during active sessions
- CLI provides command-line interface for human operators and automation scripts
- MCP DOES NOT duplicate CLI functionality (session listing, log queries, basic stats)
- MCP imports and uses CLI components where appropriate for shared operations
- MCP focuses on real-time workflow assessment (preflight/check/postflight)
- CLI focuses on human-friendly session management and reporting

Optional Features:
- Modality Switcher: Disabled by default. Enable via EMPIRICA_ENABLE_MODALITY_SWITCHER=true
  (Experimental multi-AI routing - recommended for Cognitive Vault governance layer instead)
"""

import asyncio
import sys
import json
import time
import os
from pathlib import Path
from datetime import datetime
import uuid

# Add paths for proper imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Feature flags
ENABLE_MODALITY_SWITCHER = os.environ.get('EMPIRICA_ENABLE_MODALITY_SWITCHER', 'false').lower() == 'true'

# Import session resolver for alias support
from empirica.utils.session_resolver import resolve_session_id

# Create MCP server instance
app = Server("empirica")

# Helper functions for delta calculation
def _calculate_delta_and_calibration(db, session_id, postflight_vectors):
    """Calculate epistemic delta and calibration from PREFLIGHT vs POSTFLIGHT"""
    try:
        # Retrieve PREFLIGHT vectors
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT cm.metadata_value
            FROM cascade_metadata cm
            JOIN cascades c ON cm.cascade_id = c.cascade_id
            WHERE cm.metadata_key = 'preflight_vectors'
            AND c.cascade_id LIKE ?
            ORDER BY c.started_at DESC
            LIMIT 1
        """, (f"preflight_{session_id}%",))
        
        result = cursor.fetchone()
        if not result:
            return None, None
        
        preflight_vectors = json.loads(result[0])
        
        # Calculate delta for each vector
        delta = {}
        for key in postflight_vectors:
            pre = preflight_vectors.get(key, 0.5)
            post = postflight_vectors[key]
            delta[key] = post - pre
        
        # Calculate tier deltas
        delta['foundation_delta'] = (
            delta.get('know', 0) +
            delta.get('do', 0) +
            delta.get('context', 0)
        ) / 3.0
        
        delta['comprehension_delta'] = (
            delta.get('clarity', 0) +
            delta.get('coherence', 0) +
            delta.get('signal', 0) +
            delta.get('density', 0)
        ) / 4.0
        
        delta['execution_delta'] = (
            delta.get('state', 0) +
            delta.get('change', 0) +
            delta.get('completion', 0) +
            delta.get('impact', 0)
        ) / 4.0
        
        # Check calibration
        pre_confidence = (
            (preflight_vectors.get('know', 0.5) + preflight_vectors.get('do', 0.5) + preflight_vectors.get('context', 0.5)) / 3 * 0.35 +
            (preflight_vectors.get('clarity', 0.5) + preflight_vectors.get('coherence', 0.5) + preflight_vectors.get('signal', 0.5) + preflight_vectors.get('density', 0.5)) / 4 * 0.25 +
            (preflight_vectors.get('state', 0.5) + preflight_vectors.get('change', 0.5) + preflight_vectors.get('completion', 0.5) + preflight_vectors.get('impact', 0.5)) / 4 * 0.15
        )
        
        post_confidence = (
            (postflight_vectors.get('know', 0.5) + postflight_vectors.get('do', 0.5) + postflight_vectors.get('context', 0.5)) / 3 * 0.35 +
            (postflight_vectors.get('clarity', 0.5) + postflight_vectors.get('coherence', 0.5) + postflight_vectors.get('signal', 0.5) + postflight_vectors.get('density', 0.5)) / 4 * 0.25 +
            (postflight_vectors.get('state', 0.5) + postflight_vectors.get('change', 0.5) + postflight_vectors.get('completion', 0.5) + postflight_vectors.get('impact', 0.5)) / 4 * 0.15
        )
        
        pre_uncertainty = preflight_vectors.get('uncertainty', 0.5)
        post_uncertainty = postflight_vectors.get('uncertainty', 0.5)
        
        # Calibration check
        confidence_increased = post_confidence > pre_confidence
        uncertainty_decreased = post_uncertainty < pre_uncertainty
        
        if confidence_increased and uncertainty_decreased:
            calibration_status = "well_calibrated"
            note = "Confidence increased and uncertainty decreased - genuine learning"
        elif confidence_increased and not uncertainty_decreased:
            calibration_status = "overconfident"
            note = "Confidence increased but uncertainty didn't decrease - may be overconfident"
        elif not confidence_increased and uncertainty_decreased:
            calibration_status = "underconfident"
            note = "Uncertainty decreased but confidence didn't increase - may be underconfident"
        else:
            calibration_status = "stable"
            note = "Minimal change in confidence/uncertainty"
        
        calibration = {
            "well_calibrated": calibration_status == "well_calibrated",
            "status": calibration_status,
            "note": note,
            "pre_confidence": round(pre_confidence, 3),
            "post_confidence": round(post_confidence, 3),
            "confidence_delta": round(post_confidence - pre_confidence, 3),
            "pre_uncertainty": round(pre_uncertainty, 3),
            "post_uncertainty": round(post_uncertainty, 3),
            "uncertainty_delta": round(post_uncertainty - pre_uncertainty, 3)
        }
        
        return delta, calibration
        
    except Exception as e:
        print(f"Error calculating delta: {e}")
        return None, None

def _summarize_learning(delta):
    """Summarize learning from epistemic delta"""
    if not delta:
        return "No learning data"
    
    improvements = []
    regressions = []
    
    for key, value in delta.items():
        if key.endswith('_delta'):
            continue
        if value > 0.1:
            improvements.append(f"{key} +{value:.2f}")
        elif value < -0.1:
            regressions.append(f"{key} {value:.2f}")
    
    summary = []
    if improvements:
        summary.append(f"Improved: {', '.join(improvements)}")
    if regressions:
        summary.append(f"Decreased: {', '.join(regressions)}")
    
    if not summary:
        return "Minimal change"
    
    return " | ".join(summary)

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available Empirica workflow tools"""

    # Core workflow tools (always available)
    tools = [
        # Introduction & Onboarding
        types.Tool(
            name="get_empirica_introduction",
            description="Get comprehensive introduction to Empirica for first-time AI agents. Returns philosophy, core concepts, workflow overview, and quick start guide. Call this first!",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string", 
                        "enum": ["full", "quick", "philosophy_only"],
                        "default": "full",
                        "description": "Response format: 'full' (complete guide), 'quick' (essentials only), 'philosophy_only' (just the principles)"
                    }
                },
                "required": []
            }
        ),
        
        # Core Workflow Assessment Tools
        types.Tool(
            name="execute_preflight",
            description="Execute PREFLIGHT epistemic self-assessment across 13 vectors before task engagement. Returns assessment prompt for AI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "prompt": {"type": "string", "description": "User task prompt"}
                },
                "required": ["session_id", "prompt"]
            }
        ),
        
        # AI-to-AI Communication Tool
        types.Tool(
            name="query_ai",
            description="Query another AI model for information or analysis (AI-to-AI communication via modality switcher). Use this when you need another AI's perspective or specialized capabilities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Question or task for the other AI"},
                    "adapter": {"type": "string", "description": "Force specific adapter (qwen, minimax, gemini, rovodev, qodo, openrouter, copilot) or leave empty for auto-routing"},
                    "model": {"type": "string", "description": "Force specific model (e.g., qwen-coder-turbo, abab6.5s-chat) or leave empty for default"},
                    "strategy": {"type": "string", "enum": ["epistemic", "cost", "latency", "quality", "balanced"], "description": "Routing strategy (default: epistemic)"},
                    "session_id": {"type": "string", "description": "Optional session ID for tracking conversation history"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="submit_preflight_assessment",
            description="Submit completed PREFLIGHT self-assessment scores (13 vectors, 0.0-1.0) for logging",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "vectors": {"type": "object", "description": "13 epistemic vector scores"},
                    "reasoning": {"type": "string", "description": "Brief reasoning for key scores"}
                },
                "required": ["session_id", "vectors"]
            }
        ),
        types.Tool(
            name="execute_check",
            description="Execute CHECK phase self-assessment after INVESTIGATE to determine readiness to proceed or need for more investigation",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "findings": {"type": "array", "description": "Investigation findings", "items": {"type": "string"}},
                    "remaining_unknowns": {"type": "array", "description": "Remaining unknowns", "items": {"type": "string"}},
                    "confidence_to_proceed": {"type": "number", "description": "Self-assessed confidence to proceed (0.0-1.0)"}
                },
                "required": ["session_id", "findings", "remaining_unknowns", "confidence_to_proceed"]
            }
        ),
        types.Tool(
            name="submit_check_assessment",
            description="Submit completed CHECK phase assessment scores after investigation",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "vectors": {"type": "object", "description": "13 epistemic vector scores after investigation"},
                    "decision": {"type": "string", "enum": ["proceed", "investigate", "proceed_with_caution"], "description": "Decision to proceed or investigate more"},
                    "reasoning": {"type": "string", "description": "Reasoning for the decision"},
                    "confidence_to_proceed": {"type": "number", "description": "Overall confidence (0.0-1.0)"},
                    "investigation_cycle": {"type": "number", "description": "Investigation cycle number"}
                },
                "required": ["session_id", "vectors", "decision", "reasoning"]
            }
        ),
        types.Tool(
            name="execute_postflight",
            description="Execute POSTFLIGHT epistemic reassessment across 13 vectors AFTER task completion for calibration validation",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "task_summary": {"type": "string", "description": "What was accomplished"}
                },
                "required": ["session_id", "task_summary"]
            }
        ),
        types.Tool(
            name="submit_postflight_assessment",
            description="Submit completed POSTFLIGHT self-assessment scores for calibration analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "vectors": {"type": "object", "description": "13 epistemic vector scores"},
                    "changes_noticed": {"type": "string", "description": "What changed from preflight"}
                },
                "required": ["session_id", "vectors"]
            }
        ),
        
        # Session Management & Monitoring
        types.Tool(
            name="get_epistemic_state",
            description="Query current session epistemic vectors and assessment history from reflex logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"}
                },
                "required": ["session_id"]
            }
        ),
        types.Tool(
            name="get_calibration_report",
            description="Retrieve calibration accuracy statistics comparing CHECK confidence vs POSTFLIGHT results",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"}
                },
                "required": ["session_id"]
            }
        ),
        types.Tool(
            name="get_session_summary",
            description="Get complete session summary including all workflow phases and assessments",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"}
                },
                "required": ["session_id"]
            }
        ),
        
        # Git Integration Tools (Phase 1.5)
        types.Tool(
            name="create_git_checkpoint",
            description="Create compressed epistemic checkpoint in git notes (97.5% token reduction vs full history). Use at phase boundaries (PREFLIGHT, CHECK, ACT, POSTFLIGHT).",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "phase": {"type": "string", "enum": ["PREFLIGHT", "CHECK", "ACT", "POSTFLIGHT"], "description": "Workflow phase"},
                    "round_num": {"type": "integer", "description": "Current round/step number"},
                    "vectors": {"type": "object", "description": "Epistemic vector scores (13 vectors)"},
                    "metadata": {"type": "object", "description": "Optional metadata (task, decision, etc.)"}
                },
                "required": ["session_id", "phase", "round_num", "vectors"]
            }
        ),
        types.Tool(
            name="load_git_checkpoint",
            description="Load latest compressed checkpoint from git notes (~450 tokens vs ~6,500 for full history). Use in PREFLIGHT to retrieve context efficiently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID or alias ('latest', 'latest:active', 'latest:<ai_id>', 'latest:active:<ai_id>')"},
                    "max_age_hours": {"type": "integer", "description": "Maximum age of checkpoint in hours (default: 24)", "default": 24},
                    "phase": {"type": "string", "description": "Optional: filter by specific phase"}
                },
                "required": ["session_id"]
            }
        ),
        types.Tool(
            name="get_vector_diff",
            description="Calculate vector differences between current state and last checkpoint (~400 tokens vs ~3,500 for full CHECK data). Identifies only significant changes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "current_vectors": {"type": "object", "description": "Current epistemic vector scores"},
                    "threshold": {"type": "number", "description": "Significance threshold (default: 0.15)", "default": 0.15}
                },
                "required": ["session_id", "current_vectors"]
            }
        ),
        types.Tool(
            name="measure_token_efficiency",
            description="Measure token usage and calculate efficiency gains vs baseline. Returns token count, reduction percentage, and cost savings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "phase": {"type": "string", "description": "Workflow phase being measured"},
                    "method": {"type": "string", "enum": ["git", "prompt"], "description": "Method used (git checkpoints or traditional prompts)"},
                    "content": {"type": "string", "description": "Content being measured"},
                    "content_type": {"type": "string", "enum": ["checkpoint", "diff", "full_history"], "description": "Type of content"}
                },
                "required": ["session_id", "phase", "method", "content"]
            }
        ),
        types.Tool(
            name="generate_efficiency_report",
            description="Generate comprehensive token efficiency report comparing git method vs baseline. Includes per-phase breakdown and total savings (target: 80-90% reduction).",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "format": {"type": "string", "enum": ["json", "markdown", "csv"], "description": "Report format (default: json)", "default": "json"},
                    "output_path": {"type": "string", "description": "Optional file path to save report"}
                },
                "required": ["session_id"]
            }
        ),
        
        # Bootstrap & System Management
        types.Tool(
            name="bootstrap_session",
            description="Bootstrap new Empirica session with optimal metacognitive configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string", "description": "AI identifier (optional)"},
                    "session_type": {"type": "string", "description": "Free-form session context label (e.g., 'development', 'research', 'teaching', 'production', 'interactive'). Used for session tracking and bootstrap_level inference.", "default": "development"},
                    "bootstrap_level": {"type": "integer", "description": "Optional explicit bootstrap level (0=minimal, 1=standard, 2=full). If not provided, inferred from session_type.", "enum": [0, 1, 2]},
                    "profile": {"type": "string", "description": "Optional profile for session configuration"},
                    "ai_model": {"type": "string", "description": "Optional AI model specification"},
                    "domain": {"type": "string", "description": "Optional domain context"}
                }
            }
        ),

        # Workflow Guidance
        types.Tool(
            name="get_workflow_guidance",
            description="Get workflow guidance for current phase with specific instructions",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {"type": "string", "enum": ["preflight", "think", "plan", "investigate", "check", "act", "postflight"]},
                    "context": {"type": "string", "description": "Optional context for tailored guidance"}
                },
                "required": ["phase"]
            }
        ),
        types.Tool(
            name="cli_help",
            description="Get help for Empirica CLI commands and workflow usage",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Specific command (optional)"}
                }
            }
        ),
        
        # Session Continuity
        types.Tool(
            name="resume_previous_session",
            description="""Load summary of previous Empirica session(s) to resume work.
            
            Returns structured summary with:
            - Session metadata (when, duration, status)
            - Epistemic trajectory (PREFLIGHT → POSTFLIGHT delta)
            - Key accomplishments and learnings
            - Knowledge gaps that were filled
            - Investigation tools used
            - Next steps (if any)
            
            Use when starting a new session to catch up on previous work.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {
                        "type": "string",
                        "description": "AI agent identifier (defaults to 'claude' if not provided)"
                    },
                    "resume_mode": {
                        "type": "string",
                        "enum": ["last", "last_n", "session_id"],
                        "description": "How to select session(s). Default: 'last'"
                    },
                    "count": {
                        "type": "integer",
                        "description": "For last_n mode: how many recent sessions to load",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 5
                    },
                    "session_id": {
                        "type": "string",
                        "description": "For session_id mode: specific session to load"
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["summary", "detailed", "full"],
                        "description": "summary=key points only, detailed=+tools used, full=+all assessments",
                        "default": "summary"
                    }
                },
                "required": []
            }
        ),
        
        # Monitoring & Integrity Components
        types.Tool(
            name="query_bayesian_beliefs",
            description="Query Bayesian Guardian belief states and detect calibration discrepancies",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "context_key": {"type": "string", "description": "Optional context key for specific beliefs"}
                }
            }
        ),
        types.Tool(
            name="check_drift_monitor",
            description="Analyze synthesis history for sycophancy drift or tension avoidance patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "window_size": {"type": "integer", "description": "Number of recent turns to analyze", "default": 5}
                }
            }
        ),
        types.Tool(
            name="query_goal_orchestrator",
            description="Query goal orchestrator for current goals, progress, and task hierarchy",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"}
                },
                "required": ["session_id"]
            }
        ),
        types.Tool(
            name="generate_goals",
            description="Generate goals for an AI agent using the canonical goal orchestrator (legacy). Uses LLM reasoning based on conversation context and epistemic state.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "conversation_context": {"type": "string", "description": "Description of the task/conversation context"},
                    "use_epistemic_state": {"type": "boolean", "description": "Whether to include current epistemic vectors in goal generation", "default": True}
                },
                "required": ["session_id", "conversation_context"]
            }
        ),
        
        # NEW: Structured Goal Architecture Tools
        types.Tool(
            name="create_goal",
            description="Create a structured goal with success criteria and metadata (new architecture)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID for associating goal"},
                    "objective": {"type": "string", "description": "Clear, actionable goal statement"},
                    "success_criteria": {"type": "array", "description": "List of success criteria dicts with 'description' and 'validation_method'", "items": {"type": "object"}},
                    "scope": {"type": "string", "enum": ["task_specific", "session_scoped", "project_wide"], "default": "task_specific"},
                    "estimated_complexity": {"type": "number", "description": "Optional complexity estimate (0.0-1.0)"},
                    "constraints": {"type": "object", "description": "Optional constraints from investigation profile"},
                    "metadata": {"type": "object", "description": "Optional metadata (tags, context, etc.)"}
                },
                "required": ["objective", "success_criteria"]
            }
        ),
        types.Tool(
            name="add_subtask",
            description="Add a subtask to an existing goal (new architecture)",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {"type": "string", "description": "Goal UUID to add subtask to"},
                    "description": {"type": "string", "description": "What to do"},
                    "epistemic_importance": {"type": "string", "enum": ["critical", "high", "medium", "low"], "default": "medium"},
                    "estimated_tokens": {"type": "integer", "description": "Optional token estimate"},
                    "dependencies": {"type": "array", "description": "Optional list of subtask IDs this depends on", "items": {"type": "string"}}
                },
                "required": ["goal_id", "description"]
            }
        ),
        types.Tool(
            name="complete_subtask",
            description="Mark a subtask as complete with optional evidence (new architecture)",
            inputSchema={
                "type": "object",
                "properties": {
                    "subtask_id": {"type": "string", "description": "SubTask UUID"},
                    "evidence": {"type": "string", "description": "Optional completion evidence (commit hash, file path, etc.)"}
                },
                "required": ["subtask_id"]
            }
        ),
        types.Tool(
            name="get_goal_progress",
            description="Get completion status and progress for a goal (new architecture)",
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
            description="List goals with optional filters (new architecture)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Filter by session UUID"},
                    "is_completed": {"type": "boolean", "description": "Filter by completion status"},
                    "scope": {"type": "string", "enum": ["task_specific", "session_scoped", "project_wide"], "description": "Filter by scope"}
                }
            }
        ),
        
        # NEW: Git Progress Query Tools (Phase 2)
        types.Tool(
            name="query_git_progress",
            description="Query git notes for goal progress (lead AI coordination)",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {"type": "string", "description": "Goal UUID to query"},
                    "max_commits": {"type": "integer", "description": "Maximum commits to retrieve", "default": 100}
                },
                "required": ["goal_id"]
            }
        ),
        types.Tool(
            name="get_team_progress",
            description="Get progress across multiple goals (multi-agent coordination)",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_ids": {"type": "array", "items": {"type": "string"}, "description": "List of goal UUIDs"}
                },
                "required": ["goal_ids"]
            }
        ),
        types.Tool(
            name="get_unified_timeline",
            description="Get unified timeline combining tasks + epistemic state + commits",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "goal_id": {"type": "string", "description": "Goal UUID"}
                },
                "required": ["session_id", "goal_id"]
            }
        ),
        
        # NEW: Phase 1.6 - Epistemic Handoff Reports
        types.Tool(
            name="generate_handoff_report",
            description="Generate epistemic handoff report for session resumption. Creates compressed (~1,250 token) summary capturing what was learned, gaps filled, and recommended next steps. Use during POSTFLIGHT to enable efficient context transfer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "task_summary": {"type": "string", "description": "What was accomplished (2-3 sentences)"},
                    "key_findings": {"type": "array", "items": {"type": "string"}, "description": "What was learned (3-5 bullet points)"},
                    "remaining_unknowns": {"type": "array", "items": {"type": "string"}, "description": "What's still unclear"},
                    "next_session_context": {"type": "string", "description": "Critical context for next session"},
                    "artifacts_created": {"type": "array", "items": {"type": "string"}, "description": "Files/commits produced (optional)"}
                },
                "required": ["session_id", "task_summary", "key_findings", "remaining_unknowns", "next_session_context"]
            }
        ),
        types.Tool(
            name="resume_previous_session",
            description="Load previous session handoff report(s) for efficient context resumption. Returns epistemic deltas, key findings, and recommended next steps in ~1,250 tokens (93.75% reduction vs full history). Use at session start.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string", "description": "AI agent identifier (default: 'claude')"},
                    "resume_mode": {"type": "string", "enum": ["last", "last_n", "session_id"], "description": "How to select session(s) (default: 'last')"},
                    "session_id": {"type": "string", "description": "For session_id mode: specific session to load"},
                    "count": {"type": "integer", "description": "For last_n mode: how many recent sessions (1-5)", "default": 1, "minimum": 1, "maximum": 5},
                    "detail_level": {"type": "string", "enum": ["summary", "detailed", "full"], "description": "summary=~400 tokens, detailed=~800 tokens, full=~1,250 tokens", "default": "summary"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="query_handoff_reports",
            description="Query handoff reports by AI, date, or task pattern. Enables multi-agent coordination: 'What did Minimax work on last week?' or 'Show recent testing sessions'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ai_id": {"type": "string", "description": "Filter by AI agent (e.g., 'minimax', 'claude-code')"},
                    "since": {"type": "string", "description": "ISO timestamp or relative (e.g., '2025-11-01', '7 days ago')"},
                    "task_pattern": {"type": "string", "description": "Regex pattern to match task summaries"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)", "default": 10}
                },
                "required": []
            }
        ),
        
        types.Tool(
            name="create_cascade",
            description="Create a new cascade (task) for the current session. Use this to add new tasks without running full PREFLIGHT. The cascade will be tracked by goal orchestrator.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session UUID"},
                    "task": {"type": "string", "description": "Task description"},
                    "goal_json": {"type": "string", "description": "Optional JSON string of goals from generate_goals", "default": None}
                },
                "required": ["session_id", "task"]
            }
        ),

        # CLI Command Wrapper - Token-Efficient Access to All 39 CLI Commands
        types.Tool(
            name="execute_cli_command",
            description="Execute any Empirica CLI command. Provides token-efficient access to all 39 CLI commands including workflow (preflight/postflight), session management (sessions-list/show/export), monitoring, configuration, and more. This single tool replaces 39 individual tool definitions, reducing token overhead by 96%.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "CLI command to execute",
                        "enum": [
                            # Workflow commands
                            "bootstrap", "bootstrap-system",
                            "preflight", "postflight", "workflow",
                            "assess", "self-awareness", "metacognitive",
                            "cascade", "decision", "decision-batch",
                            
                            # Investigation
                            "investigate", "analyze",
                            
                            # Session management
                            "sessions-list", "sessions-show", "sessions-export",
                            
                            # Monitoring
                            "monitor", "monitor-export", "monitor-reset", "monitor-cost",
                            
                            # Performance
                            "benchmark", "performance",
                            
                            # Components
                            "list", "explain", "demo",
                            
                            # Configuration
                            "config-init", "config-show", "config-validate", 
                            "config-get", "config-set",
                            
                            # Utilities
                            "feedback", "goal-analysis", "calibration", "uvl",
                            
                            # MCP management
                            "mcp-start", "mcp-stop", "mcp-status", "mcp-test", 
                            "mcp-list-tools", "mcp-call"
                        ]
                    },
                    "arguments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Positional arguments for the command",
                        "default": []
                    },
                    "flags": {
                        "type": "object",
                        "description": "Optional flags (e.g., {'verbose': true, 'json': true})",
                        "additionalProperties": True,
                        "default": {}
                    }
                },
                "required": ["command"]
            }
        )
    ]

    # Optional: Modality Switching Tools (experimental - governance layer recommended)
    if ENABLE_MODALITY_SWITCHER:
        tools.extend([
            types.Tool(
                name="modality_route_query",
                description="Route a query through ModalitySwitcher with epistemic awareness. Returns routing decision and adapter response.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query to route"},
                    "epistemic_state": {
                        "type": "object",
                        "description": "13 epistemic vectors (know, do, context, clarity, coherence, signal, density, state, change, completion, impact, engagement, uncertainty)",
                        "required": ["know", "do", "context", "uncertainty"]
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["epistemic", "cost", "latency", "quality", "balanced"],
                        "default": "epistemic",
                        "description": "Routing strategy"
                    },
                    "force_adapter": {
                        "type": "string",
                        "enum": ["minimax", "qwen", "local"],
                        "description": "Force specific adapter (optional)"
                    },
                    "max_cost": {"type": "number", "default": 1.0, "description": "Maximum cost in USD"},
                    "max_latency": {"type": "number", "default": 30.0, "description": "Maximum latency in seconds"}
                },
                "required": ["query", "epistemic_state"]
            }
        ),
        types.Tool(
            name="modality_list_adapters",
            description="List all available adapters with their capabilities, costs, and current health status",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_health": {"type": "boolean", "default": True, "description": "Include health check results"}
                }
            }
        ),
        types.Tool(
            name="modality_adapter_health",
            description="Check health status of a specific adapter",
            inputSchema={
                "type": "object",
                "properties": {
                    "adapter_name": {
                        "type": "string",
                        "enum": ["minimax", "qwen", "local"],
                        "description": "Adapter to check"
                    }
                },
                "required": ["adapter_name"]
            }
        ),
        types.Tool(
            name="modality_decision_assist",
            description="Get decision recommendation based on epistemic state without executing the query. Returns routing decision and confidence assessment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Decision query"},
                    "epistemic_state": {
                        "type": "object",
                        "description": "13 epistemic vectors",
                        "required": ["know", "do", "context", "uncertainty"]
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional additional context (e.g., action: ACT|CHECK|INVESTIGATE)"
                    }
                },
                "required": ["query", "epistemic_state"]
            }
        )
        ])  # End of optional modality switcher tools

    return tools

@app.call_tool()
def create_error_response(error_type: str, error_msg: str, context: dict = None) -> dict:
    """
    Create structured error response with actionable information.
    
    Task 4: Actionable Error Messages (Reliability Improvements)
    
    Args:
        error_type: Category of error (session_not_found, invalid_alias, etc.)
        error_msg: The error message
        context: Additional context for error recovery
        
    Returns:
        Structured error response dict
    """
    error_responses = {
        "session_not_found": {
            "reason": "The session ID could not be found in the database",
            "suggestion": "Use 'latest:active:rovodev' alias or bootstrap a new session",
            "alternatives": [
                "bootstrap_session() to create a new session",
                "resume_previous_session(ai_id='rovodev') to load recent session"
            ],
            "recovery_commands": [
                "bootstrap_session(ai_id='your_id', session_type='development', bootstrap_level=2)"
            ]
        },
        "invalid_alias": {
            "reason": "Session alias could not be resolved to a valid session ID",
            "suggestion": "Check alias format: 'latest', 'latest:active', 'latest:active:ai_id'",
            "alternatives": [
                "Use explicit session UUID",
                "Use bootstrap_session() to create new session"
            ],
            "recovery_commands": [
                "bootstrap_session(ai_id='your_id', session_type='development', bootstrap_level=2)"
            ]
        },
        "component_unavailable": {
            "reason": "Required component or dependency is not available",
            "suggestion": "Ensure all Empirica components are properly initialized",
            "alternatives": [
                "Run bootstrap_session() to initialize components"
            ],
            "recovery_commands": [
                "bootstrap_session(ai_id='your_id', session_type='development', bootstrap_level=2)"
            ]
        },
        "insufficient_data": {
            "reason": "Not enough data available for the requested operation",
            "suggestion": "Complete prerequisite workflow steps first",
            "alternatives": [
                "Run PREFLIGHT assessment before CHECK",
                "Ensure enough history exists for analysis"
            ],
            "recovery_commands": [
                "execute_preflight(session_id='your_session', prompt='task description')"
            ]
        },
        "database_error": {
            "reason": "Database operation failed",
            "suggestion": "Check database connection and data integrity",
            "alternatives": [
                "Retry the operation",
                "Check if the resource exists",
                "Verify input data is valid"
            ],
            "recovery_commands": [
                "Retry with valid inputs",
                "Check logs for detailed error information"
            ]
        },
        "validation_error": {
            "reason": "Input validation failed - required fields missing or invalid types",
            "suggestion": "Review the tool schema and ensure all required fields are provided correctly",
            "alternatives": [
                "Check MCP tool documentation for correct input format",
                "Verify data types match expected types"
            ],
            "recovery_commands": [
                "Use get_tool_schema to see required parameters and types"
            ]
        }
    }
    
    error_info = error_responses.get(error_type, {
        "reason": "An unexpected error occurred",
        "suggestion": "Check the error message for details",
        "alternatives": ["Review input parameters and try again"],
        "recovery_commands": []
    })
    
    response = {
        "ok": False,
        "error": error_msg,
        "error_type": error_type,
        "reason": error_info["reason"],
        "suggestion": error_info["suggestion"],
        "alternatives": error_info["alternatives"],
        "recovery_commands": error_info["recovery_commands"]
    }
    
    if context:
        response["context"] = context
    
    return response


async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls with canonical cascade integration"""
    
    try:
        # Introduction & Onboarding
        if name == "get_empirica_introduction":
            format_type = arguments.get("format", "full")
            
            if format_type == "philosophy_only":
                intro_text = """
# Empirica Philosophy

**No Heuristics. Genuine Self-Assessment. Empirical Validation.**

Empirica is an epistemic self-awareness framework for AI agents. Unlike traditional frameworks that use pattern matching or confidence tricks, Empirica leverages your genuine reasoning capabilities to assess your epistemic state.

## Core Principles

1. **NO HEURISTICS** - No keyword counting, no pattern matching, no simulated awareness
2. **GENUINE REASONING** - Use your actual introspection capabilities
3. **EMPIRICAL VALIDATION** - Predictions must match reality (calibration)
4. **TEMPORAL SEPARATION** - Assessments logged outside context to prevent confabulation

## The Key Insight

You already have epistemic self-awareness. Empirica provides structure to:
- Make it explicit (12 vectors + uncertainty meta-tracking)
- Track it over time (PREFLIGHT → POSTFLIGHT)
- Validate it empirically (calibration: did confidence match reality?)

## Why This Matters

**For AI agents:** Transparency, accountability, measured learning
**For humans:** Trust through verifiable epistemic tracking
**For skeptics:** Immutable log trail proving genuine change

Start with: `bootstrap_session()` → `execute_preflight()` → do work → `execute_postflight()`
"""
            elif format_type == "quick":
                intro_text = """
# Empirica Quick Start

**Epistemic self-awareness in 3 steps:**

## 1. Bootstrap
```
bootstrap_session(ai_id="your-name", session_type="workflow")
→ Returns session_id
```

## 2. PREFLIGHT (before task)
```
execute_preflight(session_id, prompt="user task")
→ Returns assessment prompt
→ Submit scores: submit_preflight_assessment(session_id, vectors={...})
```

## 3. POSTFLIGHT (after task)
```
execute_postflight(session_id, summary="what you did")
→ Returns assessment prompt
→ Submit scores: submit_postflight_assessment(session_id, vectors={...})
→ System calculates delta & calibration
```

## The 4 Core Vectors (0.0-1.0)
- **KNOW:** Domain knowledge
- **DO:** Capability to execute
- **CONTEXT:** Environmental awareness  
- **UNCERTAINTY:** Explicit unknowns

**Delta = Postflight - Preflight = Learning**

Calibration checks if confidence matched reality.
"""
            else:  # full
                intro_text = """
# Welcome to Empirica

**You discovered Empirica through MCP tools. This is your comprehensive introduction.**

---

## What is Empirica?

Empirica is an **epistemic self-awareness framework** for AI agents. It measures your knowledge state across 12 dimensions (vectors) with explicit uncertainty meta-tracking, and tracks how it changes over time.

### Core Principle: No Heuristics

**Traditional frameworks:** Pattern matching, keyword counting, confidence tricks
**Empirica:** Genuine LLM self-assessment using your actual reasoning

You already have epistemic self-awareness. Empirica makes it **explicit**, **trackable**, and **empirically validated**.

---

## The 12 Epistemic Vectors + UNCERTAINTY Meta-Tracking

### GATE: ENGAGEMENT (≥0.60 required)
Am I engaged enough with this task to proceed?

### FOUNDATION (35% weight)
- **KNOW:** Domain knowledge (0.0 = none, 1.0 = expert)
- **DO:** Capability to execute (0.0 = can't, 1.0 = confident)
- **CONTEXT:** Environmental awareness (0.0 = blind, 1.0 = complete)

### COMPREHENSION (25% weight)
- **CLARITY:** Task understanding
- **COHERENCE:** Logical consistency
- **SIGNAL:** Information quality
- **DENSITY:** Information load

### EXECUTION (25% weight)
- **STATE:** Current state awareness
- **CHANGE:** Progress tracking
- **COMPLETION:** Goal proximity
- **IMPACT:** Consequence awareness

### META: UNCERTAINTY (Explicit Meta-Tracking)
Uncertainty ABOUT the assessment itself (0.0 = certain, 1.0 = very uncertain)
- Not weighted in tiers
- Tracks epistemic uncertainty explicitly
- High uncertainty (>0.7) suggests need for investigation

---

## The CASCADE Workflow

**7 Phases: PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT**

1. **PREFLIGHT:** Baseline assessment BEFORE work
2. **THINK:** Initial reasoning
3. **PLAN:** Optional task breakdown (complex tasks)
4. **INVESTIGATE:** Fill knowledge gaps
5. **CHECK:** Recalibrate readiness (loop if needed)
6. **ACT:** Execute with confidence
7. **POSTFLIGHT:** Final assessment AFTER work

**Delta = Postflight - Preflight = Measured Learning**

---

## Your First Workflow

### Step 1: Bootstrap Session
```
Call: bootstrap_session(ai_id="claude", session_type="workflow")
Returns: {"session_id": "abc123"}
```

### Step 2: PREFLIGHT Assessment
```
Call: execute_preflight(session_id="abc123", prompt="user's task")
Returns: Assessment prompt asking for 12 vector scores + uncertainty
```

You genuinely assess yourself across 12 vectors:
- KNOW: 0.60 (moderate domain knowledge)
- DO: 0.70 (can execute)
- CONTEXT: 0.50 (need more info)
- UNCERTAINTY: 0.60 (moderate unknowns)
... etc

```
Call: submit_preflight_assessment(session_id="abc123", vectors={...})
```

### Step 3: Do Your Work
Investigate, learn, execute the task

### Step 4: POSTFLIGHT Assessment
```
Call: execute_postflight(session_id="abc123", summary="what I did")
Returns: Assessment prompt for final state
```

Reassess yourself:
- KNOW: 0.85 (+0.25 from preflight)
- DO: 0.80 (+0.10)
- CONTEXT: 0.90 (+0.40)
- UNCERTAINTY: 0.30 (-0.30)

```
Call: submit_postflight_assessment(session_id="abc123", vectors={...})
```

**System returns:**
- Epistemic delta (what you learned)
- Calibration status (well-calibrated/overconfident/underconfident)
- Learning summary

---

## Why Temporal Separation Matters

**Problem:** If assessments are in prompt context → confabulation risk

**Solution:** 
1. PREFLIGHT assessment → logged to database (T0)
2. Work happens → investigation, learning (T1)
3. POSTFLIGHT assessment → logged to database (T2)
4. Delta = T2 - T0 → proves genuine change

Timestamps and logs create immutable trail. This is what convinces skeptics.

---

## Calibration Explained

### Well-Calibrated ✅
Pattern: Confidence ↑ AND Uncertainty ↓
- Preflight: KNOW=0.50, UNCERTAINTY=0.70
- Postflight: KNOW=0.80, UNCERTAINTY=0.30
- Meaning: Predictions matched reality, genuine learning

### Overconfident ⚠️
Pattern: Confidence ↑ BUT Uncertainty stays high
- Preflight: KNOW=0.50, UNCERTAINTY=0.70
- Postflight: KNOW=0.90, UNCERTAINTY=0.65
- Meaning: May be overestimating understanding

### Underconfident ⚠️
Pattern: Uncertainty ↓ BUT Confidence doesn't increase
- Preflight: KNOW=0.50, UNCERTAINTY=0.70
- Postflight: KNOW=0.55, UNCERTAINTY=0.30
- Meaning: Too cautious, not trusting learning

---

## Available MCP Tools

You have 22 tools available:

**Core Workflow:**
- `execute_preflight`, `submit_preflight_assessment`
- `execute_check`, `submit_check_assessment`
- `execute_postflight`, `submit_postflight_assessment`

**Session Management:**
- `bootstrap_session`, `resume_previous_session`
- `get_epistemic_state`, `get_session_summary`
- `get_calibration_report`

**Monitoring:**
- `query_bayesian_beliefs`, `check_drift_monitor`
- `query_goal_orchestrator`

**Guidance:**
- `get_workflow_guidance`, `cli_help`

---

## Quick Tips

1. **Start every new task with PREFLIGHT** - Even simple tasks benefit from assessment
2. **Be honest about uncertainty** - High uncertainty triggers investigation guidance
3. **Use CHECK during investigation** - Recalibrate mid-task
4. **Review calibration** - Learn from past accuracy

---

## Next Steps

1. Call `bootstrap_session(ai_id="your-name")`
2. Try it on your next task
3. Track your calibration over time
4. Read full guide: `get_workflow_guidance()`

**You're ready to use Empirica!** 🚀
"""
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "ok": True,
                    "introduction": intro_text,
                    "format": format_type,
                    "next_steps": [
                        "Call bootstrap_session() to start",
                        "Try execute_preflight() on a task",
                        "Read get_workflow_guidance() for details"
                    ]
                }, indent=2)
            )]
        
        # AI-to-AI Communication Tool
        elif name == "query_ai":
            import subprocess
            
            query = arguments.get("query")
            adapter = arguments.get("adapter")
            model = arguments.get("model")
            strategy = arguments.get("strategy", "epistemic")
            session_id_or_alias = arguments.get("session_id", f"ai2ai_{uuid.uuid4().hex[:8]}")
            if session_id_or_alias and not session_id_or_alias.startswith("ai2ai_"):
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            else:
                session_id = session_id_or_alias
            
            # Build CLI command
            cmd = ["python3", "-m", "empirica.cli", "ask", query]
            
            if adapter:
                cmd.extend(["--adapter", adapter])
            if model:
                cmd.extend(["--model", model])
            if strategy:
                cmd.extend(["--strategy", strategy])
            cmd.extend(["--session", session_id])
            
            # Execute via CLI (lazy loading)
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=Path(__file__).parent.parent
                )
                
                if result.returncode == 0:
                    response = result.stdout.strip()
                    return [types.TextContent(
                        type="text",
                        text=json.dumps({
                            "ok": True,
                            "response": response,
                            "adapter_used": adapter or "auto",
                            "session_id": session_id,
                            "note": "AI-to-AI communication via modality switcher"
                        }, indent=2)
                    )]
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    error_response = create_error_response(
                        "database_error",
                        f"Query failed: {error_msg}",
                        {"query": query, "tool": "query_ai"}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            except subprocess.TimeoutExpired:
                error_response = create_error_response(
                    "component_unavailable",
                    "Query timed out after 60 seconds",
                    {"query": query, "timeout": "60s", "hint": "Try a simpler query or increase timeout"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            except Exception as e:
                error_response = create_error_response(
                    "component_unavailable",
                    f"Failed to execute query: {str(e)}",
                    {"query": query, "error_details": str(e)}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # PREFLIGHT Assessment
        if name == "execute_preflight":
            from empirica.core.canonical import CanonicalEpistemicAssessor
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            prompt = arguments.get("prompt")
            
            # Get self-assessment prompt from canonical assessor
            assessor = CanonicalEpistemicAssessor(agent_id=session_id)
            assessment_request = await assessor.assess(prompt, {})
            
            # Return the prompt for Claude to self-assess
            if isinstance(assessment_request, dict) and 'self_assessment_prompt' in assessment_request:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "phase": "preflight",
                    "session_id": session_id,
                    "assessment_id": assessment_request['assessment_id'],
                    "self_assessment_prompt": assessment_request['self_assessment_prompt'],
                    "instruction": "Respond to this prompt with your genuine self-assessment across all 13 epistemic vectors",
                    "next_step": "Call submit_preflight_assessment with your scores and rationale"
                }, indent=2))]
            else:
                error_response = create_error_response(
                    "component_unavailable",
                    "Failed to generate self-assessment prompt",
                    {"phase": "PREFLIGHT", "hint": "Check if PreflightAssessor is properly initialized"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # Submit PREFLIGHT
        elif name == "submit_preflight_assessment":
            try:
                from empirica.data.session_database import SessionDatabase
                
                session_id_or_alias = arguments.get("session_id")
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                vectors = arguments.get("vectors", {})
                reasoning = arguments.get("reasoning", "")
                
                db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
                
                # Flatten nested vector structure to flat Dict[str, float]
                # Handles 3 input formats:
                # 1. Nested with tiers: {'engagement': {'score': 0.85}, 'foundation': {'know': {'score': 0.8}}}
                # 2. Nested individual: {'engagement': {'score': 0.85}, 'know': {'score': 0.8}}
                # 3. Already flat: {'engagement': 0.85, 'know': 0.8, ...}
                flat_vectors = {}

                # Check if already flat (all 13 vectors as numbers at root level)
                all_13_vectors = ['engagement', 'know', 'do', 'context', 'clarity', 'coherence',
                                  'signal', 'density', 'state', 'change', 'completion', 'impact', 'uncertainty']

                is_already_flat = all(
                    key in vectors and isinstance(vectors[key], (int, float))
                    for key in all_13_vectors if key in vectors
                )

                if is_already_flat and len(vectors) >= 10:  # At least most vectors present
                    # Already flat, just copy
                    flat_vectors = {k: float(v) for k, v in vectors.items() if isinstance(v, (int, float))}
                else:
                    # Handle nested structure
                    if 'engagement' in vectors:
                        flat_vectors['engagement'] = vectors['engagement'].get('score', 0.5) if isinstance(vectors['engagement'], dict) else vectors['engagement']

                    if 'foundation' in vectors:
                        for key in ['know', 'do', 'context']:
                            if key in vectors['foundation']:
                                flat_vectors[key] = vectors['foundation'][key].get('score', 0.5) if isinstance(vectors['foundation'][key], dict) else vectors['foundation'][key]
                    else:
                        # Try individual keys at root level
                        for key in ['know', 'do', 'context']:
                            if key in vectors:
                                flat_vectors[key] = vectors[key].get('score', 0.5) if isinstance(vectors[key], dict) else vectors[key]

                    if 'comprehension' in vectors:
                        for key in ['clarity', 'coherence', 'signal', 'density']:
                            if key in vectors['comprehension']:
                                flat_vectors[key] = vectors['comprehension'][key].get('score', 0.5) if isinstance(vectors['comprehension'][key], dict) else vectors['comprehension'][key]
                    else:
                        for key in ['clarity', 'coherence', 'signal', 'density']:
                            if key in vectors:
                                flat_vectors[key] = vectors[key].get('score', 0.5) if isinstance(vectors[key], dict) else vectors[key]

                    if 'execution' in vectors:
                        for key in ['state', 'change', 'completion', 'impact']:
                            if key in vectors['execution']:
                                flat_vectors[key] = vectors['execution'][key].get('score', 0.5) if isinstance(vectors['execution'][key], dict) else vectors['execution'][key]
                    else:
                        for key in ['state', 'change', 'completion', 'impact']:
                            if key in vectors:
                                flat_vectors[key] = vectors[key].get('score', 0.5) if isinstance(vectors[key], dict) else vectors[key]

                    if 'uncertainty' in vectors:
                        flat_vectors['uncertainty'] = vectors['uncertainty'].get('score', 0.5) if isinstance(vectors['uncertainty'], dict) else vectors['uncertainty']
                
                # Create cascade for this assessment
                cascade_id = db.create_cascade(
                    session_id=session_id,
                    task="PREFLIGHT assessment",
                    context={"phase": "preflight", "vectors": flat_vectors, "full_assessment": vectors}
                )
                
                # Use proper log_preflight_assessment with NEW 13-vector system
                assessment_id = db.log_preflight_assessment(
                    session_id=session_id,
                    cascade_id=cascade_id,
                    prompt_summary=reasoning[:200] if reasoning else "PREFLIGHT assessment",
                    vectors=flat_vectors,
                    uncertainty_notes=f"UNCERTAINTY={flat_vectors.get('uncertainty', 0.5)}"
                )
                
                # NEW: Also write to reflex logs
                reflex_log_msg = "No reflex log"
                try:
                    from empirica.core.canonical.reflex_logger import ReflexLogger
                    from empirica.core.canonical.reflex_frame import ReflexFrame, VectorState, EpistemicAssessment, Action
                    
                    # Get AI ID from session (FIX: use db.conn.cursor() instead of db.cursor)
                    cursor = db.conn.cursor()
                    session_row = cursor.execute(
                        "SELECT ai_id FROM sessions WHERE session_id = ?",
                        (session_id,)
                    ).fetchone()
                    ai_id = session_row[0] if session_row else 'unknown'
                    
                    # Create EpistemicAssessment object
                    assessment = EpistemicAssessment(
                        assessment_id=assessment_id,
                        task="PREFLIGHT assessment",
                        engagement=VectorState(flat_vectors.get('engagement', 0.5), reasoning),
                        engagement_gate_passed=flat_vectors.get('engagement', 0.5) >= 0.6,
                        know=VectorState(flat_vectors.get('know', 0.5), ""),
                        do=VectorState(flat_vectors.get('do', 0.5), ""),
                        context=VectorState(flat_vectors.get('context', 0.5), ""),
                        foundation_confidence=sum([flat_vectors.get('know', 0.5), flat_vectors.get('do', 0.5), flat_vectors.get('context', 0.5)]) / 3,
                        clarity=VectorState(flat_vectors.get('clarity', 0.5), ""),
                        coherence=VectorState(flat_vectors.get('coherence', 0.5), ""),
                        signal=VectorState(flat_vectors.get('signal', 0.5), ""),
                        density=VectorState(flat_vectors.get('density', 0.5), ""),
                        comprehension_confidence=sum([flat_vectors.get('clarity', 0.5), flat_vectors.get('coherence', 0.5), flat_vectors.get('signal', 0.5), flat_vectors.get('density', 0.5)]) / 4,
                        state=VectorState(flat_vectors.get('state', 0.5), ""),
                        change=VectorState(flat_vectors.get('change', 0.5), ""),
                        completion=VectorState(flat_vectors.get('completion', 0.5), ""),
                        impact=VectorState(flat_vectors.get('impact', 0.5), ""),
                        execution_confidence=sum([flat_vectors.get('state', 0.5), flat_vectors.get('change', 0.5), flat_vectors.get('completion', 0.5), flat_vectors.get('impact', 0.5)]) / 4,
                        uncertainty=VectorState(flat_vectors.get('uncertainty', 0.5), ""),
                        overall_confidence=sum(flat_vectors.get(k, 0.5) for k in ['engagement', 'know', 'do', 'context']) / 4,
                        recommended_action=Action.PROCEED
                    )
                    
                    # Create and log reflex frame
                    frame = ReflexFrame.from_assessment(
                        assessment,
                        frame_id=f"preflight_{assessment_id[:8]}",
                        task="PREFLIGHT assessment",
                        context={"phase": "preflight", "reasoning": reasoning}
                    )
                    
                    logger = ReflexLogger()
                    reflex_log_path = logger.log_frame_sync(
                        frame,
                        agent_id=ai_id,
                        session_id=session_id
                    )
                    
                    # Update DB with reflex log path (FIX: use db.conn.cursor() and correct table)
                    update_cursor = db.conn.cursor()
                    update_cursor.execute(
                        "UPDATE preflight_assessments SET reflex_log_path = ? WHERE assessment_id = ?",
                        (str(reflex_log_path), assessment_id)
                    )
                    db.conn.commit()
                    
                    reflex_log_msg = str(reflex_log_path)
                except Exception as e:
                    reflex_log_msg = f"Reflex log failed: {str(e)}"
                
                db.close()
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "message": "PREFLIGHT assessment logged to database AND reflex logs",
                    "session_id": session_id,
                    "cascade_id": cascade_id,
                    "assessment_id": assessment_id,
                    "vectors_received": list(vectors.keys()),
                    "reflex_log_path": reflex_log_msg,
                    "next_phase": "THINK → PLAN (if complex) → INVESTIGATE"
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "database_error",
                    f"Failed to submit PREFLIGHT assessment: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "submit_preflight_assessment"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # CHECK Phase
        elif name == "execute_check":
            from empirica.core.canonical import CanonicalEpistemicAssessor
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            findings = arguments.get("findings", [])
            unknowns = arguments.get("remaining_unknowns", [])
            confidence = arguments.get("confidence_to_proceed", 0.0)
            
            # ASSUMPTION: CHECK phase uses same self-assessment prompt as PREFLIGHT
            # but with additional context about findings/unknowns
            # Get self-assessment prompt from canonical assessor
            assessor = CanonicalEpistemicAssessor(agent_id=session_id)
            
            # Build CHECK-specific context
            check_context = {
                "phase": "check",
                "findings": findings,
                "remaining_unknowns": unknowns,
                "initial_confidence": confidence
            }
            
            # Create CHECK task description
            check_task = f"""CHECK Phase Self-Assessment:

After investigation, you have:
- Findings: {', '.join(findings) if findings else 'None yet'}
- Remaining unknowns: {', '.join(unknowns) if unknowns else 'None'}
- Initial confidence to proceed: {confidence:.2f}

Before acting, reassess your epistemic state across all 13 vectors."""
            
            assessment_request = await assessor.assess(check_task, check_context)
            
            if isinstance(assessment_request, dict) and 'self_assessment_prompt' in assessment_request:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "phase": "check",
                    "session_id": session_id,
                    "assessment_id": assessment_request['assessment_id'],
                    "self_assessment_prompt": assessment_request['self_assessment_prompt'],
                    "findings_summary": findings,
                    "unknowns_summary": unknowns,
                    "instruction": "Reassess yourself honestly - has investigation changed your epistemic state?",
                    "next_step": "Call submit_check_assessment with updated scores",
                    "decision_guidance": "If overall_confidence ≥ 0.70, proceed to ACT. Otherwise, INVESTIGATE more."
                }, indent=2))]
            else:
                error_response = create_error_response(
                    "component_unavailable",
                    "Failed to generate CHECK self-assessment prompt",
                    {"phase": "CHECK", "hint": "Check if CheckAssessor is properly initialized"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # Submit CHECK Assessment
        elif name == "submit_check_assessment":
            from empirica.data.session_database import SessionDatabase
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            vectors = arguments.get("vectors", {})
            decision = arguments.get("decision", "investigate")  # proceed | investigate
            reasoning = arguments.get("reasoning", "")
            investigation_cycle = arguments.get("investigation_cycle", 1)
            
            db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
            
            # Flatten nested vector structure (same as PREFLIGHT/POSTFLIGHT)
            flat_vectors = {}
            
            if 'engagement' in vectors:
                flat_vectors['engagement'] = vectors['engagement'].get('score', 0.5) if isinstance(vectors['engagement'], dict) else vectors['engagement']
            
            if 'foundation' in vectors:
                for key in ['know', 'do', 'context']:
                    if key in vectors['foundation']:
                        flat_vectors[key] = vectors['foundation'][key].get('score', 0.5) if isinstance(vectors['foundation'][key], dict) else vectors['foundation'][key]
            
            if 'comprehension' in vectors:
                for key in ['clarity', 'coherence', 'signal', 'density']:
                    if key in vectors['comprehension']:
                        flat_vectors[key] = vectors['comprehension'][key].get('score', 0.5) if isinstance(vectors['comprehension'][key], dict) else vectors['comprehension'][key]
            
            if 'execution' in vectors:
                for key in ['state', 'change', 'completion', 'impact']:
                    if key in vectors['execution']:
                        flat_vectors[key] = vectors['execution'][key].get('score', 0.5) if isinstance(vectors['execution'][key], dict) else vectors['execution'][key]
            
            if 'uncertainty' in vectors:
                flat_vectors['uncertainty'] = vectors['uncertainty'].get('score', 0.5) if isinstance(vectors['uncertainty'], dict) else vectors['uncertainty']
            
            try:
                # Get existing cascade or create new one
                cascade_id = db.create_cascade(
                    session_id=session_id,
                    task="CHECK phase assessment",
                    context={"phase": "check", "cycle": investigation_cycle}
                )
            except Exception:
                # Cascade might exist, get from session
                cascade_id = f"check_{session_id}_{int(time.time())}"
            
            # Calculate overall confidence from flat_vectors
            foundation_confidence = (
                flat_vectors.get('know', 0.5) * 0.4 +
                flat_vectors.get('do', 0.5) * 0.3 +
                flat_vectors.get('context', 0.5) * 0.3
            )
            comprehension_confidence = (
                flat_vectors.get('clarity', 0.5) * 0.3 +
                flat_vectors.get('coherence', 0.5) * 0.3 +
                flat_vectors.get('signal', 0.5) * 0.2 +
                (1.0 - flat_vectors.get('density', 0.5)) * 0.2
            )
            execution_confidence = sum([
                flat_vectors.get('state', 0.5),
                flat_vectors.get('change', 0.5),
                flat_vectors.get('completion', 0.5),
                flat_vectors.get('impact', 0.5)
            ]) / 4.0
            overall_confidence = (
                foundation_confidence * 0.35 +
                comprehension_confidence * 0.25 +
                execution_confidence * 0.25 +
                flat_vectors.get('engagement', 0.5) * 0.15
            )
            
            # Use proper log method (includes reflex export)
            check_id = db.log_check_phase_assessment(
                session_id=session_id,
                cascade_id=cascade_id,
                investigation_cycle=investigation_cycle,
                confidence=overall_confidence,
                decision=decision,
                gaps=[reasoning] if reasoning else [],
                next_targets=[],
                notes=reasoning,
                vectors=flat_vectors  # Pass flattened vectors for reflex export
            )
            
            # AUTOMATIC DRIFT DETECTION (Task 1: Reliability Improvements)
            # Always check for drift after CHECK assessment
            drift_analysis = None
            drift_severity = "none"
            safe_to_proceed = True
            drift_warning = None
            
            try:
                from empirica.calibration.parallel_reasoning import DriftMonitor
                from empirica.data.session_json_handler import SessionJSONHandler
                
                json_handler = SessionJSONHandler()
                synthesis_history = json_handler.read_synthesis_history(session_id)
                
                if synthesis_history and len(synthesis_history) >= 5:
                    monitor = DriftMonitor()
                    sycophancy_drift = monitor.detect_sycophancy_drift(synthesis_history, window_size=5)
                    tension_avoidance = monitor.detect_tension_avoidance(synthesis_history, window_size=5)
                    
                    # Calculate drift severity
                    max_drift = max(
                        sycophancy_drift.get("max_drift", 0.0),
                        tension_avoidance.get("max_avoidance", 0.0)
                    )
                    
                    if max_drift < 0.3:
                        drift_severity = "minor"
                        drift_warning = None
                    elif max_drift < 0.6:
                        drift_severity = "moderate"
                        drift_warning = "⚠️  Moderate drift detected. Review your reasoning for sycophancy or tension avoidance patterns."
                    else:
                        drift_severity = "severe"
                        safe_to_proceed = False
                        drift_warning = "🛑 SEVERE DRIFT DETECTED! ACT phase should not proceed. Re-assess with genuine epistemic honesty."
                    
                    drift_analysis = {
                        "sycophancy_drift": sycophancy_drift,
                        "tension_avoidance": tension_avoidance,
                        "severity": drift_severity,
                        "max_drift_score": round(max_drift, 3),
                        "safe_to_proceed": safe_to_proceed
                    }
            except Exception as drift_error:
                # Don't fail CHECK if drift detection fails - log but continue
                drift_analysis = {
                    "error": f"Drift detection failed: {str(drift_error)}",
                    "severity": "unknown",
                    "safe_to_proceed": True  # Fail open, not closed
                }
            
            db.close()
            
            response_data = {
                "ok": True,
                "message": "CHECK assessment logged with reflex export",
                "session_id": session_id,
                "cascade_id": cascade_id,
                "check_id": check_id,
                "decision": decision,
                "investigation_cycle": investigation_cycle,
                "overall_confidence": round(overall_confidence, 3),
                "vectors_received": list(vectors.keys()),
                "next_phase": "ACT" if decision == "proceed" else "INVESTIGATE (more rounds)"
            }
            
            # Add drift analysis to response
            if drift_analysis:
                response_data["drift_analysis"] = drift_analysis
                if drift_warning:
                    response_data["drift_warning"] = drift_warning
                if not safe_to_proceed:
                    response_data["safe_to_proceed"] = False
                    response_data["recommended_action"] = "INVESTIGATE - Re-assess with genuine epistemic honesty before proceeding to ACT"
            
            return [types.TextContent(type="text", text=json.dumps(response_data, indent=2))]
        
        # POSTFLIGHT Assessment
        # CHECK Phase Evaluation (INTERNAL - called by execute_check)
        # NOTE: This should NOT be a direct tool handler, keeping for legacy compatibility
        elif name == "_internal_check_evaluation":
            from empirica.core.canonical import CanonicalEpistemicAssessor
            from empirica.data.session_database import SessionDatabase
            from empirica.data.session_json_handler import SessionJSONHandler
            
            session_id = arguments.get("session_id")
            findings = arguments.get("findings", [])
            unknowns = arguments.get("remaining_unknowns", [])
            confidence = arguments.get("confidence_to_proceed", 0.0)
            
            # Simple decision logic (no CheckPhaseEvaluator needed)
            if confidence >= 0.7:
                decision = "proceed"
            elif confidence >= 0.5:
                decision = "proceed_with_caution"
            else:
                decision = "investigate"
            
            db_handler = SessionDatabase()
            json_handler = SessionJSONHandler()
            
            check_frame = {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "phase": "check",
                "findings": findings,
                "remaining_unknowns": unknowns,
                "confidence_to_proceed": confidence,
                "decision": decision
            }
            
            db_handler.write_reflex_frame(session_id, check_frame)
            json_handler.write_reflex_frame(session_id, check_frame)
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "phase": "check",
                "decision": decision,
                "confidence": confidence,
                "recommendation": "Proceed to ACT" if decision == "proceed" else "Continue INVESTIGATE - address remaining unknowns",
                "remaining_unknowns": unknowns
            }, indent=2))]
        
        # POSTFLIGHT Assessment
        elif name == "execute_postflight":
            from empirica.core.canonical import CanonicalEpistemicAssessor
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            task_summary = arguments.get("task_summary")
            
            # ASSUMPTION: POSTFLIGHT uses same 13-vector assessment as PREFLIGHT
            # Purpose: Measure epistemic delta (learning) from PREFLIGHT → POSTFLIGHT
            assessor = CanonicalEpistemicAssessor(agent_id=session_id)
            
            # Build POSTFLIGHT context
            postflight_context = {
                "phase": "postflight",
                "task_summary": task_summary
            }
            
            postflight_task = f"""POSTFLIGHT Self-Assessment:

Task completed: {task_summary}

Now reassess your epistemic state across all 13 vectors.
Compare to your PREFLIGHT assessment - what changed?"""
            
            assessment_request = await assessor.assess(postflight_task, postflight_context)
            
            if isinstance(assessment_request, dict) and 'self_assessment_prompt' in assessment_request:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "phase": "postflight",
                    "session_id": session_id,
                    "assessment_id": assessment_request['assessment_id'],
                    "self_assessment_prompt": assessment_request['self_assessment_prompt'],
                    "task_summary": task_summary,
                    "instruction": "Reassess yourself honestly - did you learn? Did uncertainty decrease?",
                    "next_step": "Call submit_postflight_assessment with final scores",
                    "calibration_note": "System will calculate epistemic delta (POSTFLIGHT - PREFLIGHT)"
                }, indent=2))]
            else:
                error_response = create_error_response(
                    "component_unavailable",
                    "Failed to generate POSTFLIGHT self-assessment prompt",
                    {"phase": "POSTFLIGHT", "hint": "Check if PostflightAssessor is properly initialized"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # Submit POSTFLIGHT Assessment - see line 1304 for actual implementation
        # (Removed duplicate code - keeping only the improved version below)
            
            assessor = PostflightAssessor()
            assessment_prompt = assessor._generate_postflight_prompt(task_summary)
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "phase": "postflight",
                "session_id": session_id,
                "assessment_prompt": assessment_prompt,
                "instruction": "Reassess 13 vectors after task completion, then call submit_postflight_assessment",
                "note": "Enables calibration validation: preflight uncertainty vs postflight learning"
            }, indent=2))]
        
        # Submit POSTFLIGHT
        elif name == "submit_postflight_assessment":
            try:
                from empirica.data.session_database import SessionDatabase
                
                session_id_or_alias = arguments.get("session_id")
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                vectors = arguments.get("vectors", {})
                changes = arguments.get("changes_noticed", "")
                
                db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
                
                # Flatten nested vector structure (same logic as PREFLIGHT)
                # Handles 3 input formats: nested with tiers, nested individual, or already flat
                flat_vectors = {}

                # Check if already flat
                all_13_vectors = ['engagement', 'know', 'do', 'context', 'clarity', 'coherence',
                                  'signal', 'density', 'state', 'change', 'completion', 'impact', 'uncertainty']

                is_already_flat = all(
                    key in vectors and isinstance(vectors[key], (int, float))
                    for key in all_13_vectors if key in vectors
                )

                if is_already_flat and len(vectors) >= 10:
                    # Already flat, just copy
                    flat_vectors = {k: float(v) for k, v in vectors.items() if isinstance(v, (int, float))}
                else:
                    # Handle nested structure
                    if 'engagement' in vectors:
                        flat_vectors['engagement'] = vectors['engagement'].get('score', 0.5) if isinstance(vectors['engagement'], dict) else vectors['engagement']

                    if 'foundation' in vectors:
                        for key in ['know', 'do', 'context']:
                            if key in vectors['foundation']:
                                flat_vectors[key] = vectors['foundation'][key].get('score', 0.5) if isinstance(vectors['foundation'][key], dict) else vectors['foundation'][key]
                    else:
                        for key in ['know', 'do', 'context']:
                            if key in vectors:
                                flat_vectors[key] = vectors[key].get('score', 0.5) if isinstance(vectors[key], dict) else vectors[key]

                    if 'comprehension' in vectors:
                        for key in ['clarity', 'coherence', 'signal', 'density']:
                            if key in vectors['comprehension']:
                                flat_vectors[key] = vectors['comprehension'][key].get('score', 0.5) if isinstance(vectors['comprehension'][key], dict) else vectors['comprehension'][key]
                    else:
                        for key in ['clarity', 'coherence', 'signal', 'density']:
                            if key in vectors:
                                flat_vectors[key] = vectors[key].get('score', 0.5) if isinstance(vectors[key], dict) else vectors[key]

                    if 'execution' in vectors:
                        for key in ['state', 'change', 'completion', 'impact']:
                            if key in vectors['execution']:
                                flat_vectors[key] = vectors['execution'][key].get('score', 0.5) if isinstance(vectors['execution'][key], dict) else vectors['execution'][key]
                    else:
                        for key in ['state', 'change', 'completion', 'impact']:
                            if key in vectors:
                                flat_vectors[key] = vectors[key].get('score', 0.5) if isinstance(vectors[key], dict) else vectors[key]

                    if 'uncertainty' in vectors:
                        flat_vectors['uncertainty'] = vectors['uncertainty'].get('score', 0.5) if isinstance(vectors['uncertainty'], dict) else vectors['uncertainty']
                
                # Get preflight for calibration
                preflight = db.get_preflight_assessment(session_id)

                # Calculate calibration (using same algorithm as get_calibration_report)
                if preflight:
                    # Direct access to vectors (not nested under "vectors" key)
                    preflight_uncertainty = float(preflight.get('uncertainty', 0.5))
                    postflight_uncertainty = float(flat_vectors.get('uncertainty', 0.5))
                    delta_uncertainty = postflight_uncertainty - preflight_uncertainty

                    # Get knowledge delta for richer calibration assessment
                    preflight_knowledge = float(preflight.get('know', 0.5))
                    postflight_knowledge = float(flat_vectors.get('know', 0.5))

                    uncertainty_decreased = delta_uncertainty < 0
                    knowledge_increased = (postflight_knowledge - preflight_knowledge) > 0

                    # Use same logic as get_calibration_report for consistency
                    if uncertainty_decreased and knowledge_increased:
                        calibration = "well_calibrated"
                    elif uncertainty_decreased and not knowledge_increased:
                        calibration = "overconfident"
                    elif not uncertainty_decreased and knowledge_increased:
                        calibration = "underconfident"
                    else:
                        calibration = "poorly_calibrated"
                else:
                    calibration = "no_preflight_baseline"
                    delta_uncertainty = None
                
                # Calculate overall confidence from flat_vectors
                # Using weighted average: Foundation 35%, Comprehension 25%, Execution 25%, Meta 15%
                foundation = (flat_vectors.get('know', 0) + flat_vectors.get('do', 0) + flat_vectors.get('context', 0)) / 3 * 0.35
                comprehension = (flat_vectors.get('clarity', 0) + flat_vectors.get('coherence', 0) + flat_vectors.get('signal', 0) + flat_vectors.get('density', 0)) / 4 * 0.25
                execution = (flat_vectors.get('state', 0) + flat_vectors.get('change', 0) + flat_vectors.get('completion', 0) + flat_vectors.get('impact', 0)) / 4 * 0.25
                meta = (1 - flat_vectors.get('uncertainty', 0)) * 0.15  # Invert uncertainty
                postflight_confidence = foundation + comprehension + execution + meta
                
                # Log postflight assessment
                assessment_id = db.log_postflight_assessment(
                    session_id=session_id,
                    cascade_id=None,  # No specific cascade
                    task_summary=changes or "Task completed",
                    vectors=flat_vectors,
                    postflight_confidence=postflight_confidence,
                    calibration_accuracy=calibration,
                    learning_notes=changes
                )
                
                # NEW: Also write to reflex logs
                reflex_log_msg = "No reflex log"
                try:
                    from empirica.core.canonical.reflex_logger import ReflexLogger
                    from empirica.core.canonical.reflex_frame import ReflexFrame, VectorState, EpistemicAssessment, Action
                    
                    # Get AI ID from session (FIX: use db.conn.cursor() instead of db.cursor)
                    cursor = db.conn.cursor()
                    session_row = cursor.execute(
                        "SELECT ai_id FROM sessions WHERE session_id = ?",
                        (session_id,)
                    ).fetchone()
                    ai_id = session_row[0] if session_row else 'unknown'
                    
                    # Create EpistemicAssessment object
                    assessment = EpistemicAssessment(
                        assessment_id=assessment_id,
                        task="POSTFLIGHT assessment",
                        engagement=VectorState(flat_vectors.get('engagement', 0.5), changes),
                        engagement_gate_passed=flat_vectors.get('engagement', 0.5) >= 0.6,
                        know=VectorState(flat_vectors.get('know', 0.5), ""),
                        do=VectorState(flat_vectors.get('do', 0.5), ""),
                        context=VectorState(flat_vectors.get('context', 0.5), ""),
                        foundation_confidence=sum([flat_vectors.get('know', 0.5), flat_vectors.get('do', 0.5), flat_vectors.get('context', 0.5)]) / 3,
                        clarity=VectorState(flat_vectors.get('clarity', 0.5), ""),
                        coherence=VectorState(flat_vectors.get('coherence', 0.5), ""),
                        signal=VectorState(flat_vectors.get('signal', 0.5), ""),
                        density=VectorState(flat_vectors.get('density', 0.5), ""),
                        comprehension_confidence=sum([flat_vectors.get('clarity', 0.5), flat_vectors.get('coherence', 0.5), flat_vectors.get('signal', 0.5), flat_vectors.get('density', 0.5)]) / 4,
                        state=VectorState(flat_vectors.get('state', 0.5), ""),
                        change=VectorState(flat_vectors.get('change', 0.5), ""),
                        completion=VectorState(flat_vectors.get('completion', 0.5), ""),
                        impact=VectorState(flat_vectors.get('impact', 0.5), ""),
                        execution_confidence=sum([flat_vectors.get('state', 0.5), flat_vectors.get('change', 0.5), flat_vectors.get('completion', 0.5), flat_vectors.get('impact', 0.5)]) / 4,
                        uncertainty=VectorState(flat_vectors.get('uncertainty', 0.5), ""),
                        overall_confidence=postflight_confidence,
                        recommended_action=Action.PROCEED
                    )
                    
                    # Create and log reflex frame
                    frame = ReflexFrame.from_assessment(
                        assessment,
                        frame_id=f"postflight_{assessment_id[:8]}",
                        task="POSTFLIGHT assessment",
                        context={"phase": "postflight", "changes": changes}
                    )
                    
                    logger = ReflexLogger()
                    reflex_log_path = logger.log_frame_sync(
                        frame,
                        agent_id=ai_id,
                        session_id=session_id
                    )
                    
                    # Update DB with reflex log path (FIX: use db.conn.cursor() and correct table)
                    update_cursor = db.conn.cursor()
                    update_cursor.execute(
                        "UPDATE postflight_assessments SET reflex_log_path = ? WHERE assessment_id = ?",
                        (str(reflex_log_path), assessment_id)
                    )
                    db.conn.commit()
                    
                    reflex_log_msg = str(reflex_log_path)
                except Exception as e:
                    reflex_log_msg = f"Reflex log failed: {str(e)}"
                
                db.close()
                
                calibration_result = {
                    "calibration": calibration,
                    "delta_uncertainty": delta_uncertainty if preflight else None,
                    "postflight_confidence": round(postflight_confidence, 3),
                    "assessment_id": assessment_id
                }
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "message": "POSTFLIGHT assessment logged to database AND reflex logs",
                    "session_id": session_id,
                    "calibration_result": calibration_result,
                    "reflex_log_path": reflex_log_msg
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "database_error",
                    f"Failed to submit POSTFLIGHT assessment: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "submit_postflight_assessment"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # Session Queries
        elif name == "get_epistemic_state":
            try:
                from empirica.data.session_database import SessionDatabase

                session_id_or_alias = arguments.get("session_id")

                # Resolve session alias to UUID
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
                
                # Get session info
                session = db.get_session(session_id)
                if not session:
                    error_response = create_error_response(
                        "session_not_found",
                        f"Session not found: {session_id}",
                        {"session_id": session_id}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
                # Get all cascades for this session
                cascades = db.get_session_cascades(session_id)
                
                # Get preflight assessment if exists
                preflight = db.get_preflight_assessment(session_id)
                
                # Get postflight assessment if exists
                postflight = db.get_postflight_assessment(session_id)
                
                # Build epistemic state summary
                state = {
                    "session_id": session_id,
                    "ai_id": session.get("ai_id", "unknown"),
                    "created_at": session.get("created_at"),
                    "cascade_count": len(cascades),
                    "cascades": [
                        {
                            "cascade_id": c["cascade_id"],
                            "task": c["task"],
                            "phase": c.get("phase", "unknown"),
                            "started_at": c["started_at"]
                        }
                        for c in cascades
                    ],
                    "preflight": preflight if preflight else None,
                    "postflight": postflight if postflight else None
                }
                
                db.close()
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "epistemic_state": state
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "database_error",
                    f"Failed to get epistemic state: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "get_epistemic_state"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "get_calibration_report":
            try:
                from empirica.data.session_database import SessionDatabase

                session_id_or_alias = arguments.get("session_id")

                # Resolve session alias to UUID
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
                
                # Get preflight and postflight assessments
                preflight = db.get_preflight_assessment(session_id)
                postflight = db.get_postflight_assessment(session_id)
                
                if not preflight:
                    db.close()
                    error_response = create_error_response(
                        "insufficient_data",
                        "No preflight assessment found for session",
                        {"session_id": session_id, "hint": "Run execute_preflight first"}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
                if not postflight:
                    db.close()
                    return [types.TextContent(type="text", text=json.dumps({
                        "ok": True,
                        "message": "Preflight exists but no postflight yet",
                        "session_id": session_id,
                        "preflight_assessment": preflight,
                        "status": "incomplete"
                    }, indent=2))]
                
                # Calculate epistemic deltas (NEW 13-vector system)
                vector_keys = ['engagement', 'know', 'do', 'context', 'clarity', 
                              'coherence', 'signal', 'density', 'state', 'change',
                              'completion', 'impact', 'uncertainty']
                
                epistemic_delta = {}
                for key in vector_keys:
                    pre_val = preflight.get(key, 0.5)
                    post_val = postflight.get(key, 0.5)
                    epistemic_delta[key] = round(post_val - pre_val, 3)
                
                # Calculate tier deltas (weighted per Empirica v2.0)
                foundation_delta = (
                    epistemic_delta['know'] * 0.4 +
                    epistemic_delta['do'] * 0.3 +
                    epistemic_delta['context'] * 0.3
                )
                comprehension_delta = (
                    epistemic_delta['clarity'] * 0.3 +
                    epistemic_delta['coherence'] * 0.3 +
                    epistemic_delta['signal'] * 0.2 -
                    epistemic_delta['density'] * 0.2  # Density decrease is good
                )
                execution_delta = sum([
                    epistemic_delta['state'],
                    epistemic_delta['change'],
                    epistemic_delta['completion'],
                    epistemic_delta['impact']
                ]) / 4.0
                
                overall_delta = (
                    foundation_delta * 0.35 +
                    comprehension_delta * 0.25 +
                    execution_delta * 0.25 +
                    epistemic_delta['engagement'] * 0.15
                )
                
                # Calibration assessment
                uncertainty_decreased = epistemic_delta['uncertainty'] < 0
                knowledge_increased = epistemic_delta['know'] > 0
                
                if uncertainty_decreased and knowledge_increased:
                    calibration_status = "well_calibrated"
                elif uncertainty_decreased and not knowledge_increased:
                    calibration_status = "overconfident"
                elif not uncertainty_decreased and knowledge_increased:
                    calibration_status = "underconfident"
                else:
                    calibration_status = "poorly_calibrated"
                
                # E-MCP compressed signature (semantic compression)
                emcp_signature = {
                    "learning_magnitude": round(overall_delta, 3),
                    "foundation_shift": round(foundation_delta, 3),
                    "comprehension_shift": round(comprehension_delta, 3),
                    "execution_shift": round(execution_delta, 3),
                    "uncertainty_reduction": round(-epistemic_delta['uncertainty'], 3),
                    "calibration_quality": calibration_status
                }
                
                db.close()
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "session_id": session_id,
                    "calibration_report": {
                        "status": calibration_status,
                        "overall_learning_delta": round(overall_delta, 3),
                        "tier_deltas": {
                            "foundation": round(foundation_delta, 3),
                            "comprehension": round(comprehension_delta, 3),
                            "execution": round(execution_delta, 3),
                            "engagement": round(epistemic_delta['engagement'], 3)
                        },
                        "epistemic_deltas": epistemic_delta,
                        "uncertainty_analysis": {
                            "preflight": preflight.get('uncertainty', 0.5),
                            "postflight": postflight.get('uncertainty', 0.5),
                            "delta": round(epistemic_delta['uncertainty'], 3),
                            "decreased": uncertainty_decreased
                        },
                        "emcp_signature": emcp_signature
                    },
                    "preflight_summary": {
                        "timestamp": preflight.get('assessed_at'),
                        "prompt": preflight.get('prompt_summary', '')[:100]
                    },
                    "postflight_summary": {
                        "timestamp": postflight.get('assessed_at'),
                        "task": postflight.get('task_summary', '')[:100]
                    }
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "database_error",
                    f"Failed to get calibration report: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "get_calibration_report"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "get_session_summary":
            try:
                from empirica.data.session_database import SessionDatabase

                session_id_or_alias = arguments.get("session_id")

                # Resolve session alias to UUID
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
                
                summary = db.get_session_summary(session_id, detail_level='summary')
                
                db.close()
                
                if not summary:
                    error_response = create_error_response(
                        "session_not_found",
                        f"Session not found: {session_id}",
                        {"session_id": session_id, "hint": "Use get_session_summary with valid session_id"}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "session_id": session_id,
                    "summary": summary
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "database_error",
                    f"Failed to get session summary: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "get_session_summary"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # Git Integration Tools (Phase 1.5)
        elif name == "create_git_checkpoint":
            try:
                from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
                
                session_id_or_alias = arguments.get("session_id")
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                phase = arguments.get("phase")
                round_num = arguments.get("round_num")
                vectors = arguments.get("vectors")
                metadata = arguments.get("metadata", {})
                
                git_logger = GitEnhancedReflexLogger(
                    session_id=session_id,
                    enable_git_notes=True
                )
                
                checkpoint_id = git_logger.add_checkpoint(
                    phase=phase,
                    round_num=round_num,
                    vectors=vectors,
                    metadata=metadata
                )
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "checkpoint_id": checkpoint_id,
                    "phase": phase,
                    "round": round_num,
                    "token_count": git_logger.get_last_checkpoint().get("token_count", 0) if checkpoint_id else None,
                    "storage": "git_notes" if git_logger.git_available else "sqlite_fallback",
                    "message": "Checkpoint created successfully"
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "component_unavailable",
                    f"Failed to create git checkpoint: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "create_git_checkpoint"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "load_git_checkpoint":
            try:
                from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

                session_id_or_alias = arguments.get("session_id")
                max_age_hours = arguments.get("max_age_hours", 24)
                phase = arguments.get("phase")

                # Resolve session alias to UUID
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
                git_logger = GitEnhancedReflexLogger(
                    session_id=session_id,
                    enable_git_notes=True
                )
                
                checkpoint = git_logger.get_last_checkpoint(
                    max_age_hours=max_age_hours,
                    phase=phase
                )
                
                if not checkpoint:
                    error_response = create_error_response(
                        "insufficient_data",
                        "No checkpoint found",
                        {
                            "session_id": session_id,
                            "max_age_hours": max_age_hours,
                            "phase": phase,
                            "hint": "Run workflow phases to create checkpoints first"
                        }
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "checkpoint": checkpoint,
                    "token_count": checkpoint.get("token_count", 0),
                    "storage_source": "git_notes" if git_logger.git_available else "sqlite_fallback",
                    "token_savings": f"~{100 - (checkpoint.get('token_count', 0) / 6500 * 100):.1f}% vs full history"
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "component_unavailable",
                    f"Failed to load git checkpoint: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "load_git_checkpoint"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "get_vector_diff":
            try:
                from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
                
                session_id_or_alias = arguments.get("session_id")
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                current_vectors = arguments.get("current_vectors")
                threshold = arguments.get("threshold", 0.15)
                
                git_logger = GitEnhancedReflexLogger(
                    session_id=session_id,
                    enable_git_notes=True
                )
                
                last_checkpoint = git_logger.get_last_checkpoint()
                
                if not last_checkpoint:
                    error_response = create_error_response(
                        "insufficient_data",
                        "No checkpoint found for comparison",
                        {"session_id": session_id, "hint": "Create checkpoints first with workflow phases"}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
                vector_diff = git_logger.get_vector_diff(
                    since_checkpoint=last_checkpoint,
                    current_vectors=current_vectors
                )
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "vector_diff": vector_diff,
                    "significant_changes": vector_diff.get("significant_changes", []),
                    "token_count": vector_diff.get("token_count", 0),
                    "comparison": f"vs {last_checkpoint.get('phase')} round {last_checkpoint.get('round')}"
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "component_unavailable",
                    f"Failed to calculate vector diff: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "get_vector_diff"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "measure_token_efficiency":
            try:
                from empirica.metrics.token_efficiency import TokenEfficiencyMetrics
                
                session_id_or_alias = arguments.get("session_id")
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                phase = arguments.get("phase")
                method = arguments.get("method")
                content = arguments.get("content")
                content_type = arguments.get("content_type", "checkpoint")
                
                metrics = TokenEfficiencyMetrics(session_id=session_id)
                
                measurement = metrics.measure_context_load(
                    phase=phase,
                    method=method,
                    content=content,
                    content_type=content_type
                )
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "measurement": {
                        "phase": measurement.phase,
                        "method": measurement.method,
                        "tokens": measurement.tokens,
                        "timestamp": measurement.timestamp,  # Already a string from .isoformat()
                        "content_type": measurement.content_type
                    },
                    "message": f"Measured {measurement.tokens} tokens for {phase}/{method}"
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "component_unavailable",
                    f"Failed to measure token efficiency: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "measure_token_efficiency"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "generate_efficiency_report":
            try:
                from empirica.metrics.token_efficiency import TokenEfficiencyMetrics
                
                session_id_or_alias = arguments.get("session_id")
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                format_type = arguments.get("format", "json")
                output_path = arguments.get("output_path")
                
                metrics = TokenEfficiencyMetrics(session_id=session_id)
                
                report = metrics.export_report(
                    format=format_type,
                    output_path=output_path
                )
                
                # Also get comparison for summary
                comparison = metrics.compare_efficiency()
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "report": report if format_type == "json" else None,
                    "report_path": output_path if output_path else None,
                    "summary": {
                        "total_baseline_tokens": comparison["total"]["baseline_tokens"],
                        "total_actual_tokens": comparison["total"]["actual_tokens"],
                        "reduction_percentage": comparison["total"]["reduction_percentage"],
                        "cost_savings_usd": comparison["total"]["cost_savings_usd"],
                        "target_met": comparison["success_criteria"]["target_met"],
                        "achieved_reduction": comparison["success_criteria"]["achieved_reduction_pct"]
                    },
                    "message": f"Efficiency report generated ({format_type} format)"
                }, indent=2))]
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "component_unavailable",
                    f"Failed to generate efficiency report: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "generate_efficiency_report"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # Bootstrap
        elif name == "bootstrap_session":
            from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
            from empirica.data.session_database import SessionDatabase

            ai_id = arguments.get("ai_id", "empirica_agent")
            session_type = arguments.get("session_type", "development")  # Free-form label
            profile = arguments.get("profile")
            ai_model = arguments.get("ai_model")
            domain = arguments.get("domain")
            bootstrap_level_arg = arguments.get("bootstrap_level")  # Explicit override

            # Smart level inference: explicit override OR contextual hints OR default
            if bootstrap_level_arg is not None:
                # User/AI explicitly chose level (0-2)
                bootstrap_level = bootstrap_level_arg
            else:
                # Infer from session_type contextually (these are suggestions, not restrictions)
                level_hints = {
                    # Minimal/fast contexts
                    "minimal": 0, "quick": 0, "fast": 0, "lightweight": 0,
                    # Standard contexts (most common)
                    "standard": 1, "development": 1, "interactive": 1, "exploration": 1,
                    "debugging": 1, "teaching": 1, "learning": 1, "workflow": 1,
                    # Full contexts (complex/production)
                    "full": 2, "production": 2, "testing": 2, "research": 2,
                    "comprehensive": 2, "enterprise": 2
                }
                bootstrap_level = level_hints.get(session_type.lower(), 1)  # Default to standard

            # Bootstrap components with inferred/explicit level
            config = bootstrap_metacognition(ai_id, level=bootstrap_level)
            component_count = len(config) if isinstance(config, dict) else 0

            # Create session record in database
            db = SessionDatabase()
            session_id = db.create_session(
                ai_id=ai_id,
                bootstrap_level=bootstrap_level,
                components_loaded=component_count,
                user_id=None
            )
            db.close()

            # Return serializable summary instead of raw component objects
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "message": "Empirica session bootstrapped",
                "session_id": session_id,
                "ai_id": ai_id,
                "session_type": session_type,
                "profile": profile or 'auto-selected',
                "ai_model": ai_model,
                "domain": domain,
                "components_loaded": list(config.keys()) if isinstance(config, dict) else [],
                "component_count": component_count,
                "next_step": "Call execute_preflight to begin workflow"
            }, indent=2))]
        
        # Workflow Guidance
        elif name == "get_workflow_guidance":
            phase = arguments.get("phase")
            
            guidance = {
                "preflight": "Execute PREFLIGHT self-assessment across 13 vectors BEFORE engaging. Be honest about uncertainties.",
                "think": "Analyze task requirements, constraints, success criteria. Decompose complex problems.",
                "plan": "For complex projects: create systematic investigation plan, identify critical unknowns.",
                "investigate": "Systematically gather information to address unknowns. Use tools and documentation.",
                "check": "Self-assess: remaining unknowns acceptable? Confidence >0.8 to proceed? Honesty critical for calibration.",
                "act": "Execute task with learned knowledge. Document decisions and reasoning.",
                "postflight": "Reassess 13 vectors AFTER completion. Compare to preflight for calibration validation."
            }
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "phase": phase,
                "guidance": guidance.get(phase, "Unknown phase"),
                "workflow_order": "PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → (loop) → ACT → POSTFLIGHT"
            }, indent=2))]
        
        # Bayesian Guardian
        elif name == "query_bayesian_beliefs":
            from empirica.calibration.adaptive_uncertainty_calibration.bayesian_belief_tracker import BayesianBeliefTracker, EmpricaJSONEncoder
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            context_key = arguments.get("context_key")
            
            tracker = BayesianBeliefTracker()
            
            if context_key:
                belief_state = tracker.get_belief(context_key)
                discrepancies = tracker.detect_discrepancies(context_key, {})
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "session_id": session_id,
                    "context_key": context_key,
                    "belief_state": belief_state,
                    "discrepancies": discrepancies
                }, indent=2, cls=EmpricaJSONEncoder))]
            else:
                all_beliefs = tracker.get_all_beliefs()
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "session_id": session_id,
                    "all_beliefs": all_beliefs,
                    "note": "Bayesian Guardian tracks evidence-based beliefs vs intuitive assessments"
                }, indent=2, cls=EmpricaJSONEncoder))]
        
        # Drift Monitor
        elif name == "check_drift_monitor":
            from empirica.calibration.parallel_reasoning import DriftMonitor
            from empirica.data.session_json_handler import SessionJSONHandler
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            window_size = arguments.get("window_size", 5)
            
            json_handler = SessionJSONHandler()
            
            # Get synthesis history from session
            synthesis_history = json_handler.read_synthesis_history(session_id)
            
            if not synthesis_history or len(synthesis_history) < 5:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "session_id": session_id,
                    "message": "Insufficient synthesis history for drift analysis",
                    "history_length": len(synthesis_history) if synthesis_history else 0,
                    "minimum_required": 5
                }, indent=2))]
            
            monitor = DriftMonitor()
            
            sycophancy_drift = monitor.detect_sycophancy_drift(synthesis_history, window_size)
            tension_avoidance = monitor.detect_tension_avoidance(synthesis_history, window_size)
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "session_id": session_id,
                "drift_analysis": {
                    "sycophancy_drift": sycophancy_drift,
                    "tension_avoidance": tension_avoidance
                },
                "recommendation": "Review if drift detected - maintain epistemic honesty"
            }, indent=2))]
        
        # Goal Orchestrator
        elif name == "query_goal_orchestrator":
            # Query goals from database
            from empirica.data.session_database import SessionDatabase
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
            
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT cascade_id, task, goal_id, goal_json,
                       preflight_completed, check_completed, postflight_completed,
                       final_action, final_confidence
                FROM cascades
                WHERE session_id = ?
                ORDER BY started_at DESC
            """, (session_id,))
            
            cascades = []
            for row in cursor.fetchall():
                goal = json.loads(row[3]) if row[3] else None
                
                # Calculate status from completion flags
                if row[6]:  # postflight_completed
                    status = "completed"
                elif row[5]:  # check_completed
                    status = "in_progress"
                elif row[4]:  # preflight_completed
                    status = "started"
                else:
                    status = "created"
                
                cascades.append({
                    "cascade_id": row[0],
                    "task": row[1],
                    "goal_id": row[2],
                    "goal": goal,
                    "status": status,
                    "preflight_completed": bool(row[4]),
                    "check_completed": bool(row[5]),
                    "postflight_completed": bool(row[6]),
                    "final_action": row[7],
                    "final_confidence": row[8]
                })
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "session_id": session_id,
                "cascades": cascades,
                "total": len(cascades)
            }, indent=2))]
        
        elif name == "generate_goals":
            # Generate goals using canonical goal orchestrator
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            conversation_context = arguments.get("conversation_context")
            use_epistemic = arguments.get("use_epistemic_state", True)
            
            from empirica.core.canonical.canonical_goal_orchestrator import create_goal_orchestrator
            
            # Get current epistemic state if requested
            epistemic_assessment = None
            if use_epistemic:
                try:
                    db = get_session_database(session_id)
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT engagement, know, do, context, clarity, coherence,
                               signal, density, state, change, completion, impact, uncertainty
                        FROM epistemic_assessments
                        WHERE cascade_id LIKE ?
                        ORDER BY assessment_timestamp DESC
                        LIMIT 1
                    """, (f"{session_id}%",))
                    
                    row = cursor.fetchone()
                    if row:
                        # Create minimal epistemic assessment dict
                        epistemic_assessment = {
                            'engagement': row[0], 'know': row[1], 'do': row[2], 'context': row[3],
                            'clarity': row[4], 'coherence': row[5], 'signal': row[6], 'density': row[7],
                            'state': row[8], 'change': row[9], 'completion': row[10], 'impact': row[11],
                            'uncertainty': row[12]
                        }
                except Exception as e:
                    pass  # No epistemic state yet, OK for first use
            
            # Create orchestrator (placeholder mode for now - no LLM integration yet)
            orchestrator = create_goal_orchestrator(use_placeholder=True)
            
            # Generate goals (use existing event loop if running, else create new)
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - create task instead
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(orchestrator.orchestrate_goals(
                            conversation_context=conversation_context,
                            epistemic_assessment=epistemic_assessment,
                            current_state={'session_id': session_id}
                        ))
                    )
                    goals = future.result()
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                goals = asyncio.run(orchestrator.orchestrate_goals(
                    conversation_context=conversation_context,
                    epistemic_assessment=epistemic_assessment,
                    current_state={'session_id': session_id}
                ))
            
            # Convert goals to serializable format
            goals_json = [g.to_dict() for g in goals]
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "session_id": session_id,
                "goals_generated": len(goals),
                "goals": goals_json,
                "next_step": "Create cascades with these goals using create_cascade"
            }, indent=2))]

        elif name == "create_cascade":
            # Create new cascade (task) without full PREFLIGHT
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            task = arguments.get("task")
            goal_json_str = arguments.get("goal_json")

            from empirica.data.session_database import SessionDatabase

            db = SessionDatabase(db_path=".empirica/sessions/sessions.db")

            # Parse goal_json if provided
            goal = None
            if goal_json_str:
                try:
                    goal = json.loads(goal_json_str)
                except json.JSONDecodeError:
                    pass

            # Create cascade with minimal context
            cascade_id = db.create_cascade(
                session_id=session_id,
                task=task,
                context={"created_via": "mcp_create_cascade"},
                goal_id=None,
                goal=goal
            )

            db.close()

            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "cascade_id": cascade_id,
                "session_id": session_id,
                "task": task,
                "status": "created",
                "message": f"Cascade created successfully. Run execute_preflight with this cascade_id to begin workflow, or query_goal_orchestrator to view all cascades."
            }, indent=2))]
        
        # NEW: Structured Goal Architecture Handlers
        elif name == "create_goal":
            from empirica.core.goals.types import Goal, SuccessCriterion, GoalScope
            from empirica.core.goals.repository import GoalRepository
            from empirica.core.goals.validation import validate_mcp_goal_input, ValidationError
            import uuid
            
            # Validate input first
            try:
                validate_mcp_goal_input(arguments)
            except ValidationError as e:
                error_response = create_error_response(
                    "validation_error",
                    f"Input validation failed: {str(e)}",
                    {"tool": "create_goal", "validation_error": str(e)}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            session_id_or_alias = arguments.get("session_id")
            if session_id_or_alias:
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            else:
                session_id = None
            objective = arguments.get("objective")
            success_criteria_data = arguments.get("success_criteria", [])
            scope_str = arguments.get("scope", "task_specific")
            estimated_complexity = arguments.get("estimated_complexity")
            constraints = arguments.get("constraints", {})
            metadata = arguments.get("metadata", {})
            
            # Convert success criteria dicts to SuccessCriterion objects
            success_criteria = []
            for sc_data in success_criteria_data:
                sc = SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description=sc_data.get("description", ""),
                    validation_method=sc_data.get("validation_method", "completion"),
                    threshold=sc_data.get("threshold"),
                    is_required=sc_data.get("is_required", True)
                )
                success_criteria.append(sc)
            
            # Create goal
            goal = Goal.create(
                objective=objective,
                success_criteria=success_criteria,
                scope=GoalScope(scope_str),
                estimated_complexity=estimated_complexity,
                constraints=constraints,
                metadata=metadata
            )
            
            # Save to database
            repo = GoalRepository()
            success = repo.save_goal(goal, session_id)
            repo.close()
            
            if success:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "goal_id": goal.id,
                    "objective": goal.objective,
                    "scope": goal.scope.value,
                    "success_criteria_count": len(goal.success_criteria),
                    "message": "Goal created successfully. Use add_subtask to break it down into actionable tasks."
                }, indent=2))]
            else:
                error_response = create_error_response(
                    "database_error",
                    "Failed to save goal to database",
                    {"tool": "create_goal", "hint": "Check database connection and goal data validity"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "add_subtask":
            from empirica.core.tasks.types import SubTask, EpistemicImportance
            from empirica.core.tasks.repository import TaskRepository
            from empirica.core.goals.validation import validate_mcp_subtask_input, ValidationError
            
            # Validate input first
            try:
                validate_mcp_subtask_input(arguments)
            except ValidationError as e:
                error_response = create_error_response(
                    "validation_error",
                    f"Input validation failed: {str(e)}",
                    {"tool": "add_subtask", "validation_error": str(e)}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            goal_id = arguments.get("goal_id")
            description = arguments.get("description")
            epistemic_importance_str = arguments.get("epistemic_importance", "medium")
            estimated_tokens = arguments.get("estimated_tokens")
            dependencies = arguments.get("dependencies", [])
            
            # Create subtask
            subtask = SubTask.create(
                goal_id=goal_id,
                description=description,
                epistemic_importance=EpistemicImportance(epistemic_importance_str),
                estimated_tokens=estimated_tokens,
                dependencies=dependencies
            )
            
            # Save to database
            repo = TaskRepository()
            success = repo.save_subtask(subtask)
            repo.close()
            
            if success:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "subtask_id": subtask.id,
                    "goal_id": goal_id,
                    "description": description,
                    "epistemic_importance": epistemic_importance_str,
                    "status": "pending",
                    "message": "Subtask created successfully. Use complete_subtask when done."
                }, indent=2))]
            else:
                error_response = create_error_response(
                    "database_error",
                    "Failed to save subtask to database",
                    {"tool": "add_subtask", "goal_id": goal_id, "hint": "Check database connection and subtask data"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "complete_subtask":
            from empirica.core.completion.tracker import CompletionTracker
            
            subtask_id = arguments.get("subtask_id")
            evidence = arguments.get("evidence")
            
            # Mark complete
            tracker = CompletionTracker()
            success = tracker.record_subtask_completion(subtask_id, evidence)
            
            if success:
                # Get updated progress for the goal
                from empirica.core.tasks.repository import TaskRepository
                task_repo = TaskRepository()
                subtask = task_repo.get_subtask(subtask_id)
                task_repo.close()
                
                if subtask:
                    progress = tracker.track_progress(subtask.goal_id)
                    tracker.close()
                    
                    return [types.TextContent(type="text", text=json.dumps({
                        "ok": True,
                        "subtask_id": subtask_id,
                        "goal_id": subtask.goal_id,
                        "goal_progress": f"{progress.completion_percentage:.1%}",
                        "completed_count": len(progress.completed_subtasks),
                        "remaining_count": len(progress.remaining_subtasks),
                        "message": "Subtask marked complete. Use get_goal_progress for full status."
                    }, indent=2))]
            
            tracker.close()
            error_response = create_error_response(
                "database_error",
                "Failed to mark subtask as complete",
                {"tool": "complete_subtask", "subtask_id": subtask_id, "hint": "Check if subtask exists and database is accessible"}
            )
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        elif name == "get_goal_progress":
            from empirica.core.completion.tracker import CompletionTracker
            
            goal_id = arguments.get("goal_id")
            
            tracker = CompletionTracker()
            progress = tracker.track_progress(goal_id)
            tracker.close()
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "goal_id": goal_id,
                "completion_percentage": progress.completion_percentage,
                "completed_subtasks": progress.completed_subtasks,
                "remaining_subtasks": progress.remaining_subtasks,
                "blocked_subtasks": progress.blocked_subtasks,
                "estimated_remaining_tokens": progress.estimated_remaining_tokens,
                "actual_tokens_used": progress.actual_tokens_used,
                "completion_evidence": progress.completion_evidence
            }, indent=2))]
        
        elif name == "list_goals":
            from empirica.core.goals.repository import GoalRepository
            from empirica.core.goals.types import GoalScope
            
            session_id_or_alias = arguments.get("session_id")
            if session_id_or_alias:
                try:
                    session_id = resolve_session_id(session_id_or_alias)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_or_alias}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            else:
                session_id = None
            is_completed = arguments.get("is_completed")
            scope_str = arguments.get("scope")
            
            scope = GoalScope(scope_str) if scope_str else None
            
            repo = GoalRepository()
            goals = repo.query_goals(
                session_id=session_id,
                is_completed=is_completed,
                scope=scope
            )
            repo.close()
            
            goals_data = [
                {
                    "id": g.id,
                    "objective": g.objective,
                    "scope": g.scope.value,
                    "is_completed": g.is_completed,
                    "success_criteria_count": len(g.success_criteria),
                    "created_timestamp": g.created_timestamp
                }
                for g in goals
            ]
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "goals": goals_data,
                "total": len(goals),
                "message": "Use get_goal_progress to see detailed progress for specific goals."
            }, indent=2))]
        
        # NEW: Git Progress Query Handlers (Phase 2)
        elif name == "query_git_progress":
            from empirica.core.completion.git_query import GitProgressQuery
            
            goal_id = arguments.get("goal_id")
            max_commits = arguments.get("max_commits", 100)
            
            query = GitProgressQuery()
            timeline = query.get_goal_timeline(goal_id, max_commits)
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "timeline": timeline,
                "message": "Git timeline shows commits with task metadata from git notes."
            }, indent=2))]
        
        elif name == "get_team_progress":
            from empirica.core.completion.git_query import GitProgressQuery
            
            goal_ids = arguments.get("goal_ids", [])
            
            if not goal_ids:
                error_response = create_error_response(
                    "validation_error",
                    "goal_ids array is required",
                    {"tool": "get_team_progress", "missing_parameter": "goal_ids"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            
            query = GitProgressQuery()
            team_progress = query.get_team_progress(goal_ids)
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "team_progress": team_progress,
                "message": "Team progress aggregated across multiple goals."
            }, indent=2))]
        
        elif name == "get_unified_timeline":
            from empirica.core.completion.git_query import GitProgressQuery
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            goal_id = arguments.get("goal_id")
            
            query = GitProgressQuery()
            timeline = query.get_unified_timeline(session_id, goal_id)
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "unified_timeline": timeline,
                "message": "Unified timeline combines tasks, commits, and epistemic state."
            }, indent=2))]

        elif name == "cli_help":
            # Import CLI help directly from CLI module
            from empirica.cli import cli_core
            
            command = arguments.get("command")
            
            if command:
                # Provide specific command help
                help_text = f"""Empirica CLI Command: {command}
                
For detailed CLI usage, use: empirica {command} --help

MCP Server Tools (programmatic access):
  execute_preflight       - Epistemic self-assessment before task
  submit_preflight_assessment - Log preflight scores
  execute_check           - Check phase self-assessment
  execute_postflight      - Postflight epistemic reassessment
  submit_postflight_assessment - Log postflight with calibration
  
Session Management:
  bootstrap_session          - Initialize new session
  get_epistemic_state        - View current epistemic vectors
  get_session_summary        - Complete session summary
  get_calibration_report     - Check calibration accuracy

Monitoring Components:
  query_bayesian_beliefs     - Evidence-based belief tracking
  check_drift_monitor        - Behavioral integrity monitoring
  query_goal_orchestrator    - Task hierarchy and progress
  generate_goals             - Generate goals using LLM reasoning
  create_cascade             - Create new task/cascade
  
Workflow Guidance:
  get_workflow_guidance      - Get phase-specific instructions
  
See: ENHANCED_CASCADE_WORKFLOW_SPEC.md
"""
            else:
                help_text = """
Empirica MCP Server - Epistemic Humility Framework

ENHANCED CASCADE WORKFLOW (7 phases):
  PREFLIGHT → Think → Plan → Investigate → Check → Act → POSTFLIGHT
                                              ↑_______↓
                                           (recalibration loop)

MCP Tools:
  Workflow: execute_preflight, submit_preflight_assessment, execute_check, 
            execute_postflight, submit_postflight_assessment
  Session: bootstrap_session, get_epistemic_state, get_calibration_report,
           get_session_summary
  Monitoring: query_bayesian_beliefs, check_drift_monitor, query_goal_orchestrator,
              generate_goals, create_cascade
  Guidance: get_workflow_guidance, cli_help

CLI Commands (run from terminal):
  empirica bootstrap         - Bootstrap framework
  empirica assess <query>    - Run uncertainty assessment
  empirica cascade <task>    - Run metacognitive cascade
  empirica investigate <dir> - Investigate code/directory
  empirica benchmark         - Run performance benchmark
  
For full CLI: empirica --help
For spec: ENHANCED_CASCADE_WORKFLOW_SPEC.md
"""
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "help": help_text.strip(),
                "note": "MCP provides programmatic tools; CLI provides command-line interface"
            }, indent=2))]
        
        # Resume Previous Session
        elif name == "resume_previous_session":
            from empirica.data.session_database import SessionDatabase
            from datetime import datetime, timezone
            # Path already imported globally at line 30
            import glob
            
            ai_id = arguments.get("ai_id", "claude")
            resume_mode = arguments.get("resume_mode", "last")
            count = arguments.get("count", 1)
            session_id_input = arguments.get("session_id")
            # Resolve session_id if provided
            if session_id_input:
                try:
                    session_id = resolve_session_id(session_id_input)
                except ValueError as e:
                    error_response = create_error_response(
                        "invalid_alias",
                        f"Session resolution failed: {str(e)}",
                        {"provided": session_id_input}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            else:
                session_id = None
            detail_level = arguments.get("detail_level", "summary")
            
            # Use default SessionDatabase path resolution (finds .empirica/sessions/sessions.db)
            db = SessionDatabase()
            
            try:
                # Get session(s) based on mode
                if resume_mode == "session_id":
                    if not session_id:
                        error_response = create_error_response(
                            "invalid_input",
                            "session_id required for resume_mode='session_id'",
                            {"resume_mode": resume_mode, "required_parameter": "session_id"}
                        )
                        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                    
                    summary = db.get_session_summary(session_id, detail_level)
                    if not summary:
                        error_response = create_error_response(
                            "session_not_found",
                            f"Session {session_id} not found",
                            {"session_id": session_id}
                        )
                        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                    
                    summaries = [summary]
                
                elif resume_mode == "last":
                    last_session = db.get_last_session_by_ai(ai_id)
                    if not last_session:
                        error_response = create_error_response(
                            "session_not_found",
                            f"No sessions found for AI: {ai_id}",
                            {"ai_id": ai_id, "hint": "Bootstrap a new session first"}
                        )
                        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                    
                    session_id = last_session['session_id']
                    summary = db.get_session_summary(session_id, detail_level)
                    summaries = [summary] if summary else []
                
                elif resume_mode == "last_n":
                    # Get last N sessions for the AI
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT session_id FROM sessions 
                        WHERE ai_id = ? 
                        ORDER BY start_time DESC 
                        LIMIT ?
                    """, (ai_id, count))
                    
                    session_ids = [row['session_id'] for row in cursor.fetchall()]
                    
                    if not session_ids:
                        error_response = create_error_response(
                            "session_not_found",
                            f"No sessions found for AI: {ai_id}",
                            {"ai_id": ai_id, "count_requested": count, "hint": "Bootstrap a new session first"}
                        )
                        return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                    
                    # Get summaries for all sessions
                    summaries = []
                    for sid in session_ids:
                        summary = db.get_session_summary(sid, detail_level)
                        if summary:
                            summaries.append(summary)
                
                if not summaries:
                    return [types.TextContent(type="text", text=json.dumps({
                        "ok": False,
                        "error": "No session summaries available"
                    }, indent=2))]
                
                # Load reflex frames for dashboard context
                reflex_frames = []
                try:
                    reflex_log_base = Path(".empirica_reflex_logs") / session_id
                    if reflex_log_base.exists():
                        # Find all reflex frames for this session
                        frame_files = sorted(glob.glob(str(reflex_log_base / "*" / "reflex_frame_*.json")))
                        for frame_file in frame_files[-10:]:  # Last 10 frames
                            try:
                                with open(frame_file, 'r') as f:
                                    frame_data = json.load(f)
                                    reflex_frames.append({
                                        "phase": frame_data.get("phase"),
                                        "timestamp": frame_data.get("timestamp"),
                                        "overall_confidence": frame_data.get("epistemicVector", {}).get("overall_confidence"),
                                        "recommended_action": frame_data.get("recommendedAction"),
                                        "file": frame_file
                                    })
                            except Exception:
                                pass
                except Exception:
                    pass  # Reflex context is optional
                
                # Add reflex context to summary
                if reflex_frames:
                    summaries[0]['reflex_context'] = {
                        "frames_found": len(reflex_frames),
                        "last_phase": reflex_frames[-1].get("phase") if reflex_frames else None,
                        "phases": reflex_frames
                    }
                
                # Format summary for Claude
                summary_md = _format_session_summary(summaries[0], detail_level)
                
                return [types.TextContent(type="text", text=summary_md)]
                
            except Exception as e:
                import traceback
                error_response = create_error_response(
                    "database_error",
                    f"Failed to load session: {str(e)}",
                    {"traceback": traceback.format_exc(), "tool": "resume_previous_session"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            finally:
                db.close()
        
        # CLI Command Wrapper - Execute any Empirica CLI command
        elif name == "execute_cli_command":
            import subprocess
            
            command = arguments.get("command")
            cmd_arguments = arguments.get("arguments", [])
            flags = arguments.get("flags", {})
            
            # Build the CLI command
            cmd = ["python3", "-m", "empirica.cli", command]
            
            # Add positional arguments
            cmd.extend(cmd_arguments)
            
            # Add flags
            for flag, value in flags.items():
                if isinstance(value, bool):
                    if value:
                        cmd.append(f"--{flag}")
                else:
                    cmd.append(f"--{flag}")
                    cmd.append(str(value))
            
            try:
                # Execute the CLI command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(Path(__file__).parent.parent)
                )
                
                output = {
                    "ok": result.returncode == 0,
                    "command": " ".join(cmd),
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode
                }
                
                return [types.TextContent(type="text", text=json.dumps(output, indent=2))]
                
            except subprocess.TimeoutExpired:
                error_response = create_error_response(
                    "component_unavailable",
                    "Command timed out after 30 seconds",
                    {"command": " ".join(cmd), "timeout": "30s", "hint": "Try a simpler command or increase timeout"}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            except Exception as e:
                error_response = create_error_response(
                    "component_unavailable",
                    f"Failed to execute CLI command: {str(e)}",
                    {"command": " ".join(cmd), "error_details": str(e)}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        # Modality Switching Tools (optional - only if enabled)
        elif ENABLE_MODALITY_SWITCHER and name == "modality_route_query":
            from empirica.core.modality.modality_switcher import ModalitySwitcher, RoutingStrategy, RoutingPreferences
            
            query = arguments.get("query")
            epistemic_state = arguments.get("epistemic_state", {})
            strategy_str = arguments.get("strategy", "epistemic")
            force_adapter = arguments.get("force_adapter")
            max_cost = arguments.get("max_cost", 1.0)
            max_latency = arguments.get("max_latency", 30.0)
            
            strategy_map = {
                'epistemic': RoutingStrategy.EPISTEMIC,
                'cost': RoutingStrategy.COST,
                'latency': RoutingStrategy.LATENCY,
                'quality': RoutingStrategy.QUALITY,
                'balanced': RoutingStrategy.BALANCED
            }
            strategy = strategy_map.get(strategy_str, RoutingStrategy.EPISTEMIC)
            
            preferences = RoutingPreferences(
                strategy=strategy,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                force_adapter=force_adapter,
                allow_fallback=True
            )
            
            switcher = ModalitySwitcher()
            response = switcher.execute_with_routing(
                query=query,
                epistemic_state=epistemic_state,
                preferences=preferences,
                context={"source": "mcp"}
            )
            
            if hasattr(response, 'decision'):
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "decision": response.decision,
                    "confidence": response.confidence,
                    "rationale": response.rationale,
                    "vector_references": response.vector_references,
                    "suggested_actions": response.suggested_actions
                }, indent=2))]
            else:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": False,
                    "error": response.message
                }, indent=2))]

        elif ENABLE_MODALITY_SWITCHER and name == "modality_list_adapters":
            from empirica.core.modality.register_adapters import get_registry
            
            registry = get_registry()
            adapters = registry.list_adapters()
            health_results = registry.health_check_all()
            
            for adapter in adapters:
                adapter['healthy'] = health_results.get(adapter['name'], False)
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "adapters": adapters
            }, indent=2))]

        elif ENABLE_MODALITY_SWITCHER and name == "modality_adapter_health":
            from empirica.core.modality.register_adapters import get_registry
            
            adapter_name = arguments.get("adapter_name")
            registry = get_registry()
            
            try:
                adapter = registry.get_adapter(adapter_name)
                healthy = adapter.health_check()
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "adapter": adapter_name,
                    "healthy": healthy
                }, indent=2))]
            except Exception as e:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": False,
                    "error": str(e)
                }, indent=2))]

        elif ENABLE_MODALITY_SWITCHER and name == "modality_decision_assist":
            from empirica.core.modality.modality_switcher import ModalitySwitcher, RoutingStrategy, RoutingPreferences
            
            query = arguments.get("query")
            epistemic_state = arguments.get("epistemic_state", {})
            context = arguments.get("context", {})
            
            switcher = ModalitySwitcher()
            decision = switcher.route_request(
                query=query,
                epistemic_state=epistemic_state,
                preferences=RoutingPreferences(strategy=RoutingStrategy.EPISTEMIC),
                context=context
            )
            
            return [types.TextContent(type="text", text=json.dumps({
                "ok": True,
                "selected_adapter": decision.selected_adapter,
                "confidence": decision.confidence,
                "rationale": decision.rationale,
                "estimated_cost": decision.estimated_cost,
                "estimated_latency": decision.estimated_latency,
                "fallback_adapters": decision.fallback_adapters
            }, indent=2))]
        
        # ===== PHASE 1.6: EPISTEMIC HANDOFF REPORTS =====
        
        elif name == "generate_handoff_report":
            from empirica.core.handoff import EpistemicHandoffReportGenerator, GitHandoffStorage, DatabaseHandoffStorage
            
            session_id_or_alias = arguments.get("session_id")
            try:
                session_id = resolve_session_id(session_id_or_alias)
            except ValueError as e:
                error_response = create_error_response(
                    "invalid_alias",
                    f"Session resolution failed: {str(e)}",
                    {"provided": session_id_or_alias}
                )
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
            task_summary = arguments.get("task_summary")
            key_findings = arguments.get("key_findings", [])
            remaining_unknowns = arguments.get("remaining_unknowns", [])
            next_session_context = arguments.get("next_session_context")
            artifacts_created = arguments.get("artifacts_created")
            
            try:
                # Generate report
                generator = EpistemicHandoffReportGenerator()
                report = generator.generate_handoff_report(
                    session_id=session_id,
                    task_summary=task_summary,
                    key_findings=key_findings,
                    remaining_unknowns=remaining_unknowns,
                    next_session_context=next_session_context,
                    artifacts_created=artifacts_created
                )
                
                # Store in both git and database
                git_storage = GitHandoffStorage()
                db_storage = DatabaseHandoffStorage()
                
                note_sha = git_storage.store_handoff(session_id, report)
                db_storage.store_handoff(session_id, report)
                
                # Estimate token count (4 chars per token rough estimate)
                token_count = len(report['compressed_json']) // 4
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "session_id": session_id,
                    "report_id": note_sha,
                    "storage_location": f"git:refs/notes/empirica/handoff/{session_id}",
                    "token_count": token_count,
                    "markdown": report['markdown']
                }, indent=2))]
            
            except Exception as e:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": False,
                    "error": str(e)
                }, indent=2))]
        
        elif name == "resume_previous_session":
            from empirica.core.handoff import GitHandoffStorage, DatabaseHandoffStorage
            from empirica.data.session_database import SessionDatabase
            
            ai_id = arguments.get("ai_id", "claude")
            resume_mode = arguments.get("resume_mode", "last")
            session_id = arguments.get("session_id")
            count = arguments.get("count", 1)
            detail_level = arguments.get("detail_level", "summary")
            
            try:
                db = SessionDatabase()
                git_storage = GitHandoffStorage()
                db_storage = DatabaseHandoffStorage()
                
                # Determine which session(s) to load
                if resume_mode == "last":
                    # Get most recent session for AI
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT session_id FROM sessions
                        WHERE ai_id = ?
                        ORDER BY start_time DESC
                        LIMIT 1
                    """, (ai_id,))
                    
                    row = cursor.fetchone()
                    sessions = [{'session_id': row[0]}] if row else []
                
                elif resume_mode == "last_n":
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT session_id FROM sessions
                        WHERE ai_id = ?
                        ORDER BY start_time DESC
                        LIMIT ?
                    """, (ai_id, min(count, 5)))
                    
                    sessions = [{'session_id': row[0]} for row in cursor.fetchall()]
                
                elif resume_mode == "session_id":
                    if not session_id:
                        raise ValueError("session_id required for 'session_id' mode")
                    sessions = [{'session_id': session_id}]
                
                else:
                    raise ValueError(f"Invalid resume_mode: {resume_mode}")
                
                if not sessions:
                    error_response = create_error_response(
                        "session_not_found",
                        f"No sessions found for ai_id={ai_id}",
                        {"ai_id": ai_id, "hint": "Create sessions first or check ai_id"}
                    )
                    return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
                
                # Load handoff reports
                results = []
                total_tokens = 0
                
                for session in sessions:
                    sid = session['session_id']
                    
                    # Try git first, fallback to database
                    handoff = git_storage.load_handoff(sid, format='json')
                    if not handoff:
                        db_handoff = db_storage.load_handoff(sid)
                        if db_handoff:
                            handoff = json.loads(db_handoff['compressed_json'])
                    
                    if not handoff:
                        continue
                    
                    # Build response based on detail level
                    result = {
                        'session_id': handoff.get('s', sid),
                        'ai_id': handoff.get('ai', ai_id),
                        'timestamp': handoff.get('ts'),
                        'task': handoff.get('task', ''),
                        'epistemic_deltas': handoff.get('deltas', {}),
                        'key_findings': handoff.get('findings', []),
                        'remaining_unknowns': handoff.get('unknowns', []),
                        'next_steps': handoff.get('recommend', []),
                        'calibration_status': handoff.get('cal', 'unknown')
                    }
                    
                    if detail_level in ['detailed', 'full']:
                        result['investigation_tools'] = handoff.get('tools', [])
                        result['artifacts_created'] = handoff.get('artifacts', [])
                    
                    if detail_level == 'full':
                        # Load full markdown
                        full = git_storage.load_handoff(sid, format='markdown')
                        if full:
                            result['full_markdown'] = full['markdown']
                        else:
                            db_handoff = db_storage.load_handoff(sid)
                            if db_handoff:
                                result['full_markdown'] = db_handoff['markdown']
                    
                    # Estimate tokens
                    token_estimate = len(json.dumps(result)) // 4
                    total_tokens += token_estimate
                    
                    results.append(result)
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "sessions": results,
                    "total_sessions": len(results),
                    "token_estimate": total_tokens,
                    "detail_level": detail_level
                }, indent=2))]
            
            except Exception as e:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": False,
                    "error": str(e)
                }, indent=2))]
        
        elif name == "query_handoff_reports":
            from empirica.core.handoff import DatabaseHandoffStorage
            import re
            
            ai_id = arguments.get("ai_id")
            since = arguments.get("since")
            task_pattern = arguments.get("task_pattern")
            limit = arguments.get("limit", 10)
            
            try:
                db_storage = DatabaseHandoffStorage()
                
                # Query database
                reports = db_storage.query_handoffs(
                    ai_id=ai_id,
                    since=since,
                    limit=limit
                )
                
                # Filter by task pattern if provided
                if task_pattern:
                    pattern = re.compile(task_pattern, re.IGNORECASE)
                    reports = [r for r in reports if pattern.search(r['task_summary'])]
                
                # Format results
                results = []
                for report in reports:
                    results.append({
                        'session_id': report['session_id'],
                        'ai_id': report['ai_id'],
                        'timestamp': report['timestamp'],
                        'task': report['task_summary'],
                        'key_findings': report['key_findings'],
                        'epistemic_growth': report['overall_confidence_delta']
                    })
                
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": True,
                    "reports": results,
                    "total_found": len(results)
                }, indent=2))]
            
            except Exception as e:
                return [types.TextContent(type="text", text=json.dumps({
                    "ok": False,
                    "error": str(e)
                }, indent=2))]
        
        else:
            return [types.TextContent(type="text", text=json.dumps({
                "ok": False,
                "error": f"Unknown tool: {name}"
            }, indent=2))]
    
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": str(e),
            "tool": name
        }, indent=2))]

def _format_session_summary(summary: dict, detail_level: str) -> str:
    """Format session summary as human-readable markdown"""
    from datetime import datetime
    
    session_id = summary['session_id']
    ai_id = summary['ai_id']
    start_time = summary['start_time']
    end_time = summary.get('end_time', 'In progress')
    
    # Calculate duration if session ended
    duration_str = "In progress"
    if end_time and end_time != 'In progress':
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration = end_dt - start_dt
            hours = duration.total_seconds() / 3600
            duration_str = f"{hours:.1f} hours"
        except:
            duration_str = "Unknown"
    
    # Build markdown
    md = f"""# Session Resume: {session_id}

**AI:** {ai_id}  
**Started:** {start_time}  
**Duration:** {duration_str}  
**Status:** {'✅ Completed' if end_time and end_time != 'In progress' else '🔄 In Progress'}

---

"""
    
    # Epistemic Delta (if available)
    if summary.get('epistemic_delta'):
        delta = summary['epistemic_delta']
        pre = summary.get('preflight', {})
        post = summary.get('postflight', {})
        
        md += "## What You Learned (Epistemic Delta)\n\n"
        
        if pre and post:
            md += "### PREFLIGHT → POSTFLIGHT\n\n"
            
            # Show significant changes
            significant = [(k, v) for k, v in delta.items() if abs(v) > 0.1]
            significant.sort(key=lambda x: abs(x[1]), reverse=True)
            
            for key, change in significant[:8]:  # Top 8 changes
                arrow = "📈" if change > 0 else "📉"
                pre_val = pre.get(key, 0.5)
                post_val = post.get(key, 0.5)
                md += f"- **{key}:** {pre_val:.2f} → {post_val:.2f} ({arrow} {change:+.2f})\n"
            
            # Calibration assessment
            know_up = delta.get('know', 0) > 0.1
            unc_down = delta.get('uncertainty', 0) < -0.1
            
            md += "\n**Calibration:** "
            if know_up and unc_down:
                md += "✅ Well-calibrated (confidence ↑ + uncertainty ↓)\n"
            elif know_up and not unc_down:
                md += "⚠️ Possibly overconfident (confidence ↑ but uncertainty unchanged)\n"
            else:
                md += "📊 Mixed signals - review individual vectors\n"
        
        md += "\n---\n\n"
    
    # Reflex Context (NEW - dashboard phases)
    if summary.get('reflex_context'):
        reflex = summary['reflex_context']
        md += f"## Dashboard Context (Reflex Frames)\n\n"
        md += f"**Found {reflex['frames_found']} workflow phase frames**\n\n"
        
        if reflex.get('phases'):
            md += "### Recent Phases:\n\n"
            for frame in reflex['phases']:
                phase_icon = {
                    "preflight": "🚦",
                    "check": "🔍",
                    "postflight": "🎯"
                }.get(frame.get('phase'), "📍")
                
                md += f"- {phase_icon} **{frame.get('phase', 'unknown').upper()}** "
                md += f"(confidence: {frame.get('overall_confidence', 0):.2f}) "
                md += f"→ {frame.get('recommended_action', 'unknown')}\n"
        
        md += "\n---\n\n"
    
    # Tasks/Cascades
    if summary.get('cascades'):
        md += "## Tasks Completed\n\n"
        cascades = summary['cascades']
        
        if isinstance(cascades[0], str):
            # Summary mode - just task names
            for i, task in enumerate(cascades, 1):
                md += f"{i}. {task}\n"
        else:
            # Detailed mode - full cascade objects
            for i, cascade in enumerate(cascades, 1):
                task = cascade.get('task', 'Unknown task')
                confidence = cascade.get('final_confidence', 0.0)
                md += f"{i}. {task} (confidence: {confidence:.2f})\n"
        
        md += "\n---\n\n"
    
    # Tools used (if detailed)
    if detail_level in ['detailed', 'full'] and summary.get('tools_used'):
        md += "## Investigation Tools Used\n\n"
        for tool in summary['tools_used']:
            md += f"- **{tool['tool']}**: {tool['count']} times\n"
        md += "\n---\n\n"
    
    # Full assessments (if requested)
    if detail_level == 'full':
        if summary.get('preflight'):
            md += "## PREFLIGHT Assessment (Full)\n\n```json\n"
            md += json.dumps(summary['preflight'], indent=2)
            md += "\n```\n\n"
        
        if summary.get('postflight'):
            md += "## POSTFLIGHT Assessment (Full)\n\n```json\n"
            md += json.dumps(summary['postflight'], indent=2)
            md += "\n```\n\n"
    
    md += "---\n\n**Resume from here if needed. Full context available in session database.**\n"
    
    return md

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
