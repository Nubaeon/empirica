#!/usr/bin/env python3
"""
Project Init Command - Initialize Empirica in a new git repository

Creates per-project configuration files:
- .empirica/config.yaml (database paths, settings)
- .empirica/project.yaml (project metadata, BEADS settings)
- docs/SEMANTIC_INDEX.yaml (optional, documentation index template)

Usage:
    cd my-new-project
    git init
    empirica project-init
    
Author: Rovo Dev
Date: 2025-12-19
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def handle_project_init_command(args):
    """Handle project-init command - initialize Empirica in a new repo"""
    try:
        from empirica.config.path_resolver import get_git_root, ensure_empirica_structure, create_default_config
        from empirica.data.session_database import SessionDatabase
        
        # Check if in git repo
        git_root = get_git_root()
        if not git_root:
            print("❌ Error: Not in a git repository")
            print("\nRun 'git init' first, then try again")
            return None
        
        interactive = not getattr(args, 'non_interactive', False)
        output_format = getattr(args, 'output', 'default')
        
        # Check if already initialized
        config_path = git_root / '.empirica' / 'config.yaml'
        if config_path.exists() and not getattr(args, 'force', False):
            if output_format == 'json':
                print(json.dumps({
                    "ok": False,
                    "error": "Empirica already initialized in this repo",
                    "hint": "Use --force to reinitialize"
                }, indent=2))
            else:
                print("❌ Empirica already initialized in this repo")
                print(f"   Config found: {config_path}")
                print("\nTip: Use --force to reinitialize")
            return None
        
        if output_format != 'json':
            print("🚀 Initializing Empirica in this repository...")
            print(f"   Git root: {git_root}\n")
        
        # Create directory structure
        ensure_empirica_structure()
        
        # Create config.yaml
        create_default_config()
        
        # Interactive setup (only if not in JSON mode)
        project_name = None
        project_description = None
        enable_beads = False
        create_semantic_index = False
        
        if interactive and output_format != 'json':
            print("📋 Project Configuration\n")
            
            # Get project name
            default_name = git_root.name
            project_name = input(f"Project name [{default_name}]: ").strip() or default_name
            
            # Get description
            project_description = input("Project description (optional): ").strip() or None
            
            # BEADS integration
            beads_response = input("\nEnable BEADS issue tracking by default? [y/N]: ").strip().lower()
            enable_beads = beads_response in ('y', 'yes')
            
            # Semantic index
            semantic_response = input("Create SEMANTIC_INDEX.yaml template? [y/N]: ").strip().lower()
            create_semantic_index = semantic_response in ('y', 'yes')
        else:
            # Non-interactive mode: use args
            project_name = getattr(args, 'project_name', None) or git_root.name
            project_description = getattr(args, 'project_description', None)
            enable_beads = getattr(args, 'enable_beads', False)
            create_semantic_index = getattr(args, 'create_semantic_index', False)
        
        # Create project.yaml with BEADS config
        project_config_path = git_root / '.empirica' / 'project.yaml'
        
        # Get git remote URL for repos field
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                timeout=5
            )
            git_url = result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            git_url = None
        
        project_config = {
            'version': '1.0',
            'name': project_name,
            'description': project_description or f"{project_name} project",
            'beads': {
                'default_enabled': enable_beads,
            },
            'subjects': {},
            'auto_detect': {
                'enabled': True,
                'method': 'path_match'
            }
        }
        
        import yaml
        with open(project_config_path, 'w') as f:
            yaml.dump(project_config, f, default_flow_style=False, sort_keys=False)
        
        # Create or reuse project in database (idempotent)
        # For new projects, we must pass explicit path since get_session_db_path()
        # requires an existing db or context to resolve
        db_path = git_root / '.empirica' / 'sessions' / 'sessions.db'
        db = SessionDatabase(db_path=str(db_path))
        project_id = None
        reused_existing = False

        # First, check if project.yaml already has a project_id (from previous init)
        if project_config_path.exists():
            try:
                with open(project_config_path, 'r') as f:
                    existing_config = yaml.safe_load(f) or {}
                existing_id = existing_config.get('project_id')
                if existing_id:
                    # Verify it exists in DB
                    existing_project = db.get_project(existing_id)
                    if existing_project:
                        project_id = existing_id
                        reused_existing = True
                        if output_format != 'json':
                            print(f"   ♻️  Reusing existing project_id: {project_id[:8]}...")
            except Exception:
                pass  # Fall through to create new

        # If no existing project_id, check by name (prevents duplicates)
        if not project_id:
            existing_by_name = db.projects.get_project_by_name(project_name)
            if existing_by_name:
                project_id = existing_by_name['id']
                reused_existing = True
                if output_format != 'json':
                    print(f"   ♻️  Found existing project by name: {project_id[:8]}...")

        # Only create new if no existing project found
        if not project_id:
            project_id = db.create_project(
                name=project_name,
                description=project_description,
                repos=[git_url] if git_url else None
            )

        # Update project.yaml with project_id
        project_config['project_id'] = project_id
        with open(project_config_path, 'w') as f:
            yaml.dump(project_config, f, default_flow_style=False, sort_keys=False)

        db.close()

        # Register project in global workspace.db for cross-project visibility
        try:
            from .workspace_init import _register_in_workspace_db
            _register_in_workspace_db(
                project_id=project_id,
                name=project_name,
                trajectory_path=str(git_root),
                description=project_description,
                git_remote_url=git_url
            )
            if output_format != 'json':
                print(f"   📋 Registered in workspace")
        except Exception as e:
            logger.warning(f"Failed to register in workspace.db: {e}")

        # CRITICAL: Update resolver context so subsequent commands (session-create) find this project
        # This mirrors what project-switch does - updates instance_projects, TTY session, active_work
        try:
            import time
            from empirica.utils.session_resolver import get_tty_key, get_tty_session

            marker_dir = Path.home() / '.empirica'
            project_path = str(git_root)

            # Get TMUX pane for instance isolation
            tmux_pane = os.environ.get('TMUX_PANE')
            instance_id = f"tmux_{tmux_pane.lstrip('%')}" if tmux_pane else None

            # Try to get Claude session ID from TTY session (if running in Claude context)
            tty_session = get_tty_session(warn_if_stale=False)
            claude_session_id = tty_session.get('claude_session_id') if tty_session else None

            # Preserve existing claude_session_id from instance_projects if TTY doesn't have it
            if not claude_session_id and instance_id:
                existing_instance_file = marker_dir / 'instance_projects' / f'{instance_id}.json'
                if existing_instance_file.exists():
                    try:
                        with open(existing_instance_file, 'r') as f:
                            existing_data = json.load(f)
                            claude_session_id = existing_data.get('claude_session_id')
                    except Exception:
                        pass

            # Update instance_projects (works via Bash tool where TTY fails)
            if instance_id:
                instance_dir = marker_dir / 'instance_projects'
                instance_dir.mkdir(parents=True, exist_ok=True)
                instance_file = instance_dir / f'{instance_id}.json'
                instance_data = {
                    'project_path': project_path,
                    'project_id': project_id,
                    'folder_name': project_name,
                    'claude_session_id': claude_session_id,
                    'source': 'project-init',
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z')
                }
                with open(instance_file, 'w') as f:
                    json.dump(instance_data, f, indent=2)
                logger.debug(f"Updated instance_projects: {instance_id} -> {project_name}")

            # Update TTY session if available
            tty_key = get_tty_key()
            if tty_key:
                tty_sessions_dir = marker_dir / 'tty_sessions'
                tty_sessions_dir.mkdir(parents=True, exist_ok=True)
                tty_session_file = tty_sessions_dir / f'{tty_key}.json'

                tty_data = {}
                if tty_session_file.exists():
                    try:
                        with open(tty_session_file, 'r') as f:
                            tty_data = json.load(f)
                    except Exception:
                        pass

                tty_data['project_path'] = project_path
                tty_data['project_id'] = project_id
                tty_data['tty_key'] = tty_key
                tty_data['instance_id'] = instance_id
                tty_data['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')

                with open(tty_session_file, 'w') as f:
                    json.dump(tty_data, f, indent=2)
                logger.debug(f"Updated TTY session: {tty_key} -> {project_name}")

            # Update active_work file if we know the Claude session ID
            if claude_session_id:
                active_work_file = marker_dir / f'active_work_{claude_session_id}.json'
                active_work = {}
                if active_work_file.exists():
                    try:
                        with open(active_work_file, 'r') as f:
                            active_work = json.load(f)
                    except Exception:
                        pass

                active_work['project_path'] = project_path
                active_work['project_id'] = project_id
                active_work['folder_name'] = project_name
                active_work['source'] = 'project-init'
                active_work['updated_at'] = time.time()

                with open(active_work_file, 'w') as f:
                    json.dump(active_work, f, indent=2)
                logger.debug(f"Updated active_work: {claude_session_id[:8]}... -> {project_name}")

            if output_format != 'json':
                print(f"   🔗 Resolver context updated")

        except Exception as e:
            logger.warning(f"Failed to update resolver context: {e}")

        # Create SEMANTIC_INDEX.yaml template if requested
        semantic_index_path = None
        if create_semantic_index:
            docs_dir = git_root / 'docs'
            docs_dir.mkdir(exist_ok=True)
            
            semantic_index_path = docs_dir / 'SEMANTIC_INDEX.yaml'
            
            template = {
                'version': '2.0',
                'project': project_name,
                'index': {
                    'README.md': {
                        'tags': ['readme', 'getting-started'],
                        'concepts': ['Project overview'],
                        'questions': ['What is this project?'],
                        'use_cases': ['new_user_onboarding']
                    }
                },
                'total_docs_indexed': 1,
                'last_updated': '2025-12-19',
                'coverage': {
                    'core_concepts': 1,
                    'quickstart': 0,
                    'architecture': 0,
                    'api': 0
                }
            }
            
            with open(semantic_index_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False, sort_keys=False)
        
        # Format output
        if output_format == 'json':
            result = {
                "ok": True,
                "project_id": project_id,
                "project_name": project_name,
                "git_root": str(git_root),
                "reused_existing": reused_existing,
                "files_created": {
                    "config": str(config_path),
                    "project_config": str(project_config_path),
                    "semantic_index": str(semantic_index_path) if semantic_index_path else None
                },
                "beads_enabled": enable_beads,
                "message": "Empirica initialized successfully" + (" (reused existing project)" if reused_existing else "")
            }
            print(json.dumps(result, indent=2))
        else:
            print("\n✅ Empirica initialized successfully!\n")
            print("📁 Files created:")
            print(f"   • {config_path.relative_to(git_root)}")
            print(f"   • {project_config_path.relative_to(git_root)}")
            if semantic_index_path:
                print(f"   • {semantic_index_path.relative_to(git_root)}")
            
            print(f"\n🆔 Project ID: {project_id}")
            print(f"📦 Project Name: {project_name}")
            if enable_beads:
                print(f"🔗 BEADS: Enabled by default")
            
            print("\n📋 Next steps:")
            if enable_beads:
                print("   1. Initialize BEADS issue tracking:")
                print(f"      bd init")
                print("   2. Create your first session:")
                print(f"      empirica session-create --ai-id myai")
                print("   3. Create goals (BEADS will auto-link):")
                print(f"      empirica goals-create --objective '...' --success-criteria '...'")
            else:
                print("   1. Create your first session:")
                print(f"      empirica session-create --ai-id myai")
                print("   2. Start working with epistemic tracking:")
                print(f"      empirica preflight-submit <assessment.json>")
            
            if create_semantic_index:
                print(f"\n📖 Semantic index template created!")
                print(f"   Edit docs/SEMANTIC_INDEX.yaml to add your documentation metadata")

        # Return result dict for programmatic use (e.g., auto-init)
        return {
            "ok": True,
            "project_id": project_id,
            "project_name": project_name,
            "git_root": str(git_root),
        }

    except Exception as e:
        from ..cli_utils import handle_cli_error
        handle_cli_error(e, "Project init", getattr(args, 'verbose', False))
        return None
