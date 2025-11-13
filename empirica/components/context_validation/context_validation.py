#!/usr/bin/env python3
"""
🔍 Context Validation Module
Advanced context integrity checking and validation for AI systems

This module provides comprehensive context validation capabilities including:
- Internal Consistency Tokens (ICT) for AI belief tracking
- Persistent Consistency Tokens (PCT) for reality verification
- Context degradation detection and notification
- Background verification with cryptographic signing
"""

import threading
import time
import hashlib
from queue import Queue
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import os

@dataclass
class InternalConsistencyToken:
    """Internal Consistency Token - AI's belief about file content"""
    content_hash: str
    read_timestamp: float
    ai_session_id: str
    generation_time: float
    file_path: str
    sequence_number: int
    signature: bytes

@dataclass
class PersistentConsistencyToken:
    """Persistent Consistency Token - Actual file reality"""
    file_path: str
    actual_hash: str
    actual_timestamp: float
    verification_time: float
    file_size: int
    
    @classmethod
    def from_file(cls, file_path: str) -> 'PersistentConsistencyToken':
        """Generate PCT by actually reading file from disk"""
        try:
            stat = os.stat(file_path)
            with open(file_path, 'rb') as f:
                content = f.read()
                actual_hash = hashlib.sha256(content).hexdigest()
            
            return cls(
                file_path=file_path,
                actual_hash=actual_hash,
                actual_timestamp=stat.st_mtime,
                verification_time=time.time(),
                file_size=stat.st_size
            )
        except FileNotFoundError:
            return cls(
                file_path=file_path,
                actual_hash="FILE_NOT_FOUND",
                actual_timestamp=0,
                verification_time=time.time(),
                file_size=0
            )
        except Exception as e:
            return cls(
                file_path=file_path,
                actual_hash=f"ERROR: {str(e)}",
                actual_timestamp=0,
                verification_time=time.time(),
                file_size=0
            )

@dataclass
class ContextDegradation:
    """Information about detected context degradation"""
    file_path: str
    degradation_type: str
    severity: str
    ict_hash: str
    pct_hash: str
    confidence: float
    recommendation: str

