"""
⚙️ Menza Configuration

Central configuration for the application.
Update these settings for different environments (dev, staging, production).
"""

import secrets
import os


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # SocketIO
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # App Settings
    APP_NAME = "Menza"
    APP_VERSION = "1.0.0"
    
    # Security
    MIN_USERNAME_LENGTH = 3
    MIN_PASSWORD_LENGTH = 6
    MIN_AGE = 18
    
    # Channels
    MIN_CHANNEL_NAME_LENGTH = 3
    MAX_CHANNEL_DESCRIPTION_LENGTH = 500
    DEFAULT_ACCENT_COLOR = "#6366f1"
    DEFAULT_AVATAR_EMOJI = "📢"


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True


# Config mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

