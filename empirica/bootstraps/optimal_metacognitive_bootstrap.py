#!/usr/bin/env python3
"""
🚀🧠✨ Optimal Metacognitive Bootstrap
Bootstrap for epistemic humility and empirical feedback

This bootstrap loads the core metacognitive components in optimal order:
1. 13-vector metacognition (11 foundation + ENGAGEMENT + UNCERTAINTY)
2. Adaptive uncertainty calibration (empirical learning from feedback)
3. Autonomous goal orchestrator (context-aware action planning)

NOTE: The Enhanced Cascade Workflow (PREFLIGHT → Think → Plan → Investigate → 
Check → Act → POSTFLIGHT) is built into the metacognitive cascade itself.
No separate workflow loading is needed.

Design Philosophy:
- Epistemic humility through uncertainty quantification
- Empirical grounding through feedback loops
- Collaborative intelligence through ENGAGEMENT dimension
- Fast startup (<0.03s for minimal)
- AI self-assessment (not meta-prompts)

Version: 1.0.1 - Fixed LLM mode detection
"""

import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Fix sys.path: Ensure empirica paths come BEFORE semantic_self_aware_kit
empirica_root = Path(__file__).parent.parent.parent  # /home/yogapad/empirical-ai/empirica
empirica_paths = [
    str(empirica_root / 'empirica' / 'core'),
    str(empirica_root / 'empirica'),
    str(empirica_root),
    str(Path(__file__).parent)  # bootstraps directory
]

# Insert at position 0 (highest priority) in order
for path in reversed(empirica_paths):
    if path not in sys.path:
        sys.path.insert(0, path)

# Import auto-tracker for session tracking
try:
    from empirica.auto_tracker import EmpericaTracker
    AUTO_TRACKER_AVAILABLE = True
except ImportError:
    AUTO_TRACKER_AVAILABLE = False

