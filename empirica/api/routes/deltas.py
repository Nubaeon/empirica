"""Learning delta and commit epistemic endpoints

Uses SessionDatabase through the adapter layer for session deltas.
Commit epistemic endpoint reads git notes directly from Forgejo bare repos
for real-time data without requiring a sync pipeline.

All queries use ? placeholders (auto-converted for PostgreSQL).
"""

import json
import logging
import os
import subprocess
import time
from flask import Blueprint, jsonify, request

bp = Blueprint("deltas", __name__)
logger = logging.getLogger(__name__)

# Forgejo bare repos path (mounted as Docker volume)
FORGEJO_REPOS_BASE = os.environ.get(
    "FORGEJO_REPOS_PATH",
    "/forgejo-data/gitea/repositories"
)

VECTOR_NAMES = [
    "know", "do", "context", "clarity", "coherence", "signal",
    "density", "state", "change", "completion", "impact", "engagement", "uncertainty"
]


def _get_db():
    from empirica.api.app import get_db
    return get_db()


@bp.route("/sessions/<session_id>/deltas", methods=["GET"])
def get_session_deltas(session_id: str):
    """
    Get epistemic changes from PREFLIGHT to POSTFLIGHT.

    Returns deltas for each epistemic vector and learning velocity.
    """
    try:
        db = _get_db()
        vector_cols = """know, "do", context, clarity, coherence, signal,
                         density, state, change, completion, impact, engagement, uncertainty"""

        # Get PREFLIGHT
        db.adapter.execute(
            f'SELECT {vector_cols} FROM reflexes WHERE session_id = ? AND phase = \'PREFLIGHT\' ORDER BY "timestamp" ASC LIMIT 1',
            (session_id,)
        )
        preflight = db.adapter.fetchone()

        if not preflight:
            return jsonify({
                "ok": False,
                "error": "no_preflight",
                "message": "Session has no PREFLIGHT assessment"
            }), 404

        # Get POSTFLIGHT
        db.adapter.execute(
            f'SELECT {vector_cols} FROM reflexes WHERE session_id = ? AND phase = \'POSTFLIGHT\' ORDER BY "timestamp" DESC LIMIT 1',
            (session_id,)
        )
        postflight = db.adapter.fetchone()

        if not postflight:
            return jsonify({
                "ok": False,
                "error": "no_postflight",
                "message": "Session has no POSTFLIGHT assessment"
            }), 404

        # Calculate deltas
        vector_names = [
            "know", "do", "context", "clarity", "coherence", "signal",
            "density", "state", "change", "completion", "impact", "engagement", "uncertainty"
        ]

        deltas = {}
        for name in vector_names:
            pre = float(preflight.get(name, 0) or 0)
            post = float(postflight.get(name, 0) or 0)
            deltas[name] = {
                "preflight": round(pre, 2),
                "postflight": round(post, 2),
                "delta": round(post - pre, 2)
            }

        # Get session duration
        db.adapter.execute(
            "SELECT start_time, end_time FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        session = db.adapter.fetchone()
        duration_seconds = 3600  # Default 1hr placeholder
        if session and session.get("end_time") and session.get("start_time"):
            try:
                from datetime import datetime
                start = datetime.fromisoformat(str(session["start_time"]))
                end = datetime.fromisoformat(str(session["end_time"]))
                duration_seconds = max(1, int((end - start).total_seconds()))
            except (ValueError, TypeError):
                pass

        return jsonify({
            "ok": True,
            "session_id": session_id,
            "deltas": deltas,
            "learning_velocity": {
                "know_per_minute": round(deltas["know"]["delta"] / (duration_seconds / 60), 4),
                "overall_per_minute": round(
                    sum(deltas[k]["delta"] for k in vector_names) / len(vector_names) / (duration_seconds / 60), 4
                )
            }
        })

    except Exception as e:
        logger.error(f"Error getting deltas: {e}")
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": str(e),
            "status_code": 500
        }), 500


def _git_cmd(repo_path: str, *args) -> str:
    """Run a git command against a bare repo and return stdout."""
    cmd = ["git", "-C", repo_path] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return result.stdout.strip()


_commit_repo_cache: dict[str, str] = {}


