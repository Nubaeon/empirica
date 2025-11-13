#!/usr/bin/env python3
"""
🔍 Context Validation Module
Advanced context integrity checking and validation for AI systems
"""

from .context_validation import (
    InternalConsistencyToken,
    PersistentConsistencyToken,
    ContextDegradation,
    ContextIntegrityValidator
)

def create_context_validator():
    """Create a Context Integrity Validator instance"""
    return ContextIntegrityValidator()

__all__ = [
    'InternalConsistencyToken',
    'PersistentConsistencyToken',
    'ContextDegradation',
    'ContextIntegrityValidator',
    'create_context_validator'
]

__version__ = "1.0.0"
__component__ = "context_validation"
__purpose__ = "Context integrity checking and validation for AI systems"

print(f"🔍 Context validation ready for AI collaboration!")