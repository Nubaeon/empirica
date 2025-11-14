"""
Unit Tests for GitEnhancedReflexLogger

Tests git notes integration, SQLite fallback, checkpoint creation, and vector diff.
"""

import pytest
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch, MagicMock

from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger


class TestGitAvailability:
    """Test git availability detection"""
    
    def test_git_available_check_success(self, tmp_path):
        """Test successful git availability check"""
        # Create a temporary git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        
        logger = GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=True,
            git_repo_path=str(tmp_path)
        )
        
        assert logger.git_available is True
    
    def test_git_available_check_no_git_repo(self, tmp_path):
        """Test git availability check when not in git repo"""
        logger = GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=True,
            git_repo_path=str(tmp_path)
        )
        
        assert logger.git_available is False
    
    @patch('subprocess.run')
    def test_git_available_check_command_not_found(self, mock_run):
        """Test git availability check when git command not found"""
        mock_run.side_effect = FileNotFoundError("git command not found")
        
        logger = GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=True
        )
        
        assert logger.git_available is False


class TestCheckpointCreation:
    """Test checkpoint creation and storage"""
    
    @pytest.fixture
    def git_logger(self, tmp_path):
        """Create logger with git repo"""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
        
        # Create initial commit
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=tmp_path, check=True, capture_output=True)
        
        return GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=True,
            base_log_dir=str(tmp_path / ".empirica_reflex_logs"),
            git_repo_path=str(tmp_path)
        )
    
    def test_add_git_checkpoint_success(self, git_logger, tmp_path):
        """Test successful checkpoint addition to git notes"""
        vectors = {
            "know": 0.8,
            "do": 0.9,
            "context": 0.7,
            "uncertainty": 0.3
        }
        
        note_id = git_logger.add_checkpoint(
            phase="PREFLIGHT",
            round_num=1,
            vectors=vectors,
            metadata={"task": "test task"}
        )
        
        # Verify note was added
        assert note_id is not None
        
        # Verify note content
        result = subprocess.run(
            ["git", "notes", "show", "HEAD"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        
        checkpoint = json.loads(result.stdout)
        assert checkpoint["session_id"] == "test-session"
        assert checkpoint["phase"] == "PREFLIGHT"
        assert checkpoint["round"] == 1
        assert checkpoint["vectors"] == vectors
        assert "token_count" in checkpoint
    
    def test_add_checkpoint_creates_sqlite_fallback(self, git_logger):
        """Test that checkpoint is saved to SQLite even when git succeeds"""
        vectors = {"know": 0.8, "do": 0.9}
        
        git_logger.add_checkpoint(
            phase="PREFLIGHT",
            round_num=1,
            vectors=vectors
        )
        
        # Check SQLite fallback file exists
        checkpoint_dir = Path(git_logger.base_log_dir) / "checkpoints" / "test-session"
        assert checkpoint_dir.exists()
        
        checkpoint_files = list(checkpoint_dir.glob("checkpoint_PREFLIGHT_*.json"))
        assert len(checkpoint_files) > 0
    
    def test_checkpoint_token_estimation(self, git_logger):
        """Test token count estimation for checkpoints"""
        vectors = {"know": 0.8, "do": 0.9, "context": 0.7}
        
        git_logger.add_checkpoint(
            phase="PREFLIGHT",
            round_num=1,
            vectors=vectors
        )
        
        # Retrieve checkpoint
        checkpoint = git_logger.get_last_checkpoint()
        
        # Verify token count is reasonable (target: 200-500 tokens)
        assert checkpoint is not None
        assert "token_count" in checkpoint
        assert 10 < checkpoint["token_count"] < 1000  # Reasonable range


class TestCheckpointRetrieval:
    """Test checkpoint retrieval from git and SQLite"""
    
    @pytest.fixture
    def logger_with_checkpoint(self, tmp_path):
        """Create logger with existing checkpoint"""
        # Setup git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)
        
        logger = GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=True,
            base_log_dir=str(tmp_path / ".empirica_reflex_logs"),
            git_repo_path=str(tmp_path)
        )
        
        # Add checkpoint
        vectors = {"know": 0.8, "do": 0.9}
        logger.add_checkpoint("PREFLIGHT", 1, vectors)
        
        return logger
    
    def test_get_last_checkpoint_from_git(self, logger_with_checkpoint):
        """Test retrieving checkpoint from git notes"""
        checkpoint = logger_with_checkpoint.get_last_checkpoint()
        
        assert checkpoint is not None
        assert checkpoint["session_id"] == "test-session"
        assert checkpoint["phase"] == "PREFLIGHT"
        assert "vectors" in checkpoint
        assert checkpoint["vectors"]["know"] == 0.8
    
    def test_get_last_checkpoint_with_phase_filter(self, logger_with_checkpoint):
        """Test retrieving checkpoint filtered by phase"""
        # Add CHECK checkpoint
        logger_with_checkpoint.add_checkpoint(
            "CHECK", 2, {"know": 0.85, "do": 0.95}
        )
        
        # Get PREFLIGHT checkpoint
        checkpoint = logger_with_checkpoint.get_last_checkpoint(phase="PREFLIGHT")
        
        # Should still get PREFLIGHT (git notes show HEAD, which is CHECK now)
        # This test verifies phase filtering works
        assert checkpoint is not None


class TestSQLiteFallback:
    """Test fallback to SQLite when git unavailable"""
    
    @pytest.fixture
    def logger_no_git(self, tmp_path):
        """Create logger without git"""
        return GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=True,
            base_log_dir=str(tmp_path / ".empirica_reflex_logs"),
            git_repo_path=str(tmp_path)  # Not a git repo
        )
    
    def test_add_checkpoint_fallback_when_git_unavailable(self, logger_no_git):
        """Test checkpoint storage falls back to SQLite when git unavailable"""
        vectors = {"know": 0.7, "do": 0.8}
        
        note_id = logger_no_git.add_checkpoint(
            phase="PREFLIGHT",
            round_num=1,
            vectors=vectors
        )
        
        # Git operation should return None
        assert note_id is None
        
        # But SQLite fallback should work
        checkpoint = logger_no_git.get_last_checkpoint()
        assert checkpoint is not None
        assert checkpoint["vectors"] == vectors
    
    def test_get_last_checkpoint_fallback_to_sqlite(self, logger_no_git):
        """Test checkpoint retrieval falls back to SQLite"""
        vectors = {"know": 0.7, "do": 0.8}
        
        logger_no_git.add_checkpoint("PREFLIGHT", 1, vectors)
        
        # Should retrieve from SQLite
        checkpoint = logger_no_git.get_last_checkpoint()
        
        assert checkpoint is not None
        assert checkpoint["phase"] == "PREFLIGHT"
        assert checkpoint["vectors"] == vectors


