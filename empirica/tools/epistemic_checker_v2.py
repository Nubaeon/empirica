#!/usr/bin/env python3
"""
Proactive Epistemic Checker v2 - Experiential Noetics

Uses actual investigation history and evidence trails from Empirica:
- Queries findings database for supporting evidence
- Assesses based on logged work, not pattern matching
- Honest epistemic self-assessment with evidence grounding
- Distinguishes: investigated vs training data vs unknown

This is metacognitive epistemics, not just fact-checking.
"""

import re
import json
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Import Empirica session database for evidence queries
try:
    from empirica.data.session_database import SessionDatabase
except ImportError:
    SessionDatabase = None
    print("Warning: Could not import SessionDatabase - evidence base disabled", file=sys.stderr)


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


class ExperientialEvidence:
    """Evidence from actual investigation (not just training data)"""

    def __init__(self, finding_id: str, finding_text: str, session_id: str,
                 impact: float, timestamp: str):
        self.finding_id = finding_id
        self.finding_text = finding_text
        self.session_id = session_id
        self.impact = impact
        self.timestamp = timestamp

    def to_dict(self):
        return {
            'finding_id': self.finding_id,
            'finding_text': self.finding_text,
            'session_id': self.session_id,
            'impact': self.impact,
            'timestamp': self.timestamp
        }


class EpistemicAssessment:
    """
    Metacognitive assessment of epistemic state for a claim

    Three levels of knowing:
    1. Experiential: "I investigated this and logged findings"
    2. Training data: "This matches my training patterns"
    3. Unknown: "I don't actually know this"
    """

    def __init__(self, claim: EpistemicClaim, know: float, uncertainty: float,
                 evidence: List[ExperientialEvidence], reasoning: str,
                 evidence_type: str):
        self.claim = claim
        self.know = know
        self.uncertainty = uncertainty
        self.evidence = evidence
        self.reasoning = reasoning
        self.evidence_type = evidence_type  # "experiential", "training", "none"

    def should_flag(self) -> Tuple[bool, List[str]]:
        """Determine if claim should be flagged for revision"""
        flags = []

        # High uncertainty = need investigation
        if self.uncertainty > 0.5:
            flags.append(f"High uncertainty ({self.uncertainty:.2f}) - needs investigation")

        # Low knowledge without experiential evidence = suspicious
        if self.know < 0.6 and self.evidence_type != "experiential":
            flags.append(f"Low knowledge ({self.know:.2f}) - not verified through investigation")

        # No evidence at all = must verify
        if not self.evidence and self.evidence_type == "none":
            flags.append("No supporting evidence - claim ungrounded")

        # Training data only = lower confidence required
        if self.evidence_type == "training" and self.know > 0.7:
            flags.append("Training data only - cannot claim high confidence without investigation")

        return len(flags) > 0, flags

    def to_dict(self):
        should_flag, flags = self.should_flag()
        return {
            'claim': self.claim.to_dict(),
            'epistemic_state': {
                'know': self.know,
                'uncertainty': self.uncertainty,
                'evidence': [e.to_dict() for e in self.evidence],
                'evidence_type': self.evidence_type,
                'reasoning': self.reasoning
            },
            'flagged': should_flag,
            'flags': flags
        }


