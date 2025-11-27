#!/usr/bin/env python3
"""
🚀 Persay Server Runner

Simple script to start the Persay server.
Run from project root: python run.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.app import app, socketio


if __name__ == '__main__':
    print()
    print("🔐 " + "=" * 50)
    print("🚀 Starting Persay Encrypted Messaging Server")
    print("📍 Open http://localhost:5000 in your browser")
    print("🔐 " + "=" * 50)
    print()
    
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000
    )

