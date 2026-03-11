"""
Training Commands - Export epistemic transaction data as JSONL for model fine-tuning.

Exports matched (preflight, postflight, grounded_calibration, noetic_artifacts) tuples
from the sessions database. Each JSONL line is one epistemic transaction — a complete
belief-update cycle suitable for supervised fine-tuning on epistemic self-awareness.
"""

import json
import logging
import sqlite3
from pathlib import Path
from ..cli_utils import handle_cli_error

logger = logging.getLogger(__name__)


def _export_from_db(db_path, project_filter, ai_filter, min_vectors,
                    include_artifacts, include_grounded, project_name=None):
    """Export training records from a single sessions.db. Returns (records, skipped)."""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except Exception as e:
        logger.debug(f"Cannot open {db_path}: {e}")
        return [], 0

    pairs = _find_transaction_pairs(conn, project_filter, ai_filter)
    records = []
    skipped = 0
    for pair in pairs:
        record = _build_training_record(
            conn, pair,
            include_artifacts=include_artifacts,
            include_grounded=include_grounded,
            min_vectors=min_vectors,
        )
        if record:
            if project_name:
                record['_source_project'] = project_name
            records.append(record)
        else:
            skipped += 1

    conn.close()
    return records, skipped


def _find_workspace_dbs():
    """Find all project sessions.db files via workspace.db global_projects table."""
    workspace_db_path = Path.home() / '.empirica' / 'workspace' / 'workspace.db'
    if not workspace_db_path.exists():
        return []

    conn = sqlite3.connect(str(workspace_db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, name, trajectory_path FROM global_projects WHERE status != 'archived'"
        ).fetchall()
    except Exception:
        conn.close()
        return []
    conn.close()

    dbs = []
    for row in rows:
        tpath = row['trajectory_path']
        if not tpath:
            continue
        # trajectory_path may be /path/to/project/.empirica or /path/to/project
        tpath = Path(tpath)
        candidates = [
            tpath / 'sessions' / 'sessions.db',
            tpath / '.empirica' / 'sessions' / 'sessions.db',
        ]
        # Also check if tpath itself ends with .empirica
        if tpath.name == '.empirica':
            candidates.insert(0, tpath / 'sessions' / 'sessions.db')

        for candidate in candidates:
            if candidate.exists():
                dbs.append({
                    'project_id': row['id'],
                    'project_name': row['name'],
                    'db_path': candidate,
                })
                break

    return dbs


def handle_training_export_command(args):
    """Handle training-export command — export epistemic transactions as JSONL."""
    try:
        from empirica.config.path_resolver import get_session_db_path

        output_path = getattr(args, 'output_path', None)
        project_filter = getattr(args, 'project_id', None)
        ai_filter = getattr(args, 'ai_id', None)
        min_vectors = getattr(args, 'min_vectors', 3)
        include_artifacts = not getattr(args, 'no_artifacts', False)
        include_grounded = not getattr(args, 'no_grounded', False)
        workspace_mode = getattr(args, 'workspace', False)
        output_format = getattr(args, 'output', 'human')

        all_records = []
        total_skipped = 0
        db_sources = []

        if workspace_mode:
            # Export from ALL project databases in workspace
            project_dbs = _find_workspace_dbs()
            if not project_dbs:
                if output_format == 'json':
                    print(json.dumps({"ok": True, "exported": 0,
                                      "message": "No project databases found in workspace"}))
                else:
                    print("No project databases found in workspace.")
                return None

            seen_dbs = set()
            for pdb in project_dbs:
                db_key = str(pdb['db_path'])
                if db_key in seen_dbs:
                    continue
                seen_dbs.add(db_key)

                records, skipped = _export_from_db(
                    pdb['db_path'], project_filter, ai_filter,
                    min_vectors, include_artifacts, include_grounded,
                    project_name=pdb['project_name'],
                )
                if records:
                    all_records.extend(records)
                    total_skipped += skipped
                    db_sources.append({
                        'project': pdb['project_name'],
                        'db_path': str(pdb['db_path']),
                        'exported': len(records),
                    })
        else:
            # Single project export (current context)
            db_path = get_session_db_path()
            records, skipped = _export_from_db(
                db_path, project_filter, ai_filter,
                min_vectors, include_artifacts, include_grounded,
            )
            all_records = records
            total_skipped = skipped
            db_sources = [{'db_path': str(db_path), 'exported': len(records)}]

        if not all_records:
            if output_format == 'json':
                print(json.dumps({"ok": True, "exported": 0,
                                  "message": "No paired transactions found"}))
            else:
                print("No paired PREFLIGHT/POSTFLIGHT transactions found.")
            return None

        # Write output
        if output_path:
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, 'w') as f:
                for rec in all_records:
                    f.write(json.dumps(rec, default=str) + '\n')
            if output_format == 'json':
                print(json.dumps({
                    "ok": True,
                    "exported": len(all_records),
                    "skipped": total_skipped,
                    "output_path": str(out_path),
                    "sources": db_sources,
                }))
            else:
                print(f"Exported {len(all_records)} transactions to {out_path}")
                if total_skipped:
                    print(f"   Skipped {total_skipped} (insufficient vector data)")
                if workspace_mode:
                    print(f"   Sources: {len(db_sources)} project databases")
                    for src in db_sources:
                        print(f"     {src.get('project', 'unknown')}: {src['exported']} transactions")
                else:
                    print(f"   Source: {db_sources[0]['db_path']}")
        else:
            # Write to stdout
            for rec in all_records:
                print(json.dumps(rec, default=str))

        return None

    except Exception as e:
        handle_cli_error(e, "Training export", getattr(args, 'verbose', False))
        return None


