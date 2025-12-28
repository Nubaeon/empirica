#!/usr/bin/env python3
"""
Empirica Path Resolver - Single Source of Truth for All Paths

Resolves paths in priority order:
1. Environment variables (EMPIRICA_WORKSPACE_ROOT for Docker, EMPIRICA_DATA_DIR for explicit paths)
2. .empirica/config.yaml in git root
3. Fallback to CWD/.empirica (legacy behavior)

Environment Variables:
    EMPIRICA_WORKSPACE_ROOT: For Docker/multi-AI environments. Points to workspace root.
                            System will look for <workspace>/.empirica/
    EMPIRICA_DATA_DIR:      Explicit path to empirica data directory
    EMPIRICA_SESSION_DB:    Explicit path to sessions database file

Usage:
    from empirica.config.path_resolver import get_empirica_root, get_session_db_path

    root = get_empirica_root()  # Returns Path object
    db_path = get_session_db_path()  # Returns full path to sessions.db

Docker Example:
    Set in docker-compose.yml:
      environment:
        - EMPIRICA_WORKSPACE_ROOT=/workspace
    
    This ensures all containers use the same workspace for empirica data.

Author: Claude Code
Date: 2025-12-03
Version: 1.1.0 (Added EMPIRICA_WORKSPACE_ROOT support)
"""

import os
import subprocess
import yaml
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Cache for git root (expensive to compute repeatedly)
_git_root_cache: Optional[Path] = None


