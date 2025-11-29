"""
Basic tests for Phase 3 Persona System

Tests:
- Creating personas from templates
- Saving/loading personas
- Validation
- Integration with Phase 2 signing identities
"""

import pytest
import json
from pathlib import Path

from empirica.core.persona import (
    PersonaProfile,
    PersonaManager,
    validate_persona_profile,
    ValidationError
)

def test_create_persona_from_template(tmp_path):
    """Test creating persona from built-in template"""

    manager = PersonaManager(personas_dir=str(tmp_path))

    # Create security expert from template
    profile = manager.create_persona(
        persona_id="test_security",
        name="Test Security Expert",
        version="1.0.0",
        user_id="test_user",
        template="builtin:security"
    )

    assert profile.persona_id == "test_security"
    assert profile.name == "Test Security Expert"
    assert profile.get_type() == "security"

    # Check epistemic priors from template
    assert profile.epistemic_config.priors['know'] == 0.90  # High security knowledge
    assert profile.epistemic_config.priors['uncertainty'] == 0.15  # Low uncertainty

    # Check focus domains
    assert 'security' in profile.epistemic_config.focus_domains
    assert 'authentication' in profile.epistemic_config.focus_domains

def test_save_and_load_persona(tmp_path):
    """Test saving and loading persona"""

    manager = PersonaManager(personas_dir=str(tmp_path))

    # Create and save
    profile = manager.create_persona(
        persona_id="test_ux",
        name="Test UX Specialist",
        template="builtin:ux"
    )

    filepath = manager.save_persona(profile)
    assert filepath.exists()

    # Load
    loaded = manager.load_persona("test_ux")

    assert loaded.persona_id == profile.persona_id
    assert loaded.name == profile.name
    assert loaded.version == profile.version
    assert loaded.epistemic_config.priors == profile.epistemic_config.priors

def test_list_personas(tmp_path):
    """Test listing all personas"""

    manager = PersonaManager(personas_dir=str(tmp_path))

    # Create multiple personas
    manager.save_persona(manager.create_persona("sec1", "Security 1", template="builtin:security"))
    manager.save_persona(manager.create_persona("ux1", "UX 1", template="builtin:ux"))
    manager.save_persona(manager.create_persona("perf1", "Perf 1", template="builtin:performance"))

    personas = manager.list_personas()

    assert len(personas) == 3
    assert "sec1" in personas
    assert "ux1" in personas
    assert "perf1" in personas

def test_validation_weights_sum():
    """Test that weights must sum to 1.0"""

    from empirica.core.persona import EpistemicConfig, SigningIdentityConfig

    # Invalid weights (sum > 1.0)
    with pytest.raises(ValueError, match="sum to 1.0"):
        EpistemicConfig(
            priors={
                "engagement": 0.7, "know": 0.5, "do": 0.5, "context": 0.5,
                "clarity": 0.6, "coherence": 0.6, "signal": 0.5, "density": 0.5,
                "state": 0.5, "change": 0.5, "completion": 0.0, "impact": 0.5,
                "uncertainty": 0.5
            },
            weights={
                "foundation": 0.5,
                "comprehension": 0.5,
                "execution": 0.5,  # Sum = 1.5, should fail
                "engagement": 0.0
            }
        )

def test_persona_type_detection():
    """Test get_type() method"""

    manager = PersonaManager()

    sec = manager.create_persona("sec", "Security", template="builtin:security")
    assert sec.get_type() == "security"

    ux = manager.create_persona("ux", "UX", template="builtin:ux")
    assert ux.get_type() == "ux"

    perf = manager.create_persona("perf", "Performance", template="builtin:performance")
    assert perf.get_type() == "performance"

    arch = manager.create_persona("arch", "Architecture", template="builtin:architecture")
    assert arch.get_type() == "architecture"

def test_builtin_templates_available():
    """Test that all built-in templates are available"""

    from empirica.core.persona.templates import BUILTIN_TEMPLATES

    expected_templates = [
        "security", "ux", "performance",
        "architecture", "code_review", "sentinel"
    ]

    for template_name in expected_templates:
        assert template_name in BUILTIN_TEMPLATES
        template = BUILTIN_TEMPLATES[template_name]

        # Check structure
        assert "priors" in template
        assert "thresholds" in template
        assert "weights" in template
        assert "focus_domains" in template

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
