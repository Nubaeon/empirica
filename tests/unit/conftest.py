"""
Pytest configuration and fixtures for Empirica tests
"""
import sys
from pathlib import Path

# Add semantic_self_aware_kit parent directory to path
# This should point to /home/yogapad/empirical-ai/semantic_self_aware_kit
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
