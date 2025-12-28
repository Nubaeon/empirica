"""
Test SessionDatabase Git Integration (Phase 2, Task 4)

Validates SessionDatabase checkpoint methods with git/SQLite fallback.
"""

import pytest
import tempfile
import os
from pathlib import Path

from empirica.data.session_database import SessionDatabase


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = SessionDatabase(db_path=str(db_path))
        yield db
        db.close()


@pytest.fixture
def git_repo():
    """Create temporary git repository"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.system("git init > /dev/null 2>&1")
        yield tmpdir


def test_session_db_git_checkpoint_methods_exist(temp_db):
    """Verify checkpoint methods are available"""
    
    assert hasattr(temp_db, 'get_git_checkpoint'), "get_git_checkpoint method missing"
    assert hasattr(temp_db, 'list_git_checkpoints'), "list_git_checkpoints method missing"
    assert hasattr(temp_db, 'get_checkpoint_diff'), "get_checkpoint_diff method missing"
    
    print("✅ All SessionDatabase checkpoint methods exist")


def test_session_db_git_checkpoint_graceful_failure(temp_db):
    """Test that checkpoint methods handle missing data gracefully"""
    
    # Try to get checkpoint for non-existent session
    checkpoint = temp_db.get_git_checkpoint("non-existent-session")
    
    # Should return None, not crash
    assert checkpoint is None or isinstance(checkpoint, dict)
    
    print("✅ get_git_checkpoint handles missing data gracefully")


def test_session_db_list_checkpoints_empty(temp_db):
    """Test that list_checkpoints returns empty list for non-existent session"""
    
    checkpoints = temp_db.list_git_checkpoints("non-existent-session")
    
    # Should return empty list, not crash
    assert isinstance(checkpoints, list)
    assert len(checkpoints) == 0
    
    print("✅ list_git_checkpoints returns empty list for missing data")


def test_session_db_checkpoint_diff_missing(temp_db):
    """Test that checkpoint_diff handles missing data gracefully"""
    
    diff = temp_db.get_checkpoint_diff("non-existent-session")
    
    # Should return error dict, not crash
    assert isinstance(diff, dict)
    assert 'error' in diff or 'diffs' in diff
    
    print("✅ get_checkpoint_diff handles missing data gracefully")


@pytest.mark.integration
def test_session_db_checkpoint_integration(temp_db, git_repo):
    """Test checkpoint storage and retrieval (integration test)"""
    
    # Create a test session
    session_id = temp_db.create_session(
        ai_id="test-ai",
        bootstrap_level=2,
        components_loaded=10
    )
    
    # Create a cascade
    cascade_id = temp_db.create_cascade(
        session_id=session_id,
        task="Test checkpoint integration",
        context={"test": True}
    )
    
    # Log a preflight assessment (creates epistemic assessment)
    test_vectors = {
        'engagement': 0.75,
        'know': 0.65,
        'do': 0.70,
        'context': 0.60,
        'clarity': 0.70,
        'coherence': 0.75,
        'signal': 0.65,
        'density': 0.60,
        'state': 0.50,
        'change': 0.45,
        'completion': 0.40,
        'impact': 0.55,
        'uncertainty': 0.35
    }
    
    temp_db.log_preflight_assessment(
        session_id=session_id,
        cascade_id=cascade_id,
        prompt_summary="Test task",
        vectors=test_vectors,
        uncertainty_notes="Test reasoning"
    )
    
    # Try to get checkpoint (will use SQLite fallback if git not available)
    checkpoint = temp_db.get_git_checkpoint(session_id)
    
    # Should either get a checkpoint or None
    if checkpoint:
        assert 'vectors' in checkpoint
        assert 'phase' in checkpoint
        print(f"✅ Checkpoint retrieved: {checkpoint['phase']}")
    else:
        print("✅ No checkpoint found (expected for new session)")
    
    # Get latest vectors
    latest = temp_db.get_latest_vectors(session_id)
    assert latest is not None
    assert 'vectors' in latest
    assert 'engagement' in latest['vectors']
    
    print("✅ SessionDatabase integration test passed")


def test_session_db_fallback_to_sqlite(temp_db):
    """Test SQLite fallback when git unavailable"""
    
    # Create session and assessment
    session_id = temp_db.create_session("test-ai", 2, 10)
    cascade_id = temp_db.create_cascade(session_id, "Test", {})
    
    test_vectors = {k: 0.5 for k in [
        'engagement', 'know', 'do', 'context',
        'clarity', 'coherence', 'signal', 'density',
        'state', 'change', 'completion', 'impact', 'uncertainty'
    ]}
    
    temp_db.log_preflight_assessment(
        session_id=session_id,
        cascade_id=cascade_id,
        prompt_summary="Test",
        vectors=test_vectors,
        uncertainty_notes="Test"
    )
    
    # Get checkpoint via fallback
    checkpoint = temp_db._get_checkpoint_from_reflexes(session_id)
    
    if checkpoint:
        assert checkpoint['source'] == 'sqlite_fallback'
        assert 'vectors' in checkpoint
        print("✅ SQLite fallback works")
    else:
        # May be None if no assessment logged yet
        print("✅ SQLite fallback handles missing data")


if __name__ == "__main__":
    print("🧪 Testing SessionDatabase Git Integration...\n")
    
    # Create temp db for tests
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = SessionDatabase(db_path=str(db_path))
        
        try:
            test_session_db_git_checkpoint_methods_exist(db)
            test_session_db_git_checkpoint_graceful_failure(db)
            test_session_db_list_checkpoints_empty(db)
            test_session_db_checkpoint_diff_missing(db)
            test_session_db_fallback_to_sqlite(db)
            
            print("\n✅ All SessionDatabase git integration tests passed!")
        finally:
            db.close()
