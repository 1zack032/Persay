"""
Menza - Production Entry Point
This file is for Render.com deployment
"""
import sys
import os

# Set production mode
os.environ['FLASK_DEBUG'] = 'false'
os.environ['FLASK_ENV'] = 'production'

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from webapp.app import app, socketio

# Expose for gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Menza on port {port}")
    socketio.run(app, host='0.0.0.0', port=port)

