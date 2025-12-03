"""
🔐 Menza - Encrypted Messaging Application
PRODUCTION BUILD - Optimized for speed
"""

from flask import Flask, jsonify, request
from flask_socketio import SocketIO
import os

# ============================================
# MINIMAL APP INITIALIZATION
# ============================================

app = Flask(__name__)

# Secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'menza-dev-key-change-in-production')

# Session config
app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get('RENDER'))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Compression (optional)
try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(500)
def handle_500(e):
    print(f"❌ 500 Error: {e}", flush=True)
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Not found'}), 404

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Menza is running'})

# ============================================
# SOCKET.IO - SIMPLE CONFIG
# ============================================

socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=30,
    ping_interval=15,
    logger=False,
    engineio_logger=False
)

# ============================================
# REGISTER ROUTES (lazy - fast import)
# ============================================

print("📦 Loading routes...", flush=True)

from webapp.routes import register_routes
register_routes(app)

print("🔌 Loading sockets...", flush=True)

from webapp.sockets import register_socket_events
register_socket_events(socketio)

print("✅ Menza ready!", flush=True)

# ============================================
# RUN
# ============================================

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
