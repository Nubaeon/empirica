"""
Chat Command Handler - Interactive multi-turn conversation for human users

Provides REPL-style chat interface with conversation history and model switching.
Integrated with UVL (Universal Visual Language) protocol for transparent AI communication.
Supports markdown rendering via glow for beautiful terminal output.
"""

import sys
import uuid
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from empirica.plugins.modality_switcher import ModalitySwitcher, RoutingStrategy, RoutingPreferences
from empirica.data.session_database import SessionDatabase
from ..cli_utils import handle_cli_error
from ..uvl_formatter import (
    format_uvl_response,
    format_routing_decision,
    format_uvl_stream_message,
    get_agent_emoji
)

# Set up logging for chat handler
logger = logging.getLogger(__name__)


def render_markdown(text: str, use_glow: bool = True) -> str:
    """
    Render markdown text with glow for beautiful terminal output.
    
    Args:
        text: Markdown text to render
        use_glow: Whether to use glow for rendering (requires glow installed)
    
    Returns:
        Rendered text (formatted if glow available, raw if not)
    """
    if not use_glow:
        return text
    
    try:
        # Check if glow is available
        result = subprocess.run(
            ['which', 'glow'],
            capture_output=True,
            timeout=2
        )
        
        if result.returncode != 0:
            # Glow not available, return plain text
            return text
        
        # Render with glow using stdin (no temp file needed)
        # Use -s for style, -w for width, and pipe directly
        result = subprocess.run(
            ['glow', '-s', 'dark', '-w', '80', '-'],
            input=text,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        else:
            return text
    
    except Exception:
        # Fall back to plain text
        return text


def handle_chat_command(args):
    """
    Handle 'empirica chat' command for interactive conversations.
    
    Provides REPL-style interface with:
    - Multi-turn conversation
    - Conversation history
    - Model switching during chat
    - Session persistence
    """
    try:
        # Initialize
        session_id = getattr(args, 'session', None)
        resume_session = getattr(args, 'resume', None)
        
        # Handle resume
        if resume_session:
            session_id = resume_session
            conversation_history = _load_chat_session(session_id)
            if not conversation_history:
                print("⚠️  Starting new session instead.")
                session_id = f"chat_{uuid.uuid4().hex}"  # Full UUID for unique identification
                conversation_history = []
        elif session_id:
            # Check if session exists
            conversation_history = _load_chat_session(session_id)
            if not conversation_history:
                conversation_history = []
        else:
            session_id = f"chat_{uuid.uuid4().hex}"  # Full UUID for unique identification
            conversation_history = []
        
        adapter = getattr(args, 'adapter', None)
        model = getattr(args, 'model', None)
        strategy_name = getattr(args, 'strategy', 'epistemic')
        show_uvl = getattr(args, 'show_uvl', True)  # UVL indicators (default: on)
        uvl_verbose = getattr(args, 'uvl_verbose', False)  # Detailed routing info
        uvl_stream = getattr(args, 'uvl_stream', False)  # Emit UVL JSON stream
        
        conversation_history: List[Dict[str, str]] = []
        # Setup UVL stream if enabled
        uvl_stream_path = None
        if uvl_stream:
            uvl_stream_dir = Path('.uvl_stream')
            uvl_stream_dir.mkdir(exist_ok=True)
            uvl_stream_path = uvl_stream_dir / f"{session_id}.jsonl"
        
        # Print welcome banner
        agent_emoji = get_agent_emoji(adapter) if adapter else '🔄'
        print("\n" + "=" * 70)
        print("🤖 Empirica Interactive Chat")
        print("=" * 70)
        print(f"📋 Session: {session_id}")
        if conversation_history:
            print(f"📜 Resumed: {len(conversation_history)} previous messages")
        print(f"🎯 Model: {model or adapter or f'auto ({strategy_name})'} {agent_emoji}")
        if show_uvl:
            print(f"📊 UVL Indicators: Enabled")
        if uvl_stream:
            print(f"📡 UVL Stream: {uvl_stream_path}")
        print("\nCommands:")
        print("  /switch <model>  - Switch to different model")
        print("  /strategy <name> - Change routing strategy")
        print("  /history         - Show conversation history")
        print("  /clear           - Clear conversation history")
        print("  /uvl on|off      - Toggle UVL indicators")
        print("  /sessions        - List all saved sessions")
        print("  /help            - Show this help")
        print("  exit or /quit    - End chat session")
        print("=" * 70 + "\n")
        
        # Initialize modality switcher
        switcher = ModalitySwitcher()
        
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', '/quit', 'quit']:
                    print("\n👋 Ending chat session. Goodbye!")
                    break
                
                if user_input.startswith('/'):
                    command_handled = _handle_chat_command(
                        user_input, 
                        conversation_history,
                        session_id,
                        switcher,
                        locals()  # Pass local vars for /uvl command
                    )
                    if command_handled:
                        continue
                
                # Add to conversation history
                conversation_history.append({
                    'role': 'user',
                    'content': user_input
                })
                
                # Show routing decision if UVL verbose
                if uvl_verbose and not adapter:
                    # Would need to expose candidate scores from switcher
                    # For now, just show simple routing
                    print(format_routing_decision(
                        task=user_input,
                        strategy=strategy_name,
                        selected_adapter=adapter or 'auto',
                        candidates={},  # TODO: Get from switcher
                        verbose=False
                    ))
                
                # Build context with conversation history
                context = {
                    'session_id': session_id,
                    'user_type': 'human',
                    'conversation_history': conversation_history[-10:]  # Last 10 exchanges
                }
                
                # Determine routing preferences
                if adapter:
                    preferences = RoutingPreferences(force_adapter=adapter)
                else:
                    strategy_map = {
                        'epistemic': RoutingStrategy.EPISTEMIC,
                        'cost': RoutingStrategy.COST,
                        'latency': RoutingStrategy.LATENCY,
                        'quality': RoutingStrategy.QUALITY,
                        'balanced': RoutingStrategy.BALANCED
                    }
                    preferences = RoutingPreferences(
                        strategy=strategy_map.get(strategy_name, RoutingStrategy.EPISTEMIC)
                    )
                
                # Execute query
                result = switcher.execute_with_routing(
                    query=user_input,
                    epistemic_state={},
                    preferences=preferences,
                    context={
                        'session_id': session_id,
                        'user_type': 'human',
                        'conversation_history': conversation_history[-10:],
                        'model': model  # Pass model as context
                    },
                    system="You are a helpful AI assistant in a conversational chat. Maintain context from previous messages.",
                    temperature=0.7,
                    max_tokens=2000
                )
                
                # Extract response text from AdapterResponse
                if hasattr(result, 'provider_meta') and 'response_full' in result.provider_meta:
                    content = result.provider_meta['response_full']
                elif hasattr(result, 'rationale'):
                    # Extract from rationale (format: "Provider: actual response...")
                    rationale = result.rationale
                    if ':' in rationale:
                        content = rationale.split(':', 1)[1].strip()
                    else:
                        content = rationale
                else:
                    content = str(result)
                
                # Add AI response to history
                conversation_history.append({
                    'role': 'assistant',
                    'content': content
                })
                
                # Display response with UVL formatting
                if show_uvl:
                    # Format with UVL indicators
                    formatted = format_uvl_response(content, result, show_vectors=True)
                    
                    # Debug: Show actual provider and model
                    if getattr(args, 'verbose', False):
                        provider = result.provider_meta.get('provider', 'unknown')
                        model = result.provider_meta.get('model', 'unknown')
                        print(f"\n[DEBUG] Provider: {provider}, Model: {model}")
                    
                    print(formatted)
                else:
                    # Check if response looks like markdown
                    has_markdown = any(marker in content for marker in ['**', '##', '```', '- ', '* ', '1. '])
                    
                    if has_markdown:
                        # Render markdown with glow
                        rendered = render_markdown(content, use_glow=True)
                        print(f"\nAI:\n{rendered}\n")
                    else:
                        # Plain text
                        print(f"\nAI: {content}\n")
                
                # Log to UVL stream if enabled
                if uvl_stream and uvl_stream_path:
                    uvl_message = format_uvl_stream_message(
                        event_type="ai_response",
                        agent_id=result.provider_meta.get('provider', 'unknown'),
                        content=content,
                        adapter_response=result,
                        session_id=session_id
                    )
                    with open(uvl_stream_path, 'a') as f:
                        f.write(json.dumps(uvl_message) + '\n')
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 End of input. Goodbye!")
                break
        
        # Save session on exit
        if getattr(args, 'save', True):
            _save_chat_session(session_id, conversation_history)
        
    except Exception as e:
        handle_cli_error(e, "Chat command", getattr(args, 'verbose', False))
        sys.exit(1)


def _handle_chat_command(command: str, history: List[Dict], session_id: str, switcher, local_vars: dict = None) -> bool:
    """
    Handle special chat commands (starting with /).
    Returns True if command was handled, False otherwise.
    """
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None
    
    if cmd == '/help':
        print("\n📖 Chat Commands:")
        print("  /switch <model>  - Switch to different model (e.g., /switch qwen)")
        print("  /strategy <name> - Change routing strategy (epistemic/cost/latency/quality)")
        print("  /history         - Show conversation history")
        print("  /clear           - Clear conversation history")
        print("  /uvl on|off      - Toggle UVL visual indicators")
        print("  /sessions        - List all saved sessions")
        print("  /help            - Show this help")
        print("  exit or /quit    - End chat session\n")
        return True
    
    elif cmd == '/uvl':
        if local_vars and arg:
            if arg.lower() == 'on':
                local_vars['show_uvl'] = True
                print("🟢 UVL indicators enabled\n")
            elif arg.lower() == 'off':
                local_vars['show_uvl'] = False
                print("⚫ UVL indicators disabled\n")
            else:
                print("❌ Usage: /uvl on|off\n")
        else:
            print("❌ Usage: /uvl on|off\n")
        return True
    
    elif cmd == '/sessions':
        _list_chat_sessions()
        return True
    
    elif cmd == '/switch':
        if not arg:
            print("❌ Usage: /switch <model_name>")
        else:
            # Model switching: update the local adapter variable
            if local_vars:
                local_vars['adapter'] = arg
                print(f"🔄 Switched to adapter: {arg}\n")
            else:
                print(f"⚠️  Model switching not supported in this context\n")
        return True
    
    elif cmd == '/strategy':
        if not arg:
            print("❌ Usage: /strategy <epistemic|cost|latency|quality|balanced>")
        else:
            print(f"🎯 Changed strategy to: {arg}")
        return True
    
    elif cmd == '/history':
        print(f"\n📜 Conversation History ({len(history)} messages):")
        print("=" * 70)
        for i, msg in enumerate(history, 1):
            role = "You" if msg['role'] == 'user' else "AI"
            content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"{i}. {role}: {content_preview}")
        print("=" * 70 + "\n")
        return True
    
    elif cmd == '/clear':
        history.clear()
        print("🗑️  Conversation history cleared.\n")
        return True
    
    return False


