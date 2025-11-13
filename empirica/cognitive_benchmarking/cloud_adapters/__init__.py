"""
Cloud API Adapters for Cognitive Benchmarking

Enables ERB benchmarking on cloud models:
- Anthropic (Claude)
- OpenAI (GPT)
- Google (Gemini)
- xAI (Grok)
- Others via OpenRouter

Version: 1.0.0
"""

from .anthropic_adapter import AnthropicAdapter
from .openai_adapter import OpenAIAdapter
from .google_adapter import GoogleAdapter
from .xai_adapter import XAIAdapter
from .openrouter_adapter import OpenRouterAdapter

__all__ = [
    'AnthropicAdapter',
    'OpenAIAdapter',
    'GoogleAdapter',
    'XAIAdapter',
    'OpenRouterAdapter',
]
