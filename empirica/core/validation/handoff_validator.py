"""
Handoff Validator - Verify Previous AI's Work

Next AI validates incoming checkpoint BEFORE trusting it.

Validates:
1. Claimed work matches git diff reality
2. Findings are credible
3. Unknowns make sense
4. No obvious inconsistencies

Phase 3 Component: Ensures multi-AI coordination coherence
"""

import logging
from typing import Dict, List, Optional

from .validation_utils import get_git_diff_summary

logger = logging.getLogger(__name__)


class HandoffValidator:
    """Validates incoming checkpoint quality and coherence"""

    def __init__(self, session_id: str, ai_id: str = "unknown"):
        """
        Initialize validator.

        Args:
            session_id: Session ID
            ai_id: My (next AI's) identifier
        """
        self.session_id = session_id
        self.ai_id = ai_id

    def validate_handoff(
        self,
        checkpoint_data: Dict[str, any],
        previous_ai_id: str = "unknown"
    ) -> Dict[str, any]:
        """
        Before I trust previous AI's work, verify it makes sense.

        Args:
            checkpoint_data: Previous AI's checkpoint
            previous_ai_id: Who handed off to me

        Returns:
            Validation result:
            {
                "valid": bool,
                "trustworthy": bool,
                "checks": {
                    "claim_vs_reality": bool,
                    "findings_credible": bool,
                    "unknowns_reasonable": bool,
                    "coherence": bool
                },
                "issues": [str],
                "recommendations": [str],
                "message": str,
                "should_investigate": bool
            }
        """
        issues = []
        recommendations = []
        checks = {}

        # 1. CLAIM VS REALITY: Did they do what they said?
        claim_result = self._check_claim_vs_reality(checkpoint_data)
        checks["claim_vs_reality"] = claim_result["valid"]
        if not claim_result["valid"]:
            issues.append(f"Claim mismatch: {claim_result['reason']}")
            recommendations.append(claim_result.get("recommendation", "investigate"))

        # 2. FINDINGS CREDIBILITY: Do findings make sense?
        findings = checkpoint_data.get("epistemic_tags", {}).get("findings", [])
        findings_result = self._check_findings_credibility(findings, checkpoint_data)
        checks["findings_credible"] = findings_result["credible"]
        if not findings_result["credible"]:
            issues.append(f"Findings concern: {findings_result['reason']}")

        # 3. UNKNOWNS REASONABLENESS: Are remaining unknowns realistic?
        unknowns = checkpoint_data.get("epistemic_tags", {}).get("unknowns", [])
        unknowns_result = self._check_unknowns_reasonableness(unknowns, findings)
        checks["unknowns_reasonable"] = unknowns_result["reasonable"]
        if not unknowns_result["reasonable"]:
            issues.append(f"Unknowns issue: {unknowns_result['reason']}")

        # 4. OVERALL COHERENCE: Does checkpoint hang together?
        coherence_result = self._check_overall_coherence(
            checkpoint_data, findings, unknowns
        )
        checks["coherence"] = coherence_result["coherent"]
        if not coherence_result["coherent"]:
            issues.append(f"Incoherence: {coherence_result['reason']}")

        # Determine trustworthiness
        trustworthy = not any(issue for issue in issues)
        valid = trustworthy  # For this phase, same as trustworthy

        should_investigate = not valid or len(issues) > 0

        return {
            "valid": valid,
            "trustworthy": trustworthy,
            "checks": checks,
            "issues": issues,
            "recommendations": recommendations,
            "should_investigate": should_investigate,
            "previous_ai": previous_ai_id,
            "message": self._format_validation_message(
                valid, trustworthy, issues, recommendations
            ),
            "session_id": self.session_id,
            "ai_id": self.ai_id
        }

    def _check_claim_vs_reality(self, checkpoint_data: Dict[str, any]) -> Dict[str, any]:
        """
        Did they do what they claimed?

        Args:
            checkpoint_data: Their checkpoint

        Returns:
            {
                "valid": bool,
                "reason": str,
                "recommendation": str
            }
        """
        claimed_work = checkpoint_data.get("meta", {}).get("description", "")

        if not claimed_work:
            # No claim to validate
            return {"valid": True, "reason": "no_claim"}

        # Get actual git changes
        actual_diff = get_git_diff_summary()

        if actual_diff.get("error"):
            # Can't validate
            return {
                "valid": False,
                "reason": f"Cannot access git state: {actual_diff['error']}",
                "recommendation": "investigate_git_state"
            }

        # Simple validation: if they claimed work, there should be changes
        if actual_diff.get("file_count", 0) == 0 and "no changes" not in claimed_work.lower():
            return {
                "valid": False,
                "reason": f"Claimed work '{claimed_work}' but no git changes found",
                "recommendation": "investigate_why_no_changes"
            }

        # Reverse: if there are lots of changes, they should have claimed work
        if actual_diff.get("file_count", 0) > 10 and len(claimed_work) < 10:
            return {
                "valid": False,
                "reason": f"Major git changes ({actual_diff['file_count']} files) but minimal claim",
                "recommendation": "understand_scope_of_work"
            }

        return {"valid": True, "reason": "claim_matches_reality"}

    def _check_findings_credibility(
        self,
        findings: List[Dict],
        checkpoint_data: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Are findings credible given their assessment?

        Args:
            findings: Their findings tags
            checkpoint_data: Full checkpoint

        Returns:
            {
                "credible": bool,
                "reason": str
            }
        """
        if not findings:
            return {"credible": True, "reason": "no_findings"}

        vectors = checkpoint_data.get("vectors", {})
        their_know = vectors.get("know", 0.5)
        their_clarity = vectors.get("clarity", 0.5)

        # Check 1: High certainty findings with low knowledge?
        high_certainty_findings = [
            f for f in findings if f.get("certainty", 0.5) > 0.8
        ]

        if high_certainty_findings and their_know < 0.4:
            return {
                "credible": False,
                "reason": f"High certainty findings ({len(high_certainty_findings)}) with low knowledge ({their_know})"
            }

        # Check 2: Many findings with low clarity?
        if len(findings) > 5 and their_clarity < 0.5:
            return {
                "credible": False,
                "reason": f"Many findings ({len(findings)}) with unclear requirements ({their_clarity})"
            }

        # Check 3: All findings at same confidence level (suspicious uniformity)
        confidences = [f.get("certainty", 0.5) for f in findings]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)

        if len(findings) > 3 and variance < 0.01:  # Very uniform = suspicious
            return {
                "credible": False,
                "reason": f"Findings have suspicious uniformity (all ~{avg_confidence:.2f} confidence)"
            }

        return {"credible": True, "reason": "findings_appear_reasonable"}

    def _check_unknowns_reasonableness(
        self,
        unknowns: List[Dict],
        findings: List[Dict]
    ) -> Dict[str, any]:
        """
        Do the remaining unknowns make sense?

        Args:
            unknowns: Their remaining unknowns
            findings: Their findings

        Returns:
            {
                "reasonable": bool,
                "reason": str
            }
        """
        if not unknowns:
            # No unknowns listed
            if not findings:
                # No findings AND no unknowns = suspicious (shouldn't happen)
                return {
                    "reasonable": False,
                    "reason": "No findings AND no unknowns - no work seems to have happened"
                }
            # Otherwise okay
            return {"reasonable": True, "reason": "all_unknowns_resolved"}

        # Check 1: Too many unknowns despite having findings?
        if len(unknowns) > len(findings) * 2:
            return {
                "reasonable": False,
                "reason": f"Many unknowns ({len(unknowns)}) vs findings ({len(findings)}) - progress unclear"
            }

        # Check 2: Unknowns should be actionable (not too many unresolved)
        # Note: Unknowns don't have impact scores - they're open questions, not findings
        unresolved_unknowns = [
            u for u in unknowns if not u.get("is_resolved", False)
        ]

        if len(unresolved_unknowns) > len(unknowns) * 0.8:
            return {
                "reasonable": False,
                "reason": f"Many unresolved unknowns ({len(unresolved_unknowns)}) - progress unclear"
            }

        return {"reasonable": True, "reason": "unknowns_appear_reasonable"}

    def _check_overall_coherence(
        self,
        checkpoint_data: Dict[str, any],
        findings: List[Dict],
        unknowns: List[Dict]
    ) -> Dict[str, any]:
        """
        Does the overall checkpoint hang together coherently?

        Args:
            checkpoint_data: Full checkpoint
            findings: Their findings
            unknowns: Their unknowns

        Returns:
            {
                "coherent": bool,
                "reason": str
            }
        """
        vectors = checkpoint_data.get("vectors", {})
        phase = checkpoint_data.get("phase", "unknown")

        # Check: POSTFLIGHT with low completion?
        if phase == "POSTFLIGHT":
            completion = vectors.get("completion", 0.0)
            if completion < 0.3 and not unknowns:
                return {
                    "coherent": False,
                    "reason": "POSTFLIGHT with low completion but claims no unknowns"
                }

        # Check: High uncertainty but confident findings?
        uncertainty = vectors.get("uncertainty", 0.5)
        if uncertainty > 0.7:
            high_conf_findings = sum(
                1 for f in findings if f.get("certainty", 0.5) > 0.7
            )
            if high_conf_findings > len(findings) * 0.5:
                return {
                    "coherent": False,
                    "reason": f"High uncertainty ({uncertainty}) but confident findings ({high_conf_findings})"
                }

        return {"coherent": True, "reason": "checkpoint_coherent"}

    def _format_validation_message(
        self,
        valid: bool,
        trustworthy: bool,
        issues: List[str],
        recommendations: List[str]
    ) -> str:
        """Format human-readable validation message"""
        if valid and trustworthy:
            return "✅ Handoff checkpoint validated. Previous work appears sound."

        msg = "⚠️ Handoff checkpoint has issues:\n"
        for issue in issues:
            msg += f"   - {issue}\n"

        if recommendations:
            msg += "\n   Recommendations:\n"
            for rec in recommendations:
                msg += f"   - {rec}\n"

        return msg
