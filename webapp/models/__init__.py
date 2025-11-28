"""
Data Models

This package contains data storage and models.
Uses MongoDB for persistent storage.
"""

from .store import DataStore, store

__all__ = ['DataStore', 'store']
