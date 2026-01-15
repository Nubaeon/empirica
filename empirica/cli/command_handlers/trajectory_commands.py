"""
Trajectory analysis command handlers (experimental).

Part of the epistemic prediction system for analyzing
vector trajectories and detecting patterns.

NOTE: Implementation moved to empirica-prediction package.
Install with: pip install empirica-prediction
"""

import json
import sqlite3
from pathlib import Path


def _get_historical_backfill():
    """Import HistoricalBackfill from empirica-prediction package."""
    try:
        from empirica_prediction.trajectory.backfill import HistoricalBackfill
        return HistoricalBackfill
    except ImportError:
        print("Error: empirica-prediction package not installed.")
        print("Install with: pip install empirica-prediction")
        print("Or from source: pip install -e /path/to/empirica-prediction")
        return None


def get_db_path():
    """Get the database path for trajectory data."""
    return Path.cwd() / ".empirica" / "sessions" / "sessions.db"


def handle_trajectory_show(args):
    """Show vector trajectories for sessions."""
    db_path = get_db_path()

    if not db_path.exists():
        print("No database found. Run 'empirica trajectory-backfill' first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Build query
    conditions = []
    params = []

    if args.session_id:
        conditions.append("session_id = ?")
        params.append(args.session_id)

    if args.pattern:
        conditions.append("pattern = ?")
        params.append(args.pattern)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    cursor.execute(f"""
        SELECT trajectory_id, session_id, snapshot_count, pattern,
               pattern_confidence, start_vectors, end_vectors, vector_deltas,
               duration_seconds
        FROM vector_trajectories
        WHERE {where_clause}
        ORDER BY pattern_confidence DESC
        LIMIT ?
    """, params + [args.limit])

    rows = cursor.fetchall()
    conn.close()

    if args.output == 'json':
        results = []
        for row in rows:
            results.append({
                "trajectory_id": row[0],
                "session_id": row[1],
                "snapshot_count": row[2],
                "pattern": row[3],
                "pattern_confidence": row[4],
                "start_vectors": json.loads(row[5]) if row[5] else {},
                "end_vectors": json.loads(row[6]) if row[6] else {},
                "vector_deltas": json.loads(row[7]) if row[7] else {},
                "duration_seconds": row[8],
            })
        print(json.dumps(results, indent=2))
    else:
        if not rows:
            print("No trajectories found matching criteria.")
            return

        print(f"\n{'='*60}")
        print(f"VECTOR TRAJECTORIES ({len(rows)} shown)")
        print(f"{'='*60}\n")

        for row in rows:
            traj_id = row[0]
            session_id = row[1]
            snapshots = row[2]
            pattern = row[3]
            confidence = row[4]
            start = json.loads(row[5]) if row[5] else {}
            end = json.loads(row[6]) if row[6] else {}
            deltas = json.loads(row[7]) if row[7] else {}

            # Pattern emoji
            pattern_emoji = {
                'breakthrough': '🚀',
                'stable': '📈',
                'dead_end': '🛑',
                'oscillating': '〰️',
                'unknown': '❓'
            }.get(pattern, '❓')

            print(f"{pattern_emoji} {pattern.upper()} (confidence: {confidence:.2f})")
            print(f"   Session: {session_id[:12]}...")
            print(f"   Snapshots: {snapshots}")

            # Key vector changes
            print(f"   Vectors:")
            for key in ['know', 'uncertainty', 'clarity', 'completion']:
                if key in start and key in end:
                    delta = deltas.get(key, 0)
                    direction = "↑" if delta > 0 else "↓" if delta < 0 else "→"
                    print(f"      {key}: {start[key]:.2f} {direction} {end[key]:.2f} ({delta:+.2f})")

            print()


def handle_trajectory_stats(args):
    """Show trajectory pattern statistics."""
    db_path = get_db_path()

    if not db_path.exists():
        print("No database found. Run 'empirica trajectory-backfill' first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get pattern counts
    cursor.execute("""
        SELECT pattern, COUNT(*), AVG(pattern_confidence)
        FROM vector_trajectories
        GROUP BY pattern
        ORDER BY COUNT(*) DESC
    """)
    pattern_stats = cursor.fetchall()

    # Get overall stats
    cursor.execute("SELECT COUNT(*), AVG(snapshot_count) FROM vector_trajectories")
    total, avg_snapshots = cursor.fetchone()

    # Get top breakthroughs
    cursor.execute("""
        SELECT trajectory_id,
               json_extract(vector_deltas, '$.know') as delta_know,
               json_extract(vector_deltas, '$.uncertainty') as delta_unc
        FROM vector_trajectories
        WHERE pattern = 'breakthrough'
        ORDER BY json_extract(vector_deltas, '$.know') DESC
        LIMIT 5
    """)
    top_breakthroughs = cursor.fetchall()

    conn.close()

    if args.output == 'json':
        print(json.dumps({
            "total_trajectories": total,
            "avg_snapshots": avg_snapshots,
            "patterns": {row[0]: {"count": row[1], "avg_confidence": row[2]} for row in pattern_stats},
            "top_breakthroughs": [{"id": r[0], "delta_know": r[1], "delta_uncertainty": r[2]} for r in top_breakthroughs]
        }, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"TRAJECTORY STATISTICS")
        print(f"{'='*50}\n")

        print(f"Total Trajectories: {total}")
        print(f"Avg Snapshots/Trajectory: {avg_snapshots:.1f}\n")

        print("Pattern Distribution:")
        for pattern, count, avg_conf in pattern_stats:
            pct = count / total * 100 if total else 0
            emoji = {'breakthrough': '🚀', 'stable': '📈', 'dead_end': '🛑',
                     'oscillating': '〰️', 'unknown': '❓'}.get(pattern, '❓')
            print(f"  {emoji} {pattern}: {count} ({pct:.1f}%) - avg confidence: {avg_conf:.2f}")

        if top_breakthroughs:
            print("\nTop Breakthroughs (by knowledge gain):")
            for traj_id, delta_know, delta_unc in top_breakthroughs:
                print(f"  {traj_id}: know +{delta_know:.2f}, uncertainty {delta_unc:.2f}")


def handle_trajectory_backfill(args):
    """Backfill trajectories from historical git notes."""
    HistoricalBackfill = _get_historical_backfill()
    if not HistoricalBackfill:
        return

    backfill = HistoricalBackfill(repo_path=Path.cwd())

    print("Scanning available data...")
    stats = backfill.scan_available_data()
    print(f"  Sessions: {stats.sessions_processed}")
    print(f"  Epistemics: {stats.epistemics_found}")

    print("\nExtracting trajectories...")
    trajectories = backfill.extract_trajectories(min_phases=args.min_phases)
    print(f"  Found: {len(trajectories)} trajectories")

    print("\nStoring to database...")
    stored = backfill.populate_trajectory_store(trajectories, overwrite=True)
    print(f"  Stored: {stored} trajectories")

    if args.analyze:
        print("\nAnalyzing patterns...")
        patterns = backfill.analyze_historical_patterns()
        print("  Pattern distribution:")
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
            print(f"    {pattern}: {count}")

    if args.output == 'json':
        print(json.dumps({
            "ok": True,
            "sessions": stats.sessions_processed,
            "epistemics": stats.epistemics_found,
            "trajectories_stored": stored,
            "patterns": patterns if args.analyze else None
        }))
    else:
        print(f"\n✅ Backfill complete: {stored} trajectories stored")
