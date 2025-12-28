# Empirica: Reasoning Layer Architecture

**Product:** AI-Powered Doc-Code Intelligence Reasoning Assistant
**Status:** Design Phase (v0.9.2) - Ready for model selection and implementation
**Goal:** To enable AI agents to genuinely understand semantic connections between code and documentation, moving beyond simple heuristics.

---

## Executive Summary

The Reasoning Layer is a new, critical component in Empirica's architecture designed to overcome the limitations of heuristic-based analysis for doc-code intelligence. It provides AI-powered judgment to genuinely understand context, meaning, and relationships, filtering a high volume of heuristic candidates into a small set of actionable items for human review. This layer amplifies human judgment, ensuring synchronization between documentation and code, and facilitating accurate epistemic awareness for AI agents.

---

## Overall Architecture: Reasoning Layer in Context

The Reasoning Layer is positioned as an intelligent middleware, making informed judgments based on signals gathered from various sources.

```
┌─────────────────────────────────────────────────────────────┐
│                  PROJECT-BOOTSTRAP                          │
│              (Context Aggregator)                           │
│  - Gathers signals from multiple sources                    │
│  - Aggregates evidence                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              HEURISTIC DETECTOR                             │
│           (Fast Pattern Matching)                           │
│  - Finds "deprecated" in text                               │
│  - Counts usage in artifacts                                │
│  - Checks git timestamps                                    │
│  Output: ~129 candidates (many false positives)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            REASONING LAYER (NEW!)                           │
│         (AI-Powered Judgment)                               │
│  - Understands context ("previously" vs "currently")        │
│  - Synthesizes evidence                                     │
│  - Makes judgment calls                                     │
│  - Explains reasoning                                       │
│  Output: High-confidence judgments with explanations        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               HUMAN DECISION                                │
│         (Final Authority)                                   │
│  - Reviews reasoning                                        │
│  - Makes final call                                         │
│  - Executes changes                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer Responsibilities & Separation of Concerns

Each layer in the doc-code intelligence pipeline has distinct responsibilities:

### 1. Project-Bootstrap (Context Aggregator)
**Responsibility:** Gather ALL relevant signals and evidence.
*   **Does:** Queries artifacts, git history, usage patterns, documentation, and code.
*   **Does NOT:** Make judgments, decide deprecation status, or change anything.
*   **Output:** Raw evidence dictionary for a given feature.

### 2. Heuristic Detector (Fast Pattern Matching)
**Responsibility:** Rapidly identify potential doc-code discrepancies based on simple patterns.
*   **Does:** Finds keywords (e.g., "deprecated"), counts usage, checks timestamps.
*   **Does NOT:** Understand context, explain findings, or make judgment calls.
*   **Output:** A large list of heuristic candidates (e.g., 129 candidates, many false positives).

### 3. Reasoning Layer (AI-Powered Judgment)
**Responsibility:** Filter heuristic candidates into actionable judgments by genuinely understanding context and explaining its decisions.
*   **Does:** Understands temporal and semantic context, synthesizes evidence, makes informed judgments with confidence scores, explains reasoning, and recommends specific actions.
*   **Does NOT:** Execute changes, commit to git, or override human decisions.
*   **Primary Job:** Filter ~129 heuristic candidates down to 10-15 high-confidence, actionable items.
*   **Philosophy:** AI as a cognitive assistant, amplifying human judgment, not replacing it.

### 4. Human Decision (Final Authority)
**Responsibility:** Review the AI's reasoning, make final decisions, and execute changes.
*   **Does:** Reviews AI's judgments, provides feedback, and makes changes based on the amplified insights.
*   **Output:** Concrete code or documentation changes.

---

## Implementation Components: Reasoning Service

The core of the Reasoning Layer is the `ReasoningService` interface, which defines methods for various analysis tasks.

### 1. Reasoning Service Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Literal
from dataclasses import dataclass

@dataclass
class DeprecationJudgment:
    feature: str
    status: Literal["deprecated", "historical", "active"]
    confidence: float  # 0.0-1.0
    reasoning: str
    evidence: List[str]
    recommendation: str
    metadata: Dict

@dataclass
class RelationshipAnalysis:
    relationship: Literal["aligned", "partial", "drift", "unrelated"]
    confidence: float
    reasoning: str
    gaps: List[str]
    action: str

@dataclass
class ImplementationGap:
    gap_type: Literal["missing", "different", "extra", "none"]
    severity: Literal["critical", "high", "medium", "low"]
    confidence: float
    reasoning: str
    impact: str
    recommendation: str

class ReasoningService(ABC):
    """
    Abstract interface for reasoning models
    Supports: Local models, API models, custom implementations
    """
    
    @abstractmethod
    def analyze_deprecation(
        self, 
        feature: str,
        context: Dict
    ) -> DeprecationJudgment:
        """Analyze if feature is actually deprecated."""
        pass
    
    @abstractmethod
    def analyze_relationship(
        self,
        doc_section: str,
        code_section: str
    ) -> RelationshipAnalysis:
        """Analyze if doc and code describe the same thing."""
        pass
    
    @abstractmethod
    def analyze_implementation_gap(
        self,
        documented_behavior: str,
        actual_implementation: str
    ) -> ImplementationGap:
        """Analyze if implementation matches documented behavior."""
        pass
```

