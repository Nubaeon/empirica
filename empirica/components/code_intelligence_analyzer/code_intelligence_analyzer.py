#!/usr/bin/env python3
"""
🧠 Code Intelligence Analyzer - Enterprise Component
Comprehensive code analysis, archaeology, and RSA enhancement

This enterprise component provides advanced code intelligence capabilities including:
- AI Archaeologist: Project structure analysis and organization
- Extended Code Analysis: Advanced semantic code understanding
- RSA Analysis: Recursive Self Architecture enhancement

Capabilities:
- Deep code archaeology and project excavation
- Intelligent code organization and clustering
- Advanced semantic analysis and pattern detection
- RSA-based recursive improvement recommendations
- Automated refactoring and optimization suggestions
"""

import math
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import ast
import re
import os
import json
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import networkx as nx

# ============================================================================
# AI ARCHAEOLOGIST BASE (from workspace_intelligence_system)
# ============================================================================

class ProjectArchaeologist:
    """Main archaeological analysis engine for project excavation"""
    
    def __init__(self, root_path: Path, config: Dict[str, Any] = None):
        self.root_path = Path(root_path)
        self.config = config or self._default_config()
        self.artifacts = []
        self.dependency_graph = nx.DiGraph()
        self.project_clusters = {}
        self.analysis_metadata = {
            'start_time': datetime.now(),
            'version': '1.0.0'
        }
        
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for archaeological analysis"""
        return {
            'ignore_patterns': [
                '.git', '__pycache__', '.pytest_cache', 'node_modules',
                '.DS_Store', '.venv', 'venv', '.env', '*.pyc', '*.pyo', 'tool_management.py'
            ],
            'clustering': {
                'temporal_gap_hours': 168,  # 1 week
                'min_cluster_size': 2
            },
            'analysis': {
                'max_file_size_mb': 10,
                'include_binary_files': False
            }
        }
    
    def excavate_project(self) -> Dict[str, Any]:
        """Main excavation method to analyze project structure"""
        print(f"🏛️ Starting archaeological excavation of {self.root_path}")
        
        # Discover artifacts (files)
        self._discover_artifacts()
        
        # Analyze dependencies
        self._analyze_dependencies()
        
        # Perform temporal clustering
        self._temporal_clustering()
        
        # Generate archaeological report
        return self._generate_report()
    
    def _discover_artifacts(self):
        """Discover and catalog all artifacts (files) in the project"""
        for root, dirs, files in os.walk(self.root_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]

            for file in files:
                if not self._should_ignore(file):
                    file_path = Path(root) / file
                    artifact = self._analyze_artifact(file_path)
                    if artifact:
                        self.artifacts.append(artifact)
            for d in dirs:
                init_file = Path(root) / d / '__init__.py'
                if init_file.exists() and not self._should_ignore(init_file.name):
                    artifact = self._analyze_artifact(init_file)
                    if artifact:
                        self.artifacts.append(artifact)
    
    def _should_ignore(self, name: str) -> bool:
        """Check if file/directory should be ignored"""
        for pattern in self.config['ignore_patterns']:
            if pattern in name or name.startswith('.'):
                return True
        return False
    
    def _analyze_artifact(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze individual artifact (file)"""
        try:
            stat = file_path.stat()
            
            # Skip large files if configured
            max_size = self.config['analysis']['max_file_size_mb'] * 1024 * 1024
            if stat.st_size > max_size:
                return None
            
            artifact = {
                'path': str(file_path.relative_to(self.root_path)),
                'absolute_path': str(file_path),
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'extension': file_path.suffix,
                'hash': self._calculate_hash(file_path),
                'type': self._determine_file_type(file_path),
                'dependencies': []
            }
            
            # Analyze content for Python files
            if file_path.suffix == '.py':
                artifact.update(self._analyze_python_file(file_path))
            
            return artifact
            
        except Exception as e:
            print(f"Warning: Could not analyze {file_path}: {e}")
            return None
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate file hash for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return "unknown"
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determine the type/category of the file"""
        extension_map = {
            '.py': 'python_source',
            '.js': 'javascript_source',
            '.json': 'configuration',
            '.yaml': 'configuration',
            '.yml': 'configuration',
            '.md': 'documentation',
            '.txt': 'text',
            '.sql': 'database',
            '.html': 'web',
            '.css': 'stylesheet',
            '.sh': 'script'
        }
        return extension_map.get(file_path.suffix, 'unknown')
    
    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Python file for imports and structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            imports = []
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            
            return {
                'imports': imports,
                'classes': classes,
                'functions': functions,
                'lines_of_code': len(content.splitlines())
            }
            
        except Exception as e:
            return {'analysis_error': str(e)}
    
    def _analyze_dependencies(self):
        """Analyze dependencies between artifacts"""
        for artifact in self.artifacts:
            if 'imports' in artifact:
                for import_name in artifact['imports']:
                    # Find corresponding files
                    for other_artifact in self.artifacts:
                        if self._is_dependency(import_name, other_artifact):
                            artifact['dependencies'].append(other_artifact['path'])
                            self.dependency_graph.add_edge(artifact['path'], other_artifact['path'])
    
    def _is_dependency(self, import_name: str, artifact: Dict[str, Any]) -> bool:
        """Check if import corresponds to artifact"""
        artifact_path = Path(artifact['path'])
        
        # Simple heuristic: check if import name matches file name
        if import_name in str(artifact_path.stem):
            return True
        
        # Check if it's a package import
        if '.' in import_name:
            parts = import_name.split('.')
            if any(part in str(artifact_path) for part in parts):
                return True
        
        return False
    
    def _temporal_clustering(self):
        """Cluster artifacts based on temporal proximity"""
        # Sort artifacts by modification time
        sorted_artifacts = sorted(self.artifacts, key=lambda x: x['modified_time'])
        
        clusters = []
        current_cluster = []
        gap_threshold = self.config['clustering']['temporal_gap_hours']
        
        for artifact in sorted_artifacts:
            if not current_cluster:
                current_cluster.append(artifact)
            else:
                last_time = current_cluster[-1]['modified_time']
                current_time = artifact['modified_time']
                gap_hours = (current_time - last_time).total_seconds() / 3600
                
                if gap_hours <= gap_threshold:
                    current_cluster.append(artifact)
                else:
                    if len(current_cluster) >= self.config['clustering']['min_cluster_size']:
                        clusters.append(current_cluster)
                    current_cluster = [artifact]
        
        # Add final cluster
        if len(current_cluster) >= self.config['clustering']['min_cluster_size']:
            clusters.append(current_cluster)
        
        self.project_clusters = {f"cluster_{i}": cluster for i, cluster in enumerate(clusters)}
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive archaeological report"""
        return {
            'metadata': {
                'analysis_time': datetime.now().isoformat(),
                'root_path': str(self.root_path),
                'total_artifacts': len(self.artifacts),
                'total_clusters': len(self.project_clusters)
            },
            'artifacts': self.artifacts,
            'clusters': self.project_clusters,
            'dependency_graph': {
                'nodes': list(self.dependency_graph.nodes()),
                'edges': list(self.dependency_graph.edges())
            },
            'statistics': self._generate_statistics()
        }
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate statistical summary"""
        file_types = defaultdict(int)
        total_size = 0
        total_loc = 0
        
        for artifact in self.artifacts:
            file_types[artifact['type']] += 1
            total_size += artifact['size']
            if 'lines_of_code' in artifact:
                total_loc += artifact['lines_of_code']
        
        return {
            'file_types': dict(file_types),
            'total_size_bytes': total_size,
            'total_lines_of_code': total_loc,
            'average_cluster_size': sum(len(cluster) for cluster in self.project_clusters.values()) / max(len(self.project_clusters), 1)
        }

# ============================================================================
# RSA ANALYSIS INTEGRATION
# ============================================================================

class RSAAnalyzer:
    """
    RSA (Recursive Self Architecture) Analysis component - OPEN SOURCE LIMITED VERSION
    
    ⚠️  IMPORTANT NOTICE ⚠️
    This is a LIMITED version of RSA analysis for open source distribution.
    Full recursive self-improvement capabilities are proprietary and not included.
    
    Limitations:
    - Analysis only, no automatic modifications
    - Limited recursion depth (max 2 levels)
    - No autonomous code generation or file modifications
    - Human approval required for all suggestions
    - Sandboxed execution environment
    """
    
    def __init__(self, safety_mode: bool = True):
        self.analysis_results = {}
        self.optimization_suggestions = {}
        
        # Safety limitations for open source version
        self.safety_mode = safety_mode
        self.max_recursion_depth = 2 if safety_mode else None
        self.allow_modifications = False if safety_mode else True
        self.require_human_approval = True if safety_mode else False
        self.analysis_only = True if safety_mode else False
        
        # Capability restrictions
        self.restricted_capabilities = {
            'autonomous_code_generation': False,
            'file_system_modifications': False,
            'network_access': False,
            'deep_recursive_analysis': False,
            'self_evolution': False,
            'advanced_ai_collaboration': False
        } if safety_mode else {}
        
        if safety_mode:
            print("🛡️ RSA Analyzer running in SAFE MODE - Limited capabilities for open source use")
            print("   ⚠️  Full RSA capabilities require enterprise license")
        
        self._log_initialization()
    
    def analyze_component_with_rsa(self, component_name: str, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze component using LIMITED RSA methodology (Open Source Version)
        
        ⚠️ This is a restricted version with safety limitations
        """
        if self.safety_mode:
            print(f"🔧 SAFE RSA Analysis for: {component_name} (Limited Mode)")
            print(f"   🛡️ Analysis only - no modifications permitted")
        else:
            print(f"🔧 Full RSA Analysis for: {component_name}")
        
        # Enforce safety checks
        if self.safety_mode and not self._safety_check_passed(component_name, component_data):
            return self._generate_safe_fallback_analysis(component_name)
        
        # Limited RSA analysis (safe version)
        collaboration_quality = self._assess_collaboration_quality_safe(component_data)
        improvement_opportunities = self._identify_improvements_safe(component_data)
        recursive_depth = self._calculate_recursive_depth_safe(component_data)
        
        analysis = {
            'component_name': component_name,
            'collaboration_quality': collaboration_quality,
            'improvement_opportunities': improvement_opportunities,
            'recursive_depth': min(recursive_depth, self.max_recursion_depth) if self.safety_mode else recursive_depth,
            'framework_improvements': self._suggest_framework_improvements_safe(component_data),
            'optimization_score': (collaboration_quality + min(recursive_depth, 0.5)) / 2,  # Cap optimization score in safe mode
            'safety_mode': self.safety_mode,
            'limitations_applied': self.restricted_capabilities if self.safety_mode else {},
            'disclaimer': "⚠️ Limited analysis - Full RSA capabilities require enterprise license" if self.safety_mode else None
        }
        
        self.analysis_results[component_name] = analysis
        self._log_analysis_activity(component_name, analysis)
        return analysis
    
    def _log_initialization(self):
        """Log RSA analyzer initialization for audit trail"""
        if self.safety_mode:
            print(f"   📋 Audit: RSA Analyzer initialized in safe mode at {datetime.now().isoformat()}")
    
    def _safety_check_passed(self, component_name: str, component_data: Dict[str, Any]) -> bool:
        """Perform safety checks before analysis"""
        # Basic safety checks for open source version
        if not isinstance(component_name, str) or len(component_name) > 100:
            print(f"   ⚠️ Safety check failed: Invalid component name")
            return False
        
        if not isinstance(component_data, dict):
            print(f"   ⚠️ Safety check failed: Invalid component data")
            return False
        
        # Prevent analysis of system-critical components
        dangerous_patterns = ['system', 'kernel', 'root', 'admin', 'sudo', 'exec']
        if any(pattern in component_name.lower() for pattern in dangerous_patterns):
            print(f"   ⚠️ Safety check failed: System-critical component detected")
            return False
        
        return True
    
    def _generate_safe_fallback_analysis(self, component_name: str) -> Dict[str, Any]:
        """Generate safe fallback analysis when safety checks fail"""
        return {
            'component_name': component_name,
            'collaboration_quality': 0.0,
            'improvement_opportunities': ["Component analysis blocked for safety reasons"],
            'recursive_depth': 0,
            'framework_improvements': [],
            'optimization_score': 0.0,
            'safety_mode': True,
            'analysis_blocked': True,
            'reason': "Safety checks failed - component may be system-critical",
            'disclaimer': "⚠️ Analysis blocked for safety - Full analysis requires enterprise license"
        }
    
    def _log_analysis_activity(self, component_name: str, analysis: Dict[str, Any]):
        """Log analysis activity for audit trail"""
        if self.safety_mode:
            print(f"   📋 Audit: Analyzed {component_name} - Score: {analysis.get('optimization_score', 0):.2f}")
    
    def _assess_collaboration_quality_safe(self, component_data: Dict[str, Any]) -> float:
        """SAFE VERSION: Assess collaboration quality with limitations"""
        return self._assess_collaboration_quality(component_data)
    
    def _assess_collaboration_quality(self, component_data: Dict[str, Any]) -> float:
        """Assess collaboration quality score"""
        # Simple heuristic based on file count and structure
        file_count = component_data.get('files', 0)
        python_files = component_data.get('python_files', 0)
        
        if file_count == 0:
            return 0.0
        
        # Higher score for balanced file distribution
        balance_score = min(python_files / max(file_count, 1), 1.0)
        complexity_score = min(file_count / 10, 1.0)
        
        return (balance_score + complexity_score) / 2
    
    def _identify_improvements_safe(self, component_data: Dict[str, Any]) -> List[str]:
        """SAFE VERSION: Identify improvements with safety limitations"""
        improvements = self._identify_improvements(component_data)
        
        # Filter out dangerous suggestions in safe mode
        if self.safety_mode:
            safe_improvements = []
            dangerous_keywords = ['delete', 'remove', 'modify', 'replace', 'execute', 'run', 'install']
            
            for improvement in improvements:
                if not any(keyword in improvement.lower() for keyword in dangerous_keywords):
                    safe_improvements.append(improvement)
                else:
                    safe_improvements.append("Consider reviewing code structure (details require enterprise license)")
            
            # Add safety disclaimer
            safe_improvements.append("⚠️ Additional improvement suggestions available with enterprise license")
            return safe_improvements[:3]  # Limit to 3 suggestions
        
        return improvements
    
    def _identify_improvements(self, component_data: Dict[str, Any]) -> List[str]:
        """Identify improvement opportunities"""
        improvements = []
        
        file_count = component_data.get('files', 0)
        if file_count > 20:
            improvements.append("Consider breaking down into smaller modules")
        
        if file_count < 3:
            improvements.append("Consider consolidating related functionality")
        
        return improvements
    
    def _calculate_recursive_depth_safe(self, component_data: Dict[str, Any]) -> float:
        """SAFE VERSION: Calculate recursive depth with safety limitations"""
        depth = self._calculate_recursive_depth(component_data)
        
        # Cap recursive depth in safe mode
        if self.safety_mode:
            return min(depth, 0.3)  # Severely limit recursive capabilities
        
        return depth
    
    def _calculate_recursive_depth(self, component_data: Dict[str, Any]) -> float:
        """Calculate recursive improvement depth"""
        # Simple calculation based on component complexity
        return min(component_data.get('files', 0) / 5, 1.0)
    
    def _suggest_framework_improvements_safe(self, component_data: Dict[str, Any]) -> List[str]:
        """SAFE VERSION: Suggest framework improvements with safety limitations"""
        if self.safety_mode:
            # Only provide basic, safe suggestions for open source
            return [
                "Consider adding unit tests for better code coverage",
                "Implement basic logging for debugging purposes", 
                "Add code documentation and comments",
                "⚠️ Advanced framework improvements require enterprise license"
            ]
        
        return self._suggest_framework_improvements(component_data)
    
    def _suggest_framework_improvements(self, component_data: Dict[str, Any]) -> List[str]:
        """Suggest framework-level improvements"""
        # Full framework improvements (enterprise version)
        return [
            "Implement automated testing framework",
            "Add comprehensive documentation", 
            "Establish coding standards",
            "Implement continuous integration",
            "Deploy advanced monitoring and analytics",
            "Integrate AI-powered code review systems",
            "Implement recursive self-improvement protocols",
            "Enable autonomous architecture evolution"
        ]

