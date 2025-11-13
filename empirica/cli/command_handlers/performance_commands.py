"""
Performance Commands - Benchmarking, performance analysis, and optimization
"""

import time
import json
from ..cli_utils import print_component_status, handle_cli_error, format_execution_time, parse_json_safely


def handle_benchmark_command(args):
    """Handle benchmark command for performance testing"""
    try:
        from empirica.components.empirical_performance_analyzer import EmpiricalPerformanceAnalyzer
        
        print("📊 Running comprehensive benchmark suite...")
        
        analyzer = EmpiricalPerformanceAnalyzer()
        start_time = time.time()
        
        # Configure benchmark parameters
        benchmark_type = getattr(args, 'type', 'comprehensive')
        iterations = getattr(args, 'iterations', 10)
        include_memory = getattr(args, 'memory', True)
        
        # Run benchmark
        result = analyzer.run_benchmark(
            benchmark_type=benchmark_type,
            iterations=iterations,
            include_memory=include_memory,
            verbose=getattr(args, 'verbose', False)
        )
        
        end_time = time.time()
        
        print(f"✅ Benchmark complete")
        print(f"   🏁 Type: {benchmark_type}")
        print(f"   🔄 Iterations: {iterations}")
        print(f"   ⏱️ Total time: {format_execution_time(start_time, end_time)}")
        print(f"   📊 Overall score: {result.get('overall_score', 0):.2f}")
        
        # Show performance metrics
        if result.get('metrics'):
            print("📈 Performance metrics:")
            for metric, value in result['metrics'].items():
                if isinstance(value, float):
                    print(f"   • {metric}: {value:.3f}")
                else:
                    print(f"   • {metric}: {value}")
        
        # Show component performance
        if result.get('component_performance'):
            print("🧩 Component performance:")
            for component, perf in result['component_performance'].items():
                status = "✅" if perf > 0.8 else "⚠️" if perf > 0.6 else "❌"
                print(f"   {status} {component}: {perf:.2f}")
        
        # Show memory usage if included
        if include_memory and result.get('memory_usage'):
            memory = result['memory_usage']
            print("💾 Memory usage:")
            print(f"   • Peak: {memory.get('peak_mb', 0):.1f} MB")
            print(f"   • Average: {memory.get('average_mb', 0):.1f} MB")
            print(f"   • Current: {memory.get('current_mb', 0):.1f} MB")
        
        # Show recommendations
        if result.get('recommendations'):
            print("💡 Performance recommendations:")
            for rec in result['recommendations']:
                print(f"   • {rec}")
        
        # Show detailed breakdown if verbose
        if getattr(args, 'verbose', False) and result.get('detailed_breakdown'):
            print("🔍 Detailed performance breakdown:")
            for category, details in result['detailed_breakdown'].items():
                print(f"   📂 {category}:")
                for key, value in details.items():
                    print(f"     • {key}: {value}")
        
    except Exception as e:
        handle_cli_error(e, "Benchmark", getattr(args, 'verbose', False))


def handle_performance_command(args):
    """Handle performance analysis command"""
    try:
        from empirica.components.empirical_performance_analyzer import EmpiricalPerformanceAnalyzer
        
        print("⚡ Running performance analysis...")
        
        analyzer = EmpiricalPerformanceAnalyzer()
        
        # Configure analysis
        target = getattr(args, 'target', 'system')
        context = parse_json_safely(getattr(args, 'context', None))
        detailed = getattr(args, 'detailed', False)
        
        # Run performance analysis
        result = analyzer.analyze_performance(
            target=target,
            context=context,
            detailed=detailed
        )
        
        print(f"✅ Performance analysis complete")
        print(f"   🎯 Target: {target}")
        print(f"   📊 Performance score: {result.get('performance_score', 0):.2f}")
        print(f"   🏆 Grade: {result.get('performance_grade', 'unknown')}")
        
        # Show performance dimensions
        if result.get('dimensions'):
            print("📏 Performance dimensions:")
            for dimension, score in result['dimensions'].items():
                status = "🟢" if score > 0.8 else "🟡" if score > 0.6 else "🔴"
                print(f"   {status} {dimension}: {score:.2f}")
        
        # Show bottlenecks
        if result.get('bottlenecks'):
            print("🚧 Identified bottlenecks:")
            for bottleneck in result['bottlenecks']:
                severity = bottleneck.get('severity', 'medium')
                emoji = "🔴" if severity == 'high' else "🟡" if severity == 'medium' else "🟢"
                print(f"   {emoji} {bottleneck.get('description', 'Unknown bottleneck')}")
        
        # Show optimization suggestions
        if result.get('optimizations'):
            print("🚀 Optimization suggestions:")
            for opt in result['optimizations']:
                impact = opt.get('impact', 'medium')
                emoji = "⚡" if impact == 'high' else "📈" if impact == 'medium' else "📊"
                print(f"   {emoji} {opt.get('suggestion', 'Unknown optimization')}")
                if opt.get('effort'):
                    print(f"     Effort: {opt['effort']}")
        
        # Show detailed metrics if requested
        if detailed and result.get('detailed_metrics'):
            print("🔍 Detailed performance metrics:")
            for category, metrics in result['detailed_metrics'].items():
                print(f"   📂 {category}:")
                for metric, value in metrics.items():
                    print(f"     • {metric}: {value}")
        
        # Show historical comparison if available
        if result.get('historical_comparison'):
            hist = result['historical_comparison']
            trend = "📈" if hist.get('trend') == 'improving' else "📉" if hist.get('trend') == 'declining' else "➡️"
            print(f"📊 Historical trend: {trend} {hist.get('trend', 'stable')}")
            if hist.get('change_percentage'):
                print(f"   Change: {hist['change_percentage']:+.1f}%")
        
    except Exception as e:
        handle_cli_error(e, "Performance analysis", getattr(args, 'verbose', False))