"""
🔌 WebSocket Events Package

Real-time communication handlers using Socket.IO.
Each module handles events for a specific feature area.
"""

from .messaging import register_messaging_events
from .channels import register_channel_events


def register_socket_events(socketio):
    """Register all WebSocket event handlers"""
    register_messaging_events(socketio)
    register_channel_events(socketio)


__all__ = ['register_socket_events']

