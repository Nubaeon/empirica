#!/usr/bin/env python3
"""
Auto-Tracking Wrapper for Empirica

Provides automatic session and epistemic tracking for AIs using Empirica.
Can be used standalone or integrated into bootstraps/MCP servers.

Key Features:
- Automatic session creation on first use
- Context manager for cascade tracking
- Decorator for function-level tracking
- Simple API for manual tracking

Usage Examples:

1. Context Manager (Recommended):
    from empirica.auto_tracker import EmpericaTracker
    
    async with EmpericaTracker("my_task") as tracker:
        # Your code here
        result = await do_something()
        tracker.log_assessment(my_assessment)
        
2. Decorator:
    @track_empirica("task_name")
    async def my_function():
        # Automatically tracked
        pass
        
3. Manual:
    tracker = EmpericaTracker.get_instance()
    tracker.start_cascade("my_task")
    # ... work ...
    tracker.log_assessment(assessment)
    tracker.end_cascade()
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime
from pathlib import Path
import sys

# Set up logging for auto_tracker
logger = logging.getLogger(__name__)

# Ensure empirica is in path
empirica_root = Path(__file__).parent.parent
if str(empirica_root) not in sys.path:
    sys.path.insert(0, str(empirica_root))

from empirica.data.session_database import SessionDatabase
from empirica.core.canonical.reflex_frame import EpistemicAssessment, Action

# Optional JSON export
try:
    from empirica.data.session_json_handler import SessionJSONHandler
    JSON_EXPORT_AVAILABLE = True
except ImportError:
    JSON_EXPORT_AVAILABLE = False

# Optional reflex logging for tmux dashboard
try:
    from empirica.core.canonical.reflex_logger import ReflexLogger
    REFLEX_LOGGING_AVAILABLE = True
except ImportError:
    REFLEX_LOGGING_AVAILABLE = False


class EmpericaTracker:
    """
    Singleton auto-tracker for Empirica sessions and cascades
    
    Automatically creates and manages:
    - Sessions (per AI instance)
    - Cascades (per task/operation)
    - Epistemic assessments (per decision point)
    """
    
    _instance: Optional['EmpericaTracker'] = None
    
    def __init__(self, ai_id: str = "default_ai", bootstrap_level: int = 2, auto_init: bool = True, 
                 export_json: bool = True, enable_reflex_logs: bool = True):
        """
        Initialize tracker
        
        Args:
            ai_id: AI identifier (e.g., "claude", "gpt4", "gemini")
            bootstrap_level: Which bootstrap level is active (0-4)
            auto_init: Automatically create session on init
            export_json: Auto-export session to JSON on cascade completion
            enable_reflex_logs: Enable reflex frame logging for tmux dashboard
        """
        self.ai_id = ai_id
        self.bootstrap_level = bootstrap_level
        self.db = SessionDatabase()
        self.export_json = export_json and JSON_EXPORT_AVAILABLE
        self.enable_reflex_logs = enable_reflex_logs and REFLEX_LOGGING_AVAILABLE
        
        # JSON handler
        self.json_handler = None
        if self.export_json:
            self.json_handler = SessionJSONHandler()
        
        # Reflex logger for tmux dashboard
        self.reflex_logger = None
        if self.enable_reflex_logs:
            self.reflex_logger = ReflexLogger()
        
        # Session state
        self.session_id: Optional[str] = None
        self.current_cascade_id: Optional[str] = None
        self.cascade_start_time: Optional[float] = None
        self.cascade_count = 0
        self.assessment_count = 0
        
        # Auto-initialize session if requested
        if auto_init:
            self.start_session()
    
    @property
    def session_db(self) -> SessionDatabase:
        """Expose database instance for compatibility"""
        return self.db
    
    @classmethod
    def get_instance(cls, ai_id: str = "default_ai", bootstrap_level: int = 2) -> 'EmpericaTracker':
        """
        Get or create singleton instance
        
        Args:
            ai_id: AI identifier
            bootstrap_level: Bootstrap level (0-4)
            
        Returns:
            EmpericaTracker instance
        """
        if cls._instance is None:
            cls._instance = cls(ai_id, bootstrap_level)
        return cls._instance
    
    def start_session(self, components_loaded: int = 0) -> str:
        """
        Start a new Empirica session
        
        Args:
            components_loaded: Number of components loaded in bootstrap
            
        Returns:
            session_id
        """
        if self.session_id is None:
            self.session_id = self.db.create_session(
                ai_id=self.ai_id,
                bootstrap_level=self.bootstrap_level,
                components_loaded=components_loaded
            )
            logger.info(f"📊 Empirica session started: {self.session_id}")
        return self.session_id
    
    def end_session(self, avg_confidence: Optional[float] = None):
        """
        End current session
        
        Args:
            avg_confidence: Average confidence across all cascades
        """
        if self.session_id:
            self.db.end_session(
                session_id=self.session_id,
                avg_confidence=avg_confidence,
                drift_detected=False  # Could be enhanced with drift detection
            )
            logger.info(f"📊 Empirica session ended: {self.session_id}")
            self.session_id = None
    
    def start_cascade(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new cascade (task/operation)
        
        Args:
            task: Task description
            context: Additional context
            
        Returns:
            cascade_id
        """
        # Ensure session exists
        if self.session_id is None:
            self.start_session()
        
        # Create cascade
        import time
        self.cascade_start_time = time.time()
        self.current_cascade_id = self.db.create_cascade(
            session_id=self.session_id,
            task=task,
            context=context or {}
        )
        self.cascade_count += 1
        
        logger.info(f"🔄 Cascade started: {task[:50]}...")
        return self.current_cascade_id
    
    def end_cascade(self, final_action: Action = Action.PROCEED, 
                    final_confidence: float = 0.7,
                    investigation_rounds: int = 0):
        """
        End current cascade
        
        Args:
            final_action: Final decision made
            final_confidence: Final confidence level
            investigation_rounds: Number of investigation rounds performed
        """
        if self.current_cascade_id:
            import time
            # Calculate duration
            duration_ms = 0
            if self.cascade_start_time:
                duration_ms = int((time.time() - self.cascade_start_time) * 1000)
            
            self.db.complete_cascade(
                cascade_id=self.current_cascade_id,
                final_action=final_action.value if isinstance(final_action, Action) else final_action,
                final_confidence=final_confidence,
                investigation_rounds=investigation_rounds,
                duration_ms=duration_ms,
                engagement_gate_passed=True,
                bayesian_active=False,
                drift_monitored=False
            )
            logger.info(f"✅ Cascade completed: {final_action} (duration: {duration_ms}ms)")
            
            # Auto-export to JSON if enabled
            if self.export_json and self.json_handler and self.session_id:
                try:
                    export_path = self.json_handler.export_session(self.db, self.session_id)
                    logger.info(f"📤 Session exported: {export_path}")
                except Exception as e:
                    logger.warning(f"⚠️  JSON export failed: {e}")
            
            self.current_cascade_id = None
            self.cascade_start_time = None
    
    def log_assessment(self, assessment: EpistemicAssessment, phase: str = "uncertainty"):
        """
        Log an epistemic assessment
        
        Args:
            assessment: EpistemicAssessment object with all 13 vectors
            phase: Cascade phase (think, uncertainty, investigate, check, act)
        """
        if self.current_cascade_id is None:
            logger.warning("⚠️  No active cascade - starting one automatically")
            self.start_cascade(assessment.task or "auto-tracked task")
        
        # Log to database
        self.db.log_epistemic_assessment(
            cascade_id=self.current_cascade_id,
            assessment=assessment,
            phase=phase
        )
        self.assessment_count += 1
        
        logger.info(f"📝 Assessment logged: phase={phase}, confidence={assessment.overall_confidence:.2f}, uncertainty={assessment.uncertainty.score:.2f}")
        
        # Also log to reflex logger for tmux dashboard
        if self.enable_reflex_logs and self.reflex_logger:
            try:
                import asyncio
                # Log assessment directly using reflex logger
                assessment_data = {
                    'assessment_id': assessment.assessment_id,
                    'task': assessment.task if hasattr(assessment, 'task') else 'auto-tracked',
                    'phase': phase,
                    'session_id': self.session_id,
                    'cascade_id': self.current_cascade_id,
                    'ai_id': self.ai_id,
                    'cascade_count': self.cascade_count,
                    'self_aware_flag': True,  # Always true for auto-tracked assessments
                    'assessment': assessment
                }
                # Log assessment data directly
                asyncio.create_task(self.reflex_logger.log_assessment(self.session_id, assessment_data))
                logger.info(f"📊 Assessment logged for tmux dashboard (phase={phase})")
            except Exception as e:
                import traceback
                logger.warning(f"⚠️  Reflex logging failed: {e}")
                # traceback.print_exc()  # Uncomment for debugging
    
    def update_phase(self, phase: str, completed: bool = True):
        """
        Update cascade phase status
        
        Args:
            phase: Phase name (think, uncertainty, investigate, check, act)
            completed: Whether phase is completed
        """
        if self.current_cascade_id:
            self.db.update_cascade_phase(
                cascade_id=self.current_cascade_id,
                phase=phase,
                completed=completed
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get tracking statistics
        
        Returns:
            Dict with session statistics
        """
        return {
            'session_id': self.session_id,
            'ai_id': self.ai_id,
            'cascade_count': self.cascade_count,
            'assessment_count': self.assessment_count,
            'active_cascade': self.current_cascade_id is not None
        }
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.current_cascade_id:
            # Auto-end cascade on context exit
            action = Action.PROCEED if exc_type is None else Action.STOP
            self.end_cascade(final_action=action)
        return False
    
    def __enter__(self):
        """Sync context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit"""
        if self.current_cascade_id:
            action = Action.PROCEED if exc_type is None else Action.STOP
            self.end_cascade(final_action=action)
        return False


# Convenience function for context manager usage
def track_cascade(task: str, context: Optional[Dict[str, Any]] = None, 
                  ai_id: str = "default_ai") -> EmpericaTracker:
    """
    Create a tracking context for a cascade
    
    Usage:
        async with track_cascade("my task") as tracker:
            # Your code here
            tracker.log_assessment(assessment)
    
    Args:
        task: Task description
        context: Additional context
        ai_id: AI identifier
        
    Returns:
        EmpericaTracker context manager
    """
    tracker = EmpericaTracker.get_instance(ai_id)
    tracker.start_cascade(task, context)
    return tracker


# Decorator for automatic function tracking
def track_empirica(task_name: Optional[str] = None, ai_id: str = "default_ai"):
    """
    Decorator to automatically track a function with Empirica
    
    Usage:
        @track_empirica("process data")
        async def process_data(data):
            # Automatically tracked
            return result
    
    Args:
        task_name: Task description (uses function name if None)
        ai_id: AI identifier
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            task = task_name or func.__name__
            tracker = EmpericaTracker.get_instance(ai_id)
            tracker.start_cascade(task)
            
            try:
                result = await func(*args, **kwargs)
                tracker.end_cascade(final_action=Action.PROCEED)
                return result
            except Exception as e:
                tracker.end_cascade(final_action=Action.STOP, final_confidence=0.0)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            task = task_name or func.__name__
            tracker = EmpericaTracker.get_instance(ai_id)
            tracker.start_cascade(task)
            
            try:
                result = func(*args, **kwargs)
                tracker.end_cascade(final_action=Action.PROCEED)
                return result
            except Exception as e:
                tracker.end_cascade(final_action=Action.STOP, final_confidence=0.0)
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("  EMPIRICA AUTO-TRACKER DEMO")
    print("=" * 70)
    print()
    
    # Example 1: Manual tracking
    print("Example 1: Manual Tracking")
    print("-" * 70)
    tracker = EmpericaTracker.get_instance("demo_ai", bootstrap_level=2)
    cascade_id = tracker.start_cascade("Demo task", {"demo": True})
    
    # Simulate assessment
    from empirica.core.canonical.reflex_frame import VectorState
    import uuid
    
    assessment = EpistemicAssessment(
        assessment_id=f"demo_{uuid.uuid4().hex[:12]}",
        task="Demo task",
        engagement=VectorState(0.8, "High engagement"),
        engagement_gate_passed=True,
        know=VectorState(0.6, "Moderate knowledge"),
        do=VectorState(0.7, "Can execute"),
        context=VectorState(0.8, "Good context"),
        foundation_confidence=0.7,
        clarity=VectorState(0.9, "Clear task"),
        coherence=VectorState(0.9, "Coherent"),
        signal=VectorState(0.8, "Good signal"),
        density=VectorState(0.4, "Manageable"),
        comprehension_confidence=0.8,
        state=VectorState(0.7, "Ready"),
        change=VectorState(0.8, "Can progress"),
        completion=VectorState(0.5, "Halfway"),
        impact=VectorState(0.6, "Medium impact"),
        execution_confidence=0.65,
        uncertainty=VectorState(0.3, "Low uncertainty - demo environment"),
        overall_confidence=0.72,
        recommended_action=Action.PROCEED
    )
    
    tracker.log_assessment(assessment, phase="uncertainty")
    tracker.end_cascade(Action.PROCEED, 0.72, 0)
    
    stats = tracker.get_stats()
    print(f"\nStats: {stats}")
    print()
    
    # Example 2: Context manager
    print("Example 2: Context Manager")
    print("-" * 70)
    
    async def demo_context_manager():
        async with track_cascade("Context manager task", ai_id="demo_ai") as t:
            print("Inside context manager")
            # Simulated work
            await asyncio.sleep(0.1)
        print("Context exited (cascade auto-ended)")
    
    asyncio.run(demo_context_manager())
    print()
    
    # Show final stats
    final_stats = tracker.get_stats()
    print(f"Final stats: {final_stats}")
    print()
    print("=" * 70)
    print("✅ Demo complete! Check database for tracked data.")
    print("=" * 70)
