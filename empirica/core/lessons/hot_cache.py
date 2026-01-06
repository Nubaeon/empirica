"""
Empirica Lessons - Hot Cache (In-Memory Knowledge Graph)

This module provides nanosecond-level access to lesson relationships
and epistemic deltas. The graph is loaded from SQLite on startup and
updated live as lessons are created/modified.

Performance target: <100ns for relationship queries
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import time
import threading
from collections import defaultdict

from .schema import (
    EpistemicDelta,
    RelationType,
    KnowledgeGraphNode,
    KnowledgeGraphEdge
)


@dataclass
class HotLessonEntry:
    """Minimal lesson data for hot cache"""
    id: str
    name: str
    expected_delta: Dict[str, float]
    prereq_ids: Set[str]
    enables_ids: Set[str]
    requires_ids: Set[str]
    domain: Optional[str] = None


class LessonHotCache:
    """
    In-memory knowledge graph for fast lesson queries.

    This is the HOT layer - everything here is in RAM for
    nanosecond access. Relationships are stored as adjacency
    lists for O(1) traversal.

    Thread-safe with read-write lock pattern.
    """

    def __init__(self):
        # Lesson data indexed by ID
        self._lessons: Dict[str, HotLessonEntry] = {}

        # Adjacency lists for graph traversal
        self._requires: Dict[str, Set[str]] = defaultdict(set)  # lesson -> lessons it requires
        self._enables: Dict[str, Set[str]] = defaultdict(set)   # lesson -> lessons it enables
        self._required_by: Dict[str, Set[str]] = defaultdict(set)  # reverse of requires
        self._enabled_by: Dict[str, Set[str]] = defaultdict(set)   # reverse of enables

        # Index by epistemic improvement
        self._improves_know: List[Tuple[str, float]] = []
        self._improves_do: List[Tuple[str, float]] = []
        self._improves_context: List[Tuple[str, float]] = []
        self._reduces_uncertainty: List[Tuple[str, float]] = []

        # Index by domain
        self._by_domain: Dict[str, Set[str]] = defaultdict(set)

        # Thread safety
        self._lock = threading.RLock()

        # Stats
        self._load_timestamp: Optional[float] = None
        self._query_count: int = 0

    def load_lesson(self, lesson_hot_dict: Dict) -> None:
        """Load a single lesson into hot cache"""
        with self._lock:
            lesson_id = lesson_hot_dict['id']

            entry = HotLessonEntry(
                id=lesson_id,
                name=lesson_hot_dict['name'],
                expected_delta=lesson_hot_dict.get('expected_delta', {}),
                prereq_ids=set(lesson_hot_dict.get('prereq_ids', [])),
                enables_ids=set(lesson_hot_dict.get('enables', [])),
                requires_ids=set(lesson_hot_dict.get('requires', [])),
                domain=lesson_hot_dict.get('domain')
            )

            self._lessons[lesson_id] = entry

            # Build adjacency lists
            for req_id in entry.requires_ids:
                self._requires[lesson_id].add(req_id)
                self._required_by[req_id].add(lesson_id)

            for enables_id in entry.enables_ids:
                self._enables[lesson_id].add(enables_id)
                self._enabled_by[enables_id].add(lesson_id)

            # Build epistemic indexes
            delta = entry.expected_delta
            if delta.get('know', 0) > 0:
                self._improves_know.append((lesson_id, delta['know']))
            if delta.get('do', 0) > 0:
                self._improves_do.append((lesson_id, delta['do']))
            if delta.get('context', 0) > 0:
                self._improves_context.append((lesson_id, delta['context']))
            if delta.get('uncertainty', 0) < 0:  # Negative = reduces
                self._reduces_uncertainty.append((lesson_id, abs(delta['uncertainty'])))

            # Domain index
            if entry.domain:
                self._by_domain[entry.domain].add(lesson_id)

    def load_from_warm(self, warm_loader) -> int:
        """
        Load all lessons from warm storage (SQLite).
        Returns count of lessons loaded.
        """
        with self._lock:
            self._clear_indexes()
            count = 0
            for lesson_hot in warm_loader.get_all_hot_data():
                self.load_lesson(lesson_hot)
                count += 1
            self._sort_indexes()
            self._load_timestamp = time.time()
            return count

    def _clear_indexes(self) -> None:
        """Clear all indexes"""
        self._lessons.clear()
        self._requires.clear()
        self._enables.clear()
        self._required_by.clear()
        self._enabled_by.clear()
        self._improves_know.clear()
        self._improves_do.clear()
        self._improves_context.clear()
        self._reduces_uncertainty.clear()
        self._by_domain.clear()

    def _sort_indexes(self) -> None:
        """Sort epistemic indexes by impact (descending)"""
        self._improves_know.sort(key=lambda x: x[1], reverse=True)
        self._improves_do.sort(key=lambda x: x[1], reverse=True)
        self._improves_context.sort(key=lambda x: x[1], reverse=True)
        self._reduces_uncertainty.sort(key=lambda x: x[1], reverse=True)

    # ==================== FAST QUERIES ====================

    def get_lesson(self, lesson_id: str) -> Optional[HotLessonEntry]:
        """Get lesson by ID - O(1)"""
        self._query_count += 1
        return self._lessons.get(lesson_id)

    def lessons_that_improve(
        self,
        vector: str,
        threshold: float = 0.1,
        limit: int = 10
    ) -> List[str]:
        """
        Find lessons that improve a specific epistemic vector.
        Returns lesson IDs sorted by improvement magnitude.

        Performance: O(n) where n = number of lessons with positive delta
        """
        self._query_count += 1
        index_map = {
            'know': self._improves_know,
            'do': self._improves_do,
            'context': self._improves_context,
            'uncertainty': self._reduces_uncertainty
        }

        if vector not in index_map:
            return []

        return [
            lid for lid, delta in index_map[vector][:limit]
            if delta >= threshold
        ]

    def get_prerequisites(self, lesson_id: str) -> Set[str]:
        """Get all prerequisites for a lesson - O(1)"""
        self._query_count += 1
        return self._requires.get(lesson_id, set())

    def get_all_prerequisites(self, lesson_id: str) -> Set[str]:
        """
        Get all prerequisites recursively (transitive closure).
        Returns all lessons that must be completed before this one.

        Performance: O(V + E) where V = nodes, E = edges
        """
        self._query_count += 1
        result = set()
        stack = [lesson_id]
        visited = set()

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            prereqs = self._requires.get(current, set())
            result.update(prereqs)
            stack.extend(prereqs)

        return result

    def get_enabled_lessons(self, lesson_id: str) -> Set[str]:
        """Get lessons that this lesson enables - O(1)"""
        self._query_count += 1
        return self._enables.get(lesson_id, set())

    def get_learning_path(
        self,
        target_lesson_id: str,
        completed_lessons: Set[str]
    ) -> List[str]:
        """
        Compute optimal learning path to reach target lesson.
        Returns ordered list of lesson IDs to complete.

        Performance: Topological sort, O(V + E)
        """
        self._query_count += 1

        # Get all required lessons
        all_prereqs = self.get_all_prerequisites(target_lesson_id)
        all_prereqs.add(target_lesson_id)

        # Remove already completed
        remaining = all_prereqs - completed_lessons

        # Topological sort
        path = []
        visited = set()
        temp_visited = set()

        def visit(lesson_id: str):
            if lesson_id in visited:
                return
            if lesson_id in temp_visited:
                return  # Cycle detected, skip

            temp_visited.add(lesson_id)
            for prereq in self._requires.get(lesson_id, set()):
                if prereq in remaining:
                    visit(prereq)
            temp_visited.remove(lesson_id)
            visited.add(lesson_id)
            path.append(lesson_id)

        for lesson_id in remaining:
            visit(lesson_id)

        return path

    def can_execute(
        self,
        lesson_id: str,
        completed_lessons: Set[str],
        current_epistemic: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Check if a lesson can be executed given current state.
        Returns (can_execute, missing_prerequisites).
        """
        self._query_count += 1

        lesson = self._lessons.get(lesson_id)
        if not lesson:
            return False, [f"Lesson {lesson_id} not found"]

        missing = []

        # Check lesson prerequisites
        for prereq_id in lesson.prereq_ids:
            if prereq_id not in completed_lessons:
                prereq = self._lessons.get(prereq_id)
                name = prereq.name if prereq else prereq_id
                missing.append(f"Lesson: {name}")

        return len(missing) == 0, missing

    def find_by_domain(self, domain: str) -> Set[str]:
        """Find all lessons in a domain - O(1)"""
        self._query_count += 1
        return self._by_domain.get(domain, set())

    def find_best_for_gap(
        self,
        epistemic_state: Dict[str, float],
        threshold: float = 0.6
    ) -> List[Tuple[str, str, float]]:
        """
        Find lessons that address the biggest epistemic gaps.
        Returns [(lesson_id, vector, improvement), ...] sorted by impact.
        """
        self._query_count += 1

        results = []

        # Find gaps
        gaps = {
            'know': max(0, threshold - epistemic_state.get('know', 0)),
            'do': max(0, threshold - epistemic_state.get('do', 0)),
            'context': max(0, threshold - epistemic_state.get('context', 0)),
        }

        # High uncertainty is also a gap
        if epistemic_state.get('uncertainty', 0) > threshold:
            gaps['uncertainty'] = epistemic_state['uncertainty'] - threshold

        # Find lessons for each gap
        for vector, gap in gaps.items():
            if gap > 0:
                lessons = self.lessons_that_improve(vector, threshold=0.1, limit=5)
                for lid in lessons:
                    lesson = self._lessons.get(lid)
                    if lesson:
                        improvement = lesson.expected_delta.get(vector, 0)
                        if vector == 'uncertainty':
                            improvement = abs(improvement)  # Reduction is positive
                        results.append((lid, vector, improvement))

        # Sort by improvement descending
        results.sort(key=lambda x: x[2], reverse=True)
        return results

    # ==================== STATS ====================

    def stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'lesson_count': len(self._lessons),
            'edge_count': sum(len(v) for v in self._requires.values()),
            'domain_count': len(self._by_domain),
            'query_count': self._query_count,
            'load_timestamp': self._load_timestamp,
            'memory_estimate_kb': self._estimate_memory() / 1024
        }

    def _estimate_memory(self) -> int:
        """Rough memory estimate in bytes"""
        # Very rough: ~500 bytes per lesson entry
        return len(self._lessons) * 500


# Global singleton
_hot_cache: Optional[LessonHotCache] = None


def get_hot_cache() -> LessonHotCache:
    """Get or create the global hot cache singleton"""
    global _hot_cache
    if _hot_cache is None:
        _hot_cache = LessonHotCache()
    return _hot_cache


def initialize_hot_cache(warm_loader) -> int:
    """Initialize the hot cache from warm storage"""
    cache = get_hot_cache()
    return cache.load_from_warm(warm_loader)
