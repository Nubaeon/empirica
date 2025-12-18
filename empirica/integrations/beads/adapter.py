"""
BEADS Adapter - Subprocess-based integration with bd CLI

Provides Python interface to BEADS issue tracker via subprocess calls.
All methods gracefully handle missing bd CLI (returns None/empty).
"""

import subprocess
import json
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class BeadsAdapter:
    """Subprocess-based BEADS integration"""
    
    def __init__(self):
        self._available = None  # Cache availability check
    
    def is_available(self) -> bool:
        """Check if bd CLI is installed and working"""
        if self._available is not None:
            return self._available
        
        try:
            result = subprocess.run(
                ['bd', '--version'],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            self._available = True
            logger.debug(f"BEADS available: {result.stdout.strip()}")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self._available = False
            logger.debug(f"BEADS not available: {e}")
            return False
    
    def create_issue(
        self,
        title: str,
        description: str = "",
        priority: int = 2,
        issue_type: str = "task",
        labels: Optional[List[str]] = None
    ) -> Optional[str]:
        """Create BEADS issue, return hash ID (e.g., bd-a1b2)
        
        Args:
            title: Issue title (required)
            description: Issue description (optional)
            priority: Priority 1-3 (1=high, 2=medium, 3=low)
            issue_type: task, feature, bug, epic
            labels: Optional labels list
        
        Returns:
            BEADS issue ID (e.g., "bd-a1b2") or None if bd not available
        """
        if not self.is_available():
            logger.warning("BEADS not available - cannot create issue")
            return None
        
        try:
            cmd = ['bd', 'create', title, '-p', str(priority), '-t', issue_type, '--json']
            
            if description:
                cmd.extend(['-d', description])
            
            if labels:
                cmd.extend(['-l', ','.join(labels)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            issue = json.loads(result.stdout)
            issue_id = issue.get('id')
            
            logger.info(f"Created BEADS issue: {issue_id} - {title}")
            return issue_id
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"Failed to create BEADS issue: {e}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse BEADS response: {e}")
            return None
    
    def add_dependency(
        self,
        child_id: str,
        parent_id: str,
        dep_type: str = 'blocks'
    ) -> bool:
        """Add dependency between BEADS issues
        
        Args:
            child_id: Child issue ID
            parent_id: Parent issue ID
            dep_type: Dependency type (blocks, related, discovered-from)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            subprocess.run(
                ['bd', 'dep', 'add', child_id, parent_id, '--type', dep_type],
                capture_output=True,
                check=True,
                timeout=10
            )
            logger.info(f"Added dependency: {child_id} {dep_type} {parent_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add dependency: {e.stderr}")
            return False
    
    def get_ready_work(self, limit: int = 10, priority: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get ready work from BEADS (issues with no open blockers)
        
        Args:
            limit: Maximum number of issues to return
            priority: Filter by priority (1, 2, or 3)
        
        Returns:
            List of issue dicts or empty list if not available
        """
        if not self.is_available():
            return []
        
        try:
            cmd = ['bd', 'ready', '--json', '--limit', str(limit)]
            
            if priority is not None:
                cmd.extend(['--priority', str(priority)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            issues = json.loads(result.stdout)
            logger.debug(f"Found {len(issues)} ready issues")
            return issues if isinstance(issues, list) else []
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get ready work: {e.stderr}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ready work response: {e}")
            return []
    
    def update_status(self, issue_id: str, status: str) -> bool:
        """Update BEADS issue status
        
        Args:
            issue_id: BEADS issue ID
            status: Status (open, in_progress, blocked, closed)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            subprocess.run(
                ['bd', 'update', issue_id, '--status', status],
                capture_output=True,
                check=True,
                timeout=10
            )
            logger.info(f"Updated {issue_id} status to {status}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update status: {e.stderr}")
            return False
    
    def close_issue(self, issue_id: str, reason: str = "Completed") -> bool:
        """Close BEADS issue
        
        Args:
            issue_id: BEADS issue ID
            reason: Close reason (optional)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            subprocess.run(
                ['bd', 'close', issue_id, '--reason', reason],
                capture_output=True,
                check=True,
                timeout=10
            )
            logger.info(f"Closed {issue_id}: {reason}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to close issue: {e.stderr}")
            return False
    
    def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get BEADS issue details
        
        Args:
            issue_id: BEADS issue ID
        
        Returns:
            Issue dict or None if not found/not available
        """
        if not self.is_available():
            return None
        
        try:
            result = subprocess.run(
                ['bd', 'show', issue_id, '--json'],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            issue = json.loads(result.stdout)
            return issue
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get issue {issue_id}: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse issue response: {e}")
            return None
    
    def get_dependency_tree(self, issue_id: str) -> Optional[str]:
        """Get dependency tree for an issue (ASCII tree output)
        
        Args:
            issue_id: BEADS issue ID
        
        Returns:
            ASCII tree string or None if not available
        """
        if not self.is_available():
            return None
        
        try:
            result = subprocess.run(
                ['bd', 'dep', 'tree', issue_id],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get dependency tree: {e.stderr}")
            return None
