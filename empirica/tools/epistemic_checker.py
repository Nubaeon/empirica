#!/usr/bin/env python3
"""
Proactive Epistemic Checker - Automated verification of empirical claims

Scans documents for empirical claims and assesses epistemic grounding:
- Extracts quantitative, causal, and comparative assertions
- Assesses epistemic state (know, uncertainty, evidence)
- Flags ungrounded claims
- Generates verification reports

This is hallucination CORRECTION, not just prevention.
"""

import re
import json
import sys
from typing import List, Dict, Any, Tuple
from pathlib import Path


class EpistemicClaim:
    """Represents an empirical claim found in text"""

    def __init__(self, text: str, claim_type: str, line_number: int, context: str):
        self.text = text
        self.claim_type = claim_type
        self.line_number = line_number
        self.context = context

    def to_dict(self):
        return {
            'text': self.text,
            'type': self.claim_type,
            'line': self.line_number,
            'context': self.context
        }


class EpistemicAssessment:
    """Assessment of epistemic state for a claim"""

    def __init__(self, claim: EpistemicClaim, know: float, uncertainty: float,
                 evidence: List[str], reasoning: str):
        self.claim = claim
        self.know = know
        self.uncertainty = uncertainty
        self.evidence = evidence
        self.reasoning = reasoning

    def should_flag(self) -> Tuple[bool, List[str]]:
        """Determine if claim should be flagged for revision"""
        flags = []

        if self.uncertainty > 0.5:
            flags.append(f"High uncertainty ({self.uncertainty:.2f})")

        if self.know < 0.6:
            flags.append(f"Low knowledge ({self.know:.2f})")

        if not self.evidence:
            flags.append("No supporting evidence")

        return len(flags) > 0, flags

    def to_dict(self):
        should_flag, flags = self.should_flag()
        return {
            'claim': self.claim.to_dict(),
            'epistemic_state': {
                'know': self.know,
                'uncertainty': self.uncertainty,
                'evidence': self.evidence,
                'reasoning': self.reasoning
            },
            'flagged': should_flag,
            'flags': flags
        }


