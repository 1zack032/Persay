"""
🧠 Menza Core - Intelligence Engine (Lite)

Memory-optimized algorithms that power Menza's performance.
"""

from .menza_intelligence_engine import MenzaIntelligenceEngine, MIE, LRUCache

# Compatibility exports
def get_engine():
    """Get the MIE singleton"""
    return MIE

def initialize_engine():
    """Initialize MIE (already done on import)"""
    return MIE

def optimized(func):
    """Decorator for optimized functions (no-op for compatibility)"""
    return func

__all__ = [
    'MenzaIntelligenceEngine',
    'MIE',
    'LRUCache',
    'get_engine',
    'initialize_engine',
    'optimized'
]
