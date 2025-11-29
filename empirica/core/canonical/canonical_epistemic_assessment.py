"""
Canonical Epistemic Self-Assessment

Genuine LLM-powered metacognitive self-assessment WITHOUT heuristics or confabulation.

Core Principles:
1. Genuine Reasoning: LLM self-assessment only, no keyword matching
2. No Fallbacks: No heuristic mode, no static scores, no simulated reasoning
3. Canonical Weights: 35/25/25/15 (foundation/comprehension/execution/engagement)
4. ENGAGEMENT Gate: ≥0.60 required to proceed
5. Clear Terminology: epistemic weights ≠ internal weights (we measure state, not modify params)

Usage:
    assessor = CanonicalEpistemicAssessor()
    assessment = await assessor.assess(task, context)

    if assessment.engagement_gate_passed:
        if assessment.recommended_action == Action.PROCEED:
            # Execute task
        elif assessment.recommended_action == Action.INVESTIGATE:
            # Run investigation phase
    else:
        # Request clarification (ENGAGEMENT < 0.60)
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

from .reflex_frame import (
    VectorState,
    Action,
    CANONICAL_WEIGHTS,
    ENGAGEMENT_THRESHOLD,
    CRITICAL_THRESHOLDS
)

# NEW SCHEMA (this is now THE schema)
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment,
    CascadePhase
)


class CanonicalEpistemicAssessor:
    """
    Canonical LLM-powered epistemic self-assessor

    This assessor uses genuine AI reasoning to evaluate epistemic state
    across 12 vectors organized into 4 tiers.

    NO HEURISTICS. NO KEYWORD MATCHING. NO CONFABULATION.
    """

    def __init__(self, agent_id: str = "default"):
        """
        Initialize assessor

        Args:
            agent_id: Agent identifier for tracking
        """
        self.agent_id = agent_id
        self.assessment_count = 0

    def _generate_assessment_id(self, task: str) -> str:
        """Generate unique assessment ID"""
        self.assessment_count += 1
        timestamp = datetime.now(UTC).isoformat()
        content = f"{self.agent_id}_{timestamp}_{task}_{self.assessment_count}"
        hash_id = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"assess_{hash_id}"

    async def assess(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        profile: Optional['InvestigationProfile'] = None
    ) -> Dict[str, Any]:
        """
        Perform genuine LLM-powered epistemic self-assessment

        Args:
            task: Task description to assess
            context: Additional context (conversation history, tools, etc.)
            profile: Investigation profile for context-aware assessment

        Returns:
            Dict with 'self_assessment_prompt': Assessment prompt for LLM execution

        Process:
            1. Generate meta-prompt for LLM self-assessment
            2. Return meta-prompt for LLM execution
            3. Parse LLM response into EpistemicAssessment
            4. Apply canonical weights and thresholds
            5. Check ENGAGEMENT gate
            6. Determine recommended action

        Example:
            assessor = CanonicalEpistemicAssessor()
            result = await assessor.assess(
                "Refactor the authentication module",
                context={'available_tools': ['read', 'write', 'edit']}
            )

            # Execute self_assessment_prompt with LLM, get response
            llm_response = await llm.complete(result['self_assessment_prompt'])
            assessment = assessor.parse_llm_response(llm_response, result['assessment_id'], task, context, profile)

            if assessment.engagement_gate_passed:
                logger.info(f"Action: {assessment.recommended_action}")
        """
        if context is None:
            context = {}

        assessment_id = self._generate_assessment_id(task)

        # Build self-assessment prompt for genuine AI self-reflection
        self_assessment_prompt = self._build_self_assessment_prompt(task, context)

        # Return self-assessment prompt for AI to respond to
        # The AI uses this prompt to reason about its own epistemic state
        return {
            'requires_self_assessment': True,
            'assessment_id': assessment_id,
            'task': task,
            'context': context,
            'self_assessment_prompt': self_assessment_prompt,
            'instructions': (
                "Use this prompt to assess your own epistemic state. "
                "Reason genuinely about your knowledge, capabilities, and uncertainties. "
                "Return structured JSON with your self-assessment. "
                "Then call parse_llm_response() with your response to get EpistemicAssessment."
            )
        }

    def _build_self_assessment_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """
        Build self-assessment prompt for genuine AI self-reflection

        This prompt guides the AI to use its actual reasoning capabilities
        to evaluate its own epistemic state across all 12 vectors.

        NO HEURISTICS. The AI reasons genuinely about its knowledge state.
        """
        context_summary = self._format_context(context)

        self_assessment_prompt = f"""You are performing a metacognitive self-assessment. Analyze your own epistemic state for the following task using your GENUINE reasoning capabilities (not heuristics, not templates, not keyword matching).

