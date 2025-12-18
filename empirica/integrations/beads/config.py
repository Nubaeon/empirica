"""
BEADS Configuration

Manages BEADS integration settings from .empirica/config.yaml
"""

import yaml
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BeadsConfig:
    """BEADS integration configuration"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize BEADS configuration
        
        Args:
            config_path: Path to config.yaml (default: ./.empirica/config.yaml)
        """
        if config_path is None:
            config_path = Path('.empirica/config.yaml')
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            logger.debug(f"Config file not found: {self.config_path}")
            return self._default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
                return config.get('integrations', {}).get('beads', self._default_config())
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {e}")
            return self._default_config()
    
    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Default BEADS configuration"""
        return {
            'enabled': True,
            'auto_detect': True,
            'use_agent_mail': False,
            'agent_mail_url': 'http://127.0.0.1:8765',
            'agent_name': None
        }
    
    @property
    def enabled(self) -> bool:
        """Is BEADS integration enabled?"""
        return self._config.get('enabled', True)
    
    @property
    def auto_detect(self) -> bool:
        """Should we auto-detect bd CLI availability?"""
        return self._config.get('auto_detect', True)
    
    @property
    def use_agent_mail(self) -> bool:
        """Use Agent Mail for multi-AI coordination?"""
        return self._config.get('use_agent_mail', False)
    
    @property
    def agent_mail_url(self) -> str:
        """Agent Mail server URL"""
        return self._config.get('agent_mail_url', 'http://127.0.0.1:8765')
    
    @property
    def agent_name(self) -> Optional[str]:
        """Agent name for Agent Mail"""
        return self._config.get('agent_name')
    
    def save(self):
        """Save configuration to YAML file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load full config
        full_config = {}
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                full_config = yaml.safe_load(f) or {}
        
        # Update BEADS section
        if 'integrations' not in full_config:
            full_config['integrations'] = {}
        
        full_config['integrations']['beads'] = self._config
        
        # Write back
        with open(self.config_path, 'w') as f:
            yaml.dump(full_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Saved BEADS config to {self.config_path}")
