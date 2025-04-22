"""
Version information for Canvas CLI
"""
# Default version if not set in setup.py
__version__ = "unknown"

# Try to get version from package metadata if installed
try:
    import importlib.metadata
    __version__ = importlib.metadata.version("canvas-cmd")
    
except ImportError:
    # If using older Python, keep default version
    pass