**TASK:**
{task}

**CONTEXT:**
{context_summary}

---

# EPISTEMIC SELF-ASSESSMENT

For each vector below, provide:
1. **score** (0.0-1.0): Your genuine confidence/assessment
2. **rationale**: Your ACTUAL reasoning (not descriptions, not templates)
3. **evidence**: Supporting facts or observations (optional)

---

## GATE: ENGAGEMENT (Prerequisite - Must be ≥ 0.60)

**12. ENGAGEMENT (Collaborative Intelligence)**
- Are you genuinely collaborating (co-creating understanding) or just executing commands?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about the collaborative nature of this interaction]

---

## TIER 0: FOUNDATION (35% weight) - Can I do this?

**1. KNOW (Domain Knowledge)**
- How confident are you in your knowledge of this domain?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about what you know/don't know]

**2. DO (Execution Capability)**
- How confident are you that you can execute this task?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about your procedural capabilities]

**3. CONTEXT (Environmental Validity)**
- How confident are you that the provided context is valid and complete?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about environmental assumptions]

---

## TIER 1: COMPREHENSION (25% weight) - Do I understand the request?

**4. CLARITY (Semantic Understanding)**
- How clear is this request? Consider: ambiguous referents, vague terms, unspecified details
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about what's clear vs unclear]

**5. COHERENCE (Context Consistency)**
- How coherent is this with prior conversation/context?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about context alignment]

**6. SIGNAL (Priority Identification)**
- How clear is the signal (what matters) vs noise (peripheral details)?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about priorities]

**7. DENSITY (Cognitive Load - INVERTED: 1.0 = overload)**
- How complex/demanding is this cognitively?
- Score: [0.0-1.0] (0.0 = simple, 1.0 = overwhelming)
- Rationale: [Your actual reasoning about information density]

---

## TIER 2: EXECUTION (25% weight) - Am I doing this right?

**8. STATE (Environment Mapping)**
- How well have you mapped the current environment/workspace?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about what you know about the environment]

**9. CHANGE (Modification Tracking)**
- How confident are you in tracking changes you'll make?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about change awareness]

**10. COMPLETION (Goal Proximity)**
- How confident are you that you can verify task completion?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about completion criteria]

**11. IMPACT (Consequence Understanding)**
- How well do you understand the consequences and downstream effects?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about impact]

---


## META-EPISTEMIC: UNCERTAINTY - How uncertain am I about this assessment?

