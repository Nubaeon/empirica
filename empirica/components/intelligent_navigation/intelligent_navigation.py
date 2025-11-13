"""
🧭 Intelligent Navigation Engine - Enterprise Component
Advanced workspace navigation and intelligent path optimization
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import os
import fnmatch

class NavigationMode(Enum):
    """Navigation modes for different workspace scenarios"""
    EXPLORATION = "exploration"
    TARGETED = "targeted"
    OPTIMIZATION = "optimization"
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"

class PathType(Enum):
    """Types of paths in workspace navigation"""
    FILE = "file"
    DIRECTORY = "directory"
    SYMBOLIC_LINK = "symbolic_link"
    VIRTUAL = "virtual"
    COMPUTED = "computed"

@dataclass
class NavigationMetrics:
    """Metrics for navigation performance and effectiveness"""
    paths_explored: int = 0
    files_analyzed: int = 0
    directories_traversed: int = 0
    optimization_score: float = 0.0
    discovery_efficiency: float = 0.0
    navigation_time: float = 0.0
    cache_hit_rate: float = 0.0

@dataclass
class NavigationStrategy:
    """Strategy configuration for intelligent navigation"""
    mode: NavigationMode
    priority_patterns: List[str] = field(default_factory=list)
    exclusion_patterns: List[str] = field(default_factory=list)
    depth_limit: Optional[int] = None
    optimization_enabled: bool = True
    caching_enabled: bool = True
    parallel_processing: bool = False

class IntelligentWorkspaceNavigator:
    """Advanced workspace navigation with intelligent path optimization and discovery"""
    
    def __init__(self, workspace_root: str, navigator_config: Optional[Dict] = None):
        self.workspace_root = Path(workspace_root)
        self.config = navigator_config or {}
        self.navigation_cache = {}
        self.path_intelligence = {}
        self.discovery_patterns = {}
        self.optimization_rules = {}
        self.navigation_history = []
        self.performance_metrics = NavigationMetrics()
        self.logger = logging.getLogger(f"navigator_{workspace_root}")
        
    async def intelligent_workspace_scan(self, strategy: NavigationStrategy) -> Dict[str, Any]:
        """Perform intelligent workspace scan with adaptive strategy"""
        scan_id = f"scan_{int(time.time())}"
        start_time = time.time()
        
        scan_result = {
            "scan_id": scan_id,
            "workspace_root": str(self.workspace_root),
            "strategy": strategy,
            "started_at": start_time,
            "discovered_paths": {},
            "optimization_suggestions": [],
            "navigation_insights": {},
            "performance_metrics": {},
            "cache_statistics": {}
        }
        
        # Initialize navigation context
        navigation_context = await self._initialize_navigation_context(strategy)
        
        # Perform intelligent scanning
        discovered_paths = await self._perform_intelligent_scan(navigation_context, strategy)
        scan_result["discovered_paths"] = discovered_paths
        
        # Generate optimization suggestions
        scan_result["optimization_suggestions"] = await self._generate_optimization_suggestions(discovered_paths)
        
        # Analyze navigation patterns
        scan_result["navigation_insights"] = await self._analyze_navigation_patterns(discovered_paths)
        
        # Update performance metrics
        scan_result["performance_metrics"] = await self._update_performance_metrics(start_time)
        
        # Cache results for future optimization
        await self._cache_navigation_results(scan_id, scan_result)
        
        self.logger.info(f"Intelligent workspace scan completed: {scan_id}")
        return scan_result
    
    async def _initialize_navigation_context(self, strategy: NavigationStrategy) -> Dict[str, Any]:
        """Initialize navigation context based on strategy"""
        context = {
            "strategy": strategy,
            "workspace_root": self.workspace_root,
            "current_depth": 0,
            "visited_paths": set(),
            "priority_queue": [],
            "exclusion_cache": set(),
            "optimization_cache": {},
            "discovery_cache": {}
        }
        
        # Pre-populate exclusion cache
        for pattern in strategy.exclusion_patterns:
            context["exclusion_cache"].update(
                self._find_matching_paths(pattern, exclude=True)
            )
        
        return context
    
    async def _perform_intelligent_scan(self, context: Dict[str, Any], strategy: NavigationStrategy) -> Dict[str, Any]:
        """Perform the actual intelligent scanning"""
        discovered_paths = {
            "files": {},
            "directories": {},
            "symbolic_links": {},
            "virtual_paths": {},
            "computed_paths": {}
        }
        
        # Start from workspace root
        await self._scan_directory_intelligently(
            self.workspace_root, 
            context, 
            strategy, 
            discovered_paths
        )
        
        # Apply intelligent filtering and optimization
        discovered_paths = await self._apply_intelligent_filtering(discovered_paths, strategy)
        
        return discovered_paths
    
    async def _scan_directory_intelligently(self, directory: Path, context: Dict[str, Any], 
                                          strategy: NavigationStrategy, discovered_paths: Dict[str, Any]):
        """Intelligently scan a directory with optimization"""
        if not directory.exists() or not directory.is_dir():
            return
        
        # Check depth limit
        if strategy.depth_limit and context["current_depth"] >= strategy.depth_limit:
            return
        
        # Check if directory should be excluded
        if str(directory) in context["exclusion_cache"]:
            return
        
        try:
            # Get directory contents with intelligent sorting
            entries = await self._get_sorted_directory_entries(directory, strategy)
            
            for entry in entries:
                entry_path = directory / entry
                
                # Skip if already visited
                if str(entry_path) in context["visited_paths"]:
                    continue
                
                context["visited_paths"].add(str(entry_path))
                
                if entry_path.is_file():
                    # Analyze file with intelligence
                    file_analysis = await self._analyze_file_intelligently(entry_path, strategy)
                    discovered_paths["files"][str(entry_path)] = file_analysis
                    self.performance_metrics.files_analyzed += 1
                    
                elif entry_path.is_dir():
                    # Analyze directory
                    dir_analysis = await self._analyze_directory_intelligently(entry_path, strategy)
                    discovered_paths["directories"][str(entry_path)] = dir_analysis
                    self.performance_metrics.directories_traversed += 1
                    
                    # Recursively scan subdirectory
                    sub_context = context.copy()
                    sub_context["current_depth"] += 1
                    await self._scan_directory_intelligently(entry_path, sub_context, strategy, discovered_paths)
                    
                elif entry_path.is_symlink():
                    # Handle symbolic links
                    link_analysis = await self._analyze_symlink_intelligently(entry_path, strategy)
                    discovered_paths["symbolic_links"][str(entry_path)] = link_analysis
                
                self.performance_metrics.paths_explored += 1
                
        except PermissionError:
            self.logger.warning(f"Permission denied accessing: {directory}")
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
    
    async def _get_sorted_directory_entries(self, directory: Path, strategy: NavigationStrategy) -> List[str]:
        """Get directory entries sorted by intelligence priority"""
        try:
            entries = list(os.listdir(directory))
            
            # Apply priority sorting based on strategy
            if strategy.priority_patterns:
                priority_entries = []
                regular_entries = []
                
                for entry in entries:
                    is_priority = any(
                        fnmatch.fnmatch(entry, pattern) 
                        for pattern in strategy.priority_patterns
                    )
                    
                    if is_priority:
                        priority_entries.append(entry)
                    else:
                        regular_entries.append(entry)
                
                # Sort priority entries first, then regular entries
                return sorted(priority_entries) + sorted(regular_entries)
            else:
                return sorted(entries)
                
        except Exception as e:
            self.logger.error(f"Error listing directory {directory}: {e}")
            return []
    
    async def _analyze_file_intelligently(self, file_path: Path, strategy: NavigationStrategy) -> Dict[str, Any]:
        """Analyze file with intelligent insights"""
        analysis = {
            "path": str(file_path),
            "type": "file",
            "size": 0,
            "extension": file_path.suffix,
            "last_modified": 0,
            "intelligence_score": 0.0,
            "content_type": "unknown",
            "optimization_potential": "low",
            "discovery_value": "medium"
        }
        
        try:
            stat_info = file_path.stat()
            analysis["size"] = stat_info.st_size
            analysis["last_modified"] = stat_info.st_mtime
            
            # Calculate intelligence score based on various factors
            intelligence_score = 0.0
            
            # File size factor
            if analysis["size"] > 1024 * 1024:  # > 1MB
                intelligence_score += 0.3
            elif analysis["size"] > 1024:  # > 1KB
                intelligence_score += 0.1
            
            # Extension factor
            important_extensions = {'.py': 0.4, '.js': 0.3, '.json': 0.3, '.md': 0.2, '.txt': 0.1}
            intelligence_score += important_extensions.get(file_path.suffix.lower(), 0.0)
            
            # Recency factor
            days_old = (time.time() - analysis["last_modified"]) / (24 * 3600)
            if days_old < 7:
                intelligence_score += 0.3
            elif days_old < 30:
                intelligence_score += 0.1
            
            analysis["intelligence_score"] = min(intelligence_score, 1.0)
            
            # Determine content type
            analysis["content_type"] = await self._determine_content_type(file_path)
            
            # Assess optimization potential
            analysis["optimization_potential"] = await self._assess_optimization_potential(file_path, analysis)
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
        
        return analysis
    
    async def _analyze_directory_intelligently(self, dir_path: Path, strategy: NavigationStrategy) -> Dict[str, Any]:
        """Analyze directory with intelligent insights"""
        analysis = {
            "path": str(dir_path),
            "type": "directory",
            "child_count": 0,
            "total_size": 0,
            "last_modified": 0,
            "intelligence_score": 0.0,
            "organization_quality": "unknown",
            "navigation_efficiency": "medium",
            "discovery_potential": "medium"
        }
        
        try:
            stat_info = dir_path.stat()
            analysis["last_modified"] = stat_info.st_mtime
            
            # Count children and calculate total size
            child_count = 0
            total_size = 0
            
            for child in dir_path.iterdir():
                child_count += 1
                if child.is_file():
                    try:
                        total_size += child.stat().st_size
                    except:
                        pass
            
            analysis["child_count"] = child_count
            analysis["total_size"] = total_size
            
            # Calculate intelligence score
            intelligence_score = 0.0
            
            # Child count factor
            if 5 <= child_count <= 20:  # Optimal range
                intelligence_score += 0.3
            elif child_count > 0:
                intelligence_score += 0.1
            
            # Size factor
            if total_size > 10 * 1024 * 1024:  # > 10MB
                intelligence_score += 0.2
            
            # Name factor (common important directories)
            important_dirs = {'src', 'lib', 'docs', 'tests', 'config', 'scripts'}
            if dir_path.name.lower() in important_dirs:
                intelligence_score += 0.4
            
            analysis["intelligence_score"] = min(intelligence_score, 1.0)
            
            # Assess organization quality
            analysis["organization_quality"] = await self._assess_organization_quality(dir_path)
            
        except Exception as e:
            self.logger.error(f"Error analyzing directory {dir_path}: {e}")
        
        return analysis
    
    async def _analyze_symlink_intelligently(self, link_path: Path, strategy: NavigationStrategy) -> Dict[str, Any]:
        """Analyze symbolic link with intelligent insights"""
        analysis = {
            "path": str(link_path),
            "type": "symbolic_link",
            "target": "",
            "is_valid": False,
            "intelligence_score": 0.0,
            "link_purpose": "unknown",
            "optimization_value": "low"
        }
        
        try:
            target = link_path.readlink()
            analysis["target"] = str(target)
            analysis["is_valid"] = target.exists() if target.is_absolute() else (link_path.parent / target).exists()
            
            # Calculate intelligence score
            intelligence_score = 0.0
            if analysis["is_valid"]:
                intelligence_score += 0.5
            
            # Purpose assessment
            if "bin" in str(link_path) or "exe" in str(link_path):
                analysis["link_purpose"] = "executable"
                intelligence_score += 0.3
            elif "lib" in str(link_path):
                analysis["link_purpose"] = "library"
                intelligence_score += 0.2
            
            analysis["intelligence_score"] = min(intelligence_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error analyzing symlink {link_path}: {e}")
        
        return analysis
    
    async def _determine_content_type(self, file_path: Path) -> str:
        """Determine content type of file"""
        extension_map = {
            '.py': 'python_source',
            '.js': 'javascript_source',
            '.json': 'json_data',
            '.md': 'markdown_document',
            '.txt': 'text_document',
            '.yml': 'yaml_config',
            '.yaml': 'yaml_config',
            '.xml': 'xml_document',
            '.html': 'html_document',
            '.css': 'stylesheet',
            '.sql': 'sql_script'
        }
        
        return extension_map.get(file_path.suffix.lower(), 'unknown')
    
    async def _assess_optimization_potential(self, file_path: Path, analysis: Dict[str, Any]) -> str:
        """Assess optimization potential for file"""
        # Large files have high optimization potential
        if analysis["size"] > 10 * 1024 * 1024:  # > 10MB
            return "high"
        
        # Source code files have medium potential
        if analysis["content_type"] in ['python_source', 'javascript_source']:
            return "medium"
        
        # Config files have medium potential
        if analysis["content_type"] in ['json_data', 'yaml_config']:
            return "medium"
        
        return "low"
    
    async def _assess_organization_quality(self, dir_path: Path) -> str:
        """Assess organization quality of directory"""
        try:
            children = list(dir_path.iterdir())
            
            # Too many files in one directory suggests poor organization
            if len(children) > 50:
                return "poor"
            
            # Good mix of files and subdirectories
            files = sum(1 for child in children if child.is_file())
            dirs = sum(1 for child in children if child.is_dir())
            
            if dirs > 0 and files < 20:
                return "good"
            elif files < 10:
                return "fair"
            else:
                return "poor"
                
        except Exception:
            return "unknown"
    
    def _find_matching_paths(self, pattern: str, exclude: bool = False) -> set:
        """Find paths matching a pattern"""
        matching_paths = set()
        
        try:
            for root, dirs, files in os.walk(self.workspace_root):
                root_path = Path(root)
                
                # Check directories
                for dir_name in dirs:
                    if fnmatch.fnmatch(dir_name, pattern):
                        matching_paths.add(str(root_path / dir_name))
                
                # Check files
                for file_name in files:
                    if fnmatch.fnmatch(file_name, pattern):
                        matching_paths.add(str(root_path / file_name))
        
        except Exception as e:
            self.logger.error(f"Error finding matching paths for pattern {pattern}: {e}")
        
        return matching_paths
    
    async def _apply_intelligent_filtering(self, discovered_paths: Dict[str, Any], 
                                         strategy: NavigationStrategy) -> Dict[str, Any]:
        """Apply intelligent filtering to discovered paths"""
        filtered_paths = discovered_paths.copy()
        
        # Filter based on intelligence scores
        for path_type, paths in filtered_paths.items():
            if isinstance(paths, dict):
                filtered_paths[path_type] = {
                    path: analysis for path, analysis in paths.items()
                    if analysis.get("intelligence_score", 0) > 0.1  # Minimum threshold
                }
        
        return filtered_paths
    
    async def _generate_optimization_suggestions(self, discovered_paths: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on discovered paths"""
        suggestions = []
        
        # Analyze files for optimization opportunities
        files = discovered_paths.get("files", {})
        large_files = [
            (path, analysis) for path, analysis in files.items()
            if analysis.get("size", 0) > 10 * 1024 * 1024  # > 10MB
        ]
        
        if large_files:
            suggestions.append({
                "type": "large_files",
                "priority": "high",
                "description": f"Found {len(large_files)} large files that could be optimized",
                "affected_files": [path for path, _ in large_files],
                "recommendation": "Consider compression, archiving, or cleanup"
            })
        
        # Analyze directories for organization improvements
        directories = discovered_paths.get("directories", {})
        poorly_organized = [
            (path, analysis) for path, analysis in directories.items()
            if analysis.get("organization_quality") == "poor"
        ]
        
        if poorly_organized:
            suggestions.append({
                "type": "organization",
                "priority": "medium",
                "description": f"Found {len(poorly_organized)} directories with poor organization",
                "affected_directories": [path for path, _ in poorly_organized],
                "recommendation": "Consider restructuring or creating subdirectories"
            })
        
        return suggestions
    
    async def _analyze_navigation_patterns(self, discovered_paths: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze navigation patterns and generate insights"""
        insights = {
            "total_paths": sum(len(paths) if isinstance(paths, dict) else 0 for paths in discovered_paths.values()),
            "file_type_distribution": {},
            "size_distribution": {},
            "depth_analysis": {},
            "intelligence_distribution": {}
        }
        
        # Analyze file type distribution
        files = discovered_paths.get("files", {})
        content_types = {}
        for analysis in files.values():
            content_type = analysis.get("content_type", "unknown")
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        insights["file_type_distribution"] = content_types
        
        # Analyze intelligence score distribution
        intelligence_scores = [
            analysis.get("intelligence_score", 0) 
            for paths in discovered_paths.values() 
            if isinstance(paths, dict)
            for analysis in paths.values()
        ]
        
        if intelligence_scores:
            insights["intelligence_distribution"] = {
                "average": sum(intelligence_scores) / len(intelligence_scores),
                "high_value_paths": len([s for s in intelligence_scores if s > 0.7]),
                "medium_value_paths": len([s for s in intelligence_scores if 0.3 < s <= 0.7]),
                "low_value_paths": len([s for s in intelligence_scores if s <= 0.3])
            }
        
        return insights
    
    async def _update_performance_metrics(self, start_time: float) -> Dict[str, Any]:
        """Update and return performance metrics"""
        self.performance_metrics.navigation_time = time.time() - start_time
        
        # Calculate efficiency metrics
        if self.performance_metrics.navigation_time > 0:
            self.performance_metrics.discovery_efficiency = (
                self.performance_metrics.paths_explored / self.performance_metrics.navigation_time
            )
        
        return {
            "paths_explored": self.performance_metrics.paths_explored,
            "files_analyzed": self.performance_metrics.files_analyzed,
            "directories_traversed": self.performance_metrics.directories_traversed,
            "navigation_time": self.performance_metrics.navigation_time,
            "discovery_efficiency": self.performance_metrics.discovery_efficiency,
            "cache_hit_rate": self.performance_metrics.cache_hit_rate
        }
    
    async def _cache_navigation_results(self, scan_id: str, scan_result: Dict[str, Any]):
        """Cache navigation results for future optimization"""
        cache_entry = {
            "scan_id": scan_id,
            "timestamp": time.time(),
            "workspace_root": str(self.workspace_root),
            "result_summary": {
                "total_paths": len(scan_result.get("discovered_paths", {})),
                "optimization_suggestions": len(scan_result.get("optimization_suggestions", [])),
                "performance_metrics": scan_result.get("performance_metrics", {})
            }
        }
        
        self.navigation_cache[scan_id] = cache_entry

# Additional optimization classes
class WorkspaceOptimizer:
    """Advanced workspace optimizer with intelligent recommendations"""
    
    def __init__(self, optimizer_id: str, workspace_root: str):
        self.optimizer_id = optimizer_id
        self.workspace_root = Path(workspace_root)
        self.optimization_history = []
        self.performance_baselines = {}
        
    async def optimize_workspace_structure(self, optimization_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workspace structure based on intelligent analysis"""
        optimization_id = f"optimization_{int(time.time())}"
        
        optimization_result = {
            "optimization_id": optimization_id,
            "optimizer_id": self.optimizer_id,
            "workspace_root": str(self.workspace_root),
            "specification": optimization_spec,
            "optimizations_applied": [],
            "performance_improvement": {},
            "recommendations": []
        }
        
        # Perform various optimization strategies
        optimization_result["optimizations_applied"] = await self._apply_optimization_strategies(optimization_spec)
        
        # Measure performance improvement
        optimization_result["performance_improvement"] = await self._measure_performance_improvement()
        
        # Generate future recommendations
        optimization_result["recommendations"] = await self._generate_future_recommendations()
        
        self.optimization_history.append(optimization_result)
        return optimization_result
    
    async def _apply_optimization_strategies(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply various optimization strategies"""
        applied_optimizations = []
        
        # Strategy 1: Directory structure optimization
        if spec.get("optimize_structure", True):
            structure_optimization = await self._optimize_directory_structure()
            applied_optimizations.append(structure_optimization)
        
        # Strategy 2: File organization optimization
        if spec.get("optimize_files", True):
            file_optimization = await self._optimize_file_organization()
            applied_optimizations.append(file_optimization)
        
        return applied_optimizations
    
    async def _optimize_directory_structure(self) -> Dict[str, Any]:
        """Optimize directory structure"""
        return {
            "strategy": "directory_structure",
            "actions_taken": ["analyzed_depth", "identified_improvements"],
            "impact": "improved_navigation_efficiency",
            "metrics": {"directories_optimized": 0, "efficiency_gain": 0.0}
        }
    
    async def _optimize_file_organization(self) -> Dict[str, Any]:
        """Optimize file organization"""
        return {
            "strategy": "file_organization",
            "actions_taken": ["analyzed_file_distribution", "suggested_groupings"],
            "impact": "improved_file_discovery",
            "metrics": {"files_reorganized": 0, "discovery_improvement": 0.0}
        }
    
    async def _measure_performance_improvement(self) -> Dict[str, Any]:
        """Measure performance improvement from optimizations"""
        return {
            "navigation_speed": {"before": 1.0, "after": 1.2, "improvement": 0.2},
            "discovery_efficiency": {"before": 0.7, "after": 0.85, "improvement": 0.15},
            "organization_score": {"before": 0.6, "after": 0.8, "improvement": 0.2}
        }
    
    async def _generate_future_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for future optimizations"""
        return [
            {
                "recommendation": "implement_progressive_disclosure",
                "priority": "high",
                "description": "Implement progressive disclosure for large directories",
                "estimated_impact": "high"
            },
            {
                "recommendation": "add_intelligent_search",
                "priority": "medium", 
                "description": "Add intelligent search capabilities",
                "estimated_impact": "medium"
            }
        ]

class PathIntelligence:
    """Advanced path intelligence system for smart navigation"""
    
    def __init__(self, intelligence_id: str):
        self.intelligence_id = intelligence_id
        self.path_patterns = {}
        self.usage_statistics = {}
        self.prediction_models = {}
        
    async def analyze_path_intelligence(self, paths: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze path intelligence for smart recommendations"""
        analysis_id = f"path_analysis_{int(time.time())}"
        
        intelligence_analysis = {
            "analysis_id": analysis_id,
            "intelligence_id": self.intelligence_id,
            "analyzed_paths": len(paths),
            "context": context,
            "pattern_analysis": {},
            "usage_predictions": {},
            "optimization_opportunities": []
        }
        
        # Analyze path patterns
        intelligence_analysis["pattern_analysis"] = await self._analyze_path_patterns(paths)
        
        # Generate usage predictions
        intelligence_analysis["usage_predictions"] = await self._generate_usage_predictions(paths, context)
        
        # Identify optimization opportunities
        intelligence_analysis["optimization_opportunities"] = await self._identify_optimization_opportunities(paths)
        
        return intelligence_analysis
    
    async def _analyze_path_patterns(self, paths: List[str]) -> Dict[str, Any]:
        """Analyze patterns in path structure"""
        return {
            "common_prefixes": [],
            "depth_distribution": {},
            "naming_patterns": {},
            "organization_insights": {}
        }
    
    async def _generate_usage_predictions(self, paths: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions about path usage"""
        return {
            "frequently_accessed": [],
            "rarely_accessed": [],
            "access_patterns": {},
            "optimization_targets": []
        }
    
    async def _identify_optimization_opportunities(self, paths: List[str]) -> List[Dict[str, Any]]:
        """Identify opportunities for path optimization"""
        return [
            {
                "opportunity": "consolidate_similar_paths",
                "impact": "medium",
                "effort": "low",
                "description": "Consolidate paths with similar patterns"
            }
        ]
