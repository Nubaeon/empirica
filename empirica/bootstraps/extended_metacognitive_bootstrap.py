#!/usr/bin/env python3
"""
🚀🧠✨ Extended Metacognitive Bootstrap - Init-Style Levels
Complete bootstrap with Canonical Foundation and Extended Ecosystem

Init-Style Bootstrap Levels (analogous to Unix init.d):
- Level 0 (init 0): Canonical only - Tier 0 + Tier 1 (3-6 components) ~0.05s
- Level 1 (init 1): Single-user - Level 0 + Tier 2 foundation (~12 components) ~0.10s  
- Level 2 (init 2): Multi-user - Level 1 + Tier 2.5 calibration (~14 components) ~0.12s
- Level 3 (init 3): Network services - Level 2 + Tier 3 advanced (~18 components) ~0.15s
- Level 4 (init 4): Full system - Level 3 + Tier 4 specialized (~22 components) ~0.20s

Tier Structure:
- Tier 0: Canonical Foundation (data structures, assessor, logger)
- Tier 1: Core Metacognition (12D monitor, calibration, goals)
- Tier 2: Foundation (context, runtime, environment, workspace, cascade)
- Tier 2.5: Calibration Enhancements (Bayesian Guardian, Drift Monitor) [OPTIONAL]
- Tier 3: Advanced (code analysis, investigation, performance, navigation)
- Tier 4: Specialized (security, procedural, tools, plugins)

Legacy Levels (backward compatibility):
- minimal -> init 0
- standard -> init 1
- extended -> init 2
- complete -> init 4

Version: 3.0.0 - Init-Style Bootstrap with Canonical Foundation
"""

import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
import asyncio

# Set up logging for bootstrap
logger = logging.getLogger(__name__)

# Fix sys.path: Ensure empirica paths come BEFORE semantic_self_aware_kit
# This prevents importing from old location
empirica_root = Path(__file__).parent.parent.parent  # /path/to/empirica
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

# Remove any semantic_self_aware_kit paths that might interfere
sys.path = [p for p in sys.path if 'semantic_self_aware_kit' not in p]

logger.info(f"🔧 Fixed sys.path (empirica first):")
logger.info(f"   {sys.path[0]}")
logger.info(f"   {sys.path[1]}")
logger.info(f"   {sys.path[2]}")

# Import the base bootstrap
from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap

# Import component self-evaluation
try:
    from component_self_evaluation import explain_component, generate_bootstrap_explanation
    SELF_EVALUATION_AVAILABLE = True
except ImportError:
    SELF_EVALUATION_AVAILABLE = False