### 2. Local Model Adapter

An adapter like `OllamaReasoningModel` will implement the `ReasoningService` interface, connecting to locally-hosted large language models.

```python
import requests # Example import

class OllamaReasoningModel(ReasoningService):
    """Adapter for Ollama-hosted models"""
    
    def __init__(
        self,
        model_name: str,
        endpoint: str = "http://empirica-server:11434",
        temperature: float = 0.1
    ):
        self.model_name = model_name
        self.endpoint = endpoint
        self.temperature = temperature
        # ... (other initialization)
    
    def _call_ollama(self, prompt: str, format: str = "json") -> Dict:
        """Low-level Ollama API call"""
        # ... (implementation using requests.post)
        pass
    
    def analyze_deprecation(self, feature: str, context: Dict) -> DeprecationJudgment:
        # ... (implementation building prompt and parsing response)
        pass
    # ... (implement other analyze_ methods)
```

### 3. Prompt Templates

Structured prompt templates guide the reasoning model for specific tasks:

```python
DEPRECATION_ANALYSIS_PROMPT = """
You are analyzing whether a software feature is genuinely deprecated.

Feature: {feature}

Context:
- Documentation mentions: {doc_mentions}
- Code implementation: {code_snippet}
- Usage in last 50 sessions: {usage_count} times
- Last git commit: {last_commit_date}
- Related features: {related_features}

Task: Determine if this feature is:
1. Currently deprecated (should be removed/marked)
2. Previously deprecated but now current (historical context only)
3. Still active and in use

Reasoning guidelines:
- "previously deprecated" = past tense, not current
- Check if code is actively maintained
- Check if usage patterns show active use
- Consider relationships to other features

Respond in JSON:
{{
    "status": "deprecated|historical|active",
    "confidence": 0.0-1.0,
    "reasoning": "step-by-step analysis",
    "evidence": ["key evidence points"],
    "recommendation": "specific action to take"
}}
"""

# ... (Similar templates for RELATIONSHIP_ANALYSIS_PROMPT and IMPLEMENTATION_GAP_PROMPT)
```

### 4. Batch Analysis Pipeline

A `ReasoningPipeline` will manage batch processing, caching, and parallel execution for analyzing multiple candidates efficiently.

```python
class ReasoningPipeline:
    """Batch processing pipeline for analyzing candidates."""
    
    def analyze_deprecation_candidates(
        self,
        candidates: List[Dict],
        reasoning_service: ReasoningService
    ) -> List[DeprecationJudgment]:
        """Process all deprecation candidates."""
        # ... (implementation)
        pass
    
    def _gather_context(self, candidate: Dict) -> Dict:
        """Gather all relevant context for reasoning."""
        # ... (implementation)
        pass
```

