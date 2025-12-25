"""
Project Structure Health Analyzer

Epistemically assesses project structure against common patterns.
This is DYNAMIC context (what's in THIS project), not static prescription.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class StructureHealthAnalyzer:
    """Analyze project structure and detect patterns"""
    
    # Known project patterns (static knowledge)
    PATTERNS = {
        'python_package': {
            'name': 'Python Package',
            'expected_folders': ['src/', 'tests/', 'docs/'],
            'expected_files': ['setup.py', 'pyproject.toml', 'README.md'],
            'optional': ['examples/', 'scripts/', '.github/'],
            'description': 'Standard Python package with src layout'
        },
        'django': {
            'name': 'Django Application',
            'expected_folders': ['apps/', 'templates/', 'static/', 'media/'],
            'expected_files': ['manage.py', 'settings.py', 'urls.py'],
            'optional': ['requirements.txt', 'Dockerfile'],
            'description': 'Django web application'
        },
        'react': {
            'name': 'React Application',
            'expected_folders': ['src/', 'public/', 'components/'],
            'expected_files': ['package.json', 'index.html', 'App.jsx'],
            'optional': ['node_modules/', 'build/', 'dist/'],
            'description': 'React frontend application'
        },
        'monorepo': {
            'name': 'Monorepo',
            'expected_folders': ['packages/', 'apps/', 'libs/'],
            'expected_files': ['lerna.json', 'package.json', 'workspace.yaml'],
            'optional': ['docs/', 'tools/', 'scripts/'],
            'description': 'Multi-package repository'
        },
        'empirica_extension': {
            'name': 'Empirica Extension',
            'expected_folders': ['empirica/', 'tests/', 'docs/'],
            'expected_files': ['.empirica-project/PROJECT_CONFIG.yaml', 'pyproject.toml'],
            'optional': ['examples/', 'scripts/'],
            'description': 'Empirica framework extension'
        }
    }
    
    def __init__(self, project_root: str):
        """
        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)
    
    def analyze(self) -> Dict:
        """Analyze project structure and detect pattern
        
        Returns:
            Dict with:
                - detected_type: Best matching pattern
                - confidence: 0.0-1.0 score
                - conformance: How well it matches pattern
                - violations: List of issues
                - suggestions: Improvements
        """
        # Scan directory structure
        folders = self._scan_folders()
        files = self._scan_files()
        
        # Match against patterns
        pattern_scores = {}
        for pattern_id, pattern in self.PATTERNS.items():
            score = self._calculate_pattern_match(folders, files, pattern)
            pattern_scores[pattern_id] = score
        
        # Get best match
        detected_type = max(pattern_scores, key=pattern_scores.get)
        confidence = pattern_scores[detected_type]
        
        # Calculate conformance to detected pattern
        pattern = self.PATTERNS[detected_type]
        conformance, violations = self._check_conformance(folders, files, pattern)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(detected_type, violations)
        
        return {
            'detected_type': detected_type,
            'detected_name': pattern['name'],
            'confidence': round(confidence, 2),
            'conformance': round(conformance, 2),
            'description': pattern['description'],
            'violations': violations,
            'suggestions': suggestions,
            'folders_found': len(folders),
            'files_found': len(files)
        }
    
    def _scan_folders(self) -> List[str]:
        """Scan for top-level folders (depth 1)"""
        folders = []
        try:
            for item in self.project_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    folders.append(item.name + '/')
        except Exception as e:
            logger.debug(f"Error scanning folders: {e}")
        return folders
    
    def _scan_files(self) -> List[str]:
        """Scan for top-level files (depth 0-1)"""
        files = []
        try:
            # Root files
            for item in self.project_root.iterdir():
                if item.is_file():
                    files.append(item.name)
            
            # One level deep (for manage.py, settings.py, etc.)
            for folder in self.project_root.iterdir():
                if folder.is_dir():
                    for item in folder.iterdir():
                        if item.is_file():
                            files.append(item.name)
        except Exception as e:
            logger.debug(f"Error scanning files: {e}")
        return files
    
    def _calculate_pattern_match(self, folders: List[str], files: List[str], pattern: Dict) -> float:
        """Calculate how well structure matches a pattern
        
        Returns:
            Score 0.0-1.0
        """
        expected_folders = pattern['expected_folders']
        expected_files = pattern['expected_files']
        optional = pattern.get('optional', [])
        
        # Count matches
        folder_matches = sum(1 for f in expected_folders if f in folders)
        file_matches = sum(1 for f in expected_files if f in files)
        optional_matches = sum(1 for o in optional if o in folders or o in files)
        
        # Calculate score
        required_total = len(expected_folders) + len(expected_files)
        required_matches = folder_matches + file_matches
        
        if required_total == 0:
            return 0.0
        
        # Base score from required matches
        base_score = required_matches / required_total
        
        # Bonus from optional matches (up to 0.2)
        optional_bonus = min(optional_matches * 0.05, 0.2)
        
        return min(base_score + optional_bonus, 1.0)
    
    def _check_conformance(self, folders: List[str], files: List[str], pattern: Dict) -> Tuple[float, List[str]]:
        """Check conformance to detected pattern
        
        Returns:
            (conformance_score, violations)
        """
        violations = []
        
        # Check for missing expected folders
        for expected in pattern['expected_folders']:
            if expected not in folders:
                violations.append(f"Missing expected folder: {expected}")
        
        # Check for missing expected files
        for expected in pattern['expected_files']:
            if expected not in files:
                violations.append(f"Missing expected file: {expected}")
        
        # Calculate conformance (inverse of violations)
        required_total = len(pattern['expected_folders']) + len(pattern['expected_files'])
        conformance = 1.0 - (len(violations) / required_total) if required_total > 0 else 1.0
        
        return max(conformance, 0.0), violations
    
    def _generate_suggestions(self, pattern_type: str, violations: List[str]) -> List[str]:
        """Generate actionable suggestions based on violations"""
        suggestions = []
        
        pattern = self.PATTERNS[pattern_type]
        
        if violations:
            suggestions.append(f"Consider adopting {pattern['name']} conventions:")
            for violation in violations[:3]:  # Top 3
                if 'folder:' in violation:
                    folder = violation.split('folder:')[1].strip()
                    suggestions.append(f"  • Create {folder} directory")
                elif 'file:' in violation:
                    file = violation.split('file:')[1].strip()
                    suggestions.append(f"  • Add {file}")
        else:
            suggestions.append(f"✅ Structure conforms well to {pattern['name']} pattern")
        
        return suggestions


def analyze_structure_health(project_root: str) -> Dict:
    """Convenience function to analyze project structure
    
    Args:
        project_root: Path to project root
        
    Returns:
        Structure health report dict
    """
    analyzer = StructureHealthAnalyzer(project_root)
    return analyzer.analyze()
