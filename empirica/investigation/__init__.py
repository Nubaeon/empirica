"""
Investigation Module

Provides pluggable investigation capabilities for Empirica CASCADE.

Plugin Discovery:
    Extensions can register plugins via pyproject.toml entry points:

    [project.entry-points."empirica.plugins"]
    my_ext = "my_extension:register_plugins"

    Then implement:
        def register_plugins(registry: PluginRegistry):
            registry.register(InvestigationPlugin(...))
"""

from .investigation_plugin import (
    InvestigationPlugin,
    PluginRegistry,
    get_global_registry,
    reset_global_registry,
)

__all__ = [
    'InvestigationPlugin',
    'PluginRegistry',
    'get_global_registry',
    'reset_global_registry',
]
