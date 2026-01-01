"""
Unit tests for SigningPersona class

Tests:
1. Create signing persona with valid profile and identity
2. Sign epistemic state for each CASCADE phase
3. Verify valid signatures
4. Detect invalid signatures (tampered state, wrong key)
5. Export public persona information
"""

import pytest
import json
from datetime import datetime, UTC

from empirica.core.persona.persona_profile import (
    PersonaProfile, SigningIdentityConfig, EpistemicConfig,
    CapabilitiesConfig, SentinelConfig, PersonaMetadata
)
from empirica.core.identity.ai_identity import AIIdentity
from empirica.core.persona.signing_persona import SigningPersona


@pytest.fixture
def test_identity():
    """Create test AIIdentity with Ed25519 keypair"""
    identity = AIIdentity(ai_id="test_researcher")
    identity.generate_keypair()
    return identity


@pytest.fixture
def test_persona_profile(test_identity):
    """Create test PersonaProfile"""
    return PersonaProfile(
        persona_id="researcher_test",
        name="Test Researcher",
        version="1.0.0",
        signing_identity=SigningIdentityConfig(
            user_id="test",
            identity_name="researcher_test",
            public_key=test_identity.public_key_hex(),
            reputation_score=0.75
        ),
        epistemic_config=EpistemicConfig(
            priors={
                "engagement": 0.80,
                "know": 0.60,
                "do": 0.70,
                "context": 0.65,
                "clarity": 0.60,
                "coherence": 0.65,
                "signal": 0.60,
                "density": 0.55,
                "state": 0.60,
                "change": 0.70,
                "completion": 0.05,
                "impact": 0.65,
                "uncertainty": 0.75
            },
            focus_domains=["research", "exploration", "learning"]
        ),
        metadata=PersonaMetadata(
            tags=["test", "researcher"],
            created_by="test_suite"
        )
    )


@pytest.fixture
def signing_persona(test_persona_profile, test_identity):
    """Create SigningPersona instance"""
    return SigningPersona(test_persona_profile, test_identity)


def test_signing_persona_creation(signing_persona, test_persona_profile, test_identity):
    """Test creating a SigningPersona instance"""
    assert signing_persona.persona == test_persona_profile
    assert signing_persona.identity == test_identity
    assert signing_persona.persona.persona_id == "researcher_test"


def test_signing_persona_fails_without_public_key():
    """Test that creating SigningPersona without public key raises error"""
    identity = AIIdentity(ai_id="no_key")
    # Don't load or generate keypair

    profile = PersonaProfile(
        persona_id="test",
        name="Test",
        version="1.0.0",
        signing_identity=SigningIdentityConfig(
            user_id="test",
            identity_name="test",
            public_key="a" * 64
        ),
        epistemic_config=EpistemicConfig(
            priors={
                "engagement": 0.8, "know": 0.6, "do": 0.7, "context": 0.6,
                "clarity": 0.6, "coherence": 0.6, "signal": 0.6, "density": 0.5,
                "state": 0.6, "change": 0.7, "completion": 0.05, "impact": 0.6,
                "uncertainty": 0.75
            }
        )
    )

    with pytest.raises(ValueError, match="must have public key loaded"):
        SigningPersona(profile, identity)


def test_sign_epistemic_state_preflight(signing_persona):
    """Test signing an epistemic state for PREFLIGHT phase"""
    state = {
        "engagement": 0.80,
        "know": 0.60,
        "do": 0.70,
        "context": 0.65,
        "clarity": 0.60,
        "coherence": 0.65,
        "signal": 0.60,
        "density": 0.55,
        "state": 0.60,
        "change": 0.70,
        "completion": 0.05,
        "impact": 0.65,
        "uncertainty": 0.75
    }

    signed = signing_persona.sign_epistemic_state(state, phase="PREFLIGHT")

    assert "state" in signed
    assert "signature" in signed
    assert "algorithm" in signed
    assert signed["algorithm"] == "Ed25519"
    assert signed["verified"] is False

    # Verify state contents
    canonical = signed["state"]
    assert canonical["persona_id"] == "researcher_test"
    assert canonical["phase"] == "PREFLIGHT"
    assert canonical["public_key"] == signing_persona.identity.public_key_hex()
    assert "timestamp" in canonical


