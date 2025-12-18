"""
Unit tests for BEADS integration adapter

Tests subprocess-based integration with bd CLI.
Uses mocking to avoid dependency on bd CLI installation.
"""

import pytest
import json
import subprocess
from unittest.mock import Mock, patch, MagicMock
from empirica.integrations.beads import BeadsAdapter


class TestBeadsAdapter:
    """Test suite for BeadsAdapter subprocess integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.adapter = BeadsAdapter()
        # Reset availability cache
        self.adapter._available = None
    
    def test_is_available_when_bd_installed(self):
        """Test availability check when bd CLI is installed"""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = "bd version 0.20.1"
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            assert self.adapter.is_available() is True
            mock_run.assert_called_once()
    
    def test_is_available_when_bd_not_installed(self):
        """Test availability check when bd CLI is not installed"""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            assert self.adapter.is_available() is False
    
    def test_is_available_caches_result(self):
        """Test that availability check is cached"""
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = "bd version 0.20.1"
            mock_run.return_value = mock_result
            
            # First call
            self.adapter.is_available()
            # Second call should use cache
            self.adapter.is_available()
            
            # Should only call subprocess once
            assert mock_run.call_count == 1
    
    def test_create_issue_success(self):
        """Test creating BEADS issue successfully"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.stdout = json.dumps({"id": "bd-a1b2", "title": "Test Issue"})
                mock_result.returncode = 0
                mock_run.return_value = mock_result
                
                issue_id = self.adapter.create_issue(
                    title="Test Issue",
                    description="Test description",
                    priority=1,
                    issue_type="task",
                    labels=["test"]
                )
                
                assert issue_id == "bd-a1b2"
                mock_run.assert_called_once()
                
                # Verify command structure
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "bd"
                assert call_args[1] == "create"
                assert "Test Issue" in call_args
                assert "--json" in call_args
    
    def test_create_issue_when_bd_not_available(self):
        """Test create_issue returns None when bd not available"""
        with patch.object(self.adapter, 'is_available', return_value=False):
            issue_id = self.adapter.create_issue("Test")
            assert issue_id is None
    
    def test_create_issue_subprocess_error(self):
        """Test create_issue handles subprocess errors gracefully"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'bd')):
                issue_id = self.adapter.create_issue("Test")
                assert issue_id is None
    
    def test_create_issue_json_parse_error(self):
        """Test create_issue handles JSON parse errors"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.stdout = "invalid json"
                mock_run.return_value = mock_result
                
                issue_id = self.adapter.create_issue("Test")
                assert issue_id is None
    
    def test_add_dependency_success(self):
        """Test adding dependency between issues"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result
                
                success = self.adapter.add_dependency(
                    child_id="bd-a1b2",
                    parent_id="bd-f14c",
                    dep_type="blocks"
                )
                
                assert success is True
                call_args = mock_run.call_args[0][0]
                assert call_args == ['bd', 'dep', 'add', 'bd-a1b2', 'bd-f14c', '--type', 'blocks']
    
    def test_add_dependency_when_bd_not_available(self):
        """Test add_dependency returns False when bd not available"""
        with patch.object(self.adapter, 'is_available', return_value=False):
            success = self.adapter.add_dependency("bd-a1b2", "bd-f14c")
            assert success is False
    
    def test_get_ready_work_success(self):
        """Test getting ready work from BEADS"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.stdout = json.dumps([
                    {"id": "bd-a1b2", "title": "Task 1", "priority": 1},
                    {"id": "bd-f14c", "title": "Task 2", "priority": 2}
                ])
                mock_run.return_value = mock_result
                
                ready_work = self.adapter.get_ready_work(limit=10, priority=1)
                
                assert len(ready_work) == 2
                assert ready_work[0]["id"] == "bd-a1b2"
    
    def test_get_ready_work_when_bd_not_available(self):
        """Test get_ready_work returns empty list when bd not available"""
        with patch.object(self.adapter, 'is_available', return_value=False):
            ready_work = self.adapter.get_ready_work()
            assert ready_work == []
    
    def test_update_status_success(self):
        """Test updating issue status"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result
                
                success = self.adapter.update_status("bd-a1b2", "in_progress")
                
                assert success is True
                call_args = mock_run.call_args[0][0]
                assert 'bd-a1b2' in call_args
                assert 'in_progress' in call_args
    
    def test_close_issue_success(self):
        """Test closing issue"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result
                
                success = self.adapter.close_issue("bd-a1b2", "Completed")
                
                assert success is True
                call_args = mock_run.call_args[0][0]
                assert call_args == ['bd', 'close', 'bd-a1b2', '--reason', 'Completed']
    
    def test_get_issue_success(self):
        """Test getting issue details"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.stdout = json.dumps({
                    "id": "bd-a1b2",
                    "title": "Test Issue",
                    "status": "open",
                    "priority": 1
                })
                mock_run.return_value = mock_result
                
                issue = self.adapter.get_issue("bd-a1b2")
                
                assert issue is not None
                assert issue["id"] == "bd-a1b2"
                assert issue["title"] == "Test Issue"
    
    def test_get_issue_when_bd_not_available(self):
        """Test get_issue returns None when bd not available"""
        with patch.object(self.adapter, 'is_available', return_value=False):
            issue = self.adapter.get_issue("bd-a1b2")
            assert issue is None
    
    def test_get_dependency_tree_success(self):
        """Test getting dependency tree"""
        with patch.object(self.adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.stdout = "🌲 Dependency tree for bd-a1b2:\n→ bd-a1b2: Test [P1] (open)"
                mock_run.return_value = mock_result
                
                tree = self.adapter.get_dependency_tree("bd-a1b2")
                
                assert tree is not None
                assert "bd-a1b2" in tree
                assert "🌲" in tree
    
    def test_get_dependency_tree_when_bd_not_available(self):
        """Test get_dependency_tree returns None when bd not available"""
        with patch.object(self.adapter, 'is_available', return_value=False):
            tree = self.adapter.get_dependency_tree("bd-a1b2")
            assert tree is None


class TestBeadsAdapterIntegration:
    """Integration tests that verify real subprocess behavior patterns"""
    
    def test_subprocess_timeout_handling(self):
        """Test that timeout is configured correctly"""
        adapter = BeadsAdapter()
        
        with patch.object(adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                # Simulate timeout
                mock_run.side_effect = subprocess.TimeoutExpired('bd', 10)
                
                # Should handle timeout gracefully
                issue_id = adapter.create_issue("Test")
                assert issue_id is None
    
    def test_empty_json_response(self):
        """Test handling of empty JSON responses"""
        adapter = BeadsAdapter()
        
        with patch.object(adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.stdout = ""
                mock_run.return_value = mock_result
                
                issue_id = adapter.create_issue("Test")
                assert issue_id is None
    
    def test_malformed_beads_id(self):
        """Test handling of malformed BEADS IDs"""
        adapter = BeadsAdapter()
        
        with patch.object(adapter, 'is_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.stdout = json.dumps({"id": None, "title": "Test"})
                mock_run.return_value = mock_result
                
                issue_id = adapter.create_issue("Test")
                # Should return None from response even though subprocess succeeded
                assert issue_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
