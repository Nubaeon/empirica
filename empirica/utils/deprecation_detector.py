"""
Multi-Signal Deprecation Detection

Analyzes code and docs to identify deprecated content with confidence scoring.
Uses multiple signals: git history, usage patterns, explicit markers, code alignment.

Philosophy: Preservation over deletion - flag for review, don't auto-remove.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import subprocess
from datetime import datetime, timedelta

class DeprecationDetector:
    """Detect deprecated features using multiple signals"""
    
    def __init__(self, project_root: Optional[str] = None) -> None:
        """Initialize detector with project root directory."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.docs_dir = self.project_root / "docs"
        
    def detect_explicit_deprecation(self) -> List[Dict]:
        """
        Phase 1: Find features with explicit deprecation markers
        
        Returns list of explicitly deprecated features with evidence
        """
        deprecated = []
        
        deprecation_patterns = [
            (r'deprecated', 'deprecated'),
            (r'obsolete', 'obsolete'),
            (r'no longer supported', 'unsupported'),
            (r'use\s+(\S+)\s+instead', 'replaced'),
            (r'@deprecated', 'decorator')
        ]
        
        # Search docs
        if self.docs_dir.exists():
            for md_file in self.docs_dir.rglob('*.md'):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines):
                        for pattern, reason in deprecation_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                # Try to extract feature name from context
                                feature = self._extract_feature_from_context(line)
                                
                                if feature:
                                    deprecated.append({
                                        'feature': feature,
                                        'type': 'explicit',
                                        'reason': reason,
                                        'confidence': 0.9,  # High confidence for explicit markers
                                        'evidence': {
                                            'file': str(md_file.relative_to(self.project_root)),
                                            'line': i + 1,
                                            'context': line.strip()
                                        }
                                    })
                except Exception:
                    pass
        
        return deprecated
    
    def _extract_feature_from_context(self, line: str) -> Optional[str]:
        """Extract feature/command name from line context"""
        # Look for empirica command-name pattern
        cmd_match = re.search(r'empirica\s+([a-z][a-z0-9-]+)', line, re.IGNORECASE)
        if cmd_match:
            return cmd_match.group(1)
        
        # Look for function/method names
        func_match = re.search(r'`([a-z_][a-z0-9_]+)`', line)
        if func_match:
            return func_match.group(1)
        
        # Look for class names
        class_match = re.search(r'`([A-Z][a-zA-Z0-9]+)`', line)
        if class_match:
            return class_match.group(1)
        
        return None
    
    def detect_unused_features(self, lookback_sessions: int = 50) -> List[Dict]:
        """
        Phase 2: Find features with no recent usage in artifacts
        
        Requires database access to check artifacts
        """
        unused = []
        
        try:
            from empirica.data.session_database import SessionDatabase
            
            db = SessionDatabase()
            
            # Get all commands mentioned in recent artifacts
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT artifacts_created 
                FROM handoff_reports 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (lookback_sessions,))
            
            mentioned_features = set()
            for row in cursor.fetchall():
                if row['artifacts_created']:
                    import json
                    artifacts = json.loads(row['artifacts_created'])
                    for artifact in artifacts:
                        # Extract feature names from file paths
                        path_parts = artifact.split('/')
                        for part in path_parts:
                            if '.py' in part:
                                mentioned_features.add(part.replace('.py', ''))
            
            db.close()
            
            # Compare with documented features
            from empirica.utils.doc_code_integrity import DocCodeIntegrityAnalyzer
            analyzer = DocCodeIntegrityAnalyzer(str(self.project_root))
            documented = analyzer._get_documented_cli_commands()
            
            # Features in docs but not in recent artifacts
            for feature in documented:
                if feature not in mentioned_features and not self._is_core_feature(feature):
                    unused.append({
                        'feature': feature,
                        'type': 'unused',
                        'confidence': 0.7,  # Medium-high confidence
                        'evidence': {
                            'last_seen': 'Not in last {} sessions'.format(lookback_sessions),
                            'mentioned_in_artifacts': 0
                        }
                    })
            
        except Exception as e:
            print(f"Could not check usage patterns: {e}")
        
        return unused
    
    def _is_core_feature(self, feature: str) -> bool:
        """Check if feature is core (should never be flagged)"""
        core_features = {
            'session-create', 'preflight', 'postflight', 'check',
            'project-create', 'project-bootstrap', 'handoff-query',
            'goals-create', 'sessions-list'
        }
        return feature in core_features
    
    def detect_stale_code(self, months_threshold: int = 6) -> List[Dict]:
        """
        Phase 3: Find code/docs with no git activity in X months
        
        Uses git log to check last modification time
        """
        stale = []
        
        threshold_date = datetime.now() - timedelta(days=months_threshold * 30)
        
        try:
            # Get all Python files
            py_files = list(self.project_root.glob('empirica/**/*.py'))
            
            for py_file in py_files:
                try:
                    # Get last commit date for this file
                    result = subprocess.run(
                        ['git', 'log', '-1', '--format=%at', '--', str(py_file)],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=self.project_root
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        timestamp = int(result.stdout.strip())
                        last_commit = datetime.fromtimestamp(timestamp)
                        
                        if last_commit < threshold_date:
                            days_ago = (datetime.now() - last_commit).days
                            
                            stale.append({
                                'feature': py_file.stem,
                                'type': 'stale_code',
                                'confidence': min(0.5 + (days_ago / 365) * 0.3, 0.9),
                                'evidence': {
                                    'file': str(py_file.relative_to(self.project_root)),
                                    'last_commit': last_commit.strftime('%Y-%m-%d'),
                                    'days_ago': days_ago
                                }
                            })
                            
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Could not check git history: {e}")
        
        return stale
    
    def generate_deprecation_report(self) -> Dict:
        """
        Generate comprehensive deprecation report with all signals
        
        Returns structured report for human review
        """
        report = {
            'explicit_deprecation': self.detect_explicit_deprecation(),
            'unused_features': self.detect_unused_features(),
            'stale_code': self.detect_stale_code(),
            'summary': {}
        }
        
        # Calculate summary stats
        report['summary'] = {
            'total_candidates': (
                len(report['explicit_deprecation']) +
                len(report['unused_features']) +
                len(report['stale_code'])
            ),
            'high_confidence': len([
                item for category in ['explicit_deprecation', 'unused_features', 'stale_code']
                for item in report[category]
                if item['confidence'] > 0.8
            ]),
            'needs_review': len([
                item for category in ['explicit_deprecation', 'unused_features', 'stale_code']
                for item in report[category]
                if 0.6 <= item['confidence'] <= 0.8
            ])
        }
        
        return report


def analyze_deprecation(project_root: Optional[str] = None) -> Dict:
    """
    Convenience function to run deprecation analysis
    
    Returns deprecation report
    """
    detector = DeprecationDetector(project_root)
    return detector.generate_deprecation_report()
