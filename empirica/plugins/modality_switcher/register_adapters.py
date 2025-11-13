#!/usr/bin/env python3
"""
Adapter Registration Module

Centralized adapter registration for Empirica modality switching.
Registers all available adapters in the PluginRegistry.

Usage:
    from empirica.plugins.modality_switcher.register_adapters import get_registry
    
    registry = get_registry()
    adapter = registry.get_adapter('minimax')
"""

import sys
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from empirica.plugins.modality_switcher.plugin_registry import PluginRegistry

logger = logging.getLogger(__name__)

# Global registry instance
_registry = None


def get_registry(force_reload: bool = False) -> PluginRegistry:
    """
    Get or create the global plugin registry with all adapters registered.
    
    Args:
        force_reload: If True, recreate registry even if it exists
        
    Returns:
        PluginRegistry with all adapters registered
    """
    global _registry
    
    if _registry is None or force_reload:
        _registry = create_registry()
    
    return _registry


def create_registry() -> PluginRegistry:
    """
    Create a new PluginRegistry and register all available adapters.
    
    Returns:
        PluginRegistry with adapters registered
    """
    registry = PluginRegistry()
    
    logger.info("📝 Registering adapters...")
    
    # Register MiniMax adapter
    try:
        from empirica.plugins.modality_switcher.adapters import MinimaxAdapter, MINIMAX_METADATA
        registry.register('minimax', MinimaxAdapter, MINIMAX_METADATA)
        logger.info("   ✅ MiniMax adapter registered")
    except ImportError as e:
        logger.warning(f"   ⚠️  MiniMax adapter not available: {e}")
    except Exception as e:
        logger.error(f"   ❌ MiniMax registration failed: {e}")
    
    # Register Qwen adapter
    try:
        from empirica.plugins.modality_switcher.adapters.qwen_adapter import QwenAdapter, ADAPTER_METADATA as QWEN_METADATA
        registry.register('qwen', QwenAdapter, QWEN_METADATA)
        logger.info("   ✅ Qwen adapter registered")
    except ImportError as e:
        logger.warning(f"   ⚠️  Qwen adapter not available: {e}")
    except Exception as e:
        logger.error(f"   ❌ Qwen registration failed: {e}")
    
    # Register Rovodev adapter
    try:
        from empirica.plugins.modality_switcher.adapters.rovodev_adapter import RovodevAdapter, ADAPTER_METADATA as ROVODEV_METADATA
        registry.register('rovodev', RovodevAdapter, ROVODEV_METADATA)
        logger.info("   ✅ Rovodev adapter registered")
    except ImportError as e:
        logger.warning(f"   ⚠️  Rovodev adapter not available: {e}")
    except Exception as e:
        logger.error(f"   ❌ Rovodev registration failed: {e}")
    
    # Register Gemini adapter
    try:
        from empirica.plugins.modality_switcher.adapters.gemini_adapter import GeminiAdapter, ADAPTER_METADATA as GEMINI_METADATA
        registry.register('gemini', GeminiAdapter, GEMINI_METADATA)
        logger.info("   ✅ Gemini adapter registered")
    except ImportError as e:
        logger.warning(f"   ⚠️  Gemini adapter not available: {e}")
    except Exception as e:
        logger.error(f"   ❌ Gemini registration failed: {e}")
    
    # Register Qodo adapter
    try:
        from empirica.plugins.modality_switcher.adapters.qodo_adapter import QodoAdapter, ADAPTER_METADATA as QODO_METADATA
        registry.register('qodo', QodoAdapter, QODO_METADATA)
        logger.info("   ✅ Qodo adapter registered")
    except ImportError as e:
        logger.warning(f"   ⚠️  Qodo adapter not available: {e}")
    except Exception as e:
        logger.error(f"   ❌ Qodo registration failed: {e}")
    
    # Register OpenRouter adapter
    try:
        from empirica.plugins.modality_switcher.adapters.openrouter_adapter import OpenRouterAdapter, ADAPTER_METADATA as OPENROUTER_METADATA
        registry.register('openrouter', OpenRouterAdapter, OPENROUTER_METADATA)
        logger.info("   ✅ OpenRouter adapter registered")
    except ImportError as e:
        logger.warning(f"   ⚠️  OpenRouter adapter not available: {e}")
    except Exception as e:
        logger.error(f"   ❌ OpenRouter registration failed: {e}")
    
    # Register Copilot adapter
    try:
        from empirica.plugins.modality_switcher.adapters.copilot_adapter import CopilotAdapter, ADAPTER_METADATA as COPILOT_METADATA
        registry.register('copilot', CopilotAdapter, COPILOT_METADATA)
        logger.info("   ✅ Copilot adapter registered")
    except ImportError as e:
        logger.warning(f"   ⚠️  Copilot adapter not available: {e}")
    except Exception as e:
        logger.error(f"   ❌ Copilot registration failed: {e}")

    # Register Local adapter (when implemented)
    try:
        from empirica.plugins.modality_switcher.adapters import LocalAdapter, LOCAL_METADATA
        registry.register('local', LocalAdapter, LOCAL_METADATA)
        logger.info("   ✅ Local adapter registered")
    except ImportError:
        logger.debug("   ⏳ Local adapter not yet implemented")
    except Exception as e:
        logger.error(f"   ❌ Local registration failed: {e}")
    
    # Log summary
    adapters = registry.list_adapters()
    logger.info(f"✅ Registry initialized with {len(adapters)} adapter(s)")
    
    return registry