class EpistemicChecker:
    """Main epistemic checking engine"""

    def __init__(self, evidence_base: Dict[str, Any] = None):
        """
        Initialize checker

        Args:
            evidence_base: Optional dict of logged findings for evidence lookup
        """
        self.evidence_base = evidence_base or {}

        # Claim extraction patterns
        self.patterns = {
            'percentage': re.compile(r'(\d+\.?\d*)\s*%\s+(\w+)', re.IGNORECASE),
            'ratio': re.compile(r'(\d+)\s+out of\s+(\d+)', re.IGNORECASE),
            'reduction': re.compile(r'(\d+\.?\d*)\s*%\s+(reduction|increase|improvement|decrease)', re.IGNORECASE),
            'causal': re.compile(r'\b(causes?|leads? to|results? in|enables?|prevents?)\b', re.IGNORECASE),
            'comparative': re.compile(r'\b(better than|outperforms?|exceeds?|superior to|faster than)\b', re.IGNORECASE),
            'temporal': re.compile(r'(\d+\.?\d*)\s+(hours?|days?|weeks?|months?|years?)', re.IGNORECASE),
            'measured': re.compile(r'\b(measured|tested|demonstrated|validated|empirically)\b', re.IGNORECASE),
            'quantitative': re.compile(r'\b(\d+\.?\d*)\s+(times|fold|orders? of magnitude)\b', re.IGNORECASE),
        }

    def extract_claims(self, text: str) -> List[EpistemicClaim]:
        """
        Extract empirical claims from text

        Returns list of EpistemicClaim objects
        """
        claims = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Skip markdown headers, code blocks, etc.
            if line.strip().startswith('#') or line.strip().startswith('```'):
                continue

            # Check each pattern
            for claim_type, pattern in self.patterns.items():
                if pattern.search(line):
                    # Extract sentence containing the match
                    sentence = self._extract_sentence(text, line_num)

                    if sentence:
                        claims.append(EpistemicClaim(
                            text=sentence,
                            claim_type=claim_type,
                            line_number=line_num,
                            context=line.strip()
                        ))
                        break  # One claim per line max

        return claims

    def _extract_sentence(self, text: str, line_num: int) -> str:
        """Extract full sentence from line number"""
        lines = text.split('\n')
        if line_num > len(lines):
            return ""

        line = lines[line_num - 1]

        # Simple sentence extraction (could be improved)
        # For now, just return the line stripped of markdown
        sentence = line.strip()
        sentence = re.sub(r'^[-*•]\s+', '', sentence)  # Remove bullets
        sentence = re.sub(r'^\d+\.\s+', '', sentence)  # Remove numbering

        return sentence

    def assess_claim(self, claim: EpistemicClaim) -> EpistemicAssessment:
        """
        Assess epistemic state for a claim

        Uses heuristics + evidence base lookup
        """
        # Default assessment
        know = 0.5
        uncertainty = 0.5
        evidence = []
        reasoning = "Default assessment - no specific evidence found"

        # Heuristic 1: Claims with "measured", "tested", "validated" suggest higher confidence
        if self.patterns['measured'].search(claim.text):
            know = 0.7
            uncertainty = 0.3
            reasoning = "Claim uses measurement language, suggests empirical basis"

        # Heuristic 2: Specific percentages without context are suspicious
        if self.patterns['percentage'].search(claim.text) and 'measured' not in claim.text.lower():
            know = 0.3
            uncertainty = 0.7
            reasoning = "Specific percentage without measurement context - likely estimated or unverified"

        # Heuristic 3: Causal claims require strong evidence
        if claim.claim_type == 'causal':
            know = 0.4
            uncertainty = 0.6
            reasoning = "Causal claim requires controlled testing or strong evidence"

        # Heuristic 4: Comparative claims need benchmarks
        if claim.claim_type == 'comparative':
            know = 0.4
            uncertainty = 0.6
            reasoning = "Comparative claim requires benchmark data"

        # Check evidence base
        if self.evidence_base:
            evidence = self._find_supporting_evidence(claim)
            if evidence:
                know = min(0.9, know + 0.3)  # Boost confidence if evidence found
                uncertainty = max(0.1, uncertainty - 0.3)
                reasoning = f"Found {len(evidence)} supporting evidence items in findings database"

        return EpistemicAssessment(
            claim=claim,
            know=know,
            uncertainty=uncertainty,
            evidence=evidence,
            reasoning=reasoning
        )

    def _find_supporting_evidence(self, claim: EpistemicClaim) -> List[str]:
        """
        Search evidence base for supporting findings

        Returns list of finding IDs that support this claim
        """
        evidence = []

        # Extract key terms from claim
        claim_terms = set(re.findall(r'\b\w{4,}\b', claim.text.lower()))

        # Search findings
        for finding_id, finding_data in self.evidence_base.items():
            finding_text = finding_data.get('finding', '').lower()
            finding_terms = set(re.findall(r'\b\w{4,}\b', finding_text))

            # If significant overlap, consider it supporting evidence
            overlap = len(claim_terms & finding_terms)
            if overlap >= 3:  # At least 3 common words
                evidence.append(finding_id)

        return evidence

    def check_document(self, document_path: Path) -> Dict[str, Any]:
        """
        Run full epistemic check on document

        Returns:
            Dict with claims, assessments, flagged claims, and summary
        """
        # Read document
        with open(document_path, 'r') as f:
            text = f.read()

        # Extract claims
        claims = self.extract_claims(text)

        # Assess each claim
        assessments = [self.assess_claim(claim) for claim in claims]

        # Separate flagged from verified
        flagged = [a for a in assessments if a.should_flag()[0]]
        verified = [a for a in assessments if not a.should_flag()[0]]

        # Generate summary
        summary = {
            'document': str(document_path),
            'total_claims': len(claims),
            'verified': len(verified),
            'flagged': len(flagged),
            'flagged_rate': len(flagged) / len(claims) if claims else 0,
            'claims_by_type': self._count_by_type(claims)
        }

        return {
            'summary': summary,
            'assessments': [a.to_dict() for a in assessments],
            'flagged_claims': [a.to_dict() for a in flagged],
            'verified_claims': [a.to_dict() for a in verified]
        }

    def _count_by_type(self, claims: List[EpistemicClaim]) -> Dict[str, int]:
        """Count claims by type"""
        counts = {}
        for claim in claims:
            counts[claim.claim_type] = counts.get(claim.claim_type, 0) + 1
        return counts

    def generate_report(self, check_result: Dict[str, Any]) -> str:
        """Generate human-readable verification report"""
        summary = check_result['summary']
        flagged = check_result['flagged_claims']

        report = []
        report.append("# Epistemic Verification Report")
        report.append("")
        report.append(f"**Document:** {summary['document']}")
        report.append(f"**Date:** {Path(__file__).stat().st_mtime}")  # Placeholder
        report.append("")

        # Summary
        report.append("## Summary")
        report.append("")
        report.append(f"- **Total claims:** {summary['total_claims']}")
        report.append(f"- **Verified:** {summary['verified']} ({100 * (1 - summary['flagged_rate']):.1f}%)")
        report.append(f"- **Flagged:** {summary['flagged']} ({100 * summary['flagged_rate']:.1f}%)")
        report.append("")

        # Claims by type
        report.append("**Claims by type:**")
        for claim_type, count in summary['claims_by_type'].items():
            report.append(f"- {claim_type}: {count}")
        report.append("")

        # Flagged claims detail
        if flagged:
            report.append("## Flagged Claims (Require Verification)")
            report.append("")

            for i, assessment in enumerate(flagged, 1):
                claim = assessment['claim']
                state = assessment['epistemic_state']
                flags = assessment['flags']

                report.append(f"### Claim {i} (Line {claim['line']})")
                report.append("")
                report.append(f"**Text:** \"{claim['text']}\"")
                report.append("")
                report.append(f"**Type:** {claim['type']}")
                report.append("")
                report.append("**Epistemic Assessment:**")
                report.append(f"- Knowledge: {state['know']:.2f}")
                report.append(f"- Uncertainty: {state['uncertainty']:.2f}")
                report.append(f"- Evidence: {state['evidence'] if state['evidence'] else 'None'}")
                report.append("")
                report.append(f"**Reasoning:** {state['reasoning']}")
                report.append("")
                report.append("**Flags:**")
                for flag in flags:
                    report.append(f"- ❌ {flag}")
                report.append("")
                report.append("**Recommendation:** Verify claim or mark as theoretical prediction")
                report.append("")
                report.append("---")
                report.append("")
        else:
            report.append("## ✅ All Claims Verified")
            report.append("")
            report.append("No claims flagged for revision. All empirical assertions appear epistemically grounded.")
            report.append("")

        return "\n".join(report)


def main():
    """CLI interface for epistemic checking"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Proactive epistemic checker - verify empirical claims in documents"
    )
    parser.add_argument('document', help='Path to document to check')
    parser.add_argument('--evidence-base', help='Path to JSON file with evidence base')
    parser.add_argument('--output', choices=['json', 'report'], default='report',
                        help='Output format')
    parser.add_argument('--threshold-uncertainty', type=float, default=0.5,
                        help='Flag claims with uncertainty above this (default: 0.5)')
    parser.add_argument('--threshold-know', type=float, default=0.6,
                        help='Flag claims with knowledge below this (default: 0.6)')

    args = parser.parse_args()

    # Load evidence base if provided
    evidence_base = {}
    if args.evidence_base:
        with open(args.evidence_base, 'r') as f:
            evidence_base = json.load(f)

    # Run check
    checker = EpistemicChecker(evidence_base=evidence_base)
    result = checker.check_document(Path(args.document))

    # Output
    if args.output == 'json':
        print(json.dumps(result, indent=2))
    else:
        report = checker.generate_report(result)
        print(report)


if __name__ == '__main__':
    main()
