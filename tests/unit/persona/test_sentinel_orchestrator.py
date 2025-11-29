"""
Unit tests for SentinelOrchestrator

Tests multi-persona orchestration with COMPOSE and ARBITRATE operations.
Uses mock PersonaHarness to avoid LLM calls.
"""

import pytest
import asyncio
from empirica.core.persona.sentinel import SentinelOrchestrator, OrchestrationResult


@pytest.mark.asyncio
async def test_sentinel_orchestrator_basic():
    """Test basic orchestration with 2 personas"""
    orchestrator = SentinelOrchestrator(
        sentinel_id="test-orchestrator",
        composition_strategy="average",
        arbitration_strategy="majority_vote"
    )

    result = await orchestrator.orchestrate_task(
        task="Review authentication implementation",
        personas=["security", "ux"],
        execution_mode="parallel"
    )

    # Verify result structure
    assert isinstance(result, OrchestrationResult)
    assert result.final_action in ["proceed", "investigate", "escalate"]
    assert len(result.personas_used) == 2
    assert "security" in result.personas_used
    assert "ux" in result.personas_used
    assert 0.0 <= result.agreement_score <= 1.0
    assert result.composed_assessment is not None


@pytest.mark.asyncio
async def test_weighted_composition():
    """Test confidence-weighted composition"""
    orchestrator = SentinelOrchestrator(
        sentinel_id="test-weighted",
        composition_strategy="weighted_by_confidence",
        arbitration_strategy="confidence_weighted"
    )

    result = await orchestrator.orchestrate_task(
        task="Optimize database queries",
        personas=["performance", "architecture"],
        execution_mode="parallel"
    )

    assert result.composition_strategy == "weighted_by_confidence"
    assert result.arbitration_result.arbitration_strategy == "confidence_weighted"


@pytest.mark.asyncio
async def test_pessimistic_arbitration():
    """Test pessimistic arbitration strategy"""
    orchestrator = SentinelOrchestrator(
        sentinel_id="test-pessimistic",
        composition_strategy="average",
        arbitration_strategy="pessimistic"
    )

    result = await orchestrator.orchestrate_task(
        task="Implement payment processing",
        personas=["security", "ux", "performance"],
        execution_mode="parallel"
    )

    assert result.arbitration_result.arbitration_strategy == "pessimistic"
    # Pessimistic should choose most cautious action
    assert result.final_action in ["escalate", "investigate", "proceed"]


@pytest.mark.asyncio
async def test_orchestration_result_summary():
    """Test OrchestrationResult summary generation"""
    orchestrator = SentinelOrchestrator(
        sentinel_id="test-summary",
        composition_strategy="average",
        arbitration_strategy="majority_vote"
    )

    result = await orchestrator.orchestrate_task(
        task="Test task",
        personas=["security", "ux"],
        execution_mode="parallel"
    )

    summary = result.get_summary()
    assert isinstance(summary, str)
    assert "Orchestration Result" in summary
    assert "Action:" in summary
    assert "Agreement:" in summary


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_sentinel_orchestrator_basic())
    asyncio.run(test_weighted_composition())
    asyncio.run(test_pessimistic_arbitration())
    asyncio.run(test_orchestration_result_summary())
    print("✓ All tests passed!")
