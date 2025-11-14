"""
Investigation Strategy - Pluggable Pattern

Provides domain-aware investigation strategies that map epistemic gaps
to actionable tool recommendations.

Design:
- Works with canonical EpistemicAssessment (not old SelfAwarenessResult)
- Pluggable strategy pattern (BaseInvestigationStrategy)
- Domain-aware recommendations (code, creative, research, collaborative)
- Clean integration with tool_management

Usage:
    strategy = CodeAnalysisStrategy()
    recommendations = await strategy.recommend_tools(assessment, task, context)
"""

from typing import Dict, List, Any, Optional, Protocol
from abc import ABC, abstractmethod
from enum import Enum
import logging


from empirica.core.canonical import EpistemicAssessment, VectorState

logger = logging.getLogger(__name__)

class Domain(Enum):
    """Task domain categories"""
    CODE_ANALYSIS = "code_analysis"
    CREATIVE = "creative"
    RESEARCH = "research"
    COLLABORATIVE = "collaborative"
    GENERAL = "general"


class ToolRecommendation:
    """Tool recommendation with reasoning"""

    def __init__(
        self,
        tool_name: str,
        gap_addressed: str,
        confidence: float,
        reasoning: str,
        priority: int = 1
    ):
        self.tool_name = tool_name
        self.gap_addressed = gap_addressed
        self.confidence = confidence
        self.reasoning = reasoning
        self.priority = priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tool_name': self.tool_name,
            'gap_addressed': self.gap_addressed,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'priority': self.priority
        }


class BaseInvestigationStrategy(ABC):
    """
    Base class for investigation strategies

    Subclasses implement domain-specific tool recommendation logic.
    """

    def __init__(self):
        # REMOVED: gap_threshold heuristic (was 0.60)
        # Gaps now extracted from AI's self-assessment via warrants_investigation flag
        pass

    @abstractmethod
    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: Dict[str, Any],
        profile: Optional['InvestigationProfile'] = None
    ) -> List[ToolRecommendation]:
        """
        Recommend tools based on epistemic assessment and profile

        Args:
            assessment: Canonical EpistemicAssessment
            task: Task description
            context: Additional context
            profile: Investigation profile (if None, uses default)

        Returns:
            List of ToolRecommendation sorted by priority
        """
        pass

    def _extract_gaps(self, assessment: EpistemicAssessment) -> Dict[str, VectorState]:
        """
        Extract self-assessed gaps - NO HEURISTICS

        Returns dict mapping vector_name → VectorState for vectors AI flagged
        via warrants_investigation during self-assessment.
        """
        gaps = {}

        # Map all vectors
        vector_map = {
            'know': assessment.know,
            'do': assessment.do,
            'context': assessment.context,
            'clarity': assessment.clarity,
            'coherence': assessment.coherence,
            'signal': assessment.signal,
            'density': assessment.density,
            'state': assessment.state,
            'change': assessment.change,
            'completion': assessment.completion,
            'impact': assessment.impact,
            'engagement': assessment.engagement,
        }

        # Extract only self-assessed gaps
        for vector_name, vector_state in vector_map.items():
            if vector_state.warrants_investigation:
                gaps[vector_name] = vector_state

        return gaps

    def _prioritize_gaps(self, gaps: Dict[str, VectorState]) -> List[str]:
        """
        Prioritize gaps by tier and severity

        Priority order:
        1. ENGAGEMENT (gate)
        2. FOUNDATION (35% weight)
        3. COMPREHENSION (25% weight)
        4. EXECUTION (25% weight)

        Within tier: lower scores = higher priority
        """
        prioritized = []

        # Tier 0: ENGAGEMENT (gate)
        if 'engagement' in gaps:
            prioritized.append('engagement')

        # Tier 1: FOUNDATION
        foundation_gaps = [(name, gaps[name].score) for name in ['know', 'do', 'context'] if name in gaps]
        foundation_gaps.sort(key=lambda x: x[1])  # Lowest first
        prioritized.extend([name for name, _ in foundation_gaps])

        # Tier 2: COMPREHENSION
        comp_gaps = [(name, gaps[name].score) for name in ['clarity', 'coherence', 'signal', 'density'] if name in gaps]
        comp_gaps.sort(key=lambda x: x[1])
        prioritized.extend([name for name, _ in comp_gaps])

        # Tier 3: EXECUTION
        exec_gaps = [(name, gaps[name].score) for name in ['state', 'change', 'completion', 'impact'] if name in gaps]
        exec_gaps.sort(key=lambda x: x[1])
        prioritized.extend([name for name, _ in exec_gaps])

        return prioritized


