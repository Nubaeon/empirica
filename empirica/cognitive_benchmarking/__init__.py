"""
Cognitive Benchmarking for Empirica

Comprehensive AI model benchmarking combining:
1. Epistemic Reasoning Benchmark (ERB) - Self-awareness & humility
2. Traditional Performance Metrics (MMLU, HumanEval, etc.)
3. Cross-Benchmark Correlation Analysis

Version: 1.0.0
"""

try:
    from .erb.epistemic_reasoning_benchmark import (
        EpistemicReasoningBenchmark,
        BenchmarkResult
    )
except ImportError:
    EpistemicReasoningBenchmark = None
    BenchmarkResult = None

try:
    from .erb.preflight_epistemic_calibration import (
        PreflightCalibration,
        PREFLIGHT_TESTS,
        TestCategory,
        CalibrationTest
    )
except ImportError:
    PreflightCalibration = None
    PREFLIGHT_TESTS = None
    TestCategory = None
    CalibrationTest = None

from .cloud_adapters.unified_cloud_adapter import (
    get_adapter,
    AnthropicAdapter,
    OpenAIAdapter,
    GoogleAdapter,
    XAIAdapter,
    OpenRouterAdapter
)

from .analysis.cross_benchmark_correlation import (
    CrossBenchmarkAnalyzer,
    ComprehensiveBenchmarkResult,
    TraditionalBenchmarkScore,
    EpistemicBenchmarkScore,
    KNOWN_TRADITIONAL_SCORES
)

__version__ = "1.0.0"

__all__ = [
    # ERB
    'EpistemicReasoningBenchmark',
    'BenchmarkResult',
    'PreflightCalibration',
    'PREFLIGHT_TESTS',
    'TestCategory',
    'CalibrationTest',

    # Cloud Adapters
    'get_adapter',
    'AnthropicAdapter',
    'OpenAIAdapter',
    'GoogleAdapter',
    'XAIAdapter',
    'OpenRouterAdapter',

    # Cross-Benchmark Analysis
    'CrossBenchmarkAnalyzer',
    'ComprehensiveBenchmarkResult',
    'TraditionalBenchmarkScore',
    'EpistemicBenchmarkScore',
    'KNOWN_TRADITIONAL_SCORES',
]
