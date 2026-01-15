"""
Historical Data Backfill for Epistemic Prediction

Retroactively extracts trajectory data from existing git notes and SQLite.
Bootstraps the prediction system with historical patterns.

STATUS: Stub - Implementation pending

DATA SOURCES (Priority Order):
1. Git Notes (PRIMARY - richest data):
   - refs/notes/empirica/session/{session_id}/{PHASE}/{round}
   - Contains: vectors, learning_delta, meta, git_state, timestamps
   - ~1168 phase records available (470 PREFLIGHT, 266 CHECK, 432 POSTFLIGHT)

2. SQLite (SECONDARY - structured queries):
   - session_findings: 578 records with impact scores
   - session_unknowns: 111 records with resolution status
   - sessions: 600+ sessions across multiple AI IDs
   - epistemic_snapshots: 138 POSTFLIGHT snapshots

3. Git Commit Trailers (TERTIARY - commit-level metadata):
   - Epistemic-* trailers on commits
   - Learning/Mastery/Uncertainty deltas
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import subprocess
import json


@dataclass
class HistoricalEpistemic:
    """Raw epistemic record from SQLite"""
    id: str
    session_id: str
    phase: str  # PREFLIGHT, CHECK, POSTFLIGHT
    vectors: Dict[str, float]
    reasoning: str
    timestamp: float
    project_id: Optional[str] = None


@dataclass
class BackfillStats:
    """Statistics from backfill operation"""
    sessions_processed: int
    epistemics_found: int
    trajectories_created: int
    patterns_detected: Dict[str, int]  # pattern_name -> count
    date_range: Tuple[float, float]  # min, max timestamps


@dataclass
class GitNoteEpistemic:
    """Epistemic record from git notes (richer than SQLite)"""
    session_id: str
    phase: str  # PREFLIGHT, CHECK, POSTFLIGHT
    round_num: int
    timestamp: str
    vectors: Dict[str, float]
    overall_confidence: float
    meta: Dict  # decision, reasoning, gaps, cycle
    learning_delta: Optional[Dict[str, Dict[str, float]]] = None
    git_state: Optional[Dict] = None
    token_count: int = 0


class HistoricalBackfill:
    """
    Extracts and transforms historical epistemic data into trajectories.

    Primary source: Git notes (refs/notes/empirica/session/*)
    Secondary source: SQLite (session_findings, session_unknowns)

    Usage:
        backfill = HistoricalBackfill(repo_path)
        stats = backfill.scan_available_data()
        trajectories = backfill.extract_trajectories(min_phases=2)
        backfill.populate_trajectory_store(trajectories)
    """

    def __init__(self, repo_path: Path = None, db_path: Path = None):
        self.repo_path = repo_path or Path.cwd()
        self.db_path = db_path or self.repo_path / ".empirica" / "sessions" / "sessions.db"
        # TODO: Initialize trajectory tracker connection

    def list_git_note_refs(self, phase_filter: str = None) -> List[str]:
        """
        List all epistemic session refs from git notes.

        Returns refs like: refs/notes/empirica/session/{session_id}/{PHASE}/{round}
        """
        cmd = ["git", "for-each-ref", "refs/notes/empirica/session", "--format=%(refname)"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
        refs = result.stdout.strip().split('\n') if result.stdout.strip() else []

        if phase_filter:
            refs = [r for r in refs if f"/{phase_filter}/" in r]

        return refs

    def read_git_note(self, ref: str) -> Optional[GitNoteEpistemic]:
        """
        Read and parse a single git note into GitNoteEpistemic.

        Git notes store JSON blobs with full epistemic state.
        """
        # List note attachments: "blob_sha commit_sha"
        cmd = ["git", "notes", f"--ref={ref}", "list"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)

        if not result.stdout.strip():
            return None

        blob_sha = result.stdout.strip().split()[0]

        # Read blob content
        cmd = ["git", "cat-file", "-p", blob_sha]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)

        if not result.stdout.strip():
            return None

        try:
            data = json.loads(result.stdout)
            return GitNoteEpistemic(
                session_id=data.get("session_id", ""),
                phase=data.get("phase", ""),
                round_num=data.get("round", 1),
                timestamp=data.get("timestamp", ""),
                vectors=data.get("vectors", {}),
                overall_confidence=data.get("overall_confidence", 0.0),
                meta=data.get("meta", {}),
                learning_delta=data.get("learning_delta"),
                git_state=data.get("git_state"),
                token_count=data.get("token_count", 0),
            )
        except json.JSONDecodeError:
            return None

    def extract_from_git_notes(
        self,
        phase_filter: str = None
    ) -> List[GitNoteEpistemic]:
        """
        Extract all epistemic records from git notes.

        This is the primary extraction method - git notes contain
        the richest epistemic data including vectors, deltas, and context.
        """
        refs = self.list_git_note_refs(phase_filter)
        records = []

        for ref in refs:
            record = self.read_git_note(ref)
            if record:
                records.append(record)

        return records

    def scan_available_data(self) -> BackfillStats:
        """
        Scan SQLite for available historical data.
        Returns statistics about what can be backfilled.
        """
        # TODO: Implement data scanning
        raise NotImplementedError("Backfill implementation pending")

    def extract_epistemics(
        self,
        project_id: str = None,
        min_timestamp: float = None,
        max_timestamp: float = None
    ) -> List[HistoricalEpistemic]:
        """
        Extract raw epistemic records from SQLite.

        Query: SELECT * FROM epistemics
               WHERE project_id = ? AND timestamp BETWEEN ? AND ?
               ORDER BY session_id, timestamp
        """
        # TODO: Implement extraction
        raise NotImplementedError("Backfill implementation pending")

    def group_by_session(
        self,
        epistemics: List[HistoricalEpistemic]
    ) -> Dict[str, List[HistoricalEpistemic]]:
        """Group epistemics by session_id for trajectory construction"""
        # TODO: Implement grouping
        raise NotImplementedError("Backfill implementation pending")

    def construct_trajectory(
        self,
        session_epistemics: List[HistoricalEpistemic]
    ):
        """
        Convert session epistemics into a Trajectory object.
        Requires at least PREFLIGHT + one other phase.
        """
        # TODO: Import and use TrajectoryTracker
        raise NotImplementedError("Backfill implementation pending")

    def extract_trajectories(
        self,
        project_id: str = None,
        min_phases: int = 2
    ) -> List:
        """
        Extract all valid trajectories from historical data.

        Args:
            project_id: Filter to specific project (None = all)
            min_phases: Minimum phases required (default: 2)

        Returns:
            List of Trajectory objects
        """
        # TODO: Implement full extraction pipeline
        raise NotImplementedError("Backfill implementation pending")

    def analyze_historical_patterns(
        self,
        trajectories: List
    ) -> Dict[str, int]:
        """
        Run pattern detection on historical trajectories.
        Returns pattern frequency counts.
        """
        # TODO: Implement pattern analysis
        raise NotImplementedError("Backfill implementation pending")

    def extract_concept_relationships(
        self,
        project_id: str = None
    ) -> List[Tuple[str, str, float]]:
        """
        Extract concept co-occurrences from findings/unknowns.

        Returns list of (concept_a, concept_b, co_occurrence_strength)
        based on session proximity.
        """
        # TODO: Implement concept extraction
        raise NotImplementedError("Backfill implementation pending")

    def extract_discovery_sequences(
        self,
        project_id: str = None
    ) -> List:
        """
        Extract unknown→finding sequences from historical data.

        Logic:
        - Find unknowns that were later resolved
        - Track the epistemic journey between them
        - Build DiscoverySequence objects
        """
        # TODO: Implement sequence extraction
        raise NotImplementedError("Backfill implementation pending")

    def populate_trajectory_store(
        self,
        trajectories: List,
        overwrite: bool = False
    ) -> int:
        """
        Populate the trajectory tracking store with historical data.

        Args:
            trajectories: List of Trajectory objects
            overwrite: If True, replace existing data

        Returns:
            Number of trajectories stored
        """
        # TODO: Implement storage population
        raise NotImplementedError("Backfill implementation pending")

    def run_full_backfill(
        self,
        project_id: str = None,
        dry_run: bool = True
    ) -> BackfillStats:
        """
        Run complete backfill pipeline:
        1. Scan available data
        2. Extract trajectories
        3. Analyze patterns
        4. Extract concept relationships
        5. Extract discovery sequences
        6. Populate stores (if not dry_run)

        Args:
            project_id: Filter to project (None = all)
            dry_run: If True, analyze but don't store

        Returns:
            Statistics about the backfill
        """
        # TODO: Implement full pipeline
        raise NotImplementedError("Backfill implementation pending")


# SQL queries for data extraction (using actual table names)
EXTRACTION_QUERIES = {
    "epistemic_snapshots": """
        SELECT snapshot_id, session_id, ai_id, cascade_phase, vectors,
               delta, context_summary, timestamp, fidelity_score
        FROM epistemic_snapshots
        WHERE (:ai_id IS NULL OR ai_id = :ai_id)
        ORDER BY session_id, timestamp
    """,
    "session_findings": """
        SELECT id, session_id, finding, impact, timestamp, goal_id
        FROM session_findings
        WHERE 1=1
        ORDER BY timestamp
    """,
    "session_unknowns": """
        SELECT id, session_id, unknown, resolved, resolved_by, timestamp
        FROM session_unknowns
        WHERE 1=1
        ORDER BY timestamp
    """,
    "sessions": """
        SELECT session_id, ai_id, project_id, start_time, created_at
        FROM sessions
        WHERE (:ai_id IS NULL OR ai_id = :ai_id)
        ORDER BY created_at
    """,
    "cascades": """
        SELECT cascade_id, session_id, task, goal_id,
               preflight_completed, check_completed, postflight_completed,
               final_confidence, started_at, completed_at
        FROM cascades
        WHERE (:session_id IS NULL OR session_id = :session_id)
        ORDER BY started_at
    """,
}


# CLI integration point
def cli_backfill_command():
    """
    CLI: empirica prediction-backfill --project-id <ID> [--dry-run]

    Backfills trajectory data from historical epistemics.
    """
    # TODO: Implement CLI command
    pass
