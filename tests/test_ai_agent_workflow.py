"""
Test AI Agent Workflow - AI-First Interface

Tests the complete AI agent workflow using config files.
Demonstrates proper usage patterns for AI agents.
"""

import json
import os
import subprocess
import tempfile
import uuid
import pytest


class TestAIAgentWorkflow:
    """Test complete AI agent workflow with config files."""

    def test_complete_cascade_workflow(self):
        """Test full CASCADE workflow: session → preflight → check → postflight"""

        # 1. CREATE SESSION
        session_config = {
            "ai_id": "test-ai-agent",
            "bootstrap_level": 1
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(session_config, f)
            session_config_path = f.name

        try:
            result = subprocess.run(
                ['empirica', 'session-create', session_config_path],
                capture_output=True,
                text=True,
                check=True
            )

            session_response = json.loads(result.stdout)
            assert session_response['ok'] is True
            assert 'session_id' in session_response
            session_id = session_response['session_id']

            # Validate session ID format (UUID)
            assert len(session_id) == 36
            assert session_id.count('-') == 4

        finally:
            os.unlink(session_config_path)

        # 2. PREFLIGHT ASSESSMENT
        preflight_config = {
            "session_id": session_id,
            "vectors": {
                "engagement": 0.85,
                "foundation": {
                    "know": 0.60,
                    "do": 0.85,
                    "context": 0.50
                },
                "comprehension": {
                    "clarity": 0.80,
                    "coherence": 0.85,
                    "signal": 0.75,
                    "density": 0.65
                },
                "execution": {
                    "state": 0.40,
                    "change": 0.85,
                    "completion": 0.70,
                    "impact": 0.90
                },
                "uncertainty": 0.70
            },
            "reasoning": "Baseline epistemic assessment for test"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(preflight_config, f)
            preflight_config_path = f.name

        try:
            result = subprocess.run(
                ['empirica', 'preflight-submit', preflight_config_path],
                capture_output=True,
                text=True,
                check=True
            )

            preflight_response = json.loads(result.stdout)
            assert preflight_response['ok'] is True
            assert 'checkpoint_id' in preflight_response
            assert preflight_response['vectors_submitted'] == 13

        finally:
            os.unlink(preflight_config_path)

        # 3. CHECK DECISION GATE
        check_config = {
            "session_id": session_id,
            "confidence": 0.78,
            "findings": [
                "Test finding 1: AI-first interface works correctly",
                "Test finding 2: JSON I/O validated"
            ],
            "unknowns": [
                "Test unknown: Schema validation coverage"
            ],
            "cycle": 1
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(check_config, f)
            check_config_path = f.name

        try:
            result = subprocess.run(
                ['empirica', 'check', check_config_path],
                capture_output=True,
                text=True,
                check=True
            )

            check_response = json.loads(result.stdout)
            assert check_response['ok'] is True
            assert 'decision' in check_response
            assert check_response['decision'] in ['proceed', 'investigate']
            assert check_response['confidence'] == 0.78

        finally:
            os.unlink(check_config_path)

        # 4. POSTFLIGHT ASSESSMENT
        postflight_config = {
            "session_id": session_id,
            "vectors": {
                "engagement": 0.85,
                "foundation": {
                    "know": 0.85,
                    "do": 0.90,
                    "context": 0.75
                },
                "comprehension": {
                    "clarity": 0.90,
                    "coherence": 0.90,
                    "signal": 0.85,
                    "density": 0.55
                },
                "execution": {
                    "state": 0.80,
                    "change": 0.90,
                    "completion": 0.90,
                    "impact": 0.95
                },
                "uncertainty": 0.30
            },
            "reasoning": "Completed test workflow. KNOW +0.25, STATE +0.40, UNCERTAINTY -0.40"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(postflight_config, f)
            postflight_config_path = f.name

        try:
            result = subprocess.run(
                ['empirica', 'postflight-submit', postflight_config_path],
                capture_output=True,
                text=True,
                check=True
            )

            postflight_response = json.loads(result.stdout)
            assert postflight_response['ok'] is True
            assert 'deltas' in postflight_response
            assert 'calibration_accuracy' in postflight_response

        finally:
            os.unlink(postflight_config_path)

    def test_goal_creation_with_config(self):
        """Test goal creation using config file."""

        # Create session first
        session_config = {"ai_id": "test-goal-agent"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(session_config, f)
            session_config_path = f.name

        try:
            result = subprocess.run(
                ['empirica', 'session-create', session_config_path],
                capture_output=True,
                text=True,
                check=True
            )
            session_id = json.loads(result.stdout)['session_id']
        finally:
            os.unlink(session_config_path)

        # Create goal
        goal_config = {
            "session_id": session_id,
            "objective": "Test AI-first goal creation",
            "scope": {
                "breadth": 0.3,
                "duration": 0.2,
                "coordination": 0.1
            },
            "success_criteria": [
                "Config file interface works",
                "JSON output validated",
                "No shell quoting issues"
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(goal_config, f)
            goal_config_path = f.name

        try:
            result = subprocess.run(
                ['empirica', 'goals-create', goal_config_path],
                capture_output=True,
                text=True,
                check=True
            )

            goal_response = json.loads(result.stdout)
            assert goal_response['ok'] is True
            assert 'goal_id' in goal_response
            assert goal_response['objective'] == "Test AI-first goal creation"

        finally:
            os.unlink(goal_config_path)

    def test_config_validation_error(self):
        """Test that invalid config produces helpful error message."""

        # Invalid config: missing required field
        invalid_config = {
            "vectors": {"engagement": 0.85}
            # Missing required session_id
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config, f)
            invalid_config_path = f.name

        try:
            result = subprocess.run(
                ['empirica', 'preflight-submit', invalid_config_path],
                capture_output=True,
                text=True
            )

            # Should fail with helpful error
            assert result.returncode != 0
            response = json.loads(result.stdout)
            assert response['ok'] is False
            assert 'error' in response
            assert 'session_id' in response['error'].lower()

        finally:
            os.unlink(invalid_config_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
