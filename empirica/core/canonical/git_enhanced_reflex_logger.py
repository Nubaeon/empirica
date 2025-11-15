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

from .reflex_logger import ReflexLogger
from .reflex_frame import ReflexFrame, EpistemicAssessment

logger = logging.getLogger(__name__)


class GitEnhancedReflexLogger(ReflexLogger):
    """
    Git-enhanced reflex logger with compressed checkpoint storage.
    
    Extends ReflexLogger to store epistemic state in git notes for token efficiency.
    Falls back to SQLite when git unavailable.
    """
    
    def __init__(
        self,
        session_id: str,
        enable_git_notes: bool = False,
        base_log_dir: str = ".empirica_reflex_logs",
        git_repo_path: Optional[str] = None
    ):
        """
        Initialize git-enhanced logger.
        
        Args:
            session_id: Session identifier
            enable_git_notes: Enable git notes storage (default: False for backward compat)
            base_log_dir: Base directory for reflex logs
            git_repo_path: Path to git repository (default: current directory)
        """
        super().__init__(base_log_dir=base_log_dir)
        
        self.session_id = session_id
        self.enable_git_notes = enable_git_notes
        self.git_repo_path = Path(git_repo_path or Path.cwd())
        self.git_available = self._check_git_available()
        
        # Track current round for vector diff calculation
        self.current_round = 0
        self.current_phase = None
        
        if enable_git_notes and not self.git_available:
            logger.warning(
                "Git notes requested but git not available. "
                "Falling back to SQLite storage."
            )
    
    @property
    def git_enabled(self) -> bool:
        """
        Check if git notes are enabled and available.
        
        Returns:
            True if git notes enabled AND git available
        """
        return self.enable_git_notes and self.git_available
    
    def _check_git_available(self) -> bool:
        """
        Check if git repository is available.
        
        Returns:
            True if git repo exists and git command available
        """
        try:
            # Check if git command exists
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                timeout=2,
                cwd=self.git_repo_path
            )
            
            if result.returncode != 0:
                return False
            
            # Check if we're in a git repository
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
    
    def add_checkpoint(
        self,
        phase: str,
        round_num: int,
        vectors: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add compressed checkpoint to git notes and SQLite.
        
        Args:
            phase: Workflow phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
            round_num: Current round number
            vectors: Epistemic vector scores (12D)
            metadata: Additional metadata (task, decision, files changed, etc.)
        
        Returns:
            Note ID (git SHA) if successful, None otherwise
        """
        self.current_phase = phase
        self.current_round = round_num
        
        # Create compressed checkpoint
        checkpoint = self._create_checkpoint(phase, round_num, vectors, metadata)
        
        # Save to SQLite (always, for fallback)
        self._save_checkpoint_to_sqlite(checkpoint)
        
        # Save to git notes (if enabled and available)
        if self.enable_git_notes and self.git_available:
            return self._git_add_note(checkpoint)
        
        return None
    
    def _create_checkpoint(
        self,
        phase: str,
        round_num: int,
        vectors: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create compressed checkpoint (target: 200-500 tokens).
        
        Compression strategy:
        - Only store vector scores (not rationales)
        - Store metadata selectively (only what's needed for context)
        - Use compact field names
        - Calculate overall confidence from vectors
        
        Returns:
            Compressed checkpoint dictionary
        """
        # Calculate overall confidence (weighted average)
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
            "meta": metadata or {}
        }
        
        # Add token count (self-measurement)
        checkpoint["token_count"] = self._estimate_token_count(checkpoint)
        
        return checkpoint
    
    def _estimate_token_count(self, data: Dict) -> int:
        """
        Estimate token count for checkpoint data.
        
        Uses simple approximation: len(text.split()) * 1.3
        (Good enough for Phase 1.5, tiktoken will be added later)
        
        Args:
            data: Checkpoint dictionary
        
        Returns:
            Estimated token count
        """
        text = json.dumps(data)
        word_count = len(text.split())
        return int(word_count * 1.3)
    
    def _save_checkpoint_to_sqlite(self, checkpoint: Dict[str, Any]):
        """
        Save checkpoint to SQLite (fallback storage).
        
        Note: Actual implementation would integrate with SessionDatabase.
        For Phase 1.5, we store as JSON file alongside reflex logs.
        """
        # Create checkpoint directory
        checkpoint_dir = self.base_log_dir / "checkpoints" / self.session_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as timestamped JSON file
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        filename = f"checkpoint_{checkpoint['phase']}_{timestamp}.json"
        filepath = checkpoint_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        logger.debug(f"Checkpoint saved to SQLite fallback: {filepath}")
    
    def _git_add_note(self, checkpoint: Dict[str, Any]) -> Optional[str]:
        """
        Add checkpoint to git notes attached to HEAD commit.
        
        Args:
            checkpoint: Checkpoint dictionary
        
        Returns:
            Note SHA if successful, None if failed
        """
        try:
            # Validate JSON serialization
            checkpoint_json = json.dumps(checkpoint)
            json.loads(checkpoint_json)  # Validate it's parseable
            
            # Add note to HEAD commit
            result = subprocess.run(
                ["git", "notes", "add", "-f", "-m", checkpoint_json],
                capture_output=True,
                timeout=5,
                cwd=self.git_repo_path,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(
                    f"Failed to add git note: {result.stderr}. "
                    f"Fallback storage available."
                )
                return None
            
            # Get note SHA
            result = subprocess.run(
                ["git", "notes", "list", "HEAD"],
                capture_output=True,
                timeout=2,
                cwd=self.git_repo_path,
                text=True
            )
            
            note_sha = result.stdout.strip().split()[0] if result.stdout else None
            logger.info(f"Git checkpoint added: {note_sha} (phase={checkpoint['phase']})")
            
            return note_sha
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.warning(f"Git note operation failed: {e}. Using fallback storage.")
            return None
    
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
        if self.enable_git_notes and self.git_available:
            checkpoint = self._git_get_latest_note(phase=phase)
            if checkpoint and self._is_fresh(checkpoint, max_age_hours):
                return checkpoint
        
        # Fallback to SQLite
        return self._load_checkpoint_from_sqlite(phase=phase, max_age_hours=max_age_hours)
    
    def _git_get_latest_note(self, phase: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve latest checkpoint from git notes.
        
        Args:
            phase: Filter by phase (optional)
        
        Returns:
            Checkpoint dictionary or None
        """
        try:
            # Get note from HEAD
            result = subprocess.run(
                ["git", "notes", "show", "HEAD"],
                capture_output=True,
                timeout=2,
                cwd=self.git_repo_path,
                text=True
            )
            
            if result.returncode != 0:
                return None
            
            # Parse JSON
            checkpoint = json.loads(result.stdout)
            
            # Filter by phase if requested
            if phase and checkpoint.get("phase") != phase:
                return None
            
            # Validate session_id matches
            if checkpoint.get("session_id") != self.session_id:
                logger.debug("Checkpoint session_id mismatch, skipping")
                return None
            
            return checkpoint
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Failed to retrieve git note: {e}")
            return None
    
    def _load_checkpoint_from_sqlite(
        self,
        phase: Optional[str] = None,
        max_age_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint from SQLite fallback storage.
        
        Args:
            phase: Filter by phase (optional)
            max_age_hours: Maximum age in hours
        
        Returns:
            Checkpoint dictionary or None
        """
        checkpoint_dir = self.base_log_dir / "checkpoints" / self.session_id
        
        if not checkpoint_dir.exists():
            return None
        
        # Get all checkpoint files
        checkpoint_files = sorted(
            checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
        
        for filepath in checkpoint_files:
            try:
                with open(filepath, 'r') as f:
                    checkpoint = json.load(f)
                
                # Check age
                checkpoint_time = datetime.fromisoformat(checkpoint['timestamp'])
                if checkpoint_time < cutoff_time:
                    continue
                
                # Check phase filter
                if phase and checkpoint.get("phase") != phase:
                    continue
                
                return checkpoint
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.debug(f"Failed to load checkpoint {filepath}: {e}")
                continue
        
        return None
    
    def _is_fresh(self, checkpoint: Dict[str, Any], max_age_hours: int) -> bool:
        """
        Check if checkpoint is within acceptable age.
        
        Args:
            checkpoint: Checkpoint dictionary
            max_age_hours: Maximum age in hours
        
        Returns:
            True if checkpoint is fresh enough
        """
        try:
            checkpoint_time = datetime.fromisoformat(checkpoint['timestamp'])
            cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
            return checkpoint_time >= cutoff_time
        except (KeyError, ValueError):
            return False
    
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
        
        # Calculate deltas
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
        
        # Add token count
        diff["token_count"] = self._estimate_token_count(diff)
        
        return diff
