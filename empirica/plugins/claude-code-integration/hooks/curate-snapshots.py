#!/usr/bin/env python3
"""
Empirica Snapshot Curation - Impact + Completion Weighted

Curates pre-summary snapshots using importance-weighted algorithm:
- Keep: Recent (last 5), high-impact (≥0.7), milestones, resume points, best-of-day
- Archive: Low-impact trivial snapshots
- Result: ~40-50% retention, all valuable work preserved
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any


def should_keep_snapshot(
    snapshot: Dict[str, Any],
    all_snapshots: List[Dict[str, Any]],
    recent_count: int = 5
) -> Dict[str, Any]:
    """
    Determine if snapshot should be kept using Impact + Completion curation.

    Args:
        snapshot: Snapshot to evaluate
        all_snapshots: All snapshots (for context: recency, best-of-day)
        recent_count: How many recent snapshots to always keep

    Returns:
        Dict with {"keep": bool, "reason": str}
    """
    vectors = snapshot.get('checkpoint', {}).get('vectors', {})
    timestamp = snapshot.get('timestamp')

    # Extract impact and completion
    impact = vectors.get('impact', 0.5)
    completion = vectors.get('completion', 0.0)

    # Rule 1: Always keep recent snapshots (last N)
    snapshot_index = next(
        (i for i, s in enumerate(all_snapshots) if s.get('timestamp') == timestamp),
        -1
    )
    if snapshot_index >= 0 and snapshot_index < recent_count:
        return {"keep": True, "reason": f"recent (rank {snapshot_index + 1}/{recent_count})"}

    # Rule 2: High impact (important work)
    if impact >= 0.7:
        return {"keep": True, "reason": f"high_impact ({impact:.2f})"}

    # Rule 3: Milestones (high completion + moderate impact)
    if completion >= 0.9 and impact >= 0.5:
        return {"keep": True, "reason": f"milestone (completion={completion:.2f}, impact={impact:.2f})"}

    # Rule 4: Resume points (mid-progress important work)
    if 0.3 <= completion <= 0.7 and impact >= 0.6:
        return {"keep": True, "reason": f"resume_point (completion={completion:.2f}, impact={impact:.2f})"}

    # Rule 5: Best of day (highest impact in 24h window)
    if is_best_in_window(snapshot, all_snapshots, window_hours=24):
        return {"keep": True, "reason": f"best_of_day (impact={impact:.2f})"}

    # Archive: Low-impact trivial work
    return {"keep": False, "reason": f"archive (impact={impact:.2f}, completion={completion:.2f})"}


def parse_snapshot_timestamp(ts: str) -> datetime:
    """Parse snapshot timestamp, handling both ISO and dash-separated formats"""
    # Handle format like "2026-01-08T03-17-11" (dashes in time)
    ts = ts.replace('T', ' ').replace('Z', '')
    # If time portion has dashes instead of colons, fix it
    parts = ts.split(' ')
    if len(parts) == 2 and '-' in parts[1]:
        time_parts = parts[1].split('-')
        if len(time_parts) == 3:
            ts = f"{parts[0]} {':'.join(time_parts)}"
    return datetime.fromisoformat(ts)


def is_best_in_window(
    snapshot: Dict[str, Any],
    all_snapshots: List[Dict[str, Any]],
    window_hours: int = 24
) -> bool:
    """Check if snapshot has highest impact in its time window"""
    if 'timestamp' not in snapshot:
        return False
    snapshot_time = parse_snapshot_timestamp(snapshot['timestamp'])
    snapshot_impact = snapshot.get('checkpoint', {}).get('vectors', {}).get('impact', 0.0)

    window_start = snapshot_time - timedelta(hours=window_hours / 2)
    window_end = snapshot_time + timedelta(hours=window_hours / 2)

    # Find all snapshots in window
    window_snapshots = []
    for s in all_snapshots:
        if 'timestamp' not in s:
            continue
        s_time = parse_snapshot_timestamp(s['timestamp'])
        if window_start <= s_time <= window_end:
            window_snapshots.append(s)

    # Check if this is highest impact in window
    if not window_snapshots:
        return False

    max_impact = max(
        s.get('checkpoint', {}).get('vectors', {}).get('impact', 0.0)
        for s in window_snapshots
    )

    return snapshot_impact >= max_impact


def curate_snapshots(ref_docs_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Curate pre-summary snapshots in ref-docs directory.

    Args:
        ref_docs_dir: Path to .empirica/ref-docs
        dry_run: If True, don't actually move files, just report

    Returns:
        Stats dict with kept/archived counts
    """
    # Find all pre_summary snapshots
    snapshot_files = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)

    if not snapshot_files:
        return {"ok": True, "kept": 0, "archived": 0, "message": "No snapshots to curate"}

    # Load all snapshots
    snapshots = []
    for f in snapshot_files:
        with open(f, 'r') as fp:
            snapshot = json.load(fp)
            snapshot['_file_path'] = f
            snapshots.append(snapshot)

    # Sort by timestamp DESC (most recent first)
    snapshots.sort(
        key=lambda s: s.get('timestamp', ''),
        reverse=True
    )

    # Create archive directory
    archive_dir = ref_docs_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    # Curate each snapshot
    kept = 0
    archived = 0
    decisions = []

    for snapshot in snapshots:
        decision = should_keep_snapshot(snapshot, snapshots)
        file_path = snapshot['_file_path']

        decisions.append({
            "file": file_path.name,
            "timestamp": snapshot.get('timestamp'),
            "impact": snapshot.get('checkpoint', {}).get('vectors', {}).get('impact', 0.0),
            "completion": snapshot.get('checkpoint', {}).get('vectors', {}).get('completion', 0.0),
            "decision": "keep" if decision['keep'] else "archive",
            "reason": decision['reason']
        })

        if decision['keep']:
            kept += 1
        else:
            archived += 1
            if not dry_run:
                # Move to archive
                archive_path = archive_dir / file_path.name
                file_path.rename(archive_path)

    return {
        "ok": True,
        "total": len(snapshots),
        "kept": kept,
        "archived": archived,
        "retention_rate": kept / len(snapshots) if snapshots else 0,
        "decisions": decisions,
        "dry_run": dry_run
    }