class ContextIntegrityValidator:
    """
    Main Context Integrity Validation system
    
    Provides real-time context validation with cryptographic signing,
    background verification, and degradation detection.
    """
    
    def __init__(self):
        """Initialize the Context Integrity Validator"""
        self.ict_store: Dict[str, InternalConsistencyToken] = {}
        self.pct_store: Dict[str, PersistentConsistencyToken] = {}
        self.verification_queue = Queue()
        self.degradation_callbacks = []
        self.session_id = f"session_{int(time.time())}"
        self.sequence_counter = 0
        
        # Generate RSA key pair for cryptographic signing
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
        # Background verification thread
        self.verification_thread = threading.Thread(
            target=self._background_verification_loop,
            daemon=True
        )
        self.verification_thread.start()
        
        # Critical files that get immediate verification
        self.critical_files = {
            'start_octopus_consciousness.sh',
            'src/digital_feet.py',
            'DOI_CORE/src/doi/__init__.py',
            'OCTOPUS_COGNITIVE_WORKSPACE_MAP.md'
        }
    
    def validate_file_read(self, file_path: str, content: str) -> InternalConsistencyToken:
        """
        AI reads file - generate ICT immediately (fast path)
        
        Args:
            file_path (str): Path to the file being read
            content (str): Content of the file
            
        Returns:
            InternalConsistencyToken: ICT representing AI's belief about the file
        """
        # Generate ICT with minimal overhead (~1ms)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        self.sequence_counter += 1
        
        # Use consistent timestamp for both signing and storage
        timestamp = time.time()
        
        # Create message to be signed
        message = f"{content_hash}:{timestamp}:{self.session_id}:{self.sequence_counter}:{file_path}".encode('utf-8')
        
        # Sign the message
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        ict = InternalConsistencyToken(
            content_hash=content_hash,
            read_timestamp=timestamp,
            ai_session_id=self.session_id,
            generation_time=timestamp,
            file_path=file_path,
            sequence_number=self.sequence_counter,
            signature=signature
        )
        
        # Store ICT for later verification
        self.ict_store[file_path] = ict
        
        # Schedule background verification
        self._schedule_verification(file_path, ict)
        
        return ict
    
    def _schedule_verification(self, file_path: str, ict: InternalConsistencyToken):
        """Schedule background PCT verification"""
        # Critical files get immediate verification
        if any(critical in file_path for critical in self.critical_files):
            priority = 'high'
        else:
            priority = 'normal'
        
        self.verification_queue.put({
            'file_path': file_path,
            'ict': ict,
            'priority': priority,
            'scheduled_time': time.time()
        })
    
    def _background_verification_loop(self):
        """Background thread that performs PCT verification"""
        while True:
            try:
                # Get verification task
                task = self.verification_queue.get(timeout=1.0)
                
                # Generate authoritative PCT (10-100ms)
                pct = PersistentConsistencyToken.from_file(task['file_path'])
                self.pct_store[task['file_path']] = pct
                
                # Compare ICT vs PCT
                degradation = self._detect_context_degradation(task['ict'], pct)
                
                if degradation:
                    # Alert AI about context mismatch
                    self._notify_degradation(degradation)
                
                self.verification_queue.task_done()
            
            except Exception as e:
                # Continue verification loop even if individual verification fails
                continue
    
    def _detect_context_degradation(self, ict: InternalConsistencyToken, pct: PersistentConsistencyToken) -> Optional[ContextDegradation]:
        """Compare ICT vs PCT to detect degradation"""
        # Verify ICT signature
        message = f"{ict.content_hash}:{ict.read_timestamp}:{ict.ai_session_id}:{ict.sequence_number}:{ict.file_path}".encode('utf-8')
        try:
            self.public_key.verify(
                ict.signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except Exception:
            return ContextDegradation(
                file_path=ict.file_path,
                degradation_type='invalid_signature',
                severity='high',
                ict_hash=ict.content_hash,
                pct_hash=pct.actual_hash,
                confidence=1.0,
                recommendation='ict_signature_mismatch'
            )
        
        # File missing
        if pct.actual_hash == "FILE_NOT_FOUND":
            return ContextDegradation(
                file_path=ict.file_path,
                degradation_type='file_missing',
                severity='high',
                ict_hash=ict.content_hash,
                pct_hash=pct.actual_hash,
                confidence=1.0,
                recommendation='file_missing_alert'
            )
        
        # Content completely different
        if ict.content_hash != pct.actual_hash:
            return ContextDegradation(
                file_path=ict.file_path,
                degradation_type='content_mismatch',
                severity='high',
                ict_hash=ict.content_hash,
                pct_hash=pct.actual_hash,
                confidence=0.9,
                recommendation='refresh_cache_and_reread'
            )
        
        # Timestamp mismatch (file modified after AI read it)
        if ict.read_timestamp < pct.actual_timestamp:
            return ContextDegradation(
                file_path=ict.file_path,
                degradation_type='timestamp_mismatch',
                severity='medium',
                ict_hash=ict.content_hash,
                pct_hash=pct.actual_hash,
                confidence=0.7,
                recommendation='check_for_updates'
            )
        
        # ICT getting old
        ict_age = time.time() - ict.generation_time
        if ict_age > 3600:  # 1 hour
            return ContextDegradation(
                file_path=ict.file_path,
                degradation_type='stale_ict',
                severity='low',
                ict_hash=ict.content_hash,
                pct_hash=pct.actual_hash,
                confidence=0.5,
                recommendation='refresh_when_convenient'
            )
        
        return None
    
    def _notify_degradation(self, degradation: ContextDegradation):
        """Notify AI about context degradation"""
        degradation_report = {
            'file': degradation.file_path,
            'issue': degradation.degradation_type,
            'severity': degradation.severity,
            'recommendation': degradation.recommendation,
            'confidence': degradation.confidence,
            'ict_hash': degradation.ict_hash,
            'pct_hash': degradation.pct_hash,
            'timestamp': time.time()
        }
        
        # Call registered callbacks
        for callback in self.degradation_callbacks:
            try:
                callback(degradation_report)
            except Exception as e:
                print(f"⚠️ Degradation callback error: {e}")
        
        # Default logging
        print(f"🚨 CONTEXT DEGRADATION DETECTED:")
        print(f"   File: {degradation.file_path}")
        print(f"   Issue: {degradation.degradation_type}")
        print(f"   Severity: {degradation.severity}")
        print(f"   Recommendation: {degradation.recommendation}")
    
    def register_degradation_callback(self, callback):
        """Register callback for degradation notifications"""
        self.degradation_callbacks.append(callback)
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status"""
        return {
            'ict_tokens': len(self.ict_store),
            'pct_tokens': len(self.pct_store),
            'pending_verifications': self.verification_queue.qsize(),
            'session_id': self.session_id,
            'critical_files': list(self.critical_files),
            'files_tracked': list(self.ict_store.keys())
        }
    
    def force_verification(self, file_path: str) -> Optional[ContextDegradation]:
        """Force immediate verification of a specific file"""
        if file_path not in self.ict_store:
            print(f"⚠️ No ICT found for {file_path}")
            return None
        
        ict = self.ict_store[file_path]
        pct = PersistentConsistencyToken.from_file(file_path)
        self.pct_store[file_path] = pct
        
        return self._detect_context_degradation(ict, pct)
