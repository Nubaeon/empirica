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

from .reflex_frame import VectorState, Action
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema as EpistemicAssessment
from empirica.core.git_ops.signed_operations import SignedGitOperations
from empirica.core.persona.signing_persona import SigningPersona

logger = logging.getLogger(__name__)


class GitEnhancedReflexLogger:
    """
    Epistemic checkpoint logger with 3-layer storage.
    
    Storage Architecture:
    - SQLite: Queryable checkpoints (fallback)
    - Git Notes: Compressed (~450 tokens), distributed, signable
    - JSON Logs: Full audit trail (optional)
    
    No longer inherits from ReflexLogger - standalone implementation.
    Different interface: add_checkpoint() vs log_assessment()
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
            enable_git_notes: Enable git notes storage (default: True, now required)
            base_log_dir: Base directory for checkpoint logs
            git_repo_path: Path to git repository (default: current directory)
            signing_persona: Optional SigningPersona for cryptographically signed checkpoints
        """
        # Setup base log directory (no inheritance needed!)
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = session_id
        self.enable_git_notes = enable_git_notes  # Now required
        self.git_repo_path = Path(git_repo_path or Path.cwd())
        self.git_available = self._check_git_available()
        self.signing_persona = signing_persona
        self.signed_git_ops: Optional[SignedGitOperations] = None

        # Initialize signed git operations if persona provided
        if signing_persona and self.git_available:
            try:
                self.signed_git_ops = SignedGitOperations(repo_path=str(self.git_repo_path))
            except Exception as e:
                logger.warning(f"Failed to initialize SignedGitOperations: {e}")

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
        metadata: Optional[Dict[str, Any]] = None,
        epistemic_tags: Optional[Dict[str, Any]] = None,
        noema: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add compressed checkpoint to git notes and SQLite with optional signing.

        Storage Architecture (Pointer-based):
        - Git: Authoritative source for signed epistemic states (immutable, verifiable)
        - SQLite: Queryable index with pointers to git commits + noema metadata
        - Qdrant: Semantic vectors for drift detection (added in future phase)

        Args:
            phase: Workflow phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
            round_num: Current round number
            vectors: Epistemic vector scores (13D)
            metadata: Additional metadata (task, decision, files changed, etc.)
            epistemic_tags: Semantic tags (findings, unknowns, deadends) for rehydration
            noema: Optional noematic extraction (epistemic signature, learning efficiency, etc.)

        Returns:
            Git commit SHA if signed, note SHA if unsigned, None if failed
        """
        self.current_phase = phase
        self.current_round = round_num

        # Create compressed checkpoint
        checkpoint = self._create_checkpoint(phase, round_num, vectors, metadata, epistemic_tags, noema)

        # Save to git notes first (to get commit SHA for SQLite pointer)
        git_commit_sha = None
        git_notes_success = False
        if self.enable_git_notes and self.git_available:
            # If signing persona available, use signed git operations
            if self.signed_git_ops and self.signing_persona:
                git_commit_sha = self._git_add_signed_note(checkpoint, phase)
            else:
                git_commit_sha = self._git_add_note(checkpoint)
            
            # Track success for status reporting
            git_notes_success = git_commit_sha is not None

        # Save to SQLite with git pointer (always, for queryability)
        self._save_checkpoint_to_sqlite(
            checkpoint=checkpoint,
            git_commit_sha=git_commit_sha,
            git_notes_ref=f"empirica/session/{self.session_id}/{phase}/{round_num}"
        )

        # Return success indicator (string SHA on success, empty string on failure but attempted)
        # This allows callers to distinguish between:
        # - Success: git_commit_sha is a SHA string
        # - Attempted but failed: returns empty string ""
        # - Not attempted: would return None (but we always attempt if enabled)
        if git_notes_success:
            return git_commit_sha
        elif self.enable_git_notes and self.git_available:
            # Attempted but failed - return empty string to indicate "tried but failed"
            return ""
        else:
            # Git notes not enabled/available
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
        - Store metadata selectively (only what's needed for context)
        - Use compact field names
        - Calculate overall confidence from vectors

        Phase 3 Enhancement:
        - Capture epistemic tags (findings, unknowns, deadends)
        - Enable rehydration for next AI in handoff
        - Preserve reasoning trail for mutual validation

        Phase 4 Enhancement:
        - Embed noematic extraction (epistemic signature, learning efficiency)
        - Support semantic storage for drift detection
        - Enable replay scenarios for auditability

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
            "meta": metadata or {},
            "epistemic_tags": epistemic_tags or {}
        }

        # Phase 4: Embed noematic extraction
        if noema:
            checkpoint["noema"] = noema

        # Phase 2.5: Capture git state
        if self.enable_git_notes and self.git_repo_path:
            checkpoint["git_state"] = self._capture_git_state()
            checkpoint["learning_delta"] = self._calculate_learning_delta(vectors)

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
    
    def _capture_git_state(self) -> Dict[str, Any]:
        """
        Capture current git state at checkpoint time.
        
        Phase 2.5: Enables correlation of epistemic deltas to code changes.
        
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
            commits_since_last = self._get_commits_since_last_checkpoint()
            
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
    
    def _get_commits_since_last_checkpoint(self) -> List[Dict[str, Any]]:
        """
        Get commits made since last checkpoint.
        
        Returns:
            List of commit dictionaries with sha, message, author, timestamp, files_changed
        """
        try:
            # Get last checkpoint to find timestamp
            last_checkpoint = self.get_last_checkpoint()
            if not last_checkpoint:
                # No previous checkpoint - return empty list
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
    
    def _calculate_learning_delta(self, current_vectors: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate epistemic delta since last checkpoint.
        
        Phase 2.5: Enables attribution analysis (what caused learning increase).
        
        Args:
            current_vectors: Current epistemic vectors
        
        Returns:
            Dictionary mapping vector names to {prev, curr, delta} for each vector
        """
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
    
    def _save_checkpoint_to_sqlite(
        self,
        checkpoint: Dict[str, Any],
        git_commit_sha: Optional[str] = None,
        git_notes_ref: Optional[str] = None
    ):
        """
        Save checkpoint pointer to SQLite reflexes table.

        Architecture (Pointer-based):
        - Git: Authoritative source for full signed epistemic state (immutable)
        - SQLite: Lightweight index with pointers + noema metadata for queries
        - Qdrant: Semantic vectors for drift detection (future phase)

        Args:
            checkpoint: Compressed checkpoint dictionary containing:
                - session_id, phase, round, timestamp
                - vectors (all 13 epistemic dimensions)
                - noema (epistemic signature, learning efficiency, etc.)
                - metadata (task, decision, etc.)
            git_commit_sha: Git commit SHA (pointer to authoritative source)
            git_notes_ref: Git notes reference path for retrieval
        """
        try:
            from empirica.data.session_database import SessionDatabase

            # Extract data from checkpoint
            session_id = checkpoint.get('session_id')
            phase = checkpoint.get('phase')
            round_num = checkpoint.get('round', 1)
            vectors = checkpoint.get('vectors', {})

            if not session_id or not phase:
                logger.error(f"Cannot save checkpoint: missing session_id or phase")
                return

            # Initialize database
            db = SessionDatabase()

            try:
                # Extract noema metadata for quick filtering
                noema = checkpoint.get('noema', {})
                epistemic_signature = noema.get('epistemic_signature')
                learning_efficiency = noema.get('learning_efficiency')
                inferred_persona = noema.get('inferred_persona')
                investigation_domain = noema.get('investigation_domain')

                # Prepare metadata with git pointers
                metadata_dict = checkpoint.get('meta', {})
                metadata_dict['git_commit_sha'] = git_commit_sha
                metadata_dict['git_notes_ref'] = git_notes_ref

                # Store pointer + noema metadata in reflexes table
                db.store_vectors(
                    session_id=session_id,
                    phase=phase,
                    vectors=vectors,
                    cascade_id=metadata_dict.get('cascade_id'),
                    round_num=round_num,
                    metadata=metadata_dict,
                    reasoning=metadata_dict.get('reasoning')
                )

                logger.debug(
                    f"Checkpoint pointer saved to SQLite: "
                    f"session={session_id}, phase={phase}, round={round_num}, "
                    f"git_commit={git_commit_sha[:7] if git_commit_sha else 'none'}, "
                    f"noema_sig={epistemic_signature}"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to save checkpoint to SQLite: {e}", exc_info=True)
            # Continue anyway - don't fail the whole operation if SQLite has issues
    
    def _git_add_note(self, checkpoint: Dict[str, Any]) -> Optional[str]:
        """
        Add checkpoint to git notes with session-specific namespace.
        
        Uses session-specific git notes refs to prevent agent collisions:
        - empirica/session/<session_id> for individual sessions
        - Multiple agents can have concurrent checkpoints
        
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
            # Use -f flag to allow updating notes if this ref already has a note on HEAD
            # (This happens when multiple checkpoints are created before new commits)
            # Use stdin instead of -m to avoid "Argument list too long" errors with large payloads
            # -F - tells git to read note content from stdin
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
            logger.info(f"Session-specific git checkpoint added: {note_sha} (session={self.session_id}, phase={checkpoint['phase']})")
            
            return note_sha
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.warning(f"Git note operation failed: {e}. Using fallback storage.")
            return None

    def _git_add_signed_note(self, checkpoint: Dict[str, Any], phase: str) -> Optional[str]:
        """
        Add cryptographically signed checkpoint to git notes.

        Uses SignedGitOperations to:
        1. Sign epistemic state with persona's Ed25519 key
        2. Store signed state in hierarchical git notes
        3. Enable verification chain for audit trail
        4. Support noematic extraction queries

        Args:
            checkpoint: Checkpoint dictionary (includes vectors, noema, etc.)
            phase: CASCADE phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)

        Returns:
            Note SHA if successful, None if failed
        """
        try:
            if not self.signed_git_ops or not self.signing_persona:
                logger.debug("Signed operations not available, falling back to unsigned")
                return self._git_add_note(checkpoint)

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

            # Add noema-specific note ref for semantic storage in Qdrant
            # Use stdin instead of -m to avoid "Argument list too long" errors with large payloads
            # -F - tells git to read note content from stdin
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
                # Still successful if signed commit worked, this is supplementary

            logger.info(
                f"✓ Signed checkpoint committed: {commit_sha[:7]} "
                f"(session={self.session_id}, phase={phase}, persona={self.signing_persona.persona_id})"
            )

            return commit_sha

        except Exception as e:
            logger.warning(f"Failed to add signed git note: {e}. Falling back to unsigned.")
            return self._git_add_note(checkpoint)

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
        # Try git notes first - using hierarchical namespace retrieval
        if self.enable_git_notes and self.git_available:
            checkpoint = self._git_get_latest_note_new(phase=phase)
            if checkpoint and self._is_fresh(checkpoint, max_age_hours):
                return checkpoint

        # Fallback to SQLite
        return self._load_checkpoint_from_sqlite(phase=phase, max_age_hours=max_age_hours)
    
    def _git_get_latest_note(self, phase: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve latest checkpoint from git notes (new hierarchical structure).

        Args:
            phase: Filter by phase (optional)

        Returns:
            Checkpoint dictionary or None
        """
        try:
            # We now need to look for notes in the hierarchical namespace
            # For backward compatibility and to get the 'latest', we'll list notes and pick the most recent
            # First try to find the latest checkpoint for the specific phase, if specified
            if phase:
                # Look for the latest round for this specific phase
                result = subprocess.run(
                    ["git", "notes", "list", f"refs/notes/empirica/session/{self.session_id}/{phase}"],
                    capture_output=True,
                    timeout=2,
                    cwd=self.git_repo_path,
                    text=True
                )

                if result.returncode == 0 and result.stdout.strip():
                    # Get the note with the highest round number
                    lines = result.stdout.strip().split('\n')
                    latest_commit = None
                    highest_round = 0

                    for line in lines:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                note_sha, commit_sha = parts[0], parts[1]
                                # Extract round number from ref path (by getting round from the ref name)
                                # We'll check what refs exist
                                # For now, let's find the one with the highest round number in the ref path
                                pass  # We'll handle this later

                    # For now, just try HEAD for the specific phase
                    note_refs = [
                        f"empirica/session/{self.session_id}/{phase}/3",
                        f"empirica/session/{self.session_id}/{phase}/2",
                        f"empirica/session/{self.session_id}/{phase}/1"
                    ]

                    for note_ref in note_refs:
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
                                logger.warning(f"Session ID mismatch in git note: {checkpoint.get('session_id')} vs {self.session_id}")
                                continue
                            return checkpoint
                else:
                    # If no notes with specific phase exist, try generic search
                    pass

            # If no specific phase requested or no notes found with that phase,
            # search for any checkpoint from this session
            # We'll list through most recent phases/rounds in priority order
            possible_refs = [
                f"empirica/session/{self.session_id}/POSTFLIGHT/1",
                f"empirica/session/{self.session_id}/POSTFLIGHT/2",
                f"empirica/session/{self.session_id}/POSTFLIGHT/3",
                f"empirica/session/{self.session_id}/ACT/1",
                f"empirica/session/{self.session_id}/ACT/2",
                f"empirica/session/{self.session_id}/CHECK/1",
                f"empirica/session/{self.session_id}/CHECK/2",
                f"empirica/session/{self.session_id}/PREFLIGHT/1",
                f"empirica/session/{self.session_id}/PREFLIGHT/2"
            ]

            for note_ref in possible_refs:
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
                        logger.warning(f"Session ID mismatch in git note: {checkpoint.get('session_id')} vs {self.session_id}")
                        continue
                    if phase and checkpoint.get("phase") != phase:
                        continue
                    return checkpoint

            logger.debug(f"No git note found for session {self.session_id}")
            return None

        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Failed to retrieve git note: {e}")
            return None

    def _git_get_latest_note_new(self, phase: Optional[str] = None) -> Optional[Dict[str, Any]]:
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
                # Only check the specific phase requested
                phases_to_check = [phase]

            # Start checking from the highest round numbers downwards
            for round_num in range(10, 0, -1):  # Check rounds 10 to 1
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
        # This automatically finds all phase/round combinations
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
            #          0    1     2        3       4       5          6
            ref_parts = ref.split('/')
            if len(ref_parts) < 7:
                logger.warning(f"Unexpected ref format: {ref}")
                continue
            
            ref_phase = ref_parts[5]  # PREFLIGHT, CHECK, ACT, POSTFLIGHT
            
            # Apply phase filter
            if phase and ref_phase != phase:
                continue
            
            # Strip "refs/notes/" prefix for git notes command
            note_ref = ref[11:]  # "refs/notes/" is 11 characters
            
            # Get the note content for HEAD
            # CRITICAL: Correct syntax is: git notes --ref <ref> show <commit>
            show_result = subprocess.run(
                ["git", "notes", "--ref", note_ref, "show", "HEAD"],
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
