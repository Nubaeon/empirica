"""Noetic Firewall API - Client interface for inter-agent message security.

The firewall is a SEPARATE service from Sentinel:
- Sentinel: Gates local AI workflow (PREFLIGHT→CHECK→POSTFLIGHT)
- Firewall: Validates messages BETWEEN AI instances

Integration point: Firewall confidence can feed into Sentinel's epistemic state
via findings/unknowns or direct vector contribution.

Usage:
    # Client-side (in comms.py or agent code)
    from empirica.firewall import FirewallClient, wrap_with_envelope

    client = FirewallClient(base_url="http://halo-strix:8000")

    # Wrap outgoing message with epistemic envelope
    envelope = wrap_with_envelope(
        message=git_notes_message,
        sender_vectors=current_session_vectors
    )

    # Scan before sending
    result = await client.scan_outgoing(envelope)
    if result.decision == FirewallDecision.ALLOW:
        # Send via git notes
        pass
    else:
        # Log as potential attack, do not send
        pass

    # Scan incoming message
    result = await client.scan_incoming(envelope)
    # Extract confidence signals for local epistemic state
    signals = result.to_epistemic_signals()
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

from .schema import (
    EpistemicEnvelope,
    FirewallDecision,
    FirewallTier,
    MessageScanResult,
    ScannerResult,
    FirewallConfig,
)


def wrap_with_envelope(
    message: Dict[str, Any],
    sender_vectors: Dict[str, float],
    evidence_pointers: Optional[list] = None,
) -> EpistemicEnvelope:
    """Wrap a git notes message in an epistemic envelope.

    This is called by the sending agent BEFORE the message goes through
    the firewall. The firewall will add its scan results.

    Args:
        message: Git notes message dict (from/to/channel/subject/body)
        sender_vectors: Current epistemic vectors of the sender
        evidence_pointers: Optional list of goal_ids, finding_ids for audit

    Returns:
        EpistemicEnvelope ready for firewall scanning
    """
    body = message.get("body", "")
    content_hash = hashlib.sha256(body.encode()).hexdigest()

    return EpistemicEnvelope(
        message_id=message.get("message_id", str(uuid.uuid4())),
        from_agent=message.get("from", {}),
        to_agent=message.get("to", {}),
        channel=message.get("channel", "direct"),
        subject=message.get("subject", ""),
        body=body,
        content_hash=content_hash,
        sender_vectors=sender_vectors,
        evidence_pointers=evidence_pointers or [],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def extract_confidence(scan_result: MessageScanResult) -> Dict[str, float]:
    """Extract confidence signals suitable for feeding into local Sentinel.

    These signals can be logged as findings or used to adjust the local
    AI's epistemic vectors when processing incoming messages.

    Args:
        scan_result: Result from firewall scan

    Returns:
        Dict of confidence signals for epistemic integration
    """
    return scan_result.to_epistemic_signals()


@dataclass
class FirewallClient:
    """Client for communicating with the Noetic Firewall service.

    The firewall runs on isolated hardware (Halo Strix) and exposes
    an HTTP API for scanning messages.
    """

    base_url: str = "http://localhost:8000"
    timeout_seconds: float = 5.0

    async def scan_outgoing(self, envelope: EpistemicEnvelope) -> MessageScanResult:
        """Scan an outgoing message before sending.

        This is called by the local agent before writing to git notes.
        The firewall scans the message content for:
        - Prompt injection attempts
        - Goal hijacking patterns
        - Malicious content

        Args:
            envelope: Message wrapped in epistemic envelope

        Returns:
            MessageScanResult with decision and confidence signals
        """
        # TODO: Implement actual HTTP call to firewall service
        # For now, return a stub that allows all messages
        return self._stub_scan(envelope, direction="outgoing")

    async def scan_incoming(self, envelope: EpistemicEnvelope) -> MessageScanResult:
        """Scan an incoming message before processing.

        This is called when receiving a message from another agent.
        The firewall validates:
        - Message integrity (content hash matches)
        - No injection attacks in received content
        - Sender's claimed epistemic state is plausible

        Args:
            envelope: Received message with epistemic envelope

        Returns:
            MessageScanResult with decision and confidence signals
        """
        # TODO: Implement actual HTTP call to firewall service
        return self._stub_scan(envelope, direction="incoming")

    def _stub_scan(
        self, envelope: EpistemicEnvelope, direction: str
    ) -> MessageScanResult:
        """Stub implementation for development/testing.

        In production, this would call the firewall HTTP API.
        """
        return MessageScanResult(
            message_id=envelope.message_id,
            decision=FirewallDecision.ALLOW,
            tiers_executed=[FirewallTier.TIER1_FAST],
            scanner_results=[
                ScannerResult(
                    scanner_name="stub",
                    passed=True,
                    confidence=1.0,
                    latency_ms=0.0,
                    details={"stub": True, "direction": direction},
                )
            ],
            firewall_confidence=1.0,
            total_latency_ms=0.0,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check if firewall service is healthy.

        Returns:
            Dict with status, version, loaded models
        """
        # TODO: Implement actual HTTP call
        return {
            "status": "stub",
            "version": "0.1.0",
            "models_loaded": [],
            "note": "Stub implementation - firewall service not running",
        }


# Convenience function for simple scanning without client instantiation
async def scan_message(
    message: Dict[str, Any],
    sender_vectors: Dict[str, float],
    firewall_url: str = "http://localhost:8000",
    direction: str = "outgoing",
) -> MessageScanResult:
    """Convenience function to scan a message without managing client lifecycle.

    Args:
        message: Git notes message dict
        sender_vectors: Current epistemic vectors
        firewall_url: URL of firewall service
        direction: "outgoing" or "incoming"

    Returns:
        MessageScanResult with decision and confidence signals
    """
    envelope = wrap_with_envelope(message, sender_vectors)
    client = FirewallClient(base_url=firewall_url)

    if direction == "outgoing":
        return await client.scan_outgoing(envelope)
    else:
        return await client.scan_incoming(envelope)
