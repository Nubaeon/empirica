#!/usr/bin/env python3
"""
Investigation Plugin Interface

Defines reusable plugin interfaces for extending Empirica's investigation
capabilities with custom tools. Plugins can be used to integrate external
services (JIRA, Confluence, Slack, etc.) into epistemic workflows.

Usage:
    from empirica.investigation.investigation_plugin import InvestigationPlugin

    jira_plugin = InvestigationPlugin(
        name='jira_search',
        description='Search JIRA for related issues and tickets',
        improves_vectors=['know', 'context', 'state'],
        confidence_gain=0.20,
        tool_type='search'
    )
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InvestigationPlugin:
    """
    Plugin interface for custom investigation tools
    
    Attributes:
        name: Unique identifier for the tool
        description: Clear explanation of what the tool does (shown to LLM)
        improves_vectors: Which epistemic vectors this tool helps improve
        confidence_gain: Expected confidence increase (0.0-1.0)
        tool_type: Category (search, analysis, interaction, validation, custom)
        executor: Optional callable that actually executes the tool
        metadata: Additional plugin-specific data
    """
    name: str
    description: str
    improves_vectors: List[str]
    confidence_gain: float
    tool_type: str = 'custom'
    executor: Optional[Callable] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validate plugin configuration"""
        if not self.name:
            raise ValueError("Plugin name is required")
        
        if not self.description:
            raise ValueError("Plugin description is required")
        
        if not self.improves_vectors:
            raise ValueError("Plugin must improve at least one vector")
        
        if not (0.0 <= self.confidence_gain <= 1.0):
            raise ValueError("Confidence gain must be between 0.0 and 1.0")
        
        valid_vectors = [
            'know', 'do', 'context', 'clarity', 'coherence', 
            'signal', 'density', 'state', 'change', 'completion', 
            'impact', 'engagement'
        ]
        
        for vector in self.improves_vectors:
            if vector not in valid_vectors:
                raise ValueError(f"Invalid vector: {vector}. Must be one of {valid_vectors}")
        
        if self.metadata is None:
            self.metadata = {}
    
    def to_capability_dict(self) -> Dict[str, Any]:
        """
        Convert plugin to capability dictionary for tool mapping
        
        Returns dictionary compatible with Empirica's tool capability format
        """
        return {
            'description': self.description,
            'improves_vectors': self.improves_vectors,
            'tool_type': self.tool_type,
            'confidence_gain': self.confidence_gain,
            'plugin': True,
            'metadata': self.metadata
        }
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plugin tool (if executor is provided)
        
        Args:
            context: Execution context including task, current state, etc.
        
        Returns:
            Result dictionary with success status and information gained
        """
        if self.executor is None:
            return {
                'success': False,
                'error': 'Plugin has no executor defined',
                'note': 'This plugin provides capability information only'
            }
        
        try:
            result = await self.executor(context)
            return {
                'success': True,
                'plugin_name': self.name,
                'result': result,
                'vectors_improved': self.improves_vectors
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'plugin_name': self.name
            }
    
    def __repr__(self):
        return f"InvestigationPlugin(name='{self.name}', improves={self.improves_vectors}, gain={self.confidence_gain})"


class PluginRegistry:
    """
    Registry for managing investigation plugins

    Provides convenient methods for registering, discovering, and using plugins.

    Auto-discovery: Call discover_plugins() to load plugins from installed packages
    that declare entry points in [project.entry-points."empirica.plugins"].
    """

    def __init__(self, auto_discover: bool = False):
        self.plugins: Dict[str, InvestigationPlugin] = {}
        self._discovered = False
        if auto_discover:
            self.discover_plugins()

    def register(self, plugin: InvestigationPlugin) -> None:
        """Register a plugin"""
        if plugin.name in self.plugins:
            raise ValueError(f"Plugin '{plugin.name}' already registered")

        self.plugins[plugin.name] = plugin
        logger.info(f"📦 Registered plugin: {plugin.name}")

    def discover_plugins(self) -> int:
        """
        Auto-discover and load plugins from installed packages.

        Looks for entry points in group 'empirica.plugins'. Each entry point
        should be a callable that accepts a PluginRegistry and registers plugins.

        Example pyproject.toml in extension package:
            [project.entry-points."empirica.plugins"]
            my_ext = "my_extension:register_plugins"

        Where register_plugins is:
            def register_plugins(registry: PluginRegistry):
                registry.register(MyPlugin(...))

        Returns:
            Number of plugins discovered and loaded
        """
        if self._discovered:
            return 0

        count = 0
        try:
            from importlib.metadata import entry_points

            # Python 3.10+ returns SelectableGroups, 3.9 returns dict
            eps = entry_points()
            if hasattr(eps, 'select'):
                # Python 3.10+
                plugin_eps = eps.select(group='empirica.plugins')
            else:
                # Python 3.9 fallback
                plugin_eps = eps.get('empirica.plugins', [])

            for ep in plugin_eps:
                try:
                    register_fn = ep.load()
                    before_count = len(self.plugins)
                    register_fn(self)
                    added = len(self.plugins) - before_count
                    count += added
                    logger.info(f"🔌 Loaded {added} plugin(s) from {ep.name}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to load plugin entry point {ep.name}: {e}")

            self._discovered = True

        except ImportError:
            logger.debug("importlib.metadata not available, skipping plugin discovery")

        return count
    
    def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            logger.info(f"🗑️  Unregistered plugin: {plugin_name}")
    
    def get(self, plugin_name: str) -> Optional[InvestigationPlugin]:
        """Get a plugin by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin names"""
        return list(self.plugins.keys())
    
    def get_all_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capability dictionary for all plugins"""
        return {
            name: plugin.to_capability_dict()
            for name, plugin in self.plugins.items()
        }
    
    def find_by_vector(self, vector: str) -> List[InvestigationPlugin]:
        """Find all plugins that improve a specific vector"""
        return [
            plugin for plugin in self.plugins.values()
            if vector in plugin.improves_vectors
        ]
    
    def __len__(self):
        return len(self.plugins)
    
    def __repr__(self):
        return f"PluginRegistry(plugins={len(self.plugins)})"


