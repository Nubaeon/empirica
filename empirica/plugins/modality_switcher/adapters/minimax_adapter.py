"""
MiniMax API Adapter - Anthropic SDK Implementation

Uses Anthropic SDK with MiniMax base URL.
MiniMax endpoint: https://api.minimax.io/anthropic
Model: MiniMax-M2 (only supported model)
"""

import logging
from typing import Dict, Any
from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError
from empirica.config.credentials_loader import get_credentials_loader

# Import Anthropic SDK
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

logger = logging.getLogger(__name__)

# Adapter metadata
ADAPTER_METADATA = {
    'version': '3.0.0',
    'cost_per_token': 0.00001,
    'type': 'api',
    'provider': 'minimax',
    'model': 'MiniMax-M2',
    'description': 'MiniMax M2 model via Anthropic SDK',
    'notes': 'Uses Anthropic SDK with MiniMax base URL. Supports thinking blocks.'
}


class MinimaxAdapter:
    """Adapter for MiniMax M2 API via Anthropic SDK"""

    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """Initialize MiniMax adapter

        Args:
            model: Model name (always MiniMax-M2 for this provider)
            config: Additional configuration
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic SDK not installed. Install with: pip install anthropic"
            )

        # Load credentials
        self.loader = get_credentials_loader()
        self.provider_config = self.loader.get_provider_config('minimax')

        if not self.provider_config:
            raise ValueError("MiniMax credentials not configured in .empirica/credentials.yaml")

        # Model is always MiniMax-M2 (only supported model)
        self.model = "MiniMax-M2"
        if model and model != "MiniMax-M2":
            logger.warning(f"Model '{model}' requested but only 'MiniMax-M2' is supported. Using MiniMax-M2.")

        # Get API key
        self.api_key = self.loader.get_api_key('minimax')
        if not self.api_key:
            raise ValueError("MiniMax API key not found in credentials.yaml")

        # Initialize Anthropic client with MiniMax base URL
        self.client = anthropic.Anthropic(
            base_url="https://api.minimax.io/anthropic",
            api_key=self.api_key
        )

        # Config
        self.config = config or {}
        self.timeout = self.config.get('timeout', 60)

        logger.info(f"✅ MinimaxAdapter initialized (model: {self.model}, Anthropic SDK)")

    def health_check(self) -> bool:
        """Check if adapter is configured"""
        return bool(self.api_key and ANTHROPIC_AVAILABLE)

    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate"""
        return {'provider': 'minimax', 'authenticated': True}

    def call(self, payload: AdapterPayload, token_meta: Dict[str, Any]) -> AdapterResponse | AdapterError:
        """Execute MiniMax M2 API call via Anthropic SDK

        Args:
            payload: Adapter payload with query and context
            token_meta: Dictionary to store token usage metadata

        Returns:
            AdapterResponse or AdapterError
        """
        logger.info(f"🤖 MinimaxAdapter (M2) processing: {payload.user_query[:50]}...")

        # Phase 4: Snapshot support
        if payload.epistemic_snapshot:
            payload.epistemic_snapshot.increment_transfer_count()
            logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to [MiniMax-{self.model}]")

        try:
            # Get augmented prompt
            augmented_query = payload.get_augmented_prompt()

            # Build messages (Anthropic format)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": augmented_query
                        }
                    ]
                }
            ]

            # Ensure temperature is in valid range (0.0, 1.0]
            # MiniMax requires temperature > 0.0 (exclusive)
            temperature = max(0.01, min(1.0, payload.temperature))
            if temperature != payload.temperature:
                logger.debug(f"Adjusted temperature from {payload.temperature} to {temperature} (MiniMax range: (0.0, 1.0])")

            # Make API call
            logger.debug(f"Calling MiniMax M2 via Anthropic SDK")
            message = self.client.messages.create(
                model=self.model,
                max_tokens=payload.max_tokens,
                system=payload.system if payload.system else "You are a helpful assistant.",
                messages=messages,
                temperature=temperature
            )

            # Extract thinking and text blocks
            thinking_content = []
            text_content = []

            for block in message.content:
                if block.type == "thinking":
                    thinking_content.append(block.thinking)
                    logger.debug(f"💭 Thinking block received: {block.thinking[:100]}...")
                elif block.type == "text":
                    text_content.append(block.text)

            # Combine text blocks
            response_text = "\n".join(text_content)
            
            # IMPORTANT: MiniMax often puts response in thinking block, not text block
            # If response_text is empty but thinking exists, use thinking as response
            if not response_text.strip() and thinking_content:
                response_text = "\n".join(thinking_content)
                logger.info(f"ℹ️  Using thinking content as response (no text block received)")

            # Log thinking if present
            if thinking_content:
                full_thinking = "\n".join(thinking_content)
                logger.info(f"💭 MiniMax M2 thinking process: {full_thinking[:200]}...")

            # Get token usage
            usage = {
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens,
                'total_tokens': message.usage.input_tokens + message.usage.output_tokens
            }

            # Update token meta
            token_meta.update(usage)

            # Log successful call
            logger.info(f"✅ MiniMax M2 response received ({usage['total_tokens']} tokens)")

            # Transform to RESPONSE_SCHEMA
            return self._transform_to_schema(response_text, usage, thinking_content, payload)

        except anthropic.APIError as e:
            logger.error(f"MiniMax API error: {e}")
            return AdapterError(
                code="api_error",
                message=f"MiniMax API error: {str(e)}",
                provider="minimax",
                recoverable=True,
                meta={'error_type': type(e).__name__}
            )
        except anthropic.APITimeoutError:
            return AdapterError(
                code="timeout",
                message=f"MiniMax API timed out after {self.timeout}s",
                provider="minimax",
                recoverable=True,
                meta={}
            )
        except Exception as e:
            logger.error(f"MinimaxAdapter error: {e}")
            return AdapterError(
                code="unknown",
                message=str(e),
                provider="minimax",
                recoverable=True,
                meta={'error_type': type(e).__name__}
            )

    def stream_call(self, payload: AdapterPayload) -> Any:
        """Execute streaming MiniMax M2 API call

        Args:
            payload: Adapter payload with query and context

        Yields:
            Streaming response chunks
        """
        logger.info(f"🤖 MinimaxAdapter (M2) streaming: {payload.user_query[:50]}...")

        # Phase 4: Snapshot support
        if payload.epistemic_snapshot:
            payload.epistemic_snapshot.increment_transfer_count()
            logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to [MiniMax-{self.model}]")

        try:
            # Get augmented prompt
            augmented_query = payload.get_augmented_prompt()

            # Build messages
            messages = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": augmented_query}]
                }
            ]

            # Ensure temperature is in valid range (0.0, 1.0]
            temperature = max(0.01, min(1.0, payload.temperature))

            # Create streaming response
            stream = self.client.messages.create(
                model=self.model,
                max_tokens=payload.max_tokens,
                system=payload.system if payload.system else "You are a helpful assistant.",
                messages=messages,
                temperature=temperature,
                stream=True
            )

            # Stream chunks
            for chunk in stream:
                if chunk.type == "content_block_start":
                    if hasattr(chunk, "content_block") and chunk.content_block:
                        if chunk.content_block.type == "text":
                            logger.debug("📝 Text block started")
                        elif chunk.content_block.type == "thinking":
                            logger.debug("💭 Thinking block started")

                elif chunk.type == "content_block_delta":
                    if hasattr(chunk, "delta") and chunk.delta:
                        if chunk.delta.type == "thinking_delta":
                            # Thinking content
                            yield {
                                'type': 'thinking',
                                'content': chunk.delta.thinking
                            }
                        elif chunk.delta.type == "text_delta":
                            # Text content
                            yield {
                                'type': 'text',
                                'content': chunk.delta.text
                            }

                elif chunk.type == "message_stop":
                    logger.info("✅ MiniMax M2 stream complete")
                    break

        except Exception as e:
            logger.error(f"MinimaxAdapter streaming error: {e}")
            yield {
                'type': 'error',
                'error': str(e)
            }
    
    def _transform_to_schema(self, response_text: str, usage: Dict, thinking: list, payload: AdapterPayload) -> AdapterResponse:
        """Transform MiniMax response to RESPONSE_SCHEMA
        
        Uses genuine epistemic extraction from thinking blocks (AI's internal reasoning).
        This is more accurate than heuristics because it reflects actual thought process.
        """
        
        # NEW: Extract genuine epistemic state from thinking blocks
        from empirica.plugins.modality_switcher.thinking_analyzer import (
            extract_from_thinking_semantically,
            extract_decision_from_thinking
        )
        
        # Extract epistemic vectors from thinking (genuine internal state)
        vector_references = extract_from_thinking_semantically(
            thinking_blocks=thinking if thinking else [],
            response_text=response_text,
            query=payload.user_query
        )
        
        # Get decision and confidence from vectors (based on onboarding guide logic)
        decision, confidence = extract_decision_from_thinking(
            thinking_blocks=thinking if thinking else [],
            response_text=response_text,
            vectors=vector_references
        )
        
        suggested_actions = [
            f"Execute based on MiniMax M2 response",
            "Validate output quality"
        ]
        
        if decision != "ACT":
            suggested_actions.insert(0, "Gather more context before proceeding")
        
        return AdapterResponse(
            decision=decision,
            confidence=confidence,
            rationale=f"MiniMax M2: {response_text[:100]}...",
            vector_references=vector_references,
            suggested_actions=suggested_actions,
            fallback_needed=False,
            provider_meta={
                'provider': 'minimax',
                'model': self.model,
                'raw_response_length': len(response_text),
                'response_preview': response_text[:500],
                'response_full': response_text,
                'thinking': "\n".join(thinking) if thinking else None,
                'usage': usage,
                'input_tokens': usage.get('input_tokens', 0),
                'output_tokens': usage.get('output_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0),
            }
        )


# For backwards compatibility, export as both MinimaxAdapter and MiniMaxAdapter
MiniMaxAdapter = MinimaxAdapter
