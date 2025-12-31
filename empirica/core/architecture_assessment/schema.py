"""
Architecture Assessment Schema

Maps Empirica's 13 epistemic vectors to code architecture concerns.

Vector Mappings:
- KNOW → Code Understanding: How well-documented, tested, readable
- UNCERTAINTY → Technical Debt: Hidden complexity, undocumented behavior
- CONTEXT → Integration Clarity: How well it fits in the system
- CLARITY → API Surface: Clean interfaces, low coupling
- COHERENCE → Single Responsibility: Focused purpose, minimal scope creep
- SIGNAL → Change Patterns: Meaningful vs noise commits
- DENSITY → Complexity Hotspots: Cyclomatic complexity, nesting depth
- ENGAGEMENT → Activity Level: Recent development, maintenance attention
- STATE → Health Indicators: Test coverage, linting, type coverage
- CHANGE → Volatility: Churn rate, stability over time
- COMPLETION → Feature Completeness: TODO density, stub methods
- IMPACT → Blast Radius: What breaks if this changes
- DO → Actionability: Clear next steps for improvement
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ArchitectureVectors:
    """
    Epistemic vectors applied to architecture assessment.

    Each vector is 0.0-1.0 where:
    - 0.0 = Poor/Unknown/High risk
    - 1.0 = Excellent/Well-known/Low risk
    """
    # Foundation vectors (from Empirica)
    know: float = 0.5          # Code understanding (docs, tests, readability)
    uncertainty: float = 0.5   # Technical debt (hidden complexity)
    context: float = 0.5       # Integration clarity (system fit)

    # Quality vectors
    clarity: float = 0.5       # API surface cleanliness
    coherence: float = 0.5     # Single responsibility adherence
    signal: float = 0.5        # Meaningful change patterns
    density: float = 0.5       # Complexity (inverted: low density = simple)

    # Activity vectors
    engagement: float = 0.5    # Development activity level
    state: float = 0.5         # Health indicators (coverage, linting)
    change: float = 0.5        # Stability (inverted: low change = stable)

    # Outcome vectors
    completion: float = 0.5    # Feature completeness
    impact: float = 0.5        # Blast radius (inverted: low impact = isolated)
    do: float = 0.5            # Actionability (clear improvement path)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'know': self.know,
            'uncertainty': self.uncertainty,
            'context': self.context,
            'clarity': self.clarity,
            'coherence': self.coherence,
            'signal': self.signal,
            'density': self.density,
            'engagement': self.engagement,
            'state': self.state,
            'change': self.change,
            'completion': self.completion,
            'impact': self.impact,
            'do': self.do,
        }

    def confidence_score(self) -> float:
        """
        Overall confidence in the component.

        Weighted average emphasizing foundational vectors.
        """
        weights = {
            'know': 0.15,
            'uncertainty': 0.15,  # Inverted in calculation
            'context': 0.10,
            'clarity': 0.10,
            'coherence': 0.08,
            'state': 0.10,
            'density': 0.08,  # Inverted
            'change': 0.08,   # Inverted
            'impact': 0.08,   # Inverted
            'completion': 0.04,
            'engagement': 0.02,
            'signal': 0.01,
            'do': 0.01,
        }

        # Invert vectors where low = good
        values = self.to_dict()
        values['uncertainty'] = 1.0 - values['uncertainty']
        values['density'] = 1.0 - values['density']
        values['change'] = 1.0 - values['change']
        values['impact'] = 1.0 - values['impact']

        return sum(values[k] * weights[k] for k in weights)


@dataclass
class CouplingMetrics:
    """Metrics from CouplingAnalyzer."""
    afferent_coupling: int = 0      # Incoming dependencies (who uses us)
    efferent_coupling: int = 0      # Outgoing dependencies (who we use)
    instability: float = 0.5        # Ce / (Ca + Ce) - 0=stable, 1=unstable
    abstractness: float = 0.0       # Abstract types / total types
    distance_from_main: float = 0.5 # |A + I - 1| - distance from ideal

    # API surface metrics
    public_functions: int = 0
    private_functions: int = 0
    api_surface_ratio: float = 0.0  # public / total

    # Boundary clarity
    clear_interface: bool = True
    leaked_internals: List[str] = field(default_factory=list)


@dataclass
class StabilityMetrics:
    """Metrics from StabilityEstimator."""
    total_commits: int = 0
    recent_commits_30d: int = 0
    unique_authors: int = 0

    # Change patterns
    avg_lines_per_commit: float = 0.0
    churn_rate: float = 0.0         # Lines changed / total lines
    hotspot_score: float = 0.0      # Frequency * complexity

    # Time-based
    days_since_last_change: int = 0
    age_days: int = 0
    maintenance_ratio: float = 0.0  # Bug fixes / total commits


@dataclass
class ComponentAssessment:
    """
    Complete epistemic assessment of a code component.

    Combines multiple analyzer outputs into unified view.
    """
    # Identity
    component_path: str
    component_name: str
    component_type: str  # 'module', 'class', 'function', 'package'

    # Epistemic vectors
    vectors: ArchitectureVectors = field(default_factory=ArchitectureVectors)

    # Detailed metrics
    coupling: Optional[CouplingMetrics] = None
    stability: Optional[StabilityMetrics] = None

    # Analysis metadata
    analyzed_at: datetime = field(default_factory=datetime.now)
    analyzer_version: str = "1.0.0"

    # Recommendations
    risk_level: str = "unknown"  # 'low', 'medium', 'high', 'critical'
    recommendations: List[str] = field(default_factory=list)
    improvement_priority: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/display."""
        return {
            'component_path': self.component_path,
            'component_name': self.component_name,
            'component_type': self.component_type,
            'vectors': self.vectors.to_dict(),
            'confidence_score': self.vectors.confidence_score(),
            'risk_level': self.risk_level,
            'recommendations': self.recommendations,
            'analyzed_at': self.analyzed_at.isoformat(),
        }

    def summary(self) -> str:
        """Human-readable summary."""
        conf = self.vectors.confidence_score()
        return (
            f"{self.component_name} ({self.component_type})\n"
            f"  Confidence: {conf:.0%} | Risk: {self.risk_level}\n"
            f"  Know: {self.vectors.know:.0%} | Uncertainty: {self.vectors.uncertainty:.0%}\n"
            f"  Clarity: {self.vectors.clarity:.0%} | Coherence: {self.vectors.coherence:.0%}\n"
            f"  Recommendations: {len(self.recommendations)}"
        )
