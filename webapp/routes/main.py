"""
🏠 Main Routes - Optimized with MIE

Core application pages: home, chat.
Uses Menza Intelligence Engine for caching and performance.
"""

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from webapp.models import store
from webapp.core import get_engine

main_bp = Blueprint('main', __name__)


@main_bp.route('/api/users/search')
def search_users():
    """Search for users by username - MIE optimized"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').lower().strip()
    current_user = session['username']
    
    if not query or len(query) < 2:
        return jsonify({'users': []})
    
    # Check MIE cache first
    engine = get_engine()
    cache_key = f"user_search:{current_user}:{query}"
    cached = engine.get_cached(cache_key)
    if cached:
        return jsonify({'users': cached})
    
    # Query and cache result
    matched_users = store.search_users(query, current_user, limit=20)
    engine.set_cached(cache_key, matched_users, ttl=30)  # Cache 30s
    
    return jsonify({'users': matched_users})


@main_bp.route('/api/users/contacts')
def get_contacts():
    """Get users the current user has chatted with - MIE optimized"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user = session['username']
    
    # Check MIE cache
    engine = get_engine()
    cache_key = f"contacts:{current_user}"
    cached = engine.get_cached(cache_key)
    if cached:
        return jsonify({'contacts': cached})
    
    contacts = store.get_chat_partners(current_user)
    engine.set_cached(cache_key, contacts, ttl=60)  # Cache 60s
    
    return jsonify({'contacts': contacts})


@main_bp.route('/')
def index():
    """Home page - shows login or redirects to chat"""
    if 'username' in session:
        return redirect(url_for('main.chat'))
    return render_template('index.html')


@main_bp.route('/chat')
def chat():
    """Main chat page - MIE optimized loading"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    engine = get_engine()
    
    # Record user connection for predictive model
    engine.predictor.record_interaction(username, 'chat_page', 'page_view')
    
    # Check MIE cache for channels
    cache_key = f"user_channels:{username}"
    my_channels = engine.get_cached(cache_key)
    if not my_channels:
        my_channels = store.get_all_user_channels(username)
        engine.set_cached(cache_key, my_channels, ttl=120)  # Cache 2 min
    
    return render_template('chat.html', 
                         username=username,
                         all_users=[],
                         my_channels=my_channels)

