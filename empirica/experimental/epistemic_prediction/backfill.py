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
        Scan git notes and SQLite for available historical data.
        Returns statistics about what can be backfilled.
        """
        # Count git note refs by phase
        all_refs = self.list_git_note_refs()
        preflight_refs = self.list_git_note_refs("PREFLIGHT")
        check_refs = self.list_git_note_refs("CHECK")
        postflight_refs = self.list_git_note_refs("POSTFLIGHT")

        # Extract all records to get session count and date range
        records = self.extract_from_git_notes()

        # Get unique sessions
        sessions = set(r.session_id for r in records)

        # Get date range from timestamps
        timestamps = []
        for r in records:
            try:
                # Parse ISO timestamp
                from datetime import datetime
                ts = datetime.fromisoformat(r.timestamp.replace('Z', '+00:00'))
                timestamps.append(ts.timestamp())
            except (ValueError, AttributeError):
                pass

        date_range = (min(timestamps), max(timestamps)) if timestamps else (0.0, 0.0)

        return BackfillStats(
            sessions_processed=len(sessions),
            epistemics_found=len(records),
            trajectories_created=0,  # Not yet created
            patterns_detected={
                "PREFLIGHT": len(preflight_refs),
                "CHECK": len(check_refs),
                "POSTFLIGHT": len(postflight_refs),
            },
            date_range=date_range,
        )

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
        records: List[GitNoteEpistemic]
    ) -> Dict[str, List[GitNoteEpistemic]]:
        """Group epistemic records by session_id for trajectory construction"""
        from collections import defaultdict

        grouped = defaultdict(list)
        for record in records:
            grouped[record.session_id].append(record)

        # Sort each session's records by timestamp
        for session_id in grouped:
            grouped[session_id].sort(key=lambda r: r.timestamp)

        return dict(grouped)

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
        ai_id_filter: str = None,
        min_phases: int = 2
    ) -> List['Trajectory']:
        """
        Extract all valid trajectories from historical git notes.

        Args:
            ai_id_filter: Filter to specific AI ID (None = all)
            min_phases: Minimum phases required (default: 2)

        Returns:
            List of Trajectory objects
        """
        from .trajectory_tracker import Trajectory, VectorSnapshot, TrajectoryPattern

        # Extract all records
        records = self.extract_from_git_notes()

        # Group by session
        grouped = self.group_by_session(records)

        trajectories = []
        for session_id, session_records in grouped.items():
            # Filter by minimum phases
            if len(session_records) < min_phases:
                continue

            # Convert to VectorSnapshots
            snapshots = []
            for record in session_records:
                # Parse timestamp to float
                try:
                    from datetime import datetime
                    ts = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00'))
                    timestamp_float = ts.timestamp()
                except (ValueError, AttributeError):
                    timestamp_float = 0.0

                snapshot = VectorSnapshot(
                    session_id=record.session_id,
                    timestamp=timestamp_float,
                    phase=record.phase,
                    vectors=record.vectors,
                    concept_tags=list(record.meta.get("gaps", [])) if record.meta else [],
                    reasoning=record.meta.get("reasoning", "") if record.meta else None,
                )
                snapshots.append(snapshot)

            # Create trajectory
            trajectory = Trajectory(
                trajectory_id=f"traj_{session_id[:8]}",
                session_id=session_id,
                snapshots=snapshots,
                pattern=TrajectoryPattern.UNKNOWN,
                pattern_confidence=0.0,
                phase_detected=None,
            )
            trajectories.append(trajectory)

        return trajectories

    def analyze_historical_patterns(
        self,
        trajectories: List['Trajectory'] = None
    ) -> Dict[str, int]:
        """
        Run pattern detection on historical trajectories.
        Updates trajectories in database and returns pattern frequency counts.

        Pattern Detection Rules:
        - BREAKTHROUGH: know increases significantly (>0.2), uncertainty drops (>0.15)
        - DEAD_END: know stagnates or decreases, uncertainty stays high (>0.5)
        - STABLE: gradual improvement, low uncertainty throughout
        - OSCILLATING: know fluctuates up/down across phases
        """
        import sqlite3
        from .trajectory_tracker import TrajectoryPattern

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Load all trajectories with their snapshots
        cursor.execute("""
            SELECT t.trajectory_id, t.session_id, t.snapshot_count,
                   t.start_vectors, t.end_vectors, t.vector_deltas
            FROM vector_trajectories t
            WHERE t.snapshot_count >= 2
        """)

        pattern_counts = {p.value: 0 for p in TrajectoryPattern}
        updates = []

        for row in cursor.fetchall():
            traj_id = row[0]
            start_vectors = json.loads(row[3]) if row[3] else {}
            end_vectors = json.loads(row[4]) if row[4] else {}
            deltas = json.loads(row[5]) if row[5] else {}

            # Extract key metrics
            start_know = start_vectors.get('know', 0.5)
            end_know = end_vectors.get('know', 0.5)
            start_uncertainty = start_vectors.get('uncertainty', 0.5)
            end_uncertainty = end_vectors.get('uncertainty', 0.5)

            delta_know = deltas.get('know', 0)
            delta_uncertainty = deltas.get('uncertainty', 0)

            # Pattern detection
            pattern = TrajectoryPattern.UNKNOWN
            confidence = 0.0

            # BREAKTHROUGH: Big know gain + uncertainty drop
            if delta_know > 0.2 and delta_uncertainty < -0.15:
                pattern = TrajectoryPattern.BREAKTHROUGH
                confidence = min(1.0, (delta_know + abs(delta_uncertainty)) / 0.5)

            # DEAD_END: Know stagnates/drops + high uncertainty persists
            elif delta_know <= 0.05 and end_uncertainty > 0.5:
                pattern = TrajectoryPattern.DEAD_END
                confidence = min(1.0, end_uncertainty)

            # STABLE: Gradual improvement, low uncertainty
            elif delta_know > 0 and end_uncertainty < 0.3:
                pattern = TrajectoryPattern.STABLE
                confidence = min(1.0, (1 - end_uncertainty) * 0.8 + delta_know)

            # OSCILLATING: Small net change but likely fluctuation
            elif abs(delta_know) < 0.1 and abs(delta_uncertainty) < 0.1:
                pattern = TrajectoryPattern.OSCILLATING
                confidence = 0.5

            pattern_counts[pattern.value] += 1
            updates.append((pattern.value, confidence, traj_id))

        # Update database
        cursor.executemany("""
            UPDATE vector_trajectories
            SET pattern = ?, pattern_confidence = ?, analyzed_at = CURRENT_TIMESTAMP
            WHERE trajectory_id = ?
        """, updates)

        conn.commit()
        conn.close()

        return pattern_counts

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
        trajectories: List['Trajectory'],
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
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if overwrite:
            cursor.execute("DELETE FROM trajectory_snapshots")
            cursor.execute("DELETE FROM vector_trajectories")

        stored = 0
        for traj in trajectories:
            # Calculate summary data
            start_vectors = traj.snapshots[0].vectors if traj.snapshots else {}
            end_vectors = traj.snapshots[-1].vectors if traj.snapshots else {}

            first_ts = traj.snapshots[0].timestamp if traj.snapshots else 0
            last_ts = traj.snapshots[-1].timestamp if traj.snapshots else 0
            duration = last_ts - first_ts

            # Calculate deltas (only for numeric values)
            deltas = {}
            for key in start_vectors:
                if key in end_vectors:
                    sv = start_vectors[key]
                    ev = end_vectors[key]
                    if isinstance(sv, (int, float)) and isinstance(ev, (int, float)):
                        deltas[key] = ev - sv

            # Insert trajectory
            cursor.execute("""
                INSERT OR REPLACE INTO vector_trajectories
                (trajectory_id, session_id, snapshot_count, first_timestamp,
                 last_timestamp, duration_seconds, pattern, pattern_confidence,
                 phase_detected, start_vectors, end_vectors, vector_deltas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                traj.trajectory_id,
                traj.session_id,
                len(traj.snapshots),
                first_ts,
                last_ts,
                duration,
                traj.pattern.value if traj.pattern else 'unknown',
                traj.pattern_confidence,
                traj.phase_detected,
                json.dumps(start_vectors),
                json.dumps(end_vectors),
                json.dumps(deltas),
            ))

            # Insert snapshots
            for snapshot in traj.snapshots:
                cursor.execute("""
                    INSERT INTO trajectory_snapshots
                    (trajectory_id, session_id, phase, round_num, timestamp,
                     engagement, know, do_vector, context, clarity, coherence,
                     signal, density, state, change, completion, impact, uncertainty,
                     vectors_json, concept_tags, reasoning)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    traj.trajectory_id,
                    snapshot.session_id,
                    snapshot.phase,
                    1,  # round_num
                    snapshot.timestamp,
                    snapshot.vectors.get('engagement'),
                    snapshot.vectors.get('know'),
                    snapshot.vectors.get('do'),
                    snapshot.vectors.get('context'),
                    snapshot.vectors.get('clarity'),
                    snapshot.vectors.get('coherence'),
                    snapshot.vectors.get('signal'),
                    snapshot.vectors.get('density'),
                    snapshot.vectors.get('state'),
                    snapshot.vectors.get('change'),
                    snapshot.vectors.get('completion'),
                    snapshot.vectors.get('impact'),
                    snapshot.vectors.get('uncertainty'),
                    json.dumps(snapshot.vectors),
                    json.dumps(snapshot.concept_tags),
                    snapshot.reasoning,
                ))

            stored += 1

        conn.commit()
        conn.close()
        return stored

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
