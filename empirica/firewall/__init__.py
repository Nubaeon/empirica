"""Noetic Firewall - Isolated comms layer with epistemic integrity.

API Boundary Design:

    ┌─────────────────────────────────────────────────────────────┐
    │                     MAIN SYSTEM                              │
    │   (Claude Code, Subagents, External AI Instances)           │
    └─────────────────────┬───────────────────────────────────────┘
                          │
                          │ send_message(envelope)
                          │ receive_message() -> envelope
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                  NOETIC FIREWALL                             │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  TIER 1: Fast Gate (<10ms)                          │    │
    │  │  ├─ PromptGuard-86M (injection detection)           │    │
    │  │  └─ Sentinel v2 (jailbreak detection)               │    │
    │  └─────────────────────────────────────────────────────┘    │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  TIER 2: Semantic Gate (~50ms, on flag)             │    │
    │  │  ├─ Qwen3Guard-0.6B (content safety)                │    │
    │  │  └─ Llama Guard 3-1B (13 hazard categories)         │    │
    │  └─────────────────────────────────────────────────────┘    │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │  TIER 3: Code Gate (~70ms, when code detected)      │    │
    │  │  └─ CodeShield (static analysis)                    │    │
    │  └─────────────────────────────────────────────────────┘    │
    │                                                              │
    │  Confidence Extraction:                                      │
    │  - PromptGuard: P(injection) -> uncertainty signal           │
    │  - LlamaGuard: category codes -> signal density              │
    │  - Overall: composite firewall_confidence                    │
    └─────────────────────┬───────────────────────────────────────┘
                          │
                          │ git notes / Forgejo sync
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │               EXTERNAL AGENTS (Other Machines)               │
    └─────────────────────────────────────────────────────────────┘

Key Design Principles:
1. All inter-agent messages pass through firewall
2. Firewall contributes confidence signals to epistemic envelope
3. Blocked messages are logged with reason (dead-end for future)
4. Firewall runs on isolated hardware (Halo Strix 128GB)
5. Main system never sees raw external messages
"""

from .schema import (
    EpistemicEnvelope,
    FirewallDecision,
    FirewallTier,
    MessageScanResult,
    FirewallConfig,
)

from .api import (
    FirewallClient,
    scan_message,
    wrap_with_envelope,
    extract_confidence,
)

__all__ = [
    "EpistemicEnvelope",
    "FirewallDecision",
    "FirewallTier",
    "MessageScanResult",
    "FirewallConfig",
    "FirewallClient",
    "scan_message",
    "wrap_with_envelope",
    "extract_confidence",
]
