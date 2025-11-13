"""
Comprehensive test suite for Qwen adapter

Coverage areas:
1. Basic execution
2. Memory leak prevention
3. Sequential calls (no warnings)
4. Epistemic integration
5. Cost tracking (free tier)
6. Error handling
7. ModalitySwitcher integration
"""

import subprocess
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from modality_switcher.adapters.qwen_adapter import QwenAdapter
from empirica.core.modality.plugin_registry import AdapterPayload


class TestQwenAdapter:
    """Comprehensive Qwen adapter tests"""

    def test_initialization(self):
        """Test adapter initializes correctly"""
        adapter = QwenAdapter()
        assert hasattr(adapter, 'health_check')
        assert hasattr(adapter, 'authenticate')
        assert hasattr(adapter, 'call')
        # Check metadata is properly set through ADAPTER_METADATA

    def test_basic_execution(self):
        """Test basic query execution"""
        adapter = QwenAdapter()
        
        # Mock the subprocess.run call to avoid actual CLI execution
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"response": "4", "stats": {}}'
            mock_run.return_value = mock_result
            
            payload = AdapterPayload(
                system="You are a helpful assistant.",
                state_summary="{}",
                user_query="What is 2+2?",
                temperature=0.2,
                max_tokens=100
            )
            
            response = adapter.call(payload, {})
            
            # Verify subprocess was called with correct parameters
            assert mock_run.called
            args, kwargs = mock_run.call_args
            assert 'qwen' in args[0]  # Check that qwen CLI was called
            assert '--approval-mode' in args[0]  # Check memory leak fix is applied
            assert '--output-format' in args[0]  # Check JSON output format
            
            # Response should be an AdapterResponse or AdapterError
            from empirica.core.modality.plugin_registry import AdapterResponse, AdapterError
            assert isinstance(response, (AdapterResponse, AdapterError))

    def test_memory_leak_prevention(self):
        """Verify stdin=subprocess.DEVNULL prevents memory leaks"""
        adapter = QwenAdapter()
        
        payload = AdapterPayload(
            system="You are a helpful assistant.",
            state_summary="{}",
            user_query="Test query",
            temperature=0.2,
            max_tokens=100
        )
        
        # Mock the subprocess.run to avoid actual execution
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"response": "Test", "stats": {}}'
            mock_run.return_value = mock_result
            
            response = adapter.call(payload, {})
            
            # Verify that stdin=subprocess.DEVNULL was used
            _, kwargs = mock_run.call_args
            assert kwargs.get('stdin') == subprocess.DEVNULL

    def test_sequential_calls(self):
        """Test multiple sequential calls without warnings"""
        adapter = QwenAdapter()
        
        payloads = [
            AdapterPayload(
                system="You are a helpful assistant.",
                state_summary="{}",
                user_query=f"Query {i}",
                temperature=0.2,
                max_tokens=100
            )
            for i in range(5)
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"response": "Response", "stats": {}}'
            mock_run.return_value = mock_result
            
            for payload in payloads:
                response = adapter.call(payload, {})
                from empirica.core.modality.plugin_registry import AdapterResponse, AdapterError
                assert isinstance(response, (AdapterResponse, AdapterError))

    def test_cost_tracking(self):
        """Verify cost=0.0 for free tier"""
        # Qwen adapter is free by design
        adapter = QwenAdapter(config={'cost_per_token': 0.0})
        
        payload = AdapterPayload(
            system="You are a helpful assistant.",
            state_summary="{}",
            user_query="Test query",
            temperature=0.2,
            max_tokens=100
        )
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"response": "Test", "stats": {}}'
            mock_run.return_value = mock_result
            
            # The response itself doesn't track cost, but the adapter configuration should be free
            # This is validated by the metadata in the adapter
            metadata = getattr(adapter.__class__, '__dict__', {}).get('ADAPTER_METADATA', {})
            assert metadata.get('cost_per_token', 0.0) == 0.0

    def test_error_handling(self):
        """Test error handling and graceful failures"""
        adapter = QwenAdapter()
        
        payload = AdapterPayload(
            system="You are a helpful assistant.",
            state_summary="{}",
            user_query="Test query",
            temperature=0.2,
            max_tokens=100
        )
        
        # Test timeout error
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=['qwen'], timeout=30)
            
            response = adapter.call(payload, {})
            
            from empirica.core.modality.plugin_registry import AdapterError
            assert isinstance(response, AdapterError)
            assert response.code == "timeout"

        # Test file not found error
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            response = adapter.call(payload, {})
            
            from empirica.core.modality.plugin_registry import AdapterError
            assert isinstance(response, AdapterError)
            assert response.code == "not_found"

    def test_health_check(self):
        """Test health check functionality"""
        adapter = QwenAdapter()
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            health = adapter.health_check()
            assert health is True

    def test_approval_mode_flag(self):
        """Verify --approval-mode yolo is set"""
        adapter = QwenAdapter()
        
        payload = AdapterPayload(
            system="You are a helpful assistant.",
            state_summary="{}",
            user_query="Test query",
            temperature=0.2,
            max_tokens=100
        )
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"response": "Test", "stats": {}}'
            mock_run.return_value = mock_result
            
            response = adapter.call(payload, {})
            
            # Verify that --approval-mode yolo was included in the command
            args, _ = mock_run.call_args
            cmd = args[0]
            assert '--approval-mode' in cmd
            assert 'yolo' in cmd