# Example plugins for demonstration

def create_jira_plugin() -> InvestigationPlugin:
    """Example: JIRA integration plugin"""
    return InvestigationPlugin(
        name='jira_search',
        description='Search JIRA for related issues, tickets, and project information. Use when investigating bugs, feature requests, or project context.',
        improves_vectors=['know', 'context', 'state'],
        confidence_gain=0.20,
        tool_type='search',
        metadata={
            'api_required': True,
            'authentication': 'required',
            'rate_limit': '100 requests/hour'
        }
    )


def create_confluence_plugin() -> InvestigationPlugin:
    """Example: Confluence integration plugin"""
    return InvestigationPlugin(
        name='confluence_search',
        description='Search Confluence documentation and knowledge base. Use for finding architectural decisions, design docs, or team guidelines.',
        improves_vectors=['know', 'clarity', 'context'],
        confidence_gain=0.25,
        tool_type='search',
        metadata={
            'api_required': True,
            'authentication': 'required'
        }
    )


def create_slack_plugin() -> InvestigationPlugin:
    """Example: Slack integration plugin"""
    return InvestigationPlugin(
        name='slack_search',
        description='Search Slack conversations for discussions, decisions, and context. Use to understand team communications and past decisions.',
        improves_vectors=['context', 'coherence', 'state'],
        confidence_gain=0.15,
        tool_type='search',
        metadata={
            'api_required': True,
            'authentication': 'required',
            'privacy_considerations': 'May contain sensitive information'
        }
    )


def create_github_plugin() -> InvestigationPlugin:
    """Example: GitHub integration plugin"""
    return InvestigationPlugin(
        name='github_search',
        description='Search GitHub repositories, issues, pull requests, and commits. Use for code examples, bug reports, or implementation details.',
        improves_vectors=['know', 'do', 'context'],
        confidence_gain=0.25,
        tool_type='search',
        metadata={
            'api_required': True,
            'authentication': 'optional',
            'rate_limit': '5000 requests/hour (authenticated)'
        }
    )


def create_database_query_plugin() -> InvestigationPlugin:
    """Example: Database query plugin"""
    return InvestigationPlugin(
        name='database_query',
        description='Query database for data analysis and state verification. Use when you need to understand current system state or validate data.',
        improves_vectors=['know', 'state', 'context'],
        confidence_gain=0.30,
        tool_type='analysis',
        metadata={
            'requires_permissions': True,
            'safety': 'Read-only queries recommended'
        }
    )


# Convenience function for common plugin sets
def create_common_plugins() -> Dict[str, InvestigationPlugin]:
    """Create a set of commonly useful plugins"""
    return {
        'jira_search': create_jira_plugin(),
        'confluence_search': create_confluence_plugin(),
        'slack_search': create_slack_plugin(),
        'github_search': create_github_plugin()
    }


# Global plugin registry (lazy-initialized with auto-discovery)
_global_registry: Optional[PluginRegistry] = None


def get_global_registry(auto_discover: bool = True) -> PluginRegistry:
    """
    Get or create the global plugin registry.

    Args:
        auto_discover: If True, automatically discover plugins from installed packages
                      on first call. Set to False for testing or manual control.

    Returns:
        The global PluginRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry(auto_discover=auto_discover)
    return _global_registry


def reset_global_registry() -> None:
    """Reset the global registry (useful for testing)"""
    global _global_registry
    _global_registry = None


if __name__ == "__main__":
    # Demo usage
    logger.info("🔌 Investigation Plugin System Demo\n")
    
    # Create registry
    registry = PluginRegistry()
    
    # Register example plugins
    registry.register(create_jira_plugin())
    registry.register(create_confluence_plugin())
    registry.register(create_github_plugin())
    
    logger.info(f"\n✓ Registered {len(registry)} plugins")
    logger.info(f"  Plugins: {registry.list_plugins()}")
    
    # Find plugins by vector
    know_plugins = registry.find_by_vector('know')
    logger.info(f"\n✓ Plugins that improve 'know' vector: {[p.name for p in know_plugins]}")
    
    # Get capabilities for cascade integration
    capabilities = registry.get_all_capabilities()
    logger.info(f"\n✓ Plugin capabilities ready for tool mapping:")
    for name, cap in capabilities.items():
        logger.info(f"  • {name}: {cap['description'][:50]}...")
        logger.info(f"    Improves: {', '.join(cap['improves_vectors'])}")
        logger.info(f"    Gain: +{cap['confidence_gain']:.2f}")
    
    logger.info("\n✅ Plugin system ready for integration!")
