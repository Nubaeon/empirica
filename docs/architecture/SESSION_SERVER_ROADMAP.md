# Empirica Stateful Session Server - Implementation Roadmap

**Date:** 2025-11-08  
**Status:** ✅ Phase 1 MVP Complete, Phase 2 In Progress  
**Current:** Testing MiniMax integration

---

## 🎯 What's Already Built (Phase 1 - Complete)

### ✅ **Simple Session Server** (`empirica/cli/simple_session_server.py`)
**Lines:** 565 (production-ready MVP)  
**Tech:** FastAPI + Python  
**Port:** 8001 (running)

**Features Implemented:**
1. ✅ Stateful session management
2. ✅ HTTP API endpoints
3. ✅ Phase-based workflow (PREFLIGHT → INVESTIGATE → CHECK → ACT)
4. ✅ Command routing with epistemic gating
5. ✅ Dashboard JSON protocol
6. ✅ Workspace file operations (list, read, move)
7. ✅ Safe bash command execution
8. ✅ Epistemic self-assessment prompts
9. ✅ Contextual guidance system
10. ✅ Session history tracking

**API Endpoints:**
```
GET  /                              # API info
POST /sessions                      # Create session
POST /sessions/{id}/command         # Execute command
GET  /sessions/{id}/dashboard       # Get dashboard
GET  /sessions                      # List sessions
GET  /docs                          # Swagger UI
```

**Current Test Status:**
- ✅ Server running on http://localhost:8001
- ✅ Sessions can be created
- ✅ Commands can be executed
- ✅ Dashboard JSON returns correctly
- 🔄 MiniMax integration in progress (response parsing issue)

---

## 📊 Phase-Based Command System (Implemented)

### Phase Flow:
```
created
  ↓ (assess_preflight required)
preflight → preflight_done
  ↓ (investigation commands available)
investigating
  ↓ (assess_readiness)
check → ready
  ↓ (action commands unlocked)
acting
```

### Available Commands by Phase:

**Phase: `created`**
- ✅ `get_guidance` - Get contextual help
- ✅ `assess_preflight` - Required first step

**Phase: `preflight_done` / `investigating`**
- ✅ `list_files` - List directory contents
- ✅ `read_file` - Read file content
- ✅ `run_bash` - Safe bash commands (ls, pwd, cat, head, tail, wc, grep, find)
- ✅ `assess_readiness` - Check if ready to act
- ✅ `propose_plan` - Submit action plan
- ✅ `get_guidance` - Contextual help

**Phase: `ready` / `acting`**
- ✅ `move_file` - Move/rename files
- ✅ `list_files` - Continue investigation
- ✅ `read_file` - Continue investigation

---

## 🎨 Dashboard JSON Structure (Implemented)

```json
{
  "session": {
    "id": "abc12345",
    "ai_id": "minimax",
    "task": "organize docs",
    "phase": "investigating",
    "created_at": "2025-11-08T15:00:00",
    "last_activity": "2025-11-08T15:05:00"
  },
  "workspace": {
    "cwd": "/path/to/empirica/docs",
    "files_accessed": 12,
    "files_modified": 3,
    "recent_modifications": [
      {"action": "move", "from": "...", "to": "...", "at": "..."}
    ]
  },
  "epistemic": {
    "know": 0.4,
    "do": 0.7,
    "context": 0.3,
    "uncertainty": 0.6,
    "rationale": "...",
    "assessed_at": "2025-11-08T15:02:00"
  },
  "actions": {
    "available": [
      {
        "id": "list_files",
        "desc": "List files in directory",
        "args": {"path": "string (optional)"},
        "epistemic_impact": ["increases CONTEXT", "reduces UNCERTAINTY"]
      }
    ],
    "recommended": {
      "action": "list_files",
      "why": "High uncertainty - investigate workspace first",
      "priority": "recommended"
    }
  },
  "history": [
    {"cmd": "assess_preflight", "args": {}, "result_type": "success", "at": "..."}
  ],
  "status": "🔎 Investigating workspace"
}
```

**Key Features:**
- ✅ **Epistemic impact annotations** - Each action shows which vectors it affects
- ✅ **Phase-aware recommendations** - Suggests next action based on state
- ✅ **Priority levels** - required / recommended / suggested / none
- ✅ **Human-readable status** - Emoji + description

---

## 🔧 What's Working

### Session Management:
```python
# Create session
POST /sessions
{
  "ai_id": "minimax",
  "task": "organize docs folder"
}
→ Returns: session_id + dashboard

# Execute command
POST /sessions/{session_id}/command
{
  "command": "list_files",
  "args": {"path": "."}
}
→ Returns: result + updated dashboard
```

