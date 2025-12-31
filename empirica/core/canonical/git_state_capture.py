"""
Git State Capture Module

Captures git repository state at checkpoint time for epistemic correlation.
Enables attribution analysis - correlating code changes to knowledge changes.

Part of the GitEnhancedReflexLogger refactoring (extracted from 1,156 line file).
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .git_enhanced_reflex_logger import GitEnhancedReflexLogger

logger = logging.getLogger(__name__)


class GitStateCapture:
    """
    Captures git repository state for epistemic checkpoints.

    Provides:
    - HEAD commit tracking
    - Commits since last checkpoint
    - Uncommitted changes detection
    """

    def __init__(self, git_repo_path: Path):
        """
        Initialize git state capture.

        Args:
            git_repo_path: Path to git repository
        """
        self.git_repo_path = git_repo_path

    def capture_state(self, get_last_checkpoint_fn: Optional[callable] = None) -> Dict[str, Any]:
        """
        Capture current git state at checkpoint time.

        Enables correlation of epistemic deltas to code changes.

        Args:
            get_last_checkpoint_fn: Optional function to get last checkpoint (for commit diff)

        Returns:
            Dictionary containing:
            - head_commit: Current HEAD SHA
            - commits_since_last_checkpoint: List of commits since last checkpoint
            - uncommitted_changes: Working directory changes
        """
        try:
            # Get HEAD commit SHA
            head_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.git_repo_path,
                timeout=5
            )

            if head_result.returncode != 0:
                logger.warning("Failed to get HEAD commit")
                return {}

            head_commit = head_result.stdout.strip()

            # Get commits since last checkpoint
            commits_since_last = []
            if get_last_checkpoint_fn:
                commits_since_last = self._get_commits_since_last_checkpoint(get_last_checkpoint_fn)

            # Get uncommitted changes
            uncommitted_changes = self._get_uncommitted_changes()

            return {
                "head_commit": head_commit,
                "commits_since_last_checkpoint": commits_since_last,
                "uncommitted_changes": uncommitted_changes
            }

        except Exception as e:
            logger.warning(f"Failed to capture git state: {e}")
            return {}

    def _get_commits_since_last_checkpoint(
        self,
        get_last_checkpoint_fn: callable
    ) -> List[Dict[str, Any]]:
        """
        Get commits made since last checkpoint.

        Args:
            get_last_checkpoint_fn: Function to retrieve last checkpoint

        Returns:
            List of commit dictionaries with sha, message, author, timestamp, files_changed
        """
        try:
            # Get last checkpoint to find timestamp
            last_checkpoint = get_last_checkpoint_fn()
            if not last_checkpoint:
                return []

            since_time = last_checkpoint.get('timestamp')
            if not since_time:
                return []

            # Get commits since last checkpoint timestamp
            log_result = subprocess.run(
                ["git", "log", f"--since={since_time}", "--format=%H|%s|%an|%aI", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.git_repo_path,
                timeout=10
            )

            if log_result.returncode != 0:
                return []

            commits = []
            for line in log_result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 3)
                if len(parts) < 4:
                    continue

                sha, message, author, timestamp = parts

                # Get files changed in this commit
                files_result = subprocess.run(
                    ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
                    capture_output=True,
                    text=True,
                    cwd=self.git_repo_path,
                    timeout=5
                )

                files_changed = [f for f in files_result.stdout.strip().split('\n') if f]

                commits.append({
                    "sha": sha,
                    "message": message,
                    "author": author,
                    "timestamp": timestamp,
                    "files_changed": files_changed
                })

            return commits

        except Exception as e:
            logger.warning(f"Failed to get commits since last checkpoint: {e}")
            return []

    def _get_uncommitted_changes(self) -> Dict[str, Any]:
        """
        Get uncommitted working directory changes.

        Returns:
            Dictionary with files_modified, files_added, files_deleted, diff_stat
        """
        try:
            # Get status (porcelain format for easy parsing)
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.git_repo_path,
                timeout=5
            )

            if status_result.returncode != 0:
                return {}

            modified = []
            added = []
            deleted = []

            for line in status_result.stdout.split('\n'):
                if not line:
                    continue

                status = line[:2]
                filepath = line[3:] if len(line) > 3 else ""

                if 'M' in status:
                    modified.append(filepath)
                elif 'A' in status:
                    added.append(filepath)
                elif 'D' in status:
                    deleted.append(filepath)

            # Get diff stats
            diff_result = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True,
                text=True,
                cwd=self.git_repo_path,
                timeout=5
            )

            diff_stat = diff_result.stdout.strip() if diff_result.returncode == 0 else ""

            return {
                "files_modified": modified,
                "files_added": added,
                "files_deleted": deleted,
                "diff_stat": diff_stat
            }

        except Exception as e:
            logger.warning(f"Failed to get uncommitted changes: {e}")
            return {}
