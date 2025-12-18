"""
Ollama Adapter for Reasoning Service

Connects to Ollama-hosted models for doc-code intelligence reasoning.
Optimized for qwen2.5:32b on empirica-server.
"""

import requests
import json
import logging
from typing import Dict, Optional
from .service import ReasoningService
from .types import DeprecationJudgment, RelationshipAnalysis, ImplementationGap

logger = logging.getLogger(__name__)


class OllamaReasoningModel(ReasoningService):
    """Adapter for Ollama-hosted reasoning models"""
    
    def __init__(
        self,
        model_name: str = "qwen2.5:32b",
        endpoint: str = "http://empirica-server:11434",
        timeout: int = 60
    ):
        self.model_name = model_name
        self.endpoint = endpoint
        self.timeout = timeout
        
    def _call_ollama(
        self,
        prompt: str,
        format: str = "json",
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> Dict:
        """
        Low-level Ollama API call
        
        Args:
            prompt: Prompt text
            format: Response format ("json" or None)
            temperature: Sampling temperature (lower = more consistent)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with 'response' key containing model output
            
        Raises:
            Exception on connection/timeout errors
        """
        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": format,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "num_predict": max_tokens
                    }
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling {self.model_name} after {self.timeout}s")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed to {self.endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise
    
    def _build_deprecation_prompt(self, feature: str, context: Dict) -> str:
        """Build prompt for deprecation analysis"""
        
        doc_mentions = context.get('doc_mentions', [])
        doc_text = "\n".join([f"- {m['context']}" for m in doc_mentions[:3]])
        
        code_exists = context.get('code_exists', False)
        usage_count = context.get('usage_count', 0)
        last_commit = context.get('last_commit', 'unknown')
        
        prompt = f"""You are analyzing whether a software feature is genuinely deprecated.

Feature: {feature}

Documentation mentions:
{doc_text}

Code status: {'Implemented' if code_exists else 'Not found'}
Usage in last 50 sessions: {usage_count} times
Last git commit: {last_commit}

Task: Determine if this feature is:
1. "deprecated" - Currently deprecated, should be removed/marked
2. "historical" - Previously deprecated but now current (historical context only)
3. "active" - Still active and in use

Reasoning guidelines:
- "previously deprecated" = past tense, not current deprecation
- Check if code is actively maintained (recent commits = active)
- Check if usage patterns show active use (many uses = active)
- Consider relationships to other features

Respond in JSON format only, no additional text:
{{
    "status": "deprecated|historical|active",
    "confidence": 0.0-1.0,
    "reasoning": "brief step-by-step analysis",
    "evidence": ["key evidence points"],
    "recommendation": "specific action to take"
}}"""
        
        return prompt
    
    def _parse_deprecation_response(self, response: Dict) -> DeprecationJudgment:
        """Parse Ollama response into DeprecationJudgment"""
        
        try:
            # Extract response text
            response_text = response.get('response', '')
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['status', 'confidence', 'reasoning', 'evidence', 'recommendation']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field in response: {field}")
                    data[field] = "unknown" if field == 'status' else ([] if field == 'evidence' else "")
            
            # Validate status
            valid_statuses = ['deprecated', 'historical', 'active']
            if data['status'] not in valid_statuses:
                logger.warning(f"Invalid status: {data['status']}, defaulting to 'active'")
                data['status'] = 'active'
            
            # Ensure confidence is float
            try:
                confidence = float(data['confidence'])
                confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
            except (ValueError, TypeError):
                logger.warning(f"Invalid confidence: {data['confidence']}, defaulting to 0.5")
                confidence = 0.5
            
            return DeprecationJudgment(
                feature="",  # Will be set by caller
                status=data['status'],
                confidence=confidence,
                reasoning=data.get('reasoning', ''),
                evidence=data.get('evidence', []),
                recommendation=data.get('recommendation', ''),
                metadata={'raw_response': response_text}
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response was: {response.get('response', '')[:500]}")
            
            # Return fallback judgment
            return DeprecationJudgment(
                feature="",
                status="active",  # Conservative default
                confidence=0.0,
                reasoning="Failed to parse model response",
                evidence=["JSON parsing error"],
                recommendation="Manual review required",
                metadata={'error': str(e), 'raw_response': response.get('response', '')[:500]}
            )
    
    def analyze_deprecation(
        self,
        feature: str,
        context: Dict
    ) -> DeprecationJudgment:
        """
        Analyze if feature is deprecated using AI reasoning
        
        Args:
            feature: Feature name (command, function, etc.)
            context: Dict with evidence:
                - doc_mentions: List of doc locations mentioning feature
                - code_exists: Bool
                - usage_count: Int (from artifacts)
                - last_commit: Date string
                - related_features: List
                
        Returns:
            DeprecationJudgment with status and reasoning
        """
        logger.info(f"Analyzing deprecation for: {feature}")
        
        try:
            # Build prompt
            prompt = self._build_deprecation_prompt(feature, context)
            
            # Call model
            response = self._call_ollama(prompt, format="json", temperature=0.1)
            
            # Parse response
            judgment = self._parse_deprecation_response(response)
            judgment.feature = feature
            
            logger.info(f"Analysis complete: {feature} -> {judgment.status} (confidence: {judgment.confidence:.2f})")
            
            return judgment
            
        except Exception as e:
            logger.error(f"Error analyzing {feature}: {e}")
            
            # Return fallback judgment
            return DeprecationJudgment(
                feature=feature,
                status="active",  # Conservative default
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                evidence=["Error during analysis"],
                recommendation="Manual review required",
                metadata={'error': str(e)}
            )
    
    def _build_relationship_prompt(self, doc_section: str, code_section: str, context: Dict) -> str:
        """Build prompt for relationship analysis"""
        
        feature_name = context.get('feature_name', 'unknown')
        doc_location = context.get('doc_location', 'unknown')
        code_location = context.get('code_location', 'unknown')
        
        prompt = f"""You are analyzing whether documentation and code describe the same feature.

Feature name: {feature_name}

Documentation (from {doc_location}):
{doc_section}

Code implementation (from {code_location}):
{code_section}

Task: Determine the relationship between doc and code:
1. "aligned" - Doc and code describe the same feature correctly
2. "drift" - Doc and code describe the same feature but details mismatch
3. "phantom" - Doc describes feature that doesn't exist in code
4. "undocumented" - Code exists but is not documented
5. "deprecated_doc" - Doc describes deprecated/removed feature

Analysis guidelines:
- Check if doc and code refer to same feature name/identifier
- Compare parameters, behavior, return values
- Look for version mismatches (doc says X but code does Y)
- Consider if doc is historical context vs current feature
- Check for "was removed", "previously", "deprecated" language

Respond in JSON format only, no additional text:
{{
    "relationship": "aligned|drift|phantom|undocumented|deprecated_doc",
    "confidence": 0.0-1.0,
    "reasoning": "step-by-step analysis of alignment",
    "mismatches": ["specific differences found"],
    "severity": "critical|high|medium|low",
    "recommendation": "specific action to fix alignment"
}}"""
        
        return prompt
    
    def _parse_relationship_response(self, response: Dict) -> RelationshipAnalysis:
        """Parse Ollama response into RelationshipAnalysis"""
        
        try:
            response_text = response.get('response', '')
            data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['relationship', 'confidence', 'reasoning', 'mismatches', 'severity', 'recommendation']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field in relationship response: {field}")
                    data[field] = "unknown" if field in ['relationship', 'severity'] else ([] if field == 'mismatches' else "")
            
            # Validate relationship type
            valid_relationships = ['aligned', 'drift', 'phantom', 'undocumented', 'deprecated_doc']
            if data['relationship'] not in valid_relationships:
                logger.warning(f"Invalid relationship: {data['relationship']}, defaulting to 'drift'")
                data['relationship'] = 'drift'
            
            # Validate severity
            valid_severities = ['critical', 'high', 'medium', 'low']
            if data['severity'] not in valid_severities:
                logger.warning(f"Invalid severity: {data['severity']}, defaulting to 'medium'")
                data['severity'] = 'medium'
            
            # Ensure confidence is float
            try:
                confidence = float(data['confidence'])
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                logger.warning(f"Invalid confidence: {data['confidence']}, defaulting to 0.5")
                confidence = 0.5
            
            return RelationshipAnalysis(
                doc_ref="",  # Will be set by caller
                code_ref="",
                relationship=data['relationship'],
                confidence=confidence,
                reasoning=data.get('reasoning', ''),
                mismatches=data.get('mismatches', []),
                severity=data.get('severity', 'medium'),
                recommendation=data.get('recommendation', ''),
                metadata={'raw_response': response_text}
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for relationship: {e}")
            logger.error(f"Response was: {response.get('response', '')[:500]}")
            
            return RelationshipAnalysis(
                doc_ref="",
                code_ref="",
                relationship="drift",  # Conservative default
                confidence=0.0,
                reasoning="Failed to parse model response",
                mismatches=["JSON parsing error"],
                severity="medium",
                recommendation="Manual review required",
                metadata={'error': str(e), 'raw_response': response.get('response', '')[:500]}
            )
    
    def analyze_relationship(
        self,
        doc_section: str,
        code_section: str,
        context: Optional[Dict] = None
    ) -> RelationshipAnalysis:
        """
        Analyze relationship between doc and code sections
        
        Args:
            doc_section: Documentation text describing a feature
            code_section: Code implementation (function, class, etc.)
            context: Optional dict with:
                - feature_name: Name of the feature
                - doc_location: Where doc is found (file:line)
                - code_location: Where code is found (file:line)
                
        Returns:
            RelationshipAnalysis with relationship type and reasoning
        """
        context = context or {}
        feature_name = context.get('feature_name', 'unknown')
        
        logger.info(f"Analyzing doc-code relationship for: {feature_name}")
        
        try:
            # Build prompt
            prompt = self._build_relationship_prompt(doc_section, code_section, context)
            
            # Call model
            response = self._call_ollama(prompt, format="json", temperature=0.1)
            
            # Parse response
            analysis = self._parse_relationship_response(response)
            analysis.doc_ref = context.get('doc_location', 'unknown')
            analysis.code_ref = context.get('code_location', 'unknown')
            
            logger.info(f"Relationship analysis complete: {feature_name} -> {analysis.relationship} (confidence: {analysis.confidence:.2f})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing relationship for {feature_name}: {e}")
            
            return RelationshipAnalysis(
                doc_ref=context.get('doc_location', 'unknown'),
                code_ref=context.get('code_location', 'unknown'),
                relationship="drift",  # Conservative default
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                mismatches=["Error during analysis"],
                severity="medium",
                recommendation="Manual review required",
                metadata={'error': str(e)}
            )
    
    def _build_implementation_gap_prompt(self, documented_behavior: str, actual_implementation: str, context: Dict) -> str:
        """Build prompt for implementation gap analysis"""
        
        feature_name = context.get('feature_name', 'unknown')
        test_results = context.get('test_results', 'none')
        
        prompt = f"""You are analyzing whether code implementation matches documented behavior.

Feature: {feature_name}

Documented behavior:
{documented_behavior}

Actual implementation (code):
{actual_implementation}

Test results (if available):
{test_results}

Task: Identify gaps between documented behavior and actual implementation:
1. "matches" - Implementation fully matches documented behavior
2. "partial" - Implementation partially matches, some features missing/different
3. "mismatch" - Implementation does something different than documented
4. "untested" - Cannot verify match without running tests
5. "undocumented_features" - Implementation has features not in docs

Analysis guidelines:
- Compare expected inputs/outputs from docs vs code
- Check for edge cases mentioned in docs but not handled in code
- Look for parameters documented but not implemented (or vice versa)
- Identify behavior differences (doc says "validates X" but code doesn't)
- Consider if tests prove the match

Respond in JSON format only, no additional text:
{{
    "gap_type": "matches|partial|mismatch|untested|undocumented_features",
    "confidence": 0.0-1.0,
    "reasoning": "detailed analysis of behavior match",
    "gaps": ["specific gaps between doc and implementation"],
    "severity": "critical|high|medium|low",
    "missing_features": ["features in doc but not in code"],
    "extra_features": ["features in code but not in doc"],
    "recommendation": "specific action to close gap"
}}"""
        
        return prompt
    
    def _parse_implementation_gap_response(self, response: Dict) -> ImplementationGap:
        """Parse Ollama response into ImplementationGap"""
        
        try:
            response_text = response.get('response', '')
            data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['gap_type', 'confidence', 'reasoning', 'gaps', 'severity', 
                             'missing_features', 'extra_features', 'recommendation']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field in gap response: {field}")
                    if field in ['gap_type', 'severity']:
                        data[field] = "unknown"
                    elif field in ['gaps', 'missing_features', 'extra_features']:
                        data[field] = []
                    else:
                        data[field] = ""
            
            # Validate gap type
            valid_gap_types = ['matches', 'partial', 'mismatch', 'untested', 'undocumented_features']
            if data['gap_type'] not in valid_gap_types:
                logger.warning(f"Invalid gap_type: {data['gap_type']}, defaulting to 'partial'")
                data['gap_type'] = 'partial'
            
            # Validate severity
            valid_severities = ['critical', 'high', 'medium', 'low']
            if data['severity'] not in valid_severities:
                logger.warning(f"Invalid severity: {data['severity']}, defaulting to 'medium'")
                data['severity'] = 'medium'
            
            # Ensure confidence is float
            try:
                confidence = float(data['confidence'])
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                logger.warning(f"Invalid confidence: {data['confidence']}, defaulting to 0.5")
                confidence = 0.5
            
            return ImplementationGap(
                feature="",  # Will be set by caller
                gap_type=data['gap_type'],
                confidence=confidence,
                reasoning=data.get('reasoning', ''),
                gaps=data.get('gaps', []),
                severity=data.get('severity', 'medium'),
                missing_features=data.get('missing_features', []),
                extra_features=data.get('extra_features', []),
                recommendation=data.get('recommendation', ''),
                metadata={'raw_response': response_text}
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for implementation gap: {e}")
            logger.error(f"Response was: {response.get('response', '')[:500]}")
            
            return ImplementationGap(
                feature="",
                gap_type="partial",  # Conservative default
                confidence=0.0,
                reasoning="Failed to parse model response",
                gaps=["JSON parsing error"],
                severity="medium",
                missing_features=[],
                extra_features=[],
                recommendation="Manual review required",
                metadata={'error': str(e), 'raw_response': response.get('response', '')[:500]}
            )
    
    def analyze_implementation_gap(
        self,
        documented_behavior: str,
        actual_implementation: str,
        context: Optional[Dict] = None
    ) -> ImplementationGap:
        """
        Analyze gaps between documented behavior and actual implementation
        
        Args:
            documented_behavior: What the docs say the feature should do
            actual_implementation: Code implementing the feature
            context: Optional dict with:
                - feature_name: Name of the feature
                - test_results: Test output showing behavior (if available)
                
        Returns:
            ImplementationGap with gap type and specific differences
        """
        context = context or {}
        feature_name = context.get('feature_name', 'unknown')
        
        logger.info(f"Analyzing implementation gap for: {feature_name}")
        
        try:
            # Build prompt
            prompt = self._build_implementation_gap_prompt(documented_behavior, actual_implementation, context)
            
            # Call model
            response = self._call_ollama(prompt, format="json", temperature=0.1)
            
            # Parse response
            gap_analysis = self._parse_implementation_gap_response(response)
            gap_analysis.feature = feature_name
            
            logger.info(f"Gap analysis complete: {feature_name} -> {gap_analysis.gap_type} (confidence: {gap_analysis.confidence:.2f})")
            
            return gap_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing implementation gap for {feature_name}: {e}")
            
            return ImplementationGap(
                feature=feature_name,
                gap_type="partial",  # Conservative default
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                gaps=["Error during analysis"],
                severity="medium",
                missing_features=[],
                extra_features=[],
                recommendation="Manual review required",
                metadata={'error': str(e)}
            )
