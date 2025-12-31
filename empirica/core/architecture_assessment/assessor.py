"""
Component Assessor

Main orchestrator that combines all analyzers to produce a unified
epistemic assessment of a code component.

This is the "turtles all the way down" module - Empirica assessing itself.
"""

from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .schema import (
    ComponentAssessment,
    ArchitectureVectors,
    CouplingMetrics,
    StabilityMetrics,
)
from .coupling_analyzer import CouplingAnalyzer
from .stability_estimator import StabilityEstimator


class ComponentAssessor:
    """
    Unified assessment of code components using epistemic vectors.

    Combines:
    - CouplingAnalyzer: Dependencies, API surface, boundaries
    - StabilityEstimator: Git history, churn, ownership

    Produces: ComponentAssessment with risk level and recommendations
    """

    def __init__(self, project_root: str):
        """
        Initialize assessor with all analyzers.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.coupling_analyzer = CouplingAnalyzer(project_root)
        self.stability_estimator = StabilityEstimator(project_root)

    def assess(self, component_path: str) -> ComponentAssessment:
        """
        Perform full epistemic assessment of a component.

        Args:
            component_path: Path to file or package

        Returns:
            ComponentAssessment with vectors, metrics, and recommendations
        """
        path = Path(component_path)
        if not path.is_absolute():
            path = self.project_root / component_path

        # Determine component type
        if path.is_dir():
            component_type = "package"
            component_name = path.name
        elif path.suffix == ".py":
            component_type = "module"
            component_name = path.stem
        else:
            component_type = "file"
            component_name = path.name

        # Run analyzers
        coupling_metrics = self.coupling_analyzer.analyze(str(path))
        stability_metrics = self.stability_estimator.analyze(str(path))

        # Convert to vectors
        coupling_vectors = self.coupling_analyzer.to_vectors(coupling_metrics)
        stability_vectors = self.stability_estimator.to_vectors(stability_metrics)

        # Combine into unified vectors
        vectors = self._combine_vectors(coupling_vectors, stability_vectors, path)

        # Determine risk level
        risk_level = self._calculate_risk(vectors, coupling_metrics, stability_metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            vectors, coupling_metrics, stability_metrics
        )

        # Prioritize improvements
        priority = self._prioritize_improvements(vectors)

        return ComponentAssessment(
            component_path=str(path),
            component_name=component_name,
            component_type=component_type,
            vectors=vectors,
            coupling=coupling_metrics,
            stability=stability_metrics,
            analyzed_at=datetime.now(),
            risk_level=risk_level,
            recommendations=recommendations,
            improvement_priority=priority,
        )

    def _combine_vectors(
        self,
        coupling: dict,
        stability: dict,
        path: Path,
    ) -> ArchitectureVectors:
        """Combine analyzer outputs into unified vectors."""
        vectors = ArchitectureVectors()

        # From coupling analyzer
        vectors.clarity = coupling.get('clarity', 0.5)
        vectors.context = coupling.get('context', 0.5)
        vectors.impact = coupling.get('impact', 0.5)

        # From stability estimator
        vectors.change = stability.get('change', 0.5)
        vectors.engagement = stability.get('engagement', 0.5)
        vectors.signal = stability.get('signal', 0.5)

        # Derived/estimated vectors (would need additional analyzers)
        # For now, use reasonable defaults based on available data

        # Know: Based on documentation presence (simplified)
        vectors.know = self._estimate_documentation(path)

        # Uncertainty: Inverse of clarity and stability
        vectors.uncertainty = 1.0 - (vectors.clarity + (1.0 - vectors.change)) / 2

        # Coherence: Based on module size (small = focused)
        vectors.coherence = self._estimate_coherence(path)

        # Density: Complexity estimate (would need proper analysis)
        vectors.density = 0.5  # Placeholder

        # State: Health indicators (would need test coverage data)
        vectors.state = 0.5  # Placeholder

        # Completion: Based on TODO/FIXME count
        vectors.completion = self._estimate_completion(path)

        # Do: Based on clear interface and low complexity
        vectors.do = (vectors.clarity + (1.0 - vectors.density)) / 2

        return vectors

    def _estimate_documentation(self, path: Path) -> float:
        """Estimate documentation level from docstrings."""
        if path.is_dir():
            py_files = list(path.rglob("*.py"))
        else:
            py_files = [path]

        total_funcs = 0
        documented_funcs = 0

        for py_file in py_files:
            try:
                content = py_file.read_text()
                # Count function definitions
                func_count = content.count('def ')
                # Count docstrings (triple quotes after def)
                doc_count = len([
                    1 for line in content.split('def ')[1:]
                    if '"""' in line.split('\n')[1] if len(line.split('\n')) > 1
                ])
                total_funcs += func_count
                documented_funcs += min(doc_count, func_count)
            except (OSError, UnicodeDecodeError):
                pass

        if total_funcs == 0:
            return 0.5
        return min(documented_funcs / total_funcs, 1.0)

    def _estimate_coherence(self, path: Path) -> float:
        """Estimate single-responsibility adherence from size."""
        if path.is_dir():
            py_files = list(path.rglob("*.py"))
            total_lines = sum(
                len(f.read_text().splitlines())
                for f in py_files
                if f.exists()
            )
        else:
            try:
                total_lines = len(path.read_text().splitlines())
            except (OSError, UnicodeDecodeError):
                return 0.5

        # Smaller is more focused
        # <200 lines = very focused (1.0)
        # >1000 lines = probably too big (0.3)
        if total_lines < 200:
            return 1.0
        elif total_lines > 1000:
            return 0.3
        else:
            return 1.0 - ((total_lines - 200) / 800) * 0.7

    def _estimate_completion(self, path: Path) -> float:
        """Estimate completion based on TODO/FIXME markers."""
        if path.is_dir():
            py_files = list(path.rglob("*.py"))
        else:
            py_files = [path]

        total_lines = 0
        todo_count = 0

        for py_file in py_files:
            try:
                content = py_file.read_text()
                lines = content.splitlines()
                total_lines += len(lines)
                todo_count += sum(
                    1 for line in lines
                    if 'TODO' in line or 'FIXME' in line or 'XXX' in line
                )
            except (OSError, UnicodeDecodeError):
                pass

        if total_lines == 0:
            return 0.5

        # Lower TODO density = more complete
        todo_density = todo_count / total_lines
        return max(0.0, 1.0 - (todo_density * 50))  # 2% TODOs = 0.0 completion

    def _calculate_risk(
        self,
        vectors: ArchitectureVectors,
        coupling: CouplingMetrics,
        stability: StabilityMetrics,
    ) -> str:
        """Calculate overall risk level."""
        confidence = vectors.confidence_score()

        # High impact + high change = critical
        if vectors.impact > 0.7 and vectors.change > 0.7:
            return "critical"

        # Low confidence overall
        if confidence < 0.4:
            return "high"

        # Moderate concerns
        if confidence < 0.6 or vectors.uncertainty > 0.6:
            return "medium"

        return "low"

    def _generate_recommendations(
        self,
        vectors: ArchitectureVectors,
        coupling: CouplingMetrics,
        stability: StabilityMetrics,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # API surface issues
        if not coupling.clear_interface:
            recommendations.append(
                f"Clean up leaked internals: {coupling.leaked_internals}"
            )

        if coupling.api_surface_ratio < 0.3:
            recommendations.append(
                "Low public API ratio - consider exposing more functionality or extracting private code"
            )

        # Coupling issues
        if coupling.instability > 0.8:
            recommendations.append(
                "High instability - depends on many modules but few depend on it. "
                "Consider stabilizing core dependencies."
            )

        if coupling.distance_from_main > 0.5:
            recommendations.append(
                "Far from ideal balance of abstractness/stability. "
                "Either add abstractions or reduce dependencies."
            )

        # Stability issues
        if stability.churn_rate > 2.0:
            recommendations.append(
                "Very high churn rate - component changes frequently. "
                "Consider breaking into smaller, more stable pieces."
            )

        if stability.hotspot_score > 5.0:
            recommendations.append(
                "Hotspot detected - frequently changed AND complex. "
                "Priority candidate for refactoring."
            )

        if stability.unique_authors == 1 and stability.total_commits > 20:
            recommendations.append(
                "Single author for substantial code - bus factor risk. "
                "Consider knowledge sharing."
            )

        if stability.days_since_last_change > 365:
            recommendations.append(
                "Not modified in over a year - may be stable OR abandoned. "
                "Verify it still works as expected."
            )

        # Vector-based recommendations
        if vectors.know < 0.4:
            recommendations.append(
                "Low documentation - add docstrings and comments."
            )

        if vectors.completion < 0.5:
            recommendations.append(
                "Many TODOs/FIXMEs - address technical debt markers."
            )

        if vectors.coherence < 0.5:
            recommendations.append(
                "Large module - consider splitting into focused components."
            )

        return recommendations

    def _prioritize_improvements(self, vectors: ArchitectureVectors) -> List[str]:
        """Prioritize which vectors to improve first."""
        # Calculate which vectors are furthest from ideal
        scores = {
            'know': vectors.know,
            'clarity': vectors.clarity,
            'coherence': vectors.coherence,
            'completion': vectors.completion,
            # Inverted (low is good)
            'uncertainty': 1.0 - vectors.uncertainty,
            'change': 1.0 - vectors.change,
            'impact': 1.0 - vectors.impact,
        }

        # Sort by lowest score (most needs improvement)
        sorted_vectors = sorted(scores.items(), key=lambda x: x[1])

        # Return top 3 needing improvement
        return [v[0] for v in sorted_vectors[:3]]

    def assess_multiple(self, paths: List[str]) -> List[ComponentAssessment]:
        """Assess multiple components."""
        return [self.assess(path) for path in paths]

    def compare(
        self,
        path_a: str,
        path_b: str,
    ) -> dict:
        """Compare two components."""
        assessment_a = self.assess(path_a)
        assessment_b = self.assess(path_b)

        vectors_a = assessment_a.vectors.to_dict()
        vectors_b = assessment_b.vectors.to_dict()

        comparison = {
            'component_a': assessment_a.component_name,
            'component_b': assessment_b.component_name,
            'confidence_a': assessment_a.vectors.confidence_score(),
            'confidence_b': assessment_b.vectors.confidence_score(),
            'risk_a': assessment_a.risk_level,
            'risk_b': assessment_b.risk_level,
            'vector_differences': {
                k: vectors_a[k] - vectors_b[k]
                for k in vectors_a
            },
            'healthier': (
                assessment_a.component_name
                if assessment_a.vectors.confidence_score() > assessment_b.vectors.confidence_score()
                else assessment_b.component_name
            ),
        }

        return comparison