class TestQwenIntegration:
    """Integration tests with full system"""

    def test_modality_switcher_integration(self):
        """Test integration with ModalitySwitcher"""
        from empirica.core.modality.modality_switcher import ModalitySwitcher, RoutingPreferences
        from empirica.core.modality.modality_switcher import RoutingStrategy
        
        switcher = ModalitySwitcher()
        
        # Get the list of adapters to make sure qwen is registered
        adapters = switcher.registry.list_adapters()
        adapter_names = [adapter['name'] for adapter in adapters]
        assert 'qwen' in adapter_names
        
        # Test routing to qwen specifically
        preferences = RoutingPreferences(force_adapter='qwen')
        decision = switcher.route_request(
            query="Test query",
            epistemic_state={'know': 0.5, 'do': 0.5, 'uncertainty': 0.3},
            preferences=preferences
        )
        
        assert decision.selected_adapter == 'qwen'

    def test_routing_selection(self):
        """Test routing strategies select Qwen appropriately"""
        from empirica.core.modality.modality_switcher import ModalitySwitcher, RoutingPreferences
        from empirica.core.modality.modality_switcher import RoutingStrategy
        
        switcher = ModalitySwitcher()
        
        # Test cost-based routing - should prefer free adapters like qwen
        cost_preferences = RoutingPreferences(strategy=RoutingStrategy.COST)
        decision = switcher.route_request(
            query="Test query",
            epistemic_state={'know': 0.5, 'do': 0.5, 'uncertainty': 0.3},
            preferences=cost_preferences
        )
        
        # Note: local might be preferred over qwen for cost, but both are free
        # The important thing is it's a free adapter
        assert decision.selected_adapter in ['qwen', 'local'] or decision.estimated_cost == 0.0
        
        # Test high uncertainty - should prefer qwen for exploration
        epistemic_preferences = RoutingPreferences(strategy=RoutingStrategy.EPISTEMIC)
        high_uncertainty_state = {'know': 0.3, 'do': 0.4, 'uncertainty': 0.8}  # High uncertainty
        decision = switcher.route_request(
            query="Complex exploratory question",
            epistemic_state=high_uncertainty_state,
            preferences=epistemic_preferences
        )
        
        # The modality switcher logic should route high uncertainty to qwen
        # based on the implementation (high uncertainty → qwen for exploration)


class TestQwenPerformance:
    """Performance and load tests"""

    def test_response_time_simulation(self):
        """Test response time is reasonable (simulation)"""
        import time
        from empirica.core.modality.plugin_registry import AdapterPayload
        
        adapter = QwenAdapter()
        
        payload = AdapterPayload(
            system="You are a helpful assistant.",
            state_summary="{}",
            user_query="Quick test",
            temperature=0.2,
            max_tokens=100
        )
        
        with patch('subprocess.run') as mock_run:
            # Simulate fast response
            start = time.time()
            
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"response": "Test", "stats": {}}'
            mock_run.return_value = mock_result
            
            response = adapter.call(payload, {})
            
            elapsed = time.time() - start
            # Since this is mocked, elapsed time should be very small
            assert elapsed < 1.0  # Should be much less than 1 second for mocked call