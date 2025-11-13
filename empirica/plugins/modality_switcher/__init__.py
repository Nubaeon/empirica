"""
Empirica ModalitySwitcher Plugin

Intelligent routing system for multi-modal AI interactions.
"""
__version__ = "1.0.0"

from .modality_switcher import ModalitySwitcher, RoutingStrategy, RoutingPreferences
from .plugin_registry import PluginRegistry, AdapterInterface, AdapterResponse, AdapterError
from .register_adapters import get_registry, get_adapter, list_registered_adapters
from .usage_monitor import UsageMonitor
from .auth_manager import AuthManager

__all__ = [
    'ModalitySwitcher',
    'RoutingStrategy',
    'RoutingPreferences',
    'PluginRegistry',
    'AdapterInterface',
    'AdapterResponse',
    'AdapterError',
    'get_registry',
    'get_adapter',
    'list_registered_adapters',
    'UsageMonitor',
    'AuthManager',
]