def _find_repo_for_commit(commit_sha: str) -> str | None:
    """Find which Forgejo bare repo contains a commit."""
    short = commit_sha[:7]
    if short in _commit_repo_cache:
        return _commit_repo_cache[short]

    if not os.path.isdir(FORGEJO_REPOS_BASE):
        return None
    for org in os.listdir(FORGEJO_REPOS_BASE):
        org_path = os.path.join(FORGEJO_REPOS_BASE, org)
        if not os.path.isdir(org_path):
            continue
        for repo in os.listdir(org_path):
            repo_path = os.path.join(org_path, repo)
            if not repo.endswith(".git"):
                continue
            result = subprocess.run(
                ["git", "-C", repo_path, "cat-file", "-t", commit_sha],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "commit" in result.stdout:
                _commit_repo_cache[short] = repo_path
                return repo_path
    return None


def _read_note_blob(repo_path: str, ref: str) -> dict | None:
    """Read JSON blob from a git notes ref in a bare repo."""
    try:
        # ref -> commit -> tree -> blob -> content
        commit_sha = _git_cmd(repo_path, "rev-parse", ref)
        if not commit_sha:
            return None
        tree_line = _git_cmd(repo_path, "cat-file", "-p", commit_sha)
        tree_sha = None
        for line in tree_line.split("\n"):
            if line.startswith("tree "):
                tree_sha = line.split()[1]
                break
        if not tree_sha:
            return None
        ls_tree = _git_cmd(repo_path, "ls-tree", tree_sha)
        if not ls_tree:
            return None
        first_line = ls_tree.split("\n")[0]
        blob_sha = first_line.split()[2]
        content = _git_cmd(repo_path, "cat-file", "-p", blob_sha)
        return json.loads(content)
    except Exception:
        return None


# Simple TTL cache for session data per repo
_head_commit_index_cache: dict[str, tuple[float, dict[str, list[str]]]] = {}
_session_data_cache: dict[str, dict] = {}
_CACHE_TTL = 120  # seconds


def _build_head_commit_index(repo_path: str) -> dict[str, list[str]]:
    """Build a commit_sha -> [ref_path] index by reading all session blobs.

    This is expensive but cached for 120s. On subsequent requests, we only
    read the specific refs we need.
    """
    now = time.time()
    cached = _head_commit_index_cache.get(repo_path)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]

    index: dict[str, list[str]] = {}
    refs_output = _git_cmd(
        repo_path, "for-each-ref", "--format=%(refname)",
        "refs/notes/empirica/session/"
    )
    if not refs_output:
        _head_commit_index_cache[repo_path] = (now, index)
        return index

    for ref in refs_output.split("\n"):
        if not ref:
            continue
        parts = ref.split("/")
        if len(parts) < 7:
            continue

        data = _read_note_blob(repo_path, ref)
        if not data:
            continue

        # Cache the full data for later retrieval
        _session_data_cache[ref] = data

        git_state = data.get("git_state", {})
        head_commit = git_state.get("head_commit", "")
        if head_commit:
            # Index by short SHA (7 chars) for quick lookup
            short = head_commit[:7]
            if short not in index:
                index[short] = []
            index[short].append(ref)

    _head_commit_index_cache[repo_path] = (now, index)
    return index


def _get_assessment_from_ref(repo_path: str, ref: str) -> dict | None:
    """Get a parsed assessment from a session ref."""
    data = _session_data_cache.get(ref)
    if not data:
        data = _read_note_blob(repo_path, ref)
        if data:
            _session_data_cache[ref] = data
    if not data:
        return None

    parts = ref.split("/")
    if len(parts) < 7:
        return None

    meta = data.get("meta", {})
    git_state = data.get("git_state", {})
    return {
        "session_id": parts[4],
        "phase": parts[5],
        "round": parts[6] if len(parts) > 6 else "1",
        "vectors": data.get("vectors", {}),
        "overall_confidence": data.get("overall_confidence"),
        "git_state": git_state,
        "head_commit": git_state.get("head_commit", ""),
        "reasoning": meta.get("reasoning", data.get("reasoning", "")),
        "ai_id": data.get("ai_id", meta.get("ai_id", "")),
        "timestamp": data.get("timestamp", ""),
    }


def _get_session_refs(repo_path: str, session_id: str) -> list[str]:
    """Get all refs for a specific session."""
    refs_output = _git_cmd(
        repo_path, "for-each-ref", "--format=%(refname)",
        f"refs/notes/empirica/session/{session_id}/"
    )
    if not refs_output:
        return []
    return [r for r in refs_output.split("\n") if r]


