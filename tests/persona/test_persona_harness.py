"""
Tests for PersonaHarness runtime container

Tests:
- Creating harness from persona
- Applying persona priors to assessments
- Sentinel communication
- Task execution with persona-specific behavior
"""

import pytest
import asyncio
from pathlib import Path

from empirica.core.persona import PersonaManager
from empirica.core.persona.harness import (
    PersonaHarness,
    MessageType,
    PersonaMessage,
    SentinelMessage
)


def test_harness_initialization(tmp_path):
    """Test creating PersonaHarness from persona"""

    # Create a security persona
    manager = PersonaManager(personas_dir=str(tmp_path))
    persona = manager.create_persona(
        persona_id="test_security",
        name="Test Security Expert",
        template="builtin:security"
    )
    manager.save_persona(persona)

    # Create harness
    harness = PersonaHarness(
        persona_id="test_security",
        personas_dir=str(tmp_path),
        enable_sentinel=False  # Disable for testing
    )

    assert harness.persona_id == "test_security"
    assert harness.persona.name == "Test Security Expert"
    assert harness.persona.get_type() == "security"


def test_persona_prior_application(tmp_path):
    """Test that persona priors are applied to assessments"""

    # Create security persona (high KNOW prior)
    manager = PersonaManager(personas_dir=str(tmp_path))
    security = manager.create_persona(
        persona_id="test_security",
        name="Security Expert",
        template="builtin:security"
    )
    manager.save_persona(security)

    # Create harness
    harness = PersonaHarness(
        persona_id="test_security",
        personas_dir=str(tmp_path),
        enable_sentinel=False
    )

    # Check that persona has high KNOW prior
    assert security.epistemic_config.priors['know'] == 0.90

    # The harness should apply this prior during assessment
    # (This is tested via integration test with actual CASCADE execution)


def test_investigation_profile_selection(tmp_path):
    """Test that investigation profile matches persona type"""

    manager = PersonaManager(personas_dir=str(tmp_path))

    # Create different persona types
    security = manager.create_persona("sec", "Security", template="builtin:security")
    manager.save_persona(security)

    performance = manager.create_persona("perf", "Performance", template="builtin:performance")
    manager.save_persona(performance)

    # Create harnesses
    security_harness = PersonaHarness("sec", personas_dir=str(tmp_path), enable_sentinel=False)
    performance_harness = PersonaHarness("perf", personas_dir=str(tmp_path), enable_sentinel=False)

    # Check profile selection
    sec_profile = security_harness._select_investigation_profile()
    perf_profile = performance_harness._select_investigation_profile()

    assert sec_profile == "cautious"  # Security is cautious
    assert perf_profile == "autonomous_agent"  # Performance is autonomous


def test_persona_message_creation():
    """Test creating and signing persona messages"""

    from empirica.core.identity import AIIdentity

    # Create identity for signing
    identity = AIIdentity(ai_id="test_persona")
    identity.generate_keypair()

    # Create message
    message = PersonaMessage(
        message_type=MessageType.STATUS_REPORT,
        persona_id="test_persona",
        payload={"phase": "CHECK", "confidence": 0.85}
    )

    # Sign message
    message.sign(identity)

    assert message.signature is not None
    assert len(message.signature) > 0

    # Verify message can be serialized
    msg_dict = message.to_dict()
    assert msg_dict['message_type'] == 'status_report'
    assert msg_dict['persona_id'] == 'test_persona'
    assert msg_dict['signature'] is not None

    # Verify message can be deserialized
    restored = PersonaMessage.from_dict(msg_dict)
    assert restored.message_type == MessageType.STATUS_REPORT
    assert restored.persona_id == "test_persona"
    assert restored.signature == message.signature


def test_sentinel_message_creation():
    """Test creating Sentinel messages"""

    from empirica.core.identity import AIIdentity

    identity = AIIdentity(ai_id="sentinel")
    identity.generate_keypair()

    message = SentinelMessage(
        message_type=MessageType.TASK_ASSIGNMENT,
        persona_id="security_expert",
        payload={
            "task": "Review authentication code",
            "priority": "high"
        }
    )

    message.sign(identity)

    assert message.signature is not None

    # Verify serialization
    msg_dict = message.to_dict()
    assert msg_dict['message_type'] == 'task_assignment'
    assert msg_dict['payload']['task'] == "Review authentication code"


def test_persona_findings_extraction(tmp_path):
    """Test extracting persona-specific findings"""

    manager = PersonaManager(personas_dir=str(tmp_path))
    security = manager.create_persona("sec", "Security", template="builtin:security")
    manager.save_persona(security)

    harness = PersonaHarness("sec", personas_dir=str(tmp_path), enable_sentinel=False)

    # Mock CASCADE result
    cascade_result = {
        'action': 'investigate',
        'confidence': 0.65,
        'rationale': 'Need to review authentication and authorization logic',
        'execution_guidance': ['Verify input validation', 'Check for SQL injection']
    }

    # Extract persona findings
    findings = harness._extract_persona_findings(
        cascade_result,
        focus_domains=['security', 'authentication', 'authorization']
    )

    # Should identify authentication/authorization mentions
    assert any('authentication' in f.lower() for f in findings)
    assert any('authorization' in f.lower() for f in findings)


def test_persona_recommendation_generation(tmp_path):
    """Test persona-specific recommendation generation"""

    manager = PersonaManager(personas_dir=str(tmp_path))
    security = manager.create_persona("sec", "Security", template="builtin:security")
    ux = manager.create_persona("ux", "UX", template="builtin:ux")
    manager.save_persona(security)
    manager.save_persona(ux)

    security_harness = PersonaHarness("sec", personas_dir=str(tmp_path), enable_sentinel=False)
    ux_harness = PersonaHarness("ux", personas_dir=str(tmp_path), enable_sentinel=False)

    cascade_result = {'action': 'proceed', 'confidence': 0.80}

    # Security recommendation (should emphasize caution)
    sec_rec = security_harness._generate_persona_recommendation(cascade_result, 'security')
    assert 'SECURITY' in sec_rec or 'CAUTION' in sec_rec

    # UX recommendation (should emphasize user experience)
    ux_rec = ux_harness._generate_persona_recommendation(cascade_result, 'ux')
    assert 'UX' in ux_rec or 'USER' in ux_rec.upper()


def test_harness_task_execution_mock(tmp_path):
    """Test task execution with mocked CASCADE (no real LLM calls)"""

    # This is a simplified test - full integration test would require LLM
    manager = PersonaManager(personas_dir=str(tmp_path))
    security = manager.create_persona("sec", "Security", template="builtin:security")
    manager.save_persona(security)

    harness = PersonaHarness("sec", personas_dir=str(tmp_path), enable_sentinel=False)

    # Get persona info (smoke test)
    info = harness.get_persona_info()

    assert info['persona_id'] == 'sec'
    assert info['type'] == 'security'
    assert 'security' in info['focus_domains']
    assert info['thresholds']['confidence_to_proceed'] == 0.85  # Security is cautious


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
