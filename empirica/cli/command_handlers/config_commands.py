"""
Configuration Commands - CLI commands for managing Empirica configuration
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any

from empirica.plugins.modality_switcher.config_loader import ConfigLoader, get_config
from ..cli_utils import handle_cli_error


def handle_config_init_command(args):
    """
    Initialize Empirica configuration.
    
    Creates user config file at ~/.empirica/config.yaml with default values.
    """
    try:
        print("\n🔧 Initializing Empirica Configuration")
        print("=" * 70)
        
        user_config_path = Path.home() / ".empirica" / "config.yaml"
        
        # Check if config already exists
        if user_config_path.exists() and not getattr(args, 'force', False):
            print(f"\n⚠️  Configuration file already exists:")
            print(f"   {user_config_path}")
            print(f"\nUse --force to overwrite")
            return
        
        # Load default config
        loader = ConfigLoader()
        default_config = loader.to_dict()
        
        # Save to user config
        loader.save_user_config(default_config)
        
        print(f"\n✅ Configuration initialized:")
        print(f"   {user_config_path}")
        print(f"\n📝 Edit this file to customize your Empirica settings")
        print(f"\n💡 Quick commands:")
        print(f"   empirica config show       - View current configuration")
        print(f"   empirica config validate   - Validate configuration")
        
    except Exception as e:
        handle_cli_error(e, "Config Init", getattr(args, 'verbose', False))


def handle_config_show_command(args):
    """
    Show current Empirica configuration.
    
    Displays merged configuration from all sources with priority.
    """
    try:
        print("\n📋 Empirica Configuration")
        print("=" * 70)
        
        loader = get_config(reload=True)
        
        # Determine output format
        output_format = getattr(args, 'format', 'yaml')
        section = getattr(args, 'section', None)
        
        # Get config (full or section)
        if section:
            config = loader.get(section)
            if config is None:
                print(f"❌ Section not found: {section}")
                return
            print(f"\nSection: {section}")
        else:
            config = loader.to_dict()
            print("\nFull Configuration")
        
        print("=" * 70)
        
        # Display config
        if output_format == 'json':
            print(json.dumps(config, indent=2))
        else:  # yaml
            print(yaml.dump(config, default_flow_style=False, sort_keys=False))
        
        # Show config sources
        if not section:
            print("\n" + "=" * 70)
            print("📂 Configuration Sources (priority order):")
            print("   1. Environment variables (EMPIRICA_*)")
            print("   2. User config (~/.empirica/config.yaml)")
            if loader.PROJECT_CONFIG_PATH.exists():
                print("   3. Project config (./empirica_config.yaml) ✅")
            else:
                print("   3. Project config (./empirica_config.yaml) ❌")
            print("   4. Default config (built-in)")
        
    except Exception as e:
        handle_cli_error(e, "Config Show", getattr(args, 'verbose', False))


def handle_config_validate_command(args):
    """
    Validate Empirica configuration.
    
    Checks for errors and warns about potential issues.
    """
    try:
        print("\n🔍 Validating Empirica Configuration")
        print("=" * 70)
        
        loader = get_config(reload=True)
        issues = []
        warnings = []
        
        # Validate adapter configuration
        print("\n📊 Checking Adapters...")
        adapters = loader.config.get("adapters", {})
        
        if not adapters:
            issues.append("No adapters configured")
        
        for name, config in adapters.items():
            # Check required fields
            if "cost_per_1k_tokens" not in config:
                warnings.append(f"{name}: Missing cost_per_1k_tokens (using default)")
            
            if "estimated_latency_sec" not in config:
                warnings.append(f"{name}: Missing estimated_latency_sec (using default)")
            
            # Check API key for adapters that need it
            if config.get("requires_api_key", False):
                api_key_env = config.get("api_key_env")
                if api_key_env and not os.getenv(api_key_env):
                    warnings.append(f"{name}: API key not found in environment ({api_key_env})")
            
            print(f"   ✅ {name}: Valid")
        
        # Validate routing configuration
        print("\n🔄 Checking Routing...")
        routing = loader.get_routing_config()
        
        if not routing:
            issues.append("No routing configuration found")
        else:
            default_strategy = routing.get("default_strategy")
            valid_strategies = ["epistemic", "cost", "latency", "quality", "balanced"]
            
            if default_strategy not in valid_strategies:
                issues.append(f"Invalid default_strategy: {default_strategy}")
            else:
                print(f"   ✅ Default strategy: {default_strategy}")
        
        # Validate monitoring
        print("\n📈 Checking Monitoring...")
        monitoring = loader.config.get("monitoring", {})
        if monitoring.get("enabled"):
            export_path = Path(monitoring.get("export_path", "~/.empirica/usage_stats.json")).expanduser()
            if not export_path.parent.exists():
                warnings.append(f"Monitoring export directory doesn't exist: {export_path.parent}")
            else:
                print(f"   ✅ Export path: {export_path}")
        else:
            print("   ⚠️  Monitoring disabled")
        
        # Summary
        print("\n" + "=" * 70)
        
        if not issues and not warnings:
            print("✅ Configuration is valid with no issues")
        else:
            if issues:
                print(f"❌ Found {len(issues)} issue(s):")
                for issue in issues:
                    print(f"   • {issue}")
            
            if warnings:
                print(f"\n⚠️  Found {len(warnings)} warning(s):")
                for warning in warnings:
                    print(f"   • {warning}")
        
        print("=" * 70)
        
    except Exception as e:
        handle_cli_error(e, "Config Validate", getattr(args, 'verbose', False))


def handle_config_get_command(args):
    """
    Get a specific configuration value.
    
    Uses dot notation to access nested values.
    """
    try:
        key = args.key
        loader = get_config(reload=True)
        
        value = loader.get(key)
        
        if value is None:
            print(f"❌ Configuration key not found: {key}")
            return
        
        print(f"✅ {key}: {value}")
        
    except Exception as e:
        handle_cli_error(e, "Config Get", getattr(args, 'verbose', False))


def handle_config_set_command(args):
    """
    Set a configuration value in user config.
    
    Note: Only updates user config file, not environment or project config.
    """
    try:
        key = args.key
        value = args.value
        
        print(f"\n🔧 Setting Configuration")
        print("=" * 70)
        
        # Load current user config
        user_config_path = Path.home() / ".empirica" / "config.yaml"
        
        if user_config_path.exists():
            with open(user_config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
        else:
            print("⚠️  User config doesn't exist. Creating new config...")
            user_config = {}
        
        # Parse key path
        keys = key.split('.')
        current = user_config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Parse value
        parsed_value = _parse_value(value)
        
        # Set value
        current[keys[-1]] = parsed_value
        
        # Save config
        loader = ConfigLoader()
        loader.save_user_config(user_config)
        
        print(f"\n✅ Configuration updated:")
        print(f"   {key} = {parsed_value}")
        print(f"\n📝 Saved to: {user_config_path}")
        
    except Exception as e:
        handle_cli_error(e, "Config Set", getattr(args, 'verbose', False))


def _parse_value(value: str) -> Any:
    """Parse string value to appropriate type."""
    # Boolean
    if value.lower() in ('true', 'yes'):
        return True
    if value.lower() in ('false', 'no'):
        return False
    
    # Number
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    # Try JSON
    try:
        return json.loads(value)
    except:
        pass
    
    # String
    return value