class CodeAnalysisStrategy(BaseInvestigationStrategy):
    """
    Investigation strategy for code analysis tasks

    Maps gaps to code-specific tools:
    - know → search, documentation, codebase exploration
    - do → tool availability checks
    - context → workspace scanning, git status
    - state → file reading, directory structure
    - change → git diff, modification tracking
    """

    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: Dict[str, Any],
        profile: Optional['InvestigationProfile'] = None
    ) -> List[ToolRecommendation]:
        """Recommend code analysis tools based on gaps"""
        gaps = self._extract_gaps(assessment)
        prioritized_gaps = self._prioritize_gaps(gaps)
        recommendations = []

        for i, gap_name in enumerate(prioritized_gaps[:5], 1):  # Top 5 gaps
            gap = gaps[gap_name]

            if gap_name == 'know':
                recommendations.append(ToolRecommendation(
                    tool_name='codebase_search',
                    gap_addressed='know',
                    confidence=0.85,
                    reasoning=f"Domain knowledge gap ({gap.score:.2f}): Search codebase for relevant patterns, functions, or modules. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'do':
                recommendations.append(ToolRecommendation(
                    tool_name='capability_check',
                    gap_addressed='do',
                    confidence=0.80,
                    reasoning=f"Capability uncertainty ({gap.score:.2f}): Verify tool availability and execution environment. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'context':
                recommendations.append(ToolRecommendation(
                    tool_name='workspace_scan',
                    gap_addressed='context',
                    confidence=0.90,
                    reasoning=f"Context validity gap ({gap.score:.2f}): Scan workspace, check git status, validate assumptions. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'state':
                recommendations.append(ToolRecommendation(
                    tool_name='environment_mapping',
                    gap_addressed='state',
                    confidence=0.85,
                    reasoning=f"State mapping gap ({gap.score:.2f}): Read relevant files, map directory structure. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'change':
                recommendations.append(ToolRecommendation(
                    tool_name='git_diff',
                    gap_addressed='change',
                    confidence=0.80,
                    reasoning=f"Change tracking gap ({gap.score:.2f}): Review recent changes, track modifications. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'clarity':
                recommendations.append(ToolRecommendation(
                    tool_name='clarification_request',
                    gap_addressed='clarity',
                    confidence=0.95,
                    reasoning=f"Clarity gap ({gap.score:.2f}): Request user clarification on ambiguous aspects. {gap.rationale}",
                    priority=i
                ))

        return recommendations


class ResearchStrategy(BaseInvestigationStrategy):
    """
    Investigation strategy for research tasks

    Maps gaps to research-specific tools:
    - know → web search, documentation fetch, knowledge retrieval
    - context → historical context, related work
    - clarity → structured clarification
    """

    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: Dict[str, Any],
        profile: Optional['InvestigationProfile'] = None
    ) -> List[ToolRecommendation]:
        """Recommend research tools based on gaps"""
        gaps = self._extract_gaps(assessment)
        prioritized_gaps = self._prioritize_gaps(gaps)
        recommendations = []

        for i, gap_name in enumerate(prioritized_gaps[:5], 1):
            gap = gaps[gap_name]

            if gap_name == 'know':
                recommendations.append(ToolRecommendation(
                    tool_name='knowledge_search',
                    gap_addressed='know',
                    confidence=0.90,
                    reasoning=f"Knowledge gap ({gap.score:.2f}): Search documentation, papers, or web sources. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'context':
                recommendations.append(ToolRecommendation(
                    tool_name='context_retrieval',
                    gap_addressed='context',
                    confidence=0.85,
                    reasoning=f"Context gap ({gap.score:.2f}): Retrieve historical context, related work, background. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'clarity':
                recommendations.append(ToolRecommendation(
                    tool_name='structured_clarification',
                    gap_addressed='clarity',
                    confidence=0.95,
                    reasoning=f"Clarity gap ({gap.score:.2f}): Ask structured questions to narrow scope. {gap.rationale}",
                    priority=i
                ))

        return recommendations


class CollaborativeStrategy(BaseInvestigationStrategy):
    """
    Investigation strategy for collaborative tasks

    Maps gaps to collaboration-specific tools:
    - engagement → goal creation, shared understanding
    - clarity → interactive clarification
    - coherence → context synchronization
    """

    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: Dict[str, Any],
        profile: Optional['InvestigationProfile'] = None
    ) -> List[ToolRecommendation]:
        """Recommend collaboration tools based on gaps"""
        gaps = self._extract_gaps(assessment)
        prioritized_gaps = self._prioritize_gaps(gaps)
        recommendations = []

        for i, gap_name in enumerate(prioritized_gaps[:5], 1):
            gap = gaps[gap_name]

            if gap_name == 'engagement':
                recommendations.append(ToolRecommendation(
                    tool_name='goal_creation',
                    gap_addressed='engagement',
                    confidence=0.90,
                    reasoning=f"Engagement gap ({gap.score:.2f}): Create shared goals, establish collaboration framework. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'clarity':
                recommendations.append(ToolRecommendation(
                    tool_name='interactive_clarification',
                    gap_addressed='clarity',
                    confidence=0.95,
                    reasoning=f"Clarity gap ({gap.score:.2f}): Engage in dialogue to clarify expectations. {gap.rationale}",
                    priority=i
                ))

            elif gap_name == 'coherence':
                recommendations.append(ToolRecommendation(
                    tool_name='context_sync',
                    gap_addressed='coherence',
                    confidence=0.85,
                    reasoning=f"Coherence gap ({gap.score:.2f}): Synchronize shared context, align understanding. {gap.rationale}",
                    priority=i
                ))

        return recommendations


class GeneralStrategy(BaseInvestigationStrategy):
    """
    General-purpose investigation strategy

    Falls back to standard gap→tool mapping when domain is unclear.
    """

    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: Dict[str, Any],
        profile: Optional['InvestigationProfile'] = None
    ) -> List[ToolRecommendation]:
        """Recommend general tools based on gaps"""
        gaps = self._extract_gaps(assessment)
        prioritized_gaps = self._prioritize_gaps(gaps)
        recommendations = []

        # Standard mapping
        gap_to_tool = {
            'know': ('knowledge_retrieval', 'Retrieve domain knowledge'),
            'do': ('capability_check', 'Verify execution capabilities'),
            'context': ('environment_check', 'Validate environmental context'),
            'clarity': ('clarification', 'Request user clarification'),
            'coherence': ('context_review', 'Review conversation context'),
            'signal': ('priority_analysis', 'Analyze task priorities'),
            'state': ('state_mapping', 'Map current state'),
            'change': ('change_tracking', 'Track modifications'),
            'completion': ('verification', 'Verify completion criteria'),
            'impact': ('impact_analysis', 'Analyze consequences'),
            'engagement': ('goal_creation', 'Establish collaboration')
        }

        for i, gap_name in enumerate(prioritized_gaps[:5], 1):
            gap = gaps[gap_name]
            if gap_name in gap_to_tool:
                tool_name, description = gap_to_tool[gap_name]
                recommendations.append(ToolRecommendation(
                    tool_name=tool_name,
                    gap_addressed=gap_name,
                    confidence=0.75,
                    reasoning=f"{description} (gap: {gap.score:.2f}). {gap.rationale}",
                    priority=i
                ))

        return recommendations


class StrategySelector:
    """
    Selects appropriate investigation strategy based on domain
    
    Supports plugin-based extension: register custom strategies for new domains.

    Usage:
        selector = StrategySelector()
        
        # Use built-in strategy
        strategy = selector.get_strategy(domain=Domain.CODE_ANALYSIS)
        
        # Register custom strategy
        selector.register_strategy(Domain.MEDICAL, MedicalInvestigationStrategy())
        
        recommendations = await strategy.recommend_tools(assessment, task, context)
    """

    def __init__(self, custom_strategies: Optional[Dict[Domain, BaseInvestigationStrategy]] = None):
        """
        Initialize strategy selector with built-in and optional custom strategies
        
        Args:
            custom_strategies: Optional dict mapping Domain to custom strategy instances
        """
        # Built-in strategies
        self._strategies = {
            Domain.CODE_ANALYSIS: CodeAnalysisStrategy(),
            Domain.RESEARCH: ResearchStrategy(),
            Domain.COLLABORATIVE: CollaborativeStrategy(),
            Domain.GENERAL: GeneralStrategy(),
            Domain.CREATIVE: GeneralStrategy()  # Creative uses general for now
        }
        
        # Register custom strategies if provided
        if custom_strategies:
            for domain, strategy in custom_strategies.items():
                self.register_strategy(domain, strategy)

    def register_strategy(self, domain: Domain, strategy: BaseInvestigationStrategy) -> None:
        """
        Register a custom investigation strategy for a domain
        
        Args:
            domain: Domain enum value
            strategy: Strategy instance implementing BaseInvestigationStrategy
            
        Example:
            class MedicalStrategy(BaseInvestigationStrategy):
                async def recommend_tools(self, assessment, task, context, profile):
                    # Custom medical investigation logic
                    pass
            
            selector = StrategySelector()
            selector.register_strategy(Domain.CODE_ANALYSIS, MedicalStrategy())
        """
        if not isinstance(strategy, BaseInvestigationStrategy):
            raise TypeError(f"Strategy must implement BaseInvestigationStrategy, got {type(strategy)}")
        
        self._strategies[domain] = strategy

    def get_strategy(self, domain: Domain = Domain.GENERAL) -> BaseInvestigationStrategy:
        """
        Get strategy for domain
        
        Args:
            domain: Domain to get strategy for (defaults to GENERAL)
            
        Returns:
            Strategy instance for domain, or GENERAL strategy if not found
        """
        return self._strategies.get(domain, self._strategies[Domain.GENERAL])
    
    def list_domains(self) -> List[Domain]:
        """List all registered domains"""
        return list(self._strategies.keys())

    def infer_domain(
        self,
        task: str,
        context: Dict[str, Any],
        profile: Optional['InvestigationProfile'] = None
    ) -> Domain:
        """
        Infer domain based on profile strategy (NO KEYWORD MATCHING).
        
        Uses profile.strategy.domain_detection to determine approach:
        - DECLARED: Domain must be in context['domain']
        - REASONING: Use genuine AI reasoning (future: call LLM)
        - PLUGIN_ASSISTED: Get hints from plugins, AI decides
        - HYBRID: Mix of reasoning and plugins (current default)
        - EMERGENT: Start generic, let domain emerge
        """
        if profile is None:
            from empirica.config.profile_loader import load_profile
            profile = load_profile('balanced')
        
        strategy = profile.strategy.domain_detection
        
        if strategy.value == 'declared':
            # Domain must be explicitly declared
            domain = context.get('domain')
            if not domain:
                raise ValueError("Domain must be declared for this profile")
            return Domain[domain.upper()]
        
        elif strategy.value == 'reasoning':
            # Future: Call LLM to reason about domain
            # For now, fall through to hybrid
            pass
        
        elif strategy.value == 'emergent':
            # Start generic, let domain emerge through investigation
            return Domain.GENERAL
        
        # HYBRID or fallback: Use context clues (not keywords!)
        # Check for explicit hints in context
        if 'domain_hint' in context:
            try:
                return Domain[context['domain_hint'].upper()]
            except (KeyError, AttributeError):
                pass
        
        # Default to GENERAL
        return Domain.GENERAL


# CONVENIENCE FUNCTION

async def recommend_investigation_tools(
    assessment: EpistemicAssessment,
    task: str,
    context: Optional[Dict[str, Any]] = None,
    domain: Optional[Domain] = None,
    profile: Optional['InvestigationProfile'] = None
) -> List[ToolRecommendation]:
    """
    Convenience function for tool recommendations

    Args:
        assessment: Canonical EpistemicAssessment
        task: Task description
        context: Additional context
        domain: Task domain (auto-inferred if None)
        profile: Investigation profile (if None, uses default)

    Returns:
        List of ToolRecommendation sorted by priority

    Example:
        recommendations = await recommend_investigation_tools(
            assessment,
            "Refactor the authentication module",
            context={'cwd': '/path/to/project'}
        )

        for rec in recommendations:
            logger.info(f"Tool: {rec.tool_name} (priority {rec.priority})")
            logger.info(f"Addresses: {rec.gap_addressed}")
            logger.info(f"Reasoning: {rec.reasoning}")
    """
    if context is None:
        context = {}

    if profile is None:
        from empirica.config.profile_loader import load_profile
        profile = load_profile('balanced')

    selector = StrategySelector()

    # Infer domain if not provided
    if domain is None:
        domain = selector.infer_domain(task, context, profile)

    # Get strategy and recommend
    strategy = selector.get_strategy(domain)
    return await strategy.recommend_tools(assessment, task, context, profile)
