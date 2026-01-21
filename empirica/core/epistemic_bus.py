#!/usr/bin/env python3
"""
Epistemic Bus - Simple event publishing for epistemic state changes

Philosophy:
- Empirica publishes epistemic events (no routing logic)
- External systems (Sentinels, MCO, plugins) can observe
- AI decides how to respond to observations
- Completely optional - Empirica works without it

Unix metaphor: System bus for epistemic events
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
import logging
import time

logger = logging.getLogger(__name__)


class EpistemicEvent:
    """
    Simple epistemic event structure
    
    Events are just data - no behavior, no routing logic
    """
    def __init__(
        self,
        event_type: str,
        agent_id: str,
        session_id: str,
        data: Dict[str, Any],
        timestamp: Optional[float] = None
    ) -> None:
        """Initialize epistemic event with type, agent, session, and data."""
        self.event_type = event_type
        self.agent_id = agent_id
        self.session_id = session_id
        self.data = data
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for logging/transmission"""
        return {
            'event_type': self.event_type,
            'agent_id': self.agent_id,
            'session_id': self.session_id,
            'data': self.data,
            'timestamp': self.timestamp
        }
    
    def __repr__(self):
        """Return string representation of epistemic event."""
        return f"EpistemicEvent({self.event_type}, agent={self.agent_id})"


class EpistemicObserver(ABC):
    """
    Interface for external systems that observe epistemic events
    
    Examples:
    - RoutingSentinel: Suggests routing based on epistemic state
    - MCO: Coordinates multiple agents
    - Monitor: Logs/visualizes epistemic patterns
    """
    
    @abstractmethod
    def handle_event(self, event: EpistemicEvent) -> None:
        """
        React to epistemic event
        
        Args:
            event: The epistemic event
            
        Note: Observers should be fast and non-blocking.
              Heavy processing should be async or queued.
        """
        pass


class EpistemicBus:
    """
    Simple pub/sub bus for epistemic events
    
    Design principles:
    - Synchronous and simple (no queues, no async complexity)
    - Observers are called in order
    - Errors in observers are logged but don't block
    - Optional - system works without any observers
    
    Usage:
        bus = EpistemicBus()
        bus.subscribe(MyObserver())
        bus.publish(EpistemicEvent('preflight_complete', ...))
    """
    
    def __init__(self, enable_logging: bool = True) -> None:
        """Initialize epistemic bus with optional logging."""
        self.observers: List[EpistemicObserver] = []
        self.enable_logging = enable_logging
        self._event_count = 0
    
    def subscribe(self, observer: EpistemicObserver) -> None:
        """
        Register an observer to receive epistemic events
        
        Args:
            observer: Observer instance implementing EpistemicObserver interface
        """
        if not isinstance(observer, EpistemicObserver):
            raise TypeError(f"Observer must implement EpistemicObserver, got {type(observer)}")
        
        self.observers.append(observer)
        logger.info(f"Registered observer: {observer.__class__.__name__}")
    
    def unsubscribe(self, observer: EpistemicObserver) -> None:
        """Remove an observer"""
        if observer in self.observers:
            self.observers.remove(observer)
            logger.info(f"Unregistered observer: {observer.__class__.__name__}")
    
    def publish(self, event: EpistemicEvent) -> None:
        """
        Publish an epistemic event to all observers
        
        Args:
            event: The epistemic event to publish
            
        Note: Observer errors are caught and logged but don't block other observers
        """
        self._event_count += 1
        
        if self.enable_logging:
            logger.debug(f"Publishing event: {event.event_type} (agent={event.agent_id})")
        
        # Notify all observers
        for observer in self.observers:
            try:
                observer.handle_event(event)
            except Exception as e:
                # Log error but continue to other observers
                logger.error(
                    f"Observer {observer.__class__.__name__} failed on event {event.event_type}: {e}",
                    exc_info=True
                )
    
    def get_observer_count(self) -> int:
        """Get number of registered observers"""
        return len(self.observers)
    
    def get_event_count(self) -> int:
        """Get total number of events published"""
        return self._event_count
    
    def clear_observers(self) -> None:
        """Remove all observers (useful for testing)"""
        self.observers.clear()
        logger.info("Cleared all observers")


# Standard epistemic event types (conventions, not enforced)
class EventTypes:
    """Standard event types published by Empirica components"""
    
    # CASCADE phase events
    PREFLIGHT_COMPLETE = "preflight_complete"
    INVESTIGATE_ROUND_COMPLETE = "investigate_round_complete"
    CHECK_COMPLETE = "check_complete"
    ACT_STARTED = "act_started"
    ACT_COMPLETE = "act_complete"
    POSTFLIGHT_COMPLETE = "postflight_complete"
    
    # Goal/Task events
    GOAL_DECISION_MADE = "goal_decision_made"  # CASCADE decision logic output
    GOAL_CREATED = "goal_created"
    GOAL_UPDATED = "goal_updated"
    GOAL_COMPLETED = "goal_completed"
    SUBTASK_CREATED = "subtask_created"
    SUBTASK_COMPLETED = "subtask_completed"
    
    # Session events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    
    # Calibration events
    CALIBRATION_COMPLETE = "calibration_complete"
    CALIBRATION_DRIFT_DETECTED = "calibration_drift_detected"
    
    # Alerts (for Sentinel to monitor)
    INVESTIGATION_SPINNING = "investigation_spinning"
    CONFIDENCE_DROPPED = "confidence_dropped"
    ENGAGEMENT_GATE_FAILED = "engagement_gate_failed"


class LoggingObserver(EpistemicObserver):
    """
    Simple observer that logs all events
    
    Useful for debugging and development
    """
    
    def __init__(self, log_level: int = logging.INFO):
        """Initialize logging observer with configurable log level."""
        self.log_level = log_level
    
    def handle_event(self, event: EpistemicEvent) -> None:
        """Log the event"""
        logger.log(
            self.log_level,
            f"[EpistemicBus] {event.event_type}: agent={event.agent_id}, session={event.session_id}"
        )


class CallbackObserver(EpistemicObserver):
    """
    Observer that calls a function for each event
    
    Useful for testing and simple integrations
    """
    
    def __init__(self, callback: Callable[[EpistemicEvent], None]):
        """Initialize callback observer with function to call for each event."""
        self.callback = callback
    
    def handle_event(self, event: EpistemicEvent) -> None:
        """Call the callback"""
        self.callback(event)


# Global bus instance (optional convenience)
_global_bus: Optional[EpistemicBus] = None


def get_global_bus() -> EpistemicBus:
    """Get or create the global epistemic bus"""
    global _global_bus
    if _global_bus is None:
        _global_bus = EpistemicBus()
    return _global_bus


def set_global_bus(bus: Optional[EpistemicBus]) -> None:
    """Set the global epistemic bus (useful for testing)"""
    global _global_bus
    _global_bus = bus
