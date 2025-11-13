# Extensible Investigation Strategy System

**Version:** 2.0  
**Status:** Production Ready  
**Philosophy:** Plugin-based, domain-agnostic, community-extensible

---

## Overview

Empirica's investigation system is now **fully extensible**, allowing users to:
- Register custom investigation strategies for specialized domains
- Override built-in strategies
- Create domain-specific tool recommendations
- Integrate custom investigation plugins

---

## Architecture

### Built-In Components

**1. BaseInvestigationStrategy (Abstract)**
- Interface all strategies must implement
- `recommend_tools()` method returns tool recommendations based on epistemic gaps

**2. Built-In Strategies**
- `CodeAnalysisStrategy` - Software development
- `ResearchStrategy` - Academic/scientific research
- `CollaborativeStrategy` - Human-AI collaboration
- `GeneralStrategy` - General-purpose fallback

**3. StrategySelector**
- Manages strategy registration and selection
- Supports custom strategy plugins
- Falls back to GENERAL strategy if domain not found

### Extension Points

**1. Custom Strategies**
- Inherit from `BaseInvestigationStrategy`
- Implement domain-specific tool recommendations
- Register with `StrategySelector`

**2. Custom Domains**
- Use existing `Domain` enum values
- Or request new domains via extending enum (advanced)

**3. Investigation Plugins**
- Use `InvestigationPlugin` for custom tools
- Tools automatically included in recommendations

---

## Quick Start: Custom Strategy

### Step 1: Create Custom Strategy

```python
from empirica.core.metacognitive_cascade.investigation_strategy import (
    BaseInvestigationStrategy,
    ToolRecommendation
)
from empirica.core.canonical import EpistemicAssessment

class MedicalInvestigationStrategy(BaseInvestigationStrategy):
    """Custom strategy for medical/healthcare domain"""
    
    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: dict,
        profile = None
    ) -> list[ToolRecommendation]:
        """Recommend medical-specific tools based on gaps"""
        
        recommendations = []
        gaps = assessment.get_gaps(threshold=0.85)
        
        for i, gap in enumerate(gaps):
            if gap.vector == 'know':
                # Medical literature search
                recommendations.append(ToolRecommendation(
                    tool_name='pubmed_search',
                    gap_addressed='know',
                    confidence=0.85,
                    reasoning=f"Search PubMed for evidence. {gap.rationale}",
                    priority=i
                ))
            
            elif gap.vector == 'impact':
                # Safety checks
                recommendations.append(ToolRecommendation(
                    tool_name='drug_interaction_check',
                    gap_addressed='impact',
                    confidence=0.95,
                    reasoning="Check drug interactions",
                    priority=i
                ))
        
        return sorted(recommendations, key=lambda x: (x.priority, -x.confidence))
```

### Step 2: Register Strategy

```python
from empirica.core.metacognitive_cascade.investigation_strategy import (
    StrategySelector,
    Domain
)

# Create selector
selector = StrategySelector()

# Register custom strategy
medical_strategy = MedicalInvestigationStrategy()
selector.register_strategy(Domain.RESEARCH, medical_strategy)

# Use it
strategy = selector.get_strategy(Domain.RESEARCH)  # Returns your custom strategy
recommendations = await strategy.recommend_tools(assessment, task, context)
```

### Step 3: Use in CASCADE

```python
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

cascade = CanonicalEpistemicCascade(
    strategy_selector=selector  # Pass custom selector
)

result = await cascade.run(task, context)
```

---

## Advanced: Multiple Custom Strategies

```python
# Create multiple custom strategies
medical = MedicalInvestigationStrategy()
legal = LegalInvestigationStrategy()
financial = FinancialInvestigationStrategy()

# Initialize selector with all at once
selector = StrategySelector(custom_strategies={
    Domain.CODE_ANALYSIS: medical,      # Override built-in
    Domain.RESEARCH: legal,             # Override built-in
    Domain.COLLABORATIVE: financial     # Override built-in
})

# Or register individually
selector = StrategySelector()
selector.register_strategy(Domain.CODE_ANALYSIS, medical)
selector.register_strategy(Domain.RESEARCH, legal)
selector.register_strategy(Domain.COLLABORATIVE, financial)

# List available domains
print(selector.list_domains())
# [Domain.CODE_ANALYSIS, Domain.RESEARCH, Domain.COLLABORATIVE, ...]
```

---

## Pattern: Domain-Specific Tool Mapping

### Example: Financial Investigation

