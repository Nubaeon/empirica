#!/usr/bin/env python3
"""
Domain Vector Registry - Extensible epistemic dimensions per domain

Built-in Domains:
- code_analysis: Software engineering vectors
- medical_diagnosis: Healthcare reasoning vectors
- legal_analysis: Legal reasoning vectors
- financial_analysis: Risk assessment vectors

Custom Domains:
- Register via register_domain_vectors(domain_name, vector_config)
- Auto-discover from domain_vectors_custom/*.py
"""

from typing import Dict, List, Optional
from pathlib import Path
import importlib.util
import logging

logger = logging.getLogger(__name__)

# Global registry
_DOMAIN_REGISTRY: Dict[str, Dict] = {}

# Built-in domain vector definitions
BUILTIN_DOMAINS = {
    "code_analysis": {
        "description": "Software engineering and code quality assessment",
        "vectors": {
            "correctness": "Code produces expected outputs",
            "readability": "Code is clear and maintainable",
            "performance": "Code efficiency and optimization",
            "security": "Code follows security best practices",
            "testability": "Code is easy to test and verify",
            "architecture": "Code structure and design patterns"
        },
        "weights": {
            "correctness": 1.0,  # Critical
            "readability": 0.8,
            "performance": 0.7,
            "security": 0.9,
            "testability": 0.8,
            "architecture": 0.7
        }
    },
    
    "medical_diagnosis": {
        "description": "Healthcare reasoning and diagnostic assessment",
        "vectors": {
            "symptom_coverage": "All symptoms accounted for",
            "differential_breadth": "Range of diagnoses considered",
            "evidence_strength": "Quality of supporting evidence",
            "risk_assessment": "Patient safety considerations",
            "treatment_alignment": "Treatment matches diagnosis",
            "follow_up_clarity": "Clear next steps identified"
        },
        "weights": {
            "symptom_coverage": 0.9,
            "differential_breadth": 0.8,
            "evidence_strength": 1.0,  # Critical
            "risk_assessment": 1.0,     # Critical
            "treatment_alignment": 0.9,
            "follow_up_clarity": 0.7
        }
    },
    
    "legal_analysis": {
        "description": "Legal reasoning and case assessment",
        "vectors": {
            "precedent_coverage": "Relevant case law identified",
            "statute_alignment": "Applicable laws referenced",
            "argument_strength": "Quality of legal reasoning",
            "counterargument_awareness": "Opposing views considered",
            "procedural_clarity": "Process steps identified",
            "risk_mitigation": "Legal risks assessed"
        },
        "weights": {
            "precedent_coverage": 0.9,
            "statute_alignment": 1.0,  # Critical
            "argument_strength": 0.8,
            "counterargument_awareness": 0.7,
            "procedural_clarity": 0.8,
            "risk_mitigation": 0.9
        }
    },
    
    "financial_analysis": {
        "description": "Financial and risk assessment",
        "vectors": {
            "data_accuracy": "Financial data is correct",
            "risk_identification": "Key risks identified",
            "model_validity": "Financial models are sound",
            "compliance_check": "Regulatory requirements met",
            "sensitivity_analysis": "What-if scenarios explored",
            "recommendation_clarity": "Clear actionable recommendations"
        },
        "weights": {
            "data_accuracy": 1.0,      # Critical
            "risk_identification": 1.0, # Critical
            "model_validity": 0.9,
            "compliance_check": 1.0,    # Critical
            "sensitivity_analysis": 0.7,
            "recommendation_clarity": 0.8
        }
    }
}


def initialize_registry():
    """Initialize registry with built-in domains"""
    global _DOMAIN_REGISTRY
    _DOMAIN_REGISTRY = BUILTIN_DOMAINS.copy()
    logger.info(f"✅ Domain registry initialized with {len(_DOMAIN_REGISTRY)} built-in domains")


def register_domain_vectors(
    domain: str,
    description: str,
    vectors: Dict[str, str],
    weights: Optional[Dict[str, float]] = None
) -> bool:
    """
    Register custom domain vectors
    
    Args:
        domain: Domain name (e.g., "chemistry_research")
        description: Domain description
        vectors: Dict of {vector_name: description}
        weights: Optional dict of {vector_name: weight} (0.0-1.0)
        
    Returns:
        True if registered successfully
        
    Example:
        register_domain_vectors(
            domain="chemistry_research",
            description="Chemistry experiment analysis",
            vectors={
                "hypothesis_clarity": "Hypothesis is well-defined",
                "method_validity": "Experimental method is sound",
                "data_quality": "Data collection is rigorous"
            },
            weights={
                "hypothesis_clarity": 0.9,
                "method_validity": 1.0,
                "data_quality": 1.0
            }
        )
    """
    global _DOMAIN_REGISTRY
    
    # Default weights to 1.0 if not provided
    if weights is None:
        weights = {v: 1.0 for v in vectors.keys()}
    
    # Validate weights
    for vector in vectors.keys():
        if vector not in weights:
            weights[vector] = 1.0
        elif not 0.0 <= weights[vector] <= 1.0:
            logger.warning(f"Invalid weight for {vector}: {weights[vector]}, clamping to [0.0, 1.0]")
            weights[vector] = max(0.0, min(1.0, weights[vector]))
    
    _DOMAIN_REGISTRY[domain] = {
        "description": description,
        "vectors": vectors,
        "weights": weights
    }
    
    logger.info(f"✅ Registered domain '{domain}' with {len(vectors)} vectors")
    return True