def _find_transaction_pairs(conn, project_filter=None, ai_filter=None):
    """Find matched PREFLIGHT/POSTFLIGHT pairs from reflexes table."""
    # Strategy: group by transaction_id or cascade_id, find pairs
    query = """
        SELECT
            pf.id as preflight_id,
            pf.session_id,
            pf.transaction_id,
            pf.cascade_id,
            pf.timestamp as preflight_ts,
            pf.project_id,
            pf.engagement as pf_engagement, pf.know as pf_know, pf.do as pf_do,
            pf.context as pf_context, pf.clarity as pf_clarity, pf.coherence as pf_coherence,
            pf.signal as pf_signal, pf.density as pf_density, pf.state as pf_state,
            pf.change as pf_change, pf.completion as pf_completion, pf.impact as pf_impact,
            pf.uncertainty as pf_uncertainty,
            pf.reflex_data as pf_reflex_data,

            po.id as postflight_id,
            po.timestamp as postflight_ts,
            po.engagement as po_engagement, po.know as po_know, po.do as po_do,
            po.context as po_context, po.clarity as po_clarity, po.coherence as po_coherence,
            po.signal as po_signal, po.density as po_density, po.state as po_state,
            po.change as po_change, po.completion as po_completion, po.impact as po_impact,
            po.uncertainty as po_uncertainty,
            po.reflex_data as po_reflex_data,
            po.reasoning as po_reasoning,

            s.ai_id
        FROM reflexes pf
        JOIN reflexes po ON (
            (pf.transaction_id IS NOT NULL AND pf.transaction_id = po.transaction_id)
            OR (pf.transaction_id IS NULL AND pf.cascade_id IS NOT NULL AND pf.cascade_id = po.cascade_id)
            OR (pf.transaction_id IS NULL AND pf.cascade_id IS NULL AND pf.session_id = po.session_id)
        )
        JOIN sessions s ON pf.session_id = s.session_id
        WHERE pf.phase = 'PREFLIGHT'
          AND po.phase = 'POSTFLIGHT'
          AND po.timestamp > pf.timestamp
    """
    params = []

    if project_filter:
        query += " AND pf.project_id LIKE ?"
        params.append(f"{project_filter}%")

    if ai_filter:
        query += " AND s.ai_id = ?"
        params.append(ai_filter)

    # For same-session pairs without transaction_id, take closest POSTFLIGHT after each PREFLIGHT
    query += " ORDER BY pf.timestamp ASC"

    try:
        rows = conn.execute(query, params).fetchall()
    except sqlite3.OperationalError as e:
        logger.warning(f"Query failed (schema mismatch?): {e}")
        rows = []

    # Deduplicate: if a PREFLIGHT matches multiple POSTFLIGHTs, take the closest
    seen_preflight = set()
    pairs = []
    for row in rows:
        pf_id = row['preflight_id']
        if pf_id not in seen_preflight:
            seen_preflight.add(pf_id)
            pairs.append(dict(row))

    return pairs


