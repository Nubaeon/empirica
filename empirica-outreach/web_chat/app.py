"""
Empirica Web Chat - Epistemic Agent Pipeline

Architecture:
- Scout Agent: Fast initial assessment (what does user need?)
- Search Agent: Memory retrieval (eidetic facts + episodic narratives)
- FactScorer: Confidence validation (is the response grounded?)
- Ollama: Fast response generation
- Claude CLI: Deep investigation (escalation path)

No API keys needed - uses your local auth + Empirica memory.
"""

import asyncio
import subprocess
import json
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx

app = FastAPI(title="Empirica Chat")

# Ollama config
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Investigation backend: "claude" or "empirica" or "ollama"
INVESTIGATION_BACKEND = os.getenv("INVESTIGATION_BACKEND", "claude")

# Project ID for memory retrieval
PROJECT_ID = os.getenv("EMPIRICA_PROJECT_ID", "ea2f33a4-d808-434b-b776-b7246bd6134a")


# ============== EPISTEMIC AGENT FUNCTIONS ==============

async def scout_assess(message: str) -> dict:
    """
    Scout Agent: Fast initial assessment.

    Determines:
    - Topic domain (what is this about?)
    - Complexity (simple/complex)
    - Action needed (answer/investigate/escalate)
    """
    # Quick keyword-based assessment (could be LLM-enhanced)
    message_lower = message.lower()

    # Domain detection
    domains = {
        "empirica": ["empirica", "cascade", "epistemic", "preflight", "postflight", "check"],
        "memory": ["memory", "eidetic", "episodic", "remember", "recall", "forget"],
        "ai": ["ai", "llm", "claude", "model", "agent", "vector"],
        "technical": ["code", "api", "error", "bug", "install", "config"],
    }

    detected_domain = "general"
    for domain, keywords in domains.items():
        if any(kw in message_lower for kw in keywords):
            detected_domain = domain
            break

    # Complexity detection
    complex_triggers = ["explain", "how does", "why", "analyze", "deep dive", "compare"]
    is_complex = any(t in message_lower for t in complex_triggers) or len(message) > 200

    # Action recommendation
    if is_complex:
        action = "investigate"
        confidence = 0.4
    elif "?" in message:
        action = "answer"
        confidence = 0.6
    else:
        action = "answer"
        confidence = 0.7

    return {
        "domain": detected_domain,
        "complexity": "complex" if is_complex else "simple",
        "action": action,
        "confidence": confidence,
        "keywords": [w for w in message_lower.split() if len(w) > 4][:5]
    }


async def search_memory(query: str, limit: int = 3) -> dict:
    """
    Search Agent: Retrieve relevant memories.

    Searches both eidetic (facts) and episodic (narratives) memory.
    """
    try:
        # Import here to avoid circular imports
        import sys
        sys.path.insert(0, "/home/yogapad/empirical-ai/empirica")
        from empirica.core.qdrant.vector_store import search_eidetic, search_episodic

        # Search eidetic (facts with confidence)
        eidetic_results = search_eidetic(
            project_id=PROJECT_ID,
            query=query,
            min_confidence=0.5,
            limit=limit
        )

        # Search episodic (past work narratives)
        episodic_results = search_episodic(
            project_id=PROJECT_ID,
            query=query,
            limit=limit
        )

        return {
            "ok": True,
            "eidetic": [
                {
                    "content": r.get("content", "")[:200],
                    "confidence": r.get("confidence", 0.5),
                    "domain": r.get("domain")
                }
                for r in eidetic_results
            ],
            "episodic": [
                {
                    "narrative": r.get("narrative", "")[:150],
                    "outcome": r.get("outcome"),
                    "session": r.get("session_id", "")[:8]
                }
                for r in episodic_results
            ],
            "has_context": bool(eidetic_results or episodic_results)
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "eidetic": [],
            "episodic": [],
            "has_context": False
        }


def format_memory_context(memory: dict) -> str:
    """Format memory results as context for LLM."""
    if not memory.get("has_context"):
        return ""

    parts = []

    if memory.get("eidetic"):
        parts.append("**Relevant Facts (from memory):**")
        for f in memory["eidetic"][:3]:
            conf = f.get("confidence", 0.5)
            parts.append(f"- [{conf:.0%}] {f['content'][:100]}...")

    if memory.get("episodic"):
        parts.append("\n**Past Work:**")
        for e in memory["episodic"][:2]:
            parts.append(f"- Session {e['session']}: {e['narrative'][:80]}...")

    return "\n".join(parts)


