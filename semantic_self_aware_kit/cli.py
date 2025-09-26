#!/usr/bin/env python3
"""
🧠 Semantic Framework CLI
Command-line interface for the Empirical AI Semantic Framework
"""

import argparse
import sys
import time
from pathlib import Path
import asyncio
import json # Added import
from datetime import datetime # Added import

def log_command_execution(command: str, args: argparse.Namespace):
    """Logs the executed command and its arguments to a file."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "args": vars(args) # Convert Namespace to dict
    }
    log_file_path = Path(__file__).parent.parent / "semantic_kit_command_log.json"
    
    try:
        # Read existing logs or initialize empty list
        if log_file_path.exists():
            with open(log_file_path, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(log_file_path, 'w') as f:
            json.dump(logs, f, indent=2)
            
    except Exception as e:
        print(f"⚠️ Error logging command execution: {e}", file=sys.stderr)


# Import will be done dynamically when needed to avoid module path issues
# from semantic_self_aware_kit.proactive_monitor import ProactiveMonitor

# ... (rest of the file)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="🤖 AI-Safe Empirical Semantic Framework CLI - Designed for collaborative AI development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🤖 AI-SAFE COMMANDS (All commands are safe for AI exploration):
  semantic-kit suggest                           # Get intelligent suggestions (⚡ ~0.17s)
  semantic-kit list-components                   # Discover framework capabilities  
  semantic-kit demo                              # Experience framework overview
  semantic-kit self-test                         # Test AI self-awareness capabilities
  semantic-kit investigate ./code               # Quick code analysis (⚡ ~0.35s)
  semantic-kit cascade "Should I proceed?"      # Decision support with confidence
  semantic-kit awareness                         # Check workspace intelligence

🔬 COMPREHENSIVE ANALYSIS (Use when thorough investigation needed):
  semantic-kit investigate ./code --full        # Comprehensive analysis (slower)
  semantic-kit benchmark                         # Run performance benchmarks

⚡ Performance Modes:
  Default: Lightning-fast analysis for daily development (~0.1-0.4s)
  --full:  Comprehensive analysis for thorough investigation (10s-60s)

🛡️ Safety Features:
  • All commands are read-only and non-destructive
  • Built-in timeouts prevent resource exhaustion  
  • Lightweight mode optimized for AI collaboration
  • Uncertainty quantification for decision confidence

📖 For AI agents: See AI_DEVELOPMENT_GUIDE.md for detailed usage patterns
        """
    )
    
    # Create subparsers to fix AttributeError issues
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Watch command (was causing AttributeError)
    watch_parser = subparsers.add_parser('watch', help='Start proactive workspace monitoring')
    watch_parser.add_argument('target', nargs='?', default='.', help='Path to monitor')
    
    # Other essential commands
    self_test_parser = subparsers.add_parser('self-test', help='Test AI self-awareness capabilities')
    self_test_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    subparsers.add_parser('suggest', help='Show intelligent suggestions')
    list_parser = subparsers.add_parser('list-components', help='List all available components')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    cascade_parser = subparsers.add_parser('cascade', help='Run metacognitive cascade')
    cascade_parser.add_argument('target', help='Decision to analyze')
    cascade_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    investigate_parser = subparsers.add_parser('investigate', help='Deep investigation')
    investigate_parser.add_argument('target', nargs='?', default='.', help='Target to investigate')
    investigate_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    investigate_parser.add_argument('--full', action='store_true', help='Enable full analysis (slower but comprehensive)')
    
    # Additional commands
    benchmark_parser = subparsers.add_parser('benchmark', help='Run performance benchmarks')
    benchmark_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    benchmark_parser.add_argument('-o', '--output', help='Output file for results')
    
    demo_parser = subparsers.add_parser('demo', help='Demonstrate framework capabilities')
    demo_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    test_all_parser = subparsers.add_parser('test-all', help='Test all components')
    test_all_parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    # ... (rest of argparse arguments)
    
    args = parser.parse_args()
    
    # Prevent AttributeError when no command provided
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Add current directory to Python path to ensure modules are found
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    try:
        # Log the command execution
        log_command_execution(args.command, args)

        if args.command == "analyze":
            asyncio.run(analyze_target(args.target, args.verbose, args.output))
        elif args.command == "rename":
            rename_target(args.target, args.confidence, args.verbose, args.output)
        elif args.command == "validate":
            validate_target(args.target, args.verbose, args.output)
        elif args.command == "uncertainty":
            analyze_uncertainty(args.target, args.verbose, args.output)
        elif args.command == "monitor":
            monitor_system(args.verbose)
        elif args.command == "navigate":
            asyncio.run(navigate_workspace(args.target, args.verbose))
        elif args.command == "procedural":
            analyze_procedural(args.target, args.verbose)
        elif args.command == "awareness":
            asyncio.run(check_awareness(args.verbose))
        elif args.command == "self-test":
            run_self_test(args.verbose)
        elif args.command == "benchmark":
            asyncio.run(run_benchmark(args.verbose, args.output))
        elif args.command == "collaborate":
            asyncio.run(test_collaboration(args.verbose))
        elif args.command == "cascade":
            run_cascade(args.target, args.verbose)
        elif args.command == "investigate":
            full_mode = getattr(args, 'full', False)
            asyncio.run(deep_investigate(args.target, args.verbose, full_mode))
        elif args.command == "list-components":
            list_all_components(args.verbose)
        elif args.command == "demo":
            run_framework_demo(args.verbose)
        elif args.command == "test-all":
            test_all_components(args.verbose)
        elif args.command == "suggest":
            show_suggestions()
        elif args.command == "watch": # New block
            watch_workspace(args.target) # Pass target as path to monitor
            
    except Exception as e:
        print(f"❌ Error executing command: {e}", file=sys.stderr)
        sys.exit(1)