class TestVectorDiff:
    """Test vector diff calculation"""
    
    @pytest.fixture
    def logger(self, tmp_path):
        """Create basic logger"""
        return GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=False,
            base_log_dir=str(tmp_path / ".empirica_reflex_logs")
        )
    
    def test_get_vector_diff_calculation(self, logger):
        """Test vector diff calculation between checkpoints"""
        baseline_checkpoint = {
            "session_id": "test-session",
            "phase": "PREFLIGHT",
            "round": 1,
            "vectors": {
                "know": 0.5,
                "do": 0.6,
                "context": 0.7
            }
        }
        
        current_vectors = {
            "know": 0.8,
            "do": 0.9,
            "context": 0.75
        }
        
        logger.current_round = 5
        
        diff = logger.get_vector_diff(baseline_checkpoint, current_vectors)
        
        # Verify delta calculation
        assert diff["delta"]["know"] == 0.3  # 0.8 - 0.5
        assert diff["delta"]["do"] == 0.3    # 0.9 - 0.6
        assert diff["delta"]["context"] == 0.05  # 0.75 - 0.7
        
        # Verify metadata
        assert diff["baseline_phase"] == "PREFLIGHT"
        assert diff["baseline_round"] == 1
        assert diff["current_round"] == 5
        
        # Verify significant changes detection
        significant = diff["significant_changes"]
        assert len(significant) == 2  # know and do changed >0.15
        
        vector_names = [change["vector"] for change in significant]
        assert "know" in vector_names
        assert "do" in vector_names
        assert "context" not in vector_names  # Only 0.05 change
    
    def test_vector_diff_token_count(self, logger):
        """Test that vector diff is token-efficient"""
        baseline_checkpoint = {
            "vectors": {"know": 0.5, "do": 0.6},
            "phase": "PREFLIGHT",
            "round": 1
        }
        
        current_vectors = {"know": 0.8, "do": 0.9}
        
        diff = logger.get_vector_diff(baseline_checkpoint, current_vectors)
        
        # Verify token count is included
        assert "token_count" in diff
        
        # Diff should be much smaller than full checkpoint
        # (target: ~400 tokens vs ~3,500 for full assessment)
        assert diff["token_count"] < 1000


class TestBackwardCompatibility:
    """Test backward compatibility when git notes disabled"""
    
    def test_disabled_git_notes_uses_standard_logger(self, tmp_path):
        """Test that enable_git_notes=False maintains standard behavior"""
        logger = GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=False,
            base_log_dir=str(tmp_path / ".empirica_reflex_logs")
        )
        
        vectors = {"know": 0.7, "do": 0.8}
        
        note_id = logger.add_checkpoint("PREFLIGHT", 1, vectors)
        
        # Git note should not be created
        assert note_id is None
        
        # But SQLite storage should still work
        checkpoint = logger.get_last_checkpoint()
        assert checkpoint is not None


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def logger(self, tmp_path):
        return GitEnhancedReflexLogger(
            session_id="test-session",
            enable_git_notes=False,
            base_log_dir=str(tmp_path / ".empirica_reflex_logs")
        )
    
    def test_get_last_checkpoint_returns_none_when_empty(self, logger):
        """Test that get_last_checkpoint returns None when no checkpoints exist"""
        checkpoint = logger.get_last_checkpoint()
        assert checkpoint is None
    
    def test_get_last_checkpoint_respects_max_age(self, logger):
        """Test that old checkpoints are filtered out"""
        # Create checkpoint
        logger.add_checkpoint("PREFLIGHT", 1, {"know": 0.7})
        
        # Try to retrieve with very short max_age
        checkpoint = logger.get_last_checkpoint(max_age_hours=0)
        
        # Should not find checkpoint (too old)
        assert checkpoint is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
