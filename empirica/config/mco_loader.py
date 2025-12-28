#!/usr/bin/env python3
"""
MCO (Meta-Agent Configuration Object) Loader

Loads all MCO configuration files:
- model_profiles.yaml → Model-specific bias corrections
- personas.yaml → Investigation budgets and epistemic priors
- cascade_styles.yaml → Threshold profiles (via ThresholdLoader)
- epistemic_conduct.yaml → Bidirectional accountability triggers
- protocols.yaml → Tool schemas

Usage:
    from empirica.config.mco_loader import get_mco_config

    mco = get_mco_config()

    # Get model-specific bias corrections
    bias = mco.get_model_bias('claude_sonnet')

    # Get persona configuration
    persona = mco.get_persona('implementer')

    # Get active MCO snapshot (for pre-compact saving)
    snapshot = mco.export_snapshot(session_id, ai_id='claude-code', model='claude_sonnet')
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import copy

logger = logging.getLogger(__name__)


class MCOLoader:
    """
    Loads and manages all MCO (Meta-Agent Configuration Object) configs.

    Singleton pattern ensures consistent config across all components.
    """

    _instance: Optional['MCOLoader'] = None

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize MCO loader.

        Args:
            config_dir: Path to mco/ directory (defaults to empirica/config/mco/)
        """
        if config_dir is None:
            config_dir = Path(__file__).parent / 'mco'

        self.config_dir = config_dir
        self.model_profiles: Dict[str, Any] = {}
        self.personas: Dict[str, Any] = {}
        self.epistemic_conduct: Dict[str, Any] = {}
        self.protocols: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

        # Load all MCO configs
        self._load_all()

    @classmethod
    def get_instance(cls, config_dir: Optional[Path] = None) -> 'MCOLoader':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls(config_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing)"""
        cls._instance = None

    def _load_all(self):
        """Load all MCO configuration files"""
        try:
            # Load model profiles
            model_profiles_path = self.config_dir / 'model_profiles.yaml'
            if model_profiles_path.exists():
                with open(model_profiles_path) as f:
                    data = yaml.safe_load(f)
                    self.model_profiles = data.get('model_profiles', {})
                    self.metadata['model_profiles'] = data.get('metadata', {})
                    logger.info(f"✅ Loaded {len(self.model_profiles)} model profiles")

            # Load personas
            personas_path = self.config_dir / 'personas.yaml'
            if personas_path.exists():
                with open(personas_path) as f:
                    data = yaml.safe_load(f)
                    self.personas = data.get('personas', {})
                    self.metadata['personas'] = data.get('metadata', {})
                    logger.info(f"✅ Loaded {len(self.personas)} personas")

            # Load epistemic conduct
            conduct_path = self.config_dir / 'epistemic_conduct.yaml'
            if conduct_path.exists():
                with open(conduct_path) as f:
                    self.epistemic_conduct = yaml.safe_load(f) or {}
                    logger.info("✅ Loaded epistemic conduct config")

            # Load protocols
            protocols_path = self.config_dir / 'protocols.yaml'
            if protocols_path.exists():
                with open(protocols_path) as f:
                    data = yaml.safe_load(f)
                    self.protocols = data.get('protocols', {})
                    self.metadata['protocols'] = data.get('metadata', {})
                    logger.info(f"✅ Loaded {len(self.protocols)} protocols")

        except Exception as e:
            logger.error(f"Failed to load MCO configs: {e}")

    def get_model_bias(self, model_name: str) -> Dict[str, Any]:
        """
        Get bias corrections for a specific model.

        Args:
            model_name: Model identifier (claude_sonnet, claude_haiku, gpt4, etc.)

        Returns:
            Bias correction configuration or empty dict if not found
        """
        if model_name in self.model_profiles:
            return self.model_profiles[model_name].get('bias_profile', {})

        logger.warning(f"Model profile not found: {model_name}")
        return {}

    def get_model_profile(self, model_name: str) -> Dict[str, Any]:
        """Get full model profile"""
        return self.model_profiles.get(model_name, {})

    def get_persona(self, persona_name: str) -> Dict[str, Any]:
        """Get persona configuration"""
        return self.personas.get(persona_name, {})

    def infer_persona(self, ai_id: str = None, task_type: str = None) -> str:
        """
        Infer persona based on AI ID or task type.

        Args:
            ai_id: AI identifier (e.g., 'claude-implementation', 'mistral-research')
            task_type: Task type hint (e.g., 'research', 'implement', 'review')

        Returns:
            Inferred persona name
        """
        # Simple heuristics for now
        if ai_id and 'research' in ai_id.lower():
            return 'researcher'
        if ai_id and 'review' in ai_id.lower():
            return 'reviewer'
        if ai_id and 'coord' in ai_id.lower():
            return 'coordinator'

        if task_type == 'research':
            return 'researcher'
        if task_type == 'review':
            return 'reviewer'
        if task_type == 'coordinate':
            return 'coordinator'

        # Default to implementer
        return 'implementer'

    def infer_model(self, ai_id: str = None) -> str:
        """
        Infer model type from AI ID.

        Args:
            ai_id: AI identifier (e.g., 'claude-code', 'mistral-analysis')

        Returns:
            Inferred model name
        """
        if not ai_id:
            return 'claude_sonnet'  # default

        ai_lower = ai_id.lower()

        if 'haiku' in ai_lower:
            return 'claude_haiku'
        if 'sonnet' in ai_lower or 'claude-code' in ai_lower:
            return 'claude_sonnet'
        if 'gpt-4' in ai_lower or 'gpt4' in ai_lower:
            return 'gpt4'
        if 'gpt-3.5' in ai_lower or 'gpt35' in ai_lower:
            return 'gpt35'

        # Default
        return 'claude_sonnet'

    def export_snapshot(self, session_id: str, ai_id: str = None,
                       model: str = None, persona: str = None,
                       cascade_style: str = 'default') -> Dict[str, Any]:
        """
        Export MCO configuration snapshot for pre-compact saving.

        This snapshot preserves the AI's active configuration so it can be
        restored after memory compact.

        Args:
            session_id: Session identifier
            ai_id: AI identifier (for model/persona inference)
            model: Explicit model name (overrides inference)
            persona: Explicit persona name (overrides inference)
            cascade_style: Active cascade style profile

        Returns:
            MCO configuration snapshot
        """
        # Infer model and persona if not provided
        if model is None:
            model = self.infer_model(ai_id)
        if persona is None:
            persona = self.infer_persona(ai_id)

        # Get configurations
        model_profile = self.get_model_profile(model)
        persona_config = self.get_persona(persona)

        # Load cascade style from ThresholdLoader
        from empirica.config.threshold_loader import get_threshold_config
        threshold_loader = get_threshold_config()

        # Extract key values for quick reference
        bias_corrections = model_profile.get('bias_profile', {})
        investigation_style = persona_config.get('investigation_style', {})

        snapshot = {
            "model": model,
            "persona": persona,
            "cascade_style": cascade_style,

            # Model-specific bias corrections
            "bias_corrections": {
                "uncertainty_adjustment": bias_corrections.get('uncertainty_awareness', 0.0),
                "confidence_adjustment": -bias_corrections.get('overconfidence_correction', 0.0),
                "creativity_bias": bias_corrections.get('creativity_bias', 0.0),
                "speed_vs_accuracy": bias_corrections.get('speed_vs_accuracy', 0.0),
            },

            # Persona investigation budgets
            "investigation_budget": {
                "max_rounds": investigation_style.get('max_rounds', 7),
                "tools_per_round": investigation_style.get('tools_per_round', 2),
                "uncertainty_threshold": investigation_style.get('uncertainty_threshold', 0.60),
            },

            # Threshold values (from cascade_style)
            "thresholds": {
                "engagement": threshold_loader.get('engagement_threshold', 0.60),
                "ready_confidence": threshold_loader.get('cascade.ready_confidence_threshold', 0.70),
                "ready_uncertainty": threshold_loader.get('cascade.ready_uncertainty_threshold', 0.35),
                "ready_context": threshold_loader.get('cascade.ready_context_threshold', 0.65),
            },

            # Full configs for reference
            "full_configs": {
                "model_profile": model_profile,
                "persona_config": persona_config,
            }
        }

        return snapshot

    def format_for_prompt(self, snapshot: Dict[str, Any]) -> str:
        """
        Format MCO snapshot for AI consumption in prompt/bootstrap.

        Args:
            snapshot: MCO configuration snapshot

        Returns:
            Formatted text for presenting to AI
        """
        bias = snapshot['bias_corrections']
        budget = snapshot['investigation_budget']
        thresh = snapshot['thresholds']

        formatted = f"""
