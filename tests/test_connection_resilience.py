#!/usr/bin/env python3
"""
Test connection pool, retry policy, and circuit breaker functionality
"""

import time
import pytest
import sqlite3
from empirica.data.connection_pool import (
    RetryPolicy, RetryStrategy, ConnectionPool, CircuitBreaker
)


class TestRetryPolicy:
    """Test exponential backoff retry policy"""
    
    def test_successful_call_first_attempt(self):
        """Successful call on first attempt"""
        policy = RetryPolicy(max_retries=3)
        
        call_count = 0
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = policy.execute_with_retry(succeed)
        assert result == "success"
        assert call_count == 1
    
    def test_retry_with_eventual_success(self):
        """Call fails twice, succeeds on third attempt"""
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        
        call_count = 0
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.OperationalError("Database locked")
            return "success"
        
        result = policy.execute_with_retry(fail_then_succeed)
        assert result == "success"
        assert call_count == 3
        assert policy.telemetry['successful_retries'] == 1
    
    def test_max_retries_exhausted(self):
        """Raises error after max retries exhausted"""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        
        call_count = 0
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise sqlite3.OperationalError("Database locked")
        
        with pytest.raises(sqlite3.OperationalError):
            policy.execute_with_retry(always_fail)
        
        assert call_count == 3  # Initial + 2 retries
        assert policy.telemetry['failed_retries'] == 1
    
    def test_non_retryable_error(self):
        """Non-retryable errors fail immediately"""
        policy = RetryPolicy(max_retries=3)
        
        call_count = 0
        def fail_non_retryable():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid argument")  # Non-retryable
        
        with pytest.raises(ValueError):
            policy.execute_with_retry(fail_non_retryable)
        
        assert call_count == 1  # No retries
    
    def test_exponential_backoff_timing(self):
        """Exponential backoff delays increase"""
        policy = RetryPolicy(
            max_retries=3,
            base_delay=0.01,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False
        )
        
        delays = []
        for attempt in range(3):
            delay = policy.calculate_delay(attempt)
            delays.append(delay)
        
        # Delays should increase exponentially
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]
    
    def test_linear_backoff_timing(self):
        """Linear backoff increases linearly"""
        policy = RetryPolicy(
            max_retries=3,
            base_delay=0.1,
            strategy=RetryStrategy.LINEAR,
            jitter=False
        )
        
        delays = []
        for attempt in range(3):
            delay = policy.calculate_delay(attempt)
            delays.append(delay)
        
        # Linear increase: delay = base_delay * attempt
        # attempt 0: 0.1 * 0 = 0.0, but capped to 0.001
        # attempt 1: 0.1 * 1 = 0.1
        # attempt 2: 0.1 * 2 = 0.2
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]
    
    def test_max_delay_cap(self):
        """Delays are capped at max_delay"""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=10.0,
            max_delay=5.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False
        )
        
        for attempt in range(5):
            delay = policy.calculate_delay(attempt)
            assert delay <= 5.0


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    def test_normal_operation(self):
        """Circuit breaker passes calls through normally"""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def succeed():
            return "success"
        
        result = breaker.call(succeed)
        assert result == "success"
        assert breaker.state == "closed"
    
    def test_circuit_opens_after_threshold(self):
        """Circuit opens after failure threshold"""
        breaker = CircuitBreaker(failure_threshold=2)
        
        def fail():
            raise RuntimeError("Service error")
        
        # Fail twice
        for _ in range(2):
            try:
                breaker.call(fail)
            except RuntimeError:
                pass
        
        assert breaker.state == "open"
    
    def test_open_circuit_rejects_calls(self):
        """Open circuit rejects new calls"""
        breaker = CircuitBreaker(failure_threshold=1)
        
        def fail():
            raise RuntimeError("Service error")
        
        # Trigger circuit open
        try:
            breaker.call(fail)
        except RuntimeError:
            pass
        
        # Next call should be rejected immediately
        def succeed():
            return "success"
        
        with pytest.raises(RuntimeError, match="circuit is OPEN"):
            breaker.call(succeed)
    
    def test_recovery_attempt(self):
        """Circuit attempts recovery after timeout"""
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.1
        )
        
        def fail():
            raise RuntimeError("Service error")
        
        # Trigger circuit open
        try:
            breaker.call(fail)
        except RuntimeError:
            pass
        
        assert breaker.state == "open"
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        def succeed():
            return "success"
        
        # Circuit should be half-open and attempt call
        result = breaker.call(succeed)
        assert result == "success"
        assert breaker.state == "closed"


class TestConnectionPool:
    """Test connection pool functionality"""
    
    def test_get_connection(self):
        """Get connection from pool"""
        def create_conn():
            return object()  # Mock connection
        
        pool = ConnectionPool(create_conn, pool_size=3)
        conn = pool.get_connection()
        
        assert conn is not None
        assert len(pool.in_use_connections) == 1
    
    def test_return_connection(self):
        """Return connection to pool"""
        def create_conn():
            return object()
        
        pool = ConnectionPool(create_conn, pool_size=3)
        conn = pool.get_connection()
        pool.return_connection(conn)
        
        assert len(pool.available_connections) == 1
        assert len(pool.in_use_connections) == 0
    
    def test_pool_exhaustion(self):
        """Raises error when pool exhausted"""
        def create_conn():
            return object()
        
        pool = ConnectionPool(create_conn, pool_size=2)
        
        # Get all connections
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        
        # Next get should timeout
        with pytest.raises(TimeoutError):
            pool.get_connection(timeout=0.1)
    
    def test_pool_reuse(self):
        """Connections are reused from pool"""
        def create_conn():
            return object()
        
        pool = ConnectionPool(create_conn, pool_size=3)
        
        # Get and return same connection
        conn1 = pool.get_connection()
        conn_id1 = id(conn1)
        pool.return_connection(conn1)
        
        # Get again - should be same object
        conn2 = pool.get_connection()
        conn_id2 = id(conn2)
        
        assert conn_id1 == conn_id2
        assert pool.telemetry['connections_created'] == 1


def test_integration_with_session_database():
    """Test retry policy integration with SessionDatabase"""
    from empirica.data.session_database import SessionDatabase
    
    db = SessionDatabase()
    
    # Verify retry policy initialized
    assert db.retry_policy is not None
    assert db.retry_policy.max_retries == 5
    
    # Verify telemetry available
    telemetry = db.retry_policy.get_telemetry()
    assert 'total_attempts' in telemetry
    assert telemetry['strategy'] == 'exponential'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