def test_sign_epistemic_state_all_phases(signing_persona):
    """Test signing states for all CASCADE phases"""
    state = {
        "engagement": 0.85, "know": 0.75, "do": 0.80, "context": 0.70,
        "clarity": 0.75, "coherence": 0.75, "signal": 0.75, "density": 0.65,
        "state": 0.70, "change": 0.70, "completion": 0.20, "impact": 0.70,
        "uncertainty": 0.60
    }

    phases = ["PREFLIGHT", "INVESTIGATE", "CHECK", "ACT", "POSTFLIGHT"]

    for phase in phases:
        signed = signing_persona.sign_epistemic_state(state, phase=phase)
        assert signed["state"]["phase"] == phase
        assert len(signed["signature"]) > 0  # Signature is not empty


def test_sign_missing_vector(signing_persona):
    """Test that missing epistemic vector raises error"""
    state = {
        "engagement": 0.80,
        "know": 0.60,
        # Missing 'do' and others
    }

    with pytest.raises(ValueError, match="Missing required vector"):
        signing_persona.sign_epistemic_state(state, phase="PREFLIGHT")


def test_sign_invalid_vector_value(signing_persona):
    """Test that vector outside [0.0, 1.0] raises error"""
    state = {
        "engagement": 1.5,  # Invalid
        "know": 0.60,
        "do": 0.70,
        "context": 0.65,
        "clarity": 0.60,
        "coherence": 0.65,
        "signal": 0.60,
        "density": 0.55,
        "state": 0.60,
        "change": 0.70,
        "completion": 0.05,
        "impact": 0.65,
        "uncertainty": 0.75
    }

    with pytest.raises(ValueError, match="must be in \\[0.0, 1.0\\]"):
        signing_persona.sign_epistemic_state(state, phase="PREFLIGHT")


def test_verify_valid_signature(signing_persona):
    """Test verifying a valid signature"""
    state = {
        "engagement": 0.80,
        "know": 0.60,
        "do": 0.70,
        "context": 0.65,
        "clarity": 0.60,
        "coherence": 0.65,
        "signal": 0.60,
        "density": 0.55,
        "state": 0.60,
        "change": 0.70,
        "completion": 0.05,
        "impact": 0.65,
        "uncertainty": 0.75
    }

    signed = signing_persona.sign_epistemic_state(state, phase="PREFLIGHT")
    is_valid = signing_persona.verify_signature(signed)

    assert is_valid is True


def test_verify_tampered_signature(signing_persona):
    """Test that tampered state fails verification"""
    state = {
        "engagement": 0.80,
        "know": 0.60,
        "do": 0.70,
        "context": 0.65,
        "clarity": 0.60,
        "coherence": 0.65,
        "signal": 0.60,
        "density": 0.55,
        "state": 0.60,
        "change": 0.70,
        "completion": 0.05,
        "impact": 0.65,
        "uncertainty": 0.75
    }

    signed = signing_persona.sign_epistemic_state(state, phase="PREFLIGHT")

    # Tamper with the signature
    signed["signature"] = "a" * 128  # Invalid signature

    is_valid = signing_persona.verify_signature(signed)
    assert is_valid is False


def test_verify_tampered_state(signing_persona):
    """Test that tampered epistemic state fails verification"""
    state = {
        "engagement": 0.80,
        "know": 0.60,
        "do": 0.70,
        "context": 0.65,
        "clarity": 0.60,
        "coherence": 0.65,
        "signal": 0.60,
        "density": 0.55,
        "state": 0.60,
        "change": 0.70,
        "completion": 0.05,
        "impact": 0.65,
        "uncertainty": 0.75
    }

    signed = signing_persona.sign_epistemic_state(state, phase="PREFLIGHT")

    # Tamper with state
    signed["state"]["vectors"]["know"] = 0.95

    is_valid = signing_persona.verify_signature(signed)
    assert is_valid is False