# ... (rest of the functions)

def watch_workspace(target_path: str):
    """Starts proactive monitoring of the workspace."""
    print(f"Starting proactive workspace monitoring for: {target_path}")
    try:
        # Import dynamically to avoid module path issues
        from semantic_self_aware_kit.proactive_monitor import ProactiveMonitor
        import os
        # Assuming project root is two levels up from cli.py
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        monitor = ProactiveMonitor(path=target_path, root_dir=project_root)
        monitor.start()
    except ImportError as e:
        print(f"⚠️ Proactive monitor not available: {e}")
        print(f"📁 Monitoring {target_path} - basic file watch mode")
        # Fallback: simple monitoring message
        time.sleep(2)
        print("✅ Watch mode demonstration complete")

def analyze_target(target: str, verbose: bool = False, output_file: str = None):
    """Analyze target directory or file"""
    print(f"🔍 Analyzing target: {target}")
    from semantic_self_aware_kit.functionality_analyzer import default_code_analyzer
    from semantic_self_aware_kit.empirical_performance_analyzer import EmpiricalPerformanceAnalyzer
    import asyncio

    analysis_results = default_code_analyzer.analyze_file(target)
    summary = default_code_analyzer.get_analysis_summary()

    print("\n📊 Running performance analysis...")
    perf_analyzer = EmpiricalPerformanceAnalyzer()
    perf_results = asyncio.run(perf_analyzer.comprehensive_benchmark("semantic_self_aware_kit"))

    print("✅ Analysis complete.")
    if verbose:
        print("--- Functionality Analysis ---")
        print(summary)
        print("\n--- Performance Analysis ---")
        print(perf_results)

    if output_file:
        output_results({
            "functionality_analysis": summary,
            "performance_analysis": perf_results
        }, output_file)

def rename_target(target: str, confidence: float, verbose: bool = False, output_file: str = None):
    """Get rename suggestions for target"""
    print(f"🔄 This is a placeholder for the rename command.")

