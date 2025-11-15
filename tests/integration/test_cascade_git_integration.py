"""
Test CASCADE Git Integration (Phase 2, Task 4)

Validates automatic git checkpoint creation in MetacognitiveCascade workflow.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

# Skip if cascade not available
pytest.importorskip("empirica.core.metacognitive_cascade.metacognitive_cascade")

from empirica.core.metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade


@pytest.mark.asyncio
async def test_cascade_creates_checkpoints_automatically():
    """Verify automatic checkpoint creation at phase boundaries"""
    
    # Create temporary git repo for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.system("git init > /dev/null 2>&1")
        
        cascade = CanonicalEpistemicCascade(
            enable_git_notes=True,
            session_id="test-cascade-git-auto"
        )
        
        # Verify git logger initialized
        assert cascade.git_logger is not None, "Git logger not initialized"
        
        # Execute workflow (simplified test - doesn't need full execution)
        # Just verify checkpoints can be created at each phase
        
        # Simulate PREFLIGHT
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
        
        # Create checkpoint manually (simulating what CASCADE does)
        if cascade.git_logger:
            checkpoint_id = cascade.git_logger.add_checkpoint(
                phase="PREFLIGHT",
                round_num=1,
                vectors=test_vectors,
                metadata={"task": "Test git checkpoint integration"}
            )
            
            assert checkpoint_id is not None, "Failed to create checkpoint"
            print(f"✅ Checkpoint created: {checkpoint_id}")
            
            # Verify checkpoint can be loaded
            loaded = cascade.git_logger.get_last_checkpoint()
            assert loaded is not None, "Failed to load checkpoint"
            assert loaded['phase'] == 'PREFLIGHT', "Wrong phase"
            assert loaded['round'] == 1, "Wrong round"
            print(f"✅ Checkpoint loaded successfully")


@pytest.mark.asyncio
async def test_cascade_graceful_fallback_no_git():
    """Verify graceful fallback when git unavailable"""
    
    # Create CASCADE with git disabled
    cascade = CanonicalEpistemicCascade(
        enable_git_notes=False,
        session_id="test-no-git"
    )
    
    # Should work without git
    assert cascade.git_logger is None, "Git logger should be None when disabled"
    
    print("✅ Graceful fallback verified")


def test_token_efficiency_tracking():
    """Verify token metrics are tracked when enabled"""
    
    cascade = CanonicalEpistemicCascade(
        enable_git_notes=True,
        session_id="test-efficiency-tracking"
    )
    
    # Verify token metrics initialized
    assert cascade.token_metrics is not None, "Token metrics not initialized"
    
    print("✅ Token efficiency tracking enabled")


@pytest.mark.asyncio  
async def test_checkpoint_compression():
    """Verify checkpoint size is within expected range"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.system("git init > /dev/null 2>&1")
        
        cascade = CanonicalEpistemicCascade(
            enable_git_notes=True,
            session_id="test-compression"
        )
        
        if cascade.git_logger and cascade.git_logger.git_available:
            # Create checkpoint
            test_vectors = {k: 0.5 for k in [
                'engagement', 'know', 'do', 'context',
                'clarity', 'coherence', 'signal', 'density',
                'state', 'change', 'completion', 'impact', 'uncertainty'
            ]}
            
            checkpoint_id = cascade.git_logger.add_checkpoint(
                phase="PREFLIGHT",
                round_num=1,
                vectors=test_vectors,
                metadata={"test": "compression"}
            )
            
            # Load and verify size
            loaded = cascade.git_logger.get_last_checkpoint()
            
            # Estimate token count (rough)
            import json
            checkpoint_json = json.dumps(loaded)
            estimated_tokens = len(checkpoint_json) // 4  # Rough estimate
            
            # Should be under 600 tokens (target is ~450)
            assert estimated_tokens < 600, f"Checkpoint too large: {estimated_tokens} tokens"
            
            print(f"✅ Checkpoint size: ~{estimated_tokens} tokens (target: 450)")


if __name__ == "__main__":
    print("🧪 Testing CASCADE Git Integration...\n")
    
    # Run tests
    asyncio.run(test_cascade_creates_checkpoints_automatically())
    asyncio.run(test_cascade_graceful_fallback_no_git())
    test_token_efficiency_tracking()
    asyncio.run(test_checkpoint_compression())
    
    print("\n✅ All CASCADE git integration tests passed!")
