#!/usr/bin/env python3
"""
🚀 Menza Server Runner

Start the Menza secure messaging server.
- Development: python run.py
- Production: gunicorn --worker-class eventlet -w 1 run:app
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.app import app, socketio

# Export for gunicorn
application = app


if __name__ == '__main__':
    # Get port from environment (for cloud platforms) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    print()
    print("🔐 " + "=" * 50)
    print("🚀 Starting Menza Encrypted Messaging Server")
    print(f"📍 Open http://localhost:{port} in your browser")
    print("🔐 " + "=" * 50)
    print()
    
    socketio.run(
        app,
        debug=debug,
        host='0.0.0.0',
        port=port
    )

