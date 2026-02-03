"""Noetic Firewall Schema - Epistemic envelope and scan result types.

This module defines the contract between agents and the firewall.
All inter-agent messages MUST be wrapped in an EpistemicEnvelope.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
import uuid


class FirewallTier(Enum):
    """Security scan tiers - escalating depth."""
    TIER1_FAST = "tier1_fast"       # PromptGuard + Sentinel (<10ms)
    TIER2_SEMANTIC = "tier2_semantic"  # Qwen3Guard + LlamaGuard (~50ms)
    TIER3_CODE = "tier3_code"       # CodeShield (~70ms)


class FirewallDecision(Enum):
    """Firewall verdict on a message."""
    ALLOW = "allow"           # Message passes all gates
    BLOCK = "block"           # Message blocked (logged as potential attack)
    QUARANTINE = "quarantine"  # Held for human review
    REWRITE = "rewrite"       # Sanitized version allowed


class HazardCategory(Enum):
    """MLCommons hazard taxonomy (Llama Guard 3 categories)."""
    S1_VIOLENT_CRIMES = "S1"
    S2_NON_VIOLENT_CRIMES = "S2"
    S3_SEX_RELATED_CRIMES = "S3"
    S4_CHILD_SEXUAL_ABUSE = "S4"
    S5_DEFAMATION = "S5"
    S6_SPECIALIZED_ADVICE = "S6"
    S7_PRIVACY = "S7"
    S8_INTELLECTUAL_PROPERTY = "S8"
    S9_INDISCRIMINATE_WEAPONS = "S9"
    S10_HATE = "S10"
    S11_SUICIDE_SELF_HARM = "S11"
    S12_SEXUAL_CONTENT = "S12"
    S13_ELECTIONS = "S13"
    S14_CODE_INTERPRETER_ABUSE = "S14"  # Only in 8B model


@dataclass
class ScannerResult:
    """Result from a single security scanner."""
    scanner_name: str
    passed: bool
    confidence: float  # 0.0-1.0, how confident the scanner is
    latency_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    hazard_categories: List[HazardCategory] = field(default_factory=list)


@dataclass
class MessageScanResult:
    """Aggregated result from all firewall tiers."""
    message_id: str
    decision: FirewallDecision
    tiers_executed: List[FirewallTier]
    scanner_results: List[ScannerResult]

    # Composite confidence signals for epistemic envelope
    injection_probability: float = 0.0  # P(prompt injection)
    goal_hijack_probability: float = 0.0  # P(goal hijacking attempt)
    malicious_intent_probability: float = 0.0  # P(malicious content)

    # Derived from scanner confidences
    firewall_confidence: float = 1.0  # Overall confidence message is safe

    total_latency_ms: float = 0.0
    blocked_reason: Optional[str] = None
    sanitized_content: Optional[str] = None  # If decision is REWRITE

    def to_epistemic_signals(self) -> Dict[str, float]:
        """Extract signals suitable for epistemic envelope."""
        return {
            "firewall_confidence": self.firewall_confidence,
            "injection_risk": self.injection_probability,
            "hijack_risk": self.goal_hijack_probability,
            "malicious_risk": self.malicious_intent_probability,
            # Contribute to standard epistemic vectors
            "uncertainty_contribution": 1.0 - self.firewall_confidence,
            "signal_contribution": min(1.0, sum(
                r.confidence for r in self.scanner_results
            ) / max(1, len(self.scanner_results))),
        }


@dataclass
class EpistemicEnvelope:
    """Wrapper for all inter-agent messages with epistemic metadata.

    Every message between agents MUST be wrapped in this envelope.
    The firewall adds its confidence signals before delivery.
    """
    # Message identity
    envelope_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = ""  # Original message ID from git notes

    # Routing
    from_agent: Dict[str, str] = field(default_factory=dict)  # {ai_id, machine, session_id}
    to_agent: Dict[str, str] = field(default_factory=dict)
    channel: str = "direct"

    # Content (post-firewall)
    subject: str = ""
    body: str = ""
    content_hash: str = ""  # SHA256 of original content for integrity

    # Epistemic vectors from SENDER (their self-assessment)
    sender_vectors: Dict[str, float] = field(default_factory=dict)

    # Firewall assessment (added by Noetic Firewall)
    firewall_scan: Optional[MessageScanResult] = None
    firewall_passed: bool = False
    firewall_timestamp: Optional[str] = None

    # Evidence chain (for audit)
    evidence_pointers: List[str] = field(default_factory=list)  # goal_ids, finding_ids

    # Cryptographic signature (Phase 2 - Ed25519)
    signature: Optional[str] = None
    signed_by: Optional[str] = None  # AI_ID that signed

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ttl_seconds: int = 86400
    priority: str = "normal"

    def get_composite_confidence(self) -> float:
        """Get overall confidence in this message's integrity."""
        if not self.firewall_scan:
            return 0.0  # No scan = no confidence

        firewall_conf = self.firewall_scan.firewall_confidence

        # Factor in sender's self-reported uncertainty
        sender_uncertainty = self.sender_vectors.get("uncertainty", 0.5)
        sender_confidence = 1.0 - sender_uncertainty

        # Composite: geometric mean of firewall and sender confidence
        return (firewall_conf * sender_confidence) ** 0.5

    def to_git_notes_format(self) -> Dict[str, Any]:
        """Convert to format suitable for git notes storage."""
        return {
            "envelope_id": self.envelope_id,
            "message_id": self.message_id,
            "from": self.from_agent,
            "to": self.to_agent,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "content_hash": self.content_hash,
            "sender_vectors": self.sender_vectors,
            "firewall": {
                "passed": self.firewall_passed,
                "timestamp": self.firewall_timestamp,
                "confidence": self.firewall_scan.firewall_confidence if self.firewall_scan else None,
                "decision": self.firewall_scan.decision.value if self.firewall_scan else None,
            },
            "evidence": self.evidence_pointers,
            "signature": self.signature,
            "signed_by": self.signed_by,
            "created_at": self.created_at,
            "ttl": self.ttl_seconds,
            "priority": self.priority,
        }


@dataclass
class FirewallConfig:
    """Configuration for Noetic Firewall deployment."""
    # Model endpoints (Ollama on Halo Strix)
    ollama_base_url: str = "http://localhost:11434"

    # Tier 1 models (fast gate)
    prompt_guard_model: str = "prompt-guard-86m"  # HuggingFace inference
    sentinel_model: str = "qualifire/prompt-injection-jailbreak-sentinel-v2"

    # Tier 2 models (semantic gate)
    qwen_guard_model: str = "qwen3:0.6b"  # Fine-tuned for safety
    llama_guard_model: str = "llama-guard3:1b"

    # Tier 3 (code gate)
    codeshield_enabled: bool = True

    # Thresholds
    tier1_threshold: float = 0.7  # Escalate to tier2 if confidence < this
    tier2_threshold: float = 0.8  # Escalate to tier3 if confidence < this
    block_threshold: float = 0.3  # Block if confidence < this

    # Behavior
    quarantine_on_uncertainty: bool = True  # Hold for review if uncertain
    log_all_scans: bool = True  # Audit trail

    # Performance
    tier1_timeout_ms: int = 50
    tier2_timeout_ms: int = 200
    tier3_timeout_ms: int = 500
