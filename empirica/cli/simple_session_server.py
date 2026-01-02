"""
Simple Session Server - MVP for AI Collaboration

Provides stateful session management with HTTP API for remote AIs to:
- Execute commands in workspace
- Maintain session context
- Follow Empirica workflow phases
- Perform genuine epistemic self-assessment

Usage:
    uvicorn empirica.cli.simple_session_server:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

app = FastAPI(title="Empirica Session Server", version="1.0.0")


class SessionManager:
    """Manages stateful AI collaboration sessions"""
    
    def __init__(self):
        self.sessions = {}
        self.workspace_root = Path(__file__).parent.parent.parent
    
    def create(self, ai_id: str, task: str, workspace: Optional[str] = None) -> str:
        """Create new collaboration session"""
        sid = str(uuid.uuid4())[:8]
        
        self.sessions[sid] = {
            "id": sid,
            "ai_id": ai_id,
            "task": task,
            "workspace": workspace or str(self.workspace_root),
            "cwd": workspace or str(self.workspace_root / "docs"),
            "phase": "created",
            "epistemic": None,
            "history": [],
            "files_accessed": [],
            "files_modified": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
        
        return sid
    
    def execute_command(self, sid: str, cmd: str, args: dict) -> dict:
        """Execute command in session context"""
        if sid not in self.sessions:
            return {"error": f"Session {sid} not found"}
        
        session = self.sessions[sid]
        session["last_activity"] = datetime.now(timezone.utc).isoformat()
        
        # Route command
        if cmd == "list_files":
            result = self._list_files(session, args.get("path", "."))
        elif cmd == "read_file":
            result = self._read_file(session, args["path"])
        elif cmd == "move_file":
            result = self._move_file(session, args["from"], args["to"])
        elif cmd == "run_bash":
            result = self._run_bash(session, args["command"])
        elif cmd == "assess_preflight":
            result = self._prompt_assessment("preflight", session)
        elif cmd == "submit_assessment":
            result = self._store_assessment(session, args)
        elif cmd == "assess_readiness":
            result = self._prompt_assessment("check", session)
        elif cmd == "propose_plan":
            result = self._handle_plan_proposal(session, args)
        elif cmd == "get_guidance":
            result = self._get_guidance(session)
        else:
            result = {"error": f"Unknown command: {cmd}"}
        
        # Update session history
        session["history"].append({
            "cmd": cmd,
            "args": args,
            "result_type": "success" if "error" not in result else "error",
            "at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "result": result,
            "dashboard": self._dashboard(session)
        }
    
    def _list_files(self, session: dict, path: str) -> dict:
        """List files in directory"""
        try:
            full_path = Path(session["cwd"]) / path
            if not full_path.exists():
                return {"error": f"Path not found: {path}"}
            
            if full_path.is_file():
                return {"type": "file", "path": str(full_path)}
            
            files = []
            for item in full_path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "path": str(item)
                })
            
            session["files_accessed"].append(str(full_path))
            
            return {
                "path": str(full_path),
                "files": files,
                "count": len(files)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _read_file(self, session: dict, path: str) -> dict:
        """Read file content"""
        try:
            full_path = Path(session["cwd"]) / path
            if not full_path.exists():
                return {"error": f"File not found: {path}"}
            
            if not full_path.is_file():
                return {"error": f"Not a file: {path}"}
            
            content = full_path.read_text()
            session["files_accessed"].append(str(full_path))
            
            return {
                "path": str(full_path),
                "content": content,
                "lines": len(content.splitlines()),
                "size": len(content)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _move_file(self, session: dict, from_path: str, to_path: str) -> dict:
        """Move file"""
        # Check if in ACT phase
        if session["phase"] not in ["ready", "acting"]:
            return {
                "error": "Cannot move files yet",
                "reason": f"Current phase: {session['phase']}",
                "required_phase": "ready",
                "suggestion": "Complete preflight assessment first"
            }
        
        try:
            from_full = Path(session["cwd"]) / from_path
            to_full = Path(session["cwd"]) / to_path
            
            if not from_full.exists():
                return {"error": f"Source not found: {from_path}"}
            
            # Create destination directory if needed
            to_full.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            from_full.rename(to_full)
            
            session["files_modified"].append({
                "action": "move",
                "from": str(from_full),
                "to": str(to_full),
                "at": datetime.now(timezone.utc).isoformat()
            })
            
            return {
                "success": True,
                "from": str(from_full),
                "to": str(to_full)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _run_bash(self, session: dict, command: str) -> dict:
        """Run safe bash command"""
        # Whitelist of safe commands
        safe_commands = ["ls", "pwd", "cat", "head", "tail", "wc", "grep", "find"]
        
        cmd_parts = command.split()
        if not cmd_parts or cmd_parts[0] not in safe_commands:
            return {
                "error": "Command not allowed",
                "allowed": safe_commands
            }
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=session["cwd"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _prompt_assessment(self, phase: str, session: dict) -> dict:
        """Prompt AI for epistemic self-assessment"""
        prompts = {
            "preflight": """
