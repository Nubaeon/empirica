# Empirica Modality Switching - Copilot CLI Integration Guide

**Date:** 2025-11-01  
**For:** Human users of Copilot CLI with Empirica MCP  
**Status:** Phase 0 - Foundation components ready

---

## What Is Modality Switching?

Modality switching allows Empirica to intelligently route AI requests between different providers (local LLMs, premium APIs like OpenAI/Anthropic, Copilot) based on:
- **Epistemic state** (confidence, uncertainty)
- **Budget constraints** (cost limits, quotas)
- **Provider availability** (fallback chains)
- **Task requirements** (speed vs quality tradeoffs)

---

## Current Implementation (Phase 0)

**Status:** Foundation components complete, MCP integration pending

**What's Ready:**
1. ✅ **Plugin Registry** - Discovers and validates provider adapters
2. ✅ **Usage Monitor** - Tracks costs and enforces budget limits
3. ✅ **Auth Manager** - Manages API keys and tokens (with Sentinel or env vars)
4. ✅ **Local Adapter** - Stub for testing (future: real local LLMs)

**What's Next:**
1. ⏳ **MCP Integration** - Wire into Empirica MCP server
2. ⏳ **Persona Enforcer** - Validate responses against schema
3. ⏳ **Test Harness** - Golden prompts and validation

---

## How to Access (When Complete)

### Via MCP Tools

Once integrated into the Empirica MCP server, you'll have access to tools like:

```
empirica_model_call
empirica_check_usage
empirica_list_providers
empirica_set_budget
```

### Via CLI (Future)

```bash
# Direct CLI usage (future implementation)
empirica model-call "Your query here" --provider auto
empirica usage summary
empirica providers list
```

---

## Architecture Overview

```
Your Copilot CLI Query
        ↓
┌─────────────────────────────┐
│   Empirica MCP Server       │
│   (empirica_mcp_server.py)  │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│   PersonaEnforcer           │
│   (validates responses)     │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│   ModalitySwitcher          │
│   (routing logic)           │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│   Plugin Registry           │ ← Phase 0: Complete!
│   (discovers adapters)      │
└─────────────────────────────┘
        ↓
    ┌───────┬─────────┬──────────┐
    │       │         │          │
    v       v         v          v
 Local   OpenAI  Anthropic  Copilot
Adapter  Adapter  Adapter   Adapter
```

---

## Provider Adapters (Phase 0-4 Rollout)

### Phase 0 (Current): Foundations
- ✅ Local adapter (stub)
- ✅ Plugin system
- ✅ Usage tracking
- ✅ Auth management

### Phase 1: Local + Stubs
- Local LLMs (Ollama, llama.cpp)
- Provider stubs (mock responses)

### Phase 2: REST Providers
- OpenAI (GPT-4, etc.)
- Anthropic (Claude)
- Qwen (via API)

### Phase 3: CLI Wrappers
- Gemini CLI
- Copilot CLI
- Qwen CLI

### Phase 4: Production
- Full monitoring
- Billing telemetry
- Web admin panel

---

## Budget Policies (Default)

**Local Tier** (Free)
- Unlimited calls
- $0 cost
- No quotas

**Non-Premium Tier** ($50/month)
- 200 calls/hour
- 2,000 calls/day
- $5/day limit
- $50/month limit

**Premium Tier** ($100/month)
- 50 calls/hour
- 200 calls/day
- $10/day limit
- $100/month limit

**Policy File:** `~/.empirica/usage_monitor.json`

---

## Testing Modality Switching (Phase 0)

### Run the Test Suite

```bash
cd /home/yogapad/empirical-ai/empirica
python3 tests/test_phase0_plugin_registry.py
```

**Expected Output:**
```
🧪 Testing Plugin Registry        ✅ PASSED
🧪 Testing Usage Monitor          ✅ PASSED
🧪 Testing Auth Manager           ✅ PASSED
🎉 ALL TESTS PASSED!
```

### Manual Testing with Python