def test_get_persona_info(signing_persona):
    """Test getting public persona information"""
    info = signing_persona.get_persona_info()

    assert info["persona_id"] == "researcher_test"
    assert info["name"] == "Test Researcher"
    assert info["version"] == "1.0.0"
    assert "public_key" in info
    assert "epistemic_priors" in info
    assert "focus_domains" in info
    assert info["focus_domains"] == ["research", "exploration", "learning"]
    assert info["persona_type"] == "general"  # Not in specific domains


def test_export_public_persona(signing_persona):
    """Test exporting persona for public registry"""
    public = signing_persona.export_public_persona()

    assert public["persona_id"] == "researcher_test"
    assert public["name"] == "Test Researcher"
    assert public["public_key"] == signing_persona.identity.public_key_hex()
    assert "epistemic_config" in public
    assert "capabilities" in public
    assert "metadata" in public

    # Verify no private key is exported
    assert "private_key" not in json.dumps(public)


def test_signature_determinism(signing_persona):
    """Test that signing same state produces same signature"""
    from datetime import datetime, timezone
    
    state = {
        "engagement": 0.80,
        "know": 0.60,
        "do": 0.70,
        "context": 0.65,
        "clarity": 0.60,
        "coherence": 0.65,
        "signal": 0.60,
        "density": 0.55,
        "state": 0.60,
        "change": 0.70,
        "completion": 0.05,
        "impact": 0.65,
        "uncertainty": 0.75
    }

    # Use same timestamp for both signings to ensure determinism
    # (timestamps change between calls, so we fix it for this test)
    fixed_timestamp = "2025-12-31T20:39:44+00:00"
    
    # Sign twice with same timestamp
    signed1 = signing_persona.sign_epistemic_state(state, phase="PREFLIGHT", timestamp=fixed_timestamp)
    signed2 = signing_persona.sign_epistemic_state(state, phase="PREFLIGHT", timestamp=fixed_timestamp)

    # Signatures should be identical (Ed25519 is deterministic)
    assert signed1["signature"] == signed2["signature"]


def test_cross_persona_verification_fails(signing_persona, test_identity):
    """Test that signature from one persona cannot be verified by another"""
    state = {
        "engagement": 0.80,
        "know": 0.60,
        "do": 0.70,
        "context": 0.65,
        "clarity": 0.60,
        "coherence": 0.65,
        "signal": 0.60,
        "density": 0.55,
        "state": 0.60,
        "change": 0.70,
        "completion": 0.05,
        "impact": 0.65,
        "uncertainty": 0.75
    }

    # Sign with first persona
    signed = signing_persona.sign_epistemic_state(state, phase="PREFLIGHT")

    # Create different identity and persona
    other_identity = AIIdentity(ai_id="other_researcher")
    other_identity.generate_keypair()

    other_profile = PersonaProfile(
        persona_id="other_researcher",
        name="Other Researcher",
        version="1.0.0",
        signing_identity=SigningIdentityConfig(
            user_id="test",
            identity_name="other",
            public_key=other_identity.public_key_hex()
        ),
        epistemic_config=EpistemicConfig(
            priors={
                "engagement": 0.80, "know": 0.60, "do": 0.70, "context": 0.65,
                "clarity": 0.60, "coherence": 0.65, "signal": 0.60, "density": 0.55,
                "state": 0.60, "change": 0.70, "completion": 0.05, "impact": 0.65,
                "uncertainty": 0.75
            }
        )
    )

    other_signing = SigningPersona(other_profile, other_identity)

    # Try to verify with other persona
    is_valid = other_signing.verify_signature(signed)
    assert is_valid is False
