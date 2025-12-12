"""
Doc-Code Integrity Analysis

Bidirectional analysis to detect gaps between documentation and code:
1. Missing Code: Docs mention features that don't exist
2. Missing Docs: Code implements features not documented
3. Implementation Gaps: Feature exists but doesn't match described behavior

Philosophy: Analysis, not enforcement. Inform, don't block.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)


class DocCodeIntegrityAnalyzer:
    """Analyze integrity between documentation and codebase"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docs_dir = self.project_root / "docs"
        
    def analyze_cli_commands(self) -> Dict:
        """
        Phase 1: Analyze CLI command integrity
        
        Returns dict with:
        - commands_in_docs: Commands mentioned in documentation
        - commands_in_code: Commands actually implemented
        - missing_code: Documented but not implemented
        - missing_docs: Implemented but not documented
        """
        # Get actual CLI commands
        actual_commands = self._get_actual_cli_commands()
        
        # Get documented commands
        documented_commands = self._get_documented_cli_commands()
        
        # Calculate gaps
        missing_code = documented_commands - actual_commands
        missing_docs = actual_commands - documented_commands
        
        return {
            "commands_in_code": sorted(list(actual_commands)),
            "commands_in_docs": sorted(list(documented_commands)),
            "missing_code": sorted(list(missing_code)),
            "missing_docs": sorted(list(missing_docs)),
            "total_commands": len(actual_commands),
            "documented_commands": len(documented_commands),
            "integrity_score": self._calculate_integrity_score(actual_commands, documented_commands)
        }
    
    def _get_actual_cli_commands(self) -> Set[str]:
        """Get list of actually implemented CLI commands"""
        try:
            result = subprocess.run(
                ["empirica", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            commands = set()
            
            # Find the line with {command1,command2,...}
            for line in result.stdout.split('\n'):
                if '{' in line and ',' in line:
                    # Extract commands from {cmd1,cmd2,cmd3,...} format
                    match = re.search(r'\{([^}]+)\}', line)
                    if match:
                        cmd_string = match.group(1)
                        # Split by comma and clean up
                        for cmd in cmd_string.split(','):
                            cmd = cmd.strip()
                            if cmd and not cmd.startswith('.'):  # Skip "..."
                                commands.add(cmd)
                        break
            
            # Also parse individual command descriptions
            in_commands = False
            for line in result.stdout.split('\n'):
                if line.strip().startswith('positional arguments:'):
                    in_commands = True
                    continue
                    
                if in_commands:
                    # Match "  command-name    Description"
                    match = re.match(r'\s{2,}([a-z][a-z0-9-]+)\s{2,}', line)
                    if match:
                        commands.add(match.group(1))
                    elif line and not line.startswith(' '):
                        break
            
            return commands
            
        except Exception as e:
            logger.warning(f"Could not get CLI commands: {e}")
            return set()
    
    def _get_documented_cli_commands(self) -> Set[str]:
        """Extract CLI commands mentioned in documentation"""
        commands = set()
        
        # Pattern to match: `empirica command-name` or empirica command-name
        pattern = re.compile(r'`?empirica\s+([a-z][a-z0-9-]+)')
        
        # Search all markdown files in docs
        if not self.docs_dir.exists():
            return commands
            
        for md_file in self.docs_dir.rglob('*.md'):
            try:
                content = md_file.read_text(encoding='utf-8')
                matches = pattern.findall(content)
                commands.update(matches)
            except Exception as e:
                logger.debug(f"Could not read {md_file}: {e}")
        
        return commands
    
    def _calculate_integrity_score(self, actual: Set[str], documented: Set[str]) -> float:
        """
        Calculate integrity score (0.0-1.0)
        
        Perfect score (1.0): All actual commands documented, no phantom commands
        """
        if not actual and not documented:
            return 1.0
        
        intersection = actual & documented
        union = actual | documented
        
        if not union:
            return 1.0
            
        return len(intersection) / len(union)
    
    def get_detailed_gaps(self) -> Dict:
        """
        Get detailed information about integrity gaps
        
        Returns structured report with file locations and context
        """
        cli_analysis = self.analyze_cli_commands()
        
        detailed_gaps = {
            "cli_commands": cli_analysis,
            "missing_code_details": [],
            "missing_docs_details": []
        }
        
        # For each missing code command, find where it's mentioned
        for cmd in cli_analysis["missing_code"]:
            locations = self._find_command_mentions(cmd)
            detailed_gaps["missing_code_details"].append({
                "command": cmd,
                "mentioned_in": locations,
                "severity": "high" if len(locations) > 1 else "medium"
            })
        
        # For missing docs, just list them (we know they exist in code)
        for cmd in cli_analysis["missing_docs"]:
            detailed_gaps["missing_docs_details"].append({
                "command": cmd,
                "severity": "medium"
            })
        
        return detailed_gaps
    
    def _find_command_mentions(self, command: str) -> List[Dict]:
        """Find where a command is mentioned in docs with context"""
        mentions = []
        pattern = re.compile(rf'.*empirica\s+{re.escape(command)}.*', re.IGNORECASE)
        
        if not self.docs_dir.exists():
            return mentions
            
        for md_file in self.docs_dir.rglob('*.md'):
            try:
                content = md_file.read_text(encoding='utf-8')
                for i, line in enumerate(content.split('\n'), 1):
                    if pattern.match(line):
                        mentions.append({
                            "file": str(md_file.relative_to(self.project_root)),
                            "line": i,
                            "context": line.strip()[:100]
                        })
            except Exception:
                pass
        
        return mentions


def analyze_project_integrity(project_root: Optional[str] = None) -> Dict:
    """
    Convenience function to run full integrity analysis
    
    Returns:
        Dict with integrity analysis results
    """
    analyzer = DocCodeIntegrityAnalyzer(project_root)
    return analyzer.get_detailed_gaps()


def analyze_complete_integrity(project_root: Optional[str] = None) -> Dict:
    """
    Run complete integrity analysis including deprecation and superfluity
    
    Returns comprehensive integrity report
    """
    analyzer = DocCodeIntegrityAnalyzer(project_root)
    
    basic_analysis = analyzer.get_detailed_gaps()
    
    # Add deprecation analysis (placeholder for now - will implement fully)
    basic_analysis["deprecated"] = []
    
    # Add superfluity analysis (placeholder for now - will implement fully)  
    basic_analysis["superfluous"] = []
    
