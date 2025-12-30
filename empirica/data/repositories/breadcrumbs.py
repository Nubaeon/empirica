"""
Breadcrumb Repository

Manages knowledge artifacts: findings, unknowns, dead ends, mistakes, and reference docs.
These breadcrumbs enable session continuity and learning transfer across AI agents.
"""

import json
import logging
import time
import uuid
from typing import Dict, List, Optional

from .base import BaseRepository

logger = logging.getLogger(__name__)


class BreadcrumbRepository(BaseRepository):
    """Repository for knowledge artifact management (breadcrumbs for continuity)"""

    def log_finding(
        self,
        project_id: str,
        session_id: str,
        finding: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: Optional[float] = None
    ) -> str:
        """Log a project finding (what was learned/discovered)

        Args:
            impact: Impact score 0.0-1.0 (importance). If None, defaults to 0.5.
        """
        finding_id = str(uuid.uuid4())

        if impact is None:
            impact = 0.5

        finding_data = {
            "finding": finding,
            "goal_id": goal_id,
            "subtask_id": subtask_id,
            "impact": impact,
            "timestamp": time.time()
        }

        self._execute("""
            INSERT INTO project_findings (
                id, project_id, session_id, goal_id, subtask_id,
                finding, created_timestamp, finding_data, subject, impact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding_id, project_id, session_id, goal_id, subtask_id,
            finding, time.time(), json.dumps(finding_data), subject, impact
        ))

        self.commit()
        logger.info(f"📝 Finding logged: {finding[:50]}...")

        return finding_id

    def log_unknown(
        self,
        project_id: str,
        session_id: str,
        unknown: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: Optional[float] = None
    ) -> str:
        """Log a project unknown (what's still unclear)

        Args:
            impact: Impact score 0.0-1.0 (importance). If None, defaults to 0.5.
        """
        unknown_id = str(uuid.uuid4())

        if impact is None:
            impact = 0.5

        unknown_data = {
            "unknown": unknown,
            "goal_id": goal_id,
            "subtask_id": subtask_id,
            "impact": impact,
            "timestamp": time.time()
        }

        self._execute("""
            INSERT INTO project_unknowns (
                id, project_id, session_id, goal_id, subtask_id,
                unknown, created_timestamp, unknown_data, subject, impact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            unknown_id, project_id, session_id, goal_id, subtask_id,
            unknown, time.time(), json.dumps(unknown_data), subject, impact
        ))

        self.commit()
        logger.info(f"❓ Unknown logged: {unknown[:50]}...")

        return unknown_id

    def resolve_unknown(self, unknown_id: str, resolved_by: str):
        """Mark an unknown as resolved"""
        self._execute("""
            UPDATE project_unknowns
            SET is_resolved = TRUE, resolved_by = ?, resolved_timestamp = ?
            WHERE id = ?
        """, (resolved_by, time.time(), unknown_id))

        self.commit()
        logger.info(f"✅ Unknown resolved: {unknown_id[:8]}...")

    def log_dead_end(
        self,
        project_id: str,
        session_id: str,
        approach: str,
        why_failed: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: float = 0.5
    ) -> str:
        """Log a project dead end (what didn't work)

        Args:
            impact: Impact score 0.0-1.0 (importance). Default 0.5 if not provided.
        """
        dead_end_id = str(uuid.uuid4())

        dead_end_data = {
            "approach": approach,
            "why_failed": why_failed,
            "goal_id": goal_id,
            "subtask_id": subtask_id,
            "impact": impact,
            "timestamp": time.time()
        }

        self._execute("""
            INSERT INTO project_dead_ends (
                id, project_id, session_id, goal_id, subtask_id,
                approach, why_failed, created_timestamp, dead_end_data, subject
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dead_end_id, project_id, session_id, goal_id, subtask_id,
            approach, why_failed, time.time(), json.dumps(dead_end_data), subject
        ))

        self.commit()
        logger.info(f"💀 Dead end logged: {approach[:50]}...")

        return dead_end_id

    # ========================================================================
    # SESSION-SCOPED BREADCRUMBS (Dual-Scope Phase 1)
    # ========================================================================
    
    def log_session_finding(
        self,
        session_id: str,
        finding: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: Optional[float] = None
    ) -> str:
        """Log a session-scoped finding (ephemeral, session-specific learning)"""
        finding_id = str(uuid.uuid4())

        if impact is None:
            impact = 0.5

        finding_data = {
            "finding": finding,
            "goal_id": goal_id,
            "subtask_id": subtask_id,
            "impact": impact,
            "timestamp": time.time()
        }

        self._execute("""
            INSERT INTO session_findings (
                id, session_id, goal_id, subtask_id,
                finding, created_timestamp, finding_data, subject, impact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding_id, session_id, goal_id, subtask_id,
            finding, time.time(), json.dumps(finding_data), subject, impact
        ))

        self.commit()
        logger.info(f"📝 Session finding logged: {finding[:50]}...")

        return finding_id
    
    def log_session_unknown(
        self,
        session_id: str,
        unknown: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: Optional[float] = None
    ) -> str:
        """Log a session-scoped unknown (what's still unclear in this session)"""
        unknown_id = str(uuid.uuid4())

        if impact is None:
            impact = 0.5

        unknown_data = {
            "unknown": unknown,
            "goal_id": goal_id,
            "subtask_id": subtask_id,
            "impact": impact,
            "timestamp": time.time()
        }

        self._execute("""
            INSERT INTO session_unknowns (
                id, session_id, goal_id, subtask_id,
                unknown, is_resolved, created_timestamp, unknown_data, subject, impact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            unknown_id, session_id, goal_id, subtask_id,
            unknown, False, time.time(), json.dumps(unknown_data), subject, impact
        ))

        self.commit()
        logger.info(f"❓ Session unknown logged: {unknown[:50]}...")

        return unknown_id
    
    def log_session_dead_end(
        self,
        session_id: str,
        approach: str,
        why_failed: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: float = 0.5
    ) -> str:
        """Log a session-scoped dead end (what didn't work in this session)"""
        dead_end_id = str(uuid.uuid4())

        dead_end_data = {
            "approach": approach,
            "why_failed": why_failed,
            "goal_id": goal_id,
            "subtask_id": subtask_id,
            "impact": impact,
            "timestamp": time.time()
        }

        self._execute("""
            INSERT INTO session_dead_ends (
                id, session_id, goal_id, subtask_id,
                approach, why_failed, created_timestamp, dead_end_data, subject
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dead_end_id, session_id, goal_id, subtask_id,
            approach, why_failed, time.time(), json.dumps(dead_end_data), subject
        ))

        self.commit()
        logger.info(f"💀 Session dead end logged: {approach[:50]}...")

        return dead_end_id
    
    def log_session_mistake(
        self,
        session_id: str,
        mistake: str,
        why_wrong: str,
        cost_estimate: Optional[str] = None,
        root_cause_vector: Optional[str] = None,
        prevention: Optional[str] = None,
        goal_id: Optional[str] = None
    ) -> str:
        """Log a session-scoped mistake (learning from failures in this session)"""
        mistake_id = str(uuid.uuid4())

        mistake_data = {
            "mistake": mistake,
            "why_wrong": why_wrong,
            "cost_estimate": cost_estimate,
            "root_cause_vector": root_cause_vector,
            "prevention": prevention,
            "goal_id": goal_id,
            "timestamp": time.time()
        }

        self._execute("""
            INSERT INTO session_mistakes (
                id, session_id, goal_id, mistake, why_wrong,
                cost_estimate, root_cause_vector, prevention,
                created_timestamp, mistake_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mistake_id, session_id, goal_id, mistake, why_wrong,
            cost_estimate, root_cause_vector, prevention,
            time.time(), json.dumps(mistake_data)
        ))

        self.commit()
        logger.info(f"🔴 Session mistake logged: {mistake[:50]}...")

        return mistake_id

    def add_reference_doc(
        self,
        project_id: str,
        doc_path: str,
        doc_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Add a reference document to project"""
        doc_id = str(uuid.uuid4())

        doc_data = {
            "doc_path": doc_path,
            "doc_type": doc_type,
            "description": description
        }

        self._execute("""
            INSERT INTO project_reference_docs (
                id, project_id, doc_path, doc_type, description,
                created_timestamp, doc_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id, project_id, doc_path, doc_type, description,
            time.time(), json.dumps(doc_data)
        ))

        self.commit()
        logger.info(f"📄 Reference doc added: {doc_path}")

        return doc_id

    def get_project_findings(
        self,
        project_id: str,
        limit: Optional[int] = None,
        subject: Optional[str] = None,
        depth: str = "moderate",
        uncertainty: Optional[float] = None
    ) -> List[Dict]:
        """
        Get findings for a project with deprecation filtering (DUAL-SCOPE).
        Aggregates findings from both session_findings (across all sessions) and project_findings.
        
        Args:
            project_id: Project identifier
            limit: Optional limit on results (applied after filtering)
            subject: Optional subject filter
            depth: Relevance depth ("minimal", "moderate", "full", "complete", "auto")
            uncertainty: Epistemic uncertainty (for auto-depth, 0.0-1.0)
            
        Returns:
            Filtered list of findings from both scopes
        """
        # Query findings from BOTH project_findings and session_findings (across all sessions in project)
        if subject:
            query = """
                SELECT id, session_id, goal_id, subtask_id, finding, created_timestamp, finding_data, subject, impact, project_id, 'project' as scope 
                FROM project_findings 
                WHERE project_id = ? AND subject = ? 
                UNION ALL
                SELECT f.id, f.session_id, f.goal_id, f.subtask_id, f.finding, f.created_timestamp, f.finding_data, f.subject, f.impact, s.project_id, 'session' as scope 
                FROM session_findings f
                JOIN sessions s ON f.session_id = s.session_id
                WHERE s.project_id = ? AND f.subject = ?
                ORDER BY created_timestamp DESC
            """
            params = (project_id, subject, project_id, subject)
        else:
            query = """
                SELECT id, session_id, goal_id, subtask_id, finding, created_timestamp, finding_data, subject, impact, project_id, 'project' as scope 
                FROM project_findings 
                WHERE project_id = ? 
                UNION ALL
                SELECT f.id, f.session_id, f.goal_id, f.subtask_id, f.finding, f.created_timestamp, f.finding_data, f.subject, f.impact, s.project_id, 'session' as scope 
                FROM session_findings f
                JOIN sessions s ON f.session_id = s.session_id
                WHERE s.project_id = ?
                ORDER BY created_timestamp DESC
            """
            params = (project_id, project_id)
        
        cursor = self._execute(query, params)
        findings = [dict(row) for row in cursor.fetchall()]
        
        # Apply deprecation filtering
        from empirica.core.findings_deprecation import FindingsDeprecationEngine
        
        # Auto-depth based on uncertainty if requested
        if depth == "auto" and uncertainty is not None:
            if uncertainty > 0.5:
                depth = "full"
            elif uncertainty > 0.3:
                depth = "moderate"
            else:
                depth = "minimal"
        
        # Calculate relevance scores
        relevance_scores = [
            FindingsDeprecationEngine.calculate_relevance_score(f)
            for f in findings
        ]
        
        # Filter by depth
        filtered = FindingsDeprecationEngine.filter_by_depth(
            findings,
            depth=depth,
            relevance_scores=relevance_scores,
            uncertainty=uncertainty or 0.5
        )
        
        # Apply limit if specified
        if limit:
            filtered = filtered[:limit]
        
        return filtered

    def get_project_unknowns(self, project_id: str, resolved: Optional[bool] = None, subject: Optional[str] = None) -> List[Dict]:
        """Get unknowns for a project (DUAL-SCOPE: aggregates session + project unknowns)"""
        # Column list: id, session_id, goal_id, subtask_id, unknown, is_resolved, resolved_by, created_timestamp, resolved_timestamp, unknown_data, subject, impact, project_id, scope
        if subject:
            if resolved is None:
                cursor = self._execute("""
                    SELECT id, session_id, goal_id, subtask_id, unknown, is_resolved, resolved_by, created_timestamp, resolved_timestamp, unknown_data, subject, impact, project_id, 'project' as scope 
                    FROM project_unknowns
                    WHERE project_id = ? AND subject = ?
                    UNION ALL
                    SELECT u.id, u.session_id, u.goal_id, u.subtask_id, u.unknown, u.is_resolved, u.resolved_by, u.created_timestamp, u.resolved_timestamp, u.unknown_data, u.subject, u.impact, s.project_id, 'session' as scope 
                    FROM session_unknowns u
                    JOIN sessions s ON u.session_id = s.session_id
                    WHERE s.project_id = ? AND u.subject = ?
                    ORDER BY created_timestamp DESC
                """, (project_id, subject, project_id, subject))
            else:
                cursor = self._execute("""
                    SELECT id, session_id, goal_id, subtask_id, unknown, is_resolved, resolved_by, created_timestamp, resolved_timestamp, unknown_data, subject, impact, project_id, 'project' as scope 
                    FROM project_unknowns
                    WHERE project_id = ? AND subject = ? AND is_resolved = ?
                    UNION ALL
                    SELECT u.id, u.session_id, u.goal_id, u.subtask_id, u.unknown, u.is_resolved, u.resolved_by, u.created_timestamp, u.resolved_timestamp, u.unknown_data, u.subject, u.impact, s.project_id, 'session' as scope 
                    FROM session_unknowns u
                    JOIN sessions s ON u.session_id = s.session_id
                    WHERE s.project_id = ? AND u.subject = ? AND u.is_resolved = ?
                    ORDER BY created_timestamp DESC
                """, (project_id, subject, resolved, project_id, subject, resolved))
        else:
            if resolved is None:
                cursor = self._execute("""
                    SELECT id, session_id, goal_id, subtask_id, unknown, is_resolved, resolved_by, created_timestamp, resolved_timestamp, unknown_data, subject, impact, project_id, 'project' as scope 
                    FROM project_unknowns
                    WHERE project_id = ?
                    UNION ALL
                    SELECT u.id, u.session_id, u.goal_id, u.subtask_id, u.unknown, u.is_resolved, u.resolved_by, u.created_timestamp, u.resolved_timestamp, u.unknown_data, u.subject, u.impact, s.project_id, 'session' as scope 
                    FROM session_unknowns u
                    JOIN sessions s ON u.session_id = s.session_id
                    WHERE s.project_id = ?
                    ORDER BY created_timestamp DESC
                """, (project_id, project_id))
            else:
                cursor = self._execute("""
                    SELECT id, session_id, goal_id, subtask_id, unknown, is_resolved, resolved_by, created_timestamp, resolved_timestamp, unknown_data, subject, impact, project_id, 'project' as scope 
                    FROM project_unknowns
                    WHERE project_id = ? AND is_resolved = ?
                    UNION ALL
                    SELECT u.id, u.session_id, u.goal_id, u.subtask_id, u.unknown, u.is_resolved, u.resolved_by, u.created_timestamp, u.resolved_timestamp, u.unknown_data, u.subject, u.impact, s.project_id, 'session' as scope 
                    FROM session_unknowns u
                    JOIN sessions s ON u.session_id = s.session_id
                    WHERE s.project_id = ? AND u.is_resolved = ?
                    ORDER BY created_timestamp DESC
                """, (project_id, resolved, project_id, resolved))
        return [dict(row) for row in cursor.fetchall()]

    def get_project_dead_ends(self, project_id: str, limit: Optional[int] = None, subject: Optional[str] = None) -> List[Dict]:
        """Get all dead ends for a project (DUAL-SCOPE: aggregates session + project)"""
        # Column list: id, session_id, goal_id, subtask_id, approach, why_failed, created_timestamp, dead_end_data, subject, project_id, scope
        if subject:
            query = """
                SELECT id, session_id, goal_id, subtask_id, approach, why_failed, created_timestamp, dead_end_data, subject, project_id, 'project' as scope 
                FROM project_dead_ends WHERE project_id = ? AND subject = ?
                UNION ALL
                SELECT d.id, d.session_id, d.goal_id, d.subtask_id, d.approach, d.why_failed, d.created_timestamp, d.dead_end_data, d.subject, s.project_id, 'session' as scope 
                FROM session_dead_ends d
                JOIN sessions s ON d.session_id = s.session_id
                WHERE s.project_id = ? AND d.subject = ?
                ORDER BY created_timestamp DESC
            """
            params = (project_id, subject, project_id, subject)
        else:
            query = """
                SELECT id, session_id, goal_id, subtask_id, approach, why_failed, created_timestamp, dead_end_data, subject, project_id, 'project' as scope 
                FROM project_dead_ends WHERE project_id = ?
                UNION ALL
                SELECT d.id, d.session_id, d.goal_id, d.subtask_id, d.approach, d.why_failed, d.created_timestamp, d.dead_end_data, d.subject, s.project_id, 'session' as scope 
                FROM session_dead_ends d
                JOIN sessions s ON d.session_id = s.session_id
                WHERE s.project_id = ?
                ORDER BY created_timestamp DESC
            """
            params = (project_id, project_id)
        if limit:
            query += f" LIMIT {limit}"
        cursor = self._execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_project_reference_docs(self, project_id: str) -> List[Dict]:
        """Get all reference docs for a project"""
        cursor = self._execute("""
            SELECT * FROM project_reference_docs
            WHERE project_id = ?
            ORDER BY created_timestamp DESC
        """, (project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def log_mistake(
        self,
        session_id: str,
        mistake: str,
        why_wrong: str,
        cost_estimate: Optional[str] = None,
        root_cause_vector: Optional[str] = None,
        prevention: Optional[str] = None,
        goal_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Log a mistake for learning and future prevention.

        Args:
            session_id: Session identifier
            mistake: What was done wrong
            why_wrong: Explanation of why it was wrong
            cost_estimate: Estimated time/effort wasted (e.g., "2 hours")
            root_cause_vector: Epistemic vector that caused the mistake (e.g., "KNOW", "CONTEXT")
            prevention: How to prevent this mistake in the future
            goal_id: Optional goal identifier this mistake relates to

        Returns:
            mistake_id: UUID string
        """
        mistake_id = str(uuid.uuid4())

        # Build mistake_data JSON
        mistake_data = {
            "mistake": mistake,
            "why_wrong": why_wrong,
            "cost_estimate": cost_estimate,
            "root_cause_vector": root_cause_vector,
            "prevention": prevention
        }

        self._execute("""
            INSERT INTO mistakes_made (
                id, session_id, goal_id, project_id, mistake, why_wrong,
                cost_estimate, root_cause_vector, prevention,
                created_timestamp, mistake_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mistake_id, session_id, goal_id, project_id, mistake, why_wrong,
            cost_estimate, root_cause_vector, prevention,
            time.time(), json.dumps(mistake_data)
        ))

        self.commit()
        logger.info(f"📝 Mistake logged: {mistake[:50]}...")

        return mistake_id

    def get_mistakes(
        self,
        session_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve logged mistakes.

        Args:
            session_id: Optional filter by session
            goal_id: Optional filter by goal
            limit: Maximum number of results

        Returns:
            List of mistake dictionaries
        """
        if session_id and goal_id:
            cursor = self._execute("""
                SELECT * FROM mistakes_made
                WHERE session_id = ? AND goal_id = ?
                ORDER BY created_timestamp DESC
                LIMIT ?
            """, (session_id, goal_id, limit))
        elif session_id:
            cursor = self._execute("""
                SELECT * FROM mistakes_made
                WHERE session_id = ?
                ORDER BY created_timestamp DESC
                LIMIT ?
            """, (session_id, limit))
        elif goal_id:
            cursor = self._execute("""
                SELECT * FROM mistakes_made
                WHERE goal_id = ?
                ORDER BY created_timestamp DESC
                LIMIT ?
            """, (goal_id, limit))
        else:
            cursor = self._execute("""
                SELECT * FROM mistakes_made
                ORDER BY created_timestamp DESC
                LIMIT ?
            """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_project_mistakes(self, project_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get mistakes for a project (uses direct project_id column)"""
        query = """
            SELECT mistake, prevention, cost_estimate, root_cause_vector, created_timestamp
            FROM mistakes_made
            WHERE project_id = ?
            ORDER BY created_timestamp DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor = self._execute(query, (project_id,))
        return [dict(row) for row in cursor.fetchall()]
