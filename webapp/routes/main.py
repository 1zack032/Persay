"""
🏠 Main Routes - MINIMAL
"""

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from webapp.models import store

main_bp = Blueprint('main', __name__)


@main_bp.route('/api/users/search')
def search_users():
    """Search for users"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').lower().strip()
    if not query or len(query) < 2:
        return jsonify({'users': []})
    
    try:
        users = store.search_users(query, session['username'], limit=10)
        return jsonify({'users': users})
    except Exception as e:
        print(f"Search error: {e}", flush=True)
        return jsonify({'users': []})


@main_bp.route('/api/users/contacts')
def get_contacts():
    """Get chat partners"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        contacts = store.get_chat_partners(session['username'])
        return jsonify({'contacts': contacts})
    except Exception as e:
        print(f"Contacts error: {e}", flush=True)
        return jsonify({'contacts': []})


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
    
    try:
        my_channels = store.get_all_user_channels(username)
    except Exception as e:
        print(f"Channels error: {e}", flush=True)
        my_channels = []
    
    return render_template('chat.html', 
                         username=username,
                         all_users=[],
                         my_channels=my_channels)


@main_bp.route('/api/mie/stats')
def mie_stats():
    """MIE statistics"""
    try:
        from webapp.core.menza_intelligence_engine import MIE
        return jsonify(MIE.get_stats())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