---

## Communication & Integration Strategy

The Reasoning Service will integrate into Empirica through a hybrid approach to maximize flexibility and utility.

### Communication Options Explored:
1.  **Direct HTTP API (Ollama):** Simple, low latency, but tightly coupled.
2.  **Action Hook (Event-Driven):** Loosely coupled, extensible, fits existing Empirica patterns. Example integration in `project-bootstrap`.
3.  **MCP Tool Integration:** Reasoning as an MCP tool for AI-to-AI communication within MCP workflows.

### Recommended Hybrid Architecture:
The recommended approach combines the best aspects of these options:
1.  **Core `OllamaReasoningModel`:** A generic, reusable Python class that directly interfaces with local reasoning models (e.g., Ollama). This provides direct Python access for scripts and testing.
2.  **`project-bootstrap` Integration:** The primary integration point, where `project-bootstrap` can optionally invoke the Reasoning Service via an action hook to analyze integrity candidates.
3.  **MCP Tool (Future):** Expose the Reasoning Service as an MCP tool later, enabling seamless AI-to-AI reasoning within workflow orchestrations.

---

## Model Requirements & Configuration

### Ideal Model Characteristics:
*   Fast inference (< 1s per judgment)
*   Strong reasoning capabilities
*   Reliable JSON output
*   Context window: 4K-8K tokens
*   Capable of local deployment (e.g., via Ollama)

### Candidate Models:
*   **Qwen2.5-14B:** Strong reasoning, good JSON.
*   **DeepSeek-R1-7B:** Specialized for reasoning.
*   **Llama 3.3-70B:** Powerful but slower.
*   Custom fine-tuned models.

### Server Configuration (Ollama Example):
*   **URL:** `http://empirica-server:11434`
*   **Format:** JSON
*   **Timeout:** 30s (adjustable)

### Empirica Configuration (`reasoning_config.yaml`):
```yaml
reasoning:
  default_model: "phi4"
  endpoint: "http://empirica-server:11434"
  timeout: 30
  retry_attempts: 2
  fallback_to_heuristic: true
  
  models:
    phi4:
      temperature: 0.1
      top_p: 0.9
      max_tokens: 2048
    
    qwen2.5:
      temperature: 0.2
      top_p: 0.95
      max_tokens: 1024
```

---

## Error Handling

A robust error handling mechanism is defined to manage issues like model unavailability, timeouts, or invalid responses, with graceful degradation to heuristic analysis if reasoning fails.

```python
class ReasoningError(Exception): pass
class ModelNotAvailableError(ReasoningError): pass
class ReasoningTimeoutError(ReasoningError): pass
class InvalidResponseError(ReasoningError): pass

# Example graceful degradation:
try:
    judgment = reasoning.analyze_deprecation(feature, context)
except ReasoningError as e:
    # Fallback to heuristic analysis
    pass
```

---

## Testing Strategy & Rollout Plan

### Testing Strategy:
1.  **Ground Truth Dataset:** Create labeled examples for specific analysis tasks (e.g., deprecation, alignment).
2.  **Accuracy Measurement:** Evaluate reasoning service accuracy against ground truth.
3.  **Human Validation:** Expert review of a subset of AI judgments to refine prompts and models.

### Rollout Plan:
*   **Week 1 (Implementation):** Core service interface, local adapter, prompt engineering.
*   **Week 2 (Validation):** Ground truth creation, extensive testing, human validation.
*   **Week 3 (Production):** Documentation, CLI commands, apply recommendations.

---

## Product Positioning

**Name:** Empirica Reasoning Layer
**Tagline:** "Any local AI becomes a doc-code intelligence expert"

**Value Proposition:**
*   Turns local LLMs into specialized reasoning assistants.
*   Enables understanding of context, not just patterns.
*   Provides explanations for every decision.
*   Ensures privacy through local inference.

---

This architecture is metacognitive infrastructure for AI systems, designed to enhance the epistemic capabilities of Empirica.
