"""
Test project-switch command
"""

import pytest
from empirica.data.session_database import SessionDatabase


def test_project_switch_resolves_by_name():
    """Test that project-switch can resolve project by name"""
    db = SessionDatabase()
    
    # Create test project
    project_id = db.projects.create_project(
        name="test-switch-project",
        description="Test project for switch command",
        repos=["https://github.com/test/repo.git"]
    )
    
    # Test resolution by name
    resolved_id = db.projects.resolve_project_id("test-switch-project")
    assert resolved_id == project_id
    
    # Test resolution by ID
    resolved_id = db.projects.resolve_project_id(project_id)
    assert resolved_id == project_id
    
    db.close()


def test_project_switch_resolves_by_id():
    """Test that project-switch can resolve project by UUID"""
    db = SessionDatabase()
    
    # Create test project
    project_id = db.projects.create_project(
        name="test-switch-by-id",
        description="Test project",
        repos=[]
    )
    
    # Resolve by full UUID
    resolved_id = db.projects.resolve_project_id(project_id)
    assert resolved_id == project_id
    
    db.close()


def test_project_switch_handles_not_found():
    """Test that project-switch handles non-existent projects"""
    db = SessionDatabase()
    
    # Try to resolve non-existent project
    resolved_id = db.projects.resolve_project_id("non-existent-project-12345")
    assert resolved_id is None
    
    db.close()


def test_project_switch_case_insensitive():
    """Test that project name resolution is case-insensitive"""
    db = SessionDatabase()
    
    # Create test project
    project_id = db.projects.create_project(
        name="TestCaseProject",
        description="Test case sensitivity",
        repos=[]
    )
    
    # Resolve with different cases
    assert db.projects.resolve_project_id("TestCaseProject") == project_id
    assert db.projects.resolve_project_id("testcaseproject") == project_id
    assert db.projects.resolve_project_id("TESTCASEPROJECT") == project_id
    
    db.close()