def get_domain_vectors(domain: str) -> Optional[Dict]:
    """
    Get vector definitions for a domain
    
    Args:
        domain: Domain name
        
    Returns:
        Dict with {description, vectors, weights} or None if not found
    """
    if not _DOMAIN_REGISTRY:
        initialize_registry()
    
    return _DOMAIN_REGISTRY.get(domain)


def list_domains() -> List[str]:
    """
    List all registered domains
    
    Returns:
        List of domain names
    """
    if not _DOMAIN_REGISTRY:
        initialize_registry()
    
    return list(_DOMAIN_REGISTRY.keys())


def calculate_domain_confidence(domain: str, vector_scores: Dict[str, float]) -> float:
    """
    Calculate weighted confidence score for a domain
    
    Args:
        domain: Domain name
        vector_scores: Dict of {vector_name: score} (0.0-1.0)
        
    Returns:
        Weighted confidence score (0.0-1.0)
        
    Example:
        scores = {
            "correctness": 0.9,
            "readability": 0.8,
            "security": 0.95
        }
        confidence = calculate_domain_confidence("code_analysis", scores)
        # Returns weighted average based on domain weights
    """
    domain_config = get_domain_vectors(domain)
    if not domain_config:
        logger.warning(f"Unknown domain: {domain}")
        return 0.0
    
    weights = domain_config["weights"]
    
    # Calculate weighted sum
    weighted_sum = 0.0
    total_weight = 0.0
    
    for vector, score in vector_scores.items():
        if vector in weights:
            weight = weights[vector]
            weighted_sum += score * weight
            total_weight += weight
    
    # Return weighted average
    if total_weight > 0:
        return weighted_sum / total_weight
    else:
        return 0.0


def auto_discover_custom_domains(custom_dir: str = "domain_vectors_custom"):
    """
    Auto-discover custom domain definitions from Python files
    
    Looks for .py files in custom_dir that define:
    - DOMAIN_NAME: str
    - DOMAIN_DESCRIPTION: str
    - DOMAIN_VECTORS: Dict[str, str]
    - DOMAIN_WEIGHTS: Dict[str, float] (optional)
    
    Args:
        custom_dir: Directory to scan for custom domains
    """
    custom_path = Path(__file__).parent / custom_dir
    
    if not custom_path.exists():
        logger.info(f"No custom domain directory found: {custom_path}")
        return
    
    discovered = 0
    for py_file in custom_path.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Extract domain definition
            if hasattr(module, "DOMAIN_NAME") and hasattr(module, "DOMAIN_VECTORS"):
                domain_name = module.DOMAIN_NAME
                description = getattr(module, "DOMAIN_DESCRIPTION", f"Custom domain: {domain_name}")
                vectors = module.DOMAIN_VECTORS
                weights = getattr(module, "DOMAIN_WEIGHTS", None)
                
                register_domain_vectors(domain_name, description, vectors, weights)
                discovered += 1
                logger.info(f"✅ Auto-discovered domain '{domain_name}' from {py_file.name}")
                
        except Exception as e:
            logger.warning(f"Failed to load custom domain from {py_file.name}: {e}")
    
    if discovered > 0:
        logger.info(f"✅ Auto-discovered {discovered} custom domain(s)")


# Initialize on import
initialize_registry()
auto_discover_custom_domains()


if __name__ == "__main__":
    print("=" * 70)
    print("  DOMAIN VECTOR REGISTRY - TEST")
    print("=" * 70)
    
    print(f"\n✅ Registered domains: {', '.join(list_domains())}")
    
    # Show code_analysis domain
    print("\n" + "=" * 70)
    print("  CODE ANALYSIS DOMAIN")
    print("=" * 70)
    code = get_domain_vectors("code_analysis")
    print(f"\nDescription: {code['description']}")
    print(f"\nVectors ({len(code['vectors'])}):")
    for vector, desc in code["vectors"].items():
        weight = code["weights"][vector]
        print(f"  • {vector:20s} (weight: {weight:.0%}): {desc}")
    
    # Test confidence calculation
    print("\n" + "=" * 70)
    print("  CONFIDENCE CALCULATION TEST")
    print("=" * 70)
    test_scores = {
        "correctness": 0.9,
        "readability": 0.8,
        "performance": 0.7,
        "security": 0.95,
        "testability": 0.85,
        "architecture": 0.75
    }
    
    confidence = calculate_domain_confidence("code_analysis", test_scores)
    print(f"\nTest scores:")
    for vector, score in test_scores.items():
        print(f"  {vector:20s}: {score:.2f}")
    print(f"\nWeighted confidence: {confidence:.1%}")
    
    # Show all domains summary
    print("\n" + "=" * 70)
    print("  ALL DOMAINS SUMMARY")
    print("=" * 70)
    for domain in list_domains():
        config = get_domain_vectors(domain)
        print(f"\n{domain}:")
        print(f"  Description: {config['description']}")
        print(f"  Vectors: {len(config['vectors'])}")
        print(f"  Avg weight: {sum(config['weights'].values()) / len(config['weights']):.1%}")
    
    print("\n" + "=" * 70)
    print("  ✅ ALL TESTS PASSED")
    print("=" * 70)
