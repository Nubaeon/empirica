#!/usr/bin/env python3
"""
Live test for MiniMax-M2 Adapter

Tests the adapter with actual API calls to verify end-to-end functionality.
Requires MINIMAX_API_KEY environment variable.
"""

import os
import sys
sys.path.insert(0, '/path/to/empirica')

from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError
from modality_switcher.adapters.minimax_adapter import MinimaxAdapter


def test_live_health_check(adapter):
    """Test health check with actual API."""
    print("\n🧪 Live Test 1: Health Check")
    result = adapter.health_check()
    if result:
        print("   ✅ Health check passed - API is accessible")
        return True
    else:
        print("   ❌ Health check failed - API not accessible")
        return False


def test_live_authentication(adapter):
    """Test authentication with actual API."""
    print("\n🧪 Live Test 2: Authentication")
    try:
        result = adapter.authenticate({'reason': 'test'})
        assert result['authenticated'] == True
        assert result['provider'] == 'minimax'
        print(f"   ✅ Authentication successful")
        print(f"      Model: {result['model']}")
        print(f"      Base URL: {result['base_url']}")
        return True
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        return False


def test_live_simple_call(adapter):
    """Test simple API call."""
    print("\n🧪 Live Test 3: Simple API Call")
    
    payload = AdapterPayload(
        system="You are a helpful assistant for testing.",
        state_summary="Testing MiniMax adapter",
        user_query="What is 2+2? Answer briefly.",
        temperature=0.2,
        max_tokens=50
    )
    
    try:
        result = adapter.call(payload, {})
        
        if isinstance(result, AdapterError):
            print(f"   ❌ API call returned error: {result.message}")
            return False
        
        assert isinstance(result, AdapterResponse)
        assert result.decision in ["ACT", "CHECK", "INVESTIGATE", "VERIFY"]
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.vector_references) == 13
        
        print(f"   ✅ API call successful")
        print(f"      Decision: {result.decision}")
        print(f"      Confidence: {result.confidence:.2f}")
        print(f"      Rationale: {result.rationale[:80]}...")
        print(f"      Vectors: {len(result.vector_references)}")
        print(f"      Actions: {len(result.suggested_actions)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_live_complex_call(adapter):
    """Test complex API call with epistemic reasoning."""
    print("\n🧪 Live Test 4: Complex Epistemic Reasoning")
    
    payload = AdapterPayload(
        system="You are an epistemic reasoning assistant. Assess your confidence and identify what you know vs don't know.",
        state_summary="Testing epistemic assessment capabilities",
        user_query="Should I deploy a new authentication system to production without testing it first? Explain your reasoning.",
        temperature=0.3,
        max_tokens=200
    )
    
    try:
        result = adapter.call(payload, {})
        
        if isinstance(result, AdapterError):
            print(f"   ❌ API call returned error: {result.message}")
            return False
        
        print(f"   ✅ Complex reasoning successful")
        print(f"      Decision: {result.decision}")
        print(f"      Confidence: {result.confidence:.2f}")
        print(f"      Rationale preview: {result.rationale[:120]}...")
        
        # Print epistemic vectors
        print(f"      Epistemic Vectors:")
        print(f"         Foundation: KNOW={result.vector_references['know']:.2f}, DO={result.vector_references['do']:.2f}, CONTEXT={result.vector_references['context']:.2f}")
        print(f"         Comprehension: CLARITY={result.vector_references['clarity']:.2f}, COHERENCE={result.vector_references['coherence']:.2f}")
        print(f"         Execution: STATE={result.vector_references['state']:.2f}, COMPLETION={result.vector_references['completion']:.2f}")
        print(f"         Meta: ENGAGEMENT={result.vector_references['engagement']:.2f}, UNCERTAINTY={result.vector_references['uncertainty']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Complex call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all live tests."""
    print("🚀 Live Testing MiniMax-M2 Adapter")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('MINIMAX_API_KEY')
    if not api_key:
        print("❌ MINIMAX_API_KEY not set in environment")
        print("\nSet it with:")
        print("   export MINIMAX_API_KEY=$(cat ~/empirica-parent/.minimax_api)")
        return 1
    
    print(f"✅ API key loaded (length: {len(api_key)} chars)")
    
    try:
        # Initialize adapter
        adapter = MinimaxAdapter()
        print(f"✅ Adapter initialized: {adapter.model}")
        
        # Run tests
        results = []
        results.append(test_live_health_check(adapter))
        results.append(test_live_authentication(adapter))
        results.append(test_live_simple_call(adapter))
        results.append(test_live_complex_call(adapter))
        
        # Summary
        print("\n" + "=" * 60)
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"✅ All {total} live tests passed!")
            print("\n📝 MiniMax-M2 Adapter is ready for production use")
            print("\n🎯 Next steps:")
            print("   1. Register adapter in plugin registry")
            print("   2. Add to modality switcher configuration")
            print("   3. Test with persona enforcer")
            return 0
        else:
            print(f"⚠️  {passed}/{total} tests passed")
            print(f"❌ {total - passed} test(s) failed")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
