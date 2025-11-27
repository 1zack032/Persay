"""
🏠 Main Routes

Core application pages: home, chat.
"""

from flask import Blueprint, render_template, session, redirect, url_for
from webapp.models import store

main_bp = Blueprint('main', __name__)


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
    
    return render_template('chat.html', 
                         username=username,
                         all_users=all_users)

