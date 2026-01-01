"""
SigningPersona - Bind Persona Profiles to Cryptographic Identities

Enables cryptographic signing of epistemic states for reproducible,
verifiable AI reasoning. Each persona instance can sign its reasoning
process, creating an immutable audit trail in Git.

Key Features:
- Ed25519 signature of epistemic states
- Canonical JSON for deterministic hashing
- Support for CASCADE phase signing
- Verification of signed states
- Compatible with Git notes for storage

Design:
    persona = PersonaProfile(...)  # Epistemic definition
    identity = AIIdentity(...)      # Cryptographic identity
    signing = SigningPersona(persona, identity)

    # Sign an epistemic state
    signed = signing.sign_epistemic_state(state, phase="PREFLIGHT")

    # Verify later
    verified = signing.verify_signature(signed)
"""

import json
import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from dataclasses import asdict

from empirica.core.persona.persona_profile import PersonaProfile
from empirica.core.identity.ai_identity import AIIdentity

logger = logging.getLogger(__name__)


class SigningPersona:
    """
    Bind a Persona Profile to a Cryptographic Identity

    This class creates the connection between:
    - PersonaProfile: The epistemic behavior definition (13 vectors)
    - AIIdentity: The Ed25519 keypair for signing

    Enables signing epistemic states so CASCADE phases are cryptographically
    verifiable and can be stored in Git as immutable records.

    Usage:
        # Create or load persona and identity
        persona = PersonaProfile(...)
        identity = AIIdentity("researcher_v1")
        identity.load_keypair()

        # Bind them together
        signing_persona = SigningPersona(persona, identity)

        # Sign an epistemic state during a phase
        epistemic_state = {
            "engagement": 0.85,
            "know": 0.75,
            "do": 0.80,
            # ... all 13 vectors
        }

        signed = signing_persona.sign_epistemic_state(
            epistemic_state,
            phase="PREFLIGHT"
        )

        # Store in git notes
        git_notes = json.dumps(signed, indent=2)

        # Later: verify the signature
        is_valid = signing_persona.verify_signature(signed)
    """

    def __init__(self, persona_profile: PersonaProfile, ai_identity: AIIdentity):
        """
        Initialize a signing persona

        Args:
            persona_profile: The epistemic definition
            ai_identity: The Ed25519 identity (must have keypair loaded)

        Raises:
            ValueError: If identity has no public key
        """
        self.persona = persona_profile
        self.identity = ai_identity

        # Verify identity is ready
        if ai_identity.public_key is None:
            raise ValueError("AIIdentity must have public key loaded")

        logger.info(
            f"✓ Created SigningPersona: {persona_profile.persona_id} "
            f"with identity {ai_identity.ai_id}"
        )

    def _create_canonical_state(
        self,
        epistemic_vectors: Dict[str, float],
        phase: str,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create canonical representation of epistemic state

        This is deterministic so the same state always produces the same JSON,
        which is critical for signature verification.

        Args:
            epistemic_vectors: The 13 epistemic vectors
            phase: CASCADE phase (PREFLIGHT, INVESTIGATE, CHECK, ACT, POSTFLIGHT)
            timestamp: Optional timestamp (for testing determinism; defaults to now)

        Returns:
            Dict with canonical state representation
        """
        # Validate required vectors
        required_vectors = [
            "engagement", "know", "do", "context",
            "clarity", "coherence", "signal", "density",
            "state", "change", "completion", "impact", "uncertainty"
        ]

        for vector in required_vectors:
            if vector not in epistemic_vectors:
                raise ValueError(f"Missing required vector: {vector}")

            value = epistemic_vectors[vector]
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Vector {vector} must be in [0.0, 1.0], got {value}")

        # Create canonical form (sorted keys for determinism)
        canonical = {
            "persona_id": self.persona.persona_id,
            "persona_version": self.persona.version,
            "phase": phase,
            "timestamp": timestamp or datetime.now(UTC).isoformat(),
            "vectors": {
                k: epistemic_vectors[k]
                for k in sorted(required_vectors)
            },
            "public_key": self.identity.public_key_hex()
        }

        return canonical

    def sign_epistemic_state(
        self,
        epistemic_vectors: Dict[str, float],
        phase: str,
        additional_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sign an epistemic state with the persona's private key

        Args:
            epistemic_vectors: Dict with 13 epistemic vectors
            phase: CASCADE phase name
            additional_data: Optional extra data to include (not signed)
            timestamp: Optional timestamp (for testing determinism; defaults to now)

        Returns:
            Dict with:
                - state: Canonical epistemic state
                - signature: Ed25519 signature (hex)
                - algorithm: "Ed25519"
                - verified: False (signature not yet verified)

        Raises:
            ValueError: If vectors invalid or key not loaded
        """
        # Create canonical representation
        canonical_state = self._create_canonical_state(epistemic_vectors, phase, timestamp=timestamp)

        # Serialize to JSON (sorted keys for determinism)
        message_json = json.dumps(canonical_state, sort_keys=True, separators=(',', ':'))
        message_bytes = message_json.encode('utf-8')

        # Sign with private key
        signature_bytes = self.identity.sign(message_bytes)

        # Return signed state
        result = {
            "state": canonical_state,
            "signature": signature_bytes.hex(),
            "algorithm": "Ed25519",
            "verified": False
        }

        # Include additional metadata if provided
        if additional_data:
            result["metadata"] = additional_data

        logger.info(
            f"✓ Signed epistemic state: {self.persona.persona_id} "
            f"phase={phase} signature={signature_bytes.hex()[:16]}..."
        )

        return result

    def verify_signature(self, signed_state: Dict[str, Any]) -> bool:
        """
        Verify a previously signed epistemic state

        Args:
            signed_state: Dict with state, signature, and algorithm

        Returns:
            bool: True if signature is valid
        """
        try:
            # Extract components
            state = signed_state["state"]
            signature_hex = signed_state["signature"]
            algorithm = signed_state.get("algorithm", "Ed25519")

            # Validate algorithm
            if algorithm != "Ed25519":
                logger.warning(f"Unsupported signature algorithm: {algorithm}")
                return False

            # Verify public key matches
            if state["public_key"] != self.identity.public_key_hex():
                logger.warning("Public key in state does not match identity")
                return False

            # Recreate the exact message that was signed
            message_json = json.dumps(state, sort_keys=True, separators=(',', ':'))
            message_bytes = message_json.encode('utf-8')

            # Convert signature from hex
            signature_bytes = bytes.fromhex(signature_hex)

            # Get public key bytes
            public_key_bytes = bytes.fromhex(state["public_key"])

            # Verify using AIIdentity static method
            is_valid = self.identity.__class__.verify(
                signature_bytes,
                message_bytes,
                public_key_bytes
            )

            if is_valid:
                logger.info(
                    f"✓ Verified signature: {state['persona_id']} "
                    f"phase={state['phase']}"
                )
            else:
                logger.warning(
                    f"✗ Signature verification failed: {state['persona_id']} "
                    f"phase={state['phase']}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False

    def get_persona_info(self) -> Dict[str, Any]:
        """
        Get public information about this persona

        Returns:
            Dict with persona_id, name, public_key, focus_domains, etc.
        """
        return {
            "persona_id": self.persona.persona_id,
            "name": self.persona.name,
            "version": self.persona.version,
            "public_key": self.identity.public_key_hex(),
            "epistemic_priors": self.persona.epistemic_config.priors,
            "focus_domains": self.persona.epistemic_config.focus_domains,
            "persona_type": self.persona.get_type(),
            "created_at": self.identity.created_at
        }

    def export_public_persona(self) -> Dict[str, Any]:
        """
        Export persona for public registry (Qdrant)

        This contains everything needed to verify signatures except the
        private key, which remains only in AIIdentity storage.

        Returns:
            Dict suitable for storing in Qdrant
        """
        return {
            "persona_id": self.persona.persona_id,
            "name": self.persona.name,
            "version": self.persona.version,
            "public_key": self.identity.public_key_hex(),
            "epistemic_config": {
                "priors": self.persona.epistemic_config.priors,
                "thresholds": self.persona.epistemic_config.thresholds,
                "focus_domains": self.persona.epistemic_config.focus_domains
            },
            "capabilities": asdict(self.persona.capabilities),
            "metadata": asdict(self.persona.metadata),
            "persona_type": self.persona.get_type(),
            "created_at": self.identity.created_at,
            "identity_ai_id": self.identity.ai_id
        }