async def factscorer_validate(response: str, memory_context: str) -> dict:
    """
    FactScorer Agent: Validate response confidence.

    Checks if the response is grounded in memory or needs caveats.
    """
    # Simple heuristic scoring (could be LLM-enhanced)
    confidence = 0.5
    caveats = []

    # Boost if response aligns with memory
    if memory_context:
        confidence += 0.2

    # Check for hedging language (good epistemic practice)
    hedges = ["i think", "might be", "possibly", "not sure", "uncertain"]
    has_hedges = any(h in response.lower() for h in hedges)
    if has_hedges:
        confidence += 0.1  # Hedging is good epistemic practice

    # Check for overconfident language
    overconfident = ["definitely", "absolutely", "always", "never", "certainly"]
    is_overconfident = any(o in response.lower() for o in overconfident)
    if is_overconfident and not memory_context:
        confidence -= 0.2
        caveats.append("Response may be overconfident without memory grounding")

    # Determine moon phase
    if confidence >= 0.85:
        moon = "🌕"
    elif confidence >= 0.70:
        moon = "🌔"
    elif confidence >= 0.50:
        moon = "🌓"
    elif confidence >= 0.30:
        moon = "🌒"
    else:
        moon = "🌑"

    return {
        "confidence": min(1.0, max(0.0, confidence)),
        "moon": moon,
        "grounded": bool(memory_context),
        "caveats": caveats
    }


@dataclass
class ChatSession:
    """Tracks a web chat session."""
    session_id: str
    empirica_session_id: Optional[str] = None
    message_count: int = 0
    conversation: list = field(default_factory=list)
    moon_phase: str = "🌓"


# Active sessions
sessions: Dict[str, ChatSession] = {}


async def run_empirica(args: list) -> Optional[Dict]:
    """Run Empirica CLI command."""
    try:
        result = await asyncio.create_subprocess_exec(
            "empirica", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode == 0 and stdout:
            return json.loads(stdout.decode())
        return None
    except Exception as e:
        print(f"[Empirica] Error: {e}")
        return None


async def run_claude_investigation(task: str, session: ChatSession) -> str:
    """
    Run Claude CLI for deep investigation.
    No API key needed - uses your local auth!
    """
    try:
        # Build the investigation prompt
        prompt = f"""You are an epistemic investigation agent. Analyze this deeply and provide findings with honest uncertainty:

TASK: {task}

Instructions:
1. Break down what knowledge is needed
2. Identify what you DO know vs DON'T know
3. Be epistemically honest - say "I don't know" when uncertain
4. Format as bullet points"""

        # Call Claude CLI directly
        result = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt,
            "--output-format", "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate(timeout=60)

        if result.returncode == 0:
            findings = stdout.decode().strip()

            # Log to Empirica
            if session.empirica_session_id:
                await run_empirica([
                    "finding-log",
                    "--session-id", session.empirica_session_id,
                    "--finding", f"Claude investigation: {task[:50]}...",
                    "--impact", "0.7"
                ])

            return findings
        else:
            return f"Investigation failed: {stderr.decode()}"

    except asyncio.TimeoutError:
        return "Investigation timed out after 60s"
    except FileNotFoundError:
        return "Claude CLI not found. Install claude-code or use 'ollama' backend."
    except Exception as e:
        return f"Investigation error: {e}"


async def run_empirica_agent(task: str, session: ChatSession) -> str:
    """Run Empirica agent-spawn for investigation."""
    try:
        result = await run_empirica([
            "agent-spawn",
            "--session-id", session.empirica_session_id or "default",
            "--task", task,
            "--turtle",  # Auto-select best persona
            "--output", "json"
        ])

        if result and result.get("ok"):
            return result.get("findings", "Agent completed investigation.")
        return "Agent spawn completed."
    except Exception as e:
        return f"Agent error: {e}"


async def call_ollama(messages: list, system: str = None) -> str:
    """Call Ollama for fast responses."""
    try:
        # Build prompt
        prompt = ""
        if system:
            prompt = f"System: {system}\n\n"
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n\n"
        prompt += "Assistant:"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 1024}
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            return f"Ollama error: {response.status_code}"
    except Exception as e:
        return f"Ollama error: {e}"


