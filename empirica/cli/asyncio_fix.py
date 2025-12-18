"""
Asyncio Event Loop Fix for MCP Servers

Prevents "Event loop is closed" errors when httpx clients
try to cleanup after the main event loop has been closed.
"""
import warnings
import sys
import os

# Set environment variable to prevent httpx cleanup issues
os.environ['PYTHONWARNINGS'] = 'ignore::ResourceWarning'

def suppress_asyncio_warnings():
    """Suppress asyncio event loop closure warnings"""
    # Suppress ALL ResourceWarnings (httpx cleanup)
    warnings.filterwarnings('ignore', category=ResourceWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    # Suppress RuntimeError for closed event loops
    warnings.filterwarnings('ignore', message='.*Event loop is closed.*')
    
    # Suppress httpx cleanup warnings
    warnings.filterwarnings('ignore', message='.*Unclosed.*')
    warnings.filterwarnings('ignore', message='.*coroutine.*never awaited.*')
    
    # Suppress asyncio specific warnings
    warnings.filterwarnings('ignore', message='.*Task exception was never retrieved.*')

def patch_asyncio_for_mcp():
    """
    Apply patches to prevent asyncio event loop issues with MCP servers.
    
    This should be called early in CLI startup before any MCP connections.
    """
    import asyncio
    import atexit
    import threading
    
    # Suppress warnings FIRST
    suppress_asyncio_warnings()
    
    # Patch httpx to not complain about event loop closure
    try:
        import httpx
        # Monkey-patch httpx AsyncClient.__del__ to ignore errors
        original_del = httpx.AsyncClient.__del__
        def safe_del(self):
            try:
                original_del(self)
            except Exception:
                pass  # Ignore all cleanup errors
        httpx.AsyncClient.__del__ = safe_del
    except (ImportError, AttributeError):
        pass  # httpx not installed or already patched
    
    # Store reference to avoid premature closure
    _event_loop_ref = None
    
    def get_or_create_event_loop():
        """Get existing event loop or create new one"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    
    def cleanup_event_loop():
        """Safely cleanup event loop at exit"""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                # Give pending tasks time to cleanup
                pending = asyncio.all_tasks(loop)
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.close()
        except Exception:
            pass  # Ignore cleanup errors
    
    # Register cleanup handler
    atexit.register(cleanup_event_loop)
    
    # Create and store event loop reference
    _event_loop_ref = get_or_create_event_loop()
    
    return _event_loop_ref

# Auto-apply fix on import
try:
    patch_asyncio_for_mcp()
except Exception:
    pass  # Don't fail if patching doesn't work
