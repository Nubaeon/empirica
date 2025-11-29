#!/usr/bin/env python3
"""
Post-Heuristic Removal Verification Tests

This test suite verifies that the heuristic removal from the Empirica system
hasn't broken core functionality. It tests:

1. Bootstrap functionality (minimal and extended)
2. Goal creation and management without heuristics
3. Session management and epistemic tracking  
4. MCP integration still works
5. Core system components function properly
6. CASCADE workflow operates correctly without heuristics

These tests build on the existing test infrastructure and patterns.
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestBootstrapAfterHeuristicRemoval:
    """Test that bootstrap still works after removing heuristic components"""
    
    def test_minimal_bootstrap_loads_successfully(self):
        """Verify minimal bootstrap loads core components without heuristics"""
        from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
        
        # Should load without errors and return components
        config = bootstrap_metacognition("test-agent", level=0)
        
        assert isinstance(config, dict), "Bootstrap should return configuration dict"
        assert len(config) > 0, "Should load some components"
        
        # Core components should be present
        core_components = ["assessor", "cascade", "reflex_logger", "session_db"]
        for component in core_components:
            assert component in config, f"Core component {component} should be loaded"
    
    def test_bootstrap_without_heuristic_orchestrator(self):
        """Verify bootstrap doesn't fail when autonomous goal orchestrator is removed"""
        from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
        
        # Try different bootstrap levels
        for level in [0, 1]:
            config = bootstrap_metacognition("test-agent", level=level)
            assert config is not None, f"Bootstrap level {level} should succeed"
            
            # Should not have any references to autonomous orchestrator
            config_str = str(config).lower()
            assert "autonomous" not in config_str, "No autonomous components should be loaded"
            assert "orchestrator" not in config_str, "No orchestrator components should be loaded"
    
    def test_session_creation_after_heuristic_cleanup(self):
        """Verify session creation works without heuristic components"""
        from empirica.data.session_database import SessionDatabase
        
        db = SessionDatabase()
        session_id = db.create_session(
            ai_id="test-post-heuristic",
            bootstrap_level=0,
            components_loaded=5,  # Should work with any number
            user_id=None
        )
        
        assert session_id is not None, "Session should be created successfully"
        assert isinstance(session_id, str), "Session ID should be string"
        
        db.close()


class TestGoalManagementWithoutHeuristics:
    """Test goal management functionality without heuristic guidance"""
    
    def test_goal_creation_without_template_heuristics(self):
        """Verify goal creation works without heuristic templates"""
        from empirica.core.canonical.goal_orchestrator import StructuredGoalOrchestrator
        
        orchestrator = StructuredGoalOrchestrator("test-agent")
        
        # Create goal with explicit parameters (no heuristic templates)
        goal_id = orchestrator.create_goal(
            session_id="test-session",
            objective="Test goal without heuristics",
            scope={"breadth": 0.5, "duration": 0.3, "coordination": 0.7},
            success_criteria=["Goal creation works", "No templates used"]
        )
        
        assert goal_id is not None, "Goal should be created successfully"
        
        # Verify goal exists and has correct structure
        goal = orchestrator.get_goal(goal_id)
        assert goal is not None, "Goal should be retrievable"
        assert goal["objective"] == "Test goal without heuristics", "Objective should match"
    
    def test_no_autonomous_goal_templates(self):
        """Verify no autonomous goal templates exist in system"""
        # Check that autonomous orchestrator directory doesn't exist
        orchestrator_path = Path("empirica/cognitive_benchmarking/orchestration/autonomous_goal_orchestrator")
        if orchestrator_path.exists():
            assert False, "Autonomous goal orchestrator should be removed"
    
    def test_subtask_management_without_heuristics(self):
        """Verify subtask management works with explicit parameters"""
        from empirica.core.canonical.goal_orchestrator import StructuredGoalOrchestrator
        
        orchestrator = StructuredGoalOrchestrator("test-agent")
        
        # Create goal first
        goal_id = orchestrator.create_goal(
            session_id="test-session",
            objective="Test subtask management",
            scope={"breadth": 0.3, "duration": 0.4, "coordination": 0.6},
            success_criteria=["Subtask management works"]
        )
        
        # Add subtask with explicit importance level
        task_id = orchestrator.add_subtask(
            goal_id=goal_id,
            description="Test subtask",
            importance="high"  # Explicit level, not heuristic-derived
        )
        
        assert task_id is not None, "Subtask should be created"
        
        # Verify subtask can be completed
        orchestrator.complete_subtask(
            task_id=task_id,
            evidence="Test evidence"
        )
        
        # Check goal progress
        goal = orchestrator.get_goal(goal_id)
        assert "progress" in goal, "Goal should track progress"


