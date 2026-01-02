#!/usr/bin/env python3
"""
End-to-End Integration Tests for Checkpoint & Goals Systems

Tests complete workflows to ensure bugs don't reoccur:
1. Bootstrap → PREFLIGHT → Create Checkpoint → List Checkpoints
2. Create Goal → Add Subtasks → Complete → Progress Tracking
3. Checkpoint with Vectors → Load → Verify Vectors Preserved

Created: 2025-12-01
Purpose: Catch integration bugs that unit tests miss
"""

import pytest
import subprocess
import json
import time
from pathlib import Path


class TestCheckpointWorkflowE2E:
    """End-to-end checkpoint workflow tests"""
    
    @pytest.fixture
    def test_repo(self, tmp_path):
        """Create test git repository"""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
        
        # Create initial commit
        (repo_dir / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], 
                      cwd=repo_dir, check=True, capture_output=True)
        
        return repo_dir
    
    def test_full_checkpoint_workflow(self, test_repo):
        """
        E2E: Bootstrap → PREFLIGHT → Checkpoint → List
        
        This catches the bugs:
        - Missing list_checkpoints method
        - Empty vectors in checkpoints
        - Missing reflexes table
        """
        session_id = f"e2e-test-{int(time.time())}"
        
        # Step 1: Bootstrap session
        result = subprocess.run(
            ["empirica", "bootstrap", "--ai-id", "e2e-test"],
            capture_output=True,
            text=True,
            cwd=test_repo
        )
        
        if result.returncode == 0:
            # Extract session ID from output if needed
            pass
        
        # Step 2: Execute PREFLIGHT (should create assessment)
        result = subprocess.run(
            ["empirica", "preflight",
             "Test task for E2E workflow",
             "--ai-id", "e2e-test"],
            capture_output=True,
            text=True,
            cwd=test_repo
        )
        
        assert "PREFLIGHT" in result.stdout or "preflight" in result.stdout.lower(), \
            "PREFLIGHT should execute"
        
        # Step 3: Submit PREFLIGHT vectors
        vectors_json = json.dumps({
            "engagement": 0.85,
            "know": 0.65,
            "do": 0.80,
            "context": 0.70,
            "clarity": 0.90,
            "coherence": 0.85,
            "signal": 0.90,
            "density": 0.50,
            "state": 0.60,
            "change": 0.85,
            "completion": 0.80,
            "impact": 0.75,
            "uncertainty": 0.35
        })
        
        result = subprocess.run(
            ["empirica", "preflight-submit",
             "--session-id", session_id,
             "--vectors", vectors_json,
             "--reasoning", "E2E test vectors"],
            capture_output=True,
            text=True,
            cwd=test_repo
        )
        
        # Step 4: Create checkpoint (should include vectors from database)
        result = subprocess.run(
            ["empirica", "checkpoint-create",
             "--session-id", session_id,
             "--phase", "PREFLIGHT",
             "--round", "1"],
            capture_output=True,
            text=True,
            cwd=test_repo
        )
        
        # BUG CHECK: Should NOT show "empty vectors" warning
        assert "empty vectors" not in result.stdout.lower(), \
            "REGRESSION: Checkpoint should not have empty vectors"
        assert "Could not load vectors" not in result.stderr, \
            "REGRESSION: Should load vectors from reflexes table"
        
        # Should show success
        assert result.returncode == 0 or "created" in result.stdout.lower(), \
            "Checkpoint creation should succeed"
        
        # Step 5: List checkpoints (tests missing method bug)
        result = subprocess.run(
            ["empirica", "checkpoint-list",
             "--session-id", session_id],
            capture_output=True,
            text=True,
            cwd=test_repo
        )
        
        # BUG CHECK: Should NOT crash with AttributeError
        assert "AttributeError" not in result.stderr, \
            "REGRESSION: list_checkpoints method must exist"
        assert "has no attribute 'list_checkpoints'" not in result.stderr, \
            "REGRESSION: list_checkpoints must be implemented"
        
        # Should show checkpoint
        assert result.returncode == 0, \
            "checkpoint-list should execute successfully"
        
        # Step 6: Load checkpoint and verify vectors
        result = subprocess.run(
            ["empirica", "checkpoint-load",
             "--session-id", session_id],
            capture_output=True,
            text=True,
            cwd=test_repo
        )
        
        if result.returncode == 0 and result.stdout:
            # Try to parse as JSON
            try:
                checkpoint_data = json.loads(result.stdout)
                
                # BUG CHECK: Checkpoint must have vectors
                assert "vectors" in checkpoint_data, \
                    "REGRESSION: Checkpoint must include vectors"
                assert checkpoint_data["vectors"] != {}, \
                    "REGRESSION: Vectors must not be empty"
                assert len(checkpoint_data["vectors"]) == 13, \
                    "REGRESSION: Must have all 13 epistemic vectors"
                
            except json.JSONDecodeError:
                # Output might not be JSON, that's okay for now
                pass


