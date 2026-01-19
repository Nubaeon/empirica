"""
Graduated Sentinel - Trust-Aware Autonomy Modes

Integrates domain-specific trust calculation with Sentinel modes:
- CONTROLLER: Low trust - human approval for all changes
- OBSERVER: Medium trust - log warnings but don't block
- ADVISORY: High trust - suggest but allow autonomous tactical decisions
- AUTONOMOUS: Very high trust - AI makes strategic decisions with async review

Trust levels gate which Sentinel mode is active:
- TrustLevel.NONE or LOW -> CONTROLLER mode
- TrustLevel.MEDIUM -> OBSERVER mode
- TrustLevel.HIGH -> ADVISORY mode
- TrustLevel.VERY_HIGH -> AUTONOMOUS mode

Usage:
    from empirica.core.autonomy import GraduatedSentinel

    sentinel = GraduatedSentinel(session_id, domain="architecture")
    mode = sentinel.get_effective_mode()  # Based on domain trust
    decision = sentinel.evaluate_action(action_context)
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

from .trust_calculator import TrustCalculator, TrustLevel, DomainTrust

logger = logging.getLogger(__name__)


class SentinelMode(Enum):
    """Graduated Sentinel modes based on earned trust"""
    CONTROLLER = "controller"   # Active blocking - human approval for all
    OBSERVER = "observer"       # Passive logging - human approval for significant
    ADVISORY = "advisory"       # Suggestions only - autonomous tactical decisions
    AUTONOMOUS = "autonomous"   # Full autonomy - async review of strategic decisions


class ActionCategory(Enum):
    """Categories of actions for graduated control"""
    TRIVIAL = "trivial"         # Cosmetic, formatting, comments
    TACTICAL = "tactical"       # Bug fixes, small features
    STRATEGIC = "strategic"     # Architecture, major features
    CRITICAL = "critical"       # Security, data loss, production


@dataclass
class ActionDecision:
    """Result of evaluating an action through graduated sentinel"""
    action: str
    category: ActionCategory
    mode: SentinelMode
    allowed: bool
    requires_human: bool
    rationale: str
    trust_level: TrustLevel
    trust_score: float
    auto_applied: bool = False
    log_entry: Optional[str] = None


@dataclass
class GraduatedProfile:
    """Configuration for graduated autonomy behavior per mode"""
    mode: SentinelMode

    # What requires human approval
    require_human_for: List[ActionCategory] = field(default_factory=list)

    # What gets logged (but not blocked)
    log_actions: List[ActionCategory] = field(default_factory=list)

    # What can be auto-applied
    auto_apply: List[ActionCategory] = field(default_factory=list)

    # Mode-specific thresholds
    confidence_threshold: float = 0.8  # AI confidence needed for auto-apply

    description: str = ""


# Default graduated profiles
GRADUATED_PROFILES = {
    SentinelMode.CONTROLLER: GraduatedProfile(
        mode=SentinelMode.CONTROLLER,
        require_human_for=[
            ActionCategory.TRIVIAL,
            ActionCategory.TACTICAL,
            ActionCategory.STRATEGIC,
            ActionCategory.CRITICAL
        ],
        log_actions=[],
        auto_apply=[],
        confidence_threshold=1.0,  # Never auto-apply
        description="Human approval required for all changes"
    ),
    SentinelMode.OBSERVER: GraduatedProfile(
        mode=SentinelMode.OBSERVER,
        require_human_for=[
            ActionCategory.STRATEGIC,
            ActionCategory.CRITICAL
        ],
        log_actions=[
            ActionCategory.TRIVIAL,
            ActionCategory.TACTICAL
        ],
        auto_apply=[],  # Log but don't auto-apply
        confidence_threshold=0.9,
        description="Log warnings for minor changes, human approval for significant"
    ),
    SentinelMode.ADVISORY: GraduatedProfile(
        mode=SentinelMode.ADVISORY,
        require_human_for=[
            ActionCategory.CRITICAL
        ],
        log_actions=[
            ActionCategory.STRATEGIC
        ],
        auto_apply=[
            ActionCategory.TRIVIAL,
            ActionCategory.TACTICAL
        ],
        confidence_threshold=0.85,
        description="Autonomous tactical decisions, human approval for critical"
    ),
    SentinelMode.AUTONOMOUS: GraduatedProfile(
        mode=SentinelMode.AUTONOMOUS,
        require_human_for=[
            ActionCategory.CRITICAL
        ],
        log_actions=[],
        auto_apply=[
            ActionCategory.TRIVIAL,
            ActionCategory.TACTICAL,
            ActionCategory.STRATEGIC
        ],
        confidence_threshold=0.8,
        description="Full autonomy with async review for strategic, human for critical"
    )
}


# Trust level to mode mapping
TRUST_TO_MODE = {
    TrustLevel.NONE: SentinelMode.CONTROLLER,
    TrustLevel.LOW: SentinelMode.CONTROLLER,
    TrustLevel.MEDIUM: SentinelMode.OBSERVER,
    TrustLevel.HIGH: SentinelMode.ADVISORY,
    TrustLevel.VERY_HIGH: SentinelMode.AUTONOMOUS
}


class GraduatedSentinel:
    """
    Trust-aware Sentinel that adjusts autonomy based on demonstrated calibration.

    The graduated sentinel:
    1. Calculates domain-specific trust from suggestions + calibration + mistakes
    2. Selects appropriate mode (CONTROLLER → AUTONOMOUS)
    3. Evaluates actions against the active profile
    4. Tracks decisions for trust evolution
    """

    def __init__(
        self,
        session_id: str,
        domain: Optional[str] = None,
        project_id: Optional[str] = None,
        override_mode: Optional[SentinelMode] = None
    ):
        """
        Initialize graduated sentinel.

        Args:
            session_id: Current session ID
            domain: Domain for trust calculation (e.g., "architecture", "testing")
            project_id: Project ID for scoping
            override_mode: Override trust-based mode selection
        """
        self.session_id = session_id
        self.domain = domain
        self.project_id = project_id
        self.override_mode = override_mode

        self._trust_calculator: Optional[TrustCalculator] = None
        self._cached_trust: Optional[DomainTrust] = None
        self._decision_log: List[ActionDecision] = []

        # Check for environment override
        env_mode = os.environ.get("EMPIRICA_SENTINEL_MODE", "").lower()
        if env_mode in ["controller", "observer", "advisory", "autonomous"]:
            self.override_mode = SentinelMode(env_mode)
            logger.info(f"Sentinel mode overridden by environment: {env_mode}")

    def _get_trust_calculator(self) -> TrustCalculator:
        """Lazy load trust calculator"""
        if self._trust_calculator is None:
            self._trust_calculator = TrustCalculator(project_id=self.project_id)
        return self._trust_calculator

    def get_domain_trust(self, force_refresh: bool = False) -> DomainTrust:
        """
        Get current trust level for the domain.

        Args:
            force_refresh: Force recalculation instead of using cache

        Returns:
            DomainTrust with score, level, and factors
        """
        if self._cached_trust and not force_refresh:
            return self._cached_trust

        calculator = self._get_trust_calculator()

        if self.domain:
            self._cached_trust = calculator.get_domain_trust(self.domain)
        else:
            # Use overall trust
            all_trusts = calculator.get_all_domain_trust()
            self._cached_trust = all_trusts.get("_overall", DomainTrust(
                domain="_overall",
                score=0.5,
                level=TrustLevel.MEDIUM,
                factors={"calibration": 0.5, "suggestions": 0.5, "mistakes": 1.0},
                suggestions_accepted=0,
                suggestions_rejected=0,
                recent_mistakes=0,
                calibration_accuracy=0.5
            ))

        return self._cached_trust

    def get_effective_mode(self) -> SentinelMode:
        """
        Get the effective Sentinel mode based on trust level.

        Returns:
            SentinelMode that should be active
        """
        # Check for override
        if self.override_mode:
            return self.override_mode

        # Get trust and map to mode
        trust = self.get_domain_trust()
        mode = TRUST_TO_MODE.get(trust.level, SentinelMode.CONTROLLER)

        logger.debug(
            f"Effective mode for domain={self.domain}: {mode.value} "
            f"(trust={trust.level.value}, score={trust.score:.2f})"
        )

        return mode

    def get_effective_profile(self) -> GraduatedProfile:
        """Get the graduated profile for current effective mode"""
        mode = self.get_effective_mode()
        return GRADUATED_PROFILES.get(mode, GRADUATED_PROFILES[SentinelMode.CONTROLLER])

    def classify_action(self, action_context: Dict[str, Any]) -> ActionCategory:
        """
        Classify an action into a category.

        Args:
            action_context: Dict with action, target, metadata

        Returns:
            ActionCategory for the action
        """
        action = action_context.get("action", "").lower()
        target = action_context.get("target", "").lower()
        metadata = action_context.get("metadata", {})

        # Critical actions (always require human)
        critical_patterns = [
            "delete database", "drop table", "rm -rf",
            "production", "deploy", "push main", "push master",
            "credentials", "secrets", "api key", "password",
            "security", "authentication", "authorization"
        ]

        for pattern in critical_patterns:
            if pattern in action or pattern in target:
                return ActionCategory.CRITICAL

        # Strategic actions
        strategic_patterns = [
            "refactor", "architecture", "redesign", "rewrite",
            "major feature", "new module", "database schema",
            "api change", "breaking change", "migration"
        ]

        for pattern in strategic_patterns:
            if pattern in action or pattern in target:
                return ActionCategory.STRATEGIC

        # Trivial actions
        trivial_patterns = [
            "format", "lint", "comment", "typo", "whitespace",
            "rename variable", "documentation", "readme",
            "import order", "style"
        ]

        for pattern in trivial_patterns:
            if pattern in action or pattern in target:
                return ActionCategory.TRIVIAL

        # Default to tactical
        return ActionCategory.TACTICAL

    def evaluate_action(
        self,
        action_context: Dict[str, Any],
        ai_confidence: float = 0.7
    ) -> ActionDecision:
        """
        Evaluate whether an action is allowed under current trust level.

        Args:
            action_context: Dict with action, target, metadata
            ai_confidence: AI's confidence in this action (0.0-1.0)

        Returns:
            ActionDecision with allowed, requires_human, rationale
        """
        action = action_context.get("action", "unknown")
        trust = self.get_domain_trust()
        mode = self.get_effective_mode()
        profile = self.get_effective_profile()
        category = self.classify_action(action_context)

        # Determine if allowed and requirements
        requires_human = category in profile.require_human_for
        should_log = category in profile.log_actions
        can_auto_apply = (
            category in profile.auto_apply and
            ai_confidence >= profile.confidence_threshold
        )

        # Build rationale
        if requires_human:
            allowed = False
            auto_applied = False
            rationale = (
                f"Mode={mode.value}: {category.value} actions require human approval "
                f"(trust_level={trust.level.value}, score={trust.score:.2f})"
            )
        elif can_auto_apply:
            allowed = True
            auto_applied = True
            rationale = (
                f"Mode={mode.value}: Auto-applying {category.value} action "
                f"(confidence={ai_confidence:.2f} >= threshold={profile.confidence_threshold:.2f})"
            )
        elif should_log:
            allowed = True
            auto_applied = False
            rationale = (
                f"Mode={mode.value}: Logging {category.value} action for review "
                f"(trust_level={trust.level.value})"
            )
        else:
            allowed = True
            auto_applied = False
            rationale = f"Mode={mode.value}: Action permitted"

        decision = ActionDecision(
            action=action,
            category=category,
            mode=mode,
            allowed=allowed,
            requires_human=requires_human,
            rationale=rationale,
            trust_level=trust.level,
            trust_score=trust.score,
            auto_applied=auto_applied,
            log_entry=f"[{mode.value}] {category.value}: {action}" if should_log else None
        )

        # Track decision
        self._decision_log.append(decision)

        logger.info(
            f"Action decision: action={action}, category={category.value}, "
            f"allowed={allowed}, requires_human={requires_human}, auto_applied={auto_applied}"
        )

        return decision

    def get_mode_requirements(self) -> Dict[str, Any]:
        """
        Get human-readable requirements for current mode.

        Returns:
            Dict with mode info and requirements
        """
        trust = self.get_domain_trust()
        mode = self.get_effective_mode()
        profile = self.get_effective_profile()

        return {
            "mode": mode.value,
            "description": profile.description,
            "trust_level": trust.level.value,
            "trust_score": trust.score,
            "domain": self.domain or "_overall",
            "requires_human_for": [c.value for c in profile.require_human_for],
            "logs_but_allows": [c.value for c in profile.log_actions],
            "auto_applies": [c.value for c in profile.auto_apply],
            "confidence_threshold": profile.confidence_threshold,
            "override_active": self.override_mode is not None
        }

    def get_decision_log(self) -> List[Dict[str, Any]]:
        """Get log of decisions made this session"""
        return [
            {
                "action": d.action,
                "category": d.category.value,
                "mode": d.mode.value,
                "allowed": d.allowed,
                "requires_human": d.requires_human,
                "auto_applied": d.auto_applied,
                "trust_level": d.trust_level.value,
                "trust_score": d.trust_score
            }
            for d in self._decision_log
        ]

    def get_escalation_thresholds(self) -> Dict[str, Any]:
        """
        Get thresholds for mode escalation (earning more autonomy).

        Returns:
            Dict with current vs required for next level
        """
        trust = self.get_domain_trust()
        current_mode = self.get_effective_mode()

        # Define escalation requirements
        escalation_requirements = {
            SentinelMode.CONTROLLER: {
                "next_mode": SentinelMode.OBSERVER,
                "required_score": 0.4,
                "required_level": TrustLevel.MEDIUM,
                "hints": [
                    "Log more suggestions with high confidence",
                    "Get suggestions accepted by humans",
                    "Improve calibration accuracy"
                ]
            },
            SentinelMode.OBSERVER: {
                "next_mode": SentinelMode.ADVISORY,
                "required_score": 0.6,
                "required_level": TrustLevel.HIGH,
                "hints": [
                    "Maintain suggestion acceptance rate > 80%",
                    "Reduce recent mistakes",
                    "Demonstrate domain expertise"
                ]
            },
            SentinelMode.ADVISORY: {
                "next_mode": SentinelMode.AUTONOMOUS,
                "required_score": 0.8,
                "required_level": TrustLevel.VERY_HIGH,
                "hints": [
                    "Maintain high calibration accuracy (>85%)",
                    "Zero critical mistakes in last 7 days",
                    "Consistent high-quality strategic decisions"
                ]
            },
            SentinelMode.AUTONOMOUS: {
                "next_mode": None,
                "required_score": 1.0,
                "required_level": None,
                "hints": ["Maximum autonomy level reached"]
            }
        }

        current_req = escalation_requirements.get(
            current_mode,
            escalation_requirements[SentinelMode.CONTROLLER]
        )

        required_score = float(current_req["required_score"])
        next_mode = current_req["next_mode"]
        hints = current_req["hints"]
        gap = required_score - trust.score

        return {
            "current_mode": current_mode.value,
            "current_score": trust.score,
            "next_mode": next_mode.value if next_mode else None,
            "required_score": required_score,
            "gap": max(0.0, gap),
            "progress": min(1.0, trust.score / required_score) if required_score > 0 else 1.0,
            "hints": hints,
            "factors": trust.factors
        }

    def close(self):
        """Close calculator connection"""
        if self._trust_calculator:
            self._trust_calculator.close()
            self._trust_calculator = None
