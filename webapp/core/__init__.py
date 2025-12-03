"""
🧠 Menza Core - Minimal
No heavy initialization on import.
"""

# Lazy imports - nothing runs on import
def get_engine():
    """Get MIE singleton (lazy)"""
    from .menza_intelligence_engine import MIE
    return MIE

def initialize_engine():
    """No-op for compatibility"""
    pass

def optimized(func):
    """No-op decorator for compatibility"""
    return func

__all__ = ['get_engine', 'initialize_engine', 'optimized']
