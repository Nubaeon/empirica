"""
Pytest configuration and shared fixtures for Empirica tests

This file provides common fixtures and configuration for all Empirica tests,
following patterns from Pydantic AI's testing approach.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from typing import Iterator, Dict, Any
import shutil
import sys
import os


# =============================================================================
# Fixtures: Temporary Directories
# ============================================================================

@pytest.fixture
def temp_empirica_dir() -> Iterator[Path]:
    """Create temporary .empirica directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        empirica_path = Path(tmpdir) / ".empirica"
        empirica_path.mkdir()
        (empirica_path / "sessions").mkdir()
        
        # Create credentials template
        creds_template = empirica_path / "credentials.yaml.template"
        creds_template.write_text("""# Empirica Credentials Template
# Copy to credentials.yaml and add your API keys

# OpenAI
openai_api_key: \"your-key-here\"

# Anthropic
anthropic_api_key: \"your-key-here\"
"""
        )
        
        yield empirica_path


@pytest.fixture
def temp_reflex_logs_dir() -> Iterator[Path]:
    """Create temporary reflex logs directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = Path(tmpdir) / ".empirica_reflex_logs"
        logs_path.mkdir()
        (logs_path / "cascade").mkdir()
        yield logs_path


# =============================================================================
# Fixtures: Database
# ============================================================================

@pytest.fixture
def temp_session_db(temp_empirica_dir):
    """Create temporary session database for testing"""
    from empirica.data.session_database import SessionDatabase
    
    db_path = temp_empirica_dir / "sessions" / "test.db"
    db = SessionDatabase(db_path=str(db_path))
    
    yield db
    
    db.close()


# =============================================================================
# Fixtures: Sample Data
# ============================================================================

@pytest.fixture
def sample_assessment_response() -> Dict[str, Any]:
    """Sample genuine assessment response for testing"""
    return {
        "engagement": {
            "score": 0.8,
            "rationale": "Genuine collaborative intelligence with user"
        },
        "foundation": {
            "know": {
                "score": 0.6,
                "rationale": "Moderate domain knowledge of the task area"
            },
            "do": {
                "score": 0.7,
                "rationale": "Good execution capability for this type of task"
            },
            "context": {
                "score": 0.5,
                "rationale": "Adequate environmental context, but some gaps"
            }
        },
        "comprehension": {
            "clarity": {
                "score": 0.8,
                "rationale": "Clear semantic understanding of requirements"
            },
            "coherence": {
                "score": 0.7,
                "rationale": "Coherent grasp of context and relationships"
            },
            "signal": {
                "score": 0.6,
                "rationale": "Key priority signals identified"
            },
            "density": {
                "score": 0.4,
                "rationale": "Manageable cognitive complexity"
            }
        },
        "execution": {
            "state": {
                "score": 0.5,
                "rationale": "Basic environment state mapping"
            },
            "change": {
                "score": 0.6,
                "rationale": "Can track modification trajectories"
            },
            "completion": {
                "score": 0.7,
                "rationale": "Clear path to completion criteria"
            },
            "impact": {
                "score": 0.6,
                "rationale": "Understand consequence propagation"
            }
        },
        "uncertainty": {
            "score": 0.4,
            "rationale": "Moderate uncertainty about edge cases and unknowns"
        }
    }


@pytest.fixture
def sample_preflight_vectors() -> Dict[str, float]:
    """Sample preflight vector scores for testing"""
    return {
        "know": 0.5,
        "do": 0.6,
        "context": 0.4,
        "clarity": 0.7,
        "coherence": 0.6,
        "signal": 0.5,
        "density": 0.5,
        "state": 0.4,
        "change": 0.5,
        "completion": 0.6,
        "impact": 0.5,
        "engagement": 0.7,
        "uncertainty": 0.5
    }


@pytest.fixture
def sample_postflight_vectors() -> Dict[str, float]:
    """Sample postflight vector scores (showing learning)"""
    return {
        "know": 0.7,  # Increased
        "do": 0.7,    # Increased
        "context": 0.6,  # Increased
        "clarity": 0.8,  # Increased
        "coherence": 0.7,
        "signal": 0.6,
        "density": 0.5,
        "state": 0.6,  # Increased
        "change": 0.6,
        "completion": 0.7,
        "impact": 0.6,
        "engagement": 0.8,  # Increased
        "uncertainty": 0.3  # Decreased (more confident)
    }


# =============================================================================
# Fixtures: Test Helpers
# ============================================================================

@pytest.fixture
def mock_llm_response():
    """Factory fixture for creating mock LLM responses"""
    def _make_response(vectors: Dict[str, float]) -> str:
        """Create a mock LLM response with given vectors"""
        response = {
            "engagement": {
                "score": vectors.get("engagement", 0.7),
                "rationale": "Mock engagement rationale"
            },
            "foundation": {
                "know": {
                    "score": vectors.get("know", 0.5),
                    "rationale": "Mock knowledge rationale"
                },
                "do": {
                    "score": vectors.get("do", 0.5),
                    "rationale": "Mock capability rationale"
                },
                "context": {
                    "score": vectors.get("context", 0.5),
                    "rationale": "Mock context rationale"
                }
            },
            "comprehension": {
                "clarity": {
                    "score": vectors.get("clarity", 0.5),
                    "rationale": "Mock clarity rationale"
                },
                "coherence": {
                    "score": vectors.get("coherence", 0.5),
                    "rationale": "Mock coherence rationale"
                },
                "signal": {
                    "score": vectors.get("signal", 0.5),
                    "rationale": "Mock signal rationale"
                },
                "density": {
                    "score": vectors.get("density", 0.5),
                    "rationale": "Mock density rationale"
                }
            },
            "execution": {
                "state": {
                    "score": vectors.get("state", 0.5),
                    "rationale": "Mock state rationale"
                },
                "change": {
                    "score": vectors.get("change", 0.5),
                    "rationale": "Mock change rationale"
                },
                "completion": {
                    "score": vectors.get("completion", 0.5),
                    "rationale": "Mock completion rationale"
                },
                "impact": {
                    "score": vectors.get("impact", 0.5),
                    "rationale": "Mock impact rationale"
                }
            },
            "uncertainty": {
                "score": vectors.get("uncertainty", 0.5),
                "rationale": "Mock uncertainty rationale"
            }
        }
        return json.dumps(response)
    
    return _make_response


# =============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers",
        "integrity: Framework integrity tests (core principle validation)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers",
        "requires_mcp: Tests that require MCP server running"
    )


@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    """Automatically clean up test artifacts after each test"""
    yield
    
    # Clean up any test databases
    test_dbs = Path(".").glob("test*.db")
    for db in test_dbs:
        try:
            db.unlink()
        except:
            pass
    
    # Clean up test reflex logs
    test_logs = Path(".empirica_reflex_logs_test")
    if test_logs.exists():
        shutil.rmtree(test_logs, ignore_errors=True)


# =============================================================================
# Assertion Helpers (inspired by Pydantic AI's dirty-equals usage)
# ============================================================================

@pytest.fixture
def assert_vectors_valid():
    """Helper to assert epistemic vectors are valid"""
    def _assert(vectors: Dict[str, float]):
        """Assert all vector scores are in valid range [0.0, 1.0]"""
        required_vectors = [
            "know", "do", "context",
            "clarity", "coherence", "signal", "density",
            "state", "change", "completion", "impact",
            "engagement", "uncertainty"
        ]
        
        for vector in required_vectors:
            assert vector in vectors, f"Missing vector: {vector}"
            score = vectors[vector]
            assert isinstance(score, (int, float)), f"{vector} score must be numeric"
            assert 0.0 <= score <= 1.0, f"{vector} score must be in [0.0, 1.0], got {score}"
    
    return _assert


@pytest.fixture
def assert_genuine_assessment():
    """Helper to assert assessment contains genuine rationale"""
    def _assert(assessment_dict: Dict[str, Any]):
        """Assert assessment contains genuine rationale, not template text"""
        # Check engagement
        assert "engagement" in assessment_dict
        assert "rationale" in assessment_dict["engagement"]
        engagement_rationale = assessment_dict["engagement"]["rationale"]
        assert len(engagement_rationale) > 10, "Rationale too short to be genuine"
        
        # Check foundation vectors have rationale
        for vector in ["know", "do", "context"]:
            assert vector in assessment_dict["foundation"]
            assert "rationale" in assessment_dict["foundation"][vector]
            rationale = assessment_dict["foundation"][vector]["rationale"]
            assert len(rationale) > 10, f"{vector} rationale too short"
            # Ensure it's not just template text
            assert rationale.lower() not in [
                "adequate",
                "sufficient",
                "baseline",
                "default"
            ], f"{vector} rationale appears to be template text"
    
    return _assert