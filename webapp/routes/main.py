"""
🏠 Main Routes

Core application pages: home, chat.
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
    
    if not query:
        return jsonify({'users': []})
    
    # Get all users except current user
    all_usernames = store.get_all_usernames()
    matched_users = []
    
    for username in all_usernames:
        if username != current_user and query in username.lower():
            user_data = store.get_user(username)
            matched_users.append({
                'username': username,
                'display_name': user_data.get('display_name', username) if user_data else username,
                'profile_picture': user_data.get('profile_picture') if user_data else None
            })
    
    return jsonify({'users': matched_users})


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
    
    # Get list of all users except current user
    all_users = [u for u in store.get_all_usernames() if u != username]
    
    # Get user's subscribed channels
    my_channels = store.get_user_channels(username)
    subscribed_channels = store.get_subscribed_channels(username)
    all_my_channels = my_channels + subscribed_channels
    
    return render_template('chat.html', 
                         username=username,
                         all_users=all_users,
                         my_channels=all_my_channels)

