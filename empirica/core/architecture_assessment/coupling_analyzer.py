"""
Coupling Analyzer

Analyzes dependency relationships and API surface of a component.

Metrics:
- Afferent coupling (Ca): Who depends on us
- Efferent coupling (Ce): Who we depend on
- Instability (I): Ce / (Ca + Ce)
- API surface ratio: Public / Total functions

Maps to vectors:
- clarity: Clean API surface (high public/private ratio, few leaked internals)
- context: Good integration (balanced coupling, clear boundaries)
- impact: Blast radius (high Ca = breaking changes affect many)
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

from .schema import CouplingMetrics


class CouplingAnalyzer:
    """Analyzes coupling and dependencies for Python modules."""

    def __init__(self, project_root: str):
        """
        Initialize analyzer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self._import_graph: Dict[str, Set[str]] = {}
        self._reverse_graph: Dict[str, Set[str]] = {}

    def analyze(self, component_path: str) -> CouplingMetrics:
        """
        Analyze coupling metrics for a component.

        Args:
            component_path: Path to Python file or package

        Returns:
            CouplingMetrics with dependency analysis
        """
        path = Path(component_path)
        if not path.exists():
            path = self.project_root / component_path

        if path.is_dir():
            return self._analyze_package(path)
        else:
            return self._analyze_module(path)

    def _analyze_module(self, module_path: Path) -> CouplingMetrics:
        """Analyze a single Python file."""
        metrics = CouplingMetrics()

        try:
            content = module_path.read_text()
            tree = ast.parse(content)
        except (SyntaxError, FileNotFoundError) as e:
            return metrics

        # Extract imports (efferent coupling)
        imports = self._extract_imports(tree)
        internal_imports = [i for i in imports if self._is_internal(i)]
        metrics.efferent_coupling = len(internal_imports)

        # Count who imports us (afferent coupling)
        module_name = self._path_to_module(module_path)
        metrics.afferent_coupling = self._count_importers(module_name)

        # Calculate instability
        total = metrics.afferent_coupling + metrics.efferent_coupling
        if total > 0:
            metrics.instability = metrics.efferent_coupling / total
        else:
            metrics.instability = 0.5  # Unknown

        # Analyze API surface
        public, private = self._count_definitions(tree)
        metrics.public_functions = public
        metrics.private_functions = private
        total_funcs = public + private
        if total_funcs > 0:
            metrics.api_surface_ratio = public / total_funcs

        # Check for leaked internals
        metrics.leaked_internals = self._find_leaked_internals(tree)
        metrics.clear_interface = len(metrics.leaked_internals) == 0

        # Calculate abstractness (interfaces/ABCs vs concrete)
        metrics.abstractness = self._calculate_abstractness(tree)

        # Distance from main sequence: |A + I - 1|
        metrics.distance_from_main = abs(
            metrics.abstractness + metrics.instability - 1.0
        )

        return metrics

    def _analyze_package(self, package_path: Path) -> CouplingMetrics:
        """Analyze a Python package (directory with __init__.py)."""
        metrics = CouplingMetrics()

        # Aggregate from all modules
        py_files = list(package_path.rglob("*.py"))

        for py_file in py_files:
            module_metrics = self._analyze_module(py_file)
            metrics.efferent_coupling += module_metrics.efferent_coupling
            metrics.afferent_coupling += module_metrics.afferent_coupling
            metrics.public_functions += module_metrics.public_functions
            metrics.private_functions += module_metrics.private_functions
            metrics.leaked_internals.extend(module_metrics.leaked_internals)

        # Recalculate derived metrics
        total = metrics.afferent_coupling + metrics.efferent_coupling
        if total > 0:
            metrics.instability = metrics.efferent_coupling / total

        total_funcs = metrics.public_functions + metrics.private_functions
        if total_funcs > 0:
            metrics.api_surface_ratio = metrics.public_functions / total_funcs

        metrics.clear_interface = len(metrics.leaked_internals) == 0

        return metrics

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import statements from AST."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def _is_internal(self, import_name: str) -> bool:
        """Check if import is from within the project."""
        # Simple heuristic: starts with project name
        project_name = self.project_root.name
        return import_name.startswith(project_name) or import_name.startswith('.')

    def _count_importers(self, module_name: str) -> int:
        """Count how many modules import this one."""
        if not self._import_graph:
            self._build_import_graph()
        return len(self._reverse_graph.get(module_name, set()))

    def _build_import_graph(self):
        """Build full import graph for the project."""
        py_files = list(self.project_root.rglob("*.py"))

        for py_file in py_files:
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                module_name = self._path_to_module(py_file)
                imports = self._extract_imports(tree)

                self._import_graph[module_name] = set(imports)

                # Build reverse graph
                for imp in imports:
                    if imp not in self._reverse_graph:
                        self._reverse_graph[imp] = set()
                    self._reverse_graph[imp].add(module_name)
            except (SyntaxError, FileNotFoundError):
                continue

    def _path_to_module(self, path: Path) -> str:
        """Convert file path to module name."""
        try:
            rel_path = path.relative_to(self.project_root)
            parts = list(rel_path.parts)
            if parts[-1] == "__init__.py":
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1].replace(".py", "")
            return ".".join(parts)
        except ValueError:
            return path.stem

    def _count_definitions(self, tree: ast.AST) -> Tuple[int, int]:
        """Count public vs private function/class definitions."""
        public = 0
        private = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith('_'):
                    private += 1
                else:
                    public += 1

        return public, private

    def _find_leaked_internals(self, tree: ast.AST) -> List[str]:
        """Find private symbols that are exposed in __all__."""
        leaked = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    name = elt.value
                                    if isinstance(name, str) and name.startswith('_'):
                                        leaked.append(name)

        return leaked

    def _calculate_abstractness(self, tree: ast.AST) -> float:
        """Calculate ratio of abstract types to total types."""
        abstract_count = 0
        total_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                total_count += 1
                # Check for ABC inheritance or abstractmethod decorators
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id in ('ABC', 'ABCMeta'):
                        abstract_count += 1
                        break
                    if isinstance(base, ast.Attribute) and base.attr in ('ABC', 'ABCMeta'):
                        abstract_count += 1
                        break

        if total_count == 0:
            return 0.0
        return abstract_count / total_count

    def to_vectors(self, metrics: CouplingMetrics) -> Dict[str, float]:
        """
        Convert coupling metrics to epistemic vectors.

        Returns:
            Dict with 'clarity', 'context', 'impact' vectors
        """
        # Clarity: Good API surface (high ratio, no leaks)
        clarity = metrics.api_surface_ratio
        if not metrics.clear_interface:
            clarity *= 0.7  # Penalty for leaked internals

        # Context: Balanced coupling, low distance from main sequence
        context = 1.0 - metrics.distance_from_main
        context = max(0.0, min(1.0, context))

        # Impact: Inverse of afferent coupling (more dependents = higher impact)
        # Normalize: assume >20 dependents is high impact
        impact_raw = min(metrics.afferent_coupling / 20.0, 1.0)
        impact = impact_raw  # Note: HIGH impact = HIGH blast radius = risky

        return {
            'clarity': clarity,
            'context': context,
            'impact': impact,
        }