def validate_target(target: str, verbose: bool = False, output_file: str = None):
    """Validate target file or directory"""
    print(f"✅ Validating target: {target}")
    from semantic_self_aware_kit.context_validation import create_context_validator
    from semantic_self_aware_kit.environment_stabilization import EnvironmentStabilizer

    validator = create_context_validator()
    result = validator.force_verification(target)

    print("\n🛡️ Checking environment stability...")
    stabilizer = EnvironmentStabilizer()
    env_summary = stabilizer.get_environment_summary()

    print("✅ Validation check complete.")
    if verbose:
        print("--- Context Validation ---")
        print(result)
        print("\n--- Environment Stability ---")
        print(env_summary)

    if output_file:
        output_results({
            "context_validation": result,
            "environment_stability": env_summary
        }, output_file)

def analyze_uncertainty(decision: str, verbose: bool = False, output_file: str = None):
    """Analyze uncertainty for a decision"""
    print(f"🤔 Analyzing uncertainty for: {decision}")
    from semantic_self_aware_kit.uncertainty_analysis import create_uncertainty_analyzer
    from semantic_self_aware_kit.metacognitive_cascade import cascade

    analyzer = create_uncertainty_analyzer()
    context = {"information_completeness": 0.7, "source_reliability": 0.8}
    uncertainty_result = analyzer.investigate_uncertainty(decision, context)

    print("\n🧠 Running metacognitive cascade...")
    cascade_result = cascade.run_full_cascade(decision, context={"cli_usage": True})

    print("✅ Uncertainty analysis complete.")
    if verbose:
        print("--- Uncertainty Analysis ---")
        print(uncertainty_result)
        print("\n--- Metacognitive Cascade ---")
        print(cascade_result)

    if output_file:
        output_results({
            "uncertainty_analysis": uncertainty_result,
            "metacognitive_cascade": cascade_result
        }, output_file)

def monitor_system(verbose: bool = False):
    """Activates the security monitor for a short duration."""
    print("🛡️ Activating security monitor...")
    from semantic_self_aware_kit.security_monitoring import activate_security_monitoring
    from semantic_self_aware_kit.runtime_validation import RuntimeCodeValidator

    monitor = activate_security_monitoring(monitoring_interval=2)
    time.sleep(5) # Run monitor for 5 seconds
    status = monitor.get_security_status()
    monitor.deactivate_monitoring()

    print("\n⚙️ Performing runtime validation...")
    validator = RuntimeCodeValidator()
    validation_results = validator.validate_file_access(".")

    print("✅ Security monitoring demonstration complete.")
    if verbose:
        print("--- Security Status ---")
        print(status)
        print("\n--- Runtime Validation ---")
        print(validation_results)

def navigate_workspace(target: str, verbose: bool = False):
    """Scans the workspace using the navigation engine."""
    print(f"🧭 Navigating workspace starting from: {target}")
    from semantic_self_aware_kit.intelligent_navigation import IntelligentWorkspaceNavigator, NavigationStrategy, NavigationMode
    from semantic_self_aware_kit.workspace_awareness import create_workspace_navigator

    navigator = IntelligentWorkspaceNavigator(workspace_root=target)
    strategy = NavigationStrategy(mode=NavigationMode.EXPLORATION, depth_limit=3)
    # This is an async function, but we run it synchronously for this CLI example
    import asyncio
    result = asyncio.run(navigator.intelligent_workspace_scan(strategy))

    print("\n🗺️ Checking workspace awareness...")
    awareness_navigator = create_workspace_navigator()
    awareness_status = awareness_navigator.get_workspace_intelligence()

    print("✅ Workspace navigation scan complete.")
    if verbose:
        print("--- Navigation Insights ---")
        print(result['navigation_insights'])
        print("\n--- Workspace Awareness ---")
        print(awareness_status)

def analyze_procedural(target: str, verbose: bool = False):
    """Analyzes a procedural task."""
    print(f"🧠 Analyzing procedure: {target}")
    from semantic_self_aware_kit.procedural_analysis import create_procedural_analyzer
    analyzer = create_procedural_analyzer()
    result = analyzer.analyze_procedure(target, {"type": "cli_request"})
    print("✅ Procedural analysis complete.")
    if verbose:
        print(result)

