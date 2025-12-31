"""
Git-Enhanced Reflex Logger

Extends ReflexLogger with git-backed checkpoint storage for token efficiency.

Key Innovation: Store compressed epistemic checkpoints in git notes instead of
loading full session history from SQLite. Achieves 80-90% token reduction.

Architecture:
- Hybrid storage: SQLite (fallback) + Git Notes (primary)
- Backward compatible: enable_git_notes=False uses standard ReflexLogger
- Compressed checkpoints: ~450 tokens vs ~6,500 tokens for full history
- Git notes attached to HEAD commit for temporal correlation

Refactored: Uses focused modules for git state capture, git notes storage,
and checkpoint storage. Main class is now an orchestrator (~400 lines vs 1,156).

Usage:
    logger = GitEnhancedReflexLogger(
        session_id="abc-123",
        enable_git_notes=True
    )

    # Add checkpoint at phase transition
    logger.add_checkpoint(
        phase="PREFLIGHT",
        round_num=1,
        vectors={"know": 0.8, "do": 0.9, ...},
        metadata={"task": "review code"}
    )

    # Load last checkpoint (compressed)
    checkpoint = logger.get_last_checkpoint()
    # Returns ~450 tokens instead of ~6,500
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, UTC

from .reflex_frame import VectorState, Action
from .git_state_capture import GitStateCapture
from .git_notes_storage import GitNotesStorage
from .checkpoint_storage import CheckpointStorage
from empirica.core.persona.signing_persona import SigningPersona

logger = logging.getLogger(__name__)


class GitEnhancedReflexLogger:
    """
    Epistemic checkpoint logger with 3-layer storage.

    Storage Architecture:
    - SQLite: Queryable checkpoints (fallback)
    - Git Notes: Compressed (~450 tokens), distributed, signable
    - JSON Logs: Full audit trail (optional)

    Orchestrates focused modules:
    - GitStateCapture: Git repository state tracking
    - GitNotesStorage: Git notes read/write operations
    - CheckpointStorage: SQLite and JSON storage
    """

    def __init__(
        self,
        session_id: str,
        enable_git_notes: bool = True,
        base_log_dir: str = ".empirica_reflex_logs",
        git_repo_path: Optional[str] = None,
        signing_persona: Optional[SigningPersona] = None
    ):
        """
        Initialize checkpoint logger.

        Args:
            session_id: Session identifier
            enable_git_notes: Enable git notes storage (default: True)
            base_log_dir: Base directory for checkpoint logs
            git_repo_path: Path to git repository (default: current directory)
            signing_persona: Optional SigningPersona for cryptographically signed checkpoints
        """
        self.session_id = session_id
        self.enable_git_notes = enable_git_notes
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        self.git_repo_path = Path(git_repo_path or Path.cwd())
        self.git_available = self._check_git_available()
        self.signing_persona = signing_persona

        # Initialize focused modules
        self.git_state_capture = GitStateCapture(self.git_repo_path) if self.git_available else None
        self.git_notes_storage = GitNotesStorage(
            session_id=session_id,
            git_repo_path=self.git_repo_path,
            signing_persona=signing_persona
        ) if self.git_available else None
        self.checkpoint_storage = CheckpointStorage(
            session_id=session_id,
            base_log_dir=self.base_log_dir
        )

        # Track current round for vector diff calculation
        self.current_round = 0
        self.current_phase = None

        if not self.git_available:
            logger.warning(
                "Git not available. "
                "Falling back to SQLite storage only."
            )

    @property
    def git_enabled(self) -> bool:
        """Check if git notes are enabled and available."""
        return self.enable_git_notes and self.git_available

    def _check_git_available(self) -> bool:
        """Check if git repository is available."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                timeout=2,
                cwd=self.git_repo_path
            )

            if result.returncode != 0:
                return False

            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                timeout=2,
                cwd=self.git_repo_path
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug(f"Git availability check failed: {e}")
            return False

    def _get_next_round(self, phase: str) -> int:
        """Get next round number for a phase by checking existing reflexes."""
        try:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT MAX(round) FROM reflexes
                WHERE session_id = ? AND phase = ?
            ''', (self.session_id, phase))
            row = cursor.fetchone()
            db.close()
            max_round = row[0] if row and row[0] is not None else 0
            return max_round + 1
        except Exception as e:
            logger.debug(f"Failed to get next round: {e}")
            return 1

    def add_checkpoint(
        self,
        phase: str,
        round_num: Optional[int] = None,
        vectors: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        epistemic_tags: Optional[Dict[str, Any]] = None,
        noema: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add compressed checkpoint to git notes and SQLite with optional signing.

        Storage Architecture (Pointer-based):
        - Git: Authoritative source for signed epistemic states (immutable, verifiable)
        - SQLite: Queryable index with pointers to git commits + noema metadata

        Args:
            phase: Workflow phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
            round_num: Current round number (auto-incremented if None)
            vectors: Epistemic vector scores (13D)
            metadata: Additional metadata (task, decision, files changed, etc.)
            epistemic_tags: Semantic tags (findings, unknowns, deadends) for rehydration
            noema: Optional noematic extraction (epistemic signature, learning efficiency, etc.)

        Returns:
            Git commit SHA if signed, note SHA if unsigned, None if failed
        """
        # Handle backward compatibility: if round_num is a dict, it's vectors
        if isinstance(round_num, dict):
            vectors = round_num
            round_num = None

        self.current_phase = phase

        # Auto-increment round if not specified
        if round_num is None:
            round_num = self._get_next_round(phase)
        self.current_round = round_num

        # Ensure vectors is not None
        if vectors is None:
            vectors = {}

        # Create compressed checkpoint
        checkpoint = self._create_checkpoint(phase, round_num, vectors, metadata, epistemic_tags, noema)

        # Save to git notes first (to get commit SHA for SQLite pointer)
        git_commit_sha = None
        git_notes_success = False

        if self.git_enabled and self.git_notes_storage:
            if self.signing_persona:
                git_commit_sha = self.git_notes_storage.add_signed_note(checkpoint, phase)
            else:
                git_commit_sha = self.git_notes_storage.add_note(checkpoint)

            git_notes_success = git_commit_sha is not None

        # Save to SQLite with git pointer (always, for queryability)
        self.checkpoint_storage.save_to_sqlite(
            checkpoint=checkpoint,
            git_commit_sha=git_commit_sha,
            git_notes_ref=f"empirica/session/{self.session_id}/{phase}/{round_num}"
        )

        # Also save to JSON for fallback/audit trail
        self.checkpoint_storage.save_to_json(checkpoint)

        if git_notes_success:
            return git_commit_sha
        elif self.git_enabled:
            return ""  # Attempted but failed
        else:
            return None

    def _create_checkpoint(
        self,
        phase: str,
        round_num: int,
        vectors: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
        epistemic_tags: Optional[Dict[str, Any]] = None,
        noema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create compressed checkpoint (target: 200-500 tokens).

        Compression strategy:
        - Only store vector scores (not rationales)
        - Store metadata selectively
        - Use compact field names
        - Calculate overall confidence from vectors
        """
        # Calculate overall confidence (weighted average of Tier 0)
        tier0_keys = ['know', 'do', 'context']
        tier0_values = [vectors.get(k, 0.5) for k in tier0_keys]
        overall_confidence = sum(tier0_values) / len(tier0_values) if tier0_values else 0.5

        checkpoint = {
            "session_id": self.session_id,
            "phase": phase,
            "round": round_num,
            "timestamp": datetime.now(UTC).isoformat(),
            "vectors": vectors,
            "overall_confidence": round(overall_confidence, 3),
            "meta": metadata or {},
            "epistemic_tags": epistemic_tags or {}
        }

        if noema:
            checkpoint["noema"] = noema

        # Capture git state if enabled
        if self.git_enabled and self.git_state_capture:
            checkpoint["git_state"] = self.git_state_capture.capture_state(
                get_last_checkpoint_fn=self.get_last_checkpoint
            )
            checkpoint["learning_delta"] = self._calculate_learning_delta(vectors)

        checkpoint["token_count"] = self._estimate_token_count(checkpoint)

        return checkpoint

    def _estimate_token_count(self, data: Dict) -> int:
        """Estimate token count for checkpoint data."""
        text = json.dumps(data)
        word_count = len(text.split())
        return int(word_count * 1.3)

    def _calculate_learning_delta(self, current_vectors: Dict[str, float]) -> Dict[str, Any]:
        """Calculate epistemic delta since last checkpoint."""
        try:
            last_checkpoint = self.get_last_checkpoint()
            if not last_checkpoint:
                return {}

            prev_vectors = last_checkpoint.get('vectors', {})
            if not prev_vectors:
                return {}

            deltas = {}
            for key in current_vectors:
                if key in prev_vectors:
                    prev_val = prev_vectors[key]
                    curr_val = current_vectors[key]
                    delta = curr_val - prev_val

                    deltas[key] = {
                        "prev": round(prev_val, 3),
                        "curr": round(curr_val, 3),
                        "delta": round(delta, 3)
                    }

            return deltas

        except Exception as e:
            logger.warning(f"Failed to calculate learning delta: {e}")
            return {}

    def get_last_checkpoint(
        self,
        max_age_hours: int = 24,
        phase: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load most recent checkpoint (git notes preferred, SQLite fallback).

        Args:
            max_age_hours: Maximum age of checkpoint to consider (default: 24 hours)
            phase: Filter by specific phase (optional)

        Returns:
            Compressed checkpoint (~450 tokens) or None if not found
        """
        # Try git notes first
        if self.git_enabled and self.git_notes_storage:
            checkpoint = self.git_notes_storage.get_latest_note(phase=phase)
            if checkpoint and self._is_fresh(checkpoint, max_age_hours):
                return checkpoint

        # Fallback to SQLite/JSON
        return self.checkpoint_storage.load_from_sqlite(phase=phase, max_age_hours=max_age_hours)

    def _is_fresh(self, checkpoint: Dict[str, Any], max_age_hours: int) -> bool:
        """Check if checkpoint is within acceptable age."""
        try:
            checkpoint_time = datetime.fromisoformat(checkpoint['timestamp'])
            cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
            return checkpoint_time >= cutoff_time
        except (KeyError, ValueError):
            return False

    def list_checkpoints(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
        phase: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List checkpoints from git notes (using hierarchical namespace).

        Args:
            session_id: Filter by session (optional, defaults to self.session_id)
            limit: Maximum number to return (optional)
            phase: Filter by phase (optional)

        Returns:
            List of checkpoint metadata dicts, sorted newest first
        """
        if self.git_enabled and self.git_notes_storage:
            return self.git_notes_storage.list_checkpoints(
                session_id=session_id,
                limit=limit,
                phase=phase
            )
        return []

    def get_vector_diff(
        self,
        since_checkpoint: Dict[str, Any],
        current_vectors: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Compute vector delta since last checkpoint.

        Returns differential update (~400 tokens vs ~3,500 for full assessment).

        Args:
            since_checkpoint: Baseline checkpoint
            current_vectors: Current epistemic vectors

        Returns:
            Vector diff dictionary with delta and significant changes
        """
        baseline_vectors = since_checkpoint.get("vectors", {})

        delta = {}
        significant_changes = []

        for key in current_vectors:
            baseline_value = baseline_vectors.get(key, 0.5)
            current_value = current_vectors[key]
            change = current_value - baseline_value

            delta[key] = round(change, 3)

            # Flag significant changes (>0.15 threshold)
            if abs(change) > 0.15:
                significant_changes.append({
                    "vector": key,
                    "baseline": round(baseline_value, 3),
                    "current": round(current_value, 3),
                    "delta": round(change, 3)
                })

        diff = {
            "baseline_phase": since_checkpoint.get("phase"),
            "baseline_round": since_checkpoint.get("round", 0),
            "current_round": self.current_round,
            "delta": delta,
            "significant_changes": significant_changes,
            "timestamp": datetime.now(UTC).isoformat()
        }

        diff["token_count"] = self._estimate_token_count(diff)

        return diff