class OptimalMetacognitiveBootstrap:
    """
    Optimal bootstrap for metacognitive components
    
    Bootstrap Levels (supports both numeric and named):
    - 0 / minimal: Core metacognition (13-vector + calibration + goals) ~0.03s
    - 1 / standard: Level 0 + standard workflow components
    - 2 / full: Includes lazy-loaded components (context builder, evaluator, collaboration)
    
    Note: Enhanced Cascade Workflow is built into the metacognitive cascade.
    """
    
    def _normalize_level(self, level) -> str:
        """Normalize level input to string format, supporting both numeric and named"""
        # Convert to string if numeric
        level_str = str(level)
        
        # Map numeric to named levels
        numeric_to_named = {
            "0": "minimal",
            "1": "standard", 
            "2": "full"
        }
        
        # Map named to canonical names
        named_to_canonical = {
            "minimal": "minimal",
            "standard": "standard",
            "full": "full",
            "complete": "full"  # Alias
        }
        
        # First try numeric mapping
        if level_str in numeric_to_named:
            return numeric_to_named[level_str]
        
        # Then try named mapping
        if level_str in named_to_canonical:
            return named_to_canonical[level_str]
        
        # Default to standard
        print(f"⚠️  Unknown level '{level}', defaulting to 'standard'")
        return "standard"
    
    def _level_to_int(self, level: str) -> int:
        """Convert level string to bootstrap level int"""
        level_map = {"minimal": 0, "standard": 1, "full": 2}
        return level_map.get(level, 1)
    
    def __init__(self, ai_id: str = "empirica_ai", level: str = "standard"):
        self.ai_id = ai_id
        # Normalize level to handle both numeric and named inputs
        self.level = self._normalize_level(level)
        self.components = {}
        self.bootstrap_start_time = time.time()
        
        # Initialize auto-tracker
        self.tracker = None
        if AUTO_TRACKER_AVAILABLE:
            self.tracker = EmpericaTracker.get_instance(
                ai_id=ai_id,
                bootstrap_level=self._level_to_int(self.level)
            )
        
        print(f"🚀🧠✨ Optimal Metacognitive Bootstrap")
        print(f"   🤖 AI ID: {self.ai_id}")
        print(f"   📊 Level: {self.level} (normalized)")
        print(f"   🎯 Focus: Epistemic humility + Empirical feedback")
        if AUTO_TRACKER_AVAILABLE:
            print(f"   📈 Auto-tracking: ENABLED")
        print()
    
    def bootstrap(self) -> Dict[str, Any]:
        """Run bootstrap based on selected level"""
        if self.level == "minimal":
            return self.bootstrap_minimal()
        elif self.level == "standard":
            return self.bootstrap_standard()
        elif self.level == "full":
            return self.bootstrap_full()
        else:
            print(f"⚠️ Unknown level '{self.level}', using standard")
            return self.bootstrap_standard()
    
    def bootstrap_minimal(self) -> Dict[str, Any]:
        """
        Minimal bootstrap - Core metacognition only
        Fast startup for production use (~0.03s)
        """
        print("🧠 PHASE 1: Foundation (minimal)")
        print("=" * 50)
        
        # 1. Load 13-vector metacognition (FOUNDATION)
        print("1️⃣ Loading 13-vector metacognition...")
        from core.metacognition_12d_monitor import (
            ComprehensiveSelfAwarenessAssessment,
            TwelveVectorSelfAwarenessMonitor,
            EngagementDimension,
            render_11_vector_state
        )
        
        self.components['twelve_vector_monitor'] = TwelveVectorSelfAwarenessMonitor(self.ai_id)
        self.components['eleven_vector_assessment'] = ComprehensiveSelfAwarenessAssessment(self.ai_id)
        self.components['render_vectors'] = render_11_vector_state
        
        print("   ✅ 13-vector system loaded (11 foundation + ENGAGEMENT + UNCERTAINTY)")
        print(f"   📊 Total: 13 epistemic vectors")
        
        # 2. Load adaptive uncertainty calibration (EMPIRICAL LEARNING)
        print("\n2️⃣ Loading adaptive uncertainty calibration...")
        from calibration.adaptive_uncertainty_calibration import (
            AdaptiveUncertaintyCalibration,
            UQVector,
            CalibrationResult
        )
        
        self.components['calibration'] = AdaptiveUncertaintyCalibration(self.ai_id)
        self.components['uq_vector'] = UQVector
        
        print("   ✅ Calibration system loaded (KNOW-DO-CONTEXT)")
        print("   🔄 Empirical feedback loop: ACTIVE")
        
        # 3. Load canonical goal orchestrator (LLM-POWERED, NO HEURISTICS)
        print("\n3️⃣ Loading canonical goal orchestrator...")
        try:
            from core.canonical.canonical_goal_orchestrator import (
                CanonicalGoalOrchestrator,
                create_goal_orchestrator
            )
            
            self.components['canonical_goal_orchestrator'] = create_goal_orchestrator(use_placeholder=True)
            # Legacy aliases for backward compatibility
            self.components['orchestrate'] = self.components['canonical_goal_orchestrator'].orchestrate_goals
            self.components['goal_orchestrator'] = self.components['canonical_goal_orchestrator']
            
            print("   ✅ Canonical goal orchestrator loaded (LLM-powered, no heuristics)")
            print("   🎯 ENGAGEMENT-driven autonomy: ACTIVE")
        except Exception as e:
            print(f"   ⚠️ Canonical goal orchestrator failed: {e}")
            print("   ⚠️ Falling back to legacy goal orchestrator (heuristic-based)")
            
            from goal_management.autonomous_goal_orchestrator import (
                DynamicContextAnalyzer,
                create_dynamic_goals,
                enhanced_orchestrate_with_context
            )
            
            self.components['context_analyzer'] = DynamicContextAnalyzer()
            self.components['create_goals'] = create_dynamic_goals
            self.components['orchestrate'] = enhanced_orchestrate_with_context
            
            print("   ✅ Legacy goal orchestrator loaded (context-aware, heuristic-based)")
            print("   🎯 Dynamic goal generation: ACTIVE")
        
        # 4. Note: Cascade workflow is built into the metacognitive cascade
        # The 7-phase workflow (PREFLIGHT → Think → Plan → Investigate → Check → Act → POSTFLIGHT)
        # is integrated into empirica/core/metacognitive_cascade/ - no separate loading needed
        print("\n✨ Bootstrap complete!")
        print("   ℹ️  Enhanced Cascade Workflow integrated into metacognitive cascade")
        print("   📊 Ready for epistemic self-assessment")
        
        # Add auto-tracker to components and start session
        if self.tracker:
            self.components['tracker'] = self.tracker
            self.tracker.start_session(components_loaded=len(self.components))
        
        self._print_bootstrap_summary()
        return self.components
    
    def bootstrap_standard(self) -> Dict[str, Any]:
        """
        Standard bootstrap - Core + workflow components
        Balanced between speed and functionality (~0.04s)
        """
        # Load minimal first
        self.bootstrap_minimal()
        
        print("\n🧠 PHASE 2: Workflow Components (standard)")
        print("=" * 50)
        
        # Load canonical cascade (includes Enhanced Cascade Workflow)
        print("1️⃣ Loading canonical epistemic cascade...")
        try:
            from core.metacognitive_cascade import CanonicalEpistemicCascade
            self.components['canonical_cascade'] = CanonicalEpistemicCascade()
            print("   ✅ Canonical cascade loaded (7-phase workflow integrated)")
            print("   📊 Workflow: PREFLIGHT → Think → Plan → Investigate → Check → Act → POSTFLIGHT")
        except Exception as e:
            print(f"   ⚠️ Canonical cascade failed: {e}")
        
        self._print_bootstrap_summary()
        return self.components
    
    def bootstrap_full(self) -> Dict[str, Any]:
        """
        Full bootstrap - Includes lazy components
        Complete capabilities for deep work (~0.05s + lazy loading)
        """
        # Load minimal first
        self.bootstrap_minimal()
        
        print("\n🧠 PHASE 3: Lazy Components (full)")
        print("=" * 50)
        print("Note: These load on-demand when needed")
        
        # Mark components as available for lazy loading
        self.components['lazy_components'] = {
            'context_builder': {
                'module': 'context_builder',
                'class': 'ContextBuilder',
                'cost': '~2-5s (file scanning)',
                'use': 'Deep STATE/COMPLETION assessment'
            },
            'meta_cognitive_evaluator': {
                'module': 'meta_cognitive_evaluator',
                'class': 'MetaCognitiveEvaluator',
                'cost': '~0.5-2s (recursive setup)',
                'use': 'Evaluation quality analysis'
            },
            'collaboration_framework': {
                'module': 'collaboration_framework',
                'class': 'CollaborationManager',
                'cost': '~0.02s (protocol init)',
                'use': 'Multi-AI coordination'
            }
        }
        
        print("   📦 Lazy components registered:")
        for name, info in self.components['lazy_components'].items():
            print(f"      • {name}: {info['use']} ({info['cost']})")
        
        self._print_bootstrap_summary()
        return self.components
    
    def load_context_builder(self):
        """Lazy load context builder for deep assessment"""
        if 'context_builder' not in self.components:
            print("🔍 Loading context builder...")
            from context_builder import ContextBuilder
            self.components['context_builder'] = ContextBuilder()
            print("   ✅ Context builder loaded (workspace scanning active)")
        return self.components['context_builder']
    
    def load_meta_evaluator(self):
        """Lazy load meta-cognitive evaluator for evaluation quality"""
        if 'meta_evaluator' not in self.components:
            print("🔬 Loading meta-cognitive evaluator...")
            from meta_cognitive_evaluator import MetaCognitiveEvaluator
            self.components['meta_evaluator'] = MetaCognitiveEvaluator()
            print("   ✅ Meta-evaluator loaded (recursive evaluation active)")
        return self.components['meta_evaluator']
    
    def load_collaboration(self):
        """Lazy load collaboration framework for multi-AI scenarios"""
        if 'collaboration' not in self.components:
            print("🤝 Loading collaboration framework...")
            from collaboration_framework import default_collaboration_manager
            self.components['collaboration'] = default_collaboration_manager
            print("   ✅ Collaboration loaded (multi-AI coordination active)")
        return self.components['collaboration']
    
    def _print_bootstrap_summary(self):
        """Print bootstrap summary"""
        elapsed = time.time() - self.bootstrap_start_time
        loaded_count = len([k for k in self.components.keys() if k != 'lazy_components'])
        
        print(f"\n📊 BOOTSTRAP SUMMARY")
        print("=" * 50)
        print(f"   🚀 Components loaded: {loaded_count}")
        print(f"   ⏱️ Bootstrap time: {elapsed:.3f}s")
        print(f"   💡 Level: {self.level}")
        
        if self.level == "minimal":
            print(f"   ✨ Core metacognition ready!")
        elif self.level == "standard":
            print(f"   ✨ Full metacognitive workflow ready!")
        elif self.level == "full":
            print(f"   ✨ Complete system ready (with lazy loading)!")
        
        # Print workflow guidance if cascade orchestrator loaded
        if 'cascade_orchestrator' in self.components:
            print()
            print("🔄 ENHANCED CASCADE WORKFLOW AVAILABLE")
            print("=" * 50)
            print("  Use: orchestrator.start_workflow(session_id, user_prompt)")
            print("  Phases: PREFLIGHT → Think → Plan → Investigate → Check → Act → POSTFLIGHT")
            print("  Track: 13 epistemic vectors measured at each phase")
            print("  Loop: Check phase enables recalibration before acting")
        
        print()
    
    def get_assessment(self, task: str, context: Dict[str, Any] = None, 
                       goals: List[str] = None) -> Any:
        """
        Convenience method to get 13-vector assessment with REAL uncertainty calculations
        
        Args:
            task: Task description
            context: Context dictionary
            goals: List of goals
            
        Returns:
            SelfAwarenessResult with real calculated uncertainty values
        """
        if 'eleven_vector_assessment' not in self.components:
            raise RuntimeError("Bootstrap minimal or higher first")
        
        # Use ComprehensiveSelfAwarenessAssessment for REAL uncertainty calculations
        # Not the simple TwelveVectorSelfAwarenessMonitor with hardcoded defaults
        return self.components['eleven_vector_assessment'].assess(
            task, context or {}
        )
    
    def run_cascade(self, task: str, context: Dict[str, Any] = None):
        """
        Convenience method to run metacognitive cascade
        
        Args:
            task: Decision to analyze
            context: Context dictionary
            
        Returns:
            CascadeResult
        """
        if 'cascade' not in self.components:
            raise RuntimeError("Bootstrap standard or higher first")
        
        return self.components['cascade'].run_full_cascade(task, context)
    
    def provide_feedback(self, calibration_id: str, outcome: Dict[str, Any]):
        """
        Provide feedback to calibration system for learning
        
        Args:
            calibration_id: ID from calibration result
            outcome: Feedback dict with accuracy, task_success, etc.
        """
        if 'calibration' not in self.components:
            raise RuntimeError("Bootstrap minimal or higher first")
        
        from calibration.adaptive_uncertainty_calibration.adaptive_uncertainty_calibration import FeedbackOutcome
        
        feedback = FeedbackOutcome(
            accuracy=outcome.get('accuracy', 0.5),
            task_success=outcome.get('task_success', True),
            human_correction=outcome.get('human_correction', False),
            execution_quality=outcome.get('execution_quality', 0.5),
            semantic_notes=outcome.get('notes')
        )
        
        self.components['calibration'].provide_feedback(calibration_id, feedback)
        print(f"✅ Feedback provided for {calibration_id}")


