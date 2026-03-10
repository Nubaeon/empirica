"""
CLI handler for code-embed: extract and embed Python API surfaces into Qdrant.

Usage:
    empirica code-embed --project-id <UUID> [--path <dir>] [--output json|human]

Scans Python files, extracts public functions/classes via AST,
and embeds them as searchable code_api entries in the eidetic collection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def handle_code_embed_command(args):
    """Extract and embed Python API surfaces for a project."""
    from empirica.core.qdrant.code_embeddings import embed_project_code
    from empirica.data.session_database import SessionDatabase

    project_id = args.project_id
    output = getattr(args, 'output', 'human')

    # Resolve project path
    scan_path = getattr(args, 'path', None)
    if scan_path:
        root_dir = Path(scan_path).resolve()
    else:
        # Try to find project root from DB
        try:
            db = SessionDatabase()
            cursor = db.conn.cursor()
            cursor.execute("SELECT project_data FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if row and row['project_data']:
                import json as _json
                data = _json.loads(row['project_data'])
                root = data.get('root_path') or data.get('path')
                if root:
                    root_dir = Path(root).resolve()
                else:
                    root_dir = Path.cwd()
            else:
                root_dir = Path.cwd()
            db.close()
        except Exception:
            root_dir = Path.cwd()

    if not root_dir.is_dir():
        print(f"Error: {root_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Run extraction and embedding
    result = embed_project_code(
        project_id=project_id,
        root_dir=root_dir,
    )

    if output == 'json':
        print(json.dumps(result))
    else:
        print(f"Code API embedding complete:")
        print(f"  Files scanned: {result['files_scanned']}")
        print(f"  Modules embedded: {result['modules_embedded']}")
        print(f"  Skipped (no public API): {result['skipped']}")
        if result['errors']:
            print(f"  Errors: {result['errors']}")
