#!/usr/bin/env python3
"""
Auto Issue Capture System

Automatically captures bugs, errors, warnings, and other issues during work
without interrupting flow state. Issues can be handed off to other AIs.

Architecture:
  - Hooks into logging system
  - Captures context (stack trace, code location, variables)
  - Stores in SQLite + Git for portability
  - Exposes handoff API for other AIs

Benefits:
  - Maintain continuous work flow
  - Enable seamless AI-to-AI handoffs
  - Build audit trail of issues and resolutions
  - Pattern discovery across sessions
"""

import json
import logging
import sqlite3
import traceback
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import inspect
import sys

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Issue severity levels"""
    BLOCKER = "blocker"      # Prevents work
    HIGH = "high"            # Significantly impacts work
    MEDIUM = "medium"        # Notable but workaround possible
    LOW = "low"              # Minor or cosmetic


class IssueCategory(Enum):
    """Issue categories for classification"""
    BUG = "bug"                        # Code defect
    ERROR = "error"                    # Runtime error
    WARNING = "warning"                # Potential problem
    DEPRECATION = "deprecation"        # Deprecated API/pattern
    TODO = "todo"                      # Incomplete work
    PERFORMANCE = "performance"        # Performance issue
    COMPATIBILITY = "compatibility"    # Platform/version issue
    DESIGN = "design"                  # Architectural issue
    OTHER = "other"


class IssueStatus(Enum):
    """Issue status lifecycle"""
    NEW = "new"                    # Just captured
    INVESTIGATING = "investigating"  # AI working on it
    HANDOFF = "handoff"            # Ready for other AI
    RESOLVED = "resolved"          # Fixed
    WONTFIX = "wontfix"            # Intentional/acceptable


class AutoIssueCaptureService:
    """
    Central service for capturing and managing auto-discovered issues.
    
    Integrates with logging system to capture errors/warnings without
    interrupting work flow. Enables handoff to other AIs with full context.
    """
    
    def __init__(self, session_id: str, db_path: Optional[str] = None, enable: bool = True):
        """
        Initialize issue capture service.
        
        Args:
            session_id: Current session ID for tracking
            db_path: Path to SQLite database (uses session DB by default)
            enable: Whether to enable auto-capture
        """
        self.session_id = session_id
        self.enable = enable
        self.db_path = Path(db_path) if db_path else self._get_default_db_path()
        
        # Create table if needed
        self._ensure_schema()
        
        # Issue stats for this session
        self._issue_count = 0
        self._handoff_ready_count = 0
    
    @staticmethod
    def _get_default_db_path() -> Path:
        """Get default database path from session DB"""
        from empirica.config.path_resolver import get_session_db_path
        return get_session_db_path()
    
    def _ensure_schema(self) -> None:
        """Create auto_captured_issues table if it doesn't exist"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auto_captured_issues (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    code_location TEXT,
                    message TEXT NOT NULL,
                    stack_trace TEXT,
                    context TEXT,
                    status TEXT DEFAULT 'new',
                    assigned_to_ai TEXT,
                    root_cause_id TEXT,
                    resolution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Create index for fast lookup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_issues_session_status
                ON auto_captured_issues(session_id, status)
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to create issues table: {e}")
    
    def capture_error(
        self,
        message: str,
        severity: IssueSeverity = IssueSeverity.HIGH,
        category: IssueCategory = IssueCategory.ERROR,
        context: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ) -> str:
        """
        Capture an error/exception without raising it.
        
        Args:
            message: Error description
            severity: How critical is this issue?
            category: What type of issue?
            context: Additional context (locals, state, etc.)
            exc_info: Exception object if applicable
            
        Returns:
            Issue ID for tracking
        """
        if not self.enable:
            return ""
        
        # Get code location from caller
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        code_location = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
        
        # Capture stack trace if exception provided
        stack_trace = None
        if exc_info:
            stack_trace = "".join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))
        else:
            stack_trace = "".join(traceback.format_stack(caller_frame))
        
        # Capture context if provided, otherwise try to get locals
        if context is None:
            context = self._extract_safe_context(caller_frame.f_locals)
        
        # Create issue record
        issue_id = str(uuid.uuid4())
        issue = {
            "id": issue_id,
            "session_id": self.session_id,
            "severity": severity.value,
            "category": category.value,
            "code_location": code_location,
            "message": message,
            "stack_trace": stack_trace,
            "context": json.dumps(context),
            "status": IssueStatus.NEW.value,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store in database
        self._store_issue(issue)
        
        # Log for monitoring
        logger.info(f"Auto-captured issue {issue_id}: {message} ({category.value}/{severity.value})")
        
        self._issue_count += 1
        return issue_id
    
    def capture_assertion_failure(
        self,
        condition: str,
        message: str = "",
        severity: IssueSeverity = IssueSeverity.MEDIUM
    ) -> str:
        """
        Capture assertion failure without interrupting flow.
        
        Usage:
            if not expected_condition:
                auto_capture.capture_assertion_failure("expected_condition", "Why it matters")
        """
        full_message = f"Assertion failed: {condition}. {message}" if message else f"Assertion failed: {condition}"
        return self.capture_error(
            message=full_message,
            severity=severity,
            category=IssueCategory.BUG
        )
    
    def capture_performance_issue(
        self,
        operation: str,
        actual_ms: float,
        expected_ms: float,
        severity: IssueSeverity = IssueSeverity.MEDIUM
    ) -> str:
        """
        Capture performance degradation.
        
        Args:
            operation: What operation was slow?
            actual_ms: Actual time in milliseconds
            expected_ms: Expected/acceptable time in milliseconds
        """
        message = f"Performance issue: {operation} took {actual_ms:.1f}ms (expected <{expected_ms:.1f}ms)"
        return self.capture_error(
            message=message,
            severity=severity,
            category=IssueCategory.PERFORMANCE
        )
    
    def capture_warning(
        self,
        message: str,
        category: IssueCategory = IssueCategory.WARNING,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Capture a warning without raising"""
        return self.capture_error(
            message=message,
            severity=IssueSeverity.LOW,
            category=category,
            context=context
        )
    
    def capture_todo(self, description: str, priority: str = "medium") -> str:
        """Capture incomplete work for later"""
        message = f"TODO ({priority}): {description}"
        severity_map = {"high": IssueSeverity.HIGH, "medium": IssueSeverity.MEDIUM, "low": IssueSeverity.LOW}
        return self.capture_error(
            message=message,
            severity=severity_map.get(priority, IssueSeverity.MEDIUM),
            category=IssueCategory.TODO
        )
    
    def _extract_safe_context(self, locals_dict: Dict[str, Any]) -> Dict[str, str]:
        """Extract safe context from locals (avoid sensitive/large objects)"""
        safe_context = {}
        
        for key, value in locals_dict.items():
            # Skip private/system variables
            if key.startswith("_"):
                continue
            
            # Only capture simple types and limit size
            if isinstance(value, (str, int, float, bool, type(None))):
                safe_context[key] = str(value)[:200]  # Limit string length
            elif isinstance(value, (list, dict)):
                try:
                    safe_context[key] = str(value)[:500]
                except:
                    pass
        
        return safe_context
    
    def _store_issue(self, issue: Dict[str, Any]) -> None:
        """Store issue in SQLite database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO auto_captured_issues
                (id, session_id, severity, category, code_location, message, stack_trace, context, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue["id"],
                issue["session_id"],
                issue["severity"],
                issue["category"],
                issue["code_location"],
                issue["message"],
                issue["stack_trace"],
                issue["context"],
                issue["status"],
                issue["created_at"],
                issue["created_at"]
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to store issue: {e}")
    
    def list_issues(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List captured issues with optional filtering.
        
        Args:
            status: Filter by status (new, investigating, handoff, resolved, wontfix)
            category: Filter by category
            severity: Filter by severity
            limit: Maximum results
            
        Returns:
            List of issue dictionaries
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM auto_captured_issues WHERE session_id = ?"
            params = [self.session_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            if category:
                query += " AND category = ?"
                params.append(category)
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            issues = []
            for row in rows:
                issues.append(dict(row))
            
            conn.close()
            return issues
        except Exception as e:
            logger.warning(f"Failed to list issues: {e}")
            return []
    
    def mark_for_handoff(self, issue_id: str, assigned_to_ai: str) -> bool:
        """
        Mark issue as ready for handoff to another AI.
        
        Args:
            issue_id: Issue to hand off
            assigned_to_ai: AI ID to receive the issue
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE auto_captured_issues
                SET status = ?, assigned_to_ai = ?, updated_at = ?
                WHERE id = ? AND session_id = ?
            """, (
                IssueStatus.HANDOFF.value,
                assigned_to_ai,
                datetime.now(timezone.utc).isoformat(),
                issue_id,
                self.session_id
            ))
            
            conn.commit()
            conn.close()
            
            self._handoff_ready_count += 1
            return True
        except Exception as e:
            logger.warning(f"Failed to mark issue for handoff: {e}")
            return False
    
    def resolve_issue(self, issue_id: str, resolution: str) -> bool:
        """
        Mark issue as resolved with explanation.
        
        Args:
            issue_id: Issue that was fixed
            resolution: How it was resolved
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE auto_captured_issues
                SET status = ?, resolution = ?, updated_at = ?
                WHERE id = ? AND session_id = ?
            """, (
                IssueStatus.RESOLVED.value,
                resolution,
                datetime.now(timezone.utc).isoformat(),
                issue_id,
                self.session_id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"Failed to resolve issue: {e}")
            return False
    
    def export_for_handoff(self, assigned_to_ai: str) -> Dict[str, Any]:
        """
        Export all issues assigned to another AI in portable format.
        
        Perfect for passing to another AI agent with full context.
        """
        # Get all handoff issues for this AI
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM auto_captured_issues
                WHERE session_id = ? AND status = ? AND assigned_to_ai = ?
                ORDER BY created_at DESC
            """, (self.session_id, "handoff", assigned_to_ai))
            
            rows = cursor.fetchall()
            issues = [dict(row) for row in rows]
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to export issues: {e}")
            issues = []
        
        return {
            "from_session": self.session_id,
            "assigned_to_ai": assigned_to_ai,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "issue_count": len(issues),
            "issues": issues
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get capture statistics for this session"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM auto_captured_issues
                WHERE session_id = ?
                GROUP BY status
            """, (self.session_id,))
            
            stats = {"session_id": self.session_id}
            for row in cursor.fetchall():
                stats[f"{row[0]}_count"] = row[1]
            
            conn.close()
            return stats
        except Exception as e:
            logger.warning(f"Failed to get stats: {e}")
            return {"session_id": self.session_id, "error": str(e)}


# Global instance for easy access
_auto_capture_instance: Optional[AutoIssueCaptureService] = None


def initialize_auto_capture(session_id: str, enable: bool = True) -> AutoIssueCaptureService:
    """Initialize the global auto-capture service"""
    global _auto_capture_instance
    _auto_capture_instance = AutoIssueCaptureService(session_id, enable=enable)
    return _auto_capture_instance


def get_auto_capture() -> Optional[AutoIssueCaptureService]:
    """Get the global auto-capture service instance"""
    return _auto_capture_instance