# Convenience function for quick bootstrap
def bootstrap_metacognition(ai_id: str = "empirica_ai", level: str = "standard") -> Dict[str, Any]:
    """
    Quick bootstrap function
    
    Args:
        ai_id: AI identifier
        level: Bootstrap level (minimal, standard, full)
        
    Returns:
        Dictionary of loaded components
    """
    bootstrap = OptimalMetacognitiveBootstrap(ai_id, level)
    return bootstrap.bootstrap()


# Main execution for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimal Metacognitive Bootstrap")
    parser.add_argument('--level', default='minimal', 
                       choices=['minimal', 'full'],
                       help='Bootstrap level')
    parser.add_argument('--ai-id', default='test_ai',
                       help='AI identifier')
    args = parser.parse_args()
    
    print("🧪 Testing Optimal Metacognitive Bootstrap")
    print()
    
    # Bootstrap
    bootstrap = OptimalMetacognitiveBootstrap(args.ai_id, args.level)
    components = bootstrap.bootstrap()
    
    # Test assessment
    print("\n🧪 Testing 13-vector assessment...")
    assessment = bootstrap.get_assessment(
        task="Test the optimal metacognitive bootstrap",
        context={"test": True},
        goals=["Verify bootstrap works", "Test all components"]
    )
    print(f"   Assessment type: {type(assessment).__name__}")
    print(f"   ✅ Assessment successful!")
    
    print("\n✅ All tests passed! Bootstrap operational!")
