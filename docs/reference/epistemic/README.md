# Epistemic Theory & Framework Documentation

This folder contains the theoretical foundation and operational specifications for Empirica's epistemic vector framework.

## Files

### **UNIFIED_EPISTEMIC_THEORY.md** (Academic Paper)
- **Type**: Research paper for publication
- **Audience**: ML researchers, AI safety community, academic reviewers
- **Content**:
  - Mathematical proofs linking epistemic vectors to transformer attention mechanisms (Theorems 1-16)
  - Observational validation study (N=186 CASCADE workflows)
  - Empirical evidence: 4.3x learning multiplier, 93% uncertainty reduction
  - References, appendices with computational algorithms
- **Status**: Ready for arXiv submission
- **Length**: 2,242 lines (80KB)
- **Last updated**: 2025-12-27

### **UNIFIED_EPISTEMIC_VECTORS.md** (Operational Specification)
- **Type**: Practical guide for users and developers
- **Audience**: AI agents, developers integrating Empirica, power users
- **Content**:
  - Complete specification of 13 epistemic vectors
  - Tier structure (ENGAGEMENT gate, Foundation, Comprehension, Execution)
  - Calibration guidance with examples
  - Decision logic and confidence calculation formulas
  - Human analogies for each vector
- **Status**: Current reference implementation
- **Length**: 1,134 lines (32KB)
- **Last updated**: 2025-12-27

### **METACOGNITIVE_CASCADE.md** (Workflow Documentation)
- **Type**: Process documentation
- **Audience**: Developers, researchers studying the CASCADE workflow
- **Content**:
  - PREFLIGHT → INVESTIGATE → CHECK → POSTFLIGHT workflow
  - Metacognitive assessment protocols
  - Gate decision logic
  - Learning measurement methodology
- **Status**: Current operational guide
- **Length**: ~600 lines (17KB)

---

## How These Relate

```
UNIFIED_EPISTEMIC_THEORY.md
│
├─ Theoretical foundation: Proves vectors are isomorphic to attention mechanisms
│  │
│  └─ Enables: Pre-inference gating via Sentinel protocol
│
UNIFIED_EPISTEMIC_VECTORS.md
│
├─ Operational specification: How to use the 13 vectors in practice
│  │
│  └─ Implements: Post-inference self-assessment
│
METACOGNITIVE_CASCADE.md
│
└─ Workflow protocol: PREFLIGHT → CHECK → POSTFLIGHT process
   │
   └─ Measures: Learning deltas (ΔKnow, ΔUncertainty)
```

---

## Citation

If you use this framework in research, please cite:

```bibtex
@misc{vanassche2025epistemic,
  title={Epistemic Vectors as Computable Invariants of Transformer Attention Mechanisms},
  author={Van Assche, David S. L.},
  year={2025},
  note={Empirica Framework},
  howpublished={\\url{https://github.com/yourusername/empirica}}
}
```

---

## Future Work

See **UNIFIED_EPISTEMIC_THEORY.md Section 11 (Conclusion)** for:
- Pre-inference validation experiments (requires MIT-licensed model access)
- External rater validation of epistemic state
- Longitudinal learning trajectory tracking
- Ground-truth task outcome measurements