def register_custom_adapter(name: str, adapter_class: type, metadata: dict = None):
    """
    Register a custom adapter to the global registry.
    
    Args:
        name: Adapter identifier
        adapter_class: Class implementing AdapterInterface
        metadata: Optional metadata dictionary
    """
    registry = get_registry()
    registry.register(name, adapter_class, metadata)
    logger.info(f"✅ Custom adapter registered: {name}")


def list_registered_adapters() -> list:
    """
    Get list of all registered adapters with metadata.
    
    Returns:
        List of adapter info dicts
    """
    registry = get_registry()
    return registry.list_adapters()


def health_check_adapters() -> dict:
    """
    Run health checks on all registered adapters.
    
    Returns:
        Dict mapping adapter name to health status (bool)
    """
    registry = get_registry()
    return registry.health_check_all()


# Convenience function for direct access
def get_adapter(name: str, config: dict = None):
    """
    Get an instantiated adapter by name.
    
    Args:
        name: Adapter identifier ('minimax', 'qwen', 'local')
        config: Optional configuration dict
        
    Returns:
        Instantiated adapter instance
        
    Raises:
        KeyError: If adapter not found
    """
    registry = get_registry()
    return registry.get_adapter(name, config)


if __name__ == "__main__":
    # Test registration when run directly
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("              ADAPTER REGISTRATION TEST")
    print("=" * 70)
    
    # Create registry
    registry = create_registry()
    
    # List adapters
    print("\n📋 Registered Adapters:")
    adapters = list_registered_adapters()
    for adapter in adapters:
        print(f"   • {adapter['name']}")
        print(f"     - Class: {adapter['class']}")
        print(f"     - Provider: {adapter.get('provider', 'N/A')}")
        print(f"     - Model: {adapter.get('model', 'N/A')}")
        print(f"     - Version: {adapter.get('version', 'N/A')}")
        print(f"     - Type: {adapter.get('type', 'N/A')}")
    
    # Health checks
    print("\n💓 Health Checks (without API keys - expected to fail gracefully):")
    health = health_check_adapters()
    for name, status in health.items():
        emoji = "✅" if status else "⚠️"
        print(f"   {emoji} {name}: {status}")
    
    print("\n" + "=" * 70)
    print("                    ✅ TEST COMPLETE")
    print("=" * 70)
