"""
Persona Manager - Create, load, save, and manage personas

Handles:
- Creating personas from templates or scratch
- Loading/saving to .empirica/personas/
- Validation against JSON schema
- Integration with Phase 2 signing identities
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict

from .persona_profile import PersonaProfile, SigningIdentityConfig
from .validation import validate_persona_profile, ValidationError
from empirica.core.identity import AIIdentity

logger = logging.getLogger(__name__)

class PersonaManager:
    """
    Manages persona lifecycle: create, load, save, validate

    Usage:
        manager = PersonaManager()

        # Create new persona
        profile = manager.create_persona(
            persona_id="security_expert",
            template="builtin:security"
        )

        # Save persona
        manager.save_persona(profile)

        # Load persona
        loaded = manager.load_persona("security_expert")

        # List all personas
        all_personas = manager.list_personas()
    """

    def __init__(self, personas_dir: Optional[str] = None):
        """
        Initialize PersonaManager

        Args:
            personas_dir: Custom directory for persona storage
                         (default: .empirica/personas)
        """
        self.personas_dir = Path(personas_dir or ".empirica/personas")
        self.personas_dir.mkdir(parents=True, exist_ok=True)

    def create_persona(
        self,
        persona_id: str,
        name: str,
        version: str = "1.0.0",
        user_id: str = "unknown",
        identity_name: Optional[str] = None,
        epistemic_priors: Optional[Dict[str, float]] = None,
        focus_domains: Optional[List[str]] = None,
        template: Optional[str] = None
    ) -> PersonaProfile:
        """
        Create a new persona profile

        Args:
            persona_id: Unique identifier
            name: Human-readable name
            version: Semantic version
            user_id: User who owns this persona
            identity_name: Identity for signing (if None, uses persona_id)
            epistemic_priors: Custom priors (if None, uses template or defaults)
            focus_domains: Areas of focus
            template: Template to use ("builtin:security", "builtin:ux", etc.)

        Returns:
            PersonaProfile instance
        """
        # Use template if provided
        if template:
            return self._create_from_template(
                template, persona_id, name, version, user_id
            )

        # Get or create signing identity
        identity_name = identity_name or persona_id
        signing_config = self._get_or_create_signing_identity(
            user_id, identity_name
        )

        # Use provided priors or defaults
        if epistemic_priors is None:
            epistemic_priors = self._get_default_priors()

        # Validate priors has all 13 vectors
        required_vectors = [
            "engagement", "know", "do", "context",
            "clarity", "coherence", "signal", "density",
            "state", "change", "completion", "impact", "uncertainty"
        ]

        for vector in required_vectors:
            if vector not in epistemic_priors:
                epistemic_priors[vector] = 0.5  # Default to neutral

        # Create profile
        from .persona_profile import EpistemicConfig

        profile = PersonaProfile(
            persona_id=persona_id,
            name=name,
            version=version,
            signing_identity=signing_config,
            epistemic_config=EpistemicConfig(
                priors=epistemic_priors,
                focus_domains=focus_domains or []
            )
        )

        logger.info(f"✓ Created persona: {persona_id}")
        return profile

    def save_persona(self, profile: PersonaProfile, overwrite: bool = False) -> Path:
        """
        Save persona to disk

        Args:
            profile: PersonaProfile to save
            overwrite: Allow overwriting existing persona

        Returns:
            Path to saved file

        Raises:
            FileExistsError: If persona exists and overwrite=False
            ValidationError: If profile invalid
        """
        # Validate before saving
        profile_dict = profile.to_dict()
        validate_persona_profile(profile_dict)

        # Check if exists
        filepath = self.personas_dir / f"{profile.persona_id}.json"

        if filepath.exists() and not overwrite:
            raise FileExistsError(
                f"Persona {profile.persona_id} already exists. "
                f"Use overwrite=True to replace."
            )

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(profile_dict, f, indent=2)

        logger.info(f"✓ Saved persona to: {filepath}")
        return filepath

    def load_persona(self, persona_id: str) -> PersonaProfile:
        """
        Load persona from disk

        Args:
            persona_id: Persona identifier

        Returns:
            PersonaProfile instance

        Raises:
            FileNotFoundError: If persona doesn't exist
            ValidationError: If persona file invalid
        """
        filepath = self.personas_dir / f"{persona_id}.json"

        if not filepath.exists():
            raise FileNotFoundError(
                f"Persona not found: {persona_id} (looked in {filepath})"
            )

        with open(filepath, 'r') as f:
            profile_dict = json.load(f)

        # Normalize for backward compatibility / emergent persona records
        # - Some older/emergent personas may have placeholder public_key values
        # - Some may omit epistemic_config.focus_domains
        try:
            signing = profile_dict.get('signing_identity') or {}
            pk = signing.get('public_key')
            if not isinstance(pk, str) or len(pk) != 64:
                signing['public_key'] = '0' * 64
            profile_dict['signing_identity'] = signing

            epi = profile_dict.get('epistemic_config') or {}
            if 'focus_domains' not in epi or not isinstance(epi.get('focus_domains'), list) or len(epi.get('focus_domains')) == 0:
                epi['focus_domains'] = ['general']
            profile_dict['epistemic_config'] = epi
        except Exception:
            pass

        # Validate
        validate_persona_profile(profile_dict)

        # Load into PersonaProfile
        profile = PersonaProfile.from_dict(profile_dict)

        logger.info(f"✓ Loaded persona: {persona_id}")
        return profile

    def list_personas(self) -> List[str]:
        """
        List all available personas

        Returns:
            List of persona IDs
        """
        persona_files = self.personas_dir.glob("*.json")
        return [f.stem for f in persona_files]

    def delete_persona(self, persona_id: str) -> None:
        """
        Delete a persona

        Args:
            persona_id: Persona to delete

        Raises:
            FileNotFoundError: If persona doesn't exist
        """
        filepath = self.personas_dir / f"{persona_id}.json"

        if not filepath.exists():
            raise FileNotFoundError(f"Persona not found: {persona_id}")

        filepath.unlink()
        logger.info(f"✓ Deleted persona: {persona_id}")

    def get_persona_type(self, persona_id: str) -> str:
        """
        Get persona type based on focus domains

        Args:
            persona_id: Persona identifier

        Returns:
            Persona type (security, ux, performance, etc.)
        """
        profile = self.load_persona(persona_id)
        return profile.get_type()

    # Private methods

    def _get_or_create_signing_identity(
        self,
        user_id: str,
        identity_name: str
    ) -> SigningIdentityConfig:
        """
        Get existing signing identity or create new one

        Integrates with Phase 2 AIIdentity system
        """
        identity = AIIdentity(ai_id=identity_name)

        # Try to load existing identity
        try:
            identity.load_keypair()
            logger.info(f"✓ Using existing identity: {identity_name}")

        except FileNotFoundError:
            # Create new identity
            logger.info(f"Creating new identity for: {identity_name}")
            identity.generate_keypair()
            identity.save_keypair()

        # Get public key as hex
        public_key_bytes = identity.public_key.public_bytes_raw()
        public_key_hex = public_key_bytes.hex()

        return SigningIdentityConfig(
            user_id=user_id,
            identity_name=identity_name,
            public_key=public_key_hex,
            reputation_score=0.5
        )

    def _get_default_priors(self) -> Dict[str, float]:
        """Get default epistemic priors (neutral)"""
        return {
            "engagement": 0.7,
            "know": 0.5,
            "do": 0.5,
            "context": 0.5,
            "clarity": 0.6,
            "coherence": 0.6,
            "signal": 0.5,
            "density": 0.5,
            "state": 0.5,
            "change": 0.5,
            "completion": 0.0,
            "impact": 0.5,
            "uncertainty": 0.5
        }

    def _create_from_template(
        self,
        template: str,
        persona_id: str,
        name: str,
        version: str,
        user_id: str
    ) -> PersonaProfile:
        """Create persona from built-in template"""

        # Load template
        from .templates import BUILTIN_TEMPLATES

        template_name = template.replace("builtin:", "")

        if template_name not in BUILTIN_TEMPLATES:
            raise ValueError(
                f"Unknown template: {template_name}. "
                f"Available: {list(BUILTIN_TEMPLATES.keys())}"
            )

        template_data = BUILTIN_TEMPLATES[template_name]

        # Get signing identity
        signing_config = self._get_or_create_signing_identity(
            user_id, persona_id
        )

        # Create profile from template
        from .persona_profile import EpistemicConfig

        profile = PersonaProfile(
            persona_id=persona_id,
            name=name,
            version=version,
            signing_identity=signing_config,
            epistemic_config=EpistemicConfig(
                priors=template_data['priors'],
                thresholds=template_data['thresholds'],
                focus_domains=template_data['focus_domains']
            )
        )

        logger.info(f"✓ Created persona from template '{template_name}': {persona_id}")
        return profile
