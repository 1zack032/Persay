"""
🧠 MENZA INTELLIGENCE ENGINE - MINIMAL
=======================================
Ultra-lightweight version for stability.
"""

import time
import threading
from typing import Dict, Optional, Any
from functools import wraps


class MenzaIntelligenceEngine:
    """Minimal MIE - just basic caching, nothing fancy."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Simple dict cache - max 50 entries
        self._cache: Dict[str, dict] = {}
        self._max_cache = 50
        self._hits = 0
        self._misses = 0
        self._requests = 0
        
        self._initialized = True
        print("🧠 MIE ready", flush=True)
    
    def get_cached_response(self, key: str) -> Optional[Any]:
        """Get from cache"""
        entry = self._cache.get(key)
        if entry and entry['exp'] > time.time():
            self._hits += 1
            return entry['val']
        self._misses += 1
        return None
    
    def cache_response(self, key: str, value: Any, ttl: int = 60, priority: str = 'normal'):
        """Save to cache"""
        # Evict oldest if full
        if len(self._cache) >= self._max_cache:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k]['exp'])
            del self._cache[oldest]
        
        self._cache[key] = {'val': value, 'exp': time.time() + ttl}
    
    def invalidate_cache(self, pattern: str = None):
        """Clear cache"""
        if pattern:
            keys = [k for k in self._cache if pattern in k]
            for k in keys:
                del self._cache[k]
        else:
            self._cache.clear()
    
    def clear_caches(self):
        """Clear all"""
        self._cache.clear()
    
    def record_request(self):
        self._requests += 1
    
    def record_access(self, user_id: str, resource: str):
        pass  # No-op
    
    def predict_next_resources(self, user_id: str, current: str):
        return []  # No-op
    
    def check_rate_limit(self, user_id: str):
        return True, 0  # Always allow
    
    def get_rate_limit_info(self, user_id: str):
        return {'limit': 100, 'remaining': 100, 'reset': 0}
    
    def optimize_response(self, data: Any, fields=None):
        return data  # Return as-is
    
    def paginate_response(self, data, page=1, per_page=20):
        start = (page - 1) * per_page
        return {'data': data[start:start+per_page], 'pagination': {'page': page}}
    
    def get_stats(self) -> dict:
        total = self._hits + self._misses
        return {
            'cache_size': len(self._cache),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': f"{(self._hits/total*100):.0f}%" if total > 0 else "0%",
            'requests': self._requests
        }


# Global singleton
MIE = MenzaIntelligenceEngine()


# Simple decorators
def cached(ttl: int = 60, key_prefix: str = '', priority: str = 'normal'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{key_prefix or func.__name__}:{args}:{kwargs}"
            result = MIE.get_cached_response(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            MIE.cache_response(key, result, ttl)
            return result
        return wrapper
    return decorator


def rate_limited(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)  # No rate limiting for now
    return wrapper
