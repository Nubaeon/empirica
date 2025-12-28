"""
Pytest configuration and fixtures for Empirica tests
"""
import sys
from pathlib import Path

# Add parent directory to path for test imports
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import pytest


@pytest.fixture
def sample_task():
    """Sample task for testing"""
    return "Test task for validation"


@pytest.fixture
def sample_context():
    """Sample context for testing"""
    return {
        "workspace": "/test/workspace",
        "goal": "testing",
        "environment": "test"
    }


@pytest.fixture
def confidence_threshold():
    """Default confidence threshold"""
    return 0.7
