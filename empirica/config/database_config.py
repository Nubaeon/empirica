#!/usr/bin/env python3
"""
Database Configuration Loader

Loads database configuration from:
1. Environment variables (EMPIRICA_DB_TYPE, EMPIRICA_DB_*)
2. config.yaml (database section)
3. Defaults to SQLite

Example config.yaml:
    database:
      type: sqlite  # or postgresql
      sqlite:
        path: ./.empirica/sessions/sessions.db
      postgresql:
        host: localhost
        port: 5432
        database: empirica
        user: empirica
        password: ${POSTGRES_PASSWORD}  # env var substitution
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from environment or config file

    Returns:
        Dictionary with database configuration:
        {
            "type": "sqlite" | "postgresql",
            "sqlite": {...},  # if type=sqlite
            "postgresql": {...}  # if type=postgresql
        }
    """
    # Check environment variable first
    db_type = os.environ.get("EMPIRICA_DB_TYPE", "sqlite")

    if db_type == "postgresql":
        return {
            "type": "postgresql",
            "postgresql": {
                "host": os.environ.get("EMPIRICA_DB_HOST", "localhost"),
                "port": int(os.environ.get("EMPIRICA_DB_PORT", "5432")),
                "database": os.environ.get("EMPIRICA_DB_NAME", "empirica"),
                "user": os.environ.get("EMPIRICA_DB_USER", "empirica"),
                "password": os.environ.get("EMPIRICA_DB_PASSWORD", ""),
            }
        }

    # Try to load from config.yaml
    try:
        from empirica.config.path_resolver import get_git_root

        git_root = get_git_root()
        if git_root:
            config_path = git_root / ".empirica" / "config.yaml"
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    if config and "database" in config:
                        db_config = config["database"]
                        # Substitute environment variables in config
                        db_config = _substitute_env_vars(db_config)
                        logger.info(f"📊 Loaded database config from {config_path}")
                        return db_config
    except Exception as e:
        logger.debug(f"Could not load database config from file: {e}")

    # Default to SQLite
    logger.info("📊 Using default SQLite database configuration")
    return {
        "type": "sqlite",
        "sqlite": {
            "path": None  # Will use default from path_resolver
        }
    }


def _substitute_env_vars(config: Any) -> Any:
    """
    Recursively substitute ${VAR} with environment variables

    Example:
        password: ${POSTGRES_PASSWORD} -> password: actual_value
    """
    if isinstance(config, dict):
        return {k: _substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_substitute_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        var_name = config[2:-1]
        return os.environ.get(var_name, config)
    else:
        return config