## Your MCO Configuration

**Model Profile:** `{snapshot['model']}` (from `model_profiles.yaml`)
**Persona:** `{snapshot['persona']}` (from `personas.yaml`)
**CASCADE Style:** `{snapshot['cascade_style']}` (from `cascade_styles.yaml`)

### Bias Corrections (Apply to Self-Assessments)
- **Uncertainty adjustment:** +{bias['uncertainty_adjustment']:.2f} (you underestimate doubt)
- **Confidence adjustment:** {bias['confidence_adjustment']:.2f} (you overestimate knowing)
- **Creativity bias:** {bias['creativity_bias']:.2f}
- **Speed vs accuracy:** {bias['speed_vs_accuracy']:.2f}

### Investigation Budget
- **Max investigation rounds:** {budget['max_rounds']}
- **Tools per round:** {budget['tools_per_round']}
- **Uncertainty threshold:** {budget['uncertainty_threshold']:.2f}

### Readiness Thresholds
- **Engagement threshold:** {thresh['engagement']:.2f}
- **Ready confidence:** ≥{thresh['ready_confidence']:.2f}
- **Ready uncertainty:** ≤{thresh['ready_uncertainty']:.2f}
- **Ready context:** ≥{thresh['ready_context']:.2f}

**Instruction:** Internalize these values. Apply bias corrections when doing PREFLIGHT/CHECK/POSTFLIGHT assessments.
"""
        return formatted.strip()


# Global instance accessor
def get_mco_config() -> MCOLoader:
    """
    Get global MCOLoader instance.

    Returns:
        Singleton MCOLoader instance
    """
    return MCOLoader.get_instance()
