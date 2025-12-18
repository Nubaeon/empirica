"""
Data structures for reasoning layer outputs
"""

from dataclasses import dataclass
from typing import List, Dict, Literal

@dataclass
class DeprecationJudgment:
    """Result of deprecation analysis"""
    feature: str
    status: Literal["deprecated", "historical", "active"]
    confidence: float  # 0.0-1.0
    reasoning: str
    evidence: List[str]
    recommendation: str
    metadata: Dict = None

@dataclass
class RelationshipAnalysis:
    """Result of doc-code relationship analysis"""
    doc_ref: str  # Where doc is found (file:line)
    code_ref: str  # Where code is found (file:line)
    relationship: Literal["aligned", "drift", "phantom", "undocumented", "deprecated_doc"]
    confidence: float
    reasoning: str
    mismatches: List[str]  # Specific differences found
    severity: Literal["critical", "high", "medium", "low"]
    recommendation: str
    metadata: Dict = None

@dataclass
class ImplementationGap:
    """Result of implementation gap analysis"""
    feature: str  # Feature name being analyzed
    gap_type: Literal["matches", "partial", "mismatch", "untested", "undocumented_features"]
    confidence: float
    reasoning: str
    gaps: List[str]  # Specific gaps found
    severity: Literal["critical", "high", "medium", "low"]
    missing_features: List[str]  # Features in doc but not in code
    extra_features: List[str]  # Features in code but not in doc
    recommendation: str
    metadata: Dict = None