def _save_chat_session(session_id: str, history: List[Dict]):
    """Save chat session to database"""
    try:
        db = SessionDatabase()
        
        # Save conversation history as JSON in session metadata
        if len(history) > 0:
            # Create or get session
            try:
                db.create_session(session_id, ai_id='chat', started_at=None)
            except:
                pass  # Session already exists
            
            # Save conversation as JSON file
            from pathlib import Path
            import json
            from datetime import datetime, timezone
            
            chat_dir = Path('.empirica/chat_sessions')
            chat_dir.mkdir(parents=True, exist_ok=True)
            
            session_file = chat_dir / f"{session_id}.json"
            session_data = {
                'session_id': session_id,
                'created_at': datetime.now(timezone.utc).isoformat() + 'Z',
                'message_count': len(history),
                'conversation': history
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f"\n💾 Session saved: {session_id} ({len(history)} messages)")
            print(f"   Resume with: ./empirica-cli chat --resume {session_id}")
    except Exception as e:
        print(f"\n⚠️  Failed to save session: {e}")


def _load_chat_session(session_id: str) -> List[Dict]:
    """Load chat session from database"""
    try:
        from pathlib import Path
        import json
        
        chat_dir = Path('.empirica/chat_sessions')
        session_file = chat_dir / f"{session_id}.json"
        
        if not session_file.exists():
            print(f"❌ Session not found: {session_id}")
            return []
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        conversation = session_data.get('conversation', [])
        logger.info(f"Loaded session {session_id} with {len(conversation)} messages")
        print(f"✅ Loaded session: {session_id} ({len(conversation)} messages)")
        return conversation
    except Exception as e:
        logger.warning(f"Failed to load session: {e}")
        print(f"⚠️  Failed to load session: {e}")
        return []


def _list_chat_sessions():
    """List available chat sessions"""
    try:
        from pathlib import Path
        import json
        
        chat_dir = Path('.empirica/chat_sessions')
        if not chat_dir.exists():
            print("No saved chat sessions found.")
            return
        
        sessions = list(chat_dir.glob('*.json'))
        if not sessions:
            print("No saved chat sessions found.")
            return
        
        print("\n📋 Available Chat Sessions:")
        print("=" * 70)
        
        for session_file in sorted(sessions, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                session_id = data['session_id']
                created = data.get('created_at', 'unknown')
                msg_count = data.get('message_count', 0)
                
                # Show preview of first user message
                first_msg = next((m['content'][:50] for m in data.get('conversation', []) if m['role'] == 'user'), 'No messages')
                
                print(f"  {session_id}")
                print(f"    Created: {created}")
                print(f"    Messages: {msg_count}")
                print(f"    Preview: {first_msg}...")
                print()
            except Exception as e:
                continue
        
        print("=" * 70)
        print("Resume with: ./empirica-cli chat --resume <session_id>")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"⚠️  Failed to list sessions: {e}")