### Epistemic Assessment Flow:
```python
# 1. Initiate preflight
POST /sessions/{id}/command
{"command": "assess_preflight"}
→ Returns: prompt for AI to self-assess

# 2. AI submits assessment
POST /sessions/{id}/command
{
  "command": "submit_assessment",
  "args": {
    "know": 0.4,
    "do": 0.7,
    "context": 0.3,
    "uncertainty": 0.6,
    "rationale": "..."
  }
}
→ Session phase transitions to "preflight_done"
→ Investigation commands now available
```

### Safety Features:
- ✅ **Phase gating** - Can't move files without preflight assessment
- ✅ **Command whitelisting** - Only safe bash commands allowed
- ✅ **Path sandboxing** - All operations within workspace
- ✅ **Error handling** - Clear error messages with suggestions

---

## 🚧 Phase 2: What Needs to Be Built

### Priority 1: Fix MiniMax Integration (Immediate)
**Issue:** MiniMax responses not parsing correctly  
**Current:** Response object structure unclear  
**Need:**
1. Debug response parsing in adapter
2. Extract JSON from MiniMax response
3. Submit epistemic assessment to server
4. Complete full workflow test

**Files to Update:**
- `empirica/plugins/modality_switcher/adapter_minimax.py` - Fix response parsing
- Test script for full flow

**Estimated Time:** 1-2 hours

---

### Priority 2: Context Manager API (High Value)
**Goal:** Clean Python interface for session management

**What to Build:**
```python
# empirica/session_client.py
from contextlib import contextmanager

class EmpricaSession:
    def __init__(self, ai_id: str, task: str, server_url: str = "http://localhost:8001"):
        self.ai_id = ai_id
        self.task = task
        self.server_url = server_url
        self.session_id = None
    
    def __enter__(self):
        # Create session on server
        response = requests.post(f"{self.server_url}/sessions", json={
            "ai_id": self.ai_id,
            "task": self.task
        })
        self.session_id = response.json()["session_id"]
        return self
    
    def __exit__(self, *args):
        # Optional: cleanup
        pass
    
    def execute(self, command: str, **args):
        """Execute command in session"""
        response = requests.post(
            f"{self.server_url}/sessions/{self.session_id}/command",
            json={"command": command, "args": args}
        )
        return response.json()
    
    def dashboard(self):
        """Get current dashboard"""
        response = requests.get(
            f"{self.server_url}/sessions/{self.session_id}/dashboard"
        )
        return response.json()

# Usage:
with EmpricaSession(ai_id="minimax", task="docs cleanup") as session:
    # Preflight
    session.execute("assess_preflight")
    session.execute("submit_assessment", know=0.4, do=0.7, context=0.3, uncertainty=0.6)
    
    # Investigate
    files = session.execute("list_files", path=".")
    
    # Act
    session.execute("move_file", from_path="old.md", to_path="new.md")
    
    # Dashboard
    print(session.dashboard())
```

**Estimated Time:** 2 hours

---

### Priority 3: WebSocket Support (For Real-Time Collaboration)
**Goal:** Bi-directional real-time communication (Sentinel ↔ Worker AI)

**What to Build:**
```python
# Add to simple_session_server.py

from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

ws_manager = ConnectionManager()

@app.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            # Receive command from AI
            data = await websocket.receive_json()
            
            # Execute command
            result = manager.execute_command(
                session_id,
                data["command"],
                data.get("args", {})
            )
            
            # Send result back
            await websocket.send_json(result)
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
```

**Use Case:**
- Sentinel (Claude) monitors MiniMax session in real-time
- Can send guidance/interrupt commands
- See live dashboard updates
- Collaborative debugging

**Estimated Time:** 2-3 hours

---

### Priority 4: Session Persistence (For Long-Running Tasks)
**Goal:** Save/resume sessions across server restarts

**What to Build:**
```python
# Add to SessionManager class

import sqlite3
from pathlib import Path

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.workspace_root = Path(__file__).parent.parent.parent
        self.db_path = self.workspace_root / ".empirica" / "sessions" / "sessions.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                ai_id TEXT,
                task TEXT,
                phase TEXT,
                epistemic JSON,
                history JSON,
                created_at TEXT,
                last_activity TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _save_session(self, session_id: str):
        """Persist session to database"""
        session = self.sessions[session_id]
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["id"],
            session["ai_id"],
            session["task"],
            session["phase"],
            json.dumps(session["epistemic"]),
            json.dumps(session["history"]),
            session["created_at"],
            session["last_activity"]
        ))
        conn.commit()
        conn.close()
    
    def _load_session(self, session_id: str):
        """Load session from database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Reconstruct session dict
            pass
    
    def resume_session(self, session_id: str):
        """Resume a saved session"""
        self._load_session(session_id)
        return self.sessions[session_id]
```

