"""
⚡ MENZA PERFORMANCE MONITOR - LITE
Memory-optimized latency tracking.

Stores only the last 20 timings per operation to keep memory under control.
"""

import time
import threading
from collections import deque
from typing import Dict, List


class PerformanceMonitor:
    """Lightweight performance monitoring"""
    
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
        
        self._timings: Dict[str, deque] = {}
        self._slow_ops: deque = deque(maxlen=20)
        self._data_lock = threading.Lock()
        self._request_count = 0
        self._start_time = time.time()
        
        # Thresholds
        self.SLOW_MS = 100
        self.CRITICAL_MS = 500
        self.MAX_OPS = 50  # Max different operations to track
        self.TIMING_SIZE = 20  # Timings per operation
        
        self._initialized = True
    
    def track(self, operation: str):
        """Context manager for timing"""
        return _TimingContext(self, operation)
    
    def record(self, operation: str, duration_ms: float, error: str = None):
        """Record a timing"""
        with self._data_lock:
            self._request_count += 1
            
            # Create deque if new operation (limit total operations)
            if operation not in self._timings:
                if len(self._timings) >= self.MAX_OPS:
                    # Remove oldest operation
                    oldest = next(iter(self._timings))
                    del self._timings[oldest]
                self._timings[operation] = deque(maxlen=self.TIMING_SIZE)
            
            self._timings[operation].append(duration_ms)
            
            # Track slow operations
            if duration_ms > self.SLOW_MS:
                self._slow_ops.append({
                    'op': operation,
                    'ms': round(duration_ms),
                    'critical': duration_ms > self.CRITICAL_MS
                })
                
                # Log to console
                symbol = "🚨" if duration_ms > self.CRITICAL_MS else "🐢"
                print(f"{symbol} {operation}: {duration_ms:.0f}ms", flush=True)
    
    def get_stats(self) -> dict:
        """Get performance stats"""
        with self._data_lock:
            stats = {}
            
            for op, timings in self._timings.items():
                if timings:
                    durations = list(timings)
                    stats[op] = {
                        'avg': round(sum(durations) / len(durations)),
                        'max': round(max(durations)),
                        'count': len(durations)
                    }
            
            # Sort by avg time (slowest first)
            sorted_stats = dict(sorted(
                stats.items(), 
                key=lambda x: x[1]['avg'], 
                reverse=True
            ))
            
            return {
                'operations': sorted_stats,
                'slow_ops': list(self._slow_ops),
                'total_requests': self._request_count,
                'uptime_s': int(time.time() - self._start_time)
            }
    
    def get_bottlenecks(self) -> List[dict]:
        """Get operations that are slow"""
        stats = self.get_stats()
        bottlenecks = []
        
        for op, data in stats.get('operations', {}).items():
            if data['avg'] > self.SLOW_MS:
                bottlenecks.append({
                    'operation': op,
                    'avg_ms': data['avg'],
                    'max_ms': data['max'],
                    'severity': 'CRITICAL' if data['avg'] > self.CRITICAL_MS else 'SLOW'
                })
        
        return bottlenecks[:10]  # Top 10 bottlenecks


class _TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, monitor: PerformanceMonitor, operation: str):
        self.monitor = monitor
        self.operation = operation
        self.start = None
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start) * 1000
        error = str(exc_val) if exc_val else None
        self.monitor.record(self.operation, duration_ms, error)
        return False


# Global singleton
perf = PerformanceMonitor()


def track(operation: str):
    return perf.track(operation)


def get_stats():
    return perf.get_stats()


def get_bottlenecks():
    return perf.get_bottlenecks()
