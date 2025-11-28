"""
WSGI Entry Point for Production Deployment
"""
import sys
import os

# Set production environment
os.environ['FLASK_DEBUG'] = 'false'

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the app
from webapp.app import app, socketio

# This is what gunicorn will use
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)

