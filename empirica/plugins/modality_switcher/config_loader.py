"""
Configuration Loader for Empirica Modality Switching

Loads configuration from YAML files with environment variable overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Load and manage Empirica modality configuration.
    
    Configuration priority (highest to lowest):
    1. Environment variables (EMPIRICA_*)
    2. User config file (~/.empirica/config.yaml)
    3. Project config file (./empirica_config.yaml)
    4. Default config file (package empirica/config/modality_config.yaml)
    """
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "modality_config.yaml"
    # Note: PROJECT_CONFIG_PATH is lazy-loaded in __init__ to avoid Path.cwd() failures
    # when module is imported from non-standard directories (e.g., during tests)
    USER_CONFIG_PATH = Path.home() / ".empirica" / "config.yaml"
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigLoader.
        
        Args:
            config_path: Optional explicit config file path
        """
        self.config_path = config_path
        # Lazy-load PROJECT_CONFIG_PATH to avoid Path.cwd() errors at import time
        try:
            self.PROJECT_CONFIG_PATH = Path.cwd() / "empirica_config.yaml"
        except (RuntimeError, FileNotFoundError):
            # cwd() can fail if working directory was deleted
            self.PROJECT_CONFIG_PATH = None
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from files and environment variables.
        
        Returns:
            Dict with full configuration
        """
        # Start with default config
        config = self._load_yaml(self.DEFAULT_CONFIG_PATH)
        if not config:
            logger.warning("Default config not found, using minimal defaults")
            config = self._get_minimal_defaults()
        
        # Overlay project config if exists
        if self.PROJECT_CONFIG_PATH and self.PROJECT_CONFIG_PATH.exists():
            project_config = self._load_yaml(self.PROJECT_CONFIG_PATH)
            if project_config:
                config = self._merge_configs(config, project_config)
                logger.info(f"Loaded project config from {self.PROJECT_CONFIG_PATH}")
        
        # Overlay user config if exists
        if self.USER_CONFIG_PATH.exists():
            user_config = self._load_yaml(self.USER_CONFIG_PATH)
            if user_config:
                config = self._merge_configs(config, user_config)
                logger.info(f"Loaded user config from {self.USER_CONFIG_PATH}")
        
        # Overlay explicit config if provided
        if self.config_path and self.config_path.exists():
            explicit_config = self._load_yaml(self.config_path)
            if explicit_config:
                config = self._merge_configs(config, explicit_config)
                logger.info(f"Loaded explicit config from {self.config_path}")
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config)
        
        return config
    
    def _load_yaml(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return None
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading config from {path}: {e}")
            return None
    
    def _merge_configs(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two config dictionaries.
        
        Args:
            base: Base configuration
            overlay: Configuration to overlay (takes precedence)
            
        Returns:
            Merged configuration
        """
        result = base.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides.
        
        Environment variables format: EMPIRICA_<SECTION>_<KEY>=value
        Example: EMPIRICA_ROUTING_DEFAULT_STRATEGY=cost
        """
        for env_key, env_value in os.environ.items():
            if env_key.startswith("EMPIRICA_"):
                # Parse env var name
                parts = env_key[9:].lower().split('_')  # Remove EMPIRICA_ prefix
                
                if len(parts) >= 2:
                    # Navigate config dict
                    current = config
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    
                    # Set value
                    key = parts[-1]
                    current[key] = self._parse_env_value(env_value)
                    logger.debug(f"Applied env override: {env_key}={env_value}")
        
        return config
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # String
        return value
    
    def _get_minimal_defaults(self) -> Dict[str, Any]:
        """Get minimal default configuration if files not found."""
        return {
            "adapters": {
                "minimax": {
                    "enabled": True,
                    "cost_per_1k_tokens": 0.01,
                    "estimated_latency_sec": 3.0,
                    "quality_score": 0.9
                },
                "qwen": {
                    "enabled": True,
                    "cost_per_1k_tokens": 0.0,
                    "estimated_latency_sec": 30.0,
                    "quality_score": 0.75
                },
                "local": {
                    "enabled": True,
                    "cost_per_1k_tokens": 0.0,
                    "estimated_latency_sec": 10.0,
                    "quality_score": 0.7
                }
            },
            "routing": {
                "default_strategy": "epistemic",
                "fallback": {"enabled": True}
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation path.
        
        Args:
            key_path: Dot-separated path (e.g., "routing.default_strategy")
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        current = self.config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_adapter_config(self, adapter_name: str) -> Dict[str, Any]:
        """Get configuration for a specific adapter."""
        return self.config.get("adapters", {}).get(adapter_name, {})
    
    def get_routing_config(self) -> Dict[str, Any]:
        """Get routing configuration."""
        return self.config.get("routing", {})
    
    def is_adapter_enabled(self, adapter_name: str) -> bool:
        """Check if adapter is enabled."""
        return self.get_adapter_config(adapter_name).get("enabled", True)
    
    def get_adapter_costs(self) -> Dict[str, float]:
        """Get cost per 1k tokens for all adapters."""
        costs = {}
        for name, config in self.config.get("adapters", {}).items():
            costs[name] = config.get("cost_per_1k_tokens", 0.0)
        return costs
    
    def get_adapter_latencies(self) -> Dict[str, float]:
        """Get estimated latency for all adapters."""
        latencies = {}
        for name, config in self.config.get("adapters", {}).items():
            latencies[name] = config.get("estimated_latency_sec", 10.0)
        return latencies
    
    def get_adapter_quality(self) -> Dict[str, float]:
        """Get quality scores for all adapters."""
        quality = {}
        for name, config in self.config.get("adapters", {}).items():
            quality[name] = config.get("quality_score", 0.7)
        return quality
    
    def save_user_config(self, config: Dict[str, Any]):
        """
        Save configuration to user config file.
        
        Args:
            config: Configuration to save
        """
        # Ensure directory exists
        self.USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save YAML
        with open(self.USER_CONFIG_PATH, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Saved user config to {self.USER_CONFIG_PATH}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self.config.copy()


# Global config instance
_config_loader = None


def get_config(reload: bool = False) -> ConfigLoader:
    """
    Get or create global ConfigLoader instance.
    
    Args:
        reload: If True, reload configuration from files
        
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    
    if _config_loader is None or reload:
        _config_loader = ConfigLoader()
    
    return _config_loader


if __name__ == "__main__":
    # Test configuration loading
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("              CONFIGURATION LOADER TEST")
    print("=" * 70)
    
    loader = ConfigLoader()
    
    print("\n✅ Configuration loaded successfully")
    print(f"   Default strategy: {loader.get('routing.default_strategy')}")
    print(f"   MiniMax enabled: {loader.is_adapter_enabled('minimax')}")
    print(f"   Qwen enabled: {loader.is_adapter_enabled('qwen')}")
    
    print("\n📊 Adapter Costs:")
    for name, cost in loader.get_adapter_costs().items():
        print(f"   {name}: ${cost:.4f}/1k tokens")
    
    print("\n⏱️  Adapter Latencies:")
    for name, latency in loader.get_adapter_latencies().items():
        print(f"   {name}: {latency:.1f}s")
    
    print("\n⭐ Adapter Quality:")
    for name, quality in loader.get_adapter_quality().items():
        print(f"   {name}: {quality:.2f}")
    
    print("\n" + "=" * 70)
    print("                  ✅ TEST COMPLETE")
    print("=" * 70)