def _build_training_record(conn, pair, include_artifacts=True, include_grounded=True, min_vectors=3):
    """Build a single JSONL training record from a PREFLIGHT/POSTFLIGHT pair."""
    VECTORS = ['know', 'do', 'context', 'clarity', 'coherence', 'signal',
               'density', 'state', 'change', 'completion', 'impact',
               'engagement', 'uncertainty']

    # Extract preflight vectors
    preflight = {}
    postflight = {}
    for v in VECTORS:
        pf_val = pair.get(f'pf_{v}')
        po_val = pair.get(f'po_{v}')
        if pf_val is not None:
            preflight[v] = pf_val
        if po_val is not None:
            postflight[v] = po_val

    # Skip if insufficient vector data
    if len(preflight) < min_vectors or len(postflight) < min_vectors:
        return None

    # Compute delta
    delta = {}
    for v in VECTORS:
        if v in preflight and v in postflight:
            delta[v] = round(postflight[v] - preflight[v], 4)

    record = {
        "session_id": pair['session_id'],
        "ai_id": pair['ai_id'],
        "project_id": pair.get('project_id'),
        "transaction_id": pair.get('transaction_id'),
        "preflight_ts": pair['preflight_ts'],
        "postflight_ts": pair['postflight_ts'],
        "preflight_vectors": preflight,
        "postflight_vectors": postflight,
        "delta": delta,
    }

    # Parse reflex_data for phase info and notes
    for prefix, key in [('pf_reflex_data', 'preflight_meta'), ('po_reflex_data', 'postflight_meta')]:
        raw = pair.get(prefix)
        if raw:
            try:
                data = json.loads(raw)
                record[key] = {
                    k: data[k] for k in ['current_phase', 'notes', 'tool_call_count']
                    if k in data
                }
            except (json.JSONDecodeError, TypeError):
                pass

    # Postflight reasoning (context_summary / notes)
    if pair.get('po_reasoning'):
        record['postflight_reasoning'] = pair['po_reasoning']

    session_id = pair['session_id']

    # CHECK decisions within this transaction window
    check_query = """
        SELECT timestamp, reflex_data, reasoning,
               know, uncertainty, completion, clarity
        FROM reflexes
        WHERE session_id = ? AND phase = 'CHECK'
          AND timestamp > ? AND timestamp < ?
        ORDER BY timestamp
    """
    checks = conn.execute(check_query, [
        session_id, pair['preflight_ts'], pair['postflight_ts']
    ]).fetchall()
    if checks:
        record['check_decisions'] = []
        for c in checks:
            check_rec = {
                'timestamp': c['timestamp'],
                'vectors': {
                    'know': c['know'], 'uncertainty': c['uncertainty'],
                    'completion': c['completion'], 'clarity': c['clarity'],
                },
            }
            if c['reflex_data']:
                try:
                    rd = json.loads(c['reflex_data'])
                    check_rec['decision'] = rd.get('decision') or rd.get('computed_decision')
                    check_rec['gate_passed'] = rd.get('gate_passed')
                except (json.JSONDecodeError, TypeError):
                    pass
            record['check_decisions'].append(check_rec)

    # Grounded calibration (post-test verification)
    if include_grounded:
        gv_query = """
            SELECT self_assessed_vectors, grounded_vectors, calibration_gaps,
                   overall_calibration_score, grounded_coverage,
                   evidence_count, sources_available
            FROM grounded_verifications
            WHERE session_id = ?
              AND created_at >= ? AND created_at <= ? + 300
            ORDER BY created_at DESC LIMIT 1
        """
        try:
            gv = conn.execute(gv_query, [
                session_id, pair['postflight_ts'], pair['postflight_ts']
            ]).fetchone()
            if gv:
                grounded = {
                    'calibration_score': gv['overall_calibration_score'],
                    'grounded_coverage': gv['grounded_coverage'],
                    'evidence_count': gv['evidence_count'],
                }
                for field in ['calibration_gaps', 'sources_available']:
                    raw = gv[field]
                    if raw:
                        try:
                            grounded[field] = json.loads(raw)
                        except (json.JSONDecodeError, TypeError):
                            pass
                record['grounded_calibration'] = grounded
        except sqlite3.OperationalError:
            pass  # Table may not exist in older DBs

    # Noetic artifacts within transaction window
    if include_artifacts:
        artifacts = {}

        # Findings
        try:
            findings = conn.execute("""
                SELECT finding, impact, subject FROM project_findings
                WHERE session_id = ? AND created_timestamp >= ? AND created_timestamp <= ?
                ORDER BY impact DESC LIMIT 10
            """, [session_id, pair['preflight_ts'], pair['postflight_ts']]).fetchall()
            if findings:
                artifacts['findings'] = [
                    {'finding': f['finding'], 'impact': f['impact'], 'subject': f['subject']}
                    for f in findings
                ]
        except sqlite3.OperationalError:
            pass

        # Unknowns
        try:
            unknowns = conn.execute("""
                SELECT unknown, is_resolved, impact FROM project_unknowns
                WHERE session_id = ? AND created_timestamp >= ? AND created_timestamp <= ?
                LIMIT 10
            """, [session_id, pair['preflight_ts'], pair['postflight_ts']]).fetchall()
            if unknowns:
                artifacts['unknowns'] = [
                    {'unknown': u['unknown'], 'resolved': bool(u['is_resolved']), 'impact': u['impact']}
                    for u in unknowns
                ]
        except sqlite3.OperationalError:
            pass

        # Dead ends
        try:
            dead_ends = conn.execute("""
                SELECT approach, why_failed, impact FROM project_dead_ends
                WHERE session_id = ? AND created_timestamp >= ? AND created_timestamp <= ?
                LIMIT 10
            """, [session_id, pair['preflight_ts'], pair['postflight_ts']]).fetchall()
            if dead_ends:
                artifacts['dead_ends'] = [
                    {'approach': d['approach'], 'why_failed': d['why_failed'], 'impact': d['impact']}
                    for d in dead_ends
                ]
        except sqlite3.OperationalError:
            pass

        # Mistakes
        try:
            mistakes = conn.execute("""
                SELECT mistake, why_wrong, prevention, root_cause_vector FROM mistakes_made
                WHERE session_id = ? AND created_timestamp >= ? AND created_timestamp <= ?
                LIMIT 10
            """, [session_id, pair['preflight_ts'], pair['postflight_ts']]).fetchall()
            if mistakes:
                artifacts['mistakes'] = [
                    {'mistake': m['mistake'], 'why_wrong': m['why_wrong'],
                     'prevention': m['prevention'], 'root_cause_vector': m['root_cause_vector']}
                    for m in mistakes
                ]
        except sqlite3.OperationalError:
            pass

        # Decisions
        try:
            decisions = conn.execute("""
                SELECT choice, rationale, reversibility FROM decisions_made
                WHERE session_id = ? AND created_timestamp >= ? AND created_timestamp <= ?
                LIMIT 10
            """, [session_id, pair['preflight_ts'], pair['postflight_ts']]).fetchall()
            if decisions:
                artifacts['decisions'] = [
                    {'choice': d['choice'], 'rationale': d['rationale'],
                     'reversibility': d['reversibility']}
                    for d in decisions
                ]
        except sqlite3.OperationalError:
            pass

        if artifacts:
            record['noetic_artifacts'] = artifacts

    return record