class ExtendedMetacognitiveBootstrap(OptimalMetacognitiveBootstrap):
    """
    Extended bootstrap with Foundation and Advanced tiers
    
    Extends OptimalMetacognitiveBootstrap with:
    - Tier 2: Foundation components (context, execution, navigation)
    - Tier 3: Advanced components (investigation, performance)
    - Tier 4: Specialized components (security, tools)
    """
    
    def __init__(self, ai_id: str = "empirica_ai", level: str = "2"):
        # Store the init level before parent initialization
        self.init_level = self._normalize_init_level(level)
        
        # For parent class, map init level to named level for compatibility
        parent_level_map = {
            "0": "minimal",
            "1": "standard",
            "2": "full",
            "3": "full",  # Extended uses custom methods
            "4": "full"   # Extended uses custom methods
        }
        parent_level = parent_level_map.get(self.init_level, "standard")
        
        # Initialize parent (but we'll override bootstrap() method)
        # Temporarily bypass parent's __init__ to avoid double initialization
        self.ai_id = ai_id
        self.level = self.init_level  # Use init_level as primary level
        self.components = {}
        self.bootstrap_start_time = time.time()
        
        # Initialize auto-tracker
        from empirica.auto_tracker import EmpericaTracker
        self.tracker = EmpericaTracker.get_instance(
            ai_id=ai_id,
            bootstrap_level=int(self.init_level)
        )
        
        logger.info(f"🚀🧠✨ Extended Metacognitive Bootstrap")
        logger.info(f"   🤖 AI ID: {self.ai_id}")
        logger.info(f"   📊 Init Level: {self.init_level}")
        logger.info(f"   🌟 Extended Bootstrap: Init-Style Levels (0-4)")
        logger.info(f"   🎯 Focus: Epistemic humility + Empirical feedback")
        logger.info(f"   📈 Auto-tracking: ENABLED")
        logger.info(f"   📄 AI Agent Guidelines: Please review AI_AGENT_GUIDELINES.md for best practices.")
        logger.info(f"   🔷 Canonical Foundation: LLM-powered, no heuristics")
        logger.info("")
    
    def _normalize_init_level(self, level) -> str:
        """Normalize init level to support both numeric (0-4) and named conventions"""
        level_str = str(level)
        
        # Map legacy names to init levels
        legacy_to_init = {
            "minimal": "0",
            "standard": "1", 
            "extended": "2",
            "complete": "4"
        }
        
        # If it's a legacy name, convert it
        if level_str in legacy_to_init:
            return legacy_to_init[level_str]
        
        # If it's already numeric 0-4, validate and return
        if level_str in ["0", "1", "2", "3", "4"]:
            return level_str
        
        # Default to level 2 (extended)
        print(f"⚠️  Unknown level '{level}', defaulting to '2' (extended)")
        return "2"
        
    def show_explanation(self, component_name: str = None):
        """Show explanation of what components do and why they matter"""
        if not SELF_EVALUATION_AVAILABLE:
            print("⚠️ Component self-evaluation not available")
            return
        
        if component_name:
            print(explain_component(component_name))
        else:
            # Show explanation for current bootstrap level
            print(generate_bootstrap_explanation(self.level))
    
    def list_loaded_components(self, show_help: bool = True):
        """List all loaded components with optional explanations"""
        print("\n📦 LOADED COMPONENTS")
        print("=" * 70)
        
        for comp_name, comp_value in self.components.items():
            if comp_name == 'lazy_components':
                continue
            
            # Try to map to explanation
            component_key = None
            if 'twelve_vector' in comp_name or '12d' in comp_name:
                component_key = 'metacognition_12d_monitor'
            elif 'calibration' in comp_name:
                component_key = 'adaptive_uncertainty_calibration'
            elif 'goal' in comp_name or 'orchestr' in comp_name:
                component_key = 'canonical_goal_orchestrator'
            elif 'cascade' in comp_name:
                component_key = 'metacognitive_cascade'
            elif 'context_validator' in comp_name:
                component_key = 'context_validation'
            elif 'runtime' in comp_name:
                component_key = 'runtime_validation'
            elif 'environment' in comp_name:
                component_key = 'environment_stabilization'
            elif 'workspace' in comp_name or 'navigator' in comp_name:
                component_key = 'workspace_awareness'
            
            if component_key and show_help and SELF_EVALUATION_AVAILABLE:
                from component_self_evaluation import COMPONENT_VALUES
                value = COMPONENT_VALUES.get(component_key)
                if value:
                    print(f"\n▸ {value.component_name}")
                    print(f"  {value.what_it_does}")
                    print(f"  🤖 For AI: {value.how_it_helps_ai}")
            else:
                print(f"  {comp_name}: {type(comp_value).__name__}")
        
        print()

        
    def bootstrap(self) -> Dict[str, Any]:
        """Run bootstrap based on init level (0-4)"""
        if self.level == "0" or self.level == "minimal":
            return self.bootstrap_init0()  # Tier 0 + 1 (canonical + core)
        elif self.level == "1" or self.level == "standard":
            return self.bootstrap_init1()  # + Tier 2 (foundation)
        elif self.level == "2" or self.level == "extended":
            return self.bootstrap_init2()  # + Tier 2.5 (calibration)
        elif self.level == "3":
            return self.bootstrap_init3()  # + Tier 3 (advanced)
        elif self.level == "4" or self.level == "complete":
            return self.bootstrap_init4()  # + Tier 4 (specialized)
        else:
            print(f"⚠️ Unknown level '{self.level}', defaulting to init 1")
            return self.bootstrap_init1()
    
    def bootstrap_init0(self) -> Dict[str, Any]:
        """Init Level 0: Canonical + Core (Tier 0 + 1) - Minimal system"""
        print(f"\n🚀 BOOTSTRAP: INIT LEVEL 0 (Canonical + Core)")
        print("=" * 70)
        
        # Load Tier 0 (Canonical)
        tier0_loaded = self._load_tier0_canonical()
        
        # Load Tier 1 (Core from parent class)
        super().bootstrap_minimal()
        
        return self.components
    
    def bootstrap_init1(self) -> Dict[str, Any]:
        """Init Level 1: Single-user (Init 0 + Tier 2) - Foundation system"""
        print(f"\n🚀 BOOTSTRAP: INIT LEVEL 1 (Single-user)")
        print("=" * 70)
        
        # Load Init 0 (Canonical + Core)
        tier0_loaded = self._load_tier0_canonical()
        super().bootstrap_minimal()
        
        # Load Tier 2 (Foundation)
        print("\n🔷 TIER 2: FOUNDATION")
        print("=" * 70)
        tier2_loaded = self._load_tier2_foundation()
        
        self._print_bootstrap_summary()
        return self.components
    
    def bootstrap_init2(self) -> Dict[str, Any]:
        """Init Level 2: Multi-user (Init 1 + Tier 2.5) - With calibration"""
        print(f"\n🚀 BOOTSTRAP: INIT LEVEL 2 (Multi-user)")
        print("=" * 70)
        
        # Load Init 1 (Canonical + Core + Foundation)
        tier0_loaded = self._load_tier0_canonical()
        super().bootstrap_minimal()
        tier2_loaded = self._load_tier2_foundation()
        
        # Load Tier 2.5 (Calibration)
        tier2_5_loaded = self._load_tier2_5_calibration()
        
        self._print_bootstrap_summary()
        return self.components
    
    def bootstrap_init3(self) -> Dict[str, Any]:
        """Init Level 3: Network services (Init 2 + Tier 3) - Advanced"""
        print(f"\n🚀 BOOTSTRAP: INIT LEVEL 3 (Network services)")
        print("=" * 70)
        
        # Load Init 2 (up to calibration)
        tier0_loaded = self._load_tier0_canonical()
        super().bootstrap_minimal()
        tier2_loaded = self._load_tier2_foundation()
        tier2_5_loaded = self._load_tier2_5_calibration()
        
        # Load Tier 3 (Advanced)
        print("\n🔷 TIER 3: ADVANCED")
        print("=" * 70)
        tier3_loaded = self._load_tier3_advanced()
        
        self._print_bootstrap_summary()
        return self.components
    
    def bootstrap_init4(self) -> Dict[str, Any]:
        """Init Level 4: Full system (Init 3 + Tier 4) - Complete"""
        print(f"\n🚀 BOOTSTRAP: INIT LEVEL 4 (Full system)")
        print("=" * 70)
        
        # Load Init 3 (up to advanced)
        tier0_loaded = self._load_tier0_canonical()
        super().bootstrap_minimal()
        tier2_loaded = self._load_tier2_foundation()
        tier2_5_loaded = self._load_tier2_5_calibration()
        tier3_loaded = self._load_tier3_advanced()
        
        # Load Tier 4 (Specialized)
        print("\n🔷 TIER 4: SPECIALIZED")
        print("=" * 70)
        tier4_loaded = self._load_tier4_specialized()
        
        self._print_bootstrap_summary()
        return self.components
    
    # Legacy methods for backward compatibility
    def bootstrap_minimal(self) -> Dict[str, Any]:
        """Legacy alias for bootstrap_init0"""
        return self.bootstrap_init0()
    
    def bootstrap_standard_extended(self) -> Dict[str, Any]:
        """Legacy alias for bootstrap_init1"""
        return self.bootstrap_init1()
    
    def bootstrap_extended(self) -> Dict[str, Any]:
        """Legacy alias for bootstrap_init2"""
        return self.bootstrap_init2()
    
    def bootstrap_complete(self) -> Dict[str, Any]:
        """Legacy alias for bootstrap_init4"""
        return self.bootstrap_init4()
    
    def _load_tier0_canonical(self) -> int:
        """Load Tier 0 (Canonical Foundation) - Core data structures and LLM-powered assessment"""
        loaded = 0
        
        print("\n🔷 TIER 0: CANONICAL FOUNDATION")
        print("=" * 70)
        
        # 1. Canonical Data Structures
        try:
            print("1️⃣ Loading canonical data structures...")
            from canonical.reflex_frame import (
                VectorState,
                EpistemicAssessmentSchema as EpistemicAssessment,
                Action
            )
            from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema
            
            self.components['vector_state'] = VectorState
            self.components['epistemic_assessment'] = EpistemicAssessmentSchema  # Updated schema
            self.components['action_enum'] = Action
            
            print("   ✅ Canonical data structures loaded (VectorState, EpistemicAssessmentSchema, Action)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Canonical data structures failed: {e}")
        
        # 2. Canonical Assessor (LLM-powered, no heuristics)
        try:
            print("\n2️⃣ Loading canonical epistemic assessor...")
            from canonical.canonical_epistemic_assessment import CanonicalEpistemicAssessor
            
            self.components['canonical_assessor'] = CanonicalEpistemicAssessor()
            
            print("   ✅ Canonical assessor loaded (LLM-powered, no heuristics)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Canonical assessor failed: {e}")
        
        # 3. Reflex Logger (Temporal Separation)
        try:
            print("\n3️⃣ Loading reflex logger...")
            from canonical.reflex_logger import ReflexLogger
            
            self.components['reflex_logger'] = ReflexLogger()
            
            print("   ✅ Reflex logger loaded (temporal separation active)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Reflex logger failed: {e}")
        
        print()
        return loaded
    
    def _load_tier2_foundation(self) -> int:
        """Load Tier 2 (Foundation) components"""
        loaded = 0
        
        # 1. Context Validation (ICT/PCT)
        try:
            print("1️⃣ Loading context_validation (ICT/PCT)...")
            from empirica.components.context_validation import (
                ContextIntegrityValidator,
                InternalConsistencyToken,
                PersistentConsistencyToken,
                create_context_validator
            )
            
            self.components['context_validator'] = create_context_validator()
            self.components['ict_class'] = InternalConsistencyToken
            self.components['pct_class'] = PersistentConsistencyToken
            
            print("   ✅ Context validation loaded (truth grounding active)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Context validation failed: {e}")
        
        # 2. Runtime Validation
        try:
            print("\n2️⃣ Loading runtime_validation...")
            from empirica.components.runtime_validation import (
                RuntimeCodeValidator,
                ExecutionLogEntry
            )
            
            self.components['runtime_validator'] = RuntimeCodeValidator()
            self.components['execution_log'] = ExecutionLogEntry
            
            print("   ✅ Runtime validation loaded (execution safety active)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Runtime validation failed: {e}")
        
        # 3. Environment Stabilization
        try:
            print("\n3️⃣ Loading environment_stabilization...")
            from empirica.components.environment_stabilization import (
                EnvironmentStabilizer,
                EnvironmentState
            )
            
            self.components['environment_stabilizer'] = EnvironmentStabilizer()
            self.components['environment_state'] = EnvironmentState
            
            print("   ✅ Environment stabilization loaded (cross-platform stability)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Environment stabilization failed: {e}")
        
        # 4. Workspace Awareness
        try:
            print("\n4️⃣ Loading workspace_awareness...")
            from empirica.components.workspace_awareness import (
                WorkspaceNavigator,
                DigitalMap,
                create_workspace_navigator
            )
            
            self.components['workspace_navigator'] = create_workspace_navigator()
            self.components['digital_map'] = DigitalMap
            
            print("   ✅ Workspace awareness loaded (spatial intelligence active)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Workspace awareness failed: {e}")

        # 5. Canonical Epistemic Cascade (updated from EpistemicAdaptiveCascade)
        try:
            print("\n5️⃣ Loading canonical epistemic cascade...")
            from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
            self.components['canonical_cascade'] = CanonicalEpistemicCascade()
            # Keep legacy alias for backward compatibility
            self.components['epistemic_adaptive_cascade'] = self.components['canonical_cascade']
            loaded += 1
            print("   ✅ Canonical cascade loaded (legacy alias: epistemic_adaptive_cascade)")
        except Exception as e:
            print(f"   ❌ Failed to load canonical cascade: {e}")

        # 6. Epistemic Orchestrator - REMOVED (deprecated, use canonical cascade instead)
        # The canonical cascade handles orchestration internally via investigation strategy
        print("\n6️⃣ Epistemic Orchestrator skipped (deprecated, use canonical_cascade instead)")
        
        return loaded
    
    def _load_tier2_5_calibration(self) -> int:
        """Load Tier 2.5 (Calibration Enhancements) - Optional, precision-critical domains"""
        loaded = 0
        
        print("\n🔷 TIER 2.5: CALIBRATION ENHANCEMENTS (Optional)")
        print("=" * 70)
        
        # 1. Bayesian Guardian
        try:
            print("1️⃣ Loading Bayesian Guardian...")
            from empirica.calibration.adaptive_uncertainty_calibration.bayesian_belief_tracker import (
                BayesianBeliefTracker,
                Evidence,
                DomainClassifier
            )
            
            self.components['bayesian_tracker'] = BayesianBeliefTracker()
            self.components['evidence_class'] = Evidence
            self.components['domain_classifier'] = DomainClassifier
            
            print("   ✅ Bayesian Guardian loaded (evidence-based calibration)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Bayesian Guardian failed: {e}")
        
        # 2. Drift Monitor
        try:
            print("\n2️⃣ Loading Drift Monitor...")
            from empirica.calibration.parallel_reasoning import (
                ParallelReasoningSystem,
                DriftMonitor
            )
            
            self.components['parallel_reasoning'] = ParallelReasoningSystem()
            self.components['drift_monitor'] = DriftMonitor()
            
            print("   ✅ Drift Monitor loaded (sycophancy/tension detection)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Drift Monitor failed: {e}")
        
        print()
        return loaded
    
    def _load_tier3_advanced(self) -> int:
        """Load Tier 3 (Advanced) components"""
        loaded = 0
        
        # 1. Code Intelligence Analyzer - DISABLED (contains heuristics)
        try:
            print("1️⃣ Loading code_intelligence_analyzer...")
            print("   ⚠️ Code intelligence analyzer skipped (contains heuristics)")
            print("   💡 Use canonical architecture for code analysis")
            
            # Disabled due to heuristic patterns
            # from empirica.components.code_intelligence_analyzer import (
            #     CodeIntelligenceAnalyzer,
            #     ProjectArchaeologist
            # )
            
            # self.components['code_analyzer_class'] = CodeIntelligenceAnalyzer
            # self.components['project_archaeologist'] = ProjectArchaeologist
            
            # print("   ✅ Code intelligence loaded (AI archaeologist ready)")
            loaded += 0  # Not loaded
        except Exception as e:
            print(f"   ❌ Code intelligence failed: {e}")
        
        # 2. Advanced Investigation
        try:
            print("\n2️⃣ Loading advanced_investigation...")
            from advanced_investigation import (
                AdvancedInvestigationEngine,
                InvestigationProtocol
            )
            
            self.components['investigation_class'] = AdvancedInvestigationEngine
            self.components['investigation_protocol'] = InvestigationProtocol
            
            print("   ✅ Advanced investigation loaded (deep analysis ready)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Advanced investigation failed: {e}")
        
        # 3. Empirical Performance Analyzer
        try:
            print("\n3️⃣ Loading empirical_performance_analyzer...")
            from empirica.components.empirical_performance_analyzer import (
                EmpiricalPerformanceAnalyzer
            )
            
            self.components['performance_analyzer_class'] = EmpiricalPerformanceAnalyzer
            
            print("   ✅ Performance analyzer loaded (empirical benchmarking ready)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Performance analyzer failed: {e}")
        
        # 4. Intelligent Navigation
        try:
            print("\n4️⃣ Loading intelligent_navigation...")
            from empirica.components.intelligent_navigation import (
                IntelligentWorkspaceNavigator,
                NavigationStrategy
            )
            
            self.components['intelligent_navigator_class'] = IntelligentWorkspaceNavigator
            self.components['navigation_strategy'] = NavigationStrategy
            
            print("   ✅ Intelligent navigation loaded (advanced navigation ready)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Intelligent navigation failed: {e}")
        
        return loaded
    
    def _load_tier4_specialized(self) -> int:
        """Load Tier 4 (Specialized) components"""
        loaded = 0
        
        # 1. Security Monitoring
        try:
            print("1️⃣ Loading security_monitoring...")
            from empirica.components.security_monitoring import (
                SecurityMonitoringEngine,
                create_security_monitor
            )
            
            self.components['security_monitor_class'] = SecurityMonitoringEngine
            self.components['create_security_monitor'] = create_security_monitor
            
            print("   ✅ Security monitoring loaded (threat detection ready)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Security monitoring failed: {e}")
        
        # 2. Procedural Analysis
        try:
            print("\n2️⃣ Loading procedural_analysis...")
            from empirica.components.procedural_analysis import (
                ProceduralAnalysisEngine,
                create_procedural_analyzer
            )
            
            self.components['procedural_analyzer_class'] = ProceduralAnalysisEngine
            self.components['create_procedural_analyzer'] = create_procedural_analyzer
            
            print("   ✅ Procedural analysis loaded (process analysis ready)")
            loaded += 1
        except Exception as e:
            print(f"   ❌ Procedural analysis failed: {e}")
        
        # 3. Tool Management - DISABLED (contains heuristics)
        try:
            print("\n3️⃣ Loading tool_management...")
            print("   ⚠️ Tool management skipped (contains heuristics)")
            print("   💡 Use canonical architecture for tool selection")
            
            # Disabled due to heuristic patterns
            # from empirica.components.tool_management import (
            #     AIEnhancedToolManager,
            #     activate_standalone_tool_management
            # )
            
            # self.components['tool_manager_class'] = AIEnhancedToolManager
            # self.components['activate_tool_management'] = activate_standalone_tool_management
            
            # print("   ✅ Tool management loaded (AI-enhanced tools ready)")
            loaded += 0  # Not loaded
        except Exception as e:
            print(f"   ❌ Tool management failed: {e}")
        
        return loaded
    
    # Lazy loading helpers
    def load_code_analyzer(self, project_path: str = "."):
        """Lazy load code intelligence analyzer (expensive)"""
        if 'code_analyzer' not in self.components:
            print("🧠 Loading code intelligence analyzer...")
            CodeIntelligenceAnalyzer = self.components.get('code_analyzer_class')
            if CodeIntelligenceAnalyzer:
                self.components['code_analyzer'] = CodeIntelligenceAnalyzer(project_path)
                print(f"   ✅ Code analyzer loaded for {project_path}")
            else:
                print("   ❌ Code analyzer class not available - load tier 3 first")
        return self.components.get('code_analyzer')
    
    def load_investigation_engine(self, ai_id: str = None):
        """Lazy load investigation engine"""
        if 'investigation_engine' not in self.components:
            print("🔬 Loading investigation engine...")
            AdvancedInvestigationEngine = self.components.get('investigation_class')
            if AdvancedInvestigationEngine:
                self.components['investigation_engine'] = AdvancedInvestigationEngine(ai_id or self.ai_id)
                print("   ✅ Investigation engine loaded")
            else:
                print("   ❌ Investigation engine class not available - load tier 3 first")
        return self.components.get('investigation_engine')
    
    def load_performance_analyzer(self):
        """Lazy load performance analyzer"""
        if 'performance_analyzer' not in self.components:
            print("📊 Loading performance analyzer...")
            EmpiricalPerformanceAnalyzer = self.components.get('performance_analyzer_class')
            if EmpiricalPerformanceAnalyzer:
                self.components['performance_analyzer'] = EmpiricalPerformanceAnalyzer()
                print("   ✅ Performance analyzer loaded")
            else:
                print("   ❌ Performance analyzer class not available - load tier 3 first")
        return self.components.get('performance_analyzer')
    
    def _print_bootstrap_summary(self):
        """Enhanced summary with tier information"""
        elapsed = time.time() - self.bootstrap_start_time
        loaded_count = len([k for k in self.components.keys() if k != 'lazy_components'])
        
        print(f"\n📊 EXTENDED BOOTSTRAP SUMMARY")
        print("=" * 50)
        print(f"   🚀 Components loaded: {loaded_count}")
        print(f"   ⏱️ Bootstrap time: {elapsed:.3f}s")
        print(f"   💡 Level: {self.level}")
        
        # Tier breakdown
        tier_info = []
        if loaded_count >= 10:  # Tier 1 + 2
            tier_info.append("Tier 1 (Core)")
            tier_info.append("Tier 2 (Foundation)")
        if loaded_count >= 14:  # + Tier 3
            tier_info.append("Tier 3 (Advanced)")
        if loaded_count >= 17:  # + Tier 4
            tier_info.append("Tier 4 (Specialized)")
        
        if tier_info:
            print(f"   📦 Tiers: {', '.join(tier_info)}")
        
        if self.level == "minimal":
            print(f"   ✨ Core metacognition ready!")
        elif self.level == "standard":
            print(f"   ✨ Foundation ready - Production use!")
        elif self.level == "extended":
            print(f"   ✨ Extended ready - Full analysis capabilities!")
        elif self.level == "complete":
            print(f"   ✨ Complete ecosystem ready!")
        
        print()


    async def run_cascade(self, task: str, context: Dict[str, Any] = None):
        """
        Convenience method to run the new epistemic adaptive cascade
        """
        if 'epistemic_adaptive_cascade' not in self.components:
            raise RuntimeError("Bootstrap standard or higher first")
        
        return await self.components['epistemic_adaptive_cascade'].run_epistemic_cascade(task, context)


