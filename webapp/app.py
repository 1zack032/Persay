"""
🔐 Menza - Encrypted Messaging Application

Main application entry point.
This file initializes Flask, SocketIO, and registers all routes/events.

ARCHITECTURE:
============
webapp/
├── app.py              ← You are here (entry point)
├── config.py           ← Configuration settings
├── core/
│   ├── __init__.py
│   └── menza_intelligence_engine.py  ← 🧠 MIE - Performance Engine
├── models/
│   ├── __init__.py
│   └── store.py        ← Data storage (swap for database in production)
├── routes/
│   ├── __init__.py
│   ├── auth.py         ← Login, register, logout
│   ├── main.py         ← Home, chat pages
│   ├── channels.py     ← Channel management
│   └── legal.py        ← Privacy, terms pages
└── sockets/
    ├── __init__.py
    ├── messaging.py    ← Private messaging events
    └── channels.py     ← Channel events (reactions, comments)

To add a new feature:
1. Create a new route file in routes/
2. Create socket events in sockets/ if needed
3. Register in the respective __init__.py
"""

from flask import Flask, jsonify, session, request, g
from flask_socketio import SocketIO
import traceback
import sys
import time
import os

from webapp.config import get_config

# ============================================
# 🔍 DEBUG LOGGING - Find slowdowns
# ============================================
DEBUG_TIMING = os.environ.get('DEBUG_TIMING', 'true').lower() == 'true'

def log_timing(label, start_time):
    """Log timing if debug is enabled"""
    if DEBUG_TIMING:
        elapsed = (time.time() - start_time) * 1000
        symbol = "🐢" if elapsed > 500 else "⚡" if elapsed < 100 else "⏱️"
        print(f"{symbol} [{label}] {elapsed:.1f}ms", flush=True)

print("🔄 Starting app initialization...", flush=True)
init_start = time.time()

# Initialize Menza Intelligence Engine
from webapp.core import initialize_engine, get_engine
mie_start = time.time()
mie = initialize_engine()
log_timing("MIE Init", mie_start)

# ============================================
# APP INITIALIZATION
# ============================================

# Create Flask app
app = Flask(__name__)

# Load configuration
config = get_config()
app.config.from_object(config)

# Enable response compression for faster page loads
try:
    from flask_compress import Compress
    Compress(app)
    print("✅ Response compression enabled")
except ImportError:
    print("⚠️ Flask-Compress not installed, skipping compression")

# Add caching headers for static files
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year for static files

@app.before_request
def before_request_timing():
    """Track request start time"""
    g.start_time = time.time()
    if DEBUG_TIMING and not request.path.startswith('/static'):
        print(f"📥 START {request.method} {request.path}", flush=True)

@app.after_request
def add_cache_headers(response):
    # Log request timing
    if DEBUG_TIMING and hasattr(g, 'start_time') and not request.path.startswith('/static'):
        elapsed = (time.time() - g.start_time) * 1000
        symbol = "🐢" if elapsed > 1000 else "⚠️" if elapsed > 500 else "✅"
        print(f"{symbol} END {request.method} {request.path} → {response.status_code} in {elapsed:.0f}ms", flush=True)
    
    # Cache static assets aggressively
    if 'static' in response.headers.get('Content-Location', '') or \
       response.content_type and ('javascript' in response.content_type or 
                                   'css' in response.content_type or
                                   'image' in response.content_type):
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler - log all exceptions"""
    print(f"❌ ERROR: {type(e).__name__}: {str(e)}", file=sys.stderr)
    print(f"❌ TRACEBACK:\n{traceback.format_exc()}", file=sys.stderr)
    
    # Return generic error for production
    return jsonify({
        'error': 'Internal server error',
        'message': str(e) if app.debug else 'Something went wrong'
    }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


# ============================================
# 🧠 MENZA INTELLIGENCE ENGINE API
# ============================================

@app.route('/api/engine/stats')
def engine_stats():
    """Get MIE performance statistics"""
    engine = get_engine()
    return jsonify({
        'success': True,
        'engine': engine.get_engine_stats()
    })

@app.route('/api/engine/health')
def engine_health():
    """Get MIE health status"""
    engine = get_engine()
    return jsonify({
        'success': True,
        'health': engine.get_health_status()
    })

@app.route('/health')
def health_check():
    """Quick health check - minimal processing"""
    return jsonify({'status': 'ok', 'timestamp': time.time()})

@app.route('/api/debug/timing')
def debug_timing():
    """Debug endpoint to test database connectivity"""
    from webapp.models import store
    results = {}
    
    # Test MongoDB ping
    start = time.time()
    try:
        from webapp.models.store import USE_MONGODB, db
        if USE_MONGODB and db:
            db.command('ping')
            results['mongodb_ping'] = f"{(time.time()-start)*1000:.0f}ms"
        else:
            results['mongodb_ping'] = 'Not connected'
    except Exception as e:
        results['mongodb_ping'] = f"Error: {str(e)[:50]}"
    
    # Test a simple user query
    start = time.time()
    try:
        user = store.get_user('test')  # Non-existent user
        results['user_query'] = f"{(time.time()-start)*1000:.0f}ms"
    except Exception as e:
        results['user_query'] = f"Error: {str(e)[:50]}"
    
    return jsonify(results)

@app.route('/investors')
def investor_dashboard():
    """Investor dashboard showing MIE performance"""
    from flask import render_template
    return render_template('investor_dashboard.html')

# Initialize SocketIO with threading mode for production
import os
# Always use threading in production for better performance
is_production = os.environ.get('FLASK_ENV', 'production') == 'production' or os.environ.get('RENDER', False)
async_mode = 'threading' if is_production else None
socketio = SocketIO(
    app, 
    cors_allowed_origins=config.SOCKETIO_CORS_ALLOWED_ORIGINS, 
    async_mode=async_mode,
    ping_timeout=60,
    ping_interval=25,
    logger=False,
    engineio_logger=False
)


# ============================================
# REGISTER ROUTES & SOCKET EVENTS
# ============================================

def initialize_app():
    """Initialize all routes and socket events"""
    
    routes_start = time.time()
    # Register HTTP routes
    from webapp.routes import register_routes
    register_routes(app)
    log_timing("Routes registration", routes_start)
    
    sockets_start = time.time()
    # Register WebSocket events
    from webapp.sockets import register_socket_events
    register_socket_events(socketio)
    log_timing("Sockets registration", sockets_start)
    
    log_timing("Total app init", init_start)
    print(f"✅ {config.APP_NAME} v{config.APP_VERSION} initialized", flush=True)


# Initialize on import
initialize_app()


# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print()
    print("🔐 " + "=" * 50)
    print(f"🚀 Starting {config.APP_NAME} v{config.APP_VERSION}")
    print("📍 Open http://localhost:5000 in your browser")
    print("🔐 " + "=" * 50)
    print()
    
    socketio.run(
        app,
        debug=config.DEBUG,
        host='0.0.0.0',
        port=5000
    )
