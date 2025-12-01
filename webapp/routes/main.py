"""
🏠 Main Routes

Core application pages: home, chat.
"""

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from webapp.models import store

main_bp = Blueprint('main', __name__)


@main_bp.route('/api/users/search')
def search_users():
    """Search for users by username - optimized"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').lower().strip()
    current_user = session['username']
    
    if not query or len(query) < 2:
        return jsonify({'users': []})
    
    # Use optimized search function
    matched_users = store.search_users(query, current_user, limit=20)
    
    return jsonify({'users': matched_users})


@main_bp.route('/api/users/contacts')
def get_contacts():
    """Get users the current user has chatted with"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user = session['username']
    contacts = store.get_chat_partners(current_user)
    
    return jsonify({'contacts': contacts})


@main_bp.route('/')
def index():
    """Home page - shows login or redirects to chat"""
    if 'username' in session:
        return redirect(url_for('main.chat'))
    return render_template('index.html')


@main_bp.route('/chat')
def chat():
    """Main chat page - encrypted messaging"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    
    # Don't load all users - use lazy loading via search API
    # This dramatically speeds up page load
    
    # Get user's channels (combined query)
    my_channels = store.get_all_user_channels(username)
    
    return render_template('chat.html', 
                         username=username,
                         all_users=[],  # Load via API when needed
                         my_channels=my_channels)