async def should_investigate(message: str, session: ChatSession) -> tuple[bool, dict]:
    """
    Check with Empirica Sentinel if we should investigate.
    Returns (should_investigate, check_result)
    """
    if not session.empirica_session_id:
        return False, {}

    # Simple heuristic for now - could use actual CHECK gate
    know = 0.5 + (0.02 * min(session.message_count, 10))
    uncertainty = max(0.3, 0.7 - (0.03 * min(session.message_count, 10)))

    # Check for investigation triggers
    triggers = ["explain", "how does", "why", "investigate", "deep dive", "analyze"]
    needs_investigation = any(t in message.lower() for t in triggers)

    if needs_investigation:
        uncertainty += 0.2

    # Run CHECK gate
    check_data = {
        "session_id": session.empirica_session_id,
        "action_description": f"Respond to: {message[:100]}",
        "vectors": {
            "know": min(1.0, know),
            "uncertainty": min(1.0, uncertainty),
            "context": 0.5,
            "scope": 0.5
        },
        "reasoning": f"Web chat message {session.message_count}"
    }

    # For now, use heuristic. Could call actual check-submit
    should_inv = uncertainty > 0.6 or needs_investigation

    return should_inv, {"uncertainty": uncertainty, "know": know}


async def process_message(session: ChatSession, message: str) -> str:
    """
    Process a chat message with the Epistemic Agent Pipeline.

    Pipeline:
    1. Scout: Assess message (domain, complexity, action)
    2. Search: Retrieve relevant memory (eidetic facts + episodic narratives)
    3. Generate: Ollama response with memory context
    4. FactScorer: Validate confidence and add moon phase
    """
    session.message_count += 1
    session.conversation.append({"role": "user", "content": message})

    # === STEP 1: Scout Assessment ===
    scout_result = await scout_assess(message)
    domain = scout_result["domain"]
    action = scout_result["action"]

    # === STEP 2: Memory Retrieval ===
    memory = await search_memory(message)
    memory_context = format_memory_context(memory)

    # === STEP 3: Generate Response ===
    if action == "investigate" or scout_result["complexity"] == "complex":
        # Complex query - use investigation backend with memory context
        if INVESTIGATION_BACKEND == "claude":
            # Add memory context to investigation prompt
            context_note = f"\n\nRelevant context from memory:\n{memory_context}" if memory_context else ""
            response = await run_claude_investigation(message + context_note, session)
            prefix = "🔍 **Deep Investigation**\n\n"
        elif INVESTIGATION_BACKEND == "empirica":
            response = await run_empirica_agent(message, session)
            prefix = "🔍 **Epistemic Agent**\n\n"
        else:
            inv_prompt = f"Investigate deeply with epistemic honesty: {message}"
            if memory_context:
                inv_prompt += f"\n\nContext from memory:\n{memory_context}"
            response = await call_ollama([{"role": "user", "content": inv_prompt}])
            prefix = "🔍 **Investigation**\n\n"

        full_response = prefix + response
    else:
        # Simple query - fast Ollama path with memory context
        system = f"""You are Empirica Bot, an AI assistant focused on epistemic self-awareness.
Be helpful, concise, and honest about uncertainty. Say "I don't know" when unsure.

{memory_context if memory_context else "No relevant memories found for this query."}"""

        response = await call_ollama(session.conversation, system)
        full_response = response

    # === STEP 4: FactScorer Validation ===
    validation = await factscorer_validate(full_response, memory_context)
    session.moon_phase = validation["moon"]

    # Add moon phase and grounding indicator
    grounding_note = " 📚" if validation["grounded"] else ""
    full_response = f"{validation['moon']}{grounding_note} {full_response}"

    # Add caveats if any
    if validation.get("caveats"):
        full_response += f"\n\n⚠️ *{validation['caveats'][0]}*"

    session.conversation.append({"role": "assistant", "content": full_response})

    # Keep conversation history manageable
    if len(session.conversation) > 20:
        session.conversation = session.conversation[-20:]

    # Log to Empirica if we have a session
    if session.empirica_session_id and memory.get("has_context"):
        await run_empirica([
            "finding-log",
            "--session-id", session.empirica_session_id,
            "--finding", f"Chat query matched {len(memory.get('eidetic', []))} eidetic facts, {len(memory.get('episodic', []))} episodes",
            "--impact", "0.3"
        ])

    return full_response