def main():
    """Run snapshot curation"""
    import argparse

    parser = argparse.ArgumentParser(description="Curate Empirica pre-summary snapshots")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be archived without moving files')
    parser.add_argument('--ref-docs-dir', type=str, default='.empirica/ref-docs',
                        help='Path to ref-docs directory (default: project-local .empirica/ref-docs)')
    parser.add_argument('--output', choices=['default', 'json'], default='default',
                        help='Output format')

    args = parser.parse_args()

    ref_docs_dir = Path(args.ref_docs_dir).expanduser()

    if not ref_docs_dir.exists():
        result = {
            "ok": False,
            "error": f"Ref-docs directory not found: {ref_docs_dir}"
        }
        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Run curation
    result = curate_snapshots(ref_docs_dir, dry_run=args.dry_run)

    # Output results
    if args.output == 'json':
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        print(f"\n{'🔍 DRY RUN - ' if args.dry_run else ''}📦 Snapshot Curation")
        print("=" * 70)
        print(f"Total snapshots: {result['total']}")
        print(f"Kept: {result['kept']} ({result['retention_rate']:.1%})")
        print(f"Archived: {result['archived']} ({1 - result['retention_rate']:.1%})")

        if result.get('decisions'):
            print("\nDecisions:")
            for d in result['decisions'][:10]:  # Show first 10
                action = "✓ KEEP" if d['decision'] == 'keep' else "📦 ARCHIVE"
                print(f"  {action}: {d['file'][:40]:<40} | impact={d['impact']:.2f} | {d['reason']}")

            if len(result['decisions']) > 10:
                print(f"  ... and {len(result['decisions']) - 10} more")

        print()

    sys.exit(0)


if __name__ == '__main__':
    main()