def get_git_root() -> Optional[Path]:
    """
    Get git repository root directory.

    Returns:
        Path to git root, or None if not in a git repo
    """
    global _git_root_cache

    if _git_root_cache is not None:
        return _git_root_cache

    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )

        if result.returncode == 0:
            _git_root_cache = Path(result.stdout.strip())
            return _git_root_cache

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def load_empirica_config() -> Optional[dict]:
    """
    Load .empirica/config.yaml from git root.

    Returns:
        Config dict or None if not found
    """
    git_root = get_git_root()
    if not git_root:
        return None

    config_path = git_root / '.empirica' / 'config.yaml'
    if not config_path.exists():
        return None

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.debug(f"✅ Loaded Empirica config from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"⚠️  Failed to load {config_path}: {e}")
        return None


def get_empirica_root() -> Path:
    """
    Get Empirica root data directory.

    Priority:
    1. EMPIRICA_WORKSPACE_ROOT environment variable (for Docker/workspace environments)
    2. EMPIRICA_DATA_DIR environment variable (explicit data dir)
    3. .empirica/config.yaml -> root
    4. <git-root>/.empirica (if in git repo)
    5. <cwd>/.empirica (fallback)

    Returns:
        Path to .empirica root directory
    """
    # 1. Check workspace root (Docker/multi-AI environments)
    if workspace_root := os.getenv('EMPIRICA_WORKSPACE_ROOT'):
        workspace_path = Path(workspace_root).expanduser().resolve()
        empirica_root = workspace_path / '.empirica'
        if empirica_root.exists() or workspace_path.exists():
            logger.debug(f"📍 Using EMPIRICA_WORKSPACE_ROOT: {empirica_root}")
            return empirica_root

    # 2. Check explicit data dir environment variable
    if env_root := os.getenv('EMPIRICA_DATA_DIR'):
        root = Path(env_root).expanduser().resolve()
        logger.debug(f"📍 Using EMPIRICA_DATA_DIR: {root}")
        return root

    # 3. Check .empirica/config.yaml
    config = load_empirica_config()
    if config and 'root' in config:
        root = Path(config['root']).expanduser().resolve()
        logger.debug(f"📍 Using config.yaml root: {root}")
        return root

    # 4. Use git root if available
    git_root = get_git_root()
    if git_root:
        root = git_root / '.empirica'
        logger.debug(f"📍 Using git root: {root}")
        return root

    # 5. Fallback to CWD (legacy behavior)
    root = Path.cwd() / '.empirica'
    logger.debug(f"📍 Fallback to CWD: {root}")
    return root


def get_session_db_path() -> Path:
    """
    Get full path to sessions database.

    Priority:
    1. EMPIRICA_SESSION_DB environment variable
    2. .empirica/config.yaml -> paths.sessions
    3. <empirica_root>/sessions/sessions.db (default)

    Returns:
        Path to sessions.db
    """
    # 1. Check environment variable
    if env_db := os.getenv('EMPIRICA_SESSION_DB'):
        db_path = Path(env_db).expanduser().resolve()
        logger.debug(f"📍 Using EMPIRICA_SESSION_DB: {db_path}")
        return db_path

    # 2. Check config
    config = load_empirica_config()
    if config and 'paths' in config and 'sessions' in config['paths']:
        root = get_empirica_root()
        db_path = root / config['paths']['sessions']
        logger.debug(f"📍 Using config.yaml sessions path: {db_path}")
        return db_path

    # 3. Default path
    root = get_empirica_root()
    db_path = root / 'sessions' / 'sessions.db'
    logger.debug(f"📍 Using default sessions path: {db_path}")
    return db_path


def get_identity_dir() -> Path:
    """Get identity keys directory."""
    config = load_empirica_config()
    if config and 'paths' in config and 'identity' in config['paths']:
        root = get_empirica_root()
        return root / config['paths']['identity']

    return get_empirica_root() / 'identity'


def get_metrics_dir() -> Path:
    """Get metrics directory."""
    config = load_empirica_config()
    if config and 'paths' in config and 'metrics' in config['paths']:
        root = get_empirica_root()
        return root / config['paths']['metrics']

    return get_empirica_root() / 'metrics'


def get_messages_dir() -> Path:
    """Get messages directory."""
    config = load_empirica_config()
    if config and 'paths' in config and 'messages' in config['paths']:
        root = get_empirica_root()
        return root / config['paths']['messages']

    return get_empirica_root() / 'messages'


def ensure_empirica_structure() -> None:
    """
    Ensure .empirica directory structure exists.
    Creates directories if they don't exist.
    """
    root = get_empirica_root()

    # Create subdirectories
    (root / 'sessions').mkdir(parents=True, exist_ok=True)
    (root / 'identity').mkdir(parents=True, exist_ok=True)
    (root / 'metrics').mkdir(parents=True, exist_ok=True)
    (root / 'messages').mkdir(parents=True, exist_ok=True)
    (root / 'personas').mkdir(parents=True, exist_ok=True)

    logger.debug(f"✅ Ensured .empirica structure at {root}")


def create_default_config() -> None:
    """
    Create default .empirica/config.yaml if it doesn't exist.
    Only creates in git repos.
    """
    git_root = get_git_root()
    if not git_root:
        logger.debug("Not in git repo, skipping config.yaml creation")
        return

    config_path = git_root / '.empirica' / 'config.yaml'
    if config_path.exists():
        logger.debug(f"Config already exists: {config_path}")
        return

    # Ensure .empirica directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Create default config
    default_config = {
        'version': '2.0',
        'root': str(git_root / '.empirica'),
        'paths': {
            'sessions': 'sessions/sessions.db',
            'identity': 'identity/',
            'messages': 'messages/',
            'metrics': 'metrics/',
            'personas': 'personas/'
        },
        'settings': {
            'auto_checkpoint': True,
            'git_integration': True,
            'log_level': 'info'
        },
        'env_overrides': [
            'EMPIRICA_DATA_DIR',
            'EMPIRICA_SESSION_DB'
        ]
    }

    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"✅ Created default config: {config_path}")


def debug_paths() -> dict:
    """
    Get all resolved paths for debugging.

    Returns:
        Dict with all path information
    """
    return {
        'git_root': str(get_git_root()) if get_git_root() else None,
        'empirica_root': str(get_empirica_root()),
        'session_db': str(get_session_db_path()),
        'identity_dir': str(get_identity_dir()),
        'metrics_dir': str(get_metrics_dir()),
        'messages_dir': str(get_messages_dir()),
        'env_vars': {
            'EMPIRICA_DATA_DIR': os.getenv('EMPIRICA_DATA_DIR'),
            'EMPIRICA_SESSION_DB': os.getenv('EMPIRICA_SESSION_DB')
        },
        'config_loaded': load_empirica_config() is not None
    }


if __name__ == '__main__':
    # Test/debug mode
    import json

    logging.basicConfig(level=logging.DEBUG)

    print("🔍 Empirica Path Resolver Debug\n")
    print(json.dumps(debug_paths(), indent=2))

    print("\n📋 Ensuring structure...")
    ensure_empirica_structure()

    print("\n📝 Creating default config...")
    create_default_config()
