"""
Git Finding Store - Epistemic Findings in Git Notes

Stores findings in git notes for sync across devices and AI coordination.
Findings are the most valuable epistemic breadcrumbs - learnings, discoveries.

Key Features:
- Store findings in git notes (refs/notes/empirica/findings/<finding-id>)
- Discover findings by project, session, or AI
- Enable cross-device sync via standard git push/pull of notes
- Merge strategy: 'union' (multiple AIs add findings = keep all)
"""

import os
import subprocess
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class GitFindingStore:
    """
    Git-based finding storage for epistemic sync

    Storage Format (git notes):
        refs/notes/empirica/findings/<finding-id>

    Finding Data:
        {
            "finding_id": "uuid",
            "project_id": "project-uuid",
            "session_id": "session-uuid",
            "ai_id": "claude-code",
            "created_at": "2026-01-22T...",
            "finding": "Discovered that X works by Y",
            "impact": 0.8,
            "goal_id": "goal-uuid" (optional),
            "subtask_id": "subtask-uuid" (optional),
            "subject": "optional subject tag",
            "finding_data": {...}  # Full JSON payload
        }
    """

    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize git finding store"""
        self.workspace_root = workspace_root or os.getcwd()
        self._git_available = self._check_git_repo()

    def _check_git_repo(self) -> bool:
        """Check if we're in a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _has_commits(self) -> bool:
        """Check if repo has at least one commit (HEAD exists)"""
        if not self._git_available:
            return False
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def store_finding(
        self,
        finding_id: str,
        project_id: str,
        session_id: str,
        ai_id: str,
        finding: str,
        impact: Optional[float] = None,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        finding_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store finding in git notes

        Args:
            finding_id: Finding UUID
            project_id: Project identifier
            session_id: Session identifier
            ai_id: AI that logged the finding
            finding: The finding text
            impact: Impact score 0.0-1.0
            goal_id: Optional goal reference
            subtask_id: Optional subtask reference
            subject: Optional subject tag
            finding_data: Additional structured data

        Returns:
            bool: Success
        """
        if not self._git_available:
            logger.debug("Not in git repo, skipping finding storage")
            return False

        if not self._has_commits():
            logger.debug("Git repo has no commits yet, skipping finding storage")
            return False

        try:
            # Build finding payload
            payload = {
                'finding_id': finding_id,
                'project_id': project_id,
                'session_id': session_id,
                'ai_id': ai_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'finding': finding,
                'impact': impact,
                'goal_id': goal_id,
                'subtask_id': subtask_id,
                'subject': subject,
                'finding_data': finding_data or {'finding': finding, 'impact': impact}
            }

            # Serialize
            payload_json = json.dumps(payload, indent=2)

            # Get current commit
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = result.stdout.strip()

            # Store in git notes (refs/notes/empirica/findings/<finding-id>)
            note_ref = f'empirica/findings/{finding_id}'
            subprocess.run(
                ['git', 'notes', f'--ref={note_ref}', 'add', '-f', '-m', payload_json, commit_hash],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"✓ Stored finding {finding_id[:8]} in git notes (impact={impact})")
            return True

        except Exception as e:
            logger.warning(f"Failed to store finding in git: {e}")
            return False

    def load_finding(self, finding_id: str) -> Optional[Dict[str, Any]]:
        """
        Load finding from git notes

        Args:
            finding_id: Finding UUID

        Returns:
            Dict: Finding payload or None
        """
        if not self._git_available:
            return None

        if not self._has_commits():
            return None

        try:
            note_ref = f'empirica/findings/{finding_id}'

            # Get current commit
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = result.stdout.strip()

            # Load note
            result = subprocess.run(
                ['git', 'notes', f'--ref={note_ref}', 'show', commit_hash],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return None

            return json.loads(result.stdout)

        except Exception as e:
            logger.warning(f"Failed to load finding from git: {e}")
            return None

    def discover_findings(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ai_id: Optional[str] = None,
        min_impact: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover findings from git notes

        Args:
            project_id: Filter by project
            session_id: Filter by session
            ai_id: Filter by AI
            min_impact: Minimum impact threshold

        Returns:
            List[Dict]: Matching findings
        """
        if not self._git_available:
            return []

        try:
            # List all finding note refs
            result = subprocess.run(
                ['git', 'for-each-ref', 'refs/notes/empirica/findings/'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return []

            findings = []

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) < 2:
                    continue

                ref = parts[1]
                if not ref.startswith('refs/notes/empirica/findings/'):
                    continue

                finding_id = ref.split('/')[-1]
                finding_data = self.load_finding(finding_id)

                if not finding_data:
                    continue

                # Apply filters
                if project_id and finding_data.get('project_id') != project_id:
                    continue
                if session_id and finding_data.get('session_id') != session_id:
                    continue
                if ai_id and finding_data.get('ai_id') != ai_id:
                    continue
                if min_impact and (finding_data.get('impact') or 0) < min_impact:
                    continue

                findings.append(finding_data)

            # Sort by impact (highest first)
            findings.sort(key=lambda f: f.get('impact') or 0, reverse=True)

            return findings

        except Exception as e:
            logger.warning(f"Failed to discover findings: {e}")
            return []

    def count_findings(self) -> int:
        """Count total findings in git notes"""
        if not self._git_available:
            return 0

        try:
            result = subprocess.run(
                ['git', 'for-each-ref', '--count', 'refs/notes/empirica/findings/'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            # Count lines in output
            if result.returncode == 0 and result.stdout.strip():
                return len(result.stdout.strip().split('\n'))
            return 0

        except Exception:
            return 0
