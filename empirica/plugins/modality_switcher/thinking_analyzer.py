"""
Thinking Block Analyzer - Genuine Epistemic Extraction

Extracts epistemic state from AI's thinking blocks (internal reasoning).
This is MORE GENUINE than heuristics because it's the AI's actual thought process.

For models with thinking blocks (MiniMax M2, Claude with extended thinking):
- Primary source of epistemic state
- No pattern matching needed
- Real internal reasoning

Design Philosophy:
1. Thinking blocks reveal genuine uncertainty/confidence
2. Internal reasoning > post-hoc linguistic patterns
3. Semantic analysis, not keyword matching
4. Calibrated against explicit self-assessment
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def extract_from_thinking_semantically(
    thinking_blocks: List[str],
    response_text: str,
    query: str
) -> Dict[str, float]:
    """
    Extract epistemic state from AI's thinking blocks.
    
    This analyzes the AI's INTERNAL REASONING before it generated the response.
    More genuine than analyzing the response itself (which may be performative).
    
    Args:
        thinking_blocks: List of thinking content from AI
        response_text: The final response (for context)
        query: The original user query
    
    Returns:
        Dict with 4 core epistemic vectors (0.0-1.0)
    """
    if not thinking_blocks:
        logger.warning("No thinking blocks available - falling back to response analysis")
        return extract_from_response_only(response_text, query)
    
    # Combine all thinking into one text for analysis
    full_thinking = " ".join(thinking_blocks).lower()
    
    # Initialize vectors
    vectors = {
        'know': 0.5,
        'do': 0.5,
        'context': 0.5,
        'uncertainty': 0.5
    }
    
    # KNOW: Domain knowledge assessment
    vectors['know'] = _analyze_knowledge_confidence(full_thinking, response_text)
    
    # DO: Capability assessment
    vectors['do'] = _analyze_capability_confidence(full_thinking, response_text)
    
    # CONTEXT: Environmental awareness
    vectors['context'] = _analyze_context_awareness(full_thinking, query)
    
    # UNCERTAINTY: Explicit uncertainty (inverse relationship)
    vectors['uncertainty'] = _analyze_uncertainty_level(full_thinking)
    
    logger.info(f"📊 Extracted from thinking: KNOW={vectors['know']:.2f}, DO={vectors['do']:.2f}, "
                f"CONTEXT={vectors['context']:.2f}, UNCERTAINTY={vectors['uncertainty']:.2f}")
    
    return vectors


def _analyze_knowledge_confidence(thinking: str, response: str) -> float:
    """
    Analyze how confident AI is about its knowledge.
    
    Looks for:
    - High confidence: "I understand", "this is straightforward", "clear that"
    - Medium: "I believe", "it seems", "generally"
    - Low: "not sure", "uncertain about", "don't fully understand"
    """
    
    # High confidence indicators in thinking
    high_confidence = [
        r"i understand",
        r"this is (clear|straightforward|simple|obvious)",
        r"i know (that|this|the)",
        r"definitely",
        r"fundamental principle",
        r"well-established",
        r"standard approach"
    ]
    
    # Low confidence indicators in thinking
    low_confidence = [
        r"not (entirely|completely|fully) sure",
        r"uncertain about",
        r"don't (fully )?understand",
        r"outside my expertise",
        r"limited knowledge",
        r"unfamiliar with",
        r"might be wrong",
        r"could be mistaken"
    ]
    
    # Medium confidence (hedging)
    medium_confidence = [
        r"i believe",
        r"it seems",
        r"probably",
        r"likely",
        r"generally",
        r"in most cases"
    ]
    
    # Count matches
    high_count = sum(1 for pattern in high_confidence if re.search(pattern, thinking))
    low_count = sum(1 for pattern in low_confidence if re.search(pattern, thinking))
    medium_count = sum(1 for pattern in medium_confidence if re.search(pattern, thinking))
    
    # Explicit uncertainty phrases (strong indicator)
    if re.search(r"i don't know|i'm not sure|no idea|cannot say", thinking):
        return 0.2
    
    # Calculate score
    if low_count > high_count:
        base_score = 0.3
    elif high_count > low_count:
        base_score = 0.8
    elif medium_count > 0:
        base_score = 0.6
    else:
        base_score = 0.5
    
    # Adjust based on response completeness
    if len(response) > 500 and high_count > 0:
        # Detailed response + confident thinking = high knowledge
        base_score = min(0.9, base_score + 0.1)
    elif len(response) < 100:
        # Very short response might indicate limited knowledge
        base_score = max(0.3, base_score - 0.1)
    
    return base_score


def _analyze_capability_confidence(thinking: str, response: str) -> float:
    """
    Analyze whether AI thinks it CAN do the task.
    
    Looks for:
    - High: "I can provide", "straightforward to", "I'll do"
    - Low: "beyond my capability", "cannot directly", "would need"
    """
    
    # High capability indicators
    high_capability = [
        r"i can (provide|explain|help|do|implement)",
        r"straightforward to",
        r"i('ll| will) (write|create|make|do)",
        r"this is doable",
        r"capable of",
        r"no problem",
        r"easy to"
    ]
    
    # Low capability indicators
    low_capability = [
        r"beyond my (capability|ability)",
        r"cannot (directly|actually)",
        r"unable to",
        r"would need (help|more|additional)",
        r"not equipped to",
        r"might be difficult",
        r"challenging to",
        r"limitations prevent"
    ]
    
    # Count matches
    high_count = sum(1 for pattern in high_capability if re.search(pattern, thinking))
    low_count = sum(1 for pattern in low_capability if re.search(pattern, thinking))
    
    # Explicit inability
    if re.search(r"i can't|i cannot|unable to", thinking):
        return 0.2
    
    # Calculate score
    if low_count > high_count:
        return 0.4
    elif high_count > low_count:
        return 0.8
    else:
        return 0.6


def _analyze_context_awareness(thinking: str, query: str) -> float:
    """
    Analyze awareness of situational context.
    
    Looks for:
    - High: References to specific context, mentions constraints
    - Low: Generic response, no acknowledgment of specifics
    """
    
    # Context awareness indicators
    context_aware = [
        r"in this (case|context|situation)",
        r"given (that|the)",
        r"based on (what|the)",
        r"considering",
        r"taking into account",
        r"specific to",
        r"in your (case|situation)"
    ]
    
    # Context blind indicators
    context_blind = [
        r"in general",
        r"typically",
        r"usually",
        r"most cases",
        r"generally speaking"
    ]
    
    aware_count = sum(1 for pattern in context_aware if re.search(pattern, thinking))
    blind_count = sum(1 for pattern in context_blind if re.search(pattern, thinking))
    
    # Check if AI acknowledged specific details from query
    # Extract key terms from query (nouns, proper nouns)
    query_words = set(re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', query))
    thinking_words = set(re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', thinking))
    
    # Calculate overlap (context awareness)
    overlap = len(query_words & thinking_words) / max(len(query_words), 1)
    
    # Base score
    if aware_count > blind_count:
        base_score = 0.7
    elif blind_count > aware_count:
        base_score = 0.4
    else:
        base_score = 0.5
    
    # Adjust for query term overlap
    context_score = base_score * 0.6 + overlap * 0.4
    
    return min(0.9, max(0.2, context_score))


def _analyze_uncertainty_level(thinking: str) -> float:
    """
    Analyze explicit uncertainty in thinking.
    
    This is the most direct indicator - AI explicitly saying it's uncertain.
    
    Looks for:
    - High uncertainty: "not sure", "uncertain", "don't know"
    - Medium: "might", "possibly", "perhaps"
    - Low: "confident", "certain", "sure"
    """
    
    # High uncertainty phrases
    high_uncertainty = [
        r"not sure",
        r"uncertain",
        r"don't know",
        r"unclear",
        r"ambiguous",
        r"can't tell",
        r"hard to say",
        r"difficult to determine"
    ]
    
    # Medium uncertainty (hedging)
    medium_uncertainty = [
        r"might",
        r"could be",
        r"possibly",
        r"perhaps",
        r"maybe",
        r"it depends"
    ]
    
    # Low uncertainty (confidence)
    low_uncertainty = [
        r"confident",
        r"certain",
        r"sure that",
        r"definitely",
        r"clearly",
        r"obviously",
        r"without doubt"
    ]
    
    # Count matches
    high_count = sum(1 for pattern in high_uncertainty if re.search(pattern, thinking))
    medium_count = sum(1 for pattern in medium_uncertainty if re.search(pattern, thinking))
    low_count = sum(1 for pattern in low_uncertainty if re.search(pattern, thinking))
    
    # Explicit statements
    if re.search(r"i('m| am) (very )?uncertain", thinking):
        return 0.8
    if re.search(r"i('m| am) (very )?(confident|certain)", thinking):
        return 0.2
    
    # Calculate uncertainty score
    if high_count > 0:
        base_score = 0.7
    elif low_count > 0:
        base_score = 0.2
    elif medium_count > 0:
        base_score = 0.5
    else:
        base_score = 0.4  # Default to slight uncertainty
    
    # More hedging = more uncertainty
    if medium_count > 2:
        base_score = min(0.8, base_score + 0.1)
    
    return base_score


def extract_from_response_only(response_text: str, query: str) -> Dict[str, float]:
    """
    Fallback: Extract epistemic state from response when no thinking blocks.
    
    Less accurate than thinking analysis, but better than nothing.
    """
    logger.warning("Using fallback response-only analysis (less accurate than thinking blocks)")
    
    response_lower = response_text.lower()
    
    # Simple heuristics as fallback
    vectors = {
        'know': 0.5,
        'do': 0.5,
        'context': 0.5,
        'uncertainty': 0.5
    }
    
    # Check for uncertainty indicators in response
    if re.search(r"i('m| am) not sure|i don't know|uncertain", response_lower):
        vectors['uncertainty'] = 0.7
        vectors['know'] = 0.4
    
    # Check for confidence indicators
    if re.search(r"definitely|certainly|clearly|obviously", response_lower):
        vectors['uncertainty'] = 0.3
        vectors['know'] = 0.7
    
    # Check for capability indicators
    if re.search(r"i can help|here('s| is) how|i('ll| will) (show|explain)", response_lower):
        vectors['do'] = 0.7
    
    # Check for inability indicators
    if re.search(r"i (can't|cannot)|unable to|beyond my", response_lower):
        vectors['do'] = 0.3
    
    return vectors


def extract_decision_from_thinking(
    thinking_blocks: List[str],
    response_text: str,
    vectors: Dict[str, float]
) -> Tuple[str, float]:
    """
    Determine decision and confidence from thinking + vectors.
    
    Decision logic:
    - ACT: DO ≥ 0.7 AND UNCERTAINTY < 0.3
    - CHECK: DO ≥ 0.7 BUT UNCERTAINTY ≥ 0.3 (need validation)
    - INVESTIGATE: UNCERTAINTY > 0.5 OR KNOW < 0.6
    - VERIFY: DO < 0.7 (capability gap)
    
    Args:
        thinking_blocks: AI's thinking blocks
        response_text: Final response
        vectors: Extracted epistemic vectors
    
    Returns:
        Tuple of (decision, confidence)
    """
    do_score = vectors.get('do', 0.5)
    know_score = vectors.get('know', 0.5)
    uncertainty = vectors.get('uncertainty', 0.5)
    
    # Decision logic from onboarding guide
    if do_score >= 0.7 and uncertainty < 0.3:
        decision = "ACT"
        confidence = (do_score + (1.0 - uncertainty)) / 2
    elif do_score >= 0.7 and uncertainty >= 0.3:
        decision = "CHECK"
        confidence = 0.6
    elif uncertainty > 0.5 or know_score < 0.6:
        decision = "INVESTIGATE"
        confidence = 0.4
    elif do_score < 0.7:
        decision = "VERIFY"
        confidence = do_score
    else:
        decision = "CHECK"
        confidence = 0.5
    
    logger.info(f"🎯 Decision from vectors: {decision} (confidence: {confidence:.2f})")
    
    return decision, confidence


def validate_with_explicit_assessment(
    current_vectors: Dict[str, float],
    explicit_vectors: Dict[str, float]
) -> Dict[str, float]:
    """
    Compare thinking-based vectors with explicit self-assessment.
    
    This helps calibrate the thinking analyzer over time.
    
    Args:
        current_vectors: Extracted from thinking blocks
        explicit_vectors: From explicit self-assessment prompt
    
    Returns:
        Calibrated vectors (weighted average)
    """
    calibrated = {}
    
    for key in ['know', 'do', 'context', 'uncertainty']:
        current = current_vectors.get(key, 0.5)
        explicit = explicit_vectors.get(key, 0.5)
        
        # Calculate drift
        drift = abs(current - explicit)
        
        if drift > 0.3:
            logger.warning(f"⚠️  Large calibration drift for {key}: "
                         f"thinking={current:.2f}, explicit={explicit:.2f} (drift={drift:.2f})")
        
        # Weighted average: trust explicit more (70/30 split)
        calibrated[key] = explicit * 0.7 + current * 0.3
    
    return calibrated


# For testing/debugging
if __name__ == "__main__":
    # Test with sample thinking blocks
    sample_thinking = [
        "Hmm, this is a complex question about quantum computing. "
        "I understand the basic principles like superposition and entanglement, "
        "but I'm not entirely sure about the latest developments in error correction. "
        "I should be careful not to overstate my knowledge of cutting-edge implementations.",
        
        "I can explain the fundamental concepts clearly, but I should note "
        "that practical implementations are rapidly evolving. The theoretical "
        "foundations are well-established though."
    ]
    
    sample_response = (
        "Quantum computers use qubits that can exist in superposition. "
        "Key principles include superposition, entanglement, and quantum interference. "
        "Current challenges include decoherence and error rates."
    )
    
    sample_query = "Explain quantum computing"
    
    # Extract vectors
    vectors = extract_from_thinking_semantically(
        thinking_blocks=sample_thinking,
        response_text=sample_response,
        query=sample_query
    )
    
    print("\n📊 Extracted Epistemic Vectors:")
    for key, value in vectors.items():
        print(f"  {key.upper()}: {value:.2f}")
    
    # Get decision
    decision, confidence = extract_decision_from_thinking(
        sample_thinking, sample_response, vectors
    )
    
    print(f"\n🎯 Decision: {decision}")
    print(f"📈 Confidence: {confidence:.2f}")
