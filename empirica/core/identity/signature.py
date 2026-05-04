"""
EEP-1 Signature Implementation

Implements Empirica Ephemera Protocol (EEP-1) signature generation and verification
for establishing cryptographic trust in AI-generated content.

EEP-1 Signature Payload:
{
    "content_hash": "SHA-256 hash of output",
    "creator_id": "public_key_hex",
    "timestamp": "ISO 8601",
    "epistemic_state_final": {
        "KNOW": 0.92,
        "UNCERTAINTY": 0.05,
        ...
    },
    "cascade_trace_hash": "SHA-256 of git log",
    "metadata_sources": ["url1", "file2"],
    "model_id": "gemini-2.5-flash"
}

The payload is canonicalized (deterministic JSON) and signed with Ed25519.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone  # type: ignore[reportAttributeAccessIssue]
from typing import Any

from .ai_identity import AIIdentity

logger = logging.getLogger(__name__)


def create_eep1_payload(
    content: str,
    epistemic_state: dict[str, float],
    ai_id: str,
    cascade_trace_hash: str | None = None,
    metadata_sources: list[str] | None = None,
    model_id: str | None = None,
    session_id: str | None = None
) -> dict[str, Any]:
    """
    Create EEP-1 signature payload

    Args:
        content: Final output content to sign
        epistemic_state: Final epistemic vectors (13-D state)
        ai_id: AI identifier (will be replaced with public key in sign_assessment)
        cascade_trace_hash: SHA-256 of git log history
        metadata_sources: Sources used (URLs, files, etc.)
        model_id: Underlying model identifier
        session_id: Session identifier

    Returns:
        Dict: EEP-1 payload (unsigned)
    """
    # Hash content
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    # Build payload
    payload = {
        'content_hash': content_hash,
        'creator_id': ai_id,  # Will be replaced with public key when signing
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'epistemic_state_final': epistemic_state,
        'cascade_trace_hash': cascade_trace_hash or '',
        'metadata_sources': metadata_sources or [],
        'model_id': model_id or 'unknown'
    }

    if session_id:
        payload['session_id'] = session_id

    return payload


def canonicalize_payload(payload: dict[str, Any]) -> str:
    """
    Canonicalize payload for signing

    Ensures deterministic JSON representation:
    - Sorted keys
    - No whitespace
    - Consistent encoding

    Args:
        payload: EEP-1 payload

    Returns:
        str: Canonicalized JSON string
    """
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


def sign_assessment(
    content: str,
    epistemic_state: dict[str, float],
    identity: AIIdentity,
    cascade_trace_hash: str | None = None,
    metadata_sources: list[str] | None = None,
    model_id: str | None = None,
    session_id: str | None = None
) -> dict[str, Any]:
    """
    Sign assessment with EEP-1 signature

    Args:
        content: Final output content
        epistemic_state: Final epistemic vectors
        identity: AI identity with keypair
        cascade_trace_hash: Git log hash
        metadata_sources: Sources used
        model_id: Model identifier
        session_id: Session identifier

    Returns:
        Dict: Complete signed package with payload + signature

    Example:
        identity = AIIdentity("claude-code")
        identity.load_keypair()

        signed = sign_assessment(
            content="Analysis complete...",
            epistemic_state={"KNOW": 0.92, "UNCERTAINTY": 0.05, ...},
            identity=identity,
            cascade_trace_hash="abc123..."
        )

        # signed contains:
        # - payload: EEP-1 payload with public key
        # - signature: hex-encoded signature
        # - signed_at: timestamp
    """
    if identity.private_key is None:
        raise RuntimeError(
            f"No private key loaded for {identity.ai_id}. "
            "Call identity.load_keypair() first."
        )

    # Create payload
    payload = create_eep1_payload(
        content=content,
        epistemic_state=epistemic_state,
        ai_id=identity.ai_id,
        cascade_trace_hash=cascade_trace_hash,
        metadata_sources=metadata_sources,
        model_id=model_id,
        session_id=session_id
    )

    # Replace ai_id with public key
    payload['creator_id'] = identity.public_key_hex()

    # Canonicalize payload
    canonical_payload = canonicalize_payload(payload)

    # Sign canonical payload
    signature = identity.sign(canonical_payload.encode('utf-8'))

    # Build signed package
    signed_package = {
        'payload': payload,
        'signature': signature.hex(),
        'signed_at': datetime.now(timezone.utc).isoformat(),
        'ai_id': identity.ai_id,  # For convenience (not part of signed data)
        'eep_version': '1.0'
    }

    logger.info(
        f"✓ Signed assessment with EEP-1 "
        f"(ai_id={identity.ai_id}, content_hash={payload['content_hash'][:8]}...)"
    )

    return signed_package


def verify_signature(
    signed_package: dict[str, Any],
    public_key_hex: str | None = None
) -> bool:
    """
    Verify EEP-1 signature

    Args:
        signed_package: Complete signed package from sign_assessment()
        public_key_hex: Optional public key (uses creator_id if not provided)

    Returns:
        bool: True if signature valid

    Example:
        # Verify signature
        is_valid = verify_signature(signed_package)

        if is_valid:
            print("✓ Signature valid - assessment is authentic")
        else:
            print("✗ Signature invalid - assessment may be tampered")
    """
    try:
        payload = signed_package['payload']
        signature_hex = signed_package['signature']

        # Get public key
        if public_key_hex is None:
            public_key_hex = payload['creator_id']

        # Canonicalize payload
        canonical_payload = canonicalize_payload(payload)

        # Verify signature
        signature_bytes = bytes.fromhex(signature_hex)
        public_key_bytes = bytes.fromhex(public_key_hex)

        is_valid = AIIdentity.verify(
            signature=signature_bytes,
            message=canonical_payload.encode('utf-8'),
            public_key_bytes=public_key_bytes
        )

        if is_valid:
            logger.info(f"✓ Signature verified (creator_id={public_key_hex[:16]}...)")
        else:
            logger.warning("✗ Signature verification failed")

        return is_valid

    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def verify_eep1_payload(
    signed_package: dict[str, Any],
    content: str | None = None,
    cascade_trace_hash: str | None = None
) -> dict[str, Any]:
    """
    Comprehensive EEP-1 payload verification

    Verifies:
    1. Signature is valid (cryptographic integrity)
    2. Content hash matches (if content provided)
    3. Cascade trace hash matches (if provided)
    4. Timestamp is reasonable (not in future, not too old)

    Args:
        signed_package: Complete signed package
        content: Optional content to verify hash
        cascade_trace_hash: Optional cascade trace to verify

    Returns:
        Dict: Verification results with details

    Example:
        result = verify_eep1_payload(
            signed_package=signed,
            content=original_content,
            cascade_trace_hash=git_log_hash
        )

        if result['valid']:
            print(f"✓ Verified: {result['message']}")
        else:
            print(f"✗ Failed: {result['errors']}")
    """
    errors = []
    warnings = []

    # 1. Verify signature
    signature_valid = verify_signature(signed_package)
    if not signature_valid:
        errors.append("Signature verification failed")

    payload = signed_package.get('payload', {})

    # 2. Verify content hash (if content provided)
    if content is not None:
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        if content_hash != payload.get('content_hash'):
            errors.append(
                f"Content hash mismatch: expected {payload.get('content_hash')[:8]}..., "
                f"got {content_hash[:8]}..."
            )

    # 3. Verify cascade trace hash (if provided)
    if cascade_trace_hash is not None:
        if cascade_trace_hash != payload.get('cascade_trace_hash'):
            errors.append(
                f"Cascade trace hash mismatch: expected {payload.get('cascade_trace_hash')[:8]}..., "
                f"got {cascade_trace_hash[:8]}..."
            )

    # 4. Verify timestamp
    try:
        timestamp = datetime.fromisoformat(payload.get('timestamp', ''))
        now = datetime.now(timezone.utc)

        # Check not in future
        if timestamp > now:
            warnings.append(f"Timestamp is in future: {timestamp}")

        # Check not too old (warn if >1 year)
        age_days = (now - timestamp).days
        if age_days > 365:
            warnings.append(f"Timestamp is {age_days} days old")

    except Exception as e:
        errors.append(f"Invalid timestamp: {e}")

    # 5. Verify epistemic state structure
    epistemic_state = payload.get('epistemic_state_final', {})
    required_vectors = ['engagement', 'know', 'do', 'uncertainty']
    missing_vectors = [v for v in required_vectors if v not in epistemic_state]
    if missing_vectors:
        warnings.append(f"Missing epistemic vectors: {missing_vectors}")

    # Build result
    result = {
        'valid': len(errors) == 0,
        'signature_valid': signature_valid,
        'errors': errors,
        'warnings': warnings,
        'payload': payload,
        'creator_id': payload.get('creator_id', '')[:16] + '...',
        'timestamp': payload.get('timestamp'),
        'epistemic_state': epistemic_state
    }

    if result['valid']:
        result['message'] = "EEP-1 payload verified successfully"
    else:
        result['message'] = f"EEP-1 verification failed: {'; '.join(errors)}"

    return result


def compute_cascade_trace_hash(git_log: str) -> str:
    """
    Compute CASCADE trace hash from git log

    Args:
        git_log: Git log output (commit hashes)

    Returns:
        str: SHA-256 hash of git log
    """
    return hashlib.sha256(git_log.encode('utf-8')).hexdigest()
