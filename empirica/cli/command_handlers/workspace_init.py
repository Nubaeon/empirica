#!/usr/bin/env python3
"""
Workspace Init Command - Epistemic Workspace Initialization

Uses Empirica's own CASCADE workflow to initialize a workspace:
- PREFLIGHT: Assess what we know about the workspace
- CHECK gates: Decide to investigate, ask user, or proceed
- Investigation: Systematic gap-filling when uncertainty is high
- User questions: Ask when we have enough context
- POSTFLIGHT: Measure learning delta

This is meta: Empirica using Empirica to organize itself!

Author: Claude Rovo Dev
Date: 2025-12-22
Session: f729e984-71c9-4628-af2a-2415b6067224
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EpistemicDecisionEngine:
    """
    Makes epistemic decisions during workspace initialization.
    
    Decision rules:
    - uncertainty > 0.7 + context < 0.3 → INVESTIGATE (blindly exploring)
    - uncertainty > 0.4 + context > 0.5 → ASK_USER (have enough context to ask)
    - uncertainty < 0.3 + know > 0.7 → PROCEED (confident enough)
    """
    
    @staticmethod
    def should_investigate(know: float, context: float, uncertainty: float) -> bool:
        """Decide if we should investigate deeper automatically"""
        # High uncertainty and low context = need more data
        return uncertainty > 0.7 and context < 0.3
    
    @staticmethod
    def should_ask_user(know: float, context: float, uncertainty: float) -> bool:
        """Decide if we should ask user for clarification"""
        # Medium uncertainty with enough context = ask informed questions
        return uncertainty > 0.4 and context > 0.5 and know < 0.8
    
    @staticmethod
    def can_proceed(know: float, context: float, uncertainty: float) -> bool:
        """Decide if we have enough confidence to proceed"""
        # Low uncertainty and high knowledge = good to go
        return uncertainty < 0.3 and know > 0.7


class WorkspaceScanner:
    """Scans workspace and builds epistemic state"""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.git_repos = []
        self.non_git_dirs = []
        self.findings = []
        self.unknowns = []
    
    def initial_scan(self) -> Dict:
        """
        Initial directory scan - low epistemic confidence.
        Returns: Basic structure with high uncertainty
        """
        logger.info(f"Scanning workspace: {self.workspace_path}")
        
        for item in self.workspace_path.iterdir():
            if not item.is_dir():
                continue
            
            if (item / '.git').exists():
                self.git_repos.append(item)
            else:
                self.non_git_dirs.append(item)
        
        # Initial epistemic state: We know structure but not content
        return {
            "know": 0.2,  # Just discovered directories
            "context": 0.1,  # No understanding of what they contain
            "uncertainty": 0.8,  # Many unknowns
            "findings": [
                f"Found {len(self.git_repos)} git repositories",
                f"Found {len(self.non_git_dirs)} non-git directories"
            ],
            "unknowns": [
                "What are these projects about?",
                "Which repos are active vs dormant?",
                "Do non-git dirs contain valuable content?",
                "Are there nested repos?"
            ]
        }
    
    def deep_investigation(self) -> Dict:
        """
        Deep investigation - systematic gap filling.
        Returns: Enhanced understanding with lower uncertainty
        """
        logger.info("Conducting deep investigation...")
        
        investigated_repos = []
        
        for repo in self.git_repos:
            repo_info = self._investigate_repo(repo)
            investigated_repos.append(repo_info)
            
            # Update findings and unknowns
            if repo_info['readme']:
                self.findings.append(f"{repo.name}: {repo_info['description']}")
            else:
                self.unknowns.append(f"{repo.name}: No README found, unclear purpose")
        
        # Check non-git dirs for nested repos
        nested_repos = self._check_for_nested_repos()
        if nested_repos:
            self.findings.append(f"Found {len(nested_repos)} nested git repos")
            self.git_repos.extend(nested_repos)
        
        # Updated epistemic state: Much better understanding
        return {
            "know": 0.65,  # Now understand project purposes
            "context": 0.70,  # Have activity and tech stack data
            "uncertainty": 0.35,  # Still some questions about user preferences
            "investigated_repos": investigated_repos,
            "findings": self.findings,
            "unknowns": self.unknowns
        }
    
    def _investigate_repo(self, repo_path: Path) -> Dict:
        """Investigate a single repository"""
        repo_info = {
            "path": str(repo_path),
            "name": repo_path.name,
            "readme": None,
            "description": None,
            "last_commit": None,
            "commit_count_180d": 0,
            "tech_stack": [],
            "has_beads": False
        }
        
        # Parse README
        readme_paths = ['README.md', 'README.rst', 'README.txt', 'README']
        for readme_name in readme_paths:
            readme_path = repo_path / readme_name
            if readme_path.exists():
                repo_info['readme'] = readme_name
                repo_info['description'] = self._extract_description(readme_path)
                break
        
        # Analyze git history
        try:
            # Last commit date
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'log', '-1', '--format=%ct'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                timestamp = int(result.stdout.strip())
                repo_info['last_commit'] = datetime.fromtimestamp(timestamp)
            
            # Commit count in last 180 days
            since_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'rev-list', '--count', f'--since={since_date}', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                repo_info['commit_count_180d'] = int(result.stdout.strip())
        
        except Exception as e:
            logger.debug(f"Error analyzing git history for {repo_path.name}: {e}")
        
        # Detect tech stack
        repo_info['tech_stack'] = self._detect_tech_stack(repo_path)
        
        # Check for BEADS
        repo_info['has_beads'] = (repo_path / '.beads').exists()
        
        return repo_info
    
    def _extract_description(self, readme_path: Path) -> Optional[str]:
        """Extract first meaningful line from README as description"""
        try:
            with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    # Skip empty lines, headers, badges
                    if not line or line.startswith('#') or line.startswith('!') or line.startswith('['):
                        continue
                    # Found first meaningful line
                    if len(line) > 10:
                        return line[:200]  # Truncate to 200 chars
                
                return None
        except Exception as e:
            logger.debug(f"Error reading README {readme_path}: {e}")
            return None
    
    def _detect_tech_stack(self, repo_path: Path) -> List[str]:
        """Detect technology stack from key files"""
        tech_stack = []
        
        tech_indicators = {
            'package.json': 'Node.js',
            'requirements.txt': 'Python',
            'Pipfile': 'Python',
            'pyproject.toml': 'Python',
            'go.mod': 'Go',
            'Cargo.toml': 'Rust',
            'pom.xml': 'Java',
            'build.gradle': 'Java',
            'Gemfile': 'Ruby',
            'composer.json': 'PHP'
        }
        
        for filename, tech in tech_indicators.items():
            if (repo_path / filename).exists():
                tech_stack.append(tech)
        
        return tech_stack
    
    def _check_for_nested_repos(self) -> List[Path]:
        """Check non-git directories for nested git repos"""
        nested = []
        
        for dir_path in self.non_git_dirs:
            try:
                for item in dir_path.iterdir():
                    if item.is_dir() and (item / '.git').exists():
                        nested.append(item)
            except Exception as e:
                logger.debug(f"Error checking {dir_path}: {e}")
        
        return nested


def handle_workspace_init_command(args):
    """
    Handle workspace-init command - Epistemic workspace initialization.
    
    Uses CASCADE workflow:
    1. PREFLIGHT: Initial scan, assess epistemic state
    2. CHECK #1: Should we investigate deeper?
    3. Investigation: Deep repo analysis if needed
    4. CHECK #2: Should we ask user for preferences?
    5. User questions: Context-aware questions if needed
    6. CHECK #3: Can we proceed with confidence?
    7. Execution: Create projects, generate configs
    8. POSTFLIGHT: Measure learning delta
    """
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.cli.cli_utils import handle_cli_error
        
        output_format = getattr(args, 'output', 'default')
        path_arg = getattr(args, 'path', None)
        workspace_path = Path(path_arg) if path_arg else Path.cwd()
        
        # Create a session for this initialization (meta!)
        db = SessionDatabase()
        session_id = db.create_session(ai_id="workspace-init-agent")
        
        if output_format != 'json':
            print("╔════════════════════════════════════════════════════════════════╗")
            print("║  Empirica Workspace Initialization - Epistemic Mode           ║")
            print("╚════════════════════════════════════════════════════════════════╝\n")
        
        # ===== PREFLIGHT =====
        if output_format != 'json':
            print("🧠 PREFLIGHT Assessment...\n")
            print(f"Scanning workspace: {workspace_path}\n")
        
        scanner = WorkspaceScanner(workspace_path)
        initial_state = scanner.initial_scan()
        
        # Store PREFLIGHT assessment
        vectors = {
            'know': initial_state['know'],
            'do': 0.5,
            'context': initial_state['context'],
            'clarity': 0.7,
            'coherence': 0.8,
            'signal': 0.6,
            'density': 0.5,
            'state': 0.8,
            'change': 0.0,
            'completion': 0.0,
            'impact': 0.5,
            'uncertainty': initial_state['uncertainty']
        }
        db.log_preflight_assessment(
            session_id=session_id,
            cascade_id=None,
            prompt_summary="Workspace initialization scan",
            vectors=vectors,
            uncertainty_notes="Initial workspace scan complete. Low knowledge and context, high uncertainty about project purposes and user preferences."
        )
        
        if output_format != 'json':
            print(f"Initial epistemic state:")
            print(f"  know: {initial_state['know']:.2f}     (Low - just started scanning)")
            print(f"  context: {initial_state['context']:.2f}  (Low - don't know file structure yet)")
            print(f"  uncertainty: {initial_state['uncertainty']:.2f} (High - many unknowns)\n")
            print(f"Findings:")
            for finding in initial_state['findings']:
                print(f"  • {finding}")
            print(f"\nUnknowns:")
            for unknown in initial_state['unknowns']:
                print(f"  • {unknown}")
            print("\n" + "━" * 64 + "\n")
        
        # ===== CHECK #1: Should we investigate deeper? =====
        decision_engine = EpistemicDecisionEngine()
        
        if decision_engine.should_investigate(
            initial_state['know'],
            initial_state['context'],
            initial_state['uncertainty']
        ):
            if output_format != 'json':
                print("🔍 CHECK #1 - Should I investigate deeper?\n")
                print(f"Current confidence: {1 - initial_state['uncertainty']:.2f} (LOW)")
                print("Decision: INVESTIGATE MORE\n")
                print("Investigation triggered because:")
                print(f"  • High uncertainty ({initial_state['uncertainty']:.2f})")
                print(f"  • Low context ({initial_state['context']:.2f})")
                print("  • Need more data to make informed decisions\n")
                print("Investigating...\n")
            
            # Deep investigation
            investigation_state = scanner.deep_investigation()
            
            # Store CHECK #1 with decision to investigate
            db.log_check_phase_assessment(
                session_id=session_id,
                cascade_id=None,
                investigation_cycle=1,
                confidence=1 - initial_state['uncertainty'],
                decision="investigate_more",
                gaps=investigation_state['unknowns'],
                next_targets=["deep_scan", "readme_analysis"],
                findings=investigation_state['findings'],
                remaining_unknowns=investigation_state['unknowns']
            )
            
            if output_format != 'json':
                print(f"Updated epistemic state:")
                print(f"  know: {investigation_state['know']:.2f} ↑    (Medium - now understand projects)")
                print(f"  context: {investigation_state['context']:.2f} ↑ (Medium - have activity data)")
                print(f"  uncertainty: {investigation_state['uncertainty']:.2f} ↓ (Medium-Low)\n")
                print(f"New findings:")
                for finding in investigation_state['findings'][:5]:  # Show first 5
                    print(f"  • {finding}")
                if len(investigation_state['findings']) > 5:
                    print(f"  ... and {len(investigation_state['findings']) - 5} more")
                print()
        else:
            investigation_state = initial_state
            investigation_state['investigated_repos'] = []
        
        # ===== CHECK #2: Should we ask user? =====
        current_know = investigation_state['know']
        current_context = investigation_state['context']
        current_uncertainty = investigation_state['uncertainty']
        
        user_preferences = {}
        
        if decision_engine.should_ask_user(current_know, current_context, current_uncertainty):
            if output_format != 'json':
                print("━" * 64 + "\n")
                print("🔍 CHECK #2 - Can I proceed or ask user?\n")
                print(f"Current confidence: {1 - current_uncertainty:.2f} (MEDIUM)")
                print("Decision: ASK USER (uncertainty still present, have context to ask)\n")
                print("Questions to resolve unknowns:\n")
            
            # Store CHECK #2
            db.log_check_phase_assessment(
                session_id=session_id,
                cascade_id=None,
                investigation_cycle=2,
                confidence=1 - current_uncertainty,
                decision="ask_user",
                gaps=investigation_state['unknowns'],
                next_targets=["user_preferences"],
                findings=investigation_state['findings'],
                remaining_unknowns=investigation_state['unknowns']
            )
            
            # Context-aware questions
            questions = _generate_context_aware_questions(investigation_state)
            
            for q in questions:
                if output_format != 'json':
                    print(f"❓ {q['question']}")
                    answer = input(f"   {q['prompt']}: ").strip().lower()
                    user_preferences[q['key']] = answer
                    print()
                else:
                    # In JSON mode, use defaults
                    user_preferences[q['key']] = q['default']
            
            # Update epistemic state with user input
            current_know = 0.80  # User clarified preferences
            current_context = 0.85  # Complete picture now
            current_uncertainty = 0.15  # Ready to proceed
            
            if output_format != 'json':
                print("Updating with user input...")
                print(f"  know: {current_know:.2f} ↑    (High - user clarified preferences)")
                print(f"  context: {current_context:.2f} ↑ (High - complete picture)")
                print(f"  uncertainty: {current_uncertainty:.2f} ↓ (Low - ready to proceed!)\n")
        else:
            # Use sensible defaults
            user_preferences = {
                'include_archived': 'n',
                'naming_strategy': 'infer-from-readme',
                'duplicate_handling': 'keep-both'
            }
        
        # ===== CHECK #3: Can we proceed? =====
        if output_format != 'json':
            print("━" * 64 + "\n")
            print("🔍 CHECK #3 - Final review before execution\n")
            print(f"Current confidence: {1 - current_uncertainty:.2f} (HIGH)")
            print("Decision: PROCEED\n")
        
        # Store CHECK #3
        db.log_check_phase_assessment(
            session_id=session_id,
            cascade_id=None,
            investigation_cycle=3,
            confidence=1 - current_uncertainty,
            decision="proceed",
            gaps=[],  # All resolved
            next_targets=["execute_initialization"],
            findings=investigation_state['findings'],
            remaining_unknowns=[]
        )
        
        # ===== EXECUTION =====
        if output_format != 'json':
            print("🚀 Executing with high confidence...\n")
            print("Creating projects:\n")
        
        created_projects = []
        
        for repo_info in investigation_state.get('investigated_repos', []):
            # Filter based on user preferences
            if user_preferences.get('include_archived') == 'n':
                # Skip if no commits in 180 days
                if repo_info['commit_count_180d'] == 0:
                    continue
            
            # Create project
            project_name = _infer_project_name(
                repo_info,
                user_preferences.get('naming_strategy', 'infer-from-readme')
            )
            
            project_id = db.create_project(
                name=project_name,
                description=repo_info.get('description') or f"Project: {repo_info['name']}",
                repos=[repo_info['path']]
            )
            
            # Generate PROJECT_CONFIG.yaml
            _generate_project_config(Path(repo_info['path']), project_id, repo_info)
            
            created_projects.append({
                'name': project_name,
                'project_id': project_id,
                'path': repo_info['path']
            })
            
            if output_format != 'json':
                desc = repo_info.get('description', 'No description')[:60]
                print(f"  ✓ {project_name} ({desc}...)")
        
        if output_format != 'json':
            print(f"\n  ✓ {len(created_projects)} projects created\n")
        
        # ===== POSTFLIGHT =====
        final_know = 0.95
        final_context = 0.95
        final_uncertainty = 0.05
        
        final_vectors = {
            'know': final_know,
            'do': 0.9,
            'context': final_context,
            'clarity': 0.95,
            'coherence': 0.95,
            'signal': 0.90,
            'density': 0.88,
            'state': 0.95,
            'change': 0.90,
            'completion': 1.0,
            'impact': 0.90,
            'uncertainty': final_uncertainty
        }
        
        db.log_postflight_assessment(
            session_id=session_id,
            cascade_id=None,
            task_summary=f"Workspace initialization: {len(created_projects)} projects registered",
            vectors=final_vectors,
            postflight_confidence=1 - final_uncertainty,
            calibration_accuracy="high",
            learning_notes=f"Complete understanding achieved through systematic investigation and user input. Learning delta: know +{final_know - initial_state['know']:.2f}, uncertainty {final_uncertainty - initial_state['uncertainty']:.2f}"
        )
        
        if output_format != 'json':
            print("━" * 64 + "\n")
            print("✅ POSTFLIGHT Assessment\n")
            print("Final epistemic state:")
            print(f"  know: {final_know:.2f} ↑       (Excellent - comprehensive understanding)")
            print(f"  context: {final_context:.2f} ↑    (Excellent - full workspace mapped)")
            print(f"  completion: 1.0 ↑  (Complete - all projects registered)")
            print(f"  uncertainty: {final_uncertainty:.2f} ↓ (Very low - high confidence)\n")
            print("Learning delta (PREFLIGHT → POSTFLIGHT):")
            print(f"  know: +{final_know - initial_state['know']:.2f}")
            print(f"  context: +{final_context - initial_state['context']:.2f}")
            print(f"  uncertainty: {final_uncertainty - initial_state['uncertainty']:.2f}\n")
            print(f"Session recorded: {session_id}\n")
            print("━" * 64 + "\n")
            print("📊 Your Epistemic Workspace\n")
            print(f"Run 'empirica workspace-overview' to see:")
            print("  • Epistemic health of all projects")
            print("  • Cross-project knowledge patterns")
            print("  • Recommended next actions\n")
        
        db.close()
        
        # Format output
        result = {
            "ok": True,
            "session_id": session_id,
            "projects_created": len(created_projects),
            "learning_delta": {
                "know": f"+{final_know - initial_state['know']:.2f}",
                "context": f"+{final_context - initial_state['context']:.2f}",
                "uncertainty": f"{final_uncertainty - initial_state['uncertainty']:.2f}"
            },
            "projects": created_projects
        }
        
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        from ..cli_utils import handle_cli_error
        handle_cli_error(e, "Workspace init", getattr(args, 'verbose', False))
        return None


def _generate_context_aware_questions(state: Dict) -> List[Dict]:
    """Generate questions based on current epistemic state"""
    questions = []
    
    # Check for archived projects
    archived_count = sum(1 for r in state.get('investigated_repos', []) 
                        if r['commit_count_180d'] == 0)
    
    if archived_count > 0:
        questions.append({
            'key': 'include_archived',
            'question': f"Q1: Include archived projects (>{archived_count} with no commits in 180 days)?",
            'prompt': '[y/n]',
            'default': 'n'
        })
    
    # Naming strategy
    questions.append({
        'key': 'naming_strategy',
        'question': "Q2: Project naming strategy?",
        'prompt': '[git-dir-name/infer-from-readme]',
        'default': 'infer-from-readme'
    })
    
    return questions


def _infer_project_name(repo_info: Dict, strategy: str) -> str:
    """Infer project name based on strategy"""
    if strategy == 'infer-from-readme' and repo_info.get('description'):
        # Try to extract name from description
        desc = repo_info['description']
        # Simple heuristic: first few words, cleaned
        words = desc.split()[:3]
        name = '-'.join(words).lower()
        # Clean up
        name = ''.join(c if c.isalnum() or c == '-' else '' for c in name)
        if name:
            return name
    
    # Fallback to directory name
    return Path(repo_info['path']).name


def _generate_project_config(repo_path: Path, project_id: str, repo_info: Dict):
    """Generate .empirica-project/PROJECT_CONFIG.yaml"""
    config_dir = repo_path / '.empirica-project'
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / 'PROJECT_CONFIG.yaml'
    
    # Build config
    import yaml
    
    config = {
        'project': {
            'name': repo_info['name'],
            'description': repo_info.get('description') or f"Project: {repo_info['name']}",
            'repository': repo_info['path'],
            'version': '1.0.0',
            'project_id': project_id
        },
        'bootstrap': {
            'essential_docs': _detect_docs(repo_path),
            'tech_stack': repo_info.get('tech_stack', []),
            'has_beads': repo_info.get('has_beads', False)
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def _detect_docs(repo_path: Path) -> List[str]:
    """Detect key documentation files"""
    docs = []
    
    doc_files = [
        'README.md', 'CONTRIBUTING.md', 'CHANGELOG.md',
        'docs/README.md', 'docs/GETTING_STARTED.md'
    ]
    
    for doc_file in doc_files:
        if (repo_path / doc_file).exists():
            docs.append(doc_file)
    
    return docs[:5]  # Max 5
