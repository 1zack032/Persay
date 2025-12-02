"""
🔐 Persay - Encrypted Messaging Application

Main application entry point.
This file initializes Flask, SocketIO, and registers all routes/events.

ARCHITECTURE:
============
webapp/
├── app.py              ← You are here (entry point)
├── config.py           ← Configuration settings
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

from flask import Flask, jsonify
from flask_socketio import SocketIO
import traceback
import sys

from webapp.config import get_config

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

@app.after_request
def add_cache_headers(response):
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
    
    # Register HTTP routes
    from webapp.routes import register_routes
    register_routes(app)
    
    # Register WebSocket events
    from webapp.sockets import register_socket_events
    register_socket_events(socketio)
    
    print(f"✅ {config.APP_NAME} v{config.APP_VERSION} initialized")


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
