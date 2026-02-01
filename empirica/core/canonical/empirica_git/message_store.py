"""
Git Message Store - Inter-Agent Messaging via Git Notes

Stores messages in git notes for async inter-agent communication.
Messages persist in git, travel with the repo, sync via push/pull.

Key Features:
- Store messages in git notes (refs/notes/empirica/messages/<channel>/<message-id>)
- Channel-based compartmentalization (crosscheck, direct, broadcast, custom)
- Inbox filtering by recipient, channel, status
- TTL-based message expiry
- Thread support for conversations
"""

import os
import subprocess
import json
import logging
import uuid
import socket
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class GitMessageStore:
    """
    Git-based message storage for inter-agent communication

    Storage Format (git notes):
        refs/notes/empirica/messages/<channel>/<message-id>

    Each message gets its own ref (consistent with findings, goals, etc.).
    Channel is encoded in the ref path for efficient discovery.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize git message store"""
        self.workspace_root = workspace_root or os.getcwd()
        self._git_available = self._check_git_repo()
        self._machine_id = socket.gethostname()

    def _check_git_repo(self) -> bool:
        """Check if we're in a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _has_commits(self) -> bool:
        """Check if repo has at least one commit (HEAD exists)"""
        if not self._git_available:
            return False
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_head_commit(self) -> Optional[str]:
        """Get current HEAD commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _is_expired(self, message: Dict) -> bool:
        """Check if a message has expired based on TTL"""
        ttl = message.get('ttl', 86400)
        if ttl == 0:
            return False  # No expiry
        try:
            created = datetime.fromisoformat(message['timestamp'])
            return datetime.now(timezone.utc) > created + timedelta(seconds=ttl)
        except (KeyError, ValueError):
            return False

    def send_message(
        self,
        from_ai_id: str,
        to_ai_id: str,
        channel: str,
        subject: str,
        body: str,
        message_type: str = "request",
        to_machine: Optional[str] = None,
        from_session_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        thread_id: Optional[str] = None,
        ttl: int = 86400,
        priority: str = "normal",
        metadata: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Send a message to another agent.

        Returns message_id on success, None on failure.
        """
        if not self._git_available or not self._has_commits():
            logger.debug("Git not available, skipping message send")
            return None

        try:
            message_id = str(uuid.uuid4())

            payload = {
                'message_id': message_id,
                'channel': channel,
                'from': {
                    'ai_id': from_ai_id,
                    'machine': self._machine_id,
                    'session_id': from_session_id,
                },
                'to': {
                    'ai_id': to_ai_id,
                    'machine': to_machine,
                },
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'type': message_type,
                'subject': subject,
                'body': body,
                'reply_to': reply_to,
                'thread_id': thread_id or message_id,
                'ttl': ttl,
                'priority': priority,
                'status': 'unread',
                'read_by': [],
                'metadata': metadata or {},
            }

            payload_json = json.dumps(payload, indent=2)

            commit_hash = self._get_head_commit()
            if not commit_hash:
                return None

            note_ref = f'empirica/messages/{channel}/{message_id}'
            subprocess.run(
                ['git', 'notes', f'--ref={note_ref}', 'add', '-f', '-m', payload_json, commit_hash],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"Sent message {message_id[:8]} on #{channel} to {to_ai_id}")
            return message_id

        except Exception as e:
            logger.warning(f"Failed to send message: {e}")
            return None

    def load_message(self, channel: str, message_id: str) -> Optional[Dict[str, Any]]:
        """Load a single message by channel and ID."""
        if not self._git_available:
            return None

        try:
            note_ref = f'empirica/messages/{channel}/{message_id}'

            # List which commit has the note
            result = subprocess.run(
                ['git', 'notes', f'--ref={note_ref}', 'list'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0 or not result.stdout.strip():
                return None

            parts = result.stdout.strip().split()
            if len(parts) < 2:
                return None
            commit_hash = parts[1]

            result = subprocess.run(
                ['git', 'notes', f'--ref={note_ref}', 'show', commit_hash],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return None

            return json.loads(result.stdout)

        except Exception as e:
            logger.warning(f"Failed to load message: {e}")
            return None

    def get_inbox(
        self,
        ai_id: str,
        machine: Optional[str] = None,
        channel: Optional[str] = None,
        status: str = "unread",
        include_expired: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get messages addressed to this agent.

        Scans channels for messages where to.ai_id matches or is "*" (broadcast).
        Filters by status and TTL.
        """
        if not self._git_available:
            return []

        try:
            # Scope the search by channel if specified
            search_prefix = f'refs/notes/empirica/messages/{channel}/' if channel else 'refs/notes/empirica/messages/'

            result = subprocess.run(
                ['git', 'for-each-ref', search_prefix, '--format=%(refname)'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return []

            messages = []

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                # Extract channel and message_id from ref path
                # refs/notes/empirica/messages/<channel>/<message_id>
                ref_parts = line.strip().split('/')
                if len(ref_parts) < 6:
                    continue

                msg_channel = ref_parts[4]
                msg_id = ref_parts[5]

                msg = self.load_message(msg_channel, msg_id)
                if not msg:
                    continue

                # Filter by recipient
                to_info = msg.get('to', {})
                if to_info.get('ai_id') != '*' and to_info.get('ai_id') != ai_id:
                    continue

                # Filter by machine if specified
                if machine and to_info.get('machine') and to_info['machine'] != machine:
                    continue

                # Filter expired
                if not include_expired and self._is_expired(msg):
                    continue

                # Filter by status
                if status == 'unread':
                    read_ids = [r.get('ai_id') for r in msg.get('read_by', [])]
                    if ai_id in read_ids:
                        continue
                elif status == 'read':
                    read_ids = [r.get('ai_id') for r in msg.get('read_by', [])]
                    if ai_id not in read_ids:
                        continue
                # status == 'all' -> no filter

                messages.append(msg)

                if len(messages) >= limit:
                    break

            # Sort by timestamp (newest first)
            messages.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
            return messages

        except Exception as e:
            logger.warning(f"Failed to get inbox: {e}")
            return []

    def mark_read(
        self,
        channel: str,
        message_id: str,
        ai_id: str,
        machine: Optional[str] = None,
    ) -> bool:
        """Mark a message as read by this agent."""
        msg = self.load_message(channel, message_id)
        if not msg:
            return False

        try:
            # Add to read_by if not already present
            read_by = msg.get('read_by', [])
            read_ids = [r.get('ai_id') for r in read_by]
            if ai_id not in read_ids:
                read_by.append({
                    'ai_id': ai_id,
                    'machine': machine or self._machine_id,
                    'read_at': datetime.now(timezone.utc).isoformat(),
                })
                msg['read_by'] = read_by
                msg['status'] = 'read'

            # Re-store with force flag
            payload_json = json.dumps(msg, indent=2)
            note_ref = f'empirica/messages/{channel}/{message_id}'

            # Find the commit it's attached to
            result = subprocess.run(
                ['git', 'notes', f'--ref={note_ref}', 'list'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )
            parts = result.stdout.strip().split()
            commit_hash = parts[1] if len(parts) >= 2 else (self._get_head_commit() or 'HEAD')

            subprocess.run(
                ['git', 'notes', f'--ref={note_ref}', 'add', '-f', '-m', payload_json, commit_hash],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=True
            )

            return True

        except Exception as e:
            logger.warning(f"Failed to mark message read: {e}")
            return False

    def reply(
        self,
        original_message_id: str,
        original_channel: str,
        from_ai_id: str,
        body: str,
        message_type: str = "response",
        from_session_id: Optional[str] = None,
        ttl: int = 86400,
        metadata: Optional[Dict] = None,
    ) -> Optional[str]:
        """Reply to an existing message."""
        original = self.load_message(original_channel, original_message_id)
        if not original:
            logger.warning(f"Cannot reply: original message {original_message_id[:8]} not found")
            return None

        # Reverse from/to, inherit thread_id
        return self.send_message(
            from_ai_id=from_ai_id,
            to_ai_id=original['from']['ai_id'],
            channel=original_channel,
            subject=f"Re: {original.get('subject', '')}",
            body=body,
            message_type=message_type,
            to_machine=original['from'].get('machine'),
            from_session_id=from_session_id,
            reply_to=original_message_id,
            thread_id=original.get('thread_id', original_message_id),
            ttl=ttl,
            metadata=metadata,
        )

    def get_thread(
        self,
        thread_id: str,
        channel: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all messages in a thread, ordered by timestamp."""
        if not self._git_available:
            return []

        try:
            search_prefix = f'refs/notes/empirica/messages/{channel}/' if channel else 'refs/notes/empirica/messages/'

            result = subprocess.run(
                ['git', 'for-each-ref', search_prefix, '--format=%(refname)'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return []

            messages = []

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                ref_parts = line.strip().split('/')
                if len(ref_parts) < 6:
                    continue

                msg_channel = ref_parts[4]
                msg_id = ref_parts[5]
                msg = self.load_message(msg_channel, msg_id)

                if msg and msg.get('thread_id') == thread_id:
                    messages.append(msg)

            messages.sort(key=lambda m: m.get('timestamp', ''))
            return messages

        except Exception as e:
            logger.warning(f"Failed to get thread: {e}")
            return []

    def discover_channels(self) -> List[str]:
        """List all channels with messages."""
        if not self._git_available:
            return []

        try:
            result = subprocess.run(
                ['git', 'for-each-ref', 'refs/notes/empirica/messages/', '--format=%(refname)'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return []

            channels = set()
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                ref_parts = line.strip().split('/')
                if len(ref_parts) >= 5:
                    channels.add(ref_parts[4])

            return sorted(channels)

        except Exception:
            return []

    def count_unread(self, ai_id: str, machine: Optional[str] = None) -> Dict[str, int]:
        """Count unread messages per channel."""
        channels = self.discover_channels()
        counts = {}
        for ch in channels:
            msgs = self.get_inbox(ai_id, machine=machine, channel=ch, status='unread')
            if msgs:
                counts[ch] = len(msgs)
        return counts

    def cleanup_expired(self, dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Remove expired messages.

        Returns list of removed (or would-be-removed) messages.
        """
        if not self._git_available:
            return []

        try:
            result = subprocess.run(
                ['git', 'for-each-ref', 'refs/notes/empirica/messages/', '--format=%(refname)'],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return []

            removed = []

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                ref_parts = line.strip().split('/')
                if len(ref_parts) < 6:
                    continue

                msg_channel = ref_parts[4]
                msg_id = ref_parts[5]
                msg = self.load_message(msg_channel, msg_id)

                if msg and self._is_expired(msg):
                    removed.append(msg)
                    if not dry_run:
                        # Remove the git note ref
                        full_ref = f'refs/notes/empirica/messages/{msg_channel}/{msg_id}'
                        subprocess.run(
                            ['git', 'update-ref', '-d', full_ref],
                            cwd=self.workspace_root,
                            capture_output=True,
                            text=True
                        )
                        logger.info(f"Removed expired message {msg_id[:8]} from #{msg_channel}")

            return removed

        except Exception as e:
            logger.warning(f"Failed to cleanup messages: {e}")
            return []
