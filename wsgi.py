"""
WSGI Entry Point for Production Deployment
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.app import app, socketio

# This is what gunicorn will use
application = app

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

