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

# Forbidden system paths for workspace/data directories
FORBIDDEN_PATH_PREFIXES = ['/etc', '/var/log', '/usr', '/bin', '/sbin', '/root', '/boot', '/proc', '/sys']


def _validate_user_path(path_str: str, env_var_name: str) -> Path:
    """
    Validate that a user-provided path is safe.

    Args:
        path_str: The path string from environment variable
        env_var_name: Name of the env var (for error messages)

    Returns:
        Validated and resolved Path

    Raises:
        ValueError: If path is in a forbidden system directory
    """
    resolved = Path(path_str).expanduser().resolve()
    resolved_str = str(resolved)

    for prefix in FORBIDDEN_PATH_PREFIXES:
        if resolved_str.startswith(prefix):
            raise ValueError(
                f"{env_var_name} cannot point to system directory: {prefix}. "
                f"Got: {resolved_str}"
            )

    return resolved


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
        try:
            workspace_path = _validate_user_path(workspace_root, 'EMPIRICA_WORKSPACE_ROOT')
            empirica_root = workspace_path / '.empirica'
            if empirica_root.exists() or workspace_path.exists():
                logger.debug(f"📍 Using EMPIRICA_WORKSPACE_ROOT: {empirica_root}")
                return empirica_root
        except ValueError as e:
            logger.warning(f"⚠️  Invalid EMPIRICA_WORKSPACE_ROOT: {e}")
            # Fall through to next option

    # 2. Check explicit data dir environment variable
    if env_root := os.getenv('EMPIRICA_DATA_DIR'):
        try:
            root = _validate_user_path(env_root, 'EMPIRICA_DATA_DIR')
            logger.debug(f"📍 Using EMPIRICA_DATA_DIR: {root}")
            return root
        except ValueError as e:
            logger.warning(f"⚠️  Invalid EMPIRICA_DATA_DIR: {e}")
            # Fall through to next option

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
        try:
            db_path = _validate_user_path(env_db, 'EMPIRICA_SESSION_DB')
            logger.debug(f"📍 Using EMPIRICA_SESSION_DB: {db_path}")
            return db_path
        except ValueError as e:
            logger.warning(f"⚠️  Invalid EMPIRICA_SESSION_DB: {e}")
            # Fall through to next option

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


def resolve_session_db_path(session_id: str) -> Optional[Path]:
    """
    Resolve which database contains a given session.

    For now, returns the current project's DB path.
    Future enhancement: Look up session in workspace.db to find correct project.

    Args:
        session_id: UUID of the session to find

    Returns:
        Path to the sessions.db containing this session, or None if not found
    """
    # Use current project's DB (CWD-based detection)
    # TODO: Look up session_id in workspace.db to find which project it belongs to
    db_path = get_session_db_path()
    if db_path.exists():
        return db_path
    return None


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


def get_global_empirica_home() -> Path:
    """
    Get the global Empirica home directory (~/.empirica).

    This is ALWAYS the user's home directory, regardless of project context.
    Used for cross-project data like CRM, global lessons, and credentials.

    Returns:
        Path to ~/.empirica/
    """
    return Path.home() / '.empirica'


# Cache for global config to avoid repeated file reads
_global_config_cache = None


def load_global_config() -> Optional[dict]:
    """
    Load global Empirica config from ~/.empirica/config.yaml.

    Returns:
        Config dict if file exists and is valid YAML, None otherwise.
        Cached after first load.

    Example config structure:
        version: '2.0'
        defaults:
          auto_init_projects: true
        settings:
          auto_checkpoint: true
    """
    global _global_config_cache
    if _global_config_cache is not None:
        return _global_config_cache

    config_path = get_global_empirica_home() / 'config.yaml'
    if not config_path.exists():
        return None

    try:
        import yaml
        with open(config_path, 'r') as f:
            _global_config_cache = yaml.safe_load(f)
            return _global_config_cache
    except Exception as e:
        logger.warning(f"Failed to load global config: {e}")
        return None


def get_crm_db_path() -> Path:
    """
    Get path to global CRM database.

    CRM data (clients, engagements) is cross-project by nature,
    so it always lives in the global home: ~/.empirica/crm/crm.db

    Priority:
    1. EMPIRICA_CRM_DB environment variable
    2. ~/.empirica/crm/crm.db (default)

    Returns:
        Path to crm.db
    """
    # Check environment variable
    if env_db := os.getenv('EMPIRICA_CRM_DB'):
        try:
            db_path = _validate_user_path(env_db, 'EMPIRICA_CRM_DB')
            logger.debug(f"📍 Using EMPIRICA_CRM_DB: {db_path}")
            return db_path
        except ValueError as e:
            logger.warning(f"⚠️  Invalid EMPIRICA_CRM_DB: {e}")

    # Default: global home
    return get_global_empirica_home() / 'crm' / 'crm.db'


def get_client_lessons_dir(client_id: Optional[str] = None) -> Path:
    """
    Get directory for client-scoped lessons (procedural knowledge).

    Args:
        client_id: Optional client UUID. If provided, returns client-specific dir.

    Returns:
        Path to ~/.empirica/lessons/clients/ or ~/.empirica/lessons/clients/{client_id}/
    """
    base = get_global_empirica_home() / 'lessons' / 'clients'
    if client_id:
        return base / client_id
    return base


def ensure_crm_structure() -> None:
    """
    Ensure CRM directory structure exists in global home.
    Creates ~/.empirica/crm/ and ~/.empirica/lessons/clients/
    """
    global_home = get_global_empirica_home()

    # CRM database directory
    (global_home / 'crm').mkdir(parents=True, exist_ok=True)

    # Client lessons directory
    (global_home / 'lessons' / 'clients').mkdir(parents=True, exist_ok=True)

    logger.debug(f"✅ Ensured CRM structure at {global_home}")


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
        'global_home': str(get_global_empirica_home()),
        'crm_db': str(get_crm_db_path()),
        'client_lessons_dir': str(get_client_lessons_dir()),
        'env_vars': {
            'EMPIRICA_DATA_DIR': os.getenv('EMPIRICA_DATA_DIR'),
            'EMPIRICA_SESSION_DB': os.getenv('EMPIRICA_SESSION_DB'),
            'EMPIRICA_CRM_DB': os.getenv('EMPIRICA_CRM_DB')
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
