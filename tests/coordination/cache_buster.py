#!/usr/bin/env python3
"""
Cache Busting Helper for AI-Generated Code

Problem: External AI APIs (OpenAI, Anthropic, etc.) may cache file reads/writes,
causing AIs to get stale content even after files are updated locally.

Solution: This helper forces cache invalidation through multiple techniques:
1. Atomic write-and-replace (write to temp, then rename)
2. Content hashing with timestamp injection
3. Explicit cache-busting markers
4. File metadata manipulation

Usage:
    from cache_buster import CacheBuster
    
    cb = CacheBuster()
    
    # Write with cache busting
    cb.write_file('myfile.py', content)
    
    # Read with cache verification
    content = cb.read_file('myfile.py')
"""

import os
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Optional


class CacheBuster:
    """Helper to force cache invalidation for AI file operations"""
    
    def __init__(self, marker_prefix: str = "# CACHE_BUST"):
        self.marker_prefix = marker_prefix
        self.operation_count = 0
    
    def _generate_cache_marker(self) -> str:
        """Generate unique cache-busting marker"""
        timestamp = time.time()
        operation_id = self.operation_count
        self.operation_count += 1
        
        # Create unique marker with timestamp and operation counter
        marker = f"{self.marker_prefix}_{timestamp}_{operation_id}"
        return marker
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def write_file(
        self,
        filepath: str,
        content: str,
        add_marker: bool = True,
        atomic: bool = True
    ) -> dict:
        """
        Write file with cache-busting techniques
        
        Args:
            filepath: Target file path
            content: Content to write
            add_marker: Add cache-busting marker to content
            atomic: Use atomic write-and-replace
            
        Returns:
            dict with metadata (hash, marker, timestamp)
        """
        path = Path(filepath)
        timestamp = time.time()
        marker = self._generate_cache_marker()
        
        # Add cache-busting marker if requested
        if add_marker and not content.startswith(self.marker_prefix):
            # For Python files, add as comment at top
            if filepath.endswith('.py'):
                content = f"{marker}\n{content}"
            # For other files, add at end
            else:
                content = f"{content}\n{marker}\n"
        
        # Compute hash for verification
        content_hash = self._compute_content_hash(content)
        
        if atomic:
            # Atomic write: write to temp file, then rename
            # This forces filesystem cache invalidation
            temp_fd, temp_path = tempfile.mkstemp(
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp"
            )
            
            try:
                # Write to temp file
                with os.fdopen(temp_fd, 'w') as f:
                    f.write(content)
                
                # Force sync to disk
                os.sync()
                
                # Atomic rename (overwrites target)
                os.rename(temp_path, filepath)
                
            except Exception as e:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise e
        else:
            # Direct write
            path.write_text(content)
        
        # Touch file to update mtime (forces cache invalidation)
        os.utime(filepath, (timestamp, timestamp))
        
        return {
            'filepath': filepath,
            'hash': content_hash,
            'marker': marker,
            'timestamp': timestamp,
            'method': 'atomic' if atomic else 'direct'
        }
    
    def read_file(
        self,
        filepath: str,
        verify_marker: bool = False,
        expected_hash: Optional[str] = None
    ) -> tuple[str, dict]:
        """
        Read file with cache verification
        
        Args:
            filepath: File to read
            verify_marker: Check for cache-busting marker
            expected_hash: Expected content hash (for verification)
            
        Returns:
            (content, metadata) tuple
        """
        path = Path(filepath)
        
        # Force re-read by checking file stats first
        stat_info = os.stat(filepath)
        mtime = stat_info.st_mtime
        
        # Read content
        content = path.read_text()
        
        # Compute hash
        content_hash = self._compute_content_hash(content)
        
        # Check for marker
        has_marker = content.startswith(self.marker_prefix)
        
        # Extract marker if present
        marker = None
        if has_marker:
            first_line = content.split('\n')[0]
            if first_line.startswith(self.marker_prefix):
                marker = first_line
        
        metadata = {
            'filepath': filepath,
            'hash': content_hash,
            'has_marker': has_marker,
            'marker': marker,
            'mtime': mtime,
            'size': len(content)
        }
        
        # Verification
        if verify_marker and not has_marker:
            metadata['warning'] = 'Cache marker not found - may be cached read'
        
        if expected_hash and content_hash != expected_hash:
            metadata['warning'] = f'Hash mismatch - expected {expected_hash}, got {content_hash}'
        
        return content, metadata
    
    def update_file(
        self,
        filepath: str,
        find: str,
        replace: str,
        preserve_marker: bool = True
    ) -> dict:
        """
        Update file content with cache busting
        
        Args:
            filepath: File to update
            find: String to find
            replace: Replacement string
            preserve_marker: Keep existing cache marker
            
        Returns:
            dict with operation metadata
        """
        # Read current content
        content, read_meta = self.read_file(filepath)
        
        # Perform replacement
        new_content = content.replace(find, replace)
        
        # Check if anything changed
        if new_content == content:
            return {
                'changed': False,
                'message': 'No changes made'
            }
        
        # Write updated content
        write_meta = self.write_file(
            filepath,
            new_content,
            add_marker=not preserve_marker,  # Don't add new marker if preserving
            atomic=True
        )
        
        return {
            'changed': True,
            'old_hash': read_meta['hash'],
            'new_hash': write_meta['hash'],
            **write_meta
        }
    
    def force_refresh(self, filepath: str) -> dict:
        """
        Force cache refresh by touching file metadata
        
        This updates mtime without changing content,
        which can help invalidate external caches.
        """
        path = Path(filepath)
        timestamp = time.time()
        
        # Touch file with new timestamp
        os.utime(filepath, (timestamp, timestamp))
        
        # Read content to verify
        content, metadata = self.read_file(filepath)
        
        return {
            'filepath': filepath,
            'timestamp': timestamp,
            'mtime': metadata['mtime'],
            'hash': metadata['hash'],
            'method': 'metadata_touch'
        }


