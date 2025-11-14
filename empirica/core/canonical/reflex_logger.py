"""
Reflex Frame Logger

Provides temporal logging of epistemic assessments to prevent self-referential recursion.

Key Principle: Temporal Separation
- Current pass: Perform assessment, log to JSON
- Next pass: Read logged frames, act on historical data
- This prevents the AI from modifying its own reasoning mid-stream

Architecture:
- ReflexFrames logged to JSON files with timestamps
- Organized by agent_id and date
- Async I/O for non-blocking logging
- Historical frame retrieval for context building
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC, date
import aiofiles

from .reflex_frame import ReflexFrame, EpistemicAssessment

logger = logging.getLogger(__name__)

class ReflexLogger:
    """
    Temporal logger for Reflex Frames

    Logs epistemic assessments to JSON files, enabling temporal separation
    between current reasoning and historical analysis.
    """

    def __init__(self, base_log_dir: str = ".empirica_reflex_logs"):
        """
        Initialize logger

        Args:
            base_log_dir: Root directory for all reflex logs
                         Default: .empirica_reflex_logs (hidden, project-local)
        """
        self.base_log_dir = Path(base_log_dir)
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        """Create log directory structure if it doesn't exist"""
        self.base_log_dir.mkdir(parents=True, exist_ok=True)

    def _get_agent_log_dir(
        self, 
        agent_id: str, 
        session_id: Optional[str] = None,
        log_date: date = None
    ) -> Path:
        """
        Get log directory for specific agent, date, and session

        Directory structure: .empirica_reflex_logs/{YYYY-MM-DD}/{agent_id}/{session_id}/
        
        Args:
            agent_id: AI identifier (e.g., "minimax", "claude", "gpt4")
            session_id: Session UUID (optional, for session-specific logs)
            log_date: Date for log organization (default: today)
        
        Returns:
            Path to log directory
        
        Benefits of date-first structure:
        - Easy to find recent work (sort by date)
        - Easy to cleanup old logs (remove date directories)
        - Still grouped by AI and session within each date
        """
        if log_date is None:
            log_date = date.today()

        if session_id:
            # With session: {date}/{agent_id}/{session_id}/
            agent_dir = self.base_log_dir / log_date.isoformat() / agent_id / session_id
        else:
            # Without session: {date}/{agent_id}/
            agent_dir = self.base_log_dir / log_date.isoformat() / agent_id
        
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    def _generate_log_filename(self, frame_id: str) -> str:
        """
        Generate timestamped log filename

        Format: {frame_id}_{timestamp}.json
        Example: assess_abc123_20251027T153045.json
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        return f"{frame_id}_{timestamp}.json"

    async def log_frame(
        self,
        frame: ReflexFrame,
        agent_id: str = "default",
        session_id: Optional[str] = None
    ) -> Path:
        """
        Log a ReflexFrame to JSON file

        Args:
            frame: ReflexFrame to log
            agent_id: Agent identifier for organizing logs
            session_id: Session UUID for session-specific organization

        Returns:
            Path to logged file

        Example:
            logger = ReflexLogger()
            frame = ReflexFrame.from_assessment(assessment, frame_id="assess_001")
            log_path = await logger.log_frame(
                frame, 
                agent_id="minimax",
                session_id="abc-123-def"
            )
        """
        log_dir = self._get_agent_log_dir(agent_id, session_id)
        filename = self._generate_log_filename(frame.frame_id)
        log_path = log_dir / filename

        # Serialize frame to JSON
        frame_json = frame.to_json(indent=2)

        # Write async to avoid blocking
        async with aiofiles.open(log_path, 'w') as f:
            await f.write(frame_json)

        return log_path

    def log_frame_sync(
        self,
        frame: ReflexFrame,
        agent_id: str = "default",
        session_id: Optional[str] = None
    ) -> Path:
        """
        Synchronous version of log_frame for non-async contexts

        Args:
            frame: ReflexFrame to log
            agent_id: Agent identifier
            session_id: Session UUID for session-specific organization

        Returns:
            Path to logged file
        """
        log_dir = self._get_agent_log_dir(agent_id, session_id)
        filename = self._generate_log_filename(frame.frame_id)
        log_path = log_dir / filename

        # Write synchronously
        with open(log_path, 'w') as f:
            f.write(frame.to_json(indent=2))

        return log_path

    async def get_recent_frames(
        self,
        agent_id: str = "default",
        limit: int = 10,
        log_date: date = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent ReflexFrames for an agent

        Args:
            agent_id: Agent identifier
            limit: Maximum number of frames to retrieve
            log_date: Specific date to query (default: today)

        Returns:
            List of frame dictionaries (most recent first)

        Purpose: Enables historical context building without self-modification
        """
        log_dir = self._get_agent_log_dir(agent_id, log_date)

        # Get all JSON files sorted by modification time (newest first)
        log_files = sorted(
            log_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]

        frames = []
        for log_file in log_files:
            async with aiofiles.open(log_file, 'r') as f:
                content = await f.read()
                frame_data = json.loads(content)
                frames.append(frame_data)

        return frames

    def get_recent_frames_sync(
        self,
        agent_id: str = "default",
        limit: int = 10,
        log_date: date = None
    ) -> List[Dict[str, Any]]:
        """
        Synchronous version of get_recent_frames

        Args:
            agent_id: Agent identifier
            limit: Maximum number of frames to retrieve
            log_date: Specific date to query (default: today)

        Returns:
            List of frame dictionaries (most recent first)
        """
        log_dir = self._get_agent_log_dir(agent_id, log_date)

        log_files = sorted(
            log_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]

        frames = []
        for log_file in log_files:
            with open(log_file, 'r') as f:
                frame_data = json.load(f)
                frames.append(frame_data)

        return frames

    async def get_frames_by_action(
        self,
        action: str,
        agent_id: str = "default",
        limit: int = 10,
        log_date: date = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve frames filtered by recommended action

        Args:
            action: Action to filter by (e.g., "investigate", "clarify")
            agent_id: Agent identifier
            limit: Maximum frames to retrieve
            log_date: Specific date (default: today)

        Returns:
            List of frames with matching action (most recent first)

        Use Case: Analyze patterns in investigation triggers or clarifications
        """
        all_frames = await self.get_recent_frames(agent_id, limit=limit*2, log_date=log_date)

        # Filter by action
        matching_frames = [
            frame for frame in all_frames
            if frame.get('recommendedAction') == action
        ][:limit]

        return matching_frames

    def get_assessment_history(
        self,
        agent_id: str = "default",
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get assessment history across multiple days

        Args:
            agent_id: Agent identifier
            days: Number of days to look back

        Returns:
            List of all frames from the past N days

        Use Case: Calibration analysis, pattern detection, learning
        """
        all_frames = []
        today = date.today()

        for day_offset in range(days):
            target_date = today - timedelta(days=day_offset)
            day_frames = self.get_recent_frames_sync(
                agent_id,
                limit=1000,  # Get all frames for the day
                log_date=target_date
            )
            all_frames.extend(day_frames)

        return all_frames

    def cleanup_old_logs(self, agent_id: str = "default", days_to_keep: int = 30):
        """
        Remove logs older than specified days

        Args:
            agent_id: Agent identifier
            days_to_keep: Number of days of logs to retain

        Note: Be cautious - this permanently deletes historical calibration data
        """
        agent_base_dir = self.base_log_dir / agent_id

        if not agent_base_dir.exists():
            return

        cutoff_date = date.today() - timedelta(days=days_to_keep)

        # Iterate through date directories
        for date_dir in agent_base_dir.iterdir():
            if not date_dir.is_dir():
                continue

            try:
                # Parse directory name as date (YYYY-MM-DD format)
                dir_date = date.fromisoformat(date_dir.name)

                if dir_date < cutoff_date:
                    # Remove entire date directory
                    import shutil
                    shutil.rmtree(date_dir)
                    logger.info(f"Removed old logs: {date_dir}")

            except (ValueError, OSError) as e:
                # Skip directories that don't match date format or can't be removed
                logger.info(f"Skipping {date_dir}: {e}")


# CONVENIENCE FUNCTIONS

async def log_assessment(
    assessment: EpistemicAssessment,
    frame_id: str,
    task: str = "",
    context: Dict[str, Any] = None,
    agent_id: str = "default",
    logger: Optional[ReflexLogger] = None
) -> Path:
    """
    Convenience function to log an assessment

    Args:
        assessment: EpistemicAssessment to log
        frame_id: Unique frame identifier
        task: Task description
        context: Additional context
        agent_id: Agent identifier
        logger: ReflexLogger instance (creates default if None)

    Returns:
        Path to logged file

    Example:
        assessment = await canonical_assessor.assess(task, context)
        log_path = await log_assessment(
            assessment,
            frame_id="cascade_001",
            task=task,
            context=context,
            agent_id="metacognitive_cascade"
        )
    """
    if logger is None:
        logger = ReflexLogger()

    frame = ReflexFrame.from_assessment(
        assessment,
        frame_id=frame_id,
        task=task,
        context=context or {}
    )

    return await logger.log_frame(frame, agent_id=agent_id)


def log_assessment_sync(
    assessment: EpistemicAssessment,
    frame_id: str,
    task: str = "",
    context: Dict[str, Any] = None,
    agent_id: str = "default",
    logger: Optional[ReflexLogger] = None
) -> Path:
    """
    Synchronous version of log_assessment

    See log_assessment for documentation.
    """
    if logger is None:
        logger = ReflexLogger()

    frame = ReflexFrame.from_assessment(
        assessment,
        frame_id=frame_id,
        task=task,
        context=context or {}
    )

    return logger.log_frame_sync(frame, agent_id=agent_id)


# Fix missing import
from datetime import timedelta
