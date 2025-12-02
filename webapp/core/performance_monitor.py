"""
⚡ MENZA PERFORMANCE MONITOR
Real-time latency tracking and bottleneck detection.

This module tracks timing for:
- Every database operation
- Every route request
- Every socket event
- MongoDB connection health

Usage:
    from webapp.core.performance_monitor import perf
    
    with perf.track('operation_name'):
        # your code here
        
    # Or as decorator
    @perf.timed('my_function')
    def my_function():
        pass
"""

import time
import threading
from collections import defaultdict, deque
from functools import wraps
from typing import Dict, List, Optional
import os

# Enable/disable via environment
DEBUG_PERF = os.environ.get('DEBUG_PERF', 'true').lower() == 'true'


class PerformanceMonitor:
    """Centralized performance monitoring for Menza"""
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # Store last 100 timings per operation
        self._timings: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Track slow operations (>100ms)
        self._slow_ops: deque = deque(maxlen=50)
        
        # Track errors
        self._errors: deque = deque(maxlen=50)
        
        # Thresholds (ms)
        self.SLOW_THRESHOLD = 100  # Log if >100ms
        self.CRITICAL_THRESHOLD = 500  # Alert if >500ms
        
        # Request counter
        self._request_count = 0
        self._start_time = time.time()
    
    def track(self, operation: str):
        """Context manager to track operation timing"""
        return _TimingContext(self, operation)
    
    def timed(self, operation: str):
        """Decorator to time a function"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.track(operation):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def record(self, operation: str, duration_ms: float, success: bool = True, error: str = None):
        """Record a timing measurement"""
        with self._lock:
            self._timings[operation].append({
                'duration_ms': duration_ms,
                'timestamp': time.time(),
                'success': success
            })
            
            self._request_count += 1
            
            # Log slow operations
            if duration_ms > self.SLOW_THRESHOLD:
                entry = {
                    'operation': operation,
                    'duration_ms': duration_ms,
                    'timestamp': time.time(),
                    'critical': duration_ms > self.CRITICAL_THRESHOLD
                }
                self._slow_ops.append(entry)
                
                # Print to console for immediate visibility
                symbol = "🚨" if duration_ms > self.CRITICAL_THRESHOLD else "🐢"
                print(f"{symbol} SLOW: {operation} took {duration_ms:.0f}ms", flush=True)
            
            if error:
                self._errors.append({
                    'operation': operation,
                    'error': error,
                    'timestamp': time.time()
                })
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        with self._lock:
            stats = {}
            
            for op, timings in self._timings.items():
                if not timings:
                    continue
                
                durations = [t['duration_ms'] for t in timings]
                stats[op] = {
                    'count': len(durations),
                    'avg_ms': sum(durations) / len(durations),
                    'min_ms': min(durations),
                    'max_ms': max(durations),
                    'last_ms': durations[-1] if durations else 0
                }
            
            # Sort by avg time (slowest first)
            sorted_stats = dict(sorted(
                stats.items(), 
                key=lambda x: x[1]['avg_ms'], 
                reverse=True
            ))
            
            return {
                'operations': sorted_stats,
                'slow_operations': list(self._slow_ops),
                'errors': list(self._errors),
                'total_requests': self._request_count,
                'uptime_seconds': int(time.time() - self._start_time)
            }
    
    def get_bottlenecks(self) -> List[dict]:
        """Identify the top bottlenecks"""
        stats = self.get_stats()
        bottlenecks = []
        
        for op, data in stats.get('operations', {}).items():
            if data['avg_ms'] > self.SLOW_THRESHOLD:
                bottlenecks.append({
                    'operation': op,
                    'avg_ms': round(data['avg_ms'], 1),
                    'max_ms': round(data['max_ms'], 1),
                    'count': data['count'],
                    'severity': 'CRITICAL' if data['avg_ms'] > self.CRITICAL_THRESHOLD else 'SLOW'
                })
        
        return sorted(bottlenecks, key=lambda x: x['avg_ms'], reverse=True)
    
    def clear(self):
        """Clear all recorded data"""
        with self._lock:
            self._timings.clear()
            self._slow_ops.clear()
            self._errors.clear()


class _TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, monitor: PerformanceMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        error = str(exc_val) if exc_val else None
        self.monitor.record(
            self.operation, 
            duration_ms, 
            success=(exc_type is None),
            error=error
        )
        return False  # Don't suppress exceptions


# Global instance
perf = PerformanceMonitor()


# Convenience functions
def track(operation: str):
    """Track an operation's timing"""
    return perf.track(operation)


def timed(operation: str):
    """Decorator to time a function"""
    return perf.timed(operation)


def get_stats():
    """Get performance statistics"""
    return perf.get_stats()


def get_bottlenecks():
    """Get identified bottlenecks"""
    return perf.get_bottlenecks()

