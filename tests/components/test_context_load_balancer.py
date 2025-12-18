#!/usr/bin/env python3
"""
Tests for Context Load Balancer

Verifies rule-based routing logic:
- Uncertainty-driven depth selection
- Tag-based skill matching  
- MCO config selection heuristics
- Token budget calculations
- Deterministic output
"""

import pytest
from empirica.core.context_load_balancer import ContextLoadBalancer


class TestContextLoadBalancer:
    """Test suite for ContextLoadBalancer"""
    
    def setup_method(self):
        """Initialize balancer for each test"""
        self.balancer = ContextLoadBalancer()
    
    # ========================================================================
    # Test Uncertainty-Driven Depth Selection
    # ========================================================================
    
    def test_high_uncertainty_deep_context(self):
        """High uncertainty (>0.7) → deep context"""
        budget = self.balancer.calculate_context_budget(
            task="Investigate complex OAuth2 flow",
            epistemic_state={"uncertainty": 0.8}
        )
        
        assert budget["dynamic_context"]["depth"] == "high"
        assert budget["dynamic_context"]["total"] > 2000  # Deep context
        assert budget["dynamic_context"]["unknowns"] > 0  # Include unknowns
    
    def test_medium_uncertainty_moderate_context(self):
        """Medium uncertainty (0.5-0.7) → moderate context"""
        budget = self.balancer.calculate_context_budget(
            task="Implement known feature",
            epistemic_state={"uncertainty": 0.6}
        )
        
        assert budget["dynamic_context"]["depth"] == "medium"
        assert 1000 < budget["dynamic_context"]["total"] < 2000
        assert budget["dynamic_context"]["unknowns"] > 0
    
    def test_low_uncertainty_minimal_context(self):
        """Low uncertainty (<0.5) → minimal context"""
        budget = self.balancer.calculate_context_budget(
            task="Fix simple typo",
            epistemic_state={"uncertainty": 0.3}
        )
        
        assert budget["dynamic_context"]["depth"] == "low"
        assert budget["dynamic_context"]["total"] < 500  # Minimal
        assert budget["dynamic_context"]["unknowns"] == 0  # Skip unknowns
        assert budget["dynamic_context"]["skills"] == 0   # Trust baseline
    
    # ========================================================================
    # Test Tag-Based Skill Matching
    # ========================================================================
    
    def test_astro_skill_matching(self):
        """Task mentions 'astro' → inject astro-web-dev skill"""
        budget = self.balancer.calculate_context_budget(
            task="Build Astro website with components",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "astro-web-dev" in budget["skills_to_inject"]
    
    def test_tailwind_skill_matching(self):
        """Task mentions 'tailwind' OR 'css' → inject tailwind skill"""
        budget1 = self.balancer.calculate_context_budget(
            task="Style with Tailwind CSS",
            epistemic_state={"uncertainty": 0.5}
        )
        
        budget2 = self.balancer.calculate_context_budget(
            task="Fix CSS layout issues",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "tailwind-css-basics" in budget1["skills_to_inject"]
        assert "tailwind-css-basics" in budget2["skills_to_inject"]
    
    def test_python_skill_matching(self):
        """Task mentions 'python' → inject python skill"""
        budget = self.balancer.calculate_context_budget(
            task="Write Python script for data processing",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "python-basics" in budget["skills_to_inject"]
    
    def test_security_skill_matching(self):
        """Task mentions 'security' OR 'auth' → inject security skill"""
        budget1 = self.balancer.calculate_context_budget(
            task="Implement security measures",
            epistemic_state={"uncertainty": 0.5}
        )
        
        budget2 = self.balancer.calculate_context_budget(
            task="Add authentication to API",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "security-best-practices" in budget1["skills_to_inject"]
        assert "security-best-practices" in budget2["skills_to_inject"]
    
    def test_empirica_skill_matching(self):
        """Task mentions 'empirica' OR 'epistemic' → inject framework skill"""
        budget1 = self.balancer.calculate_context_budget(
            task="Build Empirica session tracking",
            epistemic_state={"uncertainty": 0.5}
        )
        
        budget2 = self.balancer.calculate_context_budget(
            task="Implement epistemic assessment",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "empirica-epistemic-framework" in budget1["skills_to_inject"]
        assert "empirica-epistemic-framework" in budget2["skills_to_inject"]
    
    def test_multiple_skill_matching(self):
        """Task mentions multiple domains → inject multiple skills"""
        budget = self.balancer.calculate_context_budget(
            task="Build Astro website with Tailwind CSS and Python backend",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "astro-web-dev" in budget["skills_to_inject"]
        assert "tailwind-css-basics" in budget["skills_to_inject"]
        assert "python-basics" in budget["skills_to_inject"]
        assert len(budget["skills_to_inject"]) == 3
    
    def test_no_skill_matching(self):
        """Task mentions no known domains → no skills injected"""
        budget = self.balancer.calculate_context_budget(
            task="Write documentation for unknown framework",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert len(budget["skills_to_inject"]) == 0
    
    # ========================================================================
    # Test MCO Config Selection
    # ========================================================================
    
    def test_investigation_workload_mco(self):
        """'investigate' in task → ask_before_investigate config"""
        budget = self.balancer.calculate_context_budget(
            task="Investigate database performance issues",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "ask_before_investigate" in budget["mco_configs"]
    
    def test_high_uncertainty_mco(self):
        """uncertainty > 0.65 → ask_before_investigate + cascade_styles"""
        budget = self.balancer.calculate_context_budget(
            task="Complex refactoring task",
            epistemic_state={"uncertainty": 0.7}
        )
        
        assert "ask_before_investigate" in budget["mco_configs"]
        assert "cascade_styles" in budget["mco_configs"]
    
    def test_coordination_workload_mco(self):
        """'multi-agent' OR 'coordinate' → personas config"""
        budget1 = self.balancer.calculate_context_budget(
            task="Coordinate with multi-agent system",
            epistemic_state={"uncertainty": 0.5}
        )
        
        budget2 = self.balancer.calculate_context_budget(
            task="Coordinate team work on feature",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "personas" in budget1["mco_configs"]
        assert "personas" in budget2["mco_configs"]
    
    def test_security_workload_mco(self):
        """'security' OR 'auth' → model_profiles config"""
        budget = self.balancer.calculate_context_budget(
            task="Implement authentication security",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "model_profiles" in budget["mco_configs"]
    
    def test_goal_creation_mco(self):
        """'goal' OR 'create' → protocols config"""
        budget = self.balancer.calculate_context_budget(
            task="Create goal for project milestone",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "protocols" in budget["mco_configs"]
    
    # ========================================================================
    # Test Token Budget Calculations
    # ========================================================================
    
    def test_token_budget_structure(self):
        """Budget has correct structure with all fields"""
        budget = self.balancer.calculate_context_budget(
            task="Sample task",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert "static_core" in budget
        assert "dynamic_context" in budget
        assert "mco_configs" in budget
        assert "skills_to_inject" in budget
        assert "total_budget" in budget
        
        assert budget["static_core"] == 3000
        assert isinstance(budget["dynamic_context"], dict)
        assert isinstance(budget["mco_configs"], dict)
        assert isinstance(budget["skills_to_inject"], list)
        assert isinstance(budget["total_budget"], int)
    
    def test_total_budget_calculation(self):
        """Total budget = static + dynamic + mco"""
        budget = self.balancer.calculate_context_budget(
            task="Investigate Astro components",
            epistemic_state={"uncertainty": 0.6}
        )
        
        expected_total = (
            budget["static_core"] +
            budget["dynamic_context"]["total"] +
            budget["mco_configs"]["total"]
        )
        
        assert budget["total_budget"] == expected_total
    
    def test_budget_validation_pass(self):
        """Valid budget passes validation"""
        budget = self.balancer.calculate_context_budget(
            task="Simple task",
            epistemic_state={"uncertainty": 0.3}
        )
        
        assert self.balancer.validate_budget(budget, max_budget=10000)
    
    def test_token_estimation(self):
        """Token estimation uses words * 1.3 heuristic"""
        content = "This is a test string with ten words total here."
        estimated = self.balancer.estimate_tokens(content)
        
        words = len(content.split())
        expected = int(words * 1.3)
        
        assert estimated == expected
    
    # ========================================================================
    # Test Deterministic Output
    # ========================================================================
    
    def test_deterministic_same_input(self):
        """Same input → same output (deterministic)"""
        task = "Build Astro website"
        state = {"uncertainty": 0.6}
        
        budget1 = self.balancer.calculate_context_budget(task, state)
        budget2 = self.balancer.calculate_context_budget(task, state)
        
        assert budget1 == budget2
    
    def test_different_uncertainty_different_output(self):
        """Different uncertainty → different budgets"""
        task = "Same task description"
        
        budget_low = self.balancer.calculate_context_budget(
            task, {"uncertainty": 0.3}
        )
        budget_high = self.balancer.calculate_context_budget(
            task, {"uncertainty": 0.8}
        )
        
        assert budget_low["dynamic_context"]["depth"] == "low"
        assert budget_high["dynamic_context"]["depth"] == "high"
        assert budget_low["total_budget"] < budget_high["total_budget"]
    
    # ========================================================================
    # Test Edge Cases
    # ========================================================================
    
    def test_empty_task_string(self):
        """Empty task string → minimal skills, MCO configs"""
        budget = self.balancer.calculate_context_budget(
            task="",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert len(budget["skills_to_inject"]) == 0
        assert budget["mco_configs"]["total"] >= 0  # May have configs based on uncertainty
    
    def test_no_epistemic_state(self):
        """No epistemic state → defaults to medium uncertainty (0.5)"""
        budget = self.balancer.calculate_context_budget(
            task="Some task",
            epistemic_state=None
        )
        
        assert budget["dynamic_context"]["depth"] == "medium"
    
    def test_case_insensitive_matching(self):
        """Keyword matching is case-insensitive"""
        budget_lower = self.balancer.calculate_context_budget(
            task="build astro website",
            epistemic_state={"uncertainty": 0.5}
        )
        
        budget_upper = self.balancer.calculate_context_budget(
            task="Build ASTRO Website",
            epistemic_state={"uncertainty": 0.5}
        )
        
        assert budget_lower["skills_to_inject"] == budget_upper["skills_to_inject"]