**Estimated Time:** 2 hours

---

### Priority 5: TUI Monitor (For Humans Watching)
**Goal:** Terminal UI for monitoring session in real-time

**What to Build:**
```python
# empirica/cli/session_monitor.py

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
import requests
import time

def monitor_session(session_id: str, server_url: str = "http://localhost:8001"):
    """Monitor session with live TUI"""
    console = Console()
    
    with Live(console=console, refresh_per_second=2) as live:
        while True:
            # Fetch dashboard
            response = requests.get(f"{server_url}/sessions/{session_id}/dashboard")
            dashboard = response.json()
            
            # Create layout
            layout = create_layout(dashboard)
            live.update(layout)
            
            time.sleep(0.5)

def create_layout(dashboard):
    """Create rich layout from dashboard"""
    # Session info panel
    session_info = Panel(
        f"[bold]{dashboard['session']['task']}[/bold]\n"
        f"AI: {dashboard['session']['ai_id']}\n"
        f"Phase: {dashboard['session']['phase']}\n"
        f"Status: {dashboard['status']}",
        title="Session Info"
    )
    
    # Epistemic state table
    if dashboard['epistemic']:
        epistemic_table = Table(title="Epistemic State")
        epistemic_table.add_column("Vector")
        epistemic_table.add_column("Score")
        
        for key, value in dashboard['epistemic'].items():
            if key != 'rationale' and key != 'assessed_at':
                epistemic_table.add_row(key.upper(), f"{value:.2f}")
    
    # Command history
    history_table = Table(title="Recent Commands")
    history_table.add_column("Command")
    history_table.add_column("Status")
    history_table.add_column("Time")
    
    for cmd in dashboard['history']:
        history_table.add_row(
            cmd['cmd'],
            cmd['result_type'],
            cmd['at'][-8:]  # Just time
        )
    
    # Combine all
    return Panel.fit(
        f"{session_info}\n{epistemic_table}\n{history_table}"
    )

# CLI command:
# python -m empirica.cli.session_monitor abc12345
```

**Estimated Time:** 3 hours

---

### Priority 6: Enhanced Command Set
**Goal:** Add more useful commands for AI collaboration

**Commands to Add:**
```python
# In SessionManager class

def _search_files(self, session: dict, pattern: str) -> dict:
    """Search for files matching pattern"""
    # Use glob or ripgrep
    pass

def _search_content(self, session: dict, query: str, path: str) -> dict:
    """Search file contents"""
    # Use grep or ripgrep
    pass

def _create_file(self, session: dict, path: str, content: str) -> dict:
    """Create new file"""
    # Check phase gating
    pass

def _edit_file(self, session: dict, path: str, changes: dict) -> dict:
    """Edit file content"""
    # Check phase gating
    # Support line-based edits
    pass

def _git_status(self, session: dict) -> dict:
    """Get git status"""
    pass

def _git_diff(self, session: dict, path: str = None) -> dict:
    """Show git diff"""
    pass
```

**Estimated Time:** 4 hours

---

### Priority 7: Sentinel Dashboard (AI Oversight)
**Goal:** Dedicated interface for Sentinel (Claude) to monitor workers

**What to Build:**
```python
# empirica/cli/sentinel_dashboard.py

class SentinelDashboard:
    """Dashboard for Sentinel to monitor multiple AI workers"""
    
    def __init__(self, server_url: str = "http://localhost:8001"):
        self.server_url = server_url
        self.active_sessions = {}
    
    def list_active_sessions(self):
        """Get all active sessions"""
        response = requests.get(f"{self.server_url}/sessions")
        return response.json()
    
    def watch_session(self, session_id: str):
        """Watch specific session"""
        # WebSocket connection for real-time updates
        pass
    
    def send_guidance(self, session_id: str, message: str):
        """Send guidance to worker AI"""
        # POST to special guidance endpoint
        pass
    
    def intervene(self, session_id: str, action: str):
        """Intervene in worker's execution"""
        # Pause/resume/stop session
        pass
    
    def review_plan(self, session_id: str) -> dict:
        """Review proposed plan from worker"""
        # Get proposed plan
        # Approve/reject/modify
        pass
```

**Features:**
- Monitor multiple MiniMax/Qwen instances simultaneously
- Real-time epistemic state tracking
- Guidance messaging
- Plan review/approval workflow
- Intervention controls