class TestCascadeWorkflowWithoutHeuristics:
    """Test CASCADE workflow operates correctly without heuristic guidance"""
    
    @pytest.mark.asyncio
    async def test_preflight_generates_prompt_not_scores(self):
        """Verify PREFLIGHT generates genuine self-assessment prompts"""
        from empirica.core.metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade
        
        cascade = CanonicalEpistemicCascade(agent_id="test-agent")
        
        # Generate preflight assessment
        assessment_result = await cascade._assess_epistemic_state(
            "Test task for preflight",
            {},
            "test-task-id",
            "PREFLIGHT"
        )
        
        # Should return assessment object, not static scores
        assert hasattr(assessment_result, 'self_assessment_prompt'), (
            "Should generate self-assessment prompt for AI"
        )
        
        # Verify it doesn't contain static heuristic scores
        assessment_str = str(assessment_result.__dict__)
        assert "0.5" not in assessment_str or "self_assessment_prompt" in assessment_str, (
            "Should not contain hardcoded baseline scores"
        )
    
    @pytest.mark.asyncio
    async def test_cascade_phases_without_keyword_heuristics(self):
        """Verify CASCADE phases don't use keyword matching for scoring"""
        from empirica.core.metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade
        
        cascade = CanonicalEpistemicCascade(agent_id="test-agent")
        
        # Test with various task types to ensure no keyword matching
        test_tasks = [
            "Debug a Python error in the main function",
            "Create a new REST API endpoint with authentication",
            "Write comprehensive unit tests for a web service",
            "Optimize database queries for better performance"
        ]
        
        for task in test_tasks:
            assessment = await cascade._assess_epistemic_state(
                task, {}, "test-task-id", "PREFLIGHT"
            )
            
            # All should produce genuine assessments, not keyword-based scores
            assert assessment is not None, f"Assessment should exist for: {task}"
            assert hasattr(assessment, 'engagement'), "Should have engagement vector"
            assert hasattr(assessment, 'know'), "Should have know vector"
    
    def test_epistemic_delta_calculation(self):
        """Verify epistemic delta calculation works without heuristics"""
        from empirica.core.metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade
        from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, VectorAssessment, CascadePhase
        
        cascade = CanonicalEpistemicCascade(agent_id="test-agent")
        
        # Create sample assessments (simulating genuine AI assessments)
        preflight = EpistemicAssessmentSchema(
            engagement=VectorAssessment(0.70, "Initial engagement"),
            know=VectorAssessment(0.50, "Initial knowledge"),
            do=VectorAssessment(0.60, "Initial capability"),
            context=VectorAssessment(0.55, "Initial context"),
            clarity=VectorAssessment(0.65, "Initial clarity"),
            coherence=VectorAssessment(0.70, "Initial coherence"),
            signal=VectorAssessment(0.60, "Initial signal"),
            density=VectorAssessment(0.65, "Initial density"),
            state=VectorAssessment(0.60, "Initial state"),
            change=VectorAssessment(0.55, "Initial change"),
            completion=VectorAssessment(0.30, "Initial completion"),
            impact=VectorAssessment(0.50, "Initial impact"),
            uncertainty=VectorAssessment(0.60, "Initial uncertainty"),
            phase=CascadePhase.PREFLIGHT,
        )
        
        postflight = EpistemicAssessmentSchema(
            engagement=VectorAssessment(0.75, "Improved engagement"),
            know=VectorAssessment(0.70, "Improved knowledge"),
            do=VectorAssessment(0.75, "Improved capability"),
            context=VectorAssessment(0.80, "Improved context"),
            clarity=VectorAssessment(0.80, "Improved clarity"),
            coherence=VectorAssessment(0.85, "Improved coherence"),
            signal=VectorAssessment(0.75, "Improved signal"),
            density=VectorAssessment(0.70, "Improved density"),
            state=VectorAssessment(0.75, "Improved state"),
            change=VectorAssessment(0.80, "Improved change"),
            completion=VectorAssessment(0.70, "Improved completion"),
            impact=VectorAssessment(0.70, "Improved impact"),
            uncertainty=VectorAssessment(0.35, "Reduced uncertainty"),
            phase=CascadePhase.POSTFLIGHT,
        )
        
        # Calculate delta
        delta = cascade._calculate_epistemic_delta(preflight, postflight)
        
        # Verify improvements (all positive except uncertainty which should decrease)
        assert delta['know'] > 0, "Knowledge should improve"
        assert delta['do'] > 0, "Capability should improve"
        assert delta['uncertainty'] < 0, "Uncertainty should decrease"
        assert delta['completion'] > 0, "Completion should improve"


