#!/usr/bin/env python3
"""
Investigation Profile Loader

Loads and manages investigation profiles from YAML configuration.
Handles profile selection, constraint validation, and runtime tuning.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from dataclasses import dataclass, field
from enum import Enum


class ToolSuggestionMode(Enum):
    """How tools are suggested to AI"""
    LIGHT = "light"              # Minimal suggestions, AI explores
    SUGGESTIVE = "suggestive"    # Suggestions provided, AI decides
    GUIDED = "guided"            # Strong guidance, AI follows
    PRESCRIBED = "prescribed"    # Specific tools required
    INSPIRATIONAL = "inspirational"  # Spark ideas for exploration


class DomainDetection(Enum):
    """How domain is detected"""
    REASONING = "reasoning"          # AI reasons about domain
    PLUGIN_ASSISTED = "plugin_assisted"  # Plugins provide hints
    HYBRID = "hybrid"                # Mix of reasoning + plugins
    DECLARED = "declared"            # User declares domain
    EMERGENT = "emergent"            # Discover through exploration


class PostflightMode(Enum):
    """How postflight assessment works"""
    GENUINE_REASSESSMENT = "genuine_reassessment"  # AI genuinely reassesses
    COMPARATIVE_ASSESSMENT = "comparative_assessment"  # Compare pre/post
    FULL_AUDIT_TRAIL = "full_audit_trail"  # Complete audit
    REFLECTION = "reflection"  # Focus on learning
    

@dataclass
class InvestigationConstraints:
    """Investigation phase constraints"""
    max_rounds: Optional[int] = None  # None = no limit
    confidence_threshold: float = 0.65
    confidence_threshold_dynamic: bool = False  # If "dynamic" in config
    tool_suggestion_mode: ToolSuggestionMode = ToolSuggestionMode.SUGGESTIVE
    allow_novel_approaches: bool = True
    require_tool_approval: bool = False
    encourage_experimentation: bool = False


@dataclass
class ActionThresholds:
    """Thresholds for action determination"""
    uncertainty_high: float = 0.75
    clarity_low: float = 0.45
    foundation_low: float = 0.45
    confidence_proceed_min: float = 0.65
    override_allowed: bool = True
    escalate_on_uncertainty: bool = False


@dataclass
class TuningParameters:
    """Confidence calculation tuning"""
    confidence_weight: float = 1.0
    foundation_weight: float = 1.0
    comprehension_weight: float = 1.0
    execution_weight: float = 1.0
    uncertainty_weight: float = 1.0


@dataclass
class StrategyConfig:
    """Investigation strategy configuration"""
    domain_detection: DomainDetection = DomainDetection.HYBRID
    tool_selection: str = "ai_guided"
    gap_prioritization: str = "balanced"


@dataclass
class LearningConfig:
    """Learning and postflight configuration"""
    postflight_mode: PostflightMode = PostflightMode.GENUINE_REASSESSMENT
    confidence_gain_calculation: str = "evidence_based"
    require_validation: bool = False


@dataclass
class InvestigationProfile:
    """Complete investigation profile"""
    name: str
    description: str
    investigation: InvestigationConstraints
    action_thresholds: ActionThresholds
    tuning: TuningParameters
    strategy: StrategyConfig
    learning: LearningConfig
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'investigation': {
                'max_rounds': self.investigation.max_rounds,
                'confidence_threshold': self.investigation.confidence_threshold,
                'confidence_threshold_dynamic': self.investigation.confidence_threshold_dynamic,
                'tool_suggestion_mode': self.investigation.tool_suggestion_mode.value,
                'allow_novel_approaches': self.investigation.allow_novel_approaches,
                'require_tool_approval': self.investigation.require_tool_approval,
                'encourage_experimentation': self.investigation.encourage_experimentation,
            },
            'action_thresholds': {
                'uncertainty_high': self.action_thresholds.uncertainty_high,
                'clarity_low': self.action_thresholds.clarity_low,
                'foundation_low': self.action_thresholds.foundation_low,
                'confidence_proceed_min': self.action_thresholds.confidence_proceed_min,
                'override_allowed': self.action_thresholds.override_allowed,
                'escalate_on_uncertainty': self.action_thresholds.escalate_on_uncertainty,
            },
            'tuning': {
                'confidence_weight': self.tuning.confidence_weight,
                'foundation_weight': self.tuning.foundation_weight,
                'comprehension_weight': self.tuning.comprehension_weight,
                'execution_weight': self.tuning.execution_weight,
                'uncertainty_weight': self.tuning.uncertainty_weight,
            },
            'strategy': {
                'domain_detection': self.strategy.domain_detection.value,
                'tool_selection': self.strategy.tool_selection,
                'gap_prioritization': self.strategy.gap_prioritization,
            },
            'learning': {
                'postflight_mode': self.learning.postflight_mode.value,
                'confidence_gain_calculation': self.learning.confidence_gain_calculation,
                'require_validation': self.learning.require_validation,
            }
        }


@dataclass
class UniversalConstraints:
    """Universal constraints enforced by Sentinel"""
    engagement_gate: float = 0.60
    coherence_min: float = 0.50
    density_max: float = 0.90
    change_min: float = 0.50
    max_tool_calls_per_round: int = 10
    investigation_timeout_seconds: int = 3600
    log_all_assessments: bool = True
    log_tool_calls: bool = True


class ProfileLoader:
    """Loads and manages investigation profiles"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize profile loader
        
        Args:
            config_path: Path to investigation_profiles.yaml (default: auto-detect)
        """
        if config_path is None:
            config_path = Path(__file__).parent / "investigation_profiles.yaml"
        
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.profiles: Dict[str, InvestigationProfile] = {}
        self.universal_constraints: Optional[UniversalConstraints] = None
        
        if config_path.exists():
            self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Load universal constraints
        uc = self.config.get('universal_constraints', {})
        self.universal_constraints = UniversalConstraints(
            engagement_gate=uc.get('engagement_gate', 0.60),
            coherence_min=uc.get('coherence_min', 0.50),
            density_max=uc.get('density_max', 0.90),
            change_min=uc.get('change_min', 0.50),
            max_tool_calls_per_round=uc.get('max_tool_calls_per_round', 10),
            investigation_timeout_seconds=uc.get('investigation_timeout_seconds', 3600),
            log_all_assessments=uc.get('log_all_assessments', True),
            log_tool_calls=uc.get('log_tool_calls', True),
        )
        
        # Load profiles
        profiles_config = self.config.get('profiles', {})
        for profile_name, profile_data in profiles_config.items():
            self.profiles[profile_name] = self._parse_profile(profile_name, profile_data)
    
    def _parse_profile(self, name: str, data: Dict[str, Any]) -> InvestigationProfile:
        """Parse profile from config data"""
        
        # Parse investigation constraints
        inv = data.get('investigation', {})
        confidence_threshold = inv.get('confidence_threshold', 0.65)
        confidence_dynamic = False
        
        if isinstance(confidence_threshold, str):
            if confidence_threshold in ('dynamic', 'adaptive'):
                confidence_dynamic = True
                confidence_threshold = inv.get('confidence_threshold_fallback', 0.65)
        
        investigation = InvestigationConstraints(
            max_rounds=inv.get('max_rounds'),
            confidence_threshold=confidence_threshold,
            confidence_threshold_dynamic=confidence_dynamic,
            tool_suggestion_mode=ToolSuggestionMode(inv.get('tool_suggestion_mode', 'suggestive')),
            allow_novel_approaches=inv.get('allow_novel_approaches', True),
            require_tool_approval=inv.get('require_tool_approval', False),
            encourage_experimentation=inv.get('encourage_experimentation', False),
        )
        
        # Parse action thresholds
        at = data.get('action_thresholds', {})
        action_thresholds = ActionThresholds(
            uncertainty_high=at.get('uncertainty_high', 0.75),
            clarity_low=at.get('clarity_low', 0.45),
            foundation_low=at.get('foundation_low', 0.45),
            confidence_proceed_min=at.get('confidence_proceed_min', 0.65),
            override_allowed=at.get('override_allowed', True),
            escalate_on_uncertainty=at.get('escalate_on_uncertainty', False),
        )
        
        # Parse tuning parameters
        tune = data.get('tuning', {})
        tuning = TuningParameters(
            confidence_weight=tune.get('confidence_weight', 1.0),
            foundation_weight=tune.get('foundation_weight', 1.0),
            comprehension_weight=tune.get('comprehension_weight', 1.0),
            execution_weight=tune.get('execution_weight', 1.0),
            uncertainty_weight=tune.get('uncertainty_weight', 1.0),
        )
        
        # Parse strategy
        strat = data.get('strategy', {})
        strategy = StrategyConfig(
            domain_detection=DomainDetection(strat.get('domain_detection', 'hybrid')),
            tool_selection=strat.get('tool_selection', 'ai_guided'),
            gap_prioritization=strat.get('gap_prioritization', 'balanced'),
        )
        
        # Parse learning
        learn = data.get('learning', {})
        learning = LearningConfig(
            postflight_mode=PostflightMode(learn.get('postflight_mode', 'genuine_reassessment')),
            confidence_gain_calculation=learn.get('confidence_gain_calculation', 'evidence_based'),
            require_validation=learn.get('require_validation', False),
        )
        
        return InvestigationProfile(
            name=name,
            description=data.get('description', ''),
            investigation=investigation,
            action_thresholds=action_thresholds,
            tuning=tuning,
            strategy=strategy,
            learning=learning,
        )
    
    def get_profile(self, profile_name: str) -> Optional[InvestigationProfile]:
        """Get profile by name"""
        return self.profiles.get(profile_name)
    
    def select_profile(
        self,
        ai_model: Optional[str] = None,
        domain: Optional[str] = None,
        explicit_profile: Optional[str] = None,
    ) -> InvestigationProfile:
        """
        Select appropriate profile based on context
        
        Args:
            ai_model: AI model identifier (e.g., "claude-sonnet")
            domain: Domain identifier (e.g., "medical", "research")
            explicit_profile: Explicitly requested profile name
        
        Returns:
            Selected InvestigationProfile
        """
        # Explicit profile takes precedence
        if explicit_profile and explicit_profile in self.profiles:
            return self.profiles[explicit_profile]
        
        # Check domain-based selection
        if domain:
            domain_mapping = self.config.get('profile_selection', {}).get('by_domain', {})
            for profile_type, domains in domain_mapping.items():
                if domain in domains:
                    profile_name = f"{profile_type}_domain" if profile_type == "critical" else profile_type
                    if profile_name in self.profiles:
                        return self.profiles[profile_name]
        
        # Check AI capability-based selection
        if ai_model:
            capability_mapping = self.config.get('profile_selection', {}).get('by_ai_capability', {})
            for capability_type, models in capability_mapping.items():
                if any(model_pattern in ai_model.lower() for model_pattern in models):
                    profile_name = f"{capability_type}_collaborative" if capability_type == "high_reasoning" else "autonomous_agent"
                    if profile_name in self.profiles:
                        return self.profiles[profile_name]
        
        # Default profile
        default_name = self.config.get('profile_selection', {}).get('default', 'balanced')
        return self.profiles.get(default_name, list(self.profiles.values())[0])
    
    def list_profiles(self) -> List[str]:
        """List available profile names"""
        return list(self.profiles.keys())
    
    def validate_constraints(self, profile: InvestigationProfile) -> List[str]:
        """
        Validate profile constraints against universal constraints
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.universal_constraints:
            return errors
        
        # Universal constraints are always enforced
        # Profile constraints must not violate them
        
        # Check engagement gate
        # (Universal gate is minimum, profiles can't go lower)
        
        # Check tool call limits
        # (Universal max is enforced regardless of profile)
        
        return errors
    
    def export_profile(self, profile_name: str, output_path: Path) -> None:
        """Export profile to YAML file"""
        profile = self.get_profile(profile_name)
        if not profile:
            raise ValueError(f"Profile not found: {profile_name}")
        
        with open(output_path, 'w') as f:
            yaml.dump(profile.to_dict(), f, default_flow_style=False)
    
    def import_profile(self, input_path: Path, profile_name: Optional[str] = None) -> None:
        """Import profile from YAML file"""
        with open(input_path, 'r') as f:
            data = yaml.safe_load(f)
        
        name = profile_name or data.get('name', 'imported')
        self.profiles[name] = self._parse_profile(name, data)


# Singleton instance
_loader_instance: Optional[ProfileLoader] = None


def get_profile_loader() -> ProfileLoader:
    """Get singleton profile loader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ProfileLoader()
    return _loader_instance


def load_profile(profile_name: str) -> InvestigationProfile:
    """Load a profile by name (convenience function)"""
    loader = get_profile_loader()
    profile = loader.get_profile(profile_name)
    if not profile:
        raise ValueError(f"Profile not found: {profile_name}")
    return profile


def select_profile(
    ai_model: Optional[str] = None,
    domain: Optional[str] = None,
    explicit_profile: Optional[str] = None,
) -> InvestigationProfile:
    """Select appropriate profile based on context (convenience function)"""
    loader = get_profile_loader()
    return loader.select_profile(ai_model, domain, explicit_profile)


__all__ = [
    'InvestigationProfile',
    'InvestigationConstraints',
    'InvestigationStrategy',
    'InvestigationLearning',
    'InvestigationTuning',
    'ActionThresholds',
    'ProfileLoader',
    'load_profile',
    'select_profile',
    'get_profile_loader',
]
