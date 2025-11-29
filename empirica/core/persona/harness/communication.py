"""
Persona-Sentinel Communication Protocol

Defines message types and communication between:
- PersonaHarness → SentinelOrchestrator
- SentinelOrchestrator → PersonaHarness

All messages are signed using Phase 2 AIIdentity for trust verification.
"""

import json
import logging
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in Persona-Sentinel communication"""

    # Sentinel → Persona
    TASK_ASSIGNMENT = "task_assignment"
    PROCEED_TO_ACT = "proceed_to_act"
    REQUEST_REASSESSMENT = "request_reassessment"
    TERMINATE = "terminate"

    # Persona → Sentinel
    STATUS_REPORT = "status_report"
    ESCALATION_REQUEST = "escalation_request"
    COMPLETION_REPORT = "completion_report"
    ERROR_REPORT = "error_report"


@dataclass
class SentinelMessage:
    """
    Message from SentinelOrchestrator to PersonaHarness

    Example:
        msg = SentinelMessage(
            message_type=MessageType.TASK_ASSIGNMENT,
            persona_id="security_expert",
            payload={
                "task": "Review authentication code for vulnerabilities",
                "priority": "high",
                "deadline_minutes": 30
            }
        )
    """
    message_type: MessageType
    persona_id: str
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: f"sent-{int(datetime.now(UTC).timestamp()*1000)}")
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    signature: Optional[str] = None  # EEP-1 signature

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for transmission"""
        return {
            'message_type': self.message_type.value,
            'persona_id': self.persona_id,
            'payload': self.payload,
            'message_id': self.message_id,
            'timestamp': self.timestamp,
            'signature': self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentinelMessage':
        """Parse from dictionary"""
        return cls(
            message_type=MessageType(data['message_type']),
            persona_id=data['persona_id'],
            payload=data['payload'],
            message_id=data.get('message_id', ''),
            timestamp=data.get('timestamp', ''),
            signature=data.get('signature')
        )

    def sign(self, identity) -> None:
        """
        Sign message using AIIdentity (Phase 2 integration)

        Args:
            identity: AIIdentity instance with loaded keypair
        """
        from empirica.core.identity.signature import sign_assessment
        import json

        # Create message content
        payload_dict = self.to_dict()
        payload_dict.pop('signature', None)  # Remove existing signature

        content = json.dumps(payload_dict, sort_keys=True)

        # Sign using EEP-1
        signed_payload = sign_assessment(
            content=content,
            epistemic_state={},  # Messages don't have epistemic state
            identity=identity,
            session_id=self.message_id
        )

        self.signature = signed_payload['signature']


@dataclass
class PersonaMessage:
    """
    Message from PersonaHarness to SentinelOrchestrator

    Example:
        msg = PersonaMessage(
            message_type=MessageType.STATUS_REPORT,
            persona_id="security_expert",
            payload={
                "phase": "CHECK",
                "confidence": 0.85,
                "findings": ["SQL injection risk in login.py:42"],
                "recommendation": "PROCEED_WITH_CAUTION"
            }
        )
    """
    message_type: MessageType
    persona_id: str
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: f"pers-{int(datetime.now(UTC).timestamp()*1000)}")
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    signature: Optional[str] = None  # EEP-1 signature

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for transmission"""
        return {
            'message_type': self.message_type.value,
            'persona_id': self.persona_id,
            'payload': self.payload,
            'message_id': self.message_id,
            'timestamp': self.timestamp,
            'signature': self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonaMessage':
        """Parse from dictionary"""
        return cls(
            message_type=MessageType(data['message_type']),
            persona_id=data['persona_id'],
            payload=data['payload'],
            message_id=data.get('message_id', ''),
            timestamp=data.get('timestamp', ''),
            signature=data.get('signature')
        )

    def sign(self, identity) -> None:
        """
        Sign message using AIIdentity (Phase 2 integration)

        Args:
            identity: AIIdentity instance with loaded keypair
        """
        from empirica.core.identity.signature import sign_assessment
        import json

        # Create message content
        payload_dict = self.to_dict()
        payload_dict.pop('signature', None)  # Remove existing signature

        content = json.dumps(payload_dict, sort_keys=True)

        # Sign using EEP-1
        signed_payload = sign_assessment(
            content=content,
            epistemic_state={},  # Messages don't have epistemic state
            identity=identity,
            session_id=self.message_id
        )

        self.signature = signed_payload['signature']


def send_message(message, transport="file", destination=".empirica/messages"):
    """
    Send message via transport mechanism

    Args:
        message: SentinelMessage or PersonaMessage
        transport: Transport type ("file", "redis", "grpc")
        destination: Destination path/address

    Returns:
        bool: True if sent successfully
    """
    try:
        if transport == "file":
            # File-based transport for MVP
            from pathlib import Path

            msg_dir = Path(destination)
            msg_dir.mkdir(parents=True, exist_ok=True)

            # Determine subdirectory based on message type
            if isinstance(message, SentinelMessage):
                subdir = msg_dir / "to_personas" / message.persona_id
            else:
                subdir = msg_dir / "to_sentinel" / message.persona_id

            subdir.mkdir(parents=True, exist_ok=True)

            # Write message to file
            msg_file = subdir / f"{message.message_id}.json"
            with open(msg_file, 'w') as f:
                json.dump(message.to_dict(), f, indent=2)

            logger.debug(f"✓ Message sent: {msg_file}")
            return True

        elif transport == "redis":
            # Redis pub/sub transport (future)
            raise NotImplementedError("Redis transport not yet implemented")

        elif transport == "grpc":
            # gRPC transport (future)
            raise NotImplementedError("gRPC transport not yet implemented")

        else:
            raise ValueError(f"Unknown transport: {transport}")

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False


def receive_message(persona_id, transport="file", source=".empirica/messages", timeout=None):
    """
    Receive message for persona

    Args:
        persona_id: Persona identifier
        transport: Transport type ("file", "redis", "grpc")
        source: Source path/address
        timeout: Timeout in seconds (None = non-blocking)

    Returns:
        SentinelMessage or None
    """
    try:
        if transport == "file":
            # File-based transport for MVP
            from pathlib import Path
            import time

            msg_dir = Path(source) / "to_personas" / persona_id

            if not msg_dir.exists():
                return None

            start_time = time.time()

            while True:
                # Get all message files
                msg_files = sorted(msg_dir.glob("*.json"))

                if msg_files:
                    # Read oldest message
                    msg_file = msg_files[0]

                    with open(msg_file, 'r') as f:
                        msg_data = json.load(f)

                    # Delete file (consumed)
                    msg_file.unlink()

                    logger.debug(f"✓ Message received: {msg_file.name}")
                    return SentinelMessage.from_dict(msg_data)

                # Check timeout
                if timeout is None:
                    return None  # Non-blocking

                if time.time() - start_time > timeout:
                    return None  # Timeout

                # Wait a bit before checking again
                time.sleep(0.1)

        elif transport == "redis":
            # Redis pub/sub transport (future)
            raise NotImplementedError("Redis transport not yet implemented")

        elif transport == "grpc":
            # gRPC transport (future)
            raise NotImplementedError("gRPC transport not yet implemented")

        else:
            raise ValueError(f"Unknown transport: {transport}")

    except Exception as e:
        logger.error(f"Failed to receive message: {e}")
        return None
