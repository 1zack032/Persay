"""
🏠 Main Routes - MIE Optimized
"""

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from webapp.models import store
from webapp.core.menza_intelligence_engine import MIE

main_bp = Blueprint('main', __name__)


@main_bp.route('/api/users/search')
def search_users():
    """Search for users by username - MIE cached"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').lower().strip()
    current_user = session['username']
    
    if not query or len(query) < 2:
        return jsonify({'users': []})
    
    # Check MIE cache first
    cache_key = f"user_search:{query}:{current_user}"
    cached = MIE.get_cached_response(cache_key)
    if cached is not None:
        return jsonify({'users': cached})
    
    # Query database
    matched_users = store.search_users(query, current_user, limit=20)
    
    # Cache for 30 seconds
    MIE.cache_response(cache_key, matched_users, ttl=30)
    
    return jsonify({'users': matched_users})


@main_bp.route('/api/users/contacts')
def get_contacts():
    """Get users the current user has chatted with - MIE cached"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    # Check MIE cache first
    cache_key = f"contacts:{username}"
    cached = MIE.get_cached_response(cache_key)
    if cached is not None:
        return jsonify({'contacts': cached})
    
    # Query database
    contacts = store.get_chat_partners(username)
    
    # Cache for 60 seconds
    MIE.cache_response(cache_key, contacts, ttl=60)
    
    return jsonify({'contacts': contacts})


@main_bp.route('/')
def index():
    """Home page"""
    if 'username' in session:
        return redirect(url_for('main.chat'))
    return render_template('index.html')


@main_bp.route('/chat')
def chat():
    """Main chat page - MIE optimized"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    
    # Check MIE cache for user's channels
    cache_key = f"user_channels:{username}"
    my_channels = MIE.get_cached_response(cache_key)
    
    if my_channels is None:
        try:
            my_channels = store.get_all_user_channels(username)
            # Cache for 2 minutes
            MIE.cache_response(cache_key, my_channels, ttl=120)
        except Exception:
            my_channels = []
    
    return render_template('chat.html', 
                         username=username,
                         all_users=[],
                         my_channels=my_channels)
