"""
🛣️ Routes Package

This package contains all HTTP route blueprints.
Each module handles a specific feature area.
"""

from flask import Blueprint

# Import blueprints
from .auth import auth_bp
from .main import main_bp
from .channels import channels_bp
from .legal import legal_bp
from .docs import docs_bp
from .settings import settings_bp


def register_routes(app):
    """Register all route blueprints with the Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(channels_bp)
    app.register_blueprint(legal_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(settings_bp)


__all__ = ['register_routes', 'auth_bp', 'main_bp', 'channels_bp', 'legal_bp', 'docs_bp', 'settings_bp']

