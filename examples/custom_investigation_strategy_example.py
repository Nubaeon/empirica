#!/usr/bin/env python3
"""
Example: Custom Investigation Strategy

Shows how to extend Empirica's investigation system with custom strategies
for specialized domains (e.g., medical, legal, financial).
"""

from empirica.core.metacognitive_cascade.investigation_strategy import (
    BaseInvestigationStrategy,
    StrategySelector,
    Domain,
    ToolRecommendation
)
from empirica.core.canonical import EpistemicAssessment
from typing import List, Dict, Any, Optional


class MedicalInvestigationStrategy(BaseInvestigationStrategy):
    """
    Custom investigation strategy for medical/healthcare domain
    
    Focuses on:
    - Evidence-based research (medical literature)
    - Clinical guidelines verification
    - Safety and compliance checks
    - Drug interaction analysis
    """
    
    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: Dict[str, Any],
        profile: Optional['InvestigationProfile'] = None
    ) -> List[ToolRecommendation]:
        """Recommend medical-specific investigation tools"""
        
        recommendations = []
        gaps = assessment.get_gaps(threshold=0.85)
        
        for i, gap in enumerate(gaps):
            # Medical-specific tool recommendations
            if gap.vector == 'know':
                recommendations.append(ToolRecommendation(
                    tool_name='pubmed_search',
                    gap_addressed='know',
                    confidence=0.85,
                    reasoning=f"Search PubMed for evidence-based medical literature. {gap.rationale}",
                    priority=i
                ))
                recommendations.append(ToolRecommendation(
                    tool_name='clinical_guidelines_check',
                    gap_addressed='know',
                    confidence=0.80,
                    reasoning="Verify against current clinical practice guidelines",
                    priority=i
                ))
            
            elif gap.vector == 'context':
                recommendations.append(ToolRecommendation(
                    tool_name='patient_history_review',
                    gap_addressed='context',
                    confidence=0.90,
                    reasoning="Review patient medical history for relevant context",
                    priority=i
                ))
            
            elif gap.vector == 'impact':
                recommendations.append(ToolRecommendation(
                    tool_name='drug_interaction_check',
                    gap_addressed='impact',
                    confidence=0.95,
                    reasoning="Check for potential drug interactions and contraindications",
                    priority=i
                ))
                recommendations.append(ToolRecommendation(
                    tool_name='safety_protocol_verify',
                    gap_addressed='impact',
                    confidence=0.85,
                    reasoning="Verify compliance with safety protocols",
                    priority=i
                ))
        
        return sorted(recommendations, key=lambda x: (x.priority, -x.confidence))


class LegalInvestigationStrategy(BaseInvestigationStrategy):
    """
    Custom investigation strategy for legal domain
    
    Focuses on:
    - Case law research
    - Statutory analysis
    - Precedent verification
    - Jurisdiction compliance
    """
    
    async def recommend_tools(
        self,
        assessment: EpistemicAssessment,
        task: str,
        context: Dict[str, Any],
        profile: Optional['InvestigationProfile'] = None
    ) -> List[ToolRecommendation]:
        """Recommend legal-specific investigation tools"""
        
        recommendations = []
        gaps = assessment.get_gaps(threshold=0.85)
        
        for i, gap in enumerate(gaps):
            if gap.vector == 'know':
                recommendations.append(ToolRecommendation(
                    tool_name='case_law_search',
                    gap_addressed='know',
                    confidence=0.90,
                    reasoning=f"Search case law for relevant precedents. {gap.rationale}",
                    priority=i
                ))
                recommendations.append(ToolRecommendation(
                    tool_name='statute_analysis',
                    gap_addressed='know',
                    confidence=0.85,
                    reasoning="Analyze applicable statutes and regulations",
                    priority=i
                ))
            
            elif gap.vector == 'context':
                recommendations.append(ToolRecommendation(
                    tool_name='jurisdiction_check',
                    gap_addressed='context',
                    confidence=0.90,
                    reasoning="Verify jurisdiction and applicable law",
                    priority=i
                ))
        
        return sorted(recommendations, key=lambda x: (x.priority, -x.confidence))


# EXAMPLE USAGE

async def example_custom_strategy():
    """Example: Using custom investigation strategies"""
    
    print("=" * 60)
    print("CUSTOM INVESTIGATION STRATEGY EXAMPLE")
    print("=" * 60)
    
    # Create strategy selector with custom strategies
    selector = StrategySelector()
    
    # Register medical strategy (using CODE_ANALYSIS as placeholder for custom domain)
    medical_strategy = MedicalInvestigationStrategy()
    selector.register_strategy(Domain.CODE_ANALYSIS, medical_strategy)
    
    print("\n✅ Registered custom medical investigation strategy")
    
    # Register legal strategy
    legal_strategy = LegalInvestigationStrategy()
    # Would need to add Domain.LEGAL to enum, or use existing domain
    
    print("✅ Registered custom legal investigation strategy")
    
    # List available domains
    print(f"\n📋 Available domains: {selector.list_domains()}")
    
    # Use custom strategy
    strategy = selector.get_strategy(Domain.CODE_ANALYSIS)  # Now returns medical strategy
    print(f"\n🔍 Selected strategy: {type(strategy).__name__}")
    
    print("\n" + "=" * 60)
    print("Custom strategies enable domain-specific investigation!")
    print("=" * 60)


if __name__ == '__main__':
    import asyncio
    asyncio.run(example_custom_strategy())
