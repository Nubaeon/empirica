"""
Prose Evidence Collector

Non-code grounded calibration evidence for research, strategy, and outreach
workflows. The prose equivalent of ruff/radon/pyright for users who don't code.

Evidence sources:
- textstat: readability indices (Flesch-Kincaid, Gunning Fog, SMOG) -> clarity, density
- proselint: prose lint violations (jargon, hedging, cliches) -> coherence, signal
- vale: configurable style guide checking -> clarity, coherence (optional)
- Document metrics: word count, source count, artifact density -> do, change, state
- Action verification: MCP action success tracking -> do, completion, impact

Activated via evidence_profile: "prose" in project.yaml or --evidence-profile flag.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .collector import EvidenceItem, EvidenceQuality

logger = logging.getLogger(__name__)


class ProseEvidenceCollector:
    """Collects deterministic evidence from prose and research artifacts."""

    def __init__(self, session_id: str, project_id: Optional[str] = None,
                 db=None, phase: str = "combined",
                 check_timestamp: Optional[float] = None):
        self.session_id = session_id
        self.project_id = project_id
        self.phase = phase
        self.check_timestamp = check_timestamp
        self._db = db
        self._owns_db = False

    def _get_db(self):
        if self._db is None:
            from empirica.data.session_database import SessionDatabase
            self._db = SessionDatabase()
            self._owns_db = True
        return self._db

    def _close_db(self):
        if self._owns_db and self._db is not None:
            self._db.close()
            self._db = None
            self._owns_db = False

    def collect_all(self) -> List[EvidenceItem]:
        """Collect prose-specific evidence from all available sources."""
        items = []

        collectors = [
            ("prose_quality", self._collect_prose_quality),
            ("document_metrics", self._collect_document_metrics),
            ("source_quality", self._collect_source_quality),
            ("action_verification", self._collect_action_verification),
        ]

        for source_name, collector_fn in collectors:
            try:
                result = collector_fn()
                if result:
                    items.extend(result)
            except Exception as e:
                logger.debug(f"Prose evidence source {source_name} failed: {e}")

        self._close_db()
        return items

    # --- Prose Quality (replaces ruff/radon/pyright) ---

    def _collect_prose_quality(self) -> List[EvidenceItem]:
        """Analyze prose quality of session artifacts using textstat and proselint.

        Runs on:
        - Finding texts logged this session
        - Handoff reports
        - Goal descriptions and completion reasons
        """
        items = []
        texts = self._get_session_texts()
        if not texts:
            return items

        combined_text = "\n\n".join(texts)
        if len(combined_text.split()) < 50:
            return items  # Too short for meaningful analysis

        # --- textstat: readability -> clarity, density ---
        items.extend(self._run_textstat(combined_text, len(texts)))

        # --- proselint: prose lint -> coherence, signal ---
        items.extend(self._run_proselint(combined_text))

        # --- vale: style guide checking -> clarity, coherence ---
        items.extend(self._run_vale(texts))

        return items

    def _run_textstat(self, text: str, text_count: int) -> List[EvidenceItem]:
        """Run textstat readability analysis."""
        items = []
        try:
            import textstat

            fk_grade = textstat.flesch_kincaid_grade(text)
            fog_index = textstat.gunning_fog(text)
            fre_score = textstat.flesch_reading_ease(text)
            word_count = textstat.lexicon_count(text, removepunct=True)
            sentence_count = textstat.sentence_count(text)

            # Flesch Reading Ease: 60-70 = standard, 30-50 = college, <30 = academic
            # For professional/research writing, 30-60 is good.
            # Normalize: 30-70 = 1.0 (sweet spot), <20 or >80 = lower
            if 30 <= fre_score <= 70:
                clarity_score = 1.0
            elif fre_score < 30:
                clarity_score = max(0.3, fre_score / 30.0)
            else:
                clarity_score = max(0.3, 1.0 - (fre_score - 70) / 30.0)

            items.append(EvidenceItem(
                source="prose_quality",
                metric_name="textstat_readability",
                value=clarity_score,
                raw_value={
                    "flesch_reading_ease": round(fre_score, 1),
                    "flesch_kincaid_grade": round(fk_grade, 1),
                    "gunning_fog": round(fog_index, 1),
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "texts_analyzed": text_count,
                },
                quality=EvidenceQuality.OBJECTIVE,
                supports_vectors=["clarity", "density"],
            ))

            # Information density: words per sentence and grade level
            # Very long sentences = low density. Very short = possibly shallow.
            avg_sentence_len = word_count / max(sentence_count, 1)
            # Sweet spot: 15-25 words per sentence
            if 15 <= avg_sentence_len <= 25:
                density_score = 1.0
            elif avg_sentence_len < 15:
                density_score = max(0.4, avg_sentence_len / 15.0)
            else:
                density_score = max(0.3, 1.0 - (avg_sentence_len - 25) / 25.0)

            items.append(EvidenceItem(
                source="prose_quality",
                metric_name="textstat_density",
                value=density_score,
                raw_value={
                    "avg_sentence_length": round(avg_sentence_len, 1),
                    "fk_grade": round(fk_grade, 1),
                },
                quality=EvidenceQuality.OBJECTIVE,
                supports_vectors=["density"],
            ))

        except ImportError:
            logger.debug("textstat not installed, skipping readability analysis")
        except Exception as e:
            logger.debug(f"textstat analysis failed: {e}")

        return items

    def _run_proselint(self, text: str) -> List[EvidenceItem]:
        """Run proselint prose linting."""
        items = []
        try:
            import tempfile
            from proselint.tools import LintFile

            # proselint >= 0.14 uses LintFile API
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.md', delete=False
            ) as f:
                f.write(text)
                tmp_path = f.name

            lf = LintFile(source=tmp_path, content=text)
            suggestions = lf.lint()
            Path(tmp_path).unlink(missing_ok=True)

            violation_count = len(suggestions)
            word_count = len(text.split())

            if word_count > 0:
                # Violations per 100 words — lower is better
                violations_per_100 = (violation_count / word_count) * 100
                # Normalize: 0 violations = 1.0, 5+ per 100 words = 0.0
                coherence_score = max(0.0, 1.0 - (violations_per_100 / 5.0))

                items.append(EvidenceItem(
                    source="prose_quality",
                    metric_name="proselint_violations",
                    value=coherence_score,
                    raw_value={
                        "violations": violation_count,
                        "words": word_count,
                        "per_100_words": round(violations_per_100, 2),
                    },
                    quality=EvidenceQuality.OBJECTIVE,
                    supports_vectors=["coherence", "signal"],
                ))

        except ImportError:
            logger.debug("proselint not installed, skipping prose lint")
        except Exception as e:
            logger.debug(f"proselint analysis failed: {e}")

        return items

    def _run_vale(self, texts: List[str]) -> List[EvidenceItem]:
        """Run vale style guide checking on prose artifacts.

        Requires vale binary and a .vale.ini config. Skipped if not available.
        """
        items = []
        import subprocess
        import tempfile

        try:
            # Check vale is available
            subprocess.run(["vale", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return items

        try:
            # Write combined text to temp file for vale
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.md', delete=False
            ) as f:
                f.write("\n\n".join(texts))
                tmp_path = f.name

            result = subprocess.run(
                ["vale", "--output", "JSON", tmp_path],
                capture_output=True, text=True, timeout=30,
            )

            Path(tmp_path).unlink(missing_ok=True)

            if result.stdout.strip():
                vale_data = json.loads(result.stdout)
                total_issues = 0
                by_severity: Dict[str, int] = {"error": 0, "warning": 0, "suggestion": 0}
                for _file, issues in vale_data.items():
                    total_issues += len(issues)
                    for issue in issues:
                        sev = issue.get("Severity", "suggestion").lower()
                        by_severity[sev] = by_severity.get(sev, 0) + 1

                word_count = sum(len(t.split()) for t in texts)
                if word_count > 0:
                    issues_per_100 = (total_issues / word_count) * 100
                    style_score = max(0.0, 1.0 - (issues_per_100 / 8.0))

                    items.append(EvidenceItem(
                        source="prose_quality",
                        metric_name="vale_style_score",
                        value=style_score,
                        raw_value={
                            "total_issues": total_issues,
                            "by_severity": by_severity,
                            "words": word_count,
                            "per_100_words": round(issues_per_100, 2),
                        },
                        quality=EvidenceQuality.OBJECTIVE,
                        supports_vectors=["clarity", "coherence"],
                    ))

        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
            logger.debug(f"vale analysis failed: {e}")

        return items

    # --- Document Metrics (replaces git metrics) ---

    def _collect_document_metrics(self) -> List[EvidenceItem]:
        """Measure document output volume and growth.

        For non-code users, "lines changed" equivalent is:
        - Total words written in findings, goals, handoffs
        - Artifact production rate
        """
        items = []
        db = self._get_db()
        cursor = db.conn.cursor()

        # Word count of all findings logged this session
        cursor.execute("""
            SELECT finding FROM project_findings WHERE session_id = ?
        """, (self.session_id,))
        findings = cursor.fetchall()

        total_words = sum(len(row[0].split()) for row in findings if row[0])
        finding_count = len(findings)

        if finding_count > 0:
            # Production rate: findings logged (like commits made)
            # Normalize: 1-2 = 0.3, 5 = 0.7, 10+ = 1.0
            production_score = min(1.0, finding_count / 10.0)
            items.append(EvidenceItem(
                source="document_metrics",
                metric_name="finding_production",
                value=production_score,
                raw_value={
                    "findings_logged": finding_count,
                    "total_words": total_words,
                    "avg_words_per_finding": round(total_words / finding_count, 1),
                },
                quality=EvidenceQuality.SEMI_OBJECTIVE,
                supports_vectors=["do", "change"],
            ))

            # Detail depth: average words per finding (like lines per commit)
            avg_words = total_words / finding_count
            # Sweet spot: 20-80 words per finding
            if 20 <= avg_words <= 80:
                depth_score = 1.0
            elif avg_words < 20:
                depth_score = max(0.3, avg_words / 20.0)
            else:
                depth_score = max(0.5, 1.0 - (avg_words - 80) / 120.0)

            items.append(EvidenceItem(
                source="document_metrics",
                metric_name="finding_depth",
                value=depth_score,
                raw_value={"avg_words": round(avg_words, 1)},
                quality=EvidenceQuality.SEMI_OBJECTIVE,
                supports_vectors=["state", "density"],
            ))

        # Goal completion as document output
        cursor.execute("""
            SELECT id, objective FROM goals
            WHERE session_id = ? AND completed = 1
        """, (self.session_id,))
        completed_goals = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) FROM goals WHERE session_id = ?
        """, (self.session_id,))
        total_goals = cursor.fetchone()[0]

        if total_goals > 0:
            completion_ratio = len(completed_goals) / total_goals
            items.append(EvidenceItem(
                source="document_metrics",
                metric_name="goal_completion_ratio",
                value=completion_ratio,
                raw_value={
                    "completed": len(completed_goals),
                    "total": total_goals,
                },
                quality=EvidenceQuality.SEMI_OBJECTIVE,
                supports_vectors=["completion", "do"],
            ))

        return items

    # --- Source Quality (replaces pytest/test coverage) ---

    def _collect_source_quality(self) -> List[EvidenceItem]:
        """Measure quality and breadth of research sources.

        For non-code users, "test coverage" equivalent is:
        - Sources cited per finding (like assertions per test)
        - Source diversity (like test file coverage)
        """
        items = []
        db = self._get_db()
        cursor = db.conn.cursor()

        # Sources logged this session
        cursor.execute("""
            SELECT COUNT(*) FROM epistemic_sources WHERE session_id = ?
        """, (self.session_id,))
        source_count = cursor.fetchone()[0]

        # Findings this session
        cursor.execute("""
            SELECT COUNT(*) FROM project_findings WHERE session_id = ?
        """, (self.session_id,))
        finding_count = cursor.fetchone()[0]

        if finding_count > 0 and source_count > 0:
            # Source-to-finding ratio (like test-to-code ratio)
            ratio = source_count / finding_count
            # Normalize: 0.5+ sources per finding = well-sourced
            source_score = min(1.0, ratio / 0.5)
            items.append(EvidenceItem(
                source="source_quality",
                metric_name="source_to_finding_ratio",
                value=source_score,
                raw_value={
                    "sources": source_count,
                    "findings": finding_count,
                    "ratio": round(ratio, 2),
                },
                quality=EvidenceQuality.SEMI_OBJECTIVE,
                supports_vectors=["know", "signal"],
            ))
        elif finding_count > 0 and source_count == 0:
            # Findings without sources — low evidence quality
            items.append(EvidenceItem(
                source="source_quality",
                metric_name="source_to_finding_ratio",
                value=0.2,
                raw_value={"sources": 0, "findings": finding_count, "ratio": 0},
                quality=EvidenceQuality.SEMI_OBJECTIVE,
                supports_vectors=["know", "signal"],
            ))

        return items

    # --- Action Verification (replaces integration tests) ---

    def _collect_action_verification(self) -> List[EvidenceItem]:
        """Verify that research led to concrete actions.

        For non-code users, "tests passing" equivalent is:
        - Goals marked complete with reasons
        - Unknowns resolved during session
        - Assumptions logged and addressed
        """
        items = []
        db = self._get_db()
        cursor = db.conn.cursor()

        # Unknowns resolved this session
        cursor.execute("""
            SELECT COUNT(*) FROM project_unknowns
            WHERE session_id = ? AND resolved = 1
        """, (self.session_id,))
        resolved = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM project_unknowns
            WHERE session_id = ?
        """, (self.session_id,))
        total_unknowns = cursor.fetchone()[0]

        if total_unknowns > 0:
            resolution_rate = resolved / total_unknowns
            items.append(EvidenceItem(
                source="action_verification",
                metric_name="unknown_resolution_rate",
                value=resolution_rate,
                raw_value={"resolved": resolved, "total": total_unknowns},
                quality=EvidenceQuality.SEMI_OBJECTIVE,
                supports_vectors=["do", "completion", "impact"],
            ))

        # Assumptions logged (epistemic honesty metric)
        cursor.execute("""
            SELECT COUNT(*) FROM assumptions WHERE session_id = ?
        """, (self.session_id,))
        assumption_count = cursor.fetchone()[0]

        if assumption_count > 0:
            # Logging assumptions = epistemic honesty, similar to writing tests
            honesty_score = min(1.0, assumption_count / 3.0)
            items.append(EvidenceItem(
                source="action_verification",
                metric_name="assumption_logging",
                value=honesty_score,
                raw_value={"assumptions_logged": assumption_count},
                quality=EvidenceQuality.SEMI_OBJECTIVE,
                supports_vectors=["uncertainty", "know"],
            ))

        # Decisions logged (choice points documented)
        cursor.execute("""
            SELECT COUNT(*) FROM decisions WHERE session_id = ?
        """, (self.session_id,))
        decision_count = cursor.fetchone()[0]

        if decision_count > 0:
            decision_score = min(1.0, decision_count / 3.0)
            items.append(EvidenceItem(
                source="action_verification",
                metric_name="decision_documentation",
                value=decision_score,
                raw_value={"decisions_logged": decision_count},
                quality=EvidenceQuality.SEMI_OBJECTIVE,
                supports_vectors=["context", "signal"],
            ))

        return items

    # --- Text Extraction Helpers ---

    def _get_session_texts(self) -> List[str]:
        """Get prose texts written during this session for quality analysis."""
        texts = []
        db = self._get_db()
        cursor = db.conn.cursor()

        # Findings text
        cursor.execute("""
            SELECT finding FROM project_findings WHERE session_id = ?
        """, (self.session_id,))
        texts.extend(row[0] for row in cursor.fetchall() if row[0])

        # Goal objectives and completion reasons
        cursor.execute("""
            SELECT objective FROM goals WHERE session_id = ?
        """, (self.session_id,))
        texts.extend(row[0] for row in cursor.fetchall() if row[0])

        # Handoff summaries
        cursor.execute("""
            SELECT task_summary FROM project_handoffs WHERE session_id = ?
        """, (self.session_id,))
        for row in cursor.fetchall():
            if row[0]:
                texts.append(row[0])

        return texts


