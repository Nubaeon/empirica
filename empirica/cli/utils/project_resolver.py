#!/usr/bin/env python3
"""
Project ID Resolver - CLI Utility for resolving project names to UUIDs

Allows users to use project names instead of UUIDs across all CLI commands.
"""

from typing import Optional
import sys


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


def get_project_name(project_id: str, db=None) -> Optional[str]:
    """
    Get project name from UUID (for display purposes).

    Args:
        project_id: Project UUID
        db: Optional SessionDatabase instance

    Returns:
        Project name or None if not found
    """
    from empirica.data.session_database import SessionDatabase

    if db is None:
        db = SessionDatabase()
        close_db = True
    else:
        close_db = False

    try:
        project = db.get_project(project_id)
        if project:
            return project.get('name', project_id[:8] + '...')
        return None
    finally:
        if close_db:
            db.close()
