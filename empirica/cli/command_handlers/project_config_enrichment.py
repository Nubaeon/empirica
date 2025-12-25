"""
Project Config Enrichment - Auto-update PROJECT_CONFIG.yaml with learnings

As users work and log findings/unknowns, automatically enrich the
PROJECT_CONFIG.yaml to build intelligence over time.
"""

import logging
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def find_project_config(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find .empirica-project/PROJECT_CONFIG.yaml by walking up directory tree.
    
    Args:
        start_path: Where to start searching (defaults to cwd)
        
    Returns:
        Path to PROJECT_CONFIG.yaml or None if not found
    """
    current = start_path or Path.cwd()
    
    # Walk up directory tree looking for .empirica-project/
    for parent in [current] + list(current.parents):
        config_path = parent / '.empirica-project' / 'PROJECT_CONFIG.yaml'
        if config_path.exists():
            return config_path
    
    return None


def load_project_config(config_path: Path) -> Dict[str, Any]:
    """Load PROJECT_CONFIG.yaml"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


def save_project_config(config_path: Path, config: Dict[str, Any]):
    """Save PROJECT_CONFIG.yaml with formatting"""
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        logger.error(f"Error saving config: {e}")


def enrich_with_finding(finding: str, session_id: Optional[str] = None) -> bool:
    """
    Add finding to PROJECT_CONFIG.yaml in current project.
    
    Args:
        finding: The finding to add
        session_id: Optional session ID for provenance
        
    Returns:
        True if enrichment successful
    """
    config_path = find_project_config()
    if not config_path:
        logger.debug("No PROJECT_CONFIG.yaml found in tree")
        return False
    
    config = load_project_config(config_path)
    
    # Ensure bootstrap section exists
    if 'bootstrap' not in config:
        config['bootstrap'] = {}
    
    # Ensure key_discoveries exists
    if 'key_discoveries' not in config['bootstrap']:
        config['bootstrap']['key_discoveries'] = []
    
    # Add finding with timestamp
    entry = {
        'finding': finding,
        'timestamp': datetime.now().isoformat(),
    }
    if session_id:
        entry['session_id'] = session_id
    
    config['bootstrap']['key_discoveries'].append(entry)
    
    # Keep last 20 findings (prevent bloat)
    config['bootstrap']['key_discoveries'] = config['bootstrap']['key_discoveries'][-20:]
    
    save_project_config(config_path, config)
    logger.info(f"Enriched PROJECT_CONFIG with finding: {finding[:50]}...")
    return True


def enrich_with_unknown(unknown: str, session_id: Optional[str] = None) -> bool:
    """
    Add unknown to PROJECT_CONFIG.yaml in current project.
    
    Args:
        unknown: The unknown/challenge to add
        session_id: Optional session ID for provenance
        
    Returns:
        True if enrichment successful
    """
    config_path = find_project_config()
    if not config_path:
        logger.debug("No PROJECT_CONFIG.yaml found in tree")
        return False
    
    config = load_project_config(config_path)
    
    # Ensure bootstrap section exists
    if 'bootstrap' not in config:
        config['bootstrap'] = {}
    
    # Ensure current_challenges exists
    if 'current_challenges' not in config['bootstrap']:
        config['bootstrap']['current_challenges'] = []
    
    # Add unknown with timestamp
    entry = {
        'challenge': unknown,
        'timestamp': datetime.now().isoformat(),
        'resolved': False
    }
    if session_id:
        entry['session_id'] = session_id
    
    config['bootstrap']['current_challenges'].append(entry)
    
    # Keep last 15 challenges
    config['bootstrap']['current_challenges'] = config['bootstrap']['current_challenges'][-15:]
    
    save_project_config(config_path, config)
    logger.info(f"Enriched PROJECT_CONFIG with unknown: {unknown[:50]}...")
    return True


def enrich_with_dead_end(approach: str, why_failed: str, session_id: Optional[str] = None) -> bool:
    """
    Add dead end to PROJECT_CONFIG.yaml in current project.
    
    Args:
        approach: What was tried
        why_failed: Why it didn't work
        session_id: Optional session ID for provenance
        
    Returns:
        True if enrichment successful
    """
    config_path = find_project_config()
    if not config_path:
        logger.debug("No PROJECT_CONFIG.yaml found in tree")
        return False
    
    config = load_project_config(config_path)
    
    # Ensure bootstrap section exists
    if 'bootstrap' not in config:
        config['bootstrap'] = {}
    
    # Ensure dead_ends exists
    if 'dead_ends' not in config['bootstrap']:
        config['bootstrap']['dead_ends'] = []
    
    # Add dead end with timestamp
    entry = {
        'approach': approach,
        'why_failed': why_failed,
        'timestamp': datetime.now().isoformat()
    }
    if session_id:
        entry['session_id'] = session_id
    
    config['bootstrap']['dead_ends'].append(entry)
    
    # Keep last 10 dead ends
    config['bootstrap']['dead_ends'] = config['bootstrap']['dead_ends'][-10:]
    
    save_project_config(config_path, config)
    logger.info(f"Enriched PROJECT_CONFIG with dead end: {approach[:50]}...")
    return True


def get_recent_learnings(limit: int = 5) -> Dict[str, List]:
    """
    Get recent learnings from PROJECT_CONFIG.yaml for display.
    
    Args:
        limit: Max items per category
        
    Returns:
        Dict with findings, challenges, dead_ends
    """
    config_path = find_project_config()
    if not config_path:
        return {'findings': [], 'challenges': [], 'dead_ends': []}
    
    config = load_project_config(config_path)
    bootstrap = config.get('bootstrap', {})
    
    return {
        'findings': bootstrap.get('key_discoveries', [])[-limit:],
        'challenges': [c for c in bootstrap.get('current_challenges', []) if not c.get('resolved', False)][-limit:],
        'dead_ends': bootstrap.get('dead_ends', [])[-limit:]
    }