# ============================================================================
# EXTENDED CODE ANALYZER (from original ai_archaeologist_extended.py)
# ============================================================================

class AnalysisDepth(Enum):
    """Depth levels for code analysis"""
    SURFACE = "surface"
    INTERMEDIATE = "intermediate"
    DEEP = "deep"
    COMPREHENSIVE = "comprehensive"

class CodePattern(Enum):
    """Advanced code patterns"""
    DESIGN_PATTERN = "design_pattern"
    ANTI_PATTERN = "anti_pattern"
    ARCHITECTURAL_PATTERN = "architectural_pattern"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"
    REFACTORING_CANDIDATE = "refactoring_candidate"
    COMPLEXITY_HOTSPOT = "complexity_hotspot"

@dataclass
class AdvancedCodeInsight:
    """Advanced insight from code analysis"""
    insight_type: CodePattern
    location: Tuple[int, int]
    description: str
    confidence: float
    impact_score: float
    recommendations: List[str]
    affected_components: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

class ExtendedCodeAnalyzer:
    """
    Enterprise-grade code analyzer with advanced semantic understanding
    """
    
    def __init__(self):
        self.analysis_cache: Dict[str, Any] = {}
        self.pattern_detectors: Dict[CodePattern, callable] = {}
        self.semantic_rules: Dict[str, Any] = {}
        self.refactoring_suggestions: List[Dict[str, Any]] = []
        
        # Initialize pattern detectors
        self._initialize_pattern_detectors()
        
    def analyze_codebase(self, root_path: str, depth: AnalysisDepth = AnalysisDepth.INTERMEDIATE) -> Dict[str, Any]:
        """Perform comprehensive codebase analysis"""
        try:
            analysis_results = {
                'root_path': root_path,
                'analysis_depth': depth.value,
                'files_analyzed': 0,
                'total_insights': 0,
                'insights_by_type': {},
                'files': {},
                'summary': {},
                'recommendations': [],
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Discover Python files
            python_files = self._discover_python_files(root_path)
            
            for file_path in python_files:
                try:
                    file_analysis = self._analyze_file_extended(file_path, depth)
                    analysis_results['files'][file_path] = file_analysis
                    analysis_results['files_analyzed'] += 1
                    
                    # Aggregate insights
                    for insight in file_analysis.get('insights', []):
                        insight_type = insight['insight_type']
                        if insight_type not in analysis_results['insights_by_type']:
                            analysis_results['insights_by_type'][insight_type] = 0
                        analysis_results['insights_by_type'][insight_type] += 1
                        analysis_results['total_insights'] += 1
                        
                except Exception as e:
                    print(f"❌ Error analyzing {file_path}: {e}")
                    analysis_results['files'][file_path] = {'error': str(e)}
            
            # Generate summary and recommendations
            analysis_results['summary'] = self._generate_analysis_summary(analysis_results)
            analysis_results['recommendations'] = self._generate_codebase_recommendations(analysis_results)
            
            print(f"🏺 Extended analysis complete: {analysis_results['files_analyzed']} files, {analysis_results['total_insights']} insights")
            return analysis_results
            
        except Exception as e:
            print(f"❌ Failed to analyze codebase: {e}")
            return {'error': str(e)}
    
    def _analyze_file_extended(self, file_path: str, depth: AnalysisDepth) -> Dict[str, Any]:
        """Perform extended analysis on single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # Basic metrics
            metrics = self._calculate_extended_metrics(content, tree)
            
            # Pattern detection
            insights = []
            for pattern_type, detector in self.pattern_detectors.items():
                pattern_insights = detector(tree, lines, file_path)
                insights.extend(pattern_insights)
            
            # Complexity analysis
            complexity_analysis = self._analyze_complexity_patterns(tree)
            
            # Dependency analysis
            dependencies = self._analyze_dependencies(tree)
            
            # Quality assessment
            quality_score = self._assess_code_quality(metrics, insights, complexity_analysis)
            
            return {
                'file_path': file_path,
                'metrics': metrics,
                'insights': [self._insight_to_dict(insight) for insight in insights],
                'complexity_analysis': complexity_analysis,
                'dependencies': dependencies,
                'quality_score': quality_score,
                'refactoring_opportunities': self._identify_refactoring_opportunities(tree, insights)
            }
            
        except Exception as e:
            return {'error': str(e), 'file_path': file_path}
    
    def _calculate_extended_metrics(self, content: str, tree: ast.AST) -> Dict[str, Any]:
        """Calculate extended code metrics"""
        lines = content.split('\n')
        
        # Basic metrics
        metrics = {
            'lines_of_code': len([line for line in lines if line.strip() and not line.strip().startswith('#')]),
            'total_lines': len(lines),
            'comment_lines': len([line for line in lines if line.strip().startswith('#')]),
            'blank_lines': len([line for line in lines if not line.strip()]),
            'comment_ratio': 0.0,
            'complexity_metrics': {},
            'maintainability_index': 0.0
        }
        
        if metrics['lines_of_code'] > 0:
            metrics['comment_ratio'] = metrics['comment_lines'] / metrics['lines_of_code']
        
        # Complexity metrics
        complexity_metrics = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                complexity_metrics[node.name] = complexity
        
        metrics['complexity_metrics'] = complexity_metrics
        metrics['average_complexity'] = sum(complexity_metrics.values()) / len(complexity_metrics) if complexity_metrics else 0
        metrics['max_complexity'] = max(complexity_metrics.values()) if complexity_metrics else 0
        
        # Maintainability index (simplified)
        metrics['maintainability_index'] = self._calculate_maintainability_index(metrics)
        
        return metrics
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                
        return complexity
    
    def _calculate_maintainability_index(self, metrics: Dict[str, Any]) -> float:
        """Calculate maintainability index"""
        # Simplified maintainability index calculation
        loc = metrics['lines_of_code']
        avg_complexity = metrics['average_complexity']
        comment_ratio = metrics['comment_ratio']
        
        if loc == 0:
            return 100.0
        
        # Formula based on Halstead metrics (simplified)
        maintainability = 171 - 5.2 * math.log(loc) - 0.23 * avg_complexity - 16.2 * math.log(loc) + 50 * math.sin(math.sqrt(2.4 * comment_ratio))
        
        return max(0.0, min(100.0, maintainability))
    
    def _analyze_complexity_patterns(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze complexity patterns in code"""
        complexity_analysis = {
            'high_complexity_functions': [],
            'nested_complexity': [],
            'complexity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0}
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                
                if complexity > 15:
                    complexity_analysis['high_complexity_functions'].append({
                        'name': node.name,
                        'complexity': complexity,
                        'line': node.lineno
                    })
                
                # Classify complexity
                if complexity <= 5:
                    complexity_analysis['complexity_distribution']['low'] += 1
                elif complexity <= 10:
                    complexity_analysis['complexity_distribution']['medium'] += 1
                elif complexity <= 15:
                    complexity_analysis['complexity_distribution']['high'] += 1
                else:
                    complexity_analysis['complexity_distribution']['very_high'] += 1
                
                # Check for nested complexity
                nesting_depth = self._calculate_nesting_depth(node)
                if nesting_depth > 4:
                    complexity_analysis['nested_complexity'].append({
                        'function': node.name,
                        'nesting_depth': nesting_depth,
                        'line': node.lineno
                    })
        
        return complexity_analysis
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth in function"""
        max_depth = 0
        
        def calculate_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
                    calculate_depth(child, current_depth + 1)
                else:
                    calculate_depth(child, current_depth)
        
        calculate_depth(node)
        return max_depth
    
    def _analyze_dependencies(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze code dependencies"""
        dependencies = {
            'imports': [],
            'internal_dependencies': [],
            'external_dependencies': [],
            'circular_dependencies': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies['imports'].append(alias.name)
                    if self._is_external_dependency(alias.name):
                        dependencies['external_dependencies'].append(alias.name)
                    else:
                        dependencies['internal_dependencies'].append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                dependencies['imports'].append(module)
                if self._is_external_dependency(module):
                    dependencies['external_dependencies'].append(module)
                else:
                    dependencies['internal_dependencies'].append(module)
        
        return dependencies
    
    def _is_external_dependency(self, module_name: str) -> bool:
        """Check if module is external dependency"""
        # Simple heuristic: if it's not a standard library or relative import
        standard_libs = {'os', 'sys', 'json', 'datetime', 'typing', 'dataclasses', 'enum', 'ast', 're', 'math', 'statistics'}
        return not (module_name in standard_libs or module_name.startswith('.') or module_name.startswith('__'))
    
    def _assess_code_quality(self, metrics: Dict[str, Any], insights: List[AdvancedCodeInsight], 
                           complexity_analysis: Dict[str, Any]) -> float:
        """Assess overall code quality score"""
        quality_score = 100.0  # Start with perfect score
        
        # Deduct for high complexity
        high_complexity_count = len(complexity_analysis['high_complexity_functions'])
        quality_score -= high_complexity_count * 5
        
        # Deduct for low comment ratio
        comment_ratio = metrics.get('comment_ratio', 0)
        if comment_ratio < 0.1:
            quality_score -= 10
        elif comment_ratio < 0.2:
            quality_score -= 5
        
        # Deduct for anti-patterns
        anti_pattern_count = len([i for i in insights if i.insight_type == CodePattern.ANTI_PATTERN])
        quality_score -= anti_pattern_count * 8
        
        # Deduct for complexity hotspots
        hotspot_count = len([i for i in insights if i.insight_type == CodePattern.COMPLEXITY_HOTSPOT])
        quality_score -= hotspot_count * 6
        
        # Bonus for design patterns
        design_pattern_count = len([i for i in insights if i.insight_type == CodePattern.DESIGN_PATTERN])
        quality_score += design_pattern_count * 3
        
        return max(0.0, min(100.0, quality_score))
    
    def _identify_refactoring_opportunities(self, tree: ast.AST, insights: List[AdvancedCodeInsight]) -> List[Dict[str, Any]]:
        """Identify refactoring opportunities"""
        opportunities = []
        
        # From insights
        for insight in insights:
            if insight.insight_type == CodePattern.REFACTORING_CANDIDATE:
                opportunities.append({
                    'type': 'insight_based',
                    'description': insight.description,
                    'location': insight.location,
                    'recommendations': insight.recommendations,
                    'impact_score': insight.impact_score
                })
        
        # Long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    function_length = node.end_lineno - node.lineno
                    if function_length > 50:
                        opportunities.append({
                            'type': 'long_function',
                            'description': f"Function '{node.name}' is {function_length} lines long",
                            'location': (node.lineno, node.end_lineno),
                            'recommendations': ['Consider breaking into smaller functions', 'Extract helper functions'],
                            'impact_score': min(1.0, function_length / 100.0)
                        })
        
        return opportunities
    
    def _initialize_pattern_detectors(self):
        """Initialize pattern detection functions"""
        self.pattern_detectors = {
            CodePattern.DESIGN_PATTERN: self._detect_design_patterns,
            CodePattern.ANTI_PATTERN: self._detect_anti_patterns,
            CodePattern.COMPLEXITY_HOTSPOT: self._detect_complexity_hotspots,
            CodePattern.OPTIMIZATION_OPPORTUNITY: self._detect_optimization_opportunities,
            CodePattern.REFACTORING_CANDIDATE: self._detect_refactoring_candidates
        }
    
    def _detect_design_patterns(self, tree: ast.AST, lines: List[str], file_path: str) -> List[AdvancedCodeInsight]:
        """Detect design patterns in code"""
        insights = []
        
        # Singleton pattern detection
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_singleton_pattern(node):
                    insights.append(AdvancedCodeInsight(
                        insight_type=CodePattern.DESIGN_PATTERN,
                        location=(node.lineno, getattr(node, 'end_lineno', node.lineno)),
                        description=f"Singleton pattern detected in class '{node.name}'",
                        confidence=0.8,
                        impact_score=0.6,
                        recommendations=["Ensure thread safety", "Consider dependency injection alternatives"],
                        affected_components=[node.name]
                    ))
        
        return insights
    
    def _detect_anti_patterns(self, tree: ast.AST, lines: List[str], file_path: str) -> List[AdvancedCodeInsight]:
        """Detect anti-patterns in code"""
        insights = []
        
        # God class detection
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                if method_count > 20:
                    insights.append(AdvancedCodeInsight(
                        insight_type=CodePattern.ANTI_PATTERN,
                        location=(node.lineno, getattr(node, 'end_lineno', node.lineno)),
                        description=f"God class detected: '{node.name}' has {method_count} methods",
                        confidence=0.9,
                        impact_score=0.8,
                        recommendations=["Break into smaller, focused classes", "Apply Single Responsibility Principle"],
                        affected_components=[node.name]
                    ))
        
        return insights
    
    def _detect_complexity_hotspots(self, tree: ast.AST, lines: List[str], file_path: str) -> List[AdvancedCodeInsight]:
        """Detect complexity hotspots"""
        insights = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 15:
                    insights.append(AdvancedCodeInsight(
                        insight_type=CodePattern.COMPLEXITY_HOTSPOT,
                        location=(node.lineno, getattr(node, 'end_lineno', node.lineno)),
                        description=f"High complexity function: '{node.name}' (complexity: {complexity})",
                        confidence=0.95,
                        impact_score=min(1.0, complexity / 20.0),
                        recommendations=["Refactor to reduce complexity", "Extract helper functions", "Simplify control flow"],
                        affected_components=[node.name]
                    ))
        
        return insights
    
    def _detect_optimization_opportunities(self, tree: ast.AST, lines: List[str], file_path: str) -> List[AdvancedCodeInsight]:
        """Detect optimization opportunities"""
        insights = []
        
        # Detect nested loops
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                nested_loops = self._count_nested_loops(node)
                if nested_loops > 2:
                    insights.append(AdvancedCodeInsight(
                        insight_type=CodePattern.OPTIMIZATION_OPPORTUNITY,
                        location=(node.lineno, getattr(node, 'end_lineno', node.lineno)),
                        description=f"Nested loops detected (depth: {nested_loops})",
                        confidence=0.7,
                        impact_score=0.6,
                        recommendations=["Consider algorithm optimization", "Look for vectorization opportunities"],
                        affected_components=[]
                    ))
        
        return insights
    
    def _detect_refactoring_candidates(self, tree: ast.AST, lines: List[str], file_path: str) -> List[AdvancedCodeInsight]:
        """Detect refactoring candidates"""
        insights = []
        
        # Long parameter lists
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > 6:
                    insights.append(AdvancedCodeInsight(
                        insight_type=CodePattern.REFACTORING_CANDIDATE,
                        location=(node.lineno, node.lineno),
                        description=f"Function '{node.name}' has {param_count} parameters",
                        confidence=0.8,
                        impact_score=0.5,
                        recommendations=["Consider parameter object pattern", "Group related parameters"],
                        affected_components=[node.name]
                    ))
        
        return insights
    
    def _is_singleton_pattern(self, class_node: ast.ClassDef) -> bool:
        """Check if class implements singleton pattern"""
        # Simple heuristic: look for instance variable and getInstance method
        has_instance_var = False
        has_get_instance = False
        
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and 'instance' in target.id.lower():
                        has_instance_var = True
            elif isinstance(node, ast.FunctionDef):
                if 'instance' in node.name.lower() or 'singleton' in node.name.lower():
                    has_get_instance = True
        
        return has_instance_var or has_get_instance
    
    def _count_nested_loops(self, node: ast.AST) -> int:
        """Count nested loop depth"""
        max_depth = 0
        
        def count_depth(node, current_depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.For, ast.While)):
                    count_depth(child, current_depth + 1)
                else:
                    count_depth(child, current_depth)
        
        count_depth(node, 1)
        return max_depth
    
    def _discover_python_files(self, root_path: str) -> List[str]:
        """Discover Python files in directory tree"""
        python_files = []

        for root, dirs, files in os.walk(root_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
            for d in dirs:
                init_file = os.path.join(root, d, '__init__.py')
                if os.path.exists(init_file):
                    python_files.append(init_file)
        
        return python_files
    
    def _insight_to_dict(self, insight: AdvancedCodeInsight) -> Dict[str, Any]:
        """Convert insight to dictionary"""
        return {
            'insight_type': insight.insight_type.value,
            'location': insight.location,
            'description': insight.description,
            'confidence': insight.confidence,
            'impact_score': insight.impact_score,
            'recommendations': insight.recommendations,
            'affected_components': insight.affected_components,
            'dependencies': insight.dependencies
        }
    
    def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis summary"""
        return {
            'total_files': analysis_results['files_analyzed'],
            'total_insights': analysis_results['total_insights'],
            'insight_distribution': analysis_results['insights_by_type'],
            'quality_assessment': 'good' if analysis_results['total_insights'] < 10 else 'needs_attention',
            'top_issues': self._get_top_issues(analysis_results)
        }
    
    def _generate_codebase_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate codebase-level recommendations"""
        recommendations = []
        
        total_insights = analysis_results['total_insights']
        if total_insights > 20:
            recommendations.append("Consider systematic refactoring to address code quality issues")
        
        insights_by_type = analysis_results['insights_by_type']
        if insights_by_type.get('anti_pattern', 0) > 3:
            recommendations.append("Focus on eliminating anti-patterns to improve maintainability")
        
        if insights_by_type.get('complexity_hotspot', 0) > 5:
            recommendations.append("Prioritize complexity reduction in identified hotspots")
        
        return recommendations
    
    def _get_top_issues(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get top issues from analysis"""
        all_insights = []
        
        for file_path, file_data in analysis_results['files'].items():
            if 'insights' in file_data:
                for insight in file_data['insights']:
                    insight['file_path'] = file_path
                    all_insights.append(insight)
        
        # Sort by impact score and return top 5
        all_insights.sort(key=lambda x: x.get('impact_score', 0), reverse=True)
        return all_insights[:5]

# ============================================================================
# UNIFIED CODE INTELLIGENCE INTERFACE
# ============================================================================

class CodeIntelligenceAnalyzer:
    """Unified interface for comprehensive code intelligence analysis"""
    
    def __init__(self, root_path: str, config: Optional[Dict[str, Any]] = None):
        self.root_path = Path(root_path)
        self.config = config or {}
        
        # Initialize component analyzers
        self.archaeologist = ProjectArchaeologist(self.root_path, config)
        self.rsa_analyzer = RSAAnalyzer()
        self.extended_analyzer = ExtendedCodeAnalyzer()
        
        self.analysis_results = {}
    
    def comprehensive_analysis(self, lightweight_mode: bool = False) -> Dict[str, Any]:
        """Perform comprehensive code intelligence analysis"""
        if lightweight_mode:
            print("🧠 Starting lightweight code intelligence analysis...")
            return self._lightweight_analysis()
        
        print("🧠 Starting comprehensive code intelligence analysis...")
        
        # 1. Archaeological excavation
        print("🏛️ Phase 1: Archaeological excavation...")
        archaeological_report = self.archaeologist.excavate_project()
        
        # 2. Extended code analysis
        print("🔍 Phase 2: Extended semantic analysis...")
        extended_analysis = self.extended_analyzer.analyze_codebase(str(self.root_path))
        
        # 3. RSA analysis on discovered components
        print("🔧 Phase 3: RSA enhancement analysis...")
        rsa_results = {}
        for cluster_name, cluster_data in archaeological_report.get('clusters', {}).items():
            component_data = {
                'files': len(cluster_data),
                'python_files': sum(1 for artifact in cluster_data if artifact.get('type') == 'python_source')
            }
            rsa_results[cluster_name] = self.rsa_analyzer.analyze_component_with_rsa(cluster_name, component_data)
        
        # 4. Synthesize results
        synthesis = self._synthesize_analysis_results(archaeological_report, extended_analysis, rsa_results)
        
        self.analysis_results = {
            'archaeological_report': archaeological_report,
            'extended_analysis': extended_analysis,
            'rsa_analysis': rsa_results,
            'synthesis': synthesis,
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'analyzer_version': "1.0.0", # Use a literal string here
                'root_path': str(self.root_path)
            }
        }
        
        print("✅ Comprehensive analysis complete!")
        return self.analysis_results
    
    def _lightweight_analysis(self) -> Dict[str, Any]:
        """Perform fast, lightweight analysis for quick operations"""
        import os
        from pathlib import Path
        from datetime import datetime
        
        print("⚡ Performing lightweight directory scan...")
        
        # Quick directory statistics without heavy analysis
        root_path = Path(self.root_path)
        total_files = 0
        python_files = 0
        
        try:
            # Limited scan to avoid performance issues
            for item in root_path.rglob("*"):
                if item.is_file() and not any(skip in str(item) for skip in ['.git', '__pycache__', '.venv']):
                    total_files += 1
                    if item.suffix == '.py':
                        python_files += 1
                    # Limit scan to prevent blocking
                    if total_files > 1000:
                        break
        except Exception:
            total_files = 0
            python_files = 0
        
        # Create lightweight results
        lightweight_results = {
            'mode': 'lightweight',
            'archaeological_report': {
                'metadata': {
                    'total_artifacts': total_files,
                    'total_clusters': 1,
                    'analysis_mode': 'lightweight'
                },
                'statistics': {
                    'total_lines_of_code': python_files * 50,  # Rough estimate
                    'python_files': python_files
                }
            },
            'synthesis': {
                'overall_health_score': 0.7,  # Default reasonable score
                'key_recommendations': ['Run full analysis for detailed insights'],
                'priority_actions': [{'action': 'consider_full_analysis', 'priority': 'medium'}],
                'architecture_insights': {'complexity': 'moderate'},
                'optimization_opportunities': ['Enable full analysis mode']
            },
            'metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'analyzer_version': "1.0.0-lightweight",
                'root_path': str(self.root_path)
            }
        }
        
        self.analysis_results = lightweight_results
        print("✅ Lightweight analysis complete!")
        return self.analysis_results
    
    def _synthesize_analysis_results(self, archaeological: Dict, extended: Dict, rsa: Dict) -> Dict[str, Any]:
        """Synthesize results from all analysis components"""
        return {
            'overall_health_score': self._calculate_overall_health(archaeological, extended, rsa),
            'key_recommendations': self._generate_key_recommendations(archaeological, extended, rsa),
            'priority_actions': self._identify_priority_actions(archaeological, extended, rsa),
            'architecture_insights': self._extract_architecture_insights(archaeological, extended, rsa),
            'optimization_opportunities': self._consolidate_optimization_opportunities(archaeological, extended, rsa)
        }
    
    def _calculate_overall_health(self, archaeological: Dict, extended: Dict, rsa: Dict) -> float:
        """Calculate overall codebase health score"""
        # Simple scoring based on various factors
        arch_score = min(archaeological['statistics']['total_lines_of_code'] / 10000, 1.0)
        
        extended_score = 0.8  # Default good score
        if 'summary' in extended:
            quality = extended['summary'].get('quality_assessment', 'good')
            extended_score = {'good': 0.8, 'needs_attention': 0.5, 'poor': 0.2}.get(quality, 0.6)
        
        rsa_scores = [result.get('optimization_score', 0.5) for result in rsa.values()]
        avg_rsa_score = sum(rsa_scores) / max(len(rsa_scores), 1)
        
        return (arch_score + extended_score + avg_rsa_score) / 3
    
    def _generate_key_recommendations(self, archaeological: Dict, extended: Dict, rsa: Dict) -> List[str]:
        """Generate key recommendations from all analyses"""
        recommendations = []
        
        # From archaeological analysis
        total_artifacts = archaeological['metadata']['total_artifacts']
        if total_artifacts > 100:
            recommendations.append("Consider modularizing the large codebase into smaller, focused components")
        
        # From extended analysis
        if 'summary' in extended and 'recommendations' in extended['summary']:
            recommendations.extend(extended['summary']['recommendations'][:2])
        
        # From RSA analysis
        for component, analysis in rsa.items():
            if analysis['optimization_score'] < 0.5:
                recommendations.append(f"Focus on improving {component} architecture and collaboration patterns")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _identify_priority_actions(self, archaeological: Dict, extended: Dict, rsa: Dict) -> List[Dict[str, Any]]:
        """Identify priority actions based on analysis"""
        actions = []
        
        # High-impact, low-effort actions
        if archaeological['statistics']['total_lines_of_code'] > 50000:
            actions.append({
                'action': 'Implement automated code quality checks',
                'priority': 'high',
                'effort': 'medium',
                'impact': 'high'
            })
        
        return actions
    
    def _extract_architecture_insights(self, archaeological: Dict, extended: Dict, rsa: Dict) -> Dict[str, Any]:
        """Extract architectural insights"""
        return {
            'dependency_complexity': len(archaeological['dependency_graph']['edges']),
            'modular_organization': len(archaeological['clusters']),
            'code_distribution': archaeological['statistics']['file_types'],
            'temporal_patterns': f"{len(archaeological['clusters'])} development clusters identified"
        }
    
    def _consolidate_optimization_opportunities(self, archaeological: Dict, extended: Dict, rsa: Dict) -> List[Dict[str, Any]]:
        """Consolidate optimization opportunities from all analyses"""
        opportunities = []
        
        # From archaeological clustering
        if len(archaeological['clusters']) > 10:
            opportunities.append({
                'type': 'structural',
                'description': 'High number of temporal clusters suggests frequent context switching',
                'recommendation': 'Consider consolidating related development efforts'
            })
        
        return opportunities
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate comprehensive analysis report"""
        if not self.analysis_results:
            raise ValueError("No analysis results available. Run comprehensive_analysis() first.")
        
        report_content = self._format_analysis_report()
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_content)
            print(f"📄 Report saved to: {output_path}")
        
        return report_content
    
    def _format_analysis_report(self) -> str:
        """Format analysis results into readable report"""
        results = self.analysis_results
        synthesis = results['synthesis']
        
        report = f"""# Code Intelligence Analysis Report
Generated: {results['metadata']['analysis_timestamp']}
Root Path: {results['metadata']['root_path']}

## Executive Summary
Overall Health Score: {synthesis['overall_health_score']:.2f}/1.0

## Key Findings
### Archaeological Analysis
- Total Artifacts: {results['archaeological_report']['metadata']['total_artifacts']}
- Project Clusters: {results['archaeological_report']['metadata']['total_clusters']}
- Lines of Code: {results['archaeological_report']['statistics']['total_lines_of_code']}

### Architecture Insights
- Dependency Complexity: {synthesis['architecture_insights']['dependency_complexity']} connections
- Modular Organization: {synthesis['architecture_insights']['modular_organization']} clusters
- Temporal Patterns: {synthesis['architecture_insights']['temporal_patterns']}

## Priority Recommendations
"""
        for i, rec in enumerate(synthesis['key_recommendations'], 1):
            report += f"{i}. {rec}\n"
        
        report += "\n## Optimization Opportunities\n"
        for opp in synthesis['optimization_opportunities']:
            report += f"- **{opp['type'].title()}**: {opp['description']}\n"
            report += f"  *Recommendation*: {opp['recommendation']}\n\n"
        
        return report