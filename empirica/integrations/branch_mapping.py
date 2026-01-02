"""
Branch Mapping - Links Goals to Git Branches

Manages the .empirica/branch_mapping.json file that tracks which git branches
are associated with which goals/BEADS issues.

This enables:
- goals-claim to create and link branches
- goals-complete to merge and clean up branches
- Multi-AI coordination via branch awareness
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timezone


class BranchMapping:
    """Manages branch-to-goal mapping in .empirica/branch_mapping.json"""
    
    def __init__(self, repo_root: Optional[str] = None):
        """
        Initialize branch mapping manager.
        
        Args:
            repo_root: Git repository root. If None, searches from cwd.
        """
        if repo_root is None:
            repo_root = self._find_repo_root()
        
        self.repo_root = Path(repo_root)
        self.empirica_dir = self.repo_root / ".empirica"
        self.mapping_file = self.empirica_dir / "branch_mapping.json"
        
        # Ensure .empirica directory exists
        self.empirica_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing mappings
        self._mappings = self._load_mappings()
    
    def _find_repo_root(self) -> str:
        """Find git repository root from current directory."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return str(current)
            current = current.parent
        raise RuntimeError("Not in a git repository")
    
    def _load_mappings(self) -> Dict:
        """Load mappings from file."""
        if not self.mapping_file.exists():
            return {"mappings": {}, "history": []}
        
        try:
            with open(self.mapping_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Corrupt file, start fresh
            return {"mappings": {}, "history": []}
    
    def _save_mappings(self):
        """Save mappings to file."""
        with open(self.mapping_file, 'w') as f:
            json.dump(self._mappings, f, indent=2)
    
    def add_mapping(
        self,
        branch_name: str,
        goal_id: str,
        beads_issue_id: Optional[str] = None,
        ai_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Add a branch-to-goal mapping.
        
        Args:
            branch_name: Git branch name
            goal_id: Empirica goal UUID
            beads_issue_id: Optional BEADS issue ID
            ai_id: Optional AI identifier
            session_id: Optional session UUID
            
        Returns:
            True if mapping added, False if branch already mapped
        """
        if branch_name in self._mappings["mappings"]:
            return False  # Branch already mapped
        
        self._mappings["mappings"][branch_name] = {
            "goal_id": goal_id,
            "beads_issue_id": beads_issue_id,
            "ai_id": ai_id,
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat() + "Z",
            "status": "active"
        }
        
        self._save_mappings()
        return True
    
    def get_mapping(self, branch_name: str) -> Optional[Dict]:
        """Get mapping for a branch."""
        return self._mappings["mappings"].get(branch_name)
    
    def get_branch_for_goal(self, goal_id: str) -> Optional[str]:
        """Find branch associated with a goal."""
        for branch, mapping in self._mappings["mappings"].items():
            if mapping["goal_id"] == goal_id and mapping["status"] == "active":
                return branch
        return None
    
    def remove_mapping(self, branch_name: str, archive: bool = True) -> bool:
        """
        Remove a branch mapping.
        
        Args:
            branch_name: Branch to remove
            archive: If True, moves to history instead of deleting
            
        Returns:
            True if removed, False if not found
        """
        if branch_name not in self._mappings["mappings"]:
            return False
        
        if archive:
            # Move to history
            mapping = self._mappings["mappings"][branch_name]
            mapping["completed_at"] = datetime.now(timezone.utc).isoformat() + "Z"
            mapping["status"] = "completed"
            self._mappings["history"].append({
                "branch": branch_name,
                **mapping
            })
        
        # Remove from active mappings
        del self._mappings["mappings"][branch_name]
        self._save_mappings()
        return True
    
    def list_active_mappings(self) -> List[Dict]:
        """List all active branch mappings."""
        return [
            {"branch": branch, **mapping}
            for branch, mapping in self._mappings["mappings"].items()
            if mapping["status"] == "active"
        ]
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get branch mapping history."""
        return self._mappings["history"][-limit:]


def get_branch_mapping(repo_root: Optional[str] = None) -> BranchMapping:
    """
    Get branch mapping instance.
    
    Args:
        repo_root: Optional git repository root
        
    Returns:
        BranchMapping instance
    """
    return BranchMapping(repo_root=repo_root)
