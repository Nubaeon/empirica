"""
Connection pooling and retry policy for database resilience.

Implements:
- Connection pooling for multi-connection scenarios
- Exponential backoff with jitter for transient errors
- Circuit breaker pattern for cascading failures
- Observability via retry telemetry
"""

import time
import logging
from typing import Optional, Callable, Any, Dict
from enum import Enum
import sqlite3

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategies for different failure types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class RetryPolicy:
    """Exponential backoff retry policy with circuit breaker"""
    
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        jitter: bool = True
    ):
        """
        Initialize retry policy.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            strategy: Retry strategy (exponential, linear, fixed)
            jitter: Add randomness to prevent thundering herd
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.jitter = jitter
        self.retry_count = 0
        self.last_error = None
        self.telemetry: Dict[str, int] = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_retries': 0,
            'circuit_breaks': 0
        }
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        else:  # FIXED
            delay = self.base_delay
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter (±20% randomness)
        if self.jitter:
            import random
            jitter_amount = delay * 0.2
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0.001, delay)  # Ensure non-negative
    
    def should_retry(self, error: Exception) -> bool:
        """Determine if error is retryable"""
        retryable_errors = (
            sqlite3.OperationalError,  # Database locked, disk I/O
            sqlite3.IntegrityError,     # Constraint violations (might be transient)
            TimeoutError,
            ConnectionError,
            IOError
        )
        return isinstance(error, retryable_errors)
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func if successful
            
        Raises:
            Last exception if all retries exhausted
        """
        self.telemetry['total_attempts'] += 1
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    self.telemetry['successful_retries'] += 1
                    logger.info(f"✓ Retry succeeded after {attempt} attempt(s)")
                
                return result
                
            except Exception as e:
                self.last_error = e
                
                if not self.should_retry(e):
                    # Non-retryable error, fail immediately
                    logger.warning(f"✗ Non-retryable error: {type(e).__name__}: {e}")
                    raise
                
                if attempt >= self.max_retries:
                    # Out of retries
                    self.telemetry['failed_retries'] += 1
                    logger.error(f"✗ Failed after {self.max_retries} retries: {e}")
                    raise
                
                # Calculate delay and retry
                delay = self.calculate_delay(attempt)
                logger.warning(
                    f"⚠️  Attempt {attempt + 1}/{self.max_retries + 1} failed: {type(e).__name__}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
    
    def get_telemetry(self) -> Dict[str, Any]:
        """Get retry telemetry for observability"""
        return {
            **self.telemetry,
            'last_error': str(self.last_error) if self.last_error else None,
            'strategy': self.strategy.value,
            'max_retries': self.max_retries
        }


class ConnectionPool:
    """Simple connection pool for database resilience"""
    
    def __init__(
        self,
        connection_factory: Callable,
        pool_size: int = 5,
        enable_retry: bool = True
    ):
        """
        Initialize connection pool.
        
        Args:
            connection_factory: Function that creates connections
            pool_size: Number of connections to maintain
            enable_retry: Enable exponential backoff retry
        """
        self.connection_factory = connection_factory
        self.pool_size = pool_size
        self.enable_retry = enable_retry
        self.available_connections = []
        self.in_use_connections = set()
        self.retry_policy = RetryPolicy() if enable_retry else None
        self.telemetry: Dict[str, int] = {
            'connections_created': 0,
            'connections_recycled': 0,
            'pool_exhausted': 0
        }
    
    def get_connection(self, timeout: float = 5.0):
        """Get a connection from the pool"""
        start = time.time()
        
        while True:
            # Try to get available connection
            if self.available_connections:
                conn = self.available_connections.pop()
                self.in_use_connections.add(id(conn))
                logger.debug(f"✓ Got connection from pool (available: {len(self.available_connections)})")
                return conn
            
            # Create new connection if under limit
            if len(self.in_use_connections) < self.pool_size:
                conn = self.connection_factory()
                self.in_use_connections.add(id(conn))
                self.telemetry['connections_created'] += 1
                logger.debug(f"✓ Created new connection (total: {len(self.in_use_connections)})")
                return conn
            
            # Wait for connection to be released
            if time.time() - start > timeout:
                self.telemetry['pool_exhausted'] += 1
                raise TimeoutError(f"No connections available after {timeout}s")
            
            time.sleep(0.01)  # Brief sleep before retry
    
    def return_connection(self, conn):
        """Return connection to pool"""
        conn_id = id(conn)
        if conn_id in self.in_use_connections:
            self.in_use_connections.remove(conn_id)
            self.available_connections.append(conn)
            self.telemetry['connections_recycled'] += 1
            logger.debug(f"✓ Returned connection to pool (available: {len(self.available_connections)})")
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with connection from pool and retry logic"""
        if not self.enable_retry:
            return func(*args, **kwargs)
        
        return self.retry_policy.execute_with_retry(func, *args, **kwargs)
    
    def get_telemetry(self) -> Dict[str, Any]:
        """Get pool telemetry"""
        return {
            **self.telemetry,
            'available_connections': len(self.available_connections),
            'in_use_connections': len(self.in_use_connections),
            'retry_telemetry': self.retry_policy.get_telemetry() if self.retry_policy else None
        }


class CircuitBreaker:
    """Circuit breaker pattern for cascading failure prevention"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: str = "CircuitBreaker"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Time before attempting recovery
            name: Identifier for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        States:
        - closed: Normal operation, calls go through
        - open: Too many failures, calls rejected
        - half-open: Testing if service recovered
        """
        if self.state == "open":
            # Check if recovery timeout passed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"🔄 {self.name}: Attempting recovery (half-open)")
                self.state = "half-open"
            else:
                raise RuntimeError(f"{self.name} circuit is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            
            # Successful call - reset
            if self.state == "half-open":
                logger.info(f"✓ {self.name}: Recovery successful (closed)")
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"🚫 {self.name}: Circuit OPEN after {self.failure_count} failures"
                )
                self.state = "open"
            
            raise