def _find_session_for_commit(commit_sha: str, repo_path: str) -> dict | None:
    """Find the session assessment whose head_commit matches the commit SHA.

    Strategy 1: Index lookup on head_commit (fast, O(1) after index build).
    Strategy 2: Timestamp proximity (fallback for notes without git_state).

    Returns the best matching assessment (prefers POSTFLIGHT > CHECK > PREFLIGHT).
    """
    index = _build_head_commit_index(repo_path)

    # Strategy 1: Direct index lookup (short SHA match)
    short = commit_sha[:7]
    matching_refs = index.get(short, [])

    if not matching_refs:
        # Try full SHA prefix match against all index keys
        for key, refs in index.items():
            if key.startswith(commit_sha[:7]) or commit_sha.startswith(key):
                matching_refs.extend(refs)
                break

    if matching_refs:
        # Get the session_id from the first match
        first_ref = matching_refs[0]
        session_id = first_ref.split("/")[4]

        # Load all phases for this session
        session_refs = _get_session_refs(repo_path, session_id)
        assessments = []
        for ref in session_refs:
            a = _get_assessment_from_ref(repo_path, ref)
            if a:
                assessments.append(a)

        if assessments:
            phase_priority = {"POSTFLIGHT": 0, "CHECK": 1, "PREFLIGHT": 2}
            assessments.sort(key=lambda x: phase_priority.get(x["phase"], 99))
            return assessments[0]

    # Strategy 2: Timestamp proximity (scans cached data, no new I/O)
    try:
        commit_time = _git_cmd(repo_path, "log", "-1", "--format=%ct", commit_sha)
        if commit_time:
            commit_ts = float(commit_time)
            best_ref = None
            best_diff = float("inf")

            for ref, data in _session_data_cache.items():
                if not ref.startswith("refs/notes/empirica/session/"):
                    continue
                ts_str = data.get("timestamp", "")
                if not ts_str:
                    continue
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    assess_ts = dt.timestamp()
                    diff = abs(assess_ts - commit_ts)
                    if diff < best_diff:
                        best_diff = diff
                        best_ref = ref
                except (ValueError, TypeError):
                    continue

            # Only match if within 2 hours
            if best_ref and best_diff < 7200:
                session_id = best_ref.split("/")[4]
                session_refs = _get_session_refs(repo_path, session_id)
                assessments = []
                for ref in session_refs:
                    a = _get_assessment_from_ref(repo_path, ref)
                    if a:
                        assessments.append(a)
                if assessments:
                    phase_priority = {"POSTFLIGHT": 0, "CHECK": 1, "PREFLIGHT": 2}
                    assessments.sort(key=lambda x: phase_priority.get(x["phase"], 99))
                    return assessments[0]
    except Exception:
        pass

    return None


_findings_cache: dict[str, tuple[float, dict[str, list[str]]]] = {}
_FINDINGS_CACHE_TTL = 120


def _get_session_findings(repo_path: str, session_id: str) -> list[str]:
    """Get findings logged during a specific session.

    Builds a session_id -> findings index on first call, caches for 120s.
    """
    now = time.time()
    cached = _findings_cache.get(repo_path)
    if cached and (now - cached[0]) < _FINDINGS_CACHE_TTL:
        return cached[1].get(session_id[:8], [])

    # Build full index
    session_findings: dict[str, list[str]] = {}
    refs_output = _git_cmd(
        repo_path, "for-each-ref", "--format=%(refname)",
        "refs/notes/empirica/findings/"
    )
    if refs_output:
        for ref in refs_output.split("\n"):
            if not ref:
                continue
            data = _read_note_blob(repo_path, ref)
            if data:
                sid = data.get("session_id", "")[:8]
                finding_text = data.get("finding", "")
                if sid and finding_text:
                    if sid not in session_findings:
                        session_findings[sid] = []
                    session_findings[sid].append(finding_text[:200])

    _findings_cache[repo_path] = (now, session_findings)
    return session_findings.get(session_id[:8], [])


def _confidence_label(know: float, uncertainty: float) -> str:
    """Compute confidence label from vectors."""
    if know >= 0.8 and uncertainty <= 0.2:
        return "high"
    elif know >= 0.6 and uncertainty <= 0.4:
        return "moderate"
    elif know >= 0.4:
        return "low"
    return "very_low"


@bp.route("/commits/<commit_sha>/epistemic", methods=["GET"])
def get_commit_epistemic(commit_sha: str):
    """
    Get epistemic state associated with a specific git commit.

    Reads git notes directly from Forgejo bare repos for real-time data.
    Falls back to DB if git notes unavailable.

    Query params:
        repo: Optional repo name filter (e.g. "empirica-platform")
    """
    try:
        repo_filter = request.args.get("repo")

        # Strategy 1: Read directly from Forgejo bare repos
        repo_path = None
        if repo_filter:
            # Try specific repo
            for org in os.listdir(FORGEJO_REPOS_BASE) if os.path.isdir(FORGEJO_REPOS_BASE) else []:
                candidate = os.path.join(FORGEJO_REPOS_BASE, org, f"{repo_filter}.git")
                if os.path.isdir(candidate):
                    repo_path = candidate
                    break
        else:
            repo_path = _find_repo_for_commit(commit_sha)

        if repo_path:
            match = _find_session_for_commit(commit_sha, repo_path)

            if match:
                vectors = match["vectors"]
                know = float(vectors.get("know", 0))
                uncertainty = float(vectors.get("uncertainty", 0))
                session_id = match["session_id"]

                # Load all phases for this session to compute delta
                preflight = None
                postflight = None
                session_refs = _get_session_refs(repo_path, session_id)
                for ref in session_refs:
                    a = _get_assessment_from_ref(repo_path, ref)
                    if a and a["phase"] == "PREFLIGHT":
                        preflight = a["vectors"]
                    if a and a["phase"] == "POSTFLIGHT":
                        postflight = a["vectors"]

                learning_delta = {}
                if preflight and postflight:
                    for v in VECTOR_NAMES:
                        pre = float(preflight.get(v, 0))
                        post = float(postflight.get(v, 0))
                        learning_delta[v] = round(post - pre, 3)
                    learning_delta["overall"] = round(
                        sum(learning_delta[v] for v in VECTOR_NAMES) / len(VECTOR_NAMES), 3
                    )

                # Get findings for this session
                findings = _get_session_findings(repo_path, session_id)

                return jsonify({
                    "ok": True,
                    "commit_sha": commit_sha,
                    "source": "git_notes",
                    "epistemic_context": {
                        "session_id": session_id,
                        "ai_id": match.get("ai_id", ""),
                        "phase": match["phase"],
                        "know": know,
                        "uncertainty": uncertainty,
                        "completion": float(vectors.get("completion", 0)),
                        "impact": float(vectors.get("impact", 0)),
                        "context": float(vectors.get("context", 0)),
                        "clarity": float(vectors.get("clarity", 0)),
                        "coherence": float(vectors.get("coherence", 0)),
                        "confidence_basis": "empirica_vectors",
                        "confidence_label": _confidence_label(know, uncertainty),
                        "overall_confidence": match.get("overall_confidence"),
                        "reasoning": match.get("reasoning", "")[:300],
                    },
                    "learning_delta": learning_delta if learning_delta else None,
                    "findings": findings[:5],  # Top 5 findings
                    "findings_count": len(findings),
                })

        # Strategy 2: Fall back to DB
        db = _get_db()
        if db.adapter.table_exists("commit_epistemics"):
            db.adapter.execute(
                "SELECT * FROM commit_epistemics WHERE commit_sha = ?",
                (commit_sha,)
            )
            row = db.adapter.fetchone()
            if row:
                know = float(row.get("know", 0) or 0)
                uncertainty = float(row.get("uncertainty", 0) or 0)
                return jsonify({
                    "ok": True,
                    "commit_sha": commit_sha,
                    "source": "database",
                    "epistemic_context": {
                        "session_id": row.get("session_id", ""),
                        "ai_id": row.get("ai_id", ""),
                        "know": know,
                        "uncertainty": uncertainty,
                        "completion": float(row.get("completion", 0) or 0),
                        "impact": float(row.get("impact", 0) or 0),
                        "context": float(row.get("context", 0) or 0),
                        "clarity": float(row.get("clarity", 0) or 0),
                        "coherence": float(row.get("coherence", 0) or 0),
                        "confidence_basis": "empirica_vectors",
                        "confidence_label": _confidence_label(know, uncertainty),
                    },
                    "learning_delta": {
                        "know": float(row.get("learning_delta_know", 0) or 0),
                        "do": float(row.get("learning_delta_do", 0) or 0),
                        "overall": float(row.get("learning_delta_overall", 0) or 0)
                    }
                })

        # No data found
        return jsonify({
            "ok": False,
            "error": "no_epistemic_data",
            "commit_sha": commit_sha,
            "message": "No epistemic data for this commit. Push git notes with your code."
        }), 404

    except Exception as e:
        logger.error(f"Error getting commit epistemic for {commit_sha}: {e}")
        return jsonify({
            "ok": False,
            "error": "server_error",
            "message": str(e),
            "status_code": 500
        }), 500
