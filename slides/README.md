# Empirica Presentation Slides

**Purpose:** Source materials for Empirica documentation and presentations

## Contents

### Slide Decks (PNG format)

- **ledger-01.png through ledger-15.png** (15 slides)
  - "The AI Epistemic Ledger" presentation
  - Covers: epistemic ledger concept, CASCADE workflow, git integration

- **architecture-01.png through architecture-13.png** (13 slides)  
  - "Empirica: Reliable AI Architecture" presentation
  - Covers: system architecture, components, integration patterns

### PDF Source Documents

Located in `pdfs/`:
- `The_AI_Epistemic_Ledger.pdf` - Original ledger deck (15 slides)
- `Empirica_Reliable_AI_Architecture.pdf` - Original architecture deck (13 slides)

## Epistemic Assessments

Slides have been processed with Empirica's vision system:

**Assessment Results:**
- **Ledger deck:** Average context value 0.53 (Good), very dense content
- **Architecture deck:** Average context value 0.50 (Good), clear visuals

**Reports generated:**
- `.empirica/slides/assessment_ledger-all.png.json` - Detailed scores
- `.empirica/slides/assessment_architecture-all.png.json` - Detailed scores
- `.empirica/slides/summary_*.md` - Human-readable summaries

## Vision System

These slides were used to test and validate Empirica's vision assessment capabilities:
- OCR text extraction (95%+ accuracy)
- Visual element detection (diagrams, code, tables)
- Epistemic scoring (clarity, signal, density, impact)
- Study guide generation

See: `empirica/vision/slide_processor.py` for processing code

## Usage

### Process slides with epistemic assessment:
```bash
python -m empirica.vision.slide_processor "slides/ledger-*.png"
```

### Generate human-readable study guide:
```bash
python -m empirica.vision.readable_translator \
    .empirica/slides/assessment_ledger-all.png.json
```

### View specific slide assessment:
```bash
python -m empirica.vision.readable_translator \
    .empirica/slides/assessment_ledger-all.png.json \
    --slide 11
```

## Future Enhancement

These slides will be used for:
- Content improvement engine testing
- Multimodal prompt generation
- Before/after regeneration comparison
- Project-bootstrap context loading

---

**Note:** Slide images are treated as source materials, not build artifacts.
They are versioned in git for reproducibility and testing purposes.
