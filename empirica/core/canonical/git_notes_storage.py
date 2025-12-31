"""
Git Notes Storage Module

Handles reading and writing epistemic checkpoints to git notes.
Uses hierarchical namespace: refs/notes/empirica/session/{session_id}/{phase}/{round}

Part of the GitEnhancedReflexLogger refactoring (extracted from 1,156 line file).
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from empirica.core.git_ops.signed_operations import SignedGitOperations
from empirica.core.persona.signing_persona import SigningPersona

logger = logging.getLogger(__name__)


class GitNotesStorage:
    """
    Git notes storage for epistemic checkpoints.

    Provides:
    - Hierarchical namespace per session/phase/round
    - Optional cryptographic signing via SigningPersona
    - Checkpoint retrieval with phase filtering
    """

    def __init__(
        self,
        session_id: str,
        git_repo_path: Path,
        signing_persona: Optional[SigningPersona] = None
    ):
        """
        Initialize git notes storage.

        Args:
            session_id: Session identifier
            git_repo_path: Path to git repository
            signing_persona: Optional SigningPersona for signed commits
        """
        self.session_id = session_id
        self.git_repo_path = git_repo_path
        self.signing_persona = signing_persona
        self.signed_git_ops: Optional[SignedGitOperations] = None

        # Initialize signed git operations if persona provided
        if signing_persona:
            try:
                self.signed_git_ops = SignedGitOperations(repo_path=str(git_repo_path))
            except Exception as e:
                logger.warning(f"Failed to initialize SignedGitOperations: {e}")

    def add_note(self, checkpoint: Dict[str, Any]) -> Optional[str]:
        """
        Add checkpoint to git notes with session-specific namespace.

        Uses session-specific git notes refs to prevent agent collisions:
        - empirica/session/<session_id>/<phase>/<round> for individual checkpoints

        Args:
            checkpoint: Checkpoint dictionary

        Returns:
            Note SHA if successful, None if failed
        """
        try:
            # Validate JSON serialization
            checkpoint_json = json.dumps(checkpoint)
            json.loads(checkpoint_json)  # Validate it's parseable

            # Create unique notes ref using phase/round to prevent overwrites
            phase = checkpoint.get('phase', 'UNKNOWN')
            round_num = checkpoint.get('round', 1)
            note_ref = f"empirica/session/{self.session_id}/{phase}/{round_num}"

            # Add note to HEAD commit with unique ref per checkpoint
            # Use stdin (-F -) to avoid "Argument list too long" errors
            result = subprocess.run(
                ["git", "notes", "--ref", note_ref, "add", "-f", "-F", "-", "HEAD"],
                input=checkpoint_json,
                capture_output=True,
                timeout=5,
                cwd=self.git_repo_path,
                text=True
            )

            if result.returncode != 0:
                logger.warning(
                    f"Failed to add session-specific git note (ref={note_ref}): {result.stderr}. "
                    f"Fallback storage available."
                )
                return None

            # Get note SHA from session-specific ref
            result = subprocess.run(
                ["git", "notes", "--ref", note_ref, "list", "HEAD"],
                capture_output=True,
                timeout=2,
                cwd=self.git_repo_path,
                text=True
            )

            note_sha = result.stdout.strip().split()[0] if result.stdout else None
            logger.info(f"Session-specific git checkpoint added: {note_sha} (session={self.session_id}, phase={phase})")

            return note_sha

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.warning(f"Git note operation failed: {e}. Using fallback storage.")
            return None

    def add_signed_note(self, checkpoint: Dict[str, Any], phase: str) -> Optional[str]:
        """
        Add cryptographically signed checkpoint to git notes.

        Uses SignedGitOperations to:
        1. Sign epistemic state with persona's Ed25519 key
        2. Store signed state in hierarchical git notes
        3. Enable verification chain for audit trail

        Args:
            checkpoint: Checkpoint dictionary (includes vectors, noema, etc.)
            phase: CASCADE phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)

        Returns:
            Commit SHA if successful, None if failed
        """
        try:
            if not self.signed_git_ops or not self.signing_persona:
                logger.debug("Signed operations not available, falling back to unsigned")
                return self.add_note(checkpoint)

            # Extract epistemic state from checkpoint
            epistemic_state = checkpoint.get("vectors", {})

            # Prepare additional data for signing
            additional_data = {
                "session_id": self.session_id,
                "round": checkpoint.get("round", 1),
                "git_state": checkpoint.get("git_state"),
                "learning_delta": checkpoint.get("learning_delta"),
                "epistemic_tags": checkpoint.get("epistemic_tags"),
                "noema": checkpoint.get("noema")
            }

            # Sign and commit state
            commit_sha = self.signed_git_ops.commit_signed_state(
                signing_persona=self.signing_persona,
                epistemic_state=epistemic_state,
                phase=phase,
                message=f"Checkpoint round {checkpoint.get('round', 1)}",
                additional_data=additional_data
            )

            # Also store in hierarchical git notes namespace for semantic queries
            checkpoint_json = json.dumps(checkpoint)
            round_num = checkpoint.get("round", 1)
            note_ref = f"empirica/session/{self.session_id}/noema/{phase}/{round_num}"

            # Add noema-specific note ref
            result = subprocess.run(
                ["git", "notes", "--ref", note_ref, "add", "-f", "-F", "-", "HEAD"],
                input=checkpoint_json,
                capture_output=True,
                timeout=5,
                cwd=self.git_repo_path,
                text=True
            )

            if result.returncode != 0:
                logger.warning(
                    f"Failed to add noema-specific git note (ref={note_ref}): {result.stderr}"
                )

            logger.info(
                f"Signed checkpoint committed: {commit_sha[:7]} "
                f"(session={self.session_id}, phase={phase}, persona={self.signing_persona.persona_id})"
            )

            return commit_sha

        except Exception as e:
            logger.warning(f"Failed to add signed git note: {e}. Falling back to unsigned.")
            return self.add_note(checkpoint)

    def get_latest_note(self, phase: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve most recent checkpoint from hierarchical git notes structure.

        Args:
            phase: Filter by phase (optional)

        Returns:
            Checkpoint dictionary or None
        """
        try:
            # Search for the most recent checkpoint across rounds and phases
            phases_to_check = ["POSTFLIGHT", "ACT", "CHECK", "INVESTIGATE", "PLAN", "THINK", "PREFLIGHT"]
            if phase:
                phases_to_check = [phase]

            # Start checking from the highest round numbers downwards
            for round_num in range(10, 0, -1):
                for ph in phases_to_check:
                    note_ref = f"empirica/session/{self.session_id}/{ph}/{round_num}"

                    result = subprocess.run(
                        ["git", "notes", "--ref", note_ref, "show", "HEAD"],
                        capture_output=True,
                        timeout=2,
                        cwd=self.git_repo_path,
                        text=True
                    )

                    if result.returncode == 0:
                        checkpoint = json.loads(result.stdout)

                        if checkpoint.get("session_id") != self.session_id:
                            logger.warning(f"Session ID mismatch: {checkpoint.get('session_id')} vs {self.session_id}")
                            continue

                        if phase and checkpoint.get("phase") != phase:
                            continue

                        logger.debug(f"Retrieved latest checkpoint: {checkpoint.get('phase', 'N/A')}")
                        return checkpoint

        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.debug(f"Failed to retrieve latest git note: {e}")
            return None

        logger.debug(f"No git note found for session {self.session_id}")
        return None

    def list_checkpoints(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
        phase: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List checkpoints from git notes (using hierarchical namespace).

        Uses git for-each-ref to discover all checkpoints automatically.

        Args:
            session_id: Filter by session (optional, defaults to self.session_id)
            limit: Maximum number to return (optional)
            phase: Filter by phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT) (optional)

        Returns:
            List of checkpoint metadata dicts, sorted newest first
        """
        checkpoints = []
        filter_session_id = session_id or self.session_id

        # Use git for-each-ref to discover all refs in session's namespace
        refs_result = subprocess.run(
            ["git", "for-each-ref", f"refs/notes/empirica/session/{filter_session_id}", "--format=%(refname)"],
            capture_output=True,
            text=True,
            cwd=self.git_repo_path
        )

        if refs_result.returncode != 0 or not refs_result.stdout.strip():
            logger.debug(f"No checkpoints found for session: {filter_session_id}")
            return []

        # Parse all refs (one per line)
        refs = [line.strip() for line in refs_result.stdout.strip().split('\n') if line.strip()]

        for ref in refs:
            # Extract phase from ref path
            # Example: refs/notes/empirica/session/abc-123/PREFLIGHT/1
            ref_parts = ref.split('/')
            if len(ref_parts) < 7:
                logger.warning(f"Unexpected ref format: {ref}")
                continue

            ref_phase = ref_parts[5]

            # Apply phase filter
            if phase and ref_phase != phase:
                continue

            # Strip "refs/notes/" prefix for git notes command
            note_ref = ref[11:]

            # Find what commit this note is attached to
            list_result = subprocess.run(
                ["git", "notes", "--ref", note_ref, "list"],
                capture_output=True,
                text=True,
                cwd=self.git_repo_path
            )

            if list_result.returncode != 0 or not list_result.stdout.strip():
                logger.debug(f"No notes found for ref {note_ref}")
                continue

            # Parse the annotated commit (second column)
            note_line = list_result.stdout.strip().split('\n')[0]
            parts = note_line.split()
            if len(parts) < 2:
                logger.warning(f"Unexpected note list format for {note_ref}: {note_line}")
                continue
            annotated_commit = parts[1]

            # Get the note content for the specific commit
            show_result = subprocess.run(
                ["git", "notes", "--ref", note_ref, "show", annotated_commit],
                capture_output=True,
                text=True,
                cwd=self.git_repo_path
            )

            if show_result.returncode == 0:
                try:
                    checkpoint = json.loads(show_result.stdout)

                    # Double-check session filter
                    if session_id and checkpoint.get("session_id") != session_id:
                        logger.warning(f"Session mismatch in checkpoint: {checkpoint.get('session_id')} != {session_id}")
                        continue

                    checkpoints.append(checkpoint)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse checkpoint from ref {ref}: {e}")
                    continue

        # Sort by timestamp descending (newest first)
        checkpoints.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Apply limit
        if limit and limit > 0:
            checkpoints = checkpoints[:limit]

        return checkpoints
