"""
Project Configuration Loader

Loads .empirica/project.yaml configuration including subject definitions
and path mappings for context filtering.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ProjectConfig:
    """Project configuration with subject mappings"""
    
    def __init__(self, config_data: Dict[str, Any]) -> None:
        """Initialize project config from configuration dictionary."""
        self.project_id = config_data.get('project_id')
        self.name = config_data.get('name', 'Unknown Project')
        self.description = config_data.get('description', '')
        self.subjects = config_data.get('subjects', {})
        self.default_subject = config_data.get('default_subject')
        self.auto_detect = config_data.get('auto_detect', {'enabled': True, 'method': 'path_match'})

        # BEADS integration settings
        self.beads = config_data.get('beads', {})
        self.default_use_beads = self.beads.get('default_enabled', False)
    
    def get_subject_for_path(self, current_path: str) -> Optional[str]:
        """
        Detect subject from current working directory.
        
        Args:
            current_path: Current working directory
            
        Returns:
            subject_id if matched, None otherwise
        """
        if not self.auto_detect.get('enabled', True):
            return None
        
        current_path = Path(current_path).resolve()
        
        # Try to match current path to subject paths
        for subject_id, subject_config in self.subjects.items():
            for path_pattern in subject_config.get('paths', []):
                # Convert to absolute path
                subject_path = Path(path_pattern).resolve()
                
                # Check if current path is within subject path
                try:
                    current_path.relative_to(subject_path)
                    logger.info(f"Auto-detected subject: {subject_id} (matched {path_pattern})")
                    return subject_id
                except ValueError:
                    # Not a subpath, continue
                    continue
        
        logger.debug(f"No subject auto-detected for path: {current_path}")
        return None
    
    def get_subject_info(self, subject_id: str) -> Optional[Dict[str, Any]]:
        """Get subject configuration"""
        return self.subjects.get(subject_id)
    
    def list_subjects(self) -> List[str]:
        """List all subject IDs"""
        return list(self.subjects.keys())


def load_project_config(project_root: Optional[Path] = None) -> Optional[ProjectConfig]:
    """
    Load project configuration from .empirica/project.yaml
    
    Args:
        project_root: Root directory of project (defaults to current directory)
        
    Returns:
        ProjectConfig if found, None otherwise
    """
    if project_root is None:
        project_root = Path.cwd()
    
    config_path = project_root / '.empirica' / 'project.yaml'
    
    if not config_path.exists():
        logger.debug(f"No project config found at {config_path}")
        return None
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        logger.info(f"Loaded project config: {config_data.get('name', 'Unknown')}")
        return ProjectConfig(config_data)
    
    except Exception as e:
        logger.error(f"Failed to load project config from {config_path}: {e}")
        return None


def get_current_subject(project_config: Optional[ProjectConfig] = None, 
                       current_path: Optional[Path] = None) -> Optional[str]:
    """
    Get current subject based on working directory.
    
    Args:
        project_config: Project configuration (loads if None)
        current_path: Current working directory (uses cwd if None)
        
    Returns:
        subject_id if detected, None otherwise
    """
    if project_config is None:
        project_config = load_project_config()
    
    if project_config is None:
        return None
    
    if current_path is None:
        current_path = Path.cwd()
    
    return project_config.get_subject_for_path(str(current_path))
