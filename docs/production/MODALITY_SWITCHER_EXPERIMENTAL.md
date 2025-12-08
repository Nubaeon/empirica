# Modality Switcher - Experimental Feature

**Status:** EXPERIMENTAL  
**Date:** 2025-12-08  
**Recommendation:** Use for research and testing only

---

## What is Modality Switcher?

The **Modality Switcher** is an experimental plugin that provides:
- Multi-adapter routing (7 adapters, 15+ models)
- Epistemic snapshot compression (95% compression, 94% fidelity)
- Domain-specific epistemic vectors
- Cross-AI context transfer

**Location:** `empirica/plugins/modality_switcher/`

---

## Why Experimental?

The modality switcher is marked as experimental because:

1. **Production alternatives exist:** For multi-AI orchestration, use **Cognitive Vault** (governance layer)
2. **Limited testing:** Not extensively tested in production environments
3. **API stability:** APIs may change in future versions
4. **Complex setup:** Requires multiple API keys and adapter configuration
5. **Research focus:** Designed for epistemic research, not production workflows

---

## Should You Use It?

### ✅ Good Use Cases:
- Research on epistemic routing strategies
- Testing different model capabilities on same tasks
- Experimenting with cross-AI context transfer
- Developing custom domain vectors

### ❌ Not Recommended For:
- Production deployments
- Mission-critical applications
- Team workflows requiring stability
- Users without experience with multiple AI APIs

---

## Core Empirica vs Modality Switcher

| Feature | Core Empirica | Modality Switcher |
|---------|---------------|-------------------|
| **Status** | Production-ready | Experimental |
| **CASCADE Workflow** | ✅ | ✅ |
| **Session Management** | ✅ | ✅ |
| **Goals & Subtasks** | ✅ | ✅ |
| **Multi-Model Routing** | ❌ | ✅ (experimental) |
| **Epistemic Snapshots** | ❌ | ✅ (experimental) |
| **Domain Vectors** | ❌ | ✅ (experimental) |
| **Stability** | High | Research-grade |
| **Support** | Full | Community |

---

## How to Enable

**Note:** Only enable if you're conducting research or experimentation.

### 1. Configuration

Create/edit `~/.empirica/config.yaml`:

```yaml
modality_switcher:
  enabled: true
  default_adapter: qwen
  routing_strategy: epistemic
  
adapters:
  qwen:
    enabled: true
    api_key: ${QWEN_API_KEY}
  gemini:
    enabled: true
    api_key: ${GEMINI_API_KEY}
  # ... other adapters
```

### 2. Environment Variables

```bash
export QWEN_API_KEY="your_key"
export GEMINI_API_KEY="your_key"
# ... other API keys
```

### 3. Usage

```bash
# CLI
empirica ask "Question" --adapter qwen --strategy epistemic

# Python API
from empirica.plugins.modality_switcher.modality_switcher import ModalitySwitcher

switcher = ModalitySwitcher()
response = switcher.route_query(
    query="Question",
    strategy="epistemic"
)
```

### 4. MCP Tools (4 experimental tools)

Available when modality switcher is enabled:

- `query_ai` - AI-to-AI communication
- `modality_route_query` - Route queries through modality switcher
- `modality_list_adapters` - List available adapters
- `modality_adapter_health` - Check adapter health

---

## Known Limitations

1. **API Rate Limits:** Each adapter has different rate limits
2. **Cost Tracking:** Usage monitoring is basic
3. **Error Handling:** Fallback behavior may be unpredictable
4. **Token Counting:** Different APIs count tokens differently
5. **Model Availability:** Some models may not be available in your region

---

## Documentation

- Plugin architecture: `empirica/plugins/modality_switcher/README.md`
- Adapter implementations: `empirica/plugins/modality_switcher/adapters/`
- Domain vectors: `empirica/plugins/modality_switcher/domain_vectors_custom/`

---

## Future Development

The modality switcher may be:
- Stabilized and promoted to core (if community demand exists)
- Replaced by a better architecture (e.g., Cognitive Vault)
- Deprecated entirely (if alternative solutions mature)

**Recommendation:** For production multi-AI orchestration, wait for **Cognitive Vault** (governance layer for multi-agent coordination).

---

## Reporting Issues

If you encounter issues with the modality switcher:

1. Check if the issue exists in core Empirica (without modality switcher)
2. If modality-specific, open a GitHub issue with `[EXPERIMENTAL]` tag
3. Include configuration, adapter used, and error messages

**Note:** Experimental features receive community support only.

---

## Alternatives

For production multi-AI workflows, consider:

1. **Single-model workflows:** Use core Empirica with one trusted model
2. **External orchestration:** Use LangChain, AutoGen, or similar frameworks
3. **Cognitive Vault:** Wait for official Empirica governance layer (coming soon)

---

**Status:** EXPERIMENTAL - Use at your own risk  
**Last Updated:** 2025-12-08
