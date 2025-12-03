"""
Menza - Production Entry Point
Minimal and fast for Render.com
"""
import sys
import os

# Production mode
os.environ['FLASK_DEBUG'] = 'false'
os.environ['FLASK_ENV'] = 'production'

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting Menza...", flush=True)

# Import Flask app
from webapp.app import app, socketio

# For gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Menza running on port {port}", flush=True)
    socketio.run(app, host='0.0.0.0', port=port)
