import pytest
import uuid


@pytest.fixture
def test_session_id():
    """Generate test session ID"""
    return str(uuid.uuid4())


@pytest.fixture
def test_goal_id():
    """Generate test goal ID"""
    return str(uuid.uuid4())


@pytest.fixture
def test_vectors():
    """Standard test vectors"""
    return {
        "engagement": 0.8,
        "know": 0.7,
        "do": 0.7,
        "context": 0.8,
        "clarity": 0.9,
        "coherence": 0.9,
        "signal": 0.8,
        "density": 0.4,
        "state": 0.7,
        "change": 0.7,
        "completion": 0.6,
        "impact": 0.7,
        "uncertainty": 0.3
    }