class AIFileBridge:
    """
    Bridge for AI-to-AI file communication with cache busting
    
    When one AI writes a file, another AI may get a cached version.
    This bridge ensures fresh reads by using cache-busting markers.
    """
    
    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace)
        self.buster = CacheBuster()
        self.message_log = []
    
    def ai_write(
        self,
        filepath: str,
        content: str,
        author: str = "unknown"
    ) -> str:
        """
        AI writes file with cache busting
        
        Returns: Message ID for tracking
        """
        full_path = self.workspace / filepath
        
        # Add metadata header
        metadata_header = f"""# Written by: {author}
# Timestamp: {time.time()}
# Message ID: {len(self.message_log)}

"""
        content_with_meta = metadata_header + content
        
        # Write with cache busting
        result = self.buster.write_file(str(full_path), content_with_meta)
        
        # Log message
        message = {
            'id': len(self.message_log),
            'author': author,
            'filepath': filepath,
            'hash': result['hash'],
            'timestamp': result['timestamp']
        }
        self.message_log.append(message)
        
        return f"Message {message['id']} written by {author}"
    
    def ai_read(
        self,
        filepath: str,
        reader: str = "unknown"
    ) -> tuple[str, dict]:
        """
        AI reads file with cache verification
        
        Returns: (content, metadata)
        """
        full_path = self.workspace / filepath
        
        # Force refresh before read
        self.buster.force_refresh(str(full_path))
        
        # Read with verification
        content, metadata = self.buster.read_file(str(full_path), verify_marker=True)
        
        # Extract author from metadata header
        lines = content.split('\n')
        author = "unknown"
        for line in lines[:5]:
            if line.startswith('# Written by:'):
                author = line.split(':', 1)[1].strip()
                break
        
        metadata['author'] = author
        metadata['reader'] = reader
        
        return content, metadata
    
    def verify_communication(self, filepath: str) -> dict:
        """
        Verify that file communication is working (not cached)
        
        Returns: Status dict with warnings if caching detected
        """
        full_path = self.workspace / filepath
        
        # Get current hash
        content1, meta1 = self.buster.read_file(str(full_path))
        hash1 = meta1['hash']
        
        # Force refresh
        self.buster.force_refresh(str(full_path))
        
        # Read again
        content2, meta2 = self.buster.read_file(str(full_path))
        hash2 = meta2['hash']
        
        # Check if hashes match (they should, content didn't change)
        if hash1 != hash2:
            return {
                'status': 'ERROR',
                'message': 'Content changed unexpectedly during verification'
            }
        
        # Check if mtime updated
        mtime_updated = meta2['mtime'] > meta1['mtime']
        
        return {
            'status': 'OK' if mtime_updated else 'WARNING',
            'message': 'Metadata refresh working' if mtime_updated else 'Metadata refresh may not invalidate cache',
            'hash': hash1,
            'mtime_changed': mtime_updated
        }


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cache_buster.py write <file> <content>")
        print("  python cache_buster.py read <file>")
        print("  python cache_buster.py refresh <file>")
        print("  python cache_buster.py update <file> <find> <replace>")
        sys.exit(1)
    
    command = sys.argv[1]
    cb = CacheBuster()
    
    if command == "write":
        filepath = sys.argv[2]
        content = sys.argv[3] if len(sys.argv) > 3 else "# Empty file\n"
        result = cb.write_file(filepath, content)
        print(f"✅ Written: {result}")
    
    elif command == "read":
        filepath = sys.argv[2]
        content, meta = cb.read_file(filepath, verify_marker=True)
        print(f"📖 Read: {meta}")
        print(f"Content preview: {content[:200]}...")
    
    elif command == "refresh":
        filepath = sys.argv[2]
        result = cb.force_refresh(filepath)
        print(f"🔄 Refreshed: {result}")
    
    elif command == "update":
        filepath = sys.argv[2]
        find = sys.argv[3]
        replace = sys.argv[4]
        result = cb.update_file(filepath, find, replace)
        print(f"✏️  Updated: {result}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
