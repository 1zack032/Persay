"""
🔐 Menza - Encrypted Messaging Application
PRODUCTION BUILD - MIE Optimized
"""

from flask import Flask, jsonify, request, g
from flask_socketio import SocketIO
import os
import time

# ============================================
# APP INITIALIZATION
# ============================================

app = Flask(__name__)

# Secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'menza-dev-key-change-in-production')

# Session config
app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get('RENDER'))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Compression
try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

# ============================================
# MIE INTEGRATION - Request Tracking
# ============================================

@app.before_request
def before_request():
    """Track request timing"""
    g.start_time = time.time()

@app.after_request
def after_request(response):
    """Log slow requests and record metrics"""
    if hasattr(g, 'start_time'):
        duration_ms = (time.time() - g.start_time) * 1000
        
        # Record in MIE
        try:
            from webapp.core.menza_intelligence_engine import MIE
            MIE.record_request()
        except:
            pass
        
        # Log slow requests (skip static files)
        if not request.path.startswith('/static') and duration_ms > 500:
            print(f"🐢 SLOW: {request.path} took {duration_ms:.0f}ms", flush=True)
    
    return response

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Menza is running'})

@app.route('/api/mie/stats')
def mie_stats():
    """Get MIE statistics"""
    try:
        from webapp.core.menza_intelligence_engine import MIE
        return jsonify(MIE.get_stats())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def handle_500(e):
    print(f"❌ 500 Error: {e}", flush=True)
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Not found'}), 404

# ============================================
# SOCKET.IO
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
# REGISTER ROUTES & SOCKETS
# ============================================

print("📦 Loading routes...", flush=True)

from webapp.routes import register_routes
register_routes(app)

print("🔌 Loading sockets...", flush=True)

from webapp.sockets import register_socket_events
register_socket_events(socketio)

# Initialize MIE
try:
    from webapp.core.menza_intelligence_engine import MIE
    print(f"🧠 MIE ready (cache: {MIE._response_cache.maxsize} entries)", flush=True)
except:
    pass

print("✅ Menza ready!", flush=True)

# ============================================
# RUN
# ============================================

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
