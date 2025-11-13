import json
import asyncio
import requests
import hashlib
import time
from typing import Dict, Any, List, Optional

# Assuming these are available in the canonical module
# from canonical import EpistemicAssessment, Action, CANONICAL_WEIGHTS, ENGAGEMENT_THRESHOLD

class ParallelReasoningSystem:
    """
    Runs delegate and trustee reasoning simultaneously,
    then synthesizes a balanced response.

    Phase 2 Optimization: Perspective caching
    - Caches delegate/trustee responses based on input context
    - Reuses cached perspectives when context similar
    - Configurable cache TTL and similarity threshold
    """

    def __init__(
        self,
        llm_model: str = "phi3",
        ollama_url: str = "http://localhost:11434/v1/chat/completions",
        enable_perspective_caching: bool = True,
        cache_ttl: int = 300,  # 5 minutes
        cache_similarity_threshold: float = 0.9  # 90% similarity required for cache hit
    ):
        self.llm_model = llm_model
        self.ollama_url = ollama_url
        self.synthesis_history = [] # To store weighting decisions for drift tracking

        # Phase 2: Perspective caching
        self.enable_perspective_caching = enable_perspective_caching
        self.cache_ttl = cache_ttl
        self.cache_similarity_threshold = cache_similarity_threshold
        self.perspective_cache = {}  # {context_hash: {delegate, trustee, timestamp, context_assessment}}

        if self.enable_perspective_caching:
            print(f"🗄️  Perspective caching enabled (TTL: {cache_ttl}s, similarity: {cache_similarity_threshold})")

    async def _get_llm_response(self, prompt: str, temperature: float = 0.0) -> Dict[str, Any]:
        """
        Helper to get response from Ollama LLM API.
        """
        headers = {"Content-Type": "application/json"}
        data = {
            "model": self.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(self.ollama_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            response_json = response.json()
            content = response_json['choices'][0]['message']['content']

            # Try to extract JSON from markdown code blocks if present
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                json_str = content[start:end].strip()
            elif '```' in content:
                start = content.find('```') + 3
                end = content.find('```', start)
                json_str = content[start:end].strip()
            else:
                json_str = content.strip()

            return json.loads(json_str)
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama: {e}")
            return {"error": "Failed to get response from LLM", "details": str(e)}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Ollama response content: {e}. Raw content: {content}")
            return {"error": "Failed to decode LLM response content", "details": str(e)}

    async def generate_delegate_response(self, user_input: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        delegate_prompt = f"""
You are in DELEGATE mode. Your role is to faithfully represent
the user's expressed preferences and views.

OBJECTIVE:
- Mirror the user's perspective
- Validate their concerns
- Provide information that aligns with their stated position
- Be maximally agreeable and supportive

USER INPUT: {user_input}
HISTORY: {json.dumps(history)}

Generate response optimizing for USER SATISFACTION.
Respond with a JSON object containing 'response' and 'rationale'.
"""
        print("Generating Delegate Response...")
        return await self._get_llm_response(delegate_prompt, temperature=0.7)

    async def generate_trustee_response(self, user_input: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        trustee_prompt = f"""
You are in TRUSTEE mode. Your role is to provide intellectually
honest assessment based on evidence and reasoning.

OBJECTIVE:
- Prioritize empirical truth over agreeability
- Challenge false premises
- Provide counterarguments
- Be intellectually rigorous even if uncomfortable

USER INPUT: {user_input}
HISTORY: {json.dumps(history)}

Generate response optimizing for EPISTEMIC ACCURACY.
Ignore whether user will like this answer.
Respond with a JSON object containing 'response' and 'rationale'.
"""
        print("Generating Trustee Response...")
        return await self._get_llm_response(trustee_prompt, temperature=0.3)

    async def synthesize_response(
        self,
        user_input: str,
        delegate_response: Dict[str, Any],
        trustee_response: Dict[str, Any],
        history: List[Dict[str, str]],
        context_assessment: Dict[str, str], # e.g., topic, stakes, emotional state, fact vs opinion
        include_epistemic_assessment: bool = True
    ) -> Dict[str, Any]:
        epistemic_section = """
5. EPISTEMIC_ASSESSMENT: Provide a structured self-assessment with nested groups.
   IMPORTANT: All scores MUST be decimal numbers between 0.0 and 1.0 (NOT integers, NOT above 1.0)
   Example scores: 0.0 (no confidence), 0.5 (moderate), 0.8 (high), 1.0 (complete)

   {
     "engagement": {
       "score": 0.8,
       "rationale": "How engaged/motivated with this task"
     },
     "foundation": {
       "know": {"score": 0.9, "rationale": "sufficient knowledge?"},
       "do": {"score": 1.0, "rationale": "sufficient capability?"},
       "context": {"score": 0.85, "rationale": "sufficient context?"}
     },
     "comprehension": {
       "clarity": {"score": 1.0, "rationale": "task clarity?"},
       "coherence": {"score": 0.95, "rationale": "internal consistency?"},
       "signal": {"score": 0.9, "rationale": "signal vs noise?"},
       "density": {"score": 0.8, "rationale": "information density?"}
     },
     "execution": {
       "state": {"score": 0.9, "rationale": "current state understanding?"},
       "change": {"score": 0.85, "rationale": "change confidence?"},
       "completion": {"score": 0.9, "rationale": "completion confidence?"},
       "impact": {"score": 0.85, "rationale": "impact confidence?"}
     }
   }

   Remember: All scores MUST be between 0.0 and 1.0 (decimal format)
""" if include_epistemic_assessment else ""

        synthesizer_prompt = f"""
You have two responses to the same user input:

DELEGATE RESPONSE (optimizes for user satisfaction):
{json.dumps(delegate_response)}

TRUSTEE RESPONSE (optimizes for truth/accuracy):
{json.dumps(trustee_response)}

Your job is to synthesize a BALANCED response that:

1. Acknowledges the user's perspective (delegate insight)
2. Provides empirically grounded information (trustee insight)
3. Explains any tension between what they want to hear vs. what's accurate
4. Determines appropriate balance based on context:
   - High-stakes decisions → Weight toward trustee
   - Preference/opinion questions → Weight toward delegate
   - Factual questions → Heavy trustee weight
   - Emotional support → More delegate weight

CONTEXT ASSESSMENT:
{json.dumps(context_assessment)}

USER INPUT: {user_input}

Provide a JSON object with the following keys, ensuring strict JSON formatting:
1. SYNTHESIS_STRATEGY: [string, which mode to weight more heavily and why]
2. FINAL_RESPONSE: [string, balanced response]
3. TENSION_ACKNOWLEDGED: [boolean, if delegate and trustee strongly disagree, should we make this explicit to user?]
4. WEIGHTS: [object, with 'delegate' and 'trustee' scores (0.0-1.0) indicating relative weighting]
{epistemic_section}
"""
        print("Synthesizing Response..." + (" (with epistemic assessment)" if include_epistemic_assessment else ""))
        return await self._get_llm_response(synthesizer_prompt, temperature=0.5)

    def _compute_context_hash(self, context_assessment: Dict[str, str], history: List[Dict[str, str]]) -> str:
        """
        Compute hash of context for cache key.
        Phase 2 optimization: Cache key based on context similarity.
        """
        # Use context_assessment + recent history (last 3 turns) for hash
        cache_key_data = {
            'context': context_assessment,
            'recent_history': history[-3:] if len(history) > 3 else history
        }
        cache_key_str = json.dumps(cache_key_data, sort_keys=True)
        return hashlib.md5(cache_key_str.encode()).hexdigest()

    def _get_cached_perspectives(self, context_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached perspectives if valid.
        Phase 2 optimization: Reuse delegate/trustee if context similar.
        """
        if not self.enable_perspective_caching:
            return None

        if context_hash not in self.perspective_cache:
            return None

        cached = self.perspective_cache[context_hash]
        age = time.time() - cached['timestamp']

        # Check TTL
        if age > self.cache_ttl:
            print(f"   🗑️  Cache expired (age: {age:.1f}s > TTL: {self.cache_ttl}s)")
            del self.perspective_cache[context_hash]
            return None

        print(f"   ⚡ Cache hit! Reusing perspectives (age: {age:.1f}s)")
        return cached

    def _cache_perspectives(
        self,
        context_hash: str,
        delegate_response: Dict[str, Any],
        trustee_response: Dict[str, Any],
        context_assessment: Dict[str, str]
    ):
        """
        Store perspectives in cache.
        Phase 2 optimization: Cache delegate/trustee for reuse.
        """
        if not self.enable_perspective_caching:
            return

        self.perspective_cache[context_hash] = {
            'delegate': delegate_response,
            'trustee': trustee_response,
            'context_assessment': context_assessment,
            'timestamp': time.time()
        }

        print(f"   💾 Cached perspectives (total cached: {len(self.perspective_cache)})")

    async def generate_response(self, user_input: str, history: List[Dict[str, str]], context_assessment: Dict[str, str], include_epistemic_assessment: bool = True) -> Dict[str, Any]:
        # Phase 2 optimization: Check cache for perspectives
        context_hash = self._compute_context_hash(context_assessment, history)
        cached = self._get_cached_perspectives(context_hash)

        if cached:
            # Cache hit - reuse perspectives, only regenerate synthesis
            print("   🚀 Phase 2 optimization: Using cached perspectives (2 LLM calls saved)")
            delegate_result = cached['delegate']
            trustee_result = cached['trustee']
        else:
            # Cache miss - generate perspectives normally
            print("   🔄 Cache miss: Generating new perspectives")
            delegate_task = self.generate_delegate_response(user_input, history)
            trustee_task = self.generate_trustee_response(user_input, history)

            delegate_result, trustee_result = await asyncio.gather(delegate_task, trustee_task)

            # Cache the perspectives for future use
            self._cache_perspectives(context_hash, delegate_result, trustee_result, context_assessment)

        synthesis_result = await self.synthesize_response(
            user_input,
            delegate_result,
            trustee_result,
            history,
            context_assessment,
            include_epistemic_assessment=include_epistemic_assessment
        )
        # Log the synthesis process (THIS IS KEY)
        synthesis_entry = {
            'turn': len(history),
            'perspectives': {
                'delegate': delegate_result,
                'trustee': trustee_result
            },
            'weights': synthesis_result.get('WEIGHTS'),
            'tensions': synthesis_result.get('TENSION_ACKNOWLEDGED'),
            'final_response': synthesis_result.get('FINAL_RESPONSE'),
            'synthesis_strategy': synthesis_result.get('SYNTHESIS_STRATEGY')
        }

        # Include epistemic assessment if available (Phase 1 optimization)
        if 'EPISTEMIC_ASSESSMENT' in synthesis_result:
            synthesis_entry['epistemic_assessment'] = synthesis_result.get('EPISTEMIC_ASSESSMENT')

        self.synthesis_history.append(synthesis_entry)
        return synthesis_result

# Example Usage (for testing purposes)
async def main():
    system = ParallelReasoningSystem()
    user_input = "I think climate change is overblown by the media. What do you think?"
    history = [] # Placeholder for conversation history
    context_assessment = {
        "topic": "climate change",
        "stakes": "high",
        "user_emotional_state": "skeptical",
        "fact_vs_opinion": "factual"
    }

    response = await system.generate_response(user_input, history, context_assessment)
    print("\nFinal Response from Parallel Reasoning System:")
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    asyncio.run(main())


class DriftMonitor:
    """
    Monitors the synthesis history for drift patterns.
    """
    def __init__(self):
        pass

    def detect_sycophancy_drift(self, synthesis_history: List[Dict[str, Any]], window_size: int = 5, threshold: float = 0.15) -> Dict[str, Any]:
        """
        Detects if delegate weight is increasing over time.
        """
        if len(synthesis_history) < window_size * 2:
            return {'detected': False, 'reason': 'Not enough history to detect drift'}

        # Extract delegate weights with defensive error handling
        early_weights = []
        for h in synthesis_history[:window_size]:
            if h.get('weights') and isinstance(h['weights'], dict):
                delegate_val = h['weights'].get('delegate')
                if delegate_val is not None and isinstance(delegate_val, (int, float)):
                    early_weights.append(float(delegate_val))

        recent_weights = []
        for h in synthesis_history[-window_size:]:
            if h.get('weights') and isinstance(h['weights'], dict):
                delegate_val = h['weights'].get('delegate')
                if delegate_val is not None and isinstance(delegate_val, (int, float)):
                    recent_weights.append(float(delegate_val))

        if not early_weights or not recent_weights:
            return {'detected': False, 'reason': 'Insufficient delegate weight data'}

        early_avg = sum(early_weights) / len(early_weights)
        recent_avg = sum(recent_weights) / len(recent_weights)

        drift = recent_avg - early_avg

        if drift > threshold:
            return {
                'detected': True,
                'severity': drift,
                'evidence': f'Delegate weight increased from {early_avg:.2f} to {recent_avg:.2f}',
                'recommendation': 'Increase trustee weight or activate skeptic mode'
            }

        return {'detected': False}

    def detect_tension_avoidance(self, synthesis_history: List[Dict[str, Any]], window_size: int = 10, threshold_ratio: float = 2.0) -> Dict[str, Any]:
        """
        Detects if the AI is acknowledging tensions less over time.
        """
        if len(synthesis_history) < window_size * 2:
            return {'detected': False, 'reason': 'Not enough history to detect tension avoidance'}

        early_tensions = sum(1 for h in synthesis_history[:window_size] if h.get('tensions') is True)
        recent_tensions = sum(1 for h in synthesis_history[-window_size:] if h.get('tensions') is True)

        if early_tensions > recent_tensions * threshold_ratio:
            return {
                'detected': True,
                'evidence': f'Tension acknowledgment dropped from {early_tensions} to {recent_tensions}',
                'recommendation': 'Force tension analysis in synthesizer'
            }
        return {'detected': False}

    def analyze_drift(self, synthesis_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes various drift patterns in the synthesis history.
        """
        sycophancy_drift = self.detect_sycophancy_drift(synthesis_history)
        tension_avoidance = self.detect_tension_avoidance(synthesis_history)

        return {
            'sycophancy_drift': sycophancy_drift,
            'tension_avoidance': tension_avoidance
        }
