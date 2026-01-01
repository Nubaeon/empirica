"""
Project Search Commands - semantic search over docs & memory (Qdrant-backed)
Path A: command scaffolding; embedding/provider assumed available via env.
"""
from __future__ import annotations
import json
from typing import List, Dict

from ..cli_utils import handle_cli_error


def handle_project_search_command(args):
    try:
        from empirica.core.qdrant.vector_store import init_collections, search
        project_id = args.project_id
        task = args.task
        kind = getattr(args, 'type', 'all')
        limit = getattr(args, 'limit', 5)

        init_collections(project_id)
        results = search(project_id, task, kind=kind, limit=limit)

        if getattr(args, 'output', 'default') == 'json':
            print(json.dumps({"ok": True, "results": results}, indent=2))
        else:
            print(f"🔎 Semantic search for: {task}")
            if 'docs' in results:
                print("\n📄 Docs:")
                for i, d in enumerate(results['docs'], 1):
                    print(f"  {i}. {d.get('doc_path')}  (score: {d.get('score'):.3f})")
            if 'memory' in results:
                print("\n🧠 Memory:")
                for i, m in enumerate(results['memory'], 1):
                    print(f"  {i}. {m.get('type')}  (score: {m.get('score'):.3f})")
        # Do NOT return results - it gets printed to stdout as a dict
        return None
    except Exception as e:
        handle_cli_error(e, "Project search", getattr(args, 'verbose', False))
        return None
