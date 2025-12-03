"""
🔐 Menza - MINIMAL BUILD
No heavy operations on startup.
"""

from flask import Flask, jsonify
from flask_socketio import SocketIO
import os

# ============================================
# MINIMAL APP
# ============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(500)
def handle_500(e):
    print(f"❌ Error: {e}", flush=True)
    return jsonify({'error': 'Server error'}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Not found'}), 404

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

# ============================================
# SOCKET.IO - MINIMAL
# ============================================

socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    logger=False,
    engineio_logger=False
)

# ============================================
# REGISTER ROUTES
# ============================================

print("📦 Loading...", flush=True)

from webapp.routes import register_routes
register_routes(app)

from webapp.sockets import register_socket_events
register_socket_events(socketio)

print("✅ Ready", flush=True)

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
