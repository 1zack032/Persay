"""
🔐 Menza - Encrypted Messaging Application
PRODUCTION BUILD - With Performance Monitoring
"""

from flask import Flask, jsonify, session, request, g
from flask_socketio import SocketIO
import os
import time

from webapp.config import get_config

# ============================================
# APP INITIALIZATION
# ============================================

app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Security: Use secure session cookies
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RENDER', False)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Compression for faster responses
try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

# Static file caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

# ============================================
# PERFORMANCE MONITORING
# ============================================

@app.before_request
def before_request():
    """Track request start time"""
    g.start_time = time.time()
    
    # Skip static files
    if request.path.startswith('/static') or request.path == '/health':
        return
    
    # Initialize test users on first request
    from webapp.models.store import ensure_initialized
    ensure_initialized()

@app.after_request
def after_request(response):
    """Track request timing and add headers"""
    # Calculate request duration
    if hasattr(g, 'start_time'):
        duration_ms = (time.time() - g.start_time) * 1000
        
        # Skip static files in logging
        if not request.path.startswith('/static'):
            # Record in performance monitor
            try:
                from webapp.core.performance_monitor import perf
                perf.record(f"route.{request.endpoint or 'unknown'}", duration_ms)
            except:
                pass
            
            # Log slow requests
            if duration_ms > 500:
                print(f"🐢 SLOW REQUEST: {request.method} {request.path} took {duration_ms:.0f}ms", flush=True)
            elif duration_ms > 1000:
                print(f"🚨 CRITICAL: {request.method} {request.path} took {duration_ms:.0f}ms", flush=True)
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Cache static files
    if response.content_type and ('javascript' in response.content_type or 
                                   'css' in response.content_type or
                                   'image' in response.content_type):
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
    return response


# ============================================
# DEBUG ENDPOINTS
# ============================================

@app.route('/api/perf')
def get_performance():
    """Get performance statistics - identifies bottlenecks"""
    try:
        from webapp.core.performance_monitor import get_stats, get_bottlenecks
        return jsonify({
            'bottlenecks': get_bottlenecks(),
            'stats': get_stats()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/perf/bottlenecks')
def get_bottlenecks_only():
    """Get just the bottlenecks"""
    try:
        from webapp.core.performance_monitor import get_bottlenecks
        return jsonify({'bottlenecks': get_bottlenecks()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

# ============================================
# SOCKETIO - SIMPLIFIED
# ============================================

socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=20,
    ping_interval=10,
    logger=False,
    engineio_logger=False
)

# ============================================
# REGISTER ROUTES & SOCKETS
# ============================================

# Initialize MIE (lightweight)
from webapp.core import initialize_engine
initialize_engine()

# Register routes
from webapp.routes import register_routes
register_routes(app)

# Register socket events
from webapp.sockets import register_socket_events
register_socket_events(socketio)

print("✅ Menza ready", flush=True)

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