```python
class FinancialInvestigationStrategy(BaseInvestigationStrategy):
    """Investigation strategy for financial analysis"""
    
    # Map epistemic gaps to financial tools
    TOOL_MAP = {
        'know': [
            ('sec_filings_search', 0.90, 'Search SEC filings and reports'),
            ('market_data_query', 0.85, 'Query real-time market data'),
            ('financial_news_search', 0.75, 'Search financial news sources')
        ],
        'context': [
            ('company_profile', 0.90, 'Retrieve company profile and history'),
            ('industry_analysis', 0.80, 'Analyze industry trends')
        ],
        'impact': [
            ('risk_assessment', 0.95, 'Assess financial risks'),
            ('compliance_check', 0.90, 'Verify regulatory compliance')
        ]
    }
    
    async def recommend_tools(self, assessment, task, context, profile):
        recommendations = []
        gaps = assessment.get_gaps(threshold=0.85)
        
        for i, gap in enumerate(gaps):
            # Get tools for this gap type
            tools = self.TOOL_MAP.get(gap.vector, [])
            
            for tool_name, confidence, reasoning in tools:
                recommendations.append(ToolRecommendation(
                    tool_name=tool_name,
                    gap_addressed=gap.vector,
                    confidence=confidence,
                    reasoning=f"{reasoning}. Gap: {gap.rationale}",
                    priority=i
                ))
        
        return sorted(recommendations, key=lambda x: (x.priority, -x.confidence))
```

---

## Pattern: Profile-Aware Strategies

Strategies can adapt based on investigation profile:

```python
class AdaptiveStrategy(BaseInvestigationStrategy):
    """Strategy that adapts to investigation profile"""
    
    async def recommend_tools(self, assessment, task, context, profile):
        recommendations = []
        
        # Adapt based on profile
        if profile and profile.name == 'critical_domain':
            # Critical domains: More conservative, validate everything
            recommendations.extend(self._critical_tools(assessment))
        elif profile and profile.name == 'exploratory':
            # Exploratory: Suggest experimental tools
            recommendations.extend(self._exploratory_tools(assessment))
        else:
            # Balanced: Standard recommendations
            recommendations.extend(self._standard_tools(assessment))
        
        return recommendations
    
    def _critical_tools(self, assessment):
        """Tools for critical domains (medical, financial, legal)"""
        return [
            ToolRecommendation(
                tool_name='dual_validation',
                gap_addressed='know',
                confidence=1.0,
                reasoning="Validate findings with two independent sources",
                priority=0
            ),
            # ... more critical tools
        ]
```

---

## Integration with Investigation Plugins

Custom strategies work seamlessly with investigation plugins:

```python
from empirica.investigation import InvestigationPlugin

# Define custom tool plugin
jira_plugin = InvestigationPlugin(
    name='jira_search',
    description='Search JIRA for related issues',
    improves_vectors=['context', 'know'],
    confidence_gain=0.20,
    tool_type='search'
)

# Use in custom strategy
class ProjectManagementStrategy(BaseInvestigationStrategy):
    def __init__(self, plugins: list[InvestigationPlugin] = None):
        self.plugins = plugins or []
    
    async def recommend_tools(self, assessment, task, context, profile):
        recommendations = []
        
        # Include plugin-provided tools
        for plugin in self.plugins:
            for vector in plugin.improves_vectors:
                if assessment.has_gap(vector, threshold=0.85):
                    recommendations.append(ToolRecommendation(
                        tool_name=plugin.name,
                        gap_addressed=vector,
                        confidence=0.80,
                        reasoning=plugin.description,
                        priority=1
                    ))
        
        return recommendations

# Use it
strategy = ProjectManagementStrategy(plugins=[jira_plugin])
selector.register_strategy(Domain.COLLABORATIVE, strategy)
```

---

## Best Practices

### 1. Strategy Granularity

**Good:**
- MedicalInvestigationStrategy (specific domain)
- LegalInvestigationStrategy (specific domain)
- FinancialInvestigationStrategy (specific domain)

**Avoid:**
- GenericStrategy (too vague)
- AllPurposeStrategy (defeats the purpose)

### 2. Tool Recommendation Quality

**Good:**
```python
ToolRecommendation(
    tool_name='pubmed_search',
    gap_addressed='know',
    confidence=0.85,
    reasoning="Search PubMed for peer-reviewed medical literature. Gap: Limited knowledge of treatment protocols",
    priority=1
)
```

**Poor:**
```python
ToolRecommendation(
    tool_name='search',  # Too vague
    gap_addressed='know',
    confidence=0.50,  # Too uncertain
    reasoning="Search",  # No context
    priority=1
)
```

