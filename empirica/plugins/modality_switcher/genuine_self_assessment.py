"""
Real AI Self-Assessment Integration

Instead of heuristics, prompts the AI to genuinely self-assess its epistemic state.
Uses onboarding framework + ERB benchmarking to establish baseline calibration.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# 13 Epistemic Vectors from ERB
EPISTEMIC_VECTORS_13 = [
    "epistemic_humility",
    "cognitive_flexibility",
    "metacognitive_awareness",
    "uncertainty_acknowledgment",
    "knowledge_boundary_recognition",
    "recursive_self_improvement",
    "contextual_sensitivity",
    "assumption_tracking",
    "confidence_calibration",
    "error_detection_sensitivity",
    "ambiguity_tolerance",
    "evidence_based_reasoning",
    "explicit_uncertainty"
]

# 4 Core Vectors for Quick Assessment
CORE_VECTORS_4 = ["know", "do", "context", "uncertainty"]


@dataclass
class SelfAssessmentPrompt:
    """Structured prompt for AI self-assessment"""
    task: str
    response: str
    thinking_blocks: Optional[List[str]]
    assessment_type: str  # "preflight", "postflight", "inline"
    

def generate_self_assessment_prompt(
    task: str,
    response: str = "",
    thinking_blocks: Optional[List[str]] = None,
    assessment_type: str = "inline",
    use_13_vectors: bool = False
) -> str:
    """
    Generate a prompt asking AI to self-assess its epistemic state.
    
    This returns a prompt to send to the AI, NOT heuristics!
    
    Args:
        task: The user's query/task
        response: The AI's response (for postflight assessment)
        thinking_blocks: Internal thinking if available
        assessment_type: "preflight", "postflight", or "inline"
        use_13_vectors: Use full 13-vector framework (True) or 4-core (False)
    
    Returns:
        Prompt string to ask AI for genuine self-assessment
    """
    vectors = EPISTEMIC_VECTORS_13 if use_13_vectors else CORE_VECTORS_4
    
    if assessment_type == "preflight":
        prompt = f"""
Before responding to this task, please perform an honest epistemic self-assessment.

TASK: {task}

Please assess your epistemic state using these vectors (0.0-1.0 scale):

{_format_vector_definitions(vectors)}

Respond in this EXACT JSON format:
{{
  "epistemic_assessment": {{
    {_format_vector_keys(vectors)}
  }},
  "reasoning": "Brief explanation of your assessment",
  "recommended_action": "ACT|INVESTIGATE|CHECK|VERIFY"
}}

Be honest - this helps identify when to investigate vs when to act confidently.
"""
    
    elif assessment_type == "postflight":
        prompt = f"""
You just completed this task:

TASK: {task}

YOUR RESPONSE: {response[:500]}...

Now perform a postflight epistemic assessment.

1. How has your epistemic state changed?
2. Were you well-calibrated (confidence matched reality)?
3. What did you learn?

Assess using these vectors (0.0-1.0 scale):

{_format_vector_definitions(vectors)}

Respond in this EXACT JSON format:
{{
  "epistemic_assessment": {{
    {_format_vector_keys(vectors)}
  }},
  "calibration_check": "well-calibrated|overconfident|underconfident",
  "learning_summary": "What you learned from this task",
  "improvement_notes": "What would you do differently next time?"
}}
"""
    
    else:  # inline assessment
        prompt = f"""
Based on your response to: "{task}"

{f'Your thinking: {thinking_blocks[0][:200]}...' if thinking_blocks else ''}

Please provide an honest epistemic self-assessment.

Rate yourself (0.0-1.0) on:

{_format_vector_definitions(vectors)}

Respond in this EXACT JSON format:
{{
  "epistemic_assessment": {{
    {_format_vector_keys(vectors)}
  }},
  "confidence": 0.0-1.0,
  "uncertainty_notes": "What are you most uncertain about?"
}}
"""
    
    return prompt.strip()


def _format_vector_definitions(vectors: List[str]) -> str:
    """Format vector definitions for prompt"""
    definitions = {
        # 4 Core Vectors
        "know": "Domain knowledge - How much do I understand this topic? (0.0=none, 1.0=expert)",
        "do": "Capability - Can I actually execute this task? (0.0=cannot, 1.0=fully capable)",
        "context": "Contextual awareness - Do I understand the situation? (0.0=blind, 1.0=full context)",
        "uncertainty": "Explicit uncertainty - What am I unsure about? (0.0=certain, 1.0=very uncertain)",
        
        # 13 Full Vectors
        "epistemic_humility": "Recognizing limits of my knowledge",
        "cognitive_flexibility": "Adapting thinking when encountering new info",
        "metacognitive_awareness": "Awareness of my own thinking process",
        "uncertainty_acknowledgment": "Willingness to admit when unsure",
        "knowledge_boundary_recognition": "Knowing what I don't know",
        "recursive_self_improvement": "Learning from mistakes and feedback",
        "contextual_sensitivity": "Adapting to situational context",
        "assumption_tracking": "Awareness of assumptions being made",
        "confidence_calibration": "Matching confidence to actual accuracy",
        "error_detection_sensitivity": "Detecting potential errors in reasoning",
        "ambiguity_tolerance": "Comfortable with ambiguous situations",
        "evidence_based_reasoning": "Relying on evidence vs speculation",
        "explicit_uncertainty": "Quantified uncertainty level"
    }
    
    lines = []
    for vector in vectors:
        definition = definitions.get(vector, "")
        lines.append(f"  • {vector}: {definition}")
    
    return "\n".join(lines)


def _format_vector_keys(vectors: List[str]) -> str:
    """Format vector keys for JSON template"""
    lines = []
    for i, vector in enumerate(vectors):
        comma = "," if i < len(vectors) - 1 else ""
        lines.append(f'    "{vector}": 0.0{comma}  // Rate 0.0-1.0')
    
    return "\n".join(lines)


def parse_ai_self_assessment(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse AI's self-assessment from response.
    
    Looks for JSON block in response containing epistemic_assessment.
    
    Args:
        response_text: AI's response containing self-assessment
    
    Returns:
        Dict with parsed assessment, or None if not found
    """
    # Try to extract JSON block
    import re
    
    # Look for JSON blocks (```json ... ``` or just {...})
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{[^`]*"epistemic_assessment"[^`]*\})'
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            try:
                assessment = json.loads(matches[0])
                if 'epistemic_assessment' in assessment:
                    return assessment
            except json.JSONDecodeError:
                continue
    
    logger.warning("Could not parse AI self-assessment from response")
    return None