Before starting this task, assess your epistemic state genuinely:

1. KNOW (0.0-1.0): How much do you understand about this task domain?
   - What do you know? What are you uncertain about?

2. DO (0.0-1.0): Can you execute this task effectively?
   - Do you have the necessary capabilities?

3. CONTEXT (0.0-1.0): Do you understand the environment/workspace?
   - Do you have enough information about the current state?

4. UNCERTAINTY (0.0-1.0): What is your overall uncertainty level?
   - What are you uncertain about? What could go wrong?

Respond with your genuine assessment using submit_assessment command.
            """,
            "check": """
Mid-task checkpoint: Assess your current state:

1. What have you learned since preflight?
2. Are you ready to proceed with execution?
3. What uncertainties remain?
4. Do you need more investigation?

Respond with submit_assessment command including your reasoning.
            """
        }
        
        session["phase"] = phase
        
        return {
            "phase": phase,
            "prompt": prompts.get(phase, "Assess your epistemic state"),
            "expects": "submit_assessment command with scores and rationale",
            "next_command": "submit_assessment"
        }
    
    def _store_assessment(self, session: dict, assessment: dict) -> dict:
        """Store epistemic assessment"""
        session["epistemic"] = {
            "know": assessment.get("know", 0.5),
            "do": assessment.get("do", 0.5),
            "context": assessment.get("context", 0.5),
            "uncertainty": assessment.get("uncertainty", 0.5),
            "rationale": assessment.get("rationale", ""),
            "assessed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update phase based on assessment
        if session["phase"] == "preflight":
            session["phase"] = "preflight_done"
        elif session["phase"] == "check":
            # Check if ready to proceed
            if session["epistemic"]["uncertainty"] < 0.5:
                session["phase"] = "ready"
            else:
                session["phase"] = "investigating"
        
        return {
            "success": True,
            "assessment_recorded": session["epistemic"],
            "phase_transition": session["phase"]
        }
    
    def _handle_plan_proposal(self, session: dict, args: dict) -> dict:
        """Handle plan proposal from AI"""
        plan = args.get("plan", "")
        
        session["proposed_plan"] = {
            "plan": plan,
            "proposed_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending_review"
        }
        
        return {
            "success": True,
            "message": "Plan received. Awaiting Sentinel review.",
            "plan": plan
        }
    
    def _get_guidance(self, session: dict) -> dict:
        """Get contextual guidance"""
        guidance = []
        
        if session["phase"] == "created":
            guidance.append("Start with assess_preflight to establish baseline")
        
        if session["epistemic"] and session["epistemic"]["uncertainty"] > 0.6:
            guidance.append("High uncertainty detected - investigate workspace first")
        
        if session["epistemic"] and session["epistemic"]["context"] < 0.4:
            guidance.append("Low context - read key documentation files")
        
        if not session["files_accessed"]:
            guidance.append("No files accessed yet - start with list_files")
        
        return {
            "guidance": guidance,
            "current_phase": session["phase"],
            "suggestion": guidance[0] if guidance else "Continue with current task"
        }
    
    def _dashboard(self, session: dict) -> dict:
        """Generate dashboard JSON"""
        return {
            "session": {
                "id": session["id"],
                "ai_id": session["ai_id"],
                "task": session["task"],
                "phase": session["phase"],
                "created_at": session["created_at"],
                "last_activity": session["last_activity"]
            },
            "workspace": {
                "cwd": session["cwd"],
                "files_accessed": len(session["files_accessed"]),
                "files_modified": len(session["files_modified"]),
                "recent_modifications": session["files_modified"][-5:]
            },
            "epistemic": session["epistemic"],
            "actions": {
                "available": self._get_available_actions(session),
                "recommended": self._get_recommended(session)
            },
            "history": session["history"][-5:],  # Last 5 commands
            "status": self._get_status_summary(session)
        }
    
    def _get_available_actions(self, session: dict) -> List[dict]:
        """Get phase-appropriate available actions"""
        actions = []
        
        # Always available
        actions.append({
            "id": "get_guidance",
            "desc": "Get contextual guidance",
            "args": {},
            "phase": "any"
        })
        
        # Phase-based actions
        if session["phase"] == "created":
            actions.append({
                "id": "assess_preflight",
                "desc": "Assess epistemic state before starting",
                "args": {},
                "required": True,
                "epistemic_impact": ["establishes baseline"]
            })
        
        elif session["phase"] in ["preflight_done", "investigating"]:
            actions.extend([
                {
                    "id": "list_files",
                    "desc": "List files in directory",
                    "args": {"path": "string (optional)"},
                    "epistemic_impact": ["increases CONTEXT", "reduces UNCERTAINTY"]
                },
                {
                    "id": "read_file",
                    "desc": "Read file content",
                    "args": {"path": "string (required)"},
                    "epistemic_impact": ["increases KNOW", "increases CONTEXT"]
                },
                {
                    "id": "run_bash",
                    "desc": "Run safe bash command",
                    "args": {"command": "string (required)"},
                    "allowed_commands": ["ls", "pwd", "cat", "head", "tail", "wc", "grep", "find"]
                },
                {
                    "id": "assess_readiness",
                    "desc": "Check if ready to proceed",
                    "args": {},
                    "recommended_when": "after investigation"
                },
                {
                    "id": "propose_plan",
                    "desc": "Propose action plan for review",
                    "args": {"plan": "string (required)"}
                }
            ])
        
        elif session["phase"] == "ready":
            actions.extend([
                {
                    "id": "move_file",
                    "desc": "Move file to new location",
                    "args": {"from": "string (required)", "to": "string (required)"},
                    "requires_preflight": True,
                    "phase": "act"
                },
                {
                    "id": "list_files",
                    "desc": "List files",
                    "args": {"path": "string (optional)"}
                },
                {
                    "id": "read_file",
                    "desc": "Read file",
                    "args": {"path": "string (required)"}
                }
            ])
        
        return actions
    
    def _get_recommended(self, session: dict) -> dict:
        """Get recommended next action"""
        if session["phase"] == "created":
            return {
                "action": "assess_preflight",
                "why": "Establish epistemic baseline before starting",
                "priority": "required"
            }
        
        elif session["phase"] == "preflight_done":
            if not session["files_accessed"]:
                return {
                    "action": "list_files",
                    "why": "High uncertainty - investigate workspace first",
                    "priority": "recommended"
                }
        
        elif session["epistemic"] and session["epistemic"]["uncertainty"] > 0.6:
            return {
                "action": "list_files",
                "why": f"High uncertainty ({session['epistemic']['uncertainty']:.2f}) - investigate more",
                "priority": "recommended"
            }
        
        elif session["epistemic"] and session["epistemic"]["uncertainty"] < 0.5 and session["phase"] == "investigating":
            return {
                "action": "propose_plan",
                "why": "Uncertainty lowered - ready to propose action plan",
                "priority": "suggested"
            }
        
        return {
            "action": None,
            "why": "Continue with current task",
            "priority": "none"
        }
    
    def _get_status_summary(self, session: dict) -> str:
        """Get human-readable status"""
        phase_status = {
            "created": "⏸️  Session created - awaiting preflight assessment",
            "preflight": "🔍 Performing preflight assessment",
            "preflight_done": "✅ Preflight complete - ready to investigate",
            "investigating": "🔎 Investigating workspace",
            "check": "🤔 Mid-task checkpoint",
            "ready": "✅ Ready to execute actions",
            "acting": "⚡ Executing actions"
        }
        
        return phase_status.get(session["phase"], f"Unknown phase: {session['phase']}")


# Global session manager
manager = SessionManager()


# Pydantic models
class SessionCreate(BaseModel):
    ai_id: str
    task: str
    workspace: Optional[str] = None


class CommandExecute(BaseModel):
    command: str
    args: Dict[str, Any] = {}


# API endpoints
@app.post("/sessions")
def create_session(req: SessionCreate):
    """Create new collaboration session"""
    sid = manager.create(req.ai_id, req.task, req.workspace)
    return {
        "session_id": sid,
        "dashboard": manager._dashboard(manager.sessions[sid]),
        "message": "Session created successfully"
    }


@app.post("/sessions/{session_id}/command")
def execute_command(session_id: str, req: CommandExecute):
    """Execute command in session context"""
    result = manager.execute_command(session_id, req.command, req.args)
    return result


@app.get("/sessions/{session_id}/dashboard")
def get_dashboard(session_id: str):
    """Get current session dashboard"""
    if session_id not in manager.sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return manager._dashboard(manager.sessions[session_id])


@app.get("/sessions")
def list_sessions():
    """List all active sessions"""
    return {
        "sessions": [
            {
                "id": sid,
                "ai_id": session["ai_id"],
                "task": session["task"],
                "phase": session["phase"],
                "created_at": session["created_at"]
            }
            for sid, session in manager.sessions.items()
        ],
        "count": len(manager.sessions)
    }


@app.get("/")
def root():
    """API info"""
    return {
        "name": "Empirica Session Server",
        "version": "1.0.0",
        "description": "Stateful session management for AI collaboration",
        "endpoints": {
            "POST /sessions": "Create new session",
            "POST /sessions/{id}/command": "Execute command",
            "GET /sessions/{id}/dashboard": "Get dashboard",
            "GET /sessions": "List all sessions"
        },
        "active_sessions": len(manager.sessions)
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Empirica Session Server...")
    print("📊 Dashboard: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
