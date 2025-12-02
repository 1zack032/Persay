"""
🧠 MENZA INTELLIGENCE ENGINE (MIE) - LITE
==========================================

Memory-optimized performance engine for Render free tier.

Key optimizations:
- Fixed-size data structures (no unbounded growth)
- LRU eviction for caches
- Minimal memory footprint (<10MB)
- Thread-safe operations

© 2024 Menza Technologies. All Rights Reserved.
"""

import time
import threading
from collections import OrderedDict
from typing import Dict, Optional, Any
from functools import wraps


class LRUCache:
    """Memory-bounded LRU cache"""
    
    def __init__(self, maxsize: int = 50):
        self.maxsize = maxsize
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                entry = self.cache[key]
                # Check TTL
                if entry['expires'] > time.time():
                    return entry['value']
                # Expired - remove it
                del self.cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int = 60):
        with self.lock:
            # Remove oldest if at capacity
            while len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
            
            self.cache[key] = {
                'value': value,
                'expires': time.time() + ttl
            }
    
    def clear(self):
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        return len(self.cache)


class MenzaIntelligenceEngine:
    """
    Lightweight performance optimization engine.
    
    Features:
    - Response caching with LRU eviction
    - Simple rate limiting
    - Request timing
    
    Memory: ~5MB max
    """
    
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
        
        # Small, bounded caches
        self._response_cache = LRUCache(maxsize=100)  # Route responses
        self._rate_limits: Dict[str, float] = {}  # user -> last_request_time
        self._rate_limit_lock = threading.Lock()
        
        # Simple metrics (fixed size)
        self._request_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
        
        self._initialized = True
        print("🧠 MIE Lite initialized (memory-optimized)", flush=True)
    
    def cache_response(self, key: str, value: Any, ttl: int = 60):
        """Cache a response with TTL"""
        self._response_cache.set(key, value, ttl)
    
    def get_cached_response(self, key: str) -> Optional[Any]:
        """Get cached response if valid"""
        result = self._response_cache.get(key)
        if result is not None:
            self._cache_hits += 1
        else:
            self._cache_misses += 1
        return result
    
    def check_rate_limit(self, user_id: str, min_interval: float = 0.1) -> bool:
        """
        Simple rate limiting.
        Returns True if request is allowed, False if rate limited.
        """
        now = time.time()
        
        with self._rate_limit_lock:
            last_request = self._rate_limits.get(user_id, 0)
            
            if now - last_request < min_interval:
                return False
            
            self._rate_limits[user_id] = now
            
            # Clean old entries (keep under 1000)
            if len(self._rate_limits) > 1000:
                cutoff = now - 60  # Remove entries older than 1 minute
                self._rate_limits = {
                    k: v for k, v in self._rate_limits.items() 
                    if v > cutoff
                }
        
        return True
    
    def record_request(self):
        """Record a request for metrics"""
        self._request_count += 1
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        total_cache = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_cache * 100) if total_cache > 0 else 0
        
        return {
            'total_requests': self._request_count,
            'cache_size': self._response_cache.size(),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': f"{hit_rate:.1f}%",
            'rate_limit_entries': len(self._rate_limits),
            'memory_status': 'optimized'
        }
    
    def clear_caches(self):
        """Clear all caches"""
        self._response_cache.clear()
        with self._rate_limit_lock:
            self._rate_limits.clear()
    
    # Compatibility methods (do nothing but don't break code)
    def register_connection(self, sid: str, user_id: str): pass
    def unregister_connection(self, sid: str): pass
    def update_user_activity(self, user_id: str, activity_type: str): pass
    def predict_user_activity(self, user_id: str): pass
    def apply_rate_limiting(self, user_id: str) -> bool: return True
    def optimize_connection(self, user_id: str): pass
    def process_bot_command(self, command: str, args: list, context: dict) -> Optional[str]: return None
    def add_to_queue(self, *args, **kwargs): pass
    def process_queue(self): pass
    def initialize(self): pass


# Global singleton
MIE = MenzaIntelligenceEngine()


# Convenience decorator for caching route responses
def cached_route(ttl: int = 60):
    """Decorator to cache route responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            cached = MIE.get_cached_response(cache_key)
            if cached is not None:
                return cached
            
            # Execute and cache
            result = func(*args, **kwargs)
            MIE.cache_response(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
