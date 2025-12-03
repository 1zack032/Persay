"""
🏠 Main Routes - PRODUCTION (simplified)
"""

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from webapp.models import store

main_bp = Blueprint('main', __name__)


@main_bp.route('/api/users/search')
def search_users():
    """Search for users by username"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').lower().strip()
    current_user = session['username']
    
    if not query or len(query) < 2:
        return jsonify({'users': []})
    
    matched_users = store.search_users(query, current_user, limit=20)
    return jsonify({'users': matched_users})


@main_bp.route('/api/users/contacts')
def get_contacts():
    """Get users the current user has chatted with"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    contacts = store.get_chat_partners(session['username'])
    return jsonify({'contacts': contacts})


@main_bp.route('/')
def index():
    """Home page"""
    if 'username' in session:
        return redirect(url_for('main.chat'))
    return render_template('index.html')


@main_bp.route('/chat')
def chat():
    """Main chat page"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    
    # Get user's channels directly (no caching to avoid issues)
    try:
        my_channels = store.get_all_user_channels(username)
    except Exception:
        my_channels = []
    
    return render_template('chat.html', 
                         username=username,
                         all_users=[],
                         my_channels=my_channels)