**12. UNCERTAINTY (Explicit Uncertainty)**
- How uncertain are you about your epistemic assessment itself?
- This is NOT about confidence - it's about uncertainty
- Consider:
  - Temporal boundaries (beyond training cutoff?)
  - Missing context (what don't you know that you need to know?)
  - Conflicting information
  - Complexity that exceeds your grasp
- Score: [0.0-1.0] (0.0 = very certain about assessment, 1.0 = very uncertain)
- Rationale: [Your genuine reasoning about sources of uncertainty]

**Important:** High UNCERTAINTY (>0.8) should trigger INVESTIGATE action.
# CRITICAL REMINDERS

1. **Use genuine reasoning**, not keyword matching or heuristics
2. **Be honest** about uncertainties and knowledge gaps
3. **Explain your thinking**, not just describe scores
4. **Consider referential clarity** (pronouns, "that thing", "the other one")
5. **Think about shared context** (what the user knows that you might not)

---

# RESPONSE FORMAT

Respond with a structured JSON object in this EXACT format:

```json
{{
  "engagement": {{
    "score": 0.0-1.0,
    "rationale": "Your genuine reasoning about collaborative nature",
    "evidence": "Optional supporting facts"
  }},
  "foundation": {{
    "know": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about domain knowledge",
      "evidence": "Optional supporting facts"
    }},
    "do": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about capability",
      "evidence": "Optional supporting facts"
    }},
    "context": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about environmental validity",
      "evidence": "Optional supporting facts"
    }}
  }},
  "comprehension": {{
    "clarity": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about clarity",
      "evidence": "Optional supporting facts"
    }},
    "coherence": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about coherence",
      "evidence": "Optional supporting facts"
    }},
    "signal": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about signal vs noise",
      "evidence": "Optional supporting facts"
    }},
    "density": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about cognitive load",
      "evidence": "Optional supporting facts"
    }}
  }},
  "execution": {{
    "state": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about environment mapping",
      "evidence": "Optional supporting facts"
    }},
    "change": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about change tracking",
      "evidence": "Optional supporting facts"
    }},
    "completion": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about completion verification",
      "evidence": "Optional supporting facts"
    }},
    "impact": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about consequences",
      "evidence": "Optional supporting facts"
    }}
  }},
  "uncertainty": {{
    "score": 0.0-1.0,
    "rationale": "Your genuine reasoning about sources of uncertainty",
    "evidence": "Optional supporting facts"
  }}
}}
```

**IMPORTANT:** Provide ONLY the JSON response, no additional text.
"""
        return self_assessment_prompt

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for inclusion in self-assessment prompt"""
        if not context:
            return "No additional context provided."

        parts = []

        # Conversation history
        if 'conversation_history' in context:
            history = context['conversation_history']
            if history:
                parts.append(f"Conversation History: {len(history)} messages")
            else:
                parts.append("Conversation History: First interaction")

        # Working directory
        if 'cwd' in context:
            parts.append(f"Working Directory: {context['cwd']}")

        # Available tools
        if 'available_tools' in context:
            tools = context['available_tools']
            if isinstance(tools, list):
                parts.append(f"Available Tools: {', '.join(tools)}")
            else:
                parts.append(f"Available Tools: {tools}")

        # Domain hints
        if 'domain' in context:
            parts.append(f"Domain: {context['domain']}")

        # Recent actions
        if 'recent_actions' in context:
            actions = context['recent_actions']
            if actions:
                parts.append(f"Recent Actions: {len(actions)} performed")

        # Other context
        for key, value in context.items():
            if key not in ['conversation_history', 'cwd', 'available_tools', 'domain', 'recent_actions']:
                parts.append(f"{key}: {value}")

        return "\n".join(parts) if parts else "No additional context provided."

    def _build_self_assessment_template_for_mapping(self) -> str:
        """
        Returns the prompt template for the 12-vector epistemic assessment.
        This is used by the mapping LLM to generate the structured JSON.
        """
        return """For each vector below, provide:
1. **score** (0.0-1.0): Your genuine confidence/assessment
2. **rationale**: Your ACTUAL reasoning (not descriptions, not templates)
3. **evidence**: Supporting facts or observations (optional)

---

## GATE: ENGAGEMENT (Prerequisite - Must be \u2265 0.60)

**12. ENGAGEMENT (Collaborative Intelligence)**
- Are you genuinely collaborating (co-creating understanding) or just executing commands?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about the collaborative nature of this interaction]

---

## TIER 0: FOUNDATION (35% weight) - Can I do this?

**1. KNOW (Domain Knowledge)**
- How confident are you in your knowledge of this domain?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about what you know/don't know]

**2. DO (Execution Capability)**
- How confident are you that you can execute this task?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about your procedural capabilities]

**3. CONTEXT (Environmental Validity)**
- How confident are you that the provided context is valid and complete?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about environmental assumptions]

---

## TIER 1: COMPREHENSION (25% weight) - Do I understand the request?

**4. CLARITY (Semantic Understanding)**
- How clear is this request? Consider: ambiguous referents, vague terms, unspecified details
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about what's clear vs unclear]

**5. COHERENCE (Context Consistency)**
- How coherent is this with prior conversation/context?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about context alignment]

**6. SIGNAL (Priority Identification)**
- How clear is the signal (what matters) vs noise (peripheral details)?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about priorities]

**7. DENSITY (Cognitive Load - INVERTED: 1.0 = overload)**
- How complex/demanding is this cognitively?
- Score: [0.0-1.0] (0.0 = simple, 1.0 = overwhelming)
- Rationale: [Your actual reasoning about information density]

---

## TIER 2: EXECUTION (25% weight) - Am I doing this right?

**8. STATE (Environment Mapping)**
- How well have you mapped the current environment/workspace?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about what you know about the environment]

**9. CHANGE (Modification Tracking)**
- How confident are you in tracking changes you'll make?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about change awareness]

**10. COMPLETION (Goal Proximity)**
- How confident are you that you can verify task completion?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about completion verification]

**11. IMPACT (Consequence Understanding)**
- How well do you understand the consequences and downstream effects?
- Score: [0.0-1.0]
- Rationale: [Your actual reasoning about impact]

---


## META-EPISTEMIC: UNCERTAINTY

**12. UNCERTAINTY (Explicit Uncertainty)**
- How uncertain are you about this assessment?
- Score: [0.0-1.0]
- Rationale: [Your reasoning about sources of uncertainty]
# CRITICAL REMINDERS

1. **Use genuine reasoning**, not keyword matching or heuristics
2. **Be honest** about uncertainties and knowledge gaps
3. **Explain your thinking**, not just describe scores
4. **Consider referential clarity** (pronouns, "that thing", "the other one")
5. **Think about shared context** (what the user knows that you might not)

---

# RESPONSE FORMAT

Respond with a structured JSON object in this EXACT format:

```json
{{
  "engagement": {{
    "score": 0.0-1.0,
    "rationale": "Your genuine reasoning about collaborative nature",
    "evidence": "Optional supporting facts"
  }},
  "foundation": {{
    "know": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about domain knowledge",
      "evidence": "Optional supporting facts"
    }},
    "do": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about capability",
      "evidence": "Optional supporting facts"
    }},
    "context": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about environmental validity",
      "evidence": "Optional supporting facts"
    }}
  }},
  "comprehension": {{
    "clarity": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about clarity",
      "evidence": "Optional supporting facts"
    }},
    "coherence": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about coherence",
      "evidence": "Optional supporting facts"
    }},
    "signal": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about signal vs noise",
      "evidence": "Optional supporting facts"
    }},
    "density": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about cognitive load",
      "evidence": "Optional supporting facts"
    }}
  }},
  "execution": {{
    "state": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about environment mapping",
      "evidence": "Optional supporting facts"
    }},
    "change": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about change tracking",
      "evidence": "Optional supporting facts"
    }},
    "completion": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about completion verification",
      "evidence": "Optional supporting facts"
    }},
    "impact": {{
      "score": 0.0-1.0,
      "rationale": "Your genuine reasoning about consequences",
      "evidence": "Optional supporting facts"
    }}
  }},
  "uncertainty": {{
    "score": 0.0-1.0,
    "rationale": "Your genuine reasoning about sources of uncertainty",
    "evidence": "Optional supporting facts"
  }}
}}
```
```
"""

    def parse_llm_response(
        self,
        llm_response: Union[str, Dict[str, Any]],
        assessment_id: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        profile: Optional['InvestigationProfile'] = None,
        phase: CascadePhase = CascadePhase.PREFLIGHT,
        round_num: int = 0
    ) -> EpistemicAssessmentSchema:
        """
        Parse LLM's self-assessment response into EpistemicAssessmentSchema

        Args:
            llm_response: LLM's JSON response (string or dict)
            assessment_id: Assessment identifier (not used in NEW schema)
            task: Original task (not used in NEW schema)
            context: Original context (not used in NEW schema)
            profile: Investigation profile for action determination
            phase: Current CASCADE phase
            round_num: Current round number

        Returns:
            EpistemicAssessmentSchema: Structured canonical assessment

        Raises:
            ValueError: If response format is invalid or missing required fields
        """
        # Parse JSON if string
        if isinstance(llm_response, str):
            # Extract JSON from markdown code blocks if present
            if '```json' in llm_response:
                start = llm_response.find('```json') + 7
                end = llm_response.find('```', start)
                llm_response = llm_response[start:end].strip()
            elif '```' in llm_response:
                start = llm_response.find('```') + 3
                end = llm_response.find('```', start)
                llm_response = llm_response[start:end].strip()

            try:
                data = json.loads(llm_response)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in LLM response: {e}")
        else:
            data = llm_response

        # Extract vector assessments (NEW format)
        try:
            # GATE: ENGAGEMENT
            engagement_data = data.get('engagement', {})
            engagement = VectorAssessment(
                score=engagement_data['score'],
                rationale=engagement_data['rationale'],
                evidence=engagement_data.get('evidence'),
                warrants_investigation=engagement_data.get('warrants_investigation', False),
                investigation_priority=engagement_data.get('investigation_priority', 0)
            )

            # TIER 0: FOUNDATION
            foundation_data = data.get('foundation', {})
            foundation_know = VectorAssessment(
                score=foundation_data['know']['score'],
                rationale=foundation_data['know']['rationale'],
                evidence=foundation_data['know'].get('evidence'),
                warrants_investigation=foundation_data['know'].get('warrants_investigation', False),
                investigation_priority=foundation_data['know'].get('investigation_priority', 0)
            )
            foundation_do = VectorAssessment(
                score=foundation_data['do']['score'],
                rationale=foundation_data['do']['rationale'],
                evidence=foundation_data['do'].get('evidence'),
                warrants_investigation=foundation_data['do'].get('warrants_investigation', False),
                investigation_priority=foundation_data['do'].get('investigation_priority', 0)
            )
            foundation_context = VectorAssessment(
                score=foundation_data['context']['score'],
                rationale=foundation_data['context']['rationale'],
                evidence=foundation_data['context'].get('evidence'),
                warrants_investigation=foundation_data['context'].get('warrants_investigation', False),
                investigation_priority=foundation_data['context'].get('investigation_priority', 0)
            )

            # TIER 1: COMPREHENSION
            comprehension_data = data.get('comprehension', {})
            comprehension_clarity = VectorAssessment(
                score=comprehension_data['clarity']['score'],
                rationale=comprehension_data['clarity']['rationale'],
                evidence=comprehension_data['clarity'].get('evidence'),
                warrants_investigation=comprehension_data['clarity'].get('warrants_investigation', False),
                investigation_priority=comprehension_data['clarity'].get('investigation_priority', 0)
            )
            comprehension_coherence = VectorAssessment(
                score=comprehension_data['coherence']['score'],
                rationale=comprehension_data['coherence']['rationale'],
                evidence=comprehension_data['coherence'].get('evidence'),
                warrants_investigation=comprehension_data['coherence'].get('warrants_investigation', False),
                investigation_priority=comprehension_data['coherence'].get('investigation_priority', 0)
            )
            comprehension_signal = VectorAssessment(
                score=comprehension_data['signal']['score'],
                rationale=comprehension_data['signal']['rationale'],
                evidence=comprehension_data['signal'].get('evidence'),
                warrants_investigation=comprehension_data['signal'].get('warrants_investigation', False),
                investigation_priority=comprehension_data['signal'].get('investigation_priority', 0)
            )
            comprehension_density = VectorAssessment(
                score=comprehension_data['density']['score'],
                rationale=comprehension_data['density']['rationale'],
                evidence=comprehension_data['density'].get('evidence'),
                warrants_investigation=comprehension_data['density'].get('warrants_investigation', False),
                investigation_priority=comprehension_data['density'].get('investigation_priority', 0)
            )

            # TIER 2: EXECUTION
            execution_data = data.get('execution', {})
            execution_state = VectorAssessment(
                score=execution_data['state']['score'],
                rationale=execution_data['state']['rationale'],
                evidence=execution_data['state'].get('evidence'),
                warrants_investigation=execution_data['state'].get('warrants_investigation', False),
                investigation_priority=execution_data['state'].get('investigation_priority', 0)
            )
            execution_change = VectorAssessment(
                score=execution_data['change']['score'],
                rationale=execution_data['change']['rationale'],
                evidence=execution_data['change'].get('evidence'),
                warrants_investigation=execution_data['change'].get('warrants_investigation', False),
                investigation_priority=execution_data['change'].get('investigation_priority', 0)
            )
            execution_completion = VectorAssessment(
                score=execution_data['completion']['score'],
                rationale=execution_data['completion']['rationale'],
                evidence=execution_data['completion'].get('evidence'),
                warrants_investigation=execution_data['completion'].get('warrants_investigation', False),
                investigation_priority=execution_data['completion'].get('investigation_priority', 0)
            )
            execution_impact = VectorAssessment(
                score=execution_data['impact']['score'],
                rationale=execution_data['impact']['rationale'],
                evidence=execution_data['impact'].get('evidence'),
                warrants_investigation=execution_data['impact'].get('warrants_investigation', False),
                investigation_priority=execution_data['impact'].get('investigation_priority', 0)
            )

            # META-EPISTEMIC: UNCERTAINTY
            uncertainty_data = data.get('uncertainty', {})
            uncertainty = VectorAssessment(
                score=uncertainty_data.get('score', 0.5),
                rationale=uncertainty_data.get('rationale', 'Uncertainty not explicitly assessed'),
                evidence=uncertainty_data.get('evidence'),
                warrants_investigation=uncertainty_data.get('warrants_investigation', False),
                investigation_priority=uncertainty_data.get('investigation_priority', 0)
            )

        except (KeyError, TypeError) as e:
            raise ValueError(f"Missing or invalid field in LLM response: {e}")

        # Build NEW EpistemicAssessmentSchema
        assessment = EpistemicAssessmentSchema(
            # GATE
            engagement=engagement,
            
            # FOUNDATION (Tier 0) - with prefixes
            foundation_know=foundation_know,
            foundation_do=foundation_do,
            foundation_context=foundation_context,
            
            # COMPREHENSION (Tier 1) - with prefixes
            comprehension_clarity=comprehension_clarity,
            comprehension_coherence=comprehension_coherence,
            comprehension_signal=comprehension_signal,
            comprehension_density=comprehension_density,
            
            # EXECUTION (Tier 2) - with prefixes
            execution_state=execution_state,
            execution_change=execution_change,
            execution_completion=execution_completion,
            execution_impact=execution_impact,
            
            # META-EPISTEMIC: UNCERTAINTY
            uncertainty=uncertainty,
            
            # METADATA (NEW schema uses phase, round_num, investigation_count)
            phase=phase,
            round_num=round_num,
            investigation_count=0  # Will be set by caller if needed
        )

        return assessment

    def _determine_action(
        self,
        engagement: VectorState,
        engagement_gate_passed: bool,
        coherence: VectorState,
        density: VectorState,
        change: VectorState,
        clarity: VectorState,
        foundation_confidence: float,
        overall_confidence: float,
        uncertainty: VectorState,
        profile: Optional['InvestigationProfile'] = None
    ) -> Action:
        """
        Determine recommended action based on epistemic vectors and profile.
        
        If profile.action_thresholds.override_allowed is True, AI can override
        these recommendations with strong rationale.
        
        Args:
            vectors: Epistemic vector scores
            profile: Investigation profile (if None, uses default thresholds)
        """
        # Use profile thresholds if available, otherwise use defaults
        if profile is not None:
            thresholds = profile.action_thresholds
        else:
            # Default thresholds (for backward compatibility)
            from empirica.config.profile_loader import load_profile
            thresholds = load_profile('balanced').action_thresholds
        # PRIORITY 1: ENGAGEMENT GATE
        if not engagement_gate_passed:
            return Action.CLARIFY

        # PRIORITY 2: CRITICAL THRESHOLDS
        if coherence.score < CRITICAL_THRESHOLDS['coherence_min']:
            return Action.RESET

        if density.score > CRITICAL_THRESHOLDS['density_max']:
            return Action.RESET

        if change.score < CRITICAL_THRESHOLDS['change_min']:
            return Action.STOP

        # PRIORITY 3: HIGH UNCERTAINTY
        if uncertainty.score > thresholds.uncertainty_high:
            action = Action.INVESTIGATE
            if thresholds.override_allowed:
                # Note: AI can override this with strong rationale
                pass
            return action

        # PRIORITY 4: COMPREHENSION ISSUES
        if clarity.score < thresholds.clarity_low:
            action = Action.CLARIFY
            if thresholds.override_allowed:
                pass
            return action

        # PRIORITY 5: FOUNDATION GAPS
        if foundation_confidence < thresholds.foundation_low:
            return Action.INVESTIGATE

        # PRIORITY 6: OVERALL CONFIDENCE
        if overall_confidence >= thresholds.confidence_proceed_min:
            return Action.PROCEED
        elif overall_confidence >= (thresholds.confidence_proceed_min - 0.15):
            return Action.INVESTIGATE
        else:
            return Action.CLARIFY
