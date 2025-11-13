"""
Empirica Plugin System

Pluggable architecture for extending Empirica functionality.
"""

__version__ = "1.0.0"

# Plugin loader will be implemented here
# For now, just expose the modality_switcher plugin

from .modality_switcher import ModalitySwitcher

__all__ = ['ModalitySwitcher']