```python
from empirica.core.modality.plugin_registry import PluginRegistry, AdapterPayload
from empirica.core.modality.usage_monitor import UsageMonitor
from empirica.core.modality.auth_manager import AuthManager

# Discover adapters
registry = PluginRegistry()
registry.discover_adapters("modality_switcher/adapters")
print(f"Found {len(registry.adapters)} adapters")

# Get an adapter
adapter = registry.get_adapter("local")

# Create a query payload
payload = AdapterPayload(
    system="You are a helpful assistant",
    state_summary="{}",
    user_query="What is the capital of France?",
    temperature=0.2,
    max_tokens=100
)

# Make a call
token_meta = adapter.authenticate({})
response = adapter.call(payload, token_meta)

print(f"Decision: {response.decision}")
print(f"Confidence: {response.confidence}")
print(f"Rationale: {response.rationale}")

# Check usage
monitor = UsageMonitor()
monitor.record_call("local", tokens_used=50, cost_usd=0.0, call_type="local")
summary = monitor.get_usage_summary("local")
print(f"Total calls: {summary['total_calls']}")
```

---

## Environment Variables (Auth Fallback)

When Sentinel is unavailable, AuthManager falls back to environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export QWEN_API_KEY="..."
export GITHUB_TOKEN="ghp_..."  # For Copilot
```

**Config File:** `~/.bashrc` or `~/.zshrc`

---

## Checking Your MCP Configuration

Your Empirica MCP server is configured at:
```
~/.copilot/mcp-config.json
```

**Current Config:**
```json
{
  "empirica": {
    "type": "local",
    "command": "python3",
    "args": [
      "empirica/mcp_local/empirica_mcp_server.py"
    ],
    "cwd": "/home/yogapad/empirical-ai",
    "tools": ["*"],
    "description": "Empirica AI Self-Awareness - 12-vector metacognition and uncertainty assessment"
  }
}
```

---

## Current Limitations (Phase 0)

1. **No MCP Integration Yet** - Components exist but not wired into MCP server
2. **Stub Adapters Only** - Local adapter returns mock responses
3. **No PersonaEnforcer** - Schema validation not yet integrated
4. **No Routing Logic** - ModalitySwitcher integration pending
5. **No Web UI** - TMUX TUI and web admin panel are Phase 2+

---

## Next Steps for Human Users

### When Phase 0 Completes:
1. Test MCP `/model_call` endpoint
2. Verify budget tracking
3. Try different providers (when Phase 1 adds them)

### When Phase 1 Completes:
1. Configure local LLM (Ollama)
2. Set budget policies
3. Test fallback chains

### When Phase 2 Completes:
1. Add API keys for premium providers
2. Monitor costs via usage endpoint
3. Configure provider preferences

---

## Troubleshooting

### "Adapter not found" Error
```bash
# List available adapters
python3 -c "
from empirica.core.modality.plugin_registry import PluginRegistry
reg = PluginRegistry()
reg.discover_adapters('modality_switcher/adapters')
print(reg.list_adapters())
"
```

### "Budget exceeded" Error
```bash
# Check usage
python3 -c "
from empirica.core.modality.usage_monitor import UsageMonitor
mon = UsageMonitor()
print(mon.get_usage_summary())
"

# Reset stop flag if needed
python3 -c "
from empirica.core.modality.usage_monitor import UsageMonitor
mon = UsageMonitor()
mon.reset_stop_flag('provider_name')
"
```

### "Authentication failed" Error
```bash
# Check if env vars are set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Check Sentinel status (future)
curl http://localhost:8765/health
```

---

## File Locations

**Core Components:**
```
empirica/core/modality/
├── __init__.py
├── plugin_registry.py   ← Adapter discovery
├── usage_monitor.py     ← Cost tracking
└── auth_manager.py      ← Token management
```

**Adapters:**
```
modality_switcher/adapters/
├── __init__.py
└── local_adapter.py     ← Phase 0 stub
```

**Tests:**
```
tests/
└── test_phase0_plugin_registry.py  ← Phase 0 validation
```

**State Files:**
```
~/.empirica/
├── usage_monitor.json   ← Usage tracking
└── vault.json.enc       ← Credentials (future)
```

---

## Getting Help

**Documentation:**
- `PHASE0_PROGRESS_2025_11_01.md` - Implementation status
- `modality_switcher/empirica_modality_extensibility_spec_2025-11-01.md` - Full spec
- `modality_switcher/empirica_modality_extensibility_phased_addendum_2025-11-01.md` - Roadmap

**Tests:**
- Run: `python3 tests/test_phase0_plugin_registry.py`
- Check: All tests should pass ✅

**Ask Claude:**
- "Show me the modality switching status"
- "How do I add a new provider adapter?"
- "What's my current usage?"

---

**Last Updated:** 2025-11-01  
**Phase:** 0 (Foundations) - 60% Complete  
**Next Milestone:** persona_test_harness implementation
