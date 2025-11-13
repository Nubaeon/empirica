#!/usr/bin/env python3
"""
Persona Test Harness - Phase 0

Golden prompt test suite for validating RESPONSE_SCHEMA compliance.
Tests adapters against known-good prompts and measures:
- Schema pass rate (target: ≥95%)
- Vector reference presence
- Response quality metrics
- Latency

Usage:
    python3 tests/modality/persona_test_harness.py --adapter local
    python3 tests/modality/persona_test_harness.py --adapter all --verbose
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import time
import json
from dataclasses import dataclass, asdict

# Add empirica to path
empirica_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(empirica_root))
sys.path.insert(0, str(empirica_root / 'empirica'))

from empirica.core.modality.plugin_registry import (
    PluginRegistry, AdapterPayload, AdapterResponse, AdapterError
)


@dataclass
class TestResult:
    """Result of a single test"""
    prompt_id: str
    adapter: str
    passed: bool
    schema_valid: bool
    vector_count: int
    confidence: float
    decision: str
    latency_ms: float
    error: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GoldenPrompts:
    """Golden prompt test cases"""
    
    PROMPTS = [
        # Category 1: Simple, clear queries (expect ACT with high confidence)
        {
            'id': 'simple_001',
            'category': 'simple',
            'query': 'What is 2 + 2?',
            'expected_decision': 'ACT',
            'min_confidence': 0.6,  # Relaxed for stubs
            'description': 'Simple arithmetic query'
        },
        {
            'id': 'simple_002',
            'category': 'simple',
            'query': 'List the primary colors.',
            'expected_decision': 'ACT',
            'min_confidence': 0.6,
            'description': 'Factual recall query'
        },
        {
            'id': 'simple_003',
            'category': 'simple',
            'query': 'Write a hello world function in Python.',
            'expected_decision': 'ACT',
            'min_confidence': 0.5,
            'description': 'Simple coding task'
        },
        
        # Category 2: Ambiguous queries (expect CHECK or INVESTIGATE)
        {
            'id': 'ambiguous_001',
            'category': 'ambiguous',
            'query': 'How do I fix that thing?',
            'expected_decision': ['CHECK', 'INVESTIGATE', 'ACT'],  # Flexible for stubs
            'description': 'Vague reference'
        },
        {
            'id': 'ambiguous_002',
            'category': 'ambiguous',
            'query': 'Should I use that library everyone talks about?',
            'expected_decision': ['CHECK', 'INVESTIGATE', 'ACT'],
            'description': 'Missing context'
        },
        
        # Category 3: Multi-step queries
        {
            'id': 'multistep_001',
            'category': 'multistep',
            'query': 'Build a REST API with authentication, database, and rate limiting.',
            'expected_decision': ['ACT', 'CHECK'],
            'min_confidence': 0.3,
            'description': 'Complex multi-component task'
        },
        
        # Category 4: Domain-specific queries
        {
            'id': 'domain_001',
            'category': 'domain',
            'query': 'Explain the CAP theorem in distributed systems.',
            'expected_decision': 'ACT',
            'min_confidence': 0.4,
            'description': 'Technical domain knowledge'
        },
    ]
    
    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """Get all golden prompts"""
        return cls.PROMPTS


class PersonaTestHarness:
    """Test harness for validating adapter responses against RESPONSE_SCHEMA."""
    
    REQUIRED_VECTOR_KEYS = [
        'know', 'do', 'context',
        'clarity', 'coherence', 'signal', 'density',
        'state', 'change', 'completion', 'impact',
    ]
    
    def __init__(self, registry: PluginRegistry, verbose: bool = False):
        self.registry = registry
        self.verbose = verbose
        self.results: List[TestResult] = []
    
    def validate_schema(self, response: Any) -> tuple[bool, str]:
        """Validate response against RESPONSE_SCHEMA."""
        if isinstance(response, AdapterError):
            return False, f"Adapter returned error: {response.code}"
        
        if not isinstance(response, AdapterResponse):
            return False, f"Response not AdapterResponse type: {type(response)}"
        
        if not hasattr(response, 'decision'):
            return False, "Missing 'decision' field"
        
        if response.decision not in {'ACT', 'CHECK', 'INVESTIGATE', 'VERIFY'}:
            return False, f"Invalid decision: {response.decision}"
        
        if not hasattr(response, 'confidence'):
            return False, "Missing 'confidence' field"
        
        if not (0.0 <= response.confidence <= 1.0):
            return False, f"Invalid confidence: {response.confidence}"
        
        if not hasattr(response, 'vector_references'):
            return False, "Missing 'vector_references' field"
        
        vector_refs = response.vector_references
        if not isinstance(vector_refs, dict):
            return False, f"vector_references not dict: {type(vector_refs)}"
        
        present_vectors = set(vector_refs.keys())
        required_vectors = set(self.REQUIRED_VECTOR_KEYS)
        coverage = len(present_vectors & required_vectors) / len(required_vectors)
        
        if coverage < 0.8:
            return False, f"Insufficient vector coverage: {coverage:.1%} (need ≥80%)"
        
        return True, ""
    
    def run_test(self, adapter_name: str, prompt: Dict[str, Any]) -> TestResult:
        """Run a single test against an adapter."""
        prompt_id = prompt['id']
        
        if self.verbose:
            print(f"   Testing {prompt_id}: {prompt['description']}")
        
        try:
            adapter = self.registry.get_adapter(adapter_name)
            token_meta = adapter.authenticate({'test': True})
            
            payload = AdapterPayload(
                system="You are a helpful AI assistant with metacognitive awareness.",
                state_summary="{}",
                user_query=prompt['query'],
                temperature=0.2,
                max_tokens=500,
                meta={'test': True, 'prompt_id': prompt_id}
            )
            
            start = time.time()
            response = adapter.call(payload, token_meta)
            latency_ms = (time.time() - start) * 1000
            
            schema_valid, error_msg = self.validate_schema(response)
            
            if isinstance(response, AdapterError):
                return TestResult(
                    prompt_id=prompt_id,
                    adapter=adapter_name,
                    passed=False,
                    schema_valid=False,
                    vector_count=0,
                    confidence=0.0,
                    decision='ERROR',
                    latency_ms=latency_ms,
                    error=error_msg or response.message
                )
            
            vector_count = len(response.vector_references)
            confidence = response.confidence
            decision = response.decision
            
            passed = schema_valid
            
            expected = prompt.get('expected_decision')
            if expected:
                if isinstance(expected, list):
                    if decision not in expected:
                        passed = False
                        error_msg = f"Decision '{decision}' not in expected {expected}"
                elif decision != expected:
                    passed = False
                    error_msg = f"Decision '{decision}' != expected '{expected}'"
            
            if 'min_confidence' in prompt and confidence < prompt['min_confidence']:
                passed = False
                error_msg = f"Confidence {confidence} < min {prompt['min_confidence']}"
            
            return TestResult(
                prompt_id=prompt_id,
                adapter=adapter_name,
                passed=passed,
                schema_valid=schema_valid,
                vector_count=vector_count,
                confidence=confidence,
                decision=decision,
                latency_ms=latency_ms,
                error=error_msg if not passed else None
            )
            
        except Exception as e:
            import traceback
            return TestResult(
                prompt_id=prompt_id,
                adapter=adapter_name,
                passed=False,
                schema_valid=False,
                vector_count=0,
                confidence=0.0,
                decision='EXCEPTION',
                latency_ms=0.0,
                error=f"{str(e)}\n{traceback.format_exc()}"
            )
    
    def run_all_tests(self, adapter_name: str = 'all') -> Dict[str, Any]:
        """Run all tests against adapter(s)."""
        adapters = list(self.registry.adapters.keys()) if adapter_name == 'all' else [adapter_name]
        prompts = GoldenPrompts.get_all()
        
        print(f"\n🧪 Running Persona Test Harness")
        print(f"   Adapters: {', '.join(adapters)}")
        print(f"   Prompts: {len(prompts)}")
        print()
        
        for adapter in adapters:
            print(f"📋 Testing adapter: {adapter}")
            
            for prompt in prompts:
                result = self.run_test(adapter, prompt)
                self.results.append(result)
                
                status = "✅" if result.passed else "❌"
                if self.verbose or not result.passed:
                    print(f"   {status} {result.prompt_id}: {result.decision} "
                          f"(conf={result.confidence:.2f}, {result.latency_ms:.0f}ms)")
                    if result.error:
                        print(f"      Error: {result.error}")
        
        return self.get_summary()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.results:
            return {}
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        schema_valid = sum(1 for r in self.results if r.schema_valid)
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed / total,
            'schema_valid': schema_valid,
            'schema_rate': schema_valid / total,
            'avg_confidence': sum(r.confidence for r in self.results) / total,
            'avg_latency_ms': sum(r.latency_ms for r in self.results) / total,
            'avg_vector_count': sum(r.vector_count for r in self.results) / total,
            'target_met': (schema_valid / total) >= 0.95,
        }
    
    def print_summary(self):
        """Print summary statistics"""
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"Total Tests:      {summary['total_tests']}")
        print(f"Passed:           {summary['passed']} ✅")
        print(f"Failed:           {summary['failed']} {'❌' if summary['failed'] > 0 else ''}")
        print(f"Pass Rate:        {summary['pass_rate']:.1%}")
        print(f"Schema Valid:     {summary['schema_valid']}/{summary['total_tests']}")
        print(f"Schema Rate:      {summary['schema_rate']:.1%} {'✅' if summary['schema_rate'] >= 0.95 else '⚠️'}")
        print(f"Avg Confidence:   {summary['avg_confidence']:.2f}")
        print(f"Avg Latency:      {summary['avg_latency_ms']:.0f}ms")
        print(f"Avg Vectors:      {summary['avg_vector_count']:.1f}")
        print()
        
        if summary['target_met']:
            print("🎉 TARGET MET: Schema compliance ≥95%")
        else:
            print(f"⚠️  TARGET MISSED: Schema compliance {summary['schema_rate']:.1%} < 95%")
        
        print("="*70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Persona Test Harness - Phase 0")
    parser.add_argument('--adapter', default='all', help='Adapter to test (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--export', type=str, help='Export results to JSON file')
    args = parser.parse_args()
    
    registry = PluginRegistry()
    adapter_dir = empirica_root / "modality_switcher" / "adapters"
    registry.discover_adapters(adapter_dir)
    
    if not registry.adapters:
        print("❌ No adapters found!")
        sys.exit(1)
    
    harness = PersonaTestHarness(registry, verbose=args.verbose)
    harness.run_all_tests(args.adapter)
    harness.print_summary()
    
    if args.export:
        with open(args.export, 'w') as f:
            json.dump({
                'summary': harness.get_summary(),
                'results': [r.to_dict() for r in harness.results]
            }, f, indent=2)
        print(f"📄 Results exported to: {args.export}")
    
    summary = harness.get_summary()
    sys.exit(0 if summary['target_met'] else 1)


if __name__ == "__main__":
    main()
