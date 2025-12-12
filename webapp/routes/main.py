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


@main_bp.route('/api/users/smart-search')
def smart_search_users():
    """
    Smart search for users - prioritizes known users (contacts) first.
    Returns two lists: known_users and other_users
    """
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').lower().strip()
    current_user = session['username']
    
    try:
        # Get contacts (people user has chatted with)
        contacts = store.get_chat_partners(current_user)
        contact_usernames = set(c['username'] for c in contacts)
        
        # Filter contacts by search query
        known_users = []
        for contact in contacts:
            if not query or query in contact['username'].lower() or query in (contact.get('display_name', '') or '').lower():
                known_users.append({
                    'username': contact['username'],
                    'display_name': contact.get('display_name'),
                    'message_count': contact.get('message_count', 0)
                })
        
        # Search all users and filter out contacts and current user
        other_users = []
        if query:
            all_results = store.search_users(query, current_user, limit=20)
            for user in all_results:
                if user['username'] not in contact_usernames:
                    other_users.append({
                        'username': user['username'],
                        'display_name': user.get('display_name')
                    })
        else:
            # If no query, show recent users from the system (excluding contacts)
            all_users = store.get_all_users()
            count = 0
            for username in all_users:
                if username != current_user and username not in contact_usernames:
                    other_users.append({
                        'username': username,
                        'display_name': None
                    })
                    count += 1
                    if count >= 10:
                        break
        
        return jsonify({
            'known_users': known_users[:10],
            'other_users': other_users[:10]
        })
    except Exception as e:
        print(f"Smart search error: {e}", flush=True)
        return jsonify({'known_users': [], 'other_users': []})


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


# ============================================================
# 📱 Mobile API Endpoints
# ============================================================

@main_bp.route('/api/chats')
def api_get_chats():
    """Get all chats/conversations for the current user"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    chats = []
    seen_users = set()
    
    try:
        # Get DM conversations by scanning message rooms
        # Check for messages with each test user
        test_users = ['sarah_test', 'mike_demo', 'alex_dev', 'emma_test']
        
        for other_user in test_users:
            users = sorted([username, other_user])
            room_id = f"dm_{users[0]}_{users[1]}"
            messages = store.get_messages(room_id)
            
            if messages:
                last_msg = messages[-1] if messages else None
                other_user_data = store.get_user(other_user) or {}
                
                chats.append({
                    'id': room_id,
                    'participants': [username, other_user],
                    'last_message': {
                        'id': last_msg.get('id', ''),
                        'content': last_msg.get('content', ''),
                        'sender': last_msg.get('sender', ''),
                        'recipient': last_msg.get('recipient'),
                        'group_id': None,
                        'timestamp': last_msg.get('timestamp', '2024-01-01T00:00:00'),
                        'is_read': True,
                        'is_delivered': True,
                        'message_type': 'text'
                    } if last_msg else None,
                    'unread_count': 0,
                    'is_group': False,
                    'group_name': other_user_data.get('display_name') or other_user,
                    'group_avatar': None,
                    'created_at': last_msg.get('timestamp', '2024-01-01T00:00:00') if last_msg else '2024-01-01T00:00:00'
                })
                seen_users.add(other_user)
        
        # Also get from contacts (chat partners)
        contacts = store.get_chat_partners(username)
        for contact in contacts:
            if contact['username'] not in seen_users:
                chat_id = f"dm_{min(username, contact['username'])}_{max(username, contact['username'])}"
                chats.append({
                    'id': chat_id,
                    'participants': [username, contact['username']],
                    'last_message': None,
                    'unread_count': 0,
                    'is_group': False,
                    'group_name': contact.get('display_name') or contact['username'],
                    'group_avatar': None,
                    'created_at': contact.get('last_message_time', '2024-01-01T00:00:00')
                })
        
        # Get groups
        groups = store.get_user_groups(username)
        for group in groups:
            chats.append({
                'id': group['id'],
                'participants': group.get('members', []),
                'last_message': None,
                'unread_count': 0,
                'is_group': True,
                'group_name': group.get('name', 'Group'),
                'group_avatar': group.get('avatar_emoji', '👥'),
                'created_at': group.get('created_at', '2024-01-01T00:00:00')
            })
        
        return jsonify({'success': True, 'chats': chats})
    except Exception as e:
        print(f"API chats error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': True, 'chats': []})


@main_bp.route('/api/channels/discover')
def api_discover_channels():
    """Get discoverable channels"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    try:
        # Get all channels user owns or is subscribed to
        my_channels = store.get_user_channels(username)
        subscribed = store.get_subscribed_channels(username)
        
        all_channels = []
        seen_ids = set()
        
        for channel in my_channels + subscribed:
            if channel['id'] not in seen_ids:
                seen_ids.add(channel['id'])
                all_channels.append({
                    'id': channel['id'],
                    'name': channel.get('name', 'Channel'),
                    'description': channel.get('description'),
                    'avatar': channel.get('branding', {}).get('avatar_emoji', '📢'),
                    'creator': channel.get('owner'),
                    'subscriber_count': channel.get('subscriber_count', 0),
                    'is_subscribed': True,
                    'posts': [],
                    'created_at': channel.get('created', '2024-01-01T00:00:00'),
                    'category': channel.get('tags', ['General'])[0] if channel.get('tags') else 'General',
                    'is_verified': channel.get('owner') == username
                })
        
        return jsonify({'success': True, 'channels': all_channels})
    except Exception as e:
        print(f"API channels error: {e}", flush=True)
        return jsonify({'success': True, 'channels': []})


@main_bp.route('/api/groups')
def api_get_groups():
    """Get user's groups"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    try:
        groups = store.get_user_groups(username)
        formatted_groups = []
        
        for group in groups:
            formatted_groups.append({
                'id': group['id'],
                'name': group.get('name', 'Group'),
                'description': group.get('description'),
                'avatar': group.get('avatar_emoji', '👥'),
                'members': group.get('members', []),
                'admins': [group.get('owner')],
                'creator': group.get('owner'),
                'created_at': group.get('created_at', '2024-01-01T00:00:00'),
                'invite_link': group.get('invite_code')
            })
        
        return jsonify({'success': True, 'groups': formatted_groups})
    except Exception as e:
        print(f"API groups error: {e}", flush=True)
        return jsonify({'success': True, 'groups': []})