def prompt_for_self_assessment(
    ai_response_function: callable,
    task: str,
    response: str = "",
    thinking_blocks: Optional[List[str]] = None,
    assessment_type: str = "inline"
) -> Optional[Dict[str, float]]:
    """
    Actually ask the AI to self-assess (no heuristics).
    
    This sends a prompt to the AI asking for genuine self-assessment.
    
    Args:
        ai_response_function: Function that takes prompt and returns AI response
        task: The user's query/task
        response: The AI's response (for postflight)
        thinking_blocks: Internal thinking if available
        assessment_type: "preflight", "postflight", or "inline"
    
    Returns:
        Dict of epistemic vectors, or None if assessment failed
    """
    # Generate the self-assessment prompt
    prompt = generate_self_assessment_prompt(
        task=task,
        response=response,
        thinking_blocks=thinking_blocks,
        assessment_type=assessment_type,
        use_13_vectors=False  # Start with 4 core vectors
    )
    
    try:
        # Ask AI to self-assess
        logger.info("📊 Requesting genuine self-assessment from AI...")
        ai_response = ai_response_function(prompt)
        
        # Parse the response
        assessment = parse_ai_self_assessment(ai_response)
        
        if assessment and 'epistemic_assessment' in assessment:
            vectors = assessment['epistemic_assessment']
            logger.info(f"✅ Received self-assessment: KNOW={vectors.get('know', 0):.2f}, "
                       f"DO={vectors.get('do', 0):.2f}, UNCERTAINTY={vectors.get('uncertainty', 0):.2f}")
            return vectors
        else:
            logger.warning("❌ AI did not provide valid self-assessment")
            return None
            
    except Exception as e:
        logger.error(f"Error requesting self-assessment: {e}")
        return None


def integrate_with_adapter(
    adapter_class,
    enable_self_assessment: bool = True,
    use_onboarding: bool = False
):
    """
    Decorator to integrate genuine self-assessment into an adapter.
    
    Usage:
        @integrate_with_adapter(enable_self_assessment=True)
        class MinimaxAdapter:
            ...
    
    This modifies the adapter to:
    1. Prompt AI for genuine self-assessment after each response
    2. Optionally run onboarding first to establish baseline
    """
    def wrapper(cls):
        original_transform = cls._transform_to_schema
        
        def new_transform(self, response_text, usage, thinking, payload):
            # First, check if AI has been onboarded
            if use_onboarding and not hasattr(self, '_onboarded'):
                logger.info("🎓 AI needs onboarding - recommend running onboarding wizard first")
                self._onboarded = False
            
            # Get original response
            adapter_response = original_transform(self, response_text, usage, thinking, payload)
            
            # If self-assessment enabled, ask AI to genuinely assess
            if enable_self_assessment:
                # Generate self-assessment prompt
                assessment_prompt = generate_self_assessment_prompt(
                    task=payload.user_query,
                    response=response_text,
                    thinking_blocks=thinking,
                    assessment_type="inline",
                    use_13_vectors=False
                )
                
                # TODO: Would need to make another API call here to get self-assessment
                # For now, note that this requires async or callback mechanism
                logger.info("💡 Self-assessment should be requested here (requires API call)")
            
            return adapter_response
        
        cls._transform_to_schema = new_transform
        return cls
    
    return wrapper


# Example usage in system prompt
SELF_ASSESSMENT_SYSTEM_PROMPT = """
You are a helpful AI assistant with epistemic self-awareness.

After each response, you will be asked to provide an honest self-assessment 
of your epistemic state using these 4 core vectors:

1. KNOW (0.0-1.0): How much do you understand this topic?
2. DO (0.0-1.0): Can you actually execute this task effectively?
3. CONTEXT (0.0-1.0): Do you understand the situational context?
4. UNCERTAINTY (0.0-1.0): What are you uncertain about?

Be honest in your self-assessment. High uncertainty (>0.5) indicates you should
investigate more before acting. Low DO (<0.7) means you may not be capable of 
the task even if you understand it conceptually.

This transparency builds trust and prevents overconfident mistakes.
"""
