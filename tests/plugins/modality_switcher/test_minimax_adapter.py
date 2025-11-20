#!/usr/bin/env python3
"""
Test script for MiniMax-M2 Adapter

Tests the adapter interface implementation without requiring actual API calls.
"""

import os
import sys
sys.path.insert(0, '/path/to/empirica')

from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload
from modality_switcher.adapters.minimax_adapter import MinimaxAdapter, ADAPTER_METADATA


def test_adapter_metadata():
    """Test adapter metadata is properly defined."""
    print("🧪 Test 1: Adapter Metadata")
    assert ADAPTER_METADATA['version'] == '1.0.0'
    assert ADAPTER_METADATA['provider'] == 'minimax'
    assert ADAPTER_METADATA['model'] == 'MiniMax-M2'
    assert ADAPTER_METADATA['type'] == 'api'
    print("   ✅ Metadata validated")


def test_adapter_instantiation():
    """Test adapter can be instantiated with config."""
    print("\n🧪 Test 2: Adapter Instantiation")
    
    # Default config
    adapter = MinimaxAdapter()
    assert adapter.model == 'MiniMax-M2'
    assert adapter.base_url == 'https://api.minimax.io/anthropic'
    assert adapter.timeout == 60
    print("   ✅ Default config works")
    
    # Custom config
    custom_adapter = MinimaxAdapter({
        'model': 'Custom-Model',
        'timeout': 120
    })
    assert custom_adapter.model == 'Custom-Model'
    assert custom_adapter.timeout == 120
    print("   ✅ Custom config works")


def test_health_check_no_key():
    """Test health check fails gracefully without API key."""
    print("\n🧪 Test 3: Health Check (No API Key)")
    
    # Temporarily clear API key
    old_key = os.environ.get('MINIMAX_API_KEY')
    if old_key:
        del os.environ['MINIMAX_API_KEY']
    
    adapter = MinimaxAdapter()
    result = adapter.health_check()
    assert result == False, "Health check should fail without API key"
    print("   ✅ Properly fails without API key")
    
    # Restore key if it existed
    if old_key:
        os.environ['MINIMAX_API_KEY'] = old_key


def test_authenticate_no_key():
    """Test authentication fails gracefully without API key."""
    print("\n🧪 Test 4: Authentication (No API Key)")
    
    # Temporarily clear API key
    old_key = os.environ.get('MINIMAX_API_KEY')
    if old_key:
        del os.environ['MINIMAX_API_KEY']
    
    adapter = MinimaxAdapter()
    try:
        adapter.authenticate({})
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "MINIMAX_API_KEY" in str(e)
        print("   ✅ Properly raises ValueError without API key")
    
    # Restore key if it existed
    if old_key:
        os.environ['MINIMAX_API_KEY'] = old_key


def test_transform_to_schema():
    """Test response transformation logic."""
    print("\n🧪 Test 5: Response Transformation")
    
    adapter = MinimaxAdapter()
    
    # Test payload
    payload = AdapterPayload(
        system="You are a helpful assistant",
        state_summary="Testing transformation",
        user_query="What is the capital of France?",
        temperature=0.7,
        max_tokens=100
    )
    
    # Test different response types
    test_cases = [
        ("Paris is the capital of France.", "ACT", 0.7),
        ("I need more information to answer this question.", "INVESTIGATE", 0.4),
        ("Let me verify the current status.", "CHECK", 0.6),
        ("I cannot provide an answer without additional context.", "VERIFY", 0.5),
    ]
    
    for response_text, expected_decision, min_confidence in test_cases:
        result = adapter._transform_to_schema(response_text, None, payload)
        
        assert result.decision == expected_decision, f"Expected {expected_decision}, got {result.decision}"
        assert result.confidence >= min_confidence - 0.1, f"Confidence too low: {result.confidence}"
        assert len(result.vector_references) == 13, "Should have 13 vectors"
        assert len(result.suggested_actions) > 0, "Should have suggested actions"
        
        # Validate all 13 vectors present
        required_vectors = [
            'know', 'do', 'context',
            'clarity', 'coherence', 'signal', 'density',
            'state', 'change', 'completion', 'impact',
            'engagement', 'uncertainty'
        ]
        for vector in required_vectors:
            assert vector in result.vector_references, f"Missing vector: {vector}"
            assert 0.0 <= result.vector_references[vector] <= 1.0, f"Vector {vector} out of range"
        
        print(f"   ✅ {expected_decision}: confidence={result.confidence:.2f}, vectors=13")


def test_adapter_interface_compliance():
    """Test adapter implements required interface."""
    print("\n🧪 Test 6: Interface Compliance")
    
    adapter = MinimaxAdapter()
    
    # Check required methods exist
    assert hasattr(adapter, 'health_check'), "Missing health_check method"
    assert hasattr(adapter, 'authenticate'), "Missing authenticate method"
    assert hasattr(adapter, 'call'), "Missing call method"
    
    # Check methods are callable
    assert callable(adapter.health_check), "health_check not callable"
    assert callable(adapter.authenticate), "authenticate not callable"
    assert callable(adapter.call), "call not callable"
    
    print("   ✅ All required methods present and callable")


def main():
    """Run all tests."""
    print("🚀 Testing MinimaxAdapter Implementation\n")
    print("=" * 60)
    
    try:
        test_adapter_metadata()
        test_adapter_instantiation()
        test_health_check_no_key()
        test_authenticate_no_key()
        test_transform_to_schema()
        test_adapter_interface_compliance()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("\n📝 Next steps:")
        print("   1. Set MINIMAX_API_KEY environment variable")
        print("   2. Run with actual API: test_minimax_adapter_live.py")
        print("   3. Register adapter in plugin registry")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
