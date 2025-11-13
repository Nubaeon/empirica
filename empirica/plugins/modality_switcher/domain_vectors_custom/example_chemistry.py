#!/usr/bin/env python3
"""
Example Custom Domain: Chemistry Research

This is an example of how to define a custom domain for epistemic snapshots.
Copy and modify this template for your own domain-specific vectors.
"""

DOMAIN_NAME = "chemistry_research"

DOMAIN_DESCRIPTION = "Chemistry experiment analysis and validation"

DOMAIN_VECTORS = {
    "hypothesis_clarity": "Research hypothesis is well-defined and testable",
    "method_validity": "Experimental method is scientifically sound",
    "data_quality": "Data collection is rigorous and reproducible",
    "safety_compliance": "Safety protocols followed correctly",
    "literature_grounding": "Work builds on existing research",
    "reproducibility": "Experiment can be reliably reproduced"
}

DOMAIN_WEIGHTS = {
    "hypothesis_clarity": 0.9,
    "method_validity": 1.0,    # Critical
    "data_quality": 1.0,        # Critical
    "safety_compliance": 1.0,   # Critical
    "literature_grounding": 0.7,
    "reproducibility": 0.9
}
