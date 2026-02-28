#!/usr/bin/env python3
"""
Project ID Resolver - CLI Utility for resolving project names to UUIDs

Allows users to use project names instead of UUIDs across all CLI commands.
Now also supports git-repo-based resolution for single-project-per-repo.
"""

from typing import Optional
import sys
import re
import subprocess


def normalize_git_url(url: str) -> str:
    """
    Normalize git URL to canonical form: host/owner/repo

    Examples:
        git@github.com:owner/repo.git -> github.com/owner/repo
        https://github.com/owner/repo.git -> github.com/owner/repo
        /home/user/repos/myrepo -> local/myrepo
    """
    if not url:
        return ""

    url = url.strip()

    # SSH format: git@host:owner/repo.git
    ssh_match = re.match(r'^git@([^:]+):(.+?)(?:\.git)?$', url)
    if ssh_match:
        host, path = ssh_match.groups()
        return f"{host}/{path}"

    # HTTPS format: https://host/owner/repo.git
    https_match = re.match(r'^https?://([^/]+)/(.+?)(?:\.git)?$', url)
    if https_match:
        host, path = https_match.groups()
        return f"{host}/{path}"

    # Local path: /path/to/repo
    if url.startswith('/') or url.startswith('~'):
        # Use just the final directory name
        import os
        return f"local/{os.path.basename(url.rstrip('/'))}"

    return url


def get_current_git_repo() -> Optional[str]:
    """Get normalized git repo URL for current directory."""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return normalize_git_url(result.stdout.strip())
    except Exception:
        pass
    return None


def resolve_project_by_git_repo(git_repo: str, db) -> Optional[str]:
    """
    Resolve project by normalized git repo URL.
    Returns the canonical project ID for this repo (creates if needed).
    """
    if not git_repo:
        return None

    cursor = db.adapter.conn.cursor()

    # Search for project with matching repo in the repos JSON array
    # The normalized URL should be contained in at least one repo entry
    cursor.execute("""
        SELECT id, name, repos FROM projects
        WHERE repos IS NOT NULL AND repos != '[]'
        ORDER BY last_activity_timestamp DESC
    """)

    for row in cursor.fetchall():
        project_id = row['id']
        repos_json = row['repos']

        try:
            import json
            repos = json.loads(repos_json) if repos_json else []
            for repo_url in repos:
                if normalize_git_url(repo_url) == git_repo:
                    return project_id
        except (json.JSONDecodeError, TypeError):
            continue

    return None


def resolve_project_id(project_id_or_name: str, db=None) -> str:
    """
    Resolve project name or UUID to UUID.

    Args:
        project_id_or_name: Either a project UUID or project name
        db: Optional SessionDatabase instance (creates one if not provided)

    Returns:
        Project UUID string

    Raises:
        SystemExit: If project not found (exits with error message)

    Examples:
        >>> resolve_project_id("empirica-web")  # Resolves name to UUID
        "258aa934-a34b-4773-b1bb-96f429de6761"

        >>> resolve_project_id("258aa934-a34b-4773-b1bb-96f429de6761")  # Pass-through UUID
        "258aa934-a34b-4773-b1bb-96f429de6761"
    """
    from empirica.data.session_database import SessionDatabase

    # Create DB if not provided
    if db is None:
        db = SessionDatabase()
        close_db = True
    else:
        close_db = False

    try:
        # Use SessionDatabase's resolve_project_id method
        resolved_id = db.resolve_project_id(project_id_or_name)

        if not resolved_id:
            print(f"❌ Error: Project '{project_id_or_name}' not found", file=sys.stderr)
            print(f"\nTip: List all projects with: empirica project-list", file=sys.stderr)
            sys.exit(1)

        return resolved_id

    finally:
        if close_db:
            db.close()