### 3. Fallback Handling

Always handle cases where tools aren't available:

```python
async def recommend_tools(self, assessment, task, context, profile):
    recommendations = []
    
    # Try domain-specific tools first
    recommendations.extend(self._domain_tools(assessment))
    
    # Fallback to general tools if none found
    if not recommendations:
        recommendations.extend(self._general_tools(assessment))
    
    return recommendations
```

---

## Testing Custom Strategies

```python
import pytest
from empirica.core.canonical import EpistemicAssessment

@pytest.mark.asyncio
async def test_custom_strategy():
    # Create test assessment with gaps
    assessment = EpistemicAssessment(
        know=VectorState(score=0.6, rationale="Limited medical knowledge"),
        impact=VectorState(score=0.7, rationale="Uncertain about side effects")
    )
    
    # Test strategy
    strategy = MedicalInvestigationStrategy()
    recommendations = await strategy.recommend_tools(
        assessment,
        task="Review treatment plan",
        context={}
    )
    
    # Verify recommendations
    assert len(recommendations) > 0
    assert any(r.tool_name == 'pubmed_search' for r in recommendations)
    assert any(r.tool_name == 'drug_interaction_check' for r in recommendations)
```

---

## Community Extensions

### Sharing Custom Strategies

**Option 1: Python Package**
```bash
# Package your strategy
# my_empirica_strategies/
#   __init__.py
#   medical.py
#   legal.py
#   financial.py

pip install my-empirica-strategies

# Use it
from my_empirica_strategies import MedicalInvestigationStrategy
```

**Option 2: Direct Integration**
```python
# Share as standalone module
# users/medical_strategy.py

from empirica.core.metacognitive_cascade.investigation_strategy import BaseInvestigationStrategy
# ... implementation
```

### Requesting Built-In Domains

If your domain is widely applicable, submit a PR to add it to the built-in `Domain` enum:

```python
class Domain(Enum):
    CODE_ANALYSIS = "code_analysis"
    RESEARCH = "research"
    COLLABORATIVE = "collaborative"
    GENERAL = "general"
    CREATIVE = "creative"
    MEDICAL = "medical"           # New
    LEGAL = "legal"               # New
    FINANCIAL = "financial"       # New
```

---

## API Reference

### BaseInvestigationStrategy

```python
class BaseInvestigationStrategy(ABC):
    @abstractmethod
    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: Dict[str, Any],
        profile: Optional[InvestigationProfile] = None
    ) -> List[ToolRecommendation]:
        """
        Recommend investigation tools based on epistemic gaps
        
        Args:
            assessment: Current epistemic assessment with gaps
            task: Task description
            context: Additional context (cwd, domain hints, etc.)
            profile: Investigation profile (optional)
            
        Returns:
            List of ToolRecommendation sorted by priority
        """
        pass
```

### StrategySelector

```python
class StrategySelector:
    def __init__(
        self,
        custom_strategies: Optional[Dict[Domain, BaseInvestigationStrategy]] = None
    ):
        """Initialize with optional custom strategies"""
    
    def register_strategy(
        self,
        domain: Domain,
        strategy: BaseInvestigationStrategy
    ) -> None:
        """Register custom strategy for domain"""
    
    def get_strategy(self, domain: Domain = Domain.GENERAL) -> BaseInvestigationStrategy:
        """Get strategy for domain (falls back to GENERAL)"""
    
    def list_domains(self) -> List[Domain]:
        """List all registered domains"""
```

### ToolRecommendation

```python
class ToolRecommendation:
    def __init__(
        self,
        tool_name: str,          # Tool identifier
        gap_addressed: str,      # Which vector this helps
        confidence: float,       # Confidence this tool helps (0.0-1.0)
        reasoning: str,          # Why this tool is recommended
        priority: int = 1        # Lower = higher priority
    ):
        pass
```

---

## Summary

**Before:**
- ❌ Hardcoded strategies
- ❌ No extension mechanism
- ❌ Limited to 5 domains

**After:**
- ✅ Fully extensible via BaseInvestigationStrategy
- ✅ Register custom strategies per domain
- ✅ Override built-in strategies
- ✅ Community-shareable extensions
- ✅ Plugin integration

**The investigation system is now truly domain-agnostic and community-extensible!** 🚀

---

**See Also:**
- `examples/custom_investigation_strategy_example.py` - Full working examples
- `empirica/investigation/investigation_plugin.py` - Plugin system
- `empirica/config/investigation_profiles.yaml` - Profile configuration
