"""
🔐 Menza - Encrypted Messaging Application
PRODUCTION BUILD - Stripped for performance
"""

from flask import Flask, jsonify, session, request, g
from flask_socketio import SocketIO
import os

from webapp.config import get_config

# ============================================
# APP INITIALIZATION - MINIMAL
# ============================================

app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Compression
try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

# Static file caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

@app.before_request
def before_request():
    """Minimal before request"""
    # Skip lazy init for static files
    if request.path.startswith('/static'):
        return
    # Lazy init test users on first real request
    from webapp.models.store import ensure_initialized
    ensure_initialized()

@app.after_request
def after_request(response):
    """Cache static files"""
    if response.content_type and ('javascript' in response.content_type or 
                                   'css' in response.content_type or
                                   'image' in response.content_type):
        response.cache_control.max_age = 31536000
        response.cache_control.public = True
    return response

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