class EpistemicCheckerV2:
    """
    Experiential noetics checker - deeply integrated with Empirica

    Queries actual investigation history, not just pattern matching
    """

    def __init__(self, project_id: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize checker with Empirica database access

        Args:
            project_id: Project to query for evidence (if None, queries all)
            session_id: Specific session to query (if None, queries all sessions)
        """
        self.project_id = project_id
        self.session_id = session_id

        # Connect to Empirica database
        if SessionDatabase:
            try:
                self.db = SessionDatabase()
            except Exception as e:
                print(f"Warning: Could not connect to database: {e}", file=sys.stderr)
                self.db = None
        else:
            self.db = None

        # Claim extraction patterns
        self.patterns = {
            'percentage': re.compile(r'(\d+\.?\d*)\s*%\s+(\w+)', re.IGNORECASE),
            'ratio': re.compile(r'(\d+)\s+out of\s+(\d+)', re.IGNORECASE),
            'reduction': re.compile(r'(\d+\.?\d*)\s*%\s+(reduction|increase|improvement|decrease)', re.IGNORECASE),
            'causal': re.compile(r'\b(causes?|leads? to|results? in|enables?|prevents?|bypasses?)\b', re.IGNORECASE),
            'comparative': re.compile(r'\b(better than|outperforms?|exceeds?|superior to|faster than)\b', re.IGNORECASE),
            'temporal': re.compile(r'(\d+\.?\d*)\s+(hours?|days?|weeks?|months?|years?)', re.IGNORECASE),
            'measured': re.compile(r'\b(measured|tested|demonstrated|validated|empirically|proven)\b', re.IGNORECASE),
            'quantitative': re.compile(r'\b(\d+\.?\d*)\s+(times|fold|orders? of magnitude)\b', re.IGNORECASE),
        }

    def extract_claims(self, text: str) -> List[EpistemicClaim]:
        """Extract empirical claims from text"""
        claims = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Skip markdown headers, code blocks, etc.
            if line.strip().startswith('#') or line.strip().startswith('```'):
                continue

            # Check each pattern
            for claim_type, pattern in self.patterns.items():
                if pattern.search(line):
                    sentence = self._extract_sentence(text, line_num)

                    if sentence:
                        claims.append(EpistemicClaim(
                            text=sentence,
                            claim_type=claim_type,
                            line_number=line_num,
                            context=line.strip()
                        ))
                        break  # One claim per line

        return claims

    def _extract_sentence(self, text: str, line_num: int) -> str:
        """Extract full sentence from line number"""
        lines = text.split('\n')
        if line_num > len(lines):
            return ""

        line = lines[line_num - 1]
        sentence = line.strip()
        sentence = re.sub(r'^[-*•]\s+', '', sentence)
        sentence = re.sub(r'^\d+\.\s+', '', sentence)

        return sentence

    def assess_claim(self, claim: EpistemicClaim) -> EpistemicAssessment:
        """
        ACTUAL epistemic self-assessment using experiential noetics

        Three-tier assessment:
        1. Do I have evidence from investigation? (experiential)
        2. Do I have training data knowledge? (training)
        3. Do I not know this? (unknown)
        """

        # Query evidence base for supporting findings
        experiential_evidence = self._query_evidence_base(claim)

        # Tier 1: Experiential knowledge (highest confidence)
        if experiential_evidence:
            return EpistemicAssessment(
                claim=claim,
                know=0.9,  # High confidence - I investigated this
                uncertainty=0.1,  # Low uncertainty - direct evidence
                evidence=experiential_evidence,
                reasoning=f"I investigated this topic and logged {len(experiential_evidence)} findings. "
                          f"This claim is grounded in actual work: {', '.join(e.finding_id[:8] for e in experiential_evidence)}",
                evidence_type="experiential"
            )

        # Tier 2: Training data knowledge (medium confidence)
        # Check if claim matches training patterns
        if self._matches_training_patterns(claim):
            return EpistemicAssessment(
                claim=claim,
                know=0.6,  # Medium confidence - training data suggests this
                uncertainty=0.4,  # Moderate uncertainty - not verified
                evidence=[],
                reasoning="This matches patterns from my training data, but I have not investigated it directly. "
                          "Cannot claim high confidence without experiential evidence.",
                evidence_type="training"
            )

        # Tier 3: Unknown (honest assessment)
        return EpistemicAssessment(
            claim=claim,
            know=0.2,  # Low confidence - I don't know this
            uncertainty=0.8,  # High uncertainty - no grounding
            evidence=[],
            reasoning="I have no investigation history on this topic and no clear training data match. "
                      "This claim is ungrounded - needs verification or removal.",
            evidence_type="none"
        )

    def _query_evidence_base(self, claim: EpistemicClaim) -> List[ExperientialEvidence]:
        """
        Query Empirica findings database for supporting evidence

        This is the key difference from v1 - actual evidence lookup
        """
        if not self.db:
            return []

        evidence = []

        try:
            # Extract key terms from claim
            claim_terms = set(re.findall(r'\b\w{4,}\b', claim.text.lower()))
            if len(claim_terms) < 2:
                return []

            # Query findings from database
            # Note: This is a simplified query - real implementation should use
            # proper SQL joins and semantic search
            conn = self.db.conn

            # Build query (note: impact is in finding_data JSON, default to 0.5)
            if self.session_id:
                query = """
                    SELECT id, finding, session_id, finding_data, created_timestamp
                    FROM project_findings
                    WHERE session_id = ?
                    ORDER BY created_timestamp DESC
                """
                params = (self.session_id,)
            elif self.project_id:
                query = """
                    SELECT id, finding, session_id, finding_data, created_timestamp
                    FROM project_findings
                    WHERE project_id = ?
                    ORDER BY created_timestamp DESC
                """
                params = (self.project_id,)
            else:
                query = """
                    SELECT id, finding, session_id, finding_data, created_timestamp
                    FROM project_findings
                    ORDER BY created_timestamp DESC
                    LIMIT 1000
                """
                params = ()

            cursor = conn.execute(query, params)

            for row in cursor:
                finding_id, finding_text, session_id, finding_data_json, timestamp = row

                # Extract impact from finding_data JSON if available
                impact = 0.5
                if finding_data_json:
                    try:
                        finding_data = json.loads(finding_data_json)
                        impact = finding_data.get('impact', 0.5)
                    except:
                        pass

                # Check if finding supports claim (simple term overlap)
                finding_terms = set(re.findall(r'\b\w{4,}\b', finding_text.lower()))
                overlap = len(claim_terms & finding_terms)

                # If significant overlap, consider it supporting evidence
                if overlap >= 3:  # At least 3 common terms
                    evidence.append(ExperientialEvidence(
                        finding_id=finding_id,
                        finding_text=finding_text,
                        session_id=session_id,
                        impact=impact or 0.5,
                        timestamp=timestamp
                    ))

        except Exception as e:
            print(f"Warning: Error querying evidence base: {e}", file=sys.stderr)

        return evidence

    def _matches_training_patterns(self, claim: EpistemicClaim) -> bool:
        """
        Check if claim matches training data patterns

        This is heuristic-based since I can't directly query my training
        But better than nothing for claims without investigation
        """
        # Heuristic: Claims with "measured", "tested" language suggest
        # they SHOULD have evidence but might not
        if self.patterns['measured'].search(claim.text):
            return False  # These REQUIRE experiential evidence

        # Heuristic: Very specific numbers without context are suspicious
        if self.patterns['percentage'].search(claim.text):
            # Check if it's in a "measured" or "validated" context
            if 'measured' in claim.context.lower() or 'tested' in claim.context.lower():
                return False  # Should have evidence
            else:
                return True  # Might be from training patterns

        # Heuristic: Causal claims usually need investigation
        if claim.claim_type == 'causal':
            return True  # Training data has causal patterns

        # Default: assume some training data exists
        return True

    def check_document(self, document_path: Path) -> Dict[str, Any]:
        """
        Run full epistemic check on document with experiential noetics

        Returns:
            Dict with claims, assessments, flagged claims, summary
        """
        # Read document
        with open(document_path, 'r') as f:
            text = f.read()

        # Extract claims
        claims = self.extract_claims(text)

        # Assess each claim using experiential noetics
        assessments = [self.assess_claim(claim) for claim in claims]

        # Categorize by evidence type
        experiential = [a for a in assessments if a.evidence_type == "experiential"]
        training = [a for a in assessments if a.evidence_type == "training"]
        unknown = [a for a in assessments if a.evidence_type == "none"]

        # Separate flagged from verified
        flagged = [a for a in assessments if a.should_flag()[0]]
        verified = [a for a in assessments if not a.should_flag()[0]]

        # Generate summary
        summary = {
            'document': str(document_path),
            'total_claims': len(claims),
            'verified': len(verified),
            'flagged': len(flagged),
            'by_evidence_type': {
                'experiential': len(experiential),
                'training': len(training),
                'unknown': len(unknown)
            },
            'flagged_rate': len(flagged) / len(claims) if claims else 0,
            'experiential_rate': len(experiential) / len(claims) if claims else 0,
        }

        return {
            'summary': summary,
            'assessments': [a.to_dict() for a in assessments],
            'flagged_claims': [a.to_dict() for a in flagged],
            'verified_claims': [a.to_dict() for a in verified],
            'by_evidence_type': {
                'experiential': [a.to_dict() for a in experiential],
                'training': [a.to_dict() for a in training],
                'unknown': [a.to_dict() for a in unknown]
            }
        }

    def generate_report(self, check_result: Dict[str, Any]) -> str:
        """Generate human-readable verification report"""
        summary = check_result['summary']
        flagged = check_result['flagged_claims']
        by_type = check_result['by_evidence_type']

        report = []
        report.append("# Epistemic Verification Report (Experiential Noetics)")
        report.append("")
        report.append(f"**Document:** {summary['document']}")
        report.append("")

        # Summary
        report.append("## Summary")
        report.append("")
        report.append(f"- **Total claims:** {summary['total_claims']}")
        report.append(f"- **Verified:** {summary['verified']} ({100 * (1 - summary['flagged_rate']):.1f}%)")
        report.append(f"- **Flagged:** {summary['flagged']} ({100 * summary['flagged_rate']:.1f}%)")
        report.append("")

        # Evidence breakdown
        report.append("**Evidence breakdown:**")
        report.append(f"- ✅ **Experiential** (investigated): {summary['by_evidence_type']['experiential']} ({100 * summary['experiential_rate']:.1f}%)")
        report.append(f"- ⚠️ **Training data** (not verified): {summary['by_evidence_type']['training']}")
        report.append(f"- ❌ **Unknown** (ungrounded): {summary['by_evidence_type']['unknown']}")
        report.append("")

        # Key insight
        if summary['experiential_rate'] < 0.3:
            report.append("⚠️ **LOW EXPERIENTIAL GROUNDING:** Less than 30% of claims backed by investigation.")
            report.append("Most claims rely on training data or are ungrounded. Consider:")
            report.append("- Run investigations to build evidence base")
            report.append("- Mark unverified claims as theoretical predictions")
            report.append("- Remove claims without grounding")
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
                report.append("**Epistemic Assessment:**")
                report.append(f"- Knowledge: {state['know']:.2f}")
                report.append(f"- Uncertainty: {state['uncertainty']:.2f}")
                report.append(f"- Evidence type: {state['evidence_type']}")

                if state['evidence']:
                    report.append(f"- Supporting findings: {len(state['evidence'])}")
                    for e in state['evidence'][:3]:  # Show first 3
                        report.append(f"  - Finding {e['finding_id'][:8]}: {e['finding_text'][:60]}...")
                else:
                    report.append("- Evidence: None")

                report.append("")
                report.append(f"**Reasoning:** {state['reasoning']}")
                report.append("")
                report.append("**Flags:**")
                for flag in flags:
                    report.append(f"- ❌ {flag}")
                report.append("")
                report.append("---")
                report.append("")
        else:
            report.append("## ✅ All Claims Verified")
            report.append("")
            report.append("All empirical assertions grounded in investigation or training data.")
            report.append("")

        return "\n".join(report)


def main():
    """CLI interface for epistemic checking v2"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Proactive epistemic checker v2 - experiential noetics with Empirica integration"
    )
    parser.add_argument('document', help='Path to document to check')
    parser.add_argument('--project-id', help='Limit evidence to specific project')
    parser.add_argument('--session-id', help='Limit evidence to specific session')
    parser.add_argument('--output', choices=['json', 'report'], default='report')

    args = parser.parse_args()

    # Run check with Empirica integration
    checker = EpistemicCheckerV2(
        project_id=args.project_id,
        session_id=args.session_id
    )
    result = checker.check_document(Path(args.document))

    # Output
    if args.output == 'json':
        print(json.dumps(result, indent=2))
    else:
        report = checker.generate_report(result)
        print(report)


if __name__ == '__main__':
    main()