**Estimated Time:** 5 hours

---

## 📋 Complete Implementation Roadmap

### ✅ Phase 1: MVP (Complete) - 2 hours
- [x] Stateful session manager
- [x] HTTP API endpoints
- [x] Phase-based command gating
- [x] Dashboard JSON protocol
- [x] Basic file operations
- [x] Epistemic assessment prompts

### 🔄 Phase 2: Integration & Polish (In Progress) - 6 hours
- [ ] Fix MiniMax response parsing (1-2 hours) **← CURRENT**
- [ ] Context manager API (2 hours)
- [ ] WebSocket support (2-3 hours)
- [ ] Session persistence (2 hours)

### 📊 Phase 3: Monitoring & UX - 8 hours
- [ ] TUI monitor (3 hours)
- [ ] Enhanced command set (4 hours)
- [ ] Error recovery patterns (1 hour)

### 🎯 Phase 4: Sentinel Features - 10 hours
- [ ] Sentinel dashboard (5 hours)
- [ ] Multi-AI coordination (3 hours)
- [ ] Plan review workflow (2 hours)

### 🚀 Phase 5: Advanced Features - 12 hours
- [ ] Calibration analytics (4 hours)
- [ ] Session replay (3 hours)
- [ ] Visual dashboard (optional) (5 hours)

**Total Estimated Time:** ~38 hours from current state

---

## 🎯 Immediate Next Steps (Priority Order)

### 1. **Fix MiniMax Integration** (1-2 hours)
**Blocker:** Must complete this before other features work

**Tasks:**
- [ ] Debug response parsing in adapter
- [ ] Extract JSON from nested response structure
- [ ] Test full assessment submission
- [ ] Validate command execution loop

**Success Criteria:**
- MiniMax can complete preflight assessment
- Assessment is stored in session
- MiniMax can list files
- Full workflow (PREFLIGHT → INVESTIGATE → ACT) works

---

### 2. **Context Manager API** (2 hours)
**Value:** Makes integration much easier

**File:** `empirica/session_client.py`

**Success Criteria:**
- Clean `with` statement usage
- Single import for all session operations
- Works with both local and remote AIs

---

### 3. **WebSocket + Sentinel Dashboard** (5 hours)
**Value:** Enables real-time oversight

**Success Criteria:**
- Claude can monitor MiniMax in real-time
- Can send guidance messages
- See live epistemic updates

---

## 💡 Design Patterns Successfully Implemented

### 1. **Phase-Based State Machine**
```
created → preflight → investigating → check → ready → acting
```
- Commands gated by phase
- Automatic phase transitions
- Clear state progression

### 2. **Dashboard as Protocol**
```json
{
  "actions": {
    "available": [...],
    "recommended": {...}
  }
}
```
- AI reads JSON, not visual UI
- Self-documenting (includes args, epistemic impact)
- Guidance built-in

### 3. **Epistemic Annotations**
```json
{
  "id": "list_files",
  "epistemic_impact": ["increases CONTEXT", "reduces UNCERTAINTY"]
}
```
- Each action shows what it affects
- Helps AI decide what to do next
- Transparent reasoning

### 4. **Safety by Design**
- Phase gating (can't ACT without PREFLIGHT)
- Command whitelisting
- Explicit error messages with suggestions
- Workspace sandboxing

---

## 📊 Success Metrics

### Phase 2 Complete When:
- ✅ MiniMax completes full workflow independently
- ✅ Context manager API working
- ✅ WebSocket real-time updates functional
- ✅ Sessions persist across restarts

### Phase 3 Complete When:
- ✅ TUI monitor shows live updates
- ✅ Enhanced command set available
- ✅ Error recovery tested

### Phase 4 Complete When:
- ✅ Claude can monitor multiple AIs
- ✅ Plan review workflow tested
- ✅ Multi-AI coordination working

---

## 🎉 What We've Achieved

**In 2 hours, we built:**
- ✅ Full stateful session server
- ✅ Phase-based workflow enforcement
- ✅ Dashboard JSON protocol
- ✅ Epistemic self-assessment framework
- ✅ Command routing with safety
- ✅ API with OpenAPI docs

**This is production-ready MVP!**

**What's unique:**
- First stateful CLI for remote AI collaboration
- Epistemic assessment as first-class feature
- Dashboard designed for AI consumption
- Phase-based workflow enforcement

**Next:** Fix MiniMax integration and we're fully operational! 🚀

---

**Document Status:** ✅ Complete  
**Last Updated:** 2025-11-08 16:10 UTC  
**Next Review:** After MiniMax integration fix
