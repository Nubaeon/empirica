#!/usr/bin/env python3
"""
Phase 3 Persona System Demo

Demonstrates:
1. Creating personas from templates
2. Saving and loading personas
3. Validating persona configurations
4. Integration with Phase 2 signing identities

Usage:
    python3 examples/phase3_persona_demo.py
"""

import sys
from pathlib import Path

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from empirica.core.persona import PersonaManager

def main():
    print("=" * 60)
    print("Phase 3: Multi-Persona Epistemic Intelligence Demo")
    print("=" * 60)
    print()

    # Initialize manager
    manager = PersonaManager()

    print("1. Creating Security Expert persona from template...")
    security = manager.create_persona(
        persona_id="security_expert",
        name="Security Expert",
        version="1.0.0",
        user_id="david",
        template="builtin:security"
    )

    print(f"   ✓ Created: {security.name}")
    print(f"   - Type: {security.get_type()}")
    print(f"   - KNOW prior: {security.epistemic_config.priors['know']}")
    print(f"   - UNCERTAINTY prior: {security.epistemic_config.priors['uncertainty']}")
    print(f"   - Focus domains: {', '.join(security.epistemic_config.focus_domains[:3])}...")
    print()

    print("2. Creating UX Specialist persona...")
    ux = manager.create_persona(
        persona_id="ux_specialist",
        name="UX Specialist",
        version="1.0.0",
        user_id="david",
        template="builtin:ux"
    )

    print(f"   ✓ Created: {ux.name}")
    print(f"   - Type: {ux.get_type()}")
    print(f"   - CONTEXT prior: {ux.epistemic_config.priors['context']} (high for user awareness)")
    print(f"   - Focus domains: {', '.join(ux.epistemic_config.focus_domains[:3])}...")
    print()

    print("3. Saving personas to disk...")
    security_path = manager.save_persona(security, overwrite=True)
    ux_path = manager.save_persona(ux, overwrite=True)

    print(f"   ✓ Saved security to: {security_path}")
    print(f"   ✓ Saved UX to: {ux_path}")
    print()

    print("4. Loading personas from disk...")
    loaded_security = manager.load_persona("security_expert")
    loaded_ux = manager.load_persona("ux_specialist")

    print(f"   ✓ Loaded: {loaded_security.name}")
    print(f"   ✓ Loaded: {loaded_ux.name}")
    print()

    print("5. Listing all personas...")
    all_personas = manager.list_personas()

    print(f"   Found {len(all_personas)} persona(s):")
    for persona_id in all_personas:
        persona_type = manager.get_persona_type(persona_id)
        print(f"   - {persona_id} ({persona_type})")
    print()

    print("6. Validating persona configurations...")
    from empirica.core.persona import validate_persona_profile

    try:
        validate_persona_profile(security.to_dict())
        print("   ✓ Security persona: VALID")

        validate_persona_profile(ux.to_dict())
        print("   ✓ UX persona: VALID")

    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
    print()

    print("7. Checking Phase 2 integration (signing identities)...")
    print(f"   - Security identity: {security.signing_identity.identity_name}")
    print(f"   - Security public key: {security.signing_identity.public_key[:16]}...")
    print(f"   - UX identity: {ux.signing_identity.identity_name}")
    print(f"   - UX public key: {ux.signing_identity.public_key[:16]}...")
    print()

    print("=" * 60)
    print("✓ Phase 3 Persona System Working!")
    print("=" * 60)
    print()

    print("Next steps:")
    print("  - Implement PersonaHarness (runtime container)")
    print("  - Implement SentinelOrchestrator (multi-persona coordination)")
    print("  - Implement Persona-Sentinel communication protocol")
    print("  - Add CLI commands: empirica persona-create, orchestrate, etc.")
    print()

if __name__ == "__main__":
    main()