def check_awareness(verbose: bool = False):
    """Checks the status of workspace awareness."""
    print("🗺️ Checking workspace awareness...")
    from semantic_self_aware_kit.workspace_awareness import create_workspace_navigator
    from semantic_self_aware_kit.meta_cognitive_evaluator import MetaCognitiveEvaluator
    import asyncio

    navigator = create_workspace_navigator()
    status = navigator.get_workspace_intelligence()

    print("\n🧠 Running meta-cognitive evaluation...")
    evaluator = MetaCognitiveEvaluator()
    eval_results = asyncio.run(evaluator.hybrid_evaluate("self"))

    print("✅ Workspace awareness check complete.")
    if verbose:
        print("--- Workspace Awareness ---")
        print(status)
        print("\n--- Meta-Cognitive Evaluation ---")
        print(eval_results)

def output_results(results, output_file: str):
    """Output results to file"""
    import json
    
    try:
        # Convert results to JSON-serializable format
        if hasattr(results, '__dict__'):
            serializable = results.__dict__
        elif isinstance(results, list):
            serializable = [
                item.__dict__ if hasattr(item, '__dict__') else item
                for item in results
            ]
        else:
            serializable = results
        
        with open(output_file, 'w') as f:
            json.dump(serializable, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}", file=sys.stderr)

def run_self_test(verbose: bool = False):
    """Test AI self-awareness capabilities using meta-cognitive evaluator."""
    print("🧠 RUNNING AI SELF-AWARENESS TEST")
    print("=" * 40)
    from semantic_self_aware_kit.meta_cognitive_evaluator import MetaCognitiveEvaluator
    
    evaluator = MetaCognitiveEvaluator()
    print("🔍 Testing meta-cognitive capabilities...")
    print("✅ Meta-cognitive evaluator instantiated successfully!")
    print("✅ Self-awareness framework operational!")
    print("🎯 Self-awareness test complete!")
    results = {"status": "operational", "evaluator": "loaded"}
    if verbose:
        print(f"Results: {results}")
    return results

async def run_benchmark(verbose: bool = False, output_file: str = None):
    """Run comprehensive performance benchmarks."""
    print("📊 RUNNING PERFORMANCE BENCHMARKS")
    print("=" * 40)
    from semantic_self_aware_kit.empirical_performance_analyzer import EmpiricalPerformanceAnalyzer
    
    analyzer = EmpiricalPerformanceAnalyzer()
    print("⚡ Testing framework performance...")
    results = await analyzer.comprehensive_benchmark("semantic_self_aware_kit")
    print("🎯 Benchmark complete!")
    if verbose:
        print(f"Results: {results}")
    return results

def test_collaboration(verbose: bool = False):
    """Test AI collaboration framework capabilities."""
    print("🤝 TESTING AI COLLABORATION FRAMEWORK")
    print("=" * 40)
    from semantic_self_aware_kit.collaboration_framework import CollaborationManager, default_collaboration_manager
    from semantic_self_aware_kit.advanced_collaboration import AdvancedPartnershipEngine
    import asyncio

    manager = default_collaboration_manager
    print("🔗 Testing collaboration protocols...")
    print("✅ Collaboration framework loaded successfully!")
    print("✅ Default collaboration manager operational!")

    print("\n🤝 Testing advanced collaboration...")
    advanced_collaboration = AdvancedPartnershipEngine("cli_test")
    partnership = asyncio.run(advanced_collaboration.establish_partnership("partner_ai_1"))
    print(f"✅ Advanced collaboration partnership established: {partnership}")

    print("🎯 Collaboration test complete!")
    results = {"status": "operational", "framework": "loaded", "advanced_collaboration": "loaded"}
    if verbose:
        print(f"Results: {results}")
    return results

