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

from flask import Flask
from flask_socketio import SocketIO

from webapp.config import get_config

# ============================================
# APP INITIALIZATION
# ============================================

# Create Flask app
app = Flask(__name__)

# Load configuration
config = get_config()
app.config.from_object(config)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=config.SOCKETIO_CORS_ALLOWED_ORIGINS)


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
