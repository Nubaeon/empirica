"""
Stability Estimator

Analyzes git history to assess component stability and change patterns.

Metrics:
- Commit frequency: How often the file changes
- Churn rate: Lines added/removed relative to size
- Author diversity: Bus factor, knowledge concentration
- Hotspot score: Frequency * complexity (high = risky)
- Maintenance ratio: Bug fixes / total commits

Maps to vectors:
- change: Stability (low change = stable, reliable)
- engagement: Activity level (recent development attention)
- signal: Meaningful changes (bug fixes, features) vs noise (formatting)
"""

import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .schema import StabilityMetrics


@dataclass
class CommitInfo:
    """Parsed git commit information."""
    hash: str
    author: str
    date: datetime
    message: str
    lines_added: int = 0
    lines_removed: int = 0


class StabilityEstimator:
    """Analyzes git history for stability metrics."""

    def __init__(self, project_root: str):
        """
        Initialize estimator.

        Args:
            project_root: Root directory of the git repository
        """
        self.project_root = Path(project_root)
        self._is_git_repo = self._check_git_repo()

    def _check_git_repo(self) -> bool:
        """Verify this is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def analyze(self, component_path: str) -> StabilityMetrics:
        """
        Analyze stability metrics for a component.

        Args:
            component_path: Path to file or directory

        Returns:
            StabilityMetrics with git history analysis
        """
        metrics = StabilityMetrics()

        if not self._is_git_repo:
            return metrics

        path = Path(component_path)
        if not path.is_absolute():
            path = self.project_root / component_path

        # Get relative path for git commands
        try:
            rel_path = path.relative_to(self.project_root)
        except ValueError:
            return metrics

        # Gather commit history
        commits = self._get_commits(str(rel_path))
        if not commits:
            return metrics

        metrics.total_commits = len(commits)

        # Recent activity (last 30 days)
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        recent = [c for c in commits if c.date > thirty_days_ago]
        metrics.recent_commits_30d = len(recent)

        # Unique authors
        authors = set(c.author for c in commits)
        metrics.unique_authors = len(authors)

        # Lines per commit
        total_changes = sum(c.lines_added + c.lines_removed for c in commits)
        if commits:
            metrics.avg_lines_per_commit = total_changes / len(commits)

        # Churn rate
        file_size = self._get_file_size(path)
        if file_size > 0:
            metrics.churn_rate = total_changes / file_size

        # Time-based metrics
        if commits:
            oldest = min(c.date for c in commits)
            newest = max(c.date for c in commits)
            metrics.age_days = (now - oldest).days
            metrics.days_since_last_change = (now - newest).days

        # Maintenance ratio (bug fixes vs total)
        bug_fix_patterns = ['fix', 'bug', 'patch', 'hotfix', 'repair']
        bug_fixes = sum(
            1 for c in commits
            if any(p in c.message.lower() for p in bug_fix_patterns)
        )
        if commits:
            metrics.maintenance_ratio = bug_fixes / len(commits)

        # Hotspot score: frequency * size (complexity proxy)
        # High score = frequently changed AND large = risky
        frequency = metrics.total_commits / max(metrics.age_days, 1) * 30  # Normalize to monthly
        complexity_proxy = file_size / 100  # 100 lines = complexity 1.0
        metrics.hotspot_score = min(frequency * complexity_proxy, 10.0)  # Cap at 10

        return metrics

    def _get_commits(self, rel_path: str) -> List[CommitInfo]:
        """Get commit history for a path."""
        try:
            # Get commit list with stats
            result = subprocess.run(
                [
                    "git", "log",
                    "--format=%H|%an|%aI|%s",
                    "--numstat",
                    "--follow",
                    "--", rel_path
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return []

            return self._parse_git_log(result.stdout)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _parse_git_log(self, output: str) -> List[CommitInfo]:
        """Parse git log output into CommitInfo objects."""
        commits = []
        current_commit = None

        for line in output.strip().split('\n'):
            if not line:
                continue

            # Check if this is a commit header line
            if '|' in line and len(line.split('|')) == 4:
                parts = line.split('|')
                try:
                    current_commit = CommitInfo(
                        hash=parts[0],
                        author=parts[1],
                        date=datetime.fromisoformat(parts[2].replace('Z', '+00:00')),
                        message=parts[3],
                    )
                    commits.append(current_commit)
                except (ValueError, IndexError):
                    continue

            # Check if this is a numstat line (added, removed, filename)
            elif current_commit and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        removed = int(parts[1]) if parts[1] != '-' else 0
                        current_commit.lines_added += added
                        current_commit.lines_removed += removed
                    except ValueError:
                        pass

        return commits

    def _get_file_size(self, path: Path) -> int:
        """Get file size in lines."""
        if path.is_dir():
            total = 0
            for py_file in path.rglob("*.py"):
                try:
                    total += len(py_file.read_text().splitlines())
                except (OSError, UnicodeDecodeError):
                    pass
            return total
        else:
            try:
                return len(path.read_text().splitlines())
            except (OSError, UnicodeDecodeError):
                return 0

    def get_authors(self, component_path: str) -> List[Tuple[str, int]]:
        """
        Get authors and their commit counts.

        Returns:
            List of (author_name, commit_count) sorted by count desc
        """
        path = Path(component_path)
        if not path.is_absolute():
            path = self.project_root / component_path

        try:
            rel_path = path.relative_to(self.project_root)
        except ValueError:
            return []

        commits = self._get_commits(str(rel_path))
        author_counts: Dict[str, int] = {}

        for commit in commits:
            author_counts[commit.author] = author_counts.get(commit.author, 0) + 1

        return sorted(author_counts.items(), key=lambda x: x[1], reverse=True)

    def to_vectors(self, metrics: StabilityMetrics) -> Dict[str, float]:
        """
        Convert stability metrics to epistemic vectors.

        Returns:
            Dict with 'change', 'engagement', 'signal' vectors
        """
        # Change: Inverse of churn (low churn = stable = good)
        # Normalize: >2.0 churn rate = very unstable
        change_raw = min(metrics.churn_rate / 2.0, 1.0)
        change = change_raw  # HIGH change = HIGH instability = risky

        # Engagement: Recent activity (some is good, none is concerning)
        if metrics.recent_commits_30d == 0:
            engagement = 0.3  # Dormant, might be stable OR abandoned
        elif metrics.recent_commits_30d > 10:
            engagement = 1.0  # Very active
        else:
            engagement = 0.3 + (metrics.recent_commits_30d / 10) * 0.7

        # Signal: Maintenance ratio indicates meaningful work
        # 20-50% bug fixes is healthy (some maintenance, some features)
        if 0.2 <= metrics.maintenance_ratio <= 0.5:
            signal = 1.0
        elif metrics.maintenance_ratio > 0.5:
            # Too many bug fixes = technical debt
            signal = 0.5
        else:
            # Very few bug fixes = either clean OR ignoring issues
            signal = 0.7

        return {
            'change': change,
            'engagement': engagement,
            'signal': signal,
        }