# HTML Chat Interface
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Empirica Chat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        h1 {
            color: #fff;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #8892b0;
            margin-bottom: 20px;
            font-size: 0.9em;
        }
        .chat-container {
            width: 100%;
            max-width: 800px;
            background: #0d1117;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 70vh;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        .message {
            margin-bottom: 16px;
            padding: 12px 16px;
            border-radius: 8px;
            max-width: 85%;
            line-height: 1.5;
        }
        .user {
            background: #238636;
            color: white;
            margin-left: auto;
        }
        .assistant {
            background: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
        }
        .input-area {
            display: flex;
            padding: 16px;
            background: #161b22;
            border-top: 1px solid #30363d;
        }
        input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #30363d;
            border-radius: 6px;
            background: #0d1117;
            color: #c9d1d9;
            font-size: 16px;
        }
        input:focus {
            outline: none;
            border-color: #58a6ff;
        }
        button {
            margin-left: 12px;
            padding: 12px 24px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #2ea043; }
        button:disabled { background: #21262d; cursor: not-allowed; }
        .status {
            color: #8b949e;
            font-size: 12px;
            padding: 8px 16px;
            background: #161b22;
        }
        .typing {
            color: #58a6ff;
            font-style: italic;
        }
        pre {
            background: #161b22;
            padding: 8px;
            border-radius: 4px;
            overflow-x: auto;
        }
        code {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>🧠 Empirica Chat</h1>
    <p class="subtitle">Epistemic Agent Pipeline • Scout → Search (Memory) → Generate → FactScorer</p>

    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="message assistant">
                🌓 Hello! I'm Empirica Bot with <b>epistemic memory</b>.
                <br><br>
                I use a 4-stage pipeline:
                <br>• <b>Scout</b>: Assess your question
                <br>• <b>Search</b>: Retrieve relevant memories (📚 = memory-grounded)
                <br>• <b>Generate</b>: Create response with context
                <br>• <b>FactScorer</b>: Validate confidence (moon phase)
                <br><br>
                Try: "What is Empirica?" or "How do epistemic vectors work?"
            </div>
        </div>
        <div class="status" id="status">Connected • Ollama: llama3.1:8b • Investigation: Claude CLI</div>
        <div class="input-area">
            <input type="text" id="input" placeholder="Type a message..." autofocus>
            <button id="send">Send</button>
        </div>
    </div>

    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const messages = document.getElementById('messages');
        const input = document.getElementById('input');
        const sendBtn = document.getElementById('send');
        const status = document.getElementById('status');

        ws.onopen = () => {
            status.textContent = 'Connected • Ollama: llama3.1:8b • Investigation: Claude CLI';
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'response') {
                // Remove typing indicator
                const typing = document.querySelector('.typing');
                if (typing) typing.remove();

                addMessage(data.content, 'assistant');
                sendBtn.disabled = false;
                input.disabled = false;
                input.focus();
            } else if (data.type === 'typing') {
                const typing = document.createElement('div');
                typing.className = 'message assistant typing';
                typing.textContent = data.content;
                messages.appendChild(typing);
                messages.scrollTop = messages.scrollHeight;
            }
        };

        ws.onclose = () => {
            status.textContent = 'Disconnected';
        };

        function addMessage(content, role) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            // Basic markdown-like formatting
            content = content
                .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\n/g, '<br>')
                .replace(/`([^`]+)`/g, '<code>$1</code>');
            div.innerHTML = content;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        function send() {
            const text = input.value.trim();
            if (!text) return;

            addMessage(text, 'user');
            ws.send(JSON.stringify({ message: text }));
            input.value = '';
            sendBtn.disabled = true;
            input.disabled = true;
        }

        sendBtn.onclick = send;
        input.onkeypress = (e) => { if (e.key === 'Enter') send(); };
    </script>
</body>
</html>
"""


@app.get("/")
async def get_chat():
    return HTMLResponse(HTML_PAGE)


@app.get("/widget.js")
async def get_widget():
    """Serve the embeddable widget JavaScript."""
    import os
    widget_path = os.path.join(os.path.dirname(__file__), "widget.js")
    with open(widget_path, "r") as f:
        content = f.read()
    return HTMLResponse(content=content, media_type="application/javascript")


@app.get("/embed-demo")
async def get_embed_demo():
    """Serve the widget demo page."""
    import os
    demo_path = os.path.join(os.path.dirname(__file__), "embed-demo.html")
    with open(demo_path, "r") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Create session
    session_id = str(uuid.uuid4())
    session = ChatSession(session_id=session_id)

    # Create Empirica session
    result = await run_empirica([
        "session-create",
        "--ai-id", "web-chat",
        "--output", "json"
    ])
    if result and result.get("ok"):
        session.empirica_session_id = result.get("session_id")

    sessions[session_id] = session

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")

            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "content": "🔍 Thinking..." if "explain" in message.lower() or "how" in message.lower()
                          else "💭 Processing..."
            })

            # Process message
            response = await process_message(session, message)

            await websocket.send_json({
                "type": "response",
                "content": response
            })

    except WebSocketDisconnect:
        del sessions[session_id]


if __name__ == "__main__":
    import uvicorn
    print("[Empirica] Starting web chat...")
    print(f"[Empirica] Ollama: {OLLAMA_URL} model={OLLAMA_MODEL}")
    print(f"[Empirica] Investigation backend: {INVESTIGATION_BACKEND}")
    print("[Empirica] Open http://localhost:8080 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8080)