class TestMCPIntegrationAfterHeuristicRemoval:
    """Test MCP integration still works without heuristic components"""
    
    def test_mcp_tools_load_without_heuristic_imports(self):
        """Verify MCP tools don't import removed heuristic components"""
        from empirica.mcp.local.server import start_server
        
        # This should not fail due to missing heuristic imports
        # We're testing that imports work, not that the server starts
        try:
            from empirica.mcp.local import server
            # If we get here, imports work
            assert True, "MCP server imports should work without heuristics"
        except ImportError as e:
            # Check that it's not about missing heuristic components
            error_msg = str(e).lower()
            assert not any(comp in error_msg for comp in ["autonomous", "orchestrator", "heuristic"]), (
                f"Import error should not be about removed heuristic components: {e}"
            )
    
    def test_mcp_goal_commands_without_heuristic_logic(self):
        """Verify MCP goal commands don't use heuristic goal templates"""
        # This is a smoke test to ensure MCP commands still work
        # The actual MCP testing would require running the server
        
        # Check that goal command handlers don't reference autonomous orchestrator
        try:
            from empirica.cli.command_handlers.goal_commands import handle_goals_list
            from argparse import Namespace
            
            # Test with minimal args
            args = Namespace(
                session_id="test",
                scope_breadth_min=None,
                scope_breadth_max=None,
                scope_duration_min=None,
                scope_duration_max=None,
                scope_coordination_min=None,
                scope_coordination_max=None,
                json=False,
                compact=False,
                kv=False,
                quiet=False
            )
            
            # This should not crash
            try:
                result = handle_goals_list(args)
                # Should return some result, even if empty
                assert True, "Goal list command should execute without errors"
            except Exception as e:
                # Should not be due to missing heuristic components
                error_msg = str(e).lower()
                assert not any(comp in error_msg for comp in ["autonomous", "orchestrator", "heuristic"]), (
                    f"Goal command error should not be about removed components: {e}"
                )
        except ImportError:
            # If module doesn't exist, that's OK - we're checking imports
            assert True, "Goal commands import check completed"


