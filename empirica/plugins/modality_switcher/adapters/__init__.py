"""
Empirica Modality Adapters

Available adapters:
- QwenAdapter: Local Qwen CLI adapter
- MinimaxAdapter: MiniMax-M2 API adapter (Anthropic SDK)
- RovodevAdapter: Atlassian Rovo Dev CLI adapter (20M FREE tokens/day!)
- GeminiAdapter: Google Gemini CLI adapter ✨ NEW
- QodoAdapter: Qodo CLI adapter ✨ NEW
- OpenRouterAdapter: OpenRouter multi-model API adapter ✨ NEW
"""

from .qwen_adapter import QwenAdapter, ADAPTER_METADATA as QWEN_METADATA
from .minimax_adapter import MinimaxAdapter, ADAPTER_METADATA as MINIMAX_METADATA
from .rovodev_adapter import RovodevAdapter, ADAPTER_METADATA as ROVODEV_METADATA
from .gemini_adapter import GeminiAdapter, ADAPTER_METADATA as GEMINI_METADATA
from .qodo_adapter import QodoAdapter, ADAPTER_METADATA as QODO_METADATA
from .openrouter_adapter import OpenRouterAdapter, ADAPTER_METADATA as OPENROUTER_METADATA
from .copilot_adapter import CopilotAdapter, ADAPTER_METADATA as COPILOT_METADATA

__all__ = [
    'QwenAdapter',
    'MinimaxAdapter',
    'RovodevAdapter',
    'GeminiAdapter',
    'QodoAdapter',
    'OpenRouterAdapter',
    'CopilotAdapter',
    'QWEN_METADATA',
    'MINIMAX_METADATA',
    'ROVODEV_METADATA',
    'GEMINI_METADATA',
    'QODO_METADATA',
    'OPENROUTER_METADATA',
    'COPILOT_METADATA',
]