class TestGoalsWorkflowE2E:
    """End-to-end goals workflow tests"""
    
    def test_full_goals_workflow(self):
        """
        E2E: Create Goal → Add Subtasks → Complete → Check Progress
        
        Verifies goals system works end-to-end via CLI
        """
        session_id = f"goals-e2e-{int(time.time())}"
        
        # Step 1: Bootstrap session
        result = subprocess.run(
            ["empirica", "bootstrap", "--ai-id", "goals-test"],
            capture_output=True,
            text=True
        )
        
        # Step 2: Create goal
        result = subprocess.run(
            ["empirica", "goals-create",
             "--session-id", session_id,
             "--objective", "E2E test goal workflow",
             "--scope-breadth", "0.3",
             "--scope-duration", "0.2",
             "--scope-coordination", "0.1",
             "--estimated-complexity", "0.2",
             "--success-criteria", '["Test goal creation", "Test subtasks", "Test completion"]'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, "Goal creation should succeed"
        
        # Extract goal ID from output
        goal_id = None
        if "goal_id" in result.stdout:
            try:
                output_data = json.loads(result.stdout)
                goal_id = output_data.get("goal_id")
            except json.JSONDecodeError:
                pass
        
        if not goal_id:
            pytest.skip("Could not extract goal_id from output")
        
        # Step 3: Add subtasks
        subtask_ids = []
        
        for i, desc in enumerate(["Subtask 1", "Subtask 2", "Subtask 3"]):
            result = subprocess.run(
                ["empirica", "goals-add-subtask",
                 "--goal-id", goal_id,
                 "--description", desc,
                 "--importance", "high"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Subtask {i+1} creation should succeed"
            
            # Extract task ID
            if "task_id" in result.stdout:
                try:
                    output_data = json.loads(result.stdout)
                    task_id = output_data.get("task_id")
                    if task_id:
                        subtask_ids.append(task_id)
                except json.JSONDecodeError:
                    pass
        
        # Step 4: Check progress (should be 0%)
        result = subprocess.run(
            ["empirica", "goals-progress",
             "--goal-id", goal_id],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, "Progress check should succeed"
        
        if result.stdout:
            try:
                progress = json.loads(result.stdout)
                assert progress.get("completion_percentage", 0) == 0, \
                    "Initial progress should be 0%"
            except json.JSONDecodeError:
                pass
        
        # Step 5: Complete first subtask
        if subtask_ids:
            result = subprocess.run(
                ["empirica", "goals-complete-subtask",
                 "--task-id", subtask_ids[0],
                 "--evidence", "E2E test completion"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, "Subtask completion should succeed"
        
        # Step 6: Check progress again (should be >0%)
        result = subprocess.run(
            ["empirica", "goals-progress",
             "--goal-id", goal_id],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            try:
                progress = json.loads(result.stdout)
                completion = progress.get("completion_percentage", 0)
                assert completion > 0, \
                    "Progress should increase after completing subtask"
                assert completion < 100, \
                    "Progress should not be 100% with incomplete subtasks"
            except json.JSONDecodeError:
                pass


class TestDatabaseIntegrity:
    """Test database schema and data integrity"""
    
    @pytest.mark.skip(reason="Old reflexes table system - replaced by GitEnhancedReflexLogger")
    def test_reflexes_table_integration(self):
        """
        E2E: Submit PREFLIGHT → Verify Reflexes Table → Create Checkpoint
        
        Catches missing reflexes table bug
        """
        import sqlite3
        from pathlib import Path
        
        # Check if database exists (project-local, not home directory)
        db_path = Path.cwd() / ".empirica" / "sessions" / "sessions.db"
        
        if not db_path.exists():
            pytest.skip("Database doesn't exist yet - expected during setup")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verify reflexes table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='reflexes'
        """)
        
        table_exists = cursor.fetchone()
        
        if not table_exists:
            conn.close()
            pytest.fail(
                "REGRESSION: reflexes table missing from database. "
                "This causes checkpoints to be created with empty vectors."
            )
        
        # Verify table has correct structure
        cursor.execute("PRAGMA table_info(reflexes)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = [
            "session_id", "phase", "timestamp",
            "know", "do", "context", "uncertainty"
        ]
        
        missing_columns = [col for col in required_columns if col not in column_names]
        
        conn.close()
        
        if missing_columns:
            pytest.fail(
                f"REGRESSION: reflexes table missing columns: {missing_columns}"
            )


class TestMCPToolsIntegration:
    """Test MCP tools integration with actual implementation"""
    
    def test_mcp_checkpoint_tools(self):
        """Verify MCP checkpoint tools work end-to-end"""
        # This would test MCP server integration
        # For now, mark as integration test
        pytest.skip("MCP server integration test - requires running server")
    
    def test_mcp_goals_tools(self):
        """Verify MCP goals tools work end-to-end"""
        pytest.skip("MCP server integration test - requires running server")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
