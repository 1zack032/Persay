"""
📦 Data Models

This package contains data storage and models.
In production, replace with database models (SQLAlchemy, etc.)
"""

from .store import DataStore, store

__all__ = ['DataStore', 'store']

