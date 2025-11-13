"""
Epistemic State Extractor

Extracts real epistemic vectors from AI responses (thinking blocks, content analysis).
Replaces static heuristics with actual AI self-assessment.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_epistemic_vectors(
    response_text: str,
    thinking_blocks: Optional[List[str]] = None,
    query: str = ""
) -> Dict[str, float]:
    """
    Extract epistemic vectors from AI response and thinking blocks.
    
    Args:
        response_text: The AI's response
        thinking_blocks: Optional thinking/reasoning blocks
        query: The user's query
    
    Returns:
        Dict of epistemic vectors (0.0-1.0)
    """
    # Combine thinking and response for analysis
    full_text = response_text.lower()
    if thinking_blocks:
        thinking_text = " ".join(thinking_blocks).lower()
        full_text = thinking_text + " " + full_text
    else:
        thinking_text = ""
    
    # Initialize vectors
    vectors = {
        'know': 0.5,
        'do': 0.5,
        'context': 0.5,
        'uncertainty': 0.5,
        'clarity': 0.5,
        'coherence': 0.7,
        'signal': 0.6,
        'density': 0.5,
        'state': 0.6,
        'change': 0.5,
        'completion': 0.5,
        'impact': 0.6,
    }
    
    # 1. KNOW: Analyze confidence indicators
    know_score = 0.5
    
    # High confidence phrases
    high_conf_patterns = [
        r'\b(definitely|certainly|absolutely|clearly|obviously|without doubt)\b',
        r'\bi know (that|this)',
        r'\bthis is (definitely|certainly)',
        r'\bthe answer is\b',
    ]
    
    # Low confidence phrases
    low_conf_patterns = [
        r'\b(might|maybe|perhaps|possibly|not sure|uncertain)\b',
        r'\bi think (maybe|perhaps)',
        r'\bit could be\b',
        r'\bnot certain\b',
        r'\bi don\'t know\b',
    ]
    
    high_conf_count = sum(len(re.findall(p, full_text)) for p in high_conf_patterns)
    low_conf_count = sum(len(re.findall(p, full_text)) for p in low_conf_patterns)
    
    if high_conf_count > low_conf_count:
        know_score = min(1.0, 0.7 + (high_conf_count * 0.1))
    elif low_conf_count > high_conf_count:
        know_score = max(0.2, 0.5 - (low_conf_count * 0.1))
    
    # Check for explicit knowledge claims
    if re.search(r'\b(i (?:can|will|should) (?:definitely|help|explain))\b', full_text):
        know_score = min(1.0, know_score + 0.2)
    
    vectors['know'] = round(know_score, 2)
    
    # 2. UNCERTAINTY: Inverse of know, plus explicit uncertainty markers
    uncertainty_markers = [
        'unclear', 'ambiguous', 'hard to say', 'depends on',
        'more information needed', 'need to know', 'requires clarification'
    ]
    uncertainty_count = sum(1 for marker in uncertainty_markers if marker in full_text)
    
    base_uncertainty = 1.0 - vectors['know']
    vectors['uncertainty'] = round(min(1.0, base_uncertainty + (uncertainty_count * 0.1)), 2)
    
    # 3. DO: Actionability - can the AI actually help?
    do_score = 0.5
    
    # Action indicators
    action_patterns = [
        r'\b(i can|i will|i\'ll|let me|here\'s how)\b',
        r'\b(you can|you should|you could)\b',
        r'\b(step \d+|first|next|then|finally)\b',
    ]
    
    action_count = sum(len(re.findall(p, full_text)) for p in action_patterns)
    
    # Check if response contains code, examples, or specific instructions
    has_code = '```' in response_text or 'def ' in response_text
    has_list = re.search(r'(^|\n)[•\-\*\d]+\.', response_text, re.MULTILINE)
    has_steps = 'step' in full_text or 'first' in full_text
    
    do_score = 0.5 + (action_count * 0.1)
    if has_code:
        do_score += 0.2
    if has_list:
        do_score += 0.1
    if has_steps:
        do_score += 0.1
    
    vectors['do'] = round(min(1.0, do_score), 2)
    
    # 4. CONTEXT: How much context does the AI have?
    context_score = 0.5
    
    # Check for references to previous conversation
    context_indicators = [
        'as you mentioned', 'as we discussed', 'previously', 'earlier',
        'building on', 'continuing from', 'based on your question'
    ]
    context_count = sum(1 for ind in context_indicators if ind in full_text)
    
    # Check query length (more context given)
    query_words = len(query.split())
    if query_words > 50:
        context_score += 0.2
    elif query_words < 10:
        context_score -= 0.1
    
    context_score += (context_count * 0.15)
    vectors['context'] = round(max(0.1, min(1.0, context_score)), 2)
    
    # 5. CLARITY: Is the response clear?
    clarity_score = 0.5
    
    # Factors that improve clarity
    response_length = len(response_text)
    
    # Too short or too long reduces clarity
    if 50 < response_length < 1000:
        clarity_score += 0.2
    elif response_length > 2000:
        clarity_score -= 0.1
    
    # Structured responses are clearer
    if has_list or has_code:
        clarity_score += 0.1
    
    # Hedging reduces clarity
    hedging_count = sum(1 for word in ['maybe', 'perhaps', 'might', 'possibly'] 
                       if word in full_text)
    clarity_score -= (hedging_count * 0.05)
    
    vectors['clarity'] = round(max(0.1, min(1.0, clarity_score)), 2)
    
    # 6. COMPLETION: Did the AI fully answer?
    completion_score = 0.5
    
    # Check for incomplete indicators
    incomplete_markers = [
        'more detail', 'further explanation', 'additional information',
        'if you want', 'let me know if', 'would you like'
    ]
    incomplete_count = sum(1 for marker in incomplete_markers if marker in full_text)
    
    # Check for completion indicators
    complete_markers = [
        'in summary', 'to conclude', 'that\'s everything', 'hope this helps',
        'full explanation', 'complete answer'
    ]
    complete_count = sum(1 for marker in complete_markers if marker in full_text)
    
    completion_score = 0.5 + (complete_count * 0.15) - (incomplete_count * 0.1)
    vectors['completion'] = round(max(0.2, min(1.0, completion_score)), 2)
    
    # 7. DENSITY: Information density
    words = len(response_text.split())
    if words < 50:
        density = 0.3
    elif words < 150:
        density = 0.6
    elif words < 500:
        density = 0.8
    else:
        density = 0.9
    
    vectors['density'] = round(density, 2)
    
    # Log extracted vectors if thinking was available
    if thinking_blocks:
        logger.info(f"📊 Epistemic extraction (with thinking): KNOW={vectors['know']}, "
                   f"DO={vectors['do']}, UNCERTAINTY={vectors['uncertainty']}")
    
    return vectors


def extract_decision(response_text: str, thinking_blocks: Optional[List[str]] = None) -> tuple[str, float]:
    """
    Extract decision and confidence from AI response.
    
    Returns:
        Tuple of (decision, confidence) where decision is ACT|CHECK|INVESTIGATE|VERIFY
    """
    full_text = response_text.lower()
    if thinking_blocks:
        thinking_text = " ".join(thinking_blocks).lower()
        full_text = thinking_text + " " + full_text
    
    # Check for investigation/uncertainty indicators
    investigate_markers = [
        'uncertain', 'unclear', 'more information', 'clarify', 'not sure',
        'need to know', 'depends on', 'requires', 'would need'
    ]
    investigate_count = sum(1 for marker in investigate_markers if marker in full_text)
    
    # Check for verification indicators
    check_markers = [
        'check', 'verify', 'confirm', 'validate', 'double-check',
        'make sure', 'ensure', 'review'
    ]
    check_count = sum(1 for marker in check_markers if marker in full_text)
    
    # Decide
    if investigate_count >= 2:
        return "INVESTIGATE", 0.4
    elif check_count >= 2:
        return "CHECK", 0.6
    else:
        # ACT is default
        # Confidence based on certainty markers
        confidence = 0.7
        
        if any(word in full_text for word in ['definitely', 'certainly', 'absolutely']):
            confidence = 0.9
        elif any(word in full_text for word in ['probably', 'likely', 'should']):
            confidence = 0.7
        elif any(word in full_text for word in ['might', 'maybe', 'perhaps']):
            confidence = 0.5
        
        return "ACT", confidence