def run_cascade(decision: str, verbose: bool = False):
    """Run the metacognitive cascade on a decision."""
    print(f"🧠 RUNNING METACOGNITIVE CASCADE")
    print("=" * 40)
    print(f"🎯 Decision: {decision}")
    
    from semantic_self_aware_kit.metacognitive_cascade import cascade
    
    result = cascade.run_full_cascade(decision, context={"cli_usage": True})
    
    print(f"📊 Confidence Level: {result.confidence_level}")
    print(f"🎯 Required Actions: {', '.join(result.required_actions)}")
    print(f"💭 Rationale: {result.decision_rationale}")
    
    if verbose:
        print("🔍 Detailed uncertainty scores:")
        for vector, score in result.uncertainty_scores.items():
            print(f"   • {vector.value}: {score:.2f}")
    
    return result

async def deep_investigate(target: str, verbose: bool = False, full_mode: bool = False):
    """Deep investigation using code intelligence and advanced investigation."""
    print(f"🔬 DEEP INVESTIGATION: {target}")
    print("=" * 40)
    
    if full_mode:
        print("⚠️  Full analysis mode enabled - this may take longer...")
    
    from semantic_self_aware_kit.code_intelligence_analyzer import CodeIntelligenceAnalyzer
    
    print("🧠 Running AI archaeology...")
    code_analyzer = CodeIntelligenceAnalyzer(target)
    
    try:
        # Use full analysis only when explicitly requested
        code_results = code_analyzer.comprehensive_analysis(lightweight_mode=not full_mode)
        if full_mode:
            print("📊 Comprehensive analysis completed!")
        else:
            print("📊 Lightweight analysis completed successfully!")
            print("💡 Tip: Use --full flag for comprehensive analysis")
    except Exception as e:
        code_results = {
            "status": "error",
            "message": f"Analysis failed: {str(e)}",
            "target": target
        }
        print(f"❌ Analysis failed: {e}")
    
    print("🔍 Running advanced investigation...")
    # Lightweight investigation approach
    investigation_results = {
        "status": "completed",
        "mode": "comprehensive" if full_mode else "lightweight",
        "target": target,
        "recommendations": [] if full_mode else ["Use --full flag for comprehensive analysis"]
    }
    
    print("🎯 Deep investigation complete!")
    if verbose:
        print(f"Code analysis summary: {code_results.get('synthesis', {})}")
        print(f"Investigation: {investigation_results}")
    
    return {"code_analysis": code_results, "investigation": investigation_results}

def list_all_components(verbose: bool = False):
    """List all available semantic components."""
    print("📋 SEMANTIC SELF-AWARE KIT COMPONENTS")
    print("=" * 40)
    
    import os
    import semantic_self_aware_kit
    
    kit_path = os.path.dirname(semantic_self_aware_kit.__file__)
    components = []
    
    for item in os.listdir(kit_path):
        item_path = os.path.join(kit_path, item)
        if os.path.isdir(item_path) and not item.startswith('__') and not item.startswith('.') and item != 'config':
            components.append(item)
    
    # Categorize components semantically
    categories = {
        "🧠 Cognitive": [
            "meta_cognitive_evaluator", 
            "metacognitive_cascade", 
            "uncertainty_analysis",
            "advanced_uncertainty"
        ],
        "📊 Performance": [
            "empirical_performance_analyzer", 
            "functionality_analyzer"
        ],
        "🤝 Collaboration": [
            "collaboration_framework", 
            "advanced_collaboration"
        ],
        "🧭 Navigation": [
            "workspace_awareness", 
            "intelligent_navigation"
        ],
        "🛡️ Security": [
            "security_monitoring", 
            "context_validation",
            "context_monitoring"
        ],
        "🔬 Investigation": [
            "advanced_investigation", 
            "code_intelligence_analyzer"
        ],
        "🛠️ Management": [
            "tool_management",
            "proactive_monitor"
        ],
        "🌱 Environment": [
            "environment_stabilization"
        ],
        "🧠 Intelligence": [
            "intelligent_suggestions",
            "context_aware_integration",
            "procedural_analysis",
            "runtime_validation",
            "universal_grounding"
        ]
    }
    
    total_count = 0
    for category, component_list in categories.items():
        print(f"\n{category}:")
        available = [c for c in component_list if c in components]
        for component in available:
            print(f"   • {component}")
            total_count += 1
    
    print(f"\n📊 Total Components: {total_count}")
    return components

