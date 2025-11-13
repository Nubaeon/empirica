# Custom Domain Vectors

This directory is for custom domain-specific epistemic vector definitions.

## Quick Start

Create a Python file in this directory (e.g., `chemistry_research.py`) with the following structure:

```python
#!/usr/bin/env python3
"""
Custom domain: Chemistry Research
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
```

## How It Works

1. **Auto-Discovery**: Files in this directory are automatically discovered on import
2. **Validation**: Weights are validated (0.0-1.0 range)
3. **Integration**: Domains are added to the global registry
4. **Usage**: Available via `get_domain_vectors("domain_name")`

## Required Fields

- `DOMAIN_NAME` (str): Unique identifier for the domain
- `DOMAIN_VECTORS` (dict): Vector names and descriptions

## Optional Fields

- `DOMAIN_DESCRIPTION` (str): Human-readable description (default: "Custom domain: {name}")
- `DOMAIN_WEIGHTS` (dict): Importance weights for each vector (default: 1.0 for all)

## Weight Guidelines

| Weight | Priority | Use For |
|--------|----------|---------|
| 1.0 | Critical | Safety, correctness, compliance |
| 0.9 | High | Core functionality, key requirements |
| 0.8 | Medium-High | Important but not critical |
| 0.7 | Medium | Nice to have, secondary concerns |
| 0.5 | Low | Optional, aesthetic concerns |

## Example Domains

### Engineering Domains
- `structural_engineering` - Building and structural analysis
- `electrical_systems` - Circuit and power system design
- `mechanical_design` - Mechanical system analysis

### Research Domains
- `clinical_trials` - Clinical research validation
- `data_science` - Data analysis and ML model assessment
- `theoretical_physics` - Physics theory validation

### Business Domains
- `market_analysis` - Market research and trends
- `product_strategy` - Product planning and roadmap
- `customer_service` - Support quality assessment

## Usage in Code

```python
from empirica.plugins.modality_switcher.domain_vectors import (
    get_domain_vectors,
    calculate_domain_confidence,
    list_domains
)

# List all available domains
domains = list_domains()
print(f"Available: {domains}")

# Get domain configuration
config = get_domain_vectors("chemistry_research")
print(f"Vectors: {config['vectors']}")

# Calculate weighted confidence
scores = {
    "hypothesis_clarity": 0.9,
    "method_validity": 0.85,
    "data_quality": 0.95,
    "safety_compliance": 1.0,
    "literature_grounding": 0.8,
    "reproducibility": 0.9
}

confidence = calculate_domain_confidence("chemistry_research", scores)
print(f"Weighted confidence: {confidence:.1%}")
```

## Integration with Snapshots

Domain vectors are stored in `EpistemicStateSnapshot.domain_vectors`:

```python
from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider

provider = EpistemicSnapshotProvider()

# Create snapshot with domain vectors
snapshot = provider.create_snapshot_from_session(
    session_id="abc-123",
    domain_vectors={
        "hypothesis_clarity": 0.9,
        "method_validity": 0.85,
        "data_quality": 0.95
    }
)

# Domain vectors included in context prompt
context = snapshot.to_context_prompt("full")
# Output includes: "Domain Vectors: hypothesis_clarity=0.9, ..."
```

## Testing Your Domain

```python
# Test file: test_my_domain.py
from empirica.plugins.modality_switcher.domain_vectors import get_domain_vectors, calculate_domain_confidence

def test_my_domain():
    config = get_domain_vectors("my_domain")
    assert config is not None, "Domain not registered"
    
    # Test all vectors have descriptions
    for vector in config["vectors"].keys():
        assert config["vectors"][vector], f"Missing description for {vector}"
    
    # Test weights are valid
    for vector, weight in config["weights"].items():
        assert 0.0 <= weight <= 1.0, f"Invalid weight for {vector}: {weight}"
    
    # Test confidence calculation
    test_scores = {v: 0.8 for v in config["vectors"].keys()}
    confidence = calculate_domain_confidence("my_domain", test_scores)
    assert 0.0 <= confidence <= 1.0, f"Invalid confidence: {confidence}"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test_my_domain()
```

## Best Practices

### 1. Keep Vectors Focused
- 4-8 vectors per domain is ideal
- Too many vectors dilute the assessment
- Too few may miss important aspects

### 2. Clear Descriptions
- Describe what "good" looks like for this vector
- Use active language ("Code follows..." not "Code should follow...")
- Be specific and measurable when possible

### 3. Thoughtful Weights
- Critical = 1.0 (safety, correctness, compliance)
- Important = 0.8-0.9 (core functionality)
- Nice-to-have = 0.6-0.7 (secondary concerns)

### 4. Domain Naming
- Use lowercase with underscores: `my_domain`
- Be specific: `mobile_app_ux` not just `ux`
- Avoid conflicts with built-in domains

### 5. Testing
- Test with various score combinations
- Verify weighted calculations make sense
- Check edge cases (all 0.0, all 1.0, mixed)

## Built-in Domains

The following domains are built-in and always available:

1. **code_analysis** - Software engineering (6 vectors)
2. **medical_diagnosis** - Healthcare reasoning (6 vectors)
3. **legal_analysis** - Legal reasoning (6 vectors)
4. **financial_analysis** - Financial assessment (6 vectors)

You can use these as templates for your custom domains.

## Troubleshooting

### Domain not appearing
- Check file is in `domain_vectors_custom/` directory
- Ensure file has `.py` extension
- Verify `DOMAIN_NAME` and `DOMAIN_VECTORS` are defined
- Check logs for import errors

### Invalid weights warning
- Weights must be between 0.0 and 1.0
- System will clamp invalid values
- Check `DOMAIN_WEIGHTS` dictionary

### Import errors
- Ensure no syntax errors in your file
- Don't use reserved Python keywords as vector names
- Avoid circular imports

## Contributing

To contribute a domain to the built-in set:

1. Create and test your custom domain
2. Document use cases and examples
3. Get feedback from domain experts
4. Submit PR to add to `BUILTIN_DOMAINS` in `domain_vectors.py`

---

**Questions?** Check the main documentation or open an issue.