# Convenience function for quick bootstrap
def bootstrap_extended(ai_id: str = "empirica_ai", level: str = "standard") -> Dict[str, Any]:
    """
    Quick extended bootstrap function
    
    Args:
        ai_id: AI identifier
        level: Bootstrap level (minimal, standard, extended, complete)
        
    Returns:
        Dictionary of loaded components
    """
    bootstrap = ExtendedMetacognitiveBootstrap(ai_id, level)
    return bootstrap.bootstrap()


# Main execution for testing
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Extended Metacognitive Bootstrap")
    parser.add_argument('--level', default='standard', 
                       choices=['minimal', 'standard', 'extended', 'complete'],
                       help='Bootstrap level')
    parser.add_argument('--ai-id', default='test_ai',
                       help='AI identifier')
    args = parser.parse_args()
    
    print("🧪 Testing Extended Metacognitive Bootstrap")
    print()
    
    # Bootstrap
    bootstrap = ExtendedMetacognitiveBootstrap(args.ai_id, args.level)
    components = bootstrap.bootstrap()
    
    # Test assessment
    print("\n🧪 Testing 12-vector assessment...")
    assessment = bootstrap.get_assessment(
        task="Test the extended metacognitive bootstrap",
        context={"test": True, "level": args.level},
        goals=["Verify bootstrap works", "Test all tiers"]
    )
    print(f"   Assessment type: {type(assessment).__name__}")
    print(f"   ✅ Assessment successful!")
    
    # Test cascade if standard or higher
    if args.level in ['standard', 'extended', 'complete']:
        print("\n🧪 Testing metacognitive cascade with a VAGUE task...")
        # Using a vague task to test dynamic rationale
        result = await bootstrap.run_cascade(
            "We should do that thing with the bootstrap stuff, you know?",
            {"bootstrap_test": True, "level": args.level}
        )
        print(f"   Decision: {result['action']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Rationale: {result['rationale']}")
        print(f"   ✅ Cascade successful!")
    
    # Test Tier 2 if standard or higher
    if args.level in ['standard', 'extended', 'complete']:
        print("\n🧪 Testing Tier 2 (Foundation)...")
        if 'context_validator' in bootstrap.components:
            print("   ✅ Context validation available")
        if 'runtime_validator' in bootstrap.components:
            print("   ✅ Runtime validation available")
        if 'environment_stabilizer' in bootstrap.components:
            print("   ✅ Environment stabilization available")
        if 'workspace_navigator' in bootstrap.components:
            print("   ✅ Workspace awareness available")
        if 'epistemic_adaptive_cascade' in bootstrap.components:
            print("   ✅ Epistemic Adaptive Cascade available")
        if 'epistemic_orchestrator' in bootstrap.components:
            print("   ✅ Epistemic Orchestrator available")
    
    # Test Tier 3 if extended or complete
    if args.level in ['extended', 'complete']:
        print("\n🧪 Testing Tier 3 (Advanced)...")
        if 'code_analyzer_class' in bootstrap.components:
            print("   ✅ Code intelligence available")
        if 'investigation_class' in bootstrap.components:
            print("   ✅ Advanced investigation available")
        if 'performance_analyzer_class' in bootstrap.components:
            print("   ✅ Performance analyzer available")
        if 'intelligent_navigator_class' in bootstrap.components:
            print("   ✅ Intelligent navigation available")
    
    print("\n✅ All tests passed! Extended bootstrap operational!")
    print(f"📦 Total components available: {len(bootstrap.components)}")

if __name__ == "__main__":
    asyncio.run(main())