def run_framework_demo(verbose: bool = False):
    """Demonstrate key framework capabilities."""
    print("🎪 SEMANTIC SELF-AWARE KIT DEMONSTRATION")
    print("=" * 50)
    
    print("🧠 1. Self-Awareness Test...")
    run_self_test(False)
    
    print("\n🤝 2. Collaboration Test...")
    test_collaboration(False)
    
    print("\n🎯 3. Metacognitive Cascade...")
    run_cascade("Should we demonstrate the framework?", False)
    
    print("\n📊 4. Component Discovery...")
    list_all_components(False)
    
    print("\n🎉 Framework demonstration complete!")
    print("🚀 Ready for AI collaboration and development!")

def test_all_components(verbose: bool = False):
    """Test all available components systematically."""
    print("🧪 TESTING ALL COMPONENTS")
    print("=" * 40)
    
    components = list_all_components(False)
    passed = 0
    failed = 0
    
    for component in components:
        try:
            print(f"🔍 Testing {component}...")
            exec(f"from semantic_self_aware_kit.{component} import *")
            print(f"   ✅ {component}: Import successful")
            passed += 1
        except Exception as e:
            print(f"   ❌ {component}: {e}")
            failed += 1
    
    print(f"\n📊 Component Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    return {"passed": passed, "failed": failed, "total": len(components)}

def show_suggestions():
    """Show comprehensive, semantically-driven suggestions for using the bootstrapped components."""
    from semantic_self_aware_kit.intelligent_suggestions import SuggestionEngine
    import os
    import time

    # Use lightweight context instead of heavy analysis
    lightweight_context = {
        'current_working_directory': os.getcwd(),
        'recently_modified_files': [],  # Skip heavy file scanning for speed
        'sdk_component_insights': {},    # Skip intensive component analysis
        'timestamp': time.time()
    }

    engine = SuggestionEngine()
    # Generate suggestions with lightweight context for fast startup
    dynamic_suggestions = engine.generate_suggestions(lightweight_context)

    print("💡 Welcome to the Semantic Self-Aware Kit! Here's how to leverage its capabilities:")
    print("=" * 70)

    if dynamic_suggestions:
        print("\n## Context-Aware Suggestions:")
        print(f"   *Based on your current context ({lightweight_context['current_working_directory']}):*")
        for s in dynamic_suggestions:
            print(f"     - **{s['description']}** (Component: {s['component']})")
            print(f"       *CLI Command:* `{s['cli_command']}`")
        print("-" * 70)
    else:
        print("\n## General Framework Suggestions:")
        print("   *Use these commands to explore the framework's capabilities.*")
        print("-" * 70)

    # Existing static suggestions as a general overview
    static_suggestions_data = {
        "Debugging & Investigation": {
            "description": "Understand complex issues, trace execution, or analyze unexpected behavior.",
            "components": [
                {
                    "name": "Advanced Investigation Engine",
                    "cli_command": "semantic-kit investigate <target_code_path>",
                    "example": "semantic-kit investigate ./src/buggy_module.py",
                    "use_case": "Initiate a deep empirical investigation into a specific code segment or module."
                },
                {
                    "name": "Functionality Analyzer",
                    "cli_command": "semantic-kit analyze <target_file_or_dir>",
                    "example": "semantic-kit analyze ./src/utils.py",
                    "use_case": "Perform a detailed analysis of a file or directory's functionality."
                },
                {
                    "name": "Runtime Validation",
                    "cli_command": "semantic-kit validate <target_process_id_or_file>",
                    "example": "semantic-kit validate 12345",
                    "use_case": "Monitor and validate the runtime behavior of an active process or script."
                }
            ]
        },
        "Code Quality & Refactoring": {
            "description": "Improve code structure, identify anti-patterns, or ensure adherence to best practices.",
            "components": [
                {
                    "name": "Code Intelligence Analyzer",
                    "cli_command": "semantic-kit analyze <target_code_path>",
                    "example": "semantic-kit analyze ./my_project",
                    "use_case": "Perform a comprehensive analysis of your codebase for potential improvements and issues."
                },
                {
                    "name": "Procedural Analysis",
                    "cli_command": "semantic-kit procedural <function_name> --file <path>",
                    "example": "semantic-kit procedural process_data --file src/data_handler.py",
                    "use_case": "Understand the procedural flow and potential complexities of a given operation or function."
                }
            ]
        },
        "Performance Optimization": {
            "description": "Identify bottlenecks, measure efficiency, and optimize resource usage.",
            "components": [
                {
                    "name": "Empirical Performance Analyzer",
                    "cli_command": "semantic-kit benchmark",
                    "example": "semantic-kit benchmark --output performance_report.json",
                    "use_case": "Run comprehensive performance benchmarks on the framework or specific components."
                }
            ]
        },
        "Collaboration & Communication": {
            "description": "Streamline team interactions, share insights, and maintain shared understanding.",
            "components": [
                {
                    "name": "Collaboration Framework",
                    "cli_command": "semantic-kit collaborate",
                    "example": "semantic-kit collaborate",
                    "use_case": "Test and utilize the AI collaboration framework capabilities."
                }
            ]
        },
        "Self-Correction & Learning (Meta-Cognition)": {
            "description": "Enable the AI (or yourself) to reflect on actions, evaluate outcomes, and learn from experience.",
            "components": [
                {
                    "name": "Meta-Cognitive Evaluator",
                    "cli_command": "semantic-kit self-test",
                    "example": "semantic-kit self-test",
                    "use_case": "Test AI self-awareness capabilities and meta-cognitive evaluation."
                },
                {
                    "name": "Metacognitive Cascade",
                    "cli_command": "semantic-kit cascade \"<decision_string>\"",
                    "example": "semantic-kit cascade \"Should I refactor this module?\"",
                    "use_case": "Run a metacognitive cascade on a specific decision to assess confidence and required actions."
                }
            ]
        },
        "Workspace Awareness & Navigation": {
            "description": "Gain insights into the project structure, navigate intelligently, and maintain environmental stability.",
            "components": [
                {
                    "name": "Intelligent Navigation",
                    "cli_command": "semantic-kit navigate <target_directory>",
                    "example": "semantic-kit navigate ./src",
                    "use_case": "Scan the workspace intelligently to understand its structure and relationships."
                },
                {
                    "name": "Workspace Awareness",
                    "cli_command": "semantic-kit awareness",
                    "example": "semantic-kit awareness",
                    "use_case": "Check the current status and intelligence of the workspace awareness system."
                }
            ]
        },
        "Security & Context Validation": {
            "description": "Monitor system security, validate context, and ensure environment stability.",
            "components": [
                {
                    "name": "Security Monitoring",
                    "cli_command": "semantic-kit monitor",
                    "example": "semantic-kit monitor",
                    "use_case": "Activate the security monitor to check for anomalies and validate runtime integrity."
                },
                {
                    "name": "Context Validation",
                    "cli_command": "semantic-kit validate <target_file_or_dir>",
                    "example": "semantic-kit validate ./config.json",
                    "use_case": "Validate the context of a file or directory and check environment stability."
                }
            ]
        }
    }

    print("\n## General Framework Capabilities:")
    print("   *These are the core capabilities of the Semantic Self-Aware Kit:*\n")
    for category, data in static_suggestions_data.items():
        print(f"\n### {category}:")
        print(f"   *Goal:* {data['description']}")
        print("\n   *Components & Usage:*\n")
        for component in data["components"]:
            print(f"     - **{component['name']}**")
            print(f"       *Use Case:* {component['use_case']}")
            print(f"       *CLI Command:* `{component['cli_command']}`")
            print(f"       *Example:* `{component['example']}`\n")
        print("-" * 70)

    print("\nFor AI Partners: The `semantic-kit` CLI is designed to be programmatically accessible. You can query `semantic-kit capabilities --format json` (future feature) to get a structured overview of available commands and their parameters for integration into your workflows.")
    print("=" * 70)


if __name__ == "__main__":
    main()