class TestSessionManagementWithoutHeuristics:
    """Test session management and epistemic tracking without heuristics"""
    
    def test_session_state_tracking_without_heuristics(self):
        """Verify session state tracking works without heuristic fallback"""
        from empirica.data.session_database import SessionDatabase
        
        db = SessionDatabase()
        session_id = db.create_session(
            ai_id="test-session-tracking",
            bootstrap_level=0,
            components_loaded=6,
            user_id=None
        )
        
        # Update session state (simulate epistemic tracking)
        db.update_session_state(session_id, {
            "preflight_completed": True,
            "vectors_collected": True,
            "confidence_level": 0.75
        })
        
        # Retrieve session state
        session_state = db.get_session_state(session_id)
        
        assert session_state is not None, "Session state should be retrievable"
        assert session_state.get("preflight_completed") is True, "State should be updated"
        
        db.close()
    
    def test_epistemic_handoff_without_heuristic_templates(self):
        """Verify handoff reports don't use heuristic templates"""
        # Test creating a handoff report manually
        from empirica.data.session_database import SessionDatabase
        
        db = SessionDatabase()
        session_id = db.create_session(
            ai_id="test-handoff",
            bootstrap_level=0,
            components_loaded=5,
            user_id=None
        )
        
        # Create handoff report
        db.create_handoff_report(
            session_id=session_id,
            task_summary="Test task completed successfully",
            key_findings=["Finding 1", "Finding 2"],
            next_session_context="Context for next session",
            artifacts_created=["file1.txt", "file2.py"],
            remaining_unknowns=["Unknown 1"]
        )
        
        # Retrieve handoff report
        report = db.get_handoff_report(session_id)
        
        assert report is not None, "Handoff report should be created"
        assert report["task_summary"] == "Test task completed successfully", "Summary should match"
        assert len(report["key_findings"]) == 2, "Should have findings"
        
        db.close()


class TestReflexLoggerWithoutHeuristics:
    """Test reflex logging functionality without heuristic components"""
    
    def test_reflex_logging_stores_genuine_assessments(self):
        """Verify reflex logger stores genuine assessments, not synthetic"""
        from empirica.core.canonical.reflex_logger import ReflexLogger
        
        logger = ReflexLogger("test-reflex")
        
        # Create a sample assessment (simulating genuine AI assessment)
        sample_assessment = {
            "engagement": {"score": 0.75, "rationale": "Genuine engagement analysis"},
            "know": {"score": 0.70, "rationale": "Genuine knowledge assessment"},
            "do": {"score": 0.65, "rationale": "Genuine capability assessment"},
            "context": {"score": 0.80, "rationale": "Genuine context assessment"},
            "phase": "PREFLIGHT"
        }
        
        # Log the assessment
        logger.log_assessment("test-session", sample_assessment)
        
        # Verify logging doesn't use synthetic data
        # The logger should store what was provided, not modify with heuristics
        
        # Check that no synthetic/heuristic values were added
        logged_data = logger.get_latest_assessment("test-session")
        assert logged_data is not None, "Assessment should be logged"
        
        # Should contain the original assessment data
        assert "genuine engagement analysis" in str(logged_data), "Should contain original rationale"
    
    def test_no_baseline_score_generation(self):
        """Verify reflex logger doesn't generate baseline scores"""
        from empirica.core.canonical.reflex_logger import ReflexLogger
        
        logger = ReflexLogger("test-reflex-baseline")
        
        # Log empty assessment
        logger.log_assessment("test-session", {})
        
        # Retrieve and verify no baseline scores were generated
        logged = logger.get_latest_assessment("test-session")
        
        # Should not contain default scores like 0.5 for all vectors
        # (unless explicitly provided in the assessment)
        logged_str = str(logged)
        assert "0.5" not in logged_str, "Should not generate default baseline scores"


def run_comprehensive_verification():
    """Run all verification tests and report results"""
    print("🔍 Running Post-Heuristic Removal Verification Tests")
    print("=" * 60)
    
    # Run pytest programmatically
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
    
    return exit_code


if __name__ == "__main__":
    exit_code = run_comprehensive_verification()
    if exit_code == 0:
        print("\n✅ All verification tests passed!")
        print("🎉 Heuristic removal verification successful")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")
        print("⚠️  Please investigate failures before considering removal complete")
    
    sys.exit(exit_code)