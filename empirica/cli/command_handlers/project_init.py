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
        
        # Create project in database
        db = SessionDatabase()
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
                "files_created": {
                    "config": str(config_path),
                    "project_config": str(project_config_path),
                    "semantic_index": str(semantic_index_path) if semantic_index_path else None
                },
                "beads_enabled": enable_beads,
                "message": "Empirica initialized successfully"
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
        
        # Return None to avoid exit code issues (output already printed)
        return None

    except Exception as e:
        from ..cli_utils import handle_cli_error
        handle_cli_error(e, "Project init", getattr(args, 'verbose', False))
        return None
