"""
Base Plugin Interface

Defines the standard interface all Empirica plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePlugin(ABC):
    """Base class for all Empirica plugins."""
    
    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the plugin with optional configuration.
        
        Args:
            config: Optional plugin configuration
            
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the plugin is healthy and operational.
        
        Returns:
            True if healthy
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get plugin metadata (name, version, description, etc).
        
        Returns:
            Metadata dictionary
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass
