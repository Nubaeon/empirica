"""
Project Embed Command - Build Qdrant indices from docs + project memory.
"""
from __future__ import annotations
import os
import json
import logging
from typing import List, Dict

from ..cli_utils import handle_cli_error

logger = logging.getLogger(__name__)


def _load_semantic_index(root: str) -> Dict:
    """Load semantic index (per-project, with graceful fallback)"""
    from empirica.config.semantic_index_loader import load_semantic_index
    index = load_semantic_index(root)
    return index or {}


def _read_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


def handle_project_embed_command(args):
    try:
        from empirica.core.qdrant.vector_store import (
            init_collections, upsert_docs, upsert_memory,
            sync_high_impact_to_global, init_global_collection
        )
        from empirica.data.session_database import SessionDatabase

        project_id = args.project_id
        root = os.getcwd()
        sync_global = getattr(args, 'global_sync', False)

        init_collections(project_id)
        if sync_global:
            init_global_collection()

        # Prepare docs from semantic index
        idx = _load_semantic_index(root)
        docs_cfg = idx.get('index', {})
        docs_to_upsert: List[Dict] = []
        did = 1
        for relpath, meta in docs_cfg.items():
            doc_path = os.path.join(root, 'docs', relpath.split('docs/')[-1]) if not relpath.startswith('docs/') else os.path.join(root, relpath)
            text = _read_file(doc_path)
            docs_to_upsert.append({
                'id': did,
                'text': text,
                'metadata': {
                    'doc_path': relpath,
                    'tags': meta.get('tags', []),
                    'concepts': meta.get('concepts', []),
                    'questions': meta.get('questions', []),
                    'use_cases': meta.get('use_cases', []),
                }
            })
            did += 1
        upsert_docs(project_id, docs_to_upsert)

        # Prepare memory from DB
        db = SessionDatabase()
        findings = db.get_project_findings(project_id)
        unknowns = db.get_project_unknowns(project_id)
        # mistakes: join via sessions already built into breadcrumbs; simple select here
        cur = db.conn.cursor()
        cur.execute("""
            SELECT m.id, m.mistake, m.prevention
            FROM mistakes_made m
            JOIN sessions s ON m.session_id = s.session_id
            WHERE s.project_id = ?
            ORDER BY m.created_timestamp DESC
        """, (project_id,))
        mistakes = [dict(row) for row in cur.fetchall()]
        db.close()

        mem_items: List[Dict] = []
        mid = 1_000_000
        for f in findings:
            mem_items.append({
                'id': mid,
                'text': f.get('finding', ''),
                'type': 'finding',
                'goal_id': f.get('goal_id'),
                'subtask_id': f.get('subtask_id'),
                'session_id': f.get('session_id'),
                'timestamp': f.get('created_timestamp'),
                'subject': f.get('subject')
            })
            mid += 1
        for u in unknowns:
            mem_items.append({
                'id': mid,
                'text': u.get('unknown', ''),
                'type': 'unknown',
                'goal_id': u.get('goal_id'),
                'subtask_id': u.get('subtask_id'),
                'session_id': u.get('session_id'),
                'timestamp': u.get('created_timestamp'),
                'subject': u.get('subject'),
                'is_resolved': u.get('is_resolved', False)
            })
            mid += 1
        for m in mistakes:
            text = f"{m.get('mistake','')} Prevention: {m.get('prevention','')}"
            mem_items.append({
                'id': mid,
                'text': text,
                'type': 'mistake',
                'session_id': m.get('session_id'),
                'goal_id': m.get('goal_id'),
                # Note: mistakes_made doesn't have subtask_id yet (will add in migration)
                'timestamp': m.get('created_timestamp')
            })
            mid += 1

        upsert_memory(project_id, mem_items)

        # Sync high-impact items to global collection if --global flag
        global_synced = 0
        if sync_global:
            min_impact = getattr(args, 'min_impact', 0.7)
            global_synced = sync_high_impact_to_global(project_id, min_impact)

        result = {
            'ok': True,
            'docs': len(docs_to_upsert),
            'memory': len(mem_items),
            'global_synced': global_synced if sync_global else None
        }

        if getattr(args, 'output', 'default') == 'json':
            print(json.dumps(result, indent=2))
        else:
            msg = f"✅ Embedded docs: {len(docs_to_upsert)} | memory items: {len(mem_items)}"
            if sync_global:
                msg += f" | global: {global_synced}"
            print(msg)

        # Note: Skills are structured metadata (project_skills/*.yaml), not vectors
        # They are referenced by project-bootstrap via tags and id lookup, not semantic search
        return result
    except Exception as e:
        handle_cli_error(e, "Project embed", getattr(args, 'verbose', False))
        return None
