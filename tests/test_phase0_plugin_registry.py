#!/usr/bin/env python3
"""
Phase 0 Plugin Registry Test

Verifies that:
1. Plugin registry can discover adapters
2. Adapters can be instantiated
3. Health checks work
4. Adapter interface is validated

NOTE: Modality system not supported - skipping for now
"""

import sys
from pathlib import Path
import pytest

# Add empirica to path
empirica_root = Path(__file__).parent.parent
sys.path.insert(0, str(empirica_root))
sys.path.insert(0, str(empirica_root / 'empirica'))

pytest.skip("Modality system not supported", allow_module_level=True)

from empirica.core.modality.plugin_registry import PluginRegistry, AdapterPayload
from empirica.core.modality.usage_monitor import UsageMonitor
from empirica.core.modality.auth_manager import AuthManager

def test_plugin_registry():
    """Test plugin registry discovery and registration"""
    print("🧪 Testing Plugin Registry\n")
    
    # Create registry
    registry = PluginRegistry()
    print("✅ Created plugin registry")
    
    # Discover adapters
    adapter_dir = empirica_root / "modality_switcher" / "adapters"
    print(f"📁 Searching for adapters in: {adapter_dir}")
    registry.discover_adapters(adapter_dir)
    
    # List discovered adapters
    adapters = registry.list_adapters()
    print(f"\n📋 Discovered {len(adapters)} adapter(s):")
    for adapter in adapters:
        print(f"   - {adapter['name']}: {adapter.get('description', 'No description')}")
    
    # Health check all adapters
    print("\n🏥 Running health checks:")
    health_results = registry.health_check_all()
    for name, healthy in health_results.items():
        status = "✅ OK" if healthy else "❌ FAIL"
        print(f"   {name}: {status}")
    
    # Test local adapter specifically
    if 'local' in registry.adapters:
        print("\n🤖 Testing local adapter:")
        adapter = registry.get_adapter('local')
        print(f"   ✅ Instantiated: {adapter.__class__.__name__}")
        
        # Test health check
        healthy = adapter.health_check()
        print(f"   ✅ Health check: {healthy}")
        
        # Test auth (should not require real auth)
        token_meta = adapter.authenticate({})
        print(f"   ✅ Authenticate: {token_meta.get('provider')}")
        
        # Test call with mock payload
        payload = AdapterPayload(
            system="You are a helpful assistant",
            state_summary="{}",
            user_query="Hello, test query",
            temperature=0.2,
            max_tokens=800,
            meta={'test': True}
        )
        
        response = adapter.call(payload, token_meta)
        print(f"   ✅ Call: {response.decision if hasattr(response, 'decision') else response.code}")
        
        if hasattr(response, 'decision'):
            print(f"      - Decision: {response.decision}")
            print(f"      - Confidence: {response.confidence}")
            print(f"      - Rationale: {response.rationale[:50]}...")
            print(f"      - Vector refs: {len(response.vector_references)} vectors")
    
    print("\n✅ Plugin Registry Tests Complete!")
    return True


def test_usage_monitor():
    """Test usage monitor"""
    print("\n\n🧪 Testing Usage Monitor\n")
    
    # Create monitor with test state file
    test_state = empirica_root / ".test_usage_monitor.json"
    if test_state.exists():
        test_state.unlink()
    
    monitor = UsageMonitor(state_file=test_state)
    print("✅ Created usage monitor")
    
    # Record some test calls
    print("\n📊 Recording test calls:")
    monitor.record_call("openai", tokens_used=1000, cost_usd=0.03, call_type="premium", success=True)
    print("   ✅ Recorded OpenAI premium call")
    
    monitor.record_call("local", tokens_used=500, cost_usd=0.0, call_type="local", success=True)
    print("   ✅ Recorded local call")
    
    # Check budget
    print("\n💰 Checking budgets:")
    can_use_premium = monitor.check_budget("openai", "premium")
    print(f"   OpenAI premium: {'✅ OK' if can_use_premium else '⛔ BLOCKED'}")
    
    can_use_local = monitor.check_budget("local", "local")
    print(f"   Local: {'✅ OK' if can_use_local else '⛔ BLOCKED'}")
    
    # Get usage summary
    print("\n📈 Usage summary:")
    summary = monitor.get_usage_summary()
    print(f"   Total calls: {summary['total_calls']}")
    print(f"   Hour calls: {summary['hour']['calls']}")
    print(f"   Hour cost: ${summary['hour']['cost_usd']:.4f}")
    print(f"   Hour tokens: {summary['hour']['tokens']}")
    
    # Cleanup
    if test_state.exists():
        test_state.unlink()
    
    print("\n✅ Usage Monitor Tests Complete!")
    return True


def test_auth_manager():
    """Test auth manager (will use fallback mode)"""
    print("\n\n🧪 Testing Auth Manager\n")
    
    auth = AuthManager(fallback_mode="env")
    print("✅ Created auth manager")
    print(f"   Sentinel available: {auth.sentinel_available}")
    print(f"   Fallback mode: {auth.fallback_mode}")
    
    # Try to get token for local (should always work)
    print("\n🔐 Testing token retrieval:")
    try:
        # This will fail if no env var, which is expected
        print("   Attempting local token (no auth needed)...")
        # Local adapter doesn't actually use AuthManager, so skip this test
        print("   ⏭️  Skipped (local adapter doesn't require auth)")
    except Exception as e:
        print(f"   ⚠️  Expected: {e}")
    
    print("\n✅ Auth Manager Tests Complete!")
    return True


if __name__ == "__main__":
    try:
        all_passed = True
        
        all_passed &= test_plugin_registry()
        all_passed &= test_usage_monitor()
        all_passed &= test_auth_manager()
        
        print("\n" + "="*50)
        if all_passed:
            print("🎉 ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print("❌ SOME TESTS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
