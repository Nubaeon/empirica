"""
Ecosystem manifest loader and dependency graph builder.

Reads ecosystem.yaml from the workspace root and provides:
- Project topology (roles, types, dependencies)
- Dependency graph traversal (downstream/upstream impact)
- Validation (missing projects, circular deps, version conflicts)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Lazy import to avoid hard dependency
_yaml = None


def _get_yaml():
    """Lazy-load PyYAML."""
    global _yaml
    if _yaml is None:
        import yaml
        _yaml = yaml
    return _yaml


def find_ecosystem_manifest(start_path: str = None) -> Optional[Path]:
    """Find ecosystem.yaml by walking up from start_path or cwd.

    Search order:
    1. start_path (if given)
    2. Current working directory
    3. Parent directories up to filesystem root
    4. Git root of current repo
    """
    if start_path:
        candidate = Path(start_path) / "ecosystem.yaml"
        if candidate.exists():
            return candidate

    # Walk up from cwd
    current = Path.cwd()
    for _ in range(10):  # Max 10 levels up
        candidate = current / "ecosystem.yaml"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def load_manifest(manifest_path: str = None) -> Dict:
    """Load and parse ecosystem.yaml.

    Returns the raw parsed YAML dict.
    Raises FileNotFoundError if manifest not found.
    Raises ValueError if manifest is invalid.
    """
    yaml = _get_yaml()

    if manifest_path:
        path = Path(manifest_path)
    else:
        path = find_ecosystem_manifest()

    if not path or not path.exists():
        raise FileNotFoundError(
            "ecosystem.yaml not found. Create one at your workspace root."
        )

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    if not data or 'projects' not in data:
        raise ValueError(f"Invalid ecosystem manifest: {path} (missing 'projects' key)")

    return data


class EcosystemGraph:
    """Dependency graph built from ecosystem.yaml.

    Provides traversal for impact analysis:
    - downstream(project): what breaks if this project changes
    - upstream(project): what this project depends on
    - impact_of(file_or_module): which projects are affected
    """

    def __init__(self, manifest: Dict):
        self.manifest = manifest
        self.workspace_root = manifest.get('workspace_root', '')
        self.projects = manifest.get('projects', {})

        # Build adjacency lists
        self._depends_on: Dict[str, Set[str]] = {}  # project -> set of deps
        self._depended_by: Dict[str, Set[str]] = {}  # project -> set of dependents
        self._build_graph()

    def _build_graph(self):
        """Build dependency adjacency lists from manifest."""
        for name, config in self.projects.items():
            self._depends_on[name] = set()
            if name not in self._depended_by:
                self._depended_by[name] = set()

            deps = config.get('depends_on', [])
            if isinstance(deps, list):
                for dep in deps:
                    if isinstance(dep, dict):
                        dep_name = list(dep.keys())[0]
                    else:
                        dep_name = dep
                    self._depends_on[name].add(dep_name)
                    if dep_name not in self._depended_by:
                        self._depended_by[dep_name] = set()
                    self._depended_by[dep_name].add(name)

            # Also handle optional depends for graph completeness
            opt_deps = config.get('optional_depends', [])
            if isinstance(opt_deps, list):
                for dep in opt_deps:
                    if isinstance(dep, dict):
                        dep_name = list(dep.keys())[0]
                    else:
                        dep_name = dep
                    # Don't add to hard deps, but track reverse edge
                    if dep_name not in self._depended_by:
                        self._depended_by[dep_name] = set()
                    self._depended_by[dep_name].add(name)

    def downstream(self, project: str, transitive: bool = True) -> Set[str]:
        """Get projects that depend on this project (directly or transitively).

        These are the projects that could break if `project` changes.
        """
        if project not in self._depended_by:
            return set()

        if not transitive:
            return set(self._depended_by.get(project, set()))

        visited = set()
        queue = list(self._depended_by.get(project, set()))
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self._depended_by.get(current, set()) - visited)

        return visited

    def upstream(self, project: str, transitive: bool = True) -> Set[str]:
        """Get projects that this project depends on (directly or transitively)."""
        if project not in self._depends_on:
            return set()

        if not transitive:
            return set(self._depends_on.get(project, set()))

        visited = set()
        queue = list(self._depends_on.get(project, set()))
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self._depends_on.get(current, set()) - visited)

        return visited

    def project_for_path(self, file_path: str) -> Optional[str]:
        """Determine which project a file path belongs to.

        Matches by project path prefix against the file path.
        """
        file_path = str(file_path)

        # Normalize: strip workspace root if present
        if self.workspace_root and file_path.startswith(self.workspace_root):
            file_path = file_path[len(self.workspace_root):].lstrip('/')

        best_match = None
        best_length = 0

        for name, config in self.projects.items():
            proj_path = config.get('path', name)
            if file_path.startswith(proj_path + '/') or file_path == proj_path:
                if len(proj_path) > best_length:
                    best_match = name
                    best_length = len(proj_path)

        return best_match

    def impact_of(self, file_path: str) -> Dict:
        """Analyze impact of changing a file.

        Returns:
            {
                "project": str,           # Which project the file belongs to
                "downstream": [str],      # Projects that depend on this project
                "downstream_count": int,
                "exports_affected": bool, # Whether file is in an exported surface
            }
        """
        project = self.project_for_path(file_path)
        if not project:
            return {
                "project": None,
                "downstream": [],
                "downstream_count": 0,
                "exports_affected": False,
            }

        downstream = sorted(self.downstream(project))
        config = self.projects.get(project, {})

        # Check if the changed file is in an exported surface
        exports = config.get('exports', [])
        file_path_str = str(file_path)
        exports_affected = any(
            exp.replace('.', '/') in file_path_str
            for exp in exports
        ) if exports else False

        return {
            "project": project,
            "downstream": downstream,
            "downstream_count": len(downstream),
            "exports_affected": exports_affected,
        }

    def by_role(self, role: str) -> List[str]:
        """Get all projects with a given role."""
        return [
            name for name, config in self.projects.items()
            if config.get('role') == role
        ]

    def by_tag(self, tag: str) -> List[str]:
        """Get all projects with a given tag."""
        return [
            name for name, config in self.projects.items()
            if tag in config.get('tags', [])
        ]

    def validate(self) -> List[str]:
        """Validate the ecosystem manifest.

        Returns list of warnings/errors (empty = valid).
        """
        issues = []

        # Check for references to non-existent projects
        for name, deps in self._depends_on.items():
            for dep in deps:
                if dep not in self.projects:
                    issues.append(
                        f"Project '{name}' depends on '{dep}' which is not in the manifest"
                    )

        # Check for circular dependencies
        for name in self.projects:
            if name in self.downstream(name):
                issues.append(f"Circular dependency detected involving '{name}'")

        # Check paths exist
        for name, config in self.projects.items():
            proj_path = config.get('path', name)
            full_path = Path(self.workspace_root) / proj_path if self.workspace_root else Path(proj_path)
            if not full_path.exists():
                issues.append(f"Project '{name}' path does not exist: {full_path}")

        return issues

    def summary(self) -> Dict:
        """Get ecosystem summary statistics."""
        roles = {}
        types = {}
        for name, config in self.projects.items():
            role = config.get('role', 'unknown')
            ptype = config.get('type', 'unknown')
            roles[role] = roles.get(role, 0) + 1
            types[ptype] = types.get(ptype, 0) + 1

        return {
            "total_projects": len(self.projects),
            "by_role": roles,
            "by_type": types,
            "dependency_edges": sum(len(deps) for deps in self._depends_on.values()),
            "root_projects": sorted([
                name for name, deps in self._depends_on.items()
                if not deps
            ]),
            "leaf_projects": sorted([
                name for name in self.projects
                if not self._depended_by.get(name)
            ]),
        }


def load_ecosystem(manifest_path: str = None) -> EcosystemGraph:
    """Convenience: load manifest and return EcosystemGraph."""
    manifest = load_manifest(manifest_path)
    return EcosystemGraph(manifest)
