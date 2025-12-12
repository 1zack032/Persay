"""
📺 Channel Routes - MINIMAL
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from webapp.models import store
from webapp.config import Config

channels_bp = Blueprint('channels', __name__)


@channels_bp.route('/channels')
def channels_page():
    """Channel discovery page"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    discover_filter = request.args.get('filter', 'trending')
    
    try:
        discover_data = store.get_discover_channels_rotated(username=username)
        my_channels = store.get_user_channels(username)
        subscribed = store.get_subscribed_channels(username)
    except Exception as e:
        print(f"Channels page error: {e}", flush=True)
        discover_data = {'trending': [], 'most_liked': [], 'most_viewed': [], 'new': []}
        my_channels = []
        subscribed = []
    
    filter_map = {'most_liked': 'most_liked', 'most_viewed': 'most_viewed', 'new': 'new'}
    discover_channels = discover_data.get(filter_map.get(discover_filter, 'trending'), [])[:20]
    
    return render_template('channels.html',
                         username=username,
                         my_channels=my_channels,
                         subscribed_channels=subscribed,
                         discover_channels=discover_channels,
                         discover_filter=discover_filter,
                         trending_channels=discover_data.get('trending', [])[:5])


@channels_bp.route('/channels/search')
def search_channels():
    """Search channels"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    query = request.args.get('q', '').strip()
    username = session['username']
    
    try:
        if query:
            results = store.search_channels(query, limit=20)
        else:
            results = []
    except Exception as e:
        print(f"Search error: {e}", flush=True)
        results = []
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'results': results, 'query': query})
    
    return render_template('channels_search.html',
                         username=username,
                         query=query,
                         results=results,
                         categories=store.get_all_categories())


@channels_bp.route('/channels/categories')
def get_categories():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({'categories': store.get_all_categories()})


@channels_bp.route('/api/channels/search')
def api_search_channels():
    """API search"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify({'channels': []})
    
    try:
        results = store.search_channels(query, limit=20)
        return jsonify({'channels': results})
    except Exception as e:
        print(f"API search error: {e}", flush=True)
        return jsonify({'channels': []})


@channels_bp.route('/channel/<channel_id>/like', methods=['POST'])
def like_channel(channel_id):
    if 'username' not in session:
        return jsonify({'success': False}), 401
    try:
        return jsonify(store.like_channel(channel_id, session['username']))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@channels_bp.route('/channel/<channel_id>/unlike', methods=['POST'])
def unlike_channel(channel_id):
    if 'username' not in session:
        return jsonify({'success': False}), 401
    try:
        return jsonify(store.unlike_channel(channel_id, session['username']))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@channels_bp.route('/channel/create', methods=['GET', 'POST'])
def create_channel():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        accent_color = request.form.get('accent_color', '#8B5CF6')
        avatar_emoji = request.form.get('avatar_emoji', '📢')
        discoverable = request.form.get('discoverable') == 'on'
        
        if len(name) < 3:
            return render_template('channel_create.html', 
                error="Channel name must be at least 3 characters",
                username=session['username'])
        
        try:
            if store.channel_name_exists(name):
                return render_template('channel_create.html', 
                    error="Channel name already exists",
                    username=session['username'])
            
            channel = store.create_channel(
                name=name,
                description=description,
                owner=session['username'],
                accent_color=accent_color,
                avatar_emoji=avatar_emoji,
                discoverable=discoverable
            )
            return redirect(url_for('channels.view_channel', channel_id=channel['id']))
        except Exception as e:
            print(f"Create channel error: {e}", flush=True)
            return render_template('channel_create.html', 
                error="Failed to create channel",
                username=session['username'])
    
    return render_template('channel_create.html', username=session['username'])


@channels_bp.route('/channel/<channel_id>')
def view_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        channel = store.get_channel(channel_id)
        if not channel:
            return redirect(url_for('channels.channels_page'))
        
        username = session['username']
        is_owner = channel['owner'] == username
        posts = store.get_channel_posts(channel_id)
        my_channels = store.get_user_channels(username)
        subscribed = store.get_subscribed_channels(username)
        
        return render_template('channel_view.html',
                             channel=channel,
                             posts=posts,
                             username=username,
                             is_owner=is_owner,
                             is_subscribed=(username in channel.get('subscribers', [])),
                             user_role=store.get_member_role(channel_id, username),
                             can_post=store.can_post_in_channel(channel_id, username),
                             can_manage=is_owner,
                             members_with_roles=[],
                             my_channels=my_channels,
                             subscribed_channels=subscribed)
    except Exception as e:
        print(f"View channel error: {e}", flush=True)
        return redirect(url_for('channels.channels_page'))


@channels_bp.route('/channel/<channel_id>/settings', methods=['GET', 'POST'])
def channel_settings(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        channel = store.get_channel(channel_id)
        if not channel or channel['owner'] != session['username']:
            return redirect(url_for('channels.channels_page'))
        
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'toggle_discoverable':
                store.set_channel_discoverable(channel_id, not channel.get('discoverable', True))
            return redirect(url_for('channels.channel_settings', channel_id=channel_id))
        
        return render_template('channel_settings.html',
                             channel=channel,
                             username=session['username'],
                             members_with_roles=[],
                             total_likes=0,
                             posts_count=len(store.get_channel_posts(channel_id)))
    except Exception as e:
        print(f"Channel settings error: {e}", flush=True)
        return redirect(url_for('channels.channels_page'))


@channels_bp.route('/channel/<channel_id>/post', methods=['POST'])
def create_post(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    
    # SECURITY: Check if user has permission to post in this channel
    if not store.can_post_in_channel(channel_id, username):
        # User is not an admin or moderator - cannot post
        return redirect(url_for('channels.view_channel', channel_id=channel_id))
    
    content = request.form.get('content', '').strip()
    if content:
        try:
            store.create_post(channel_id=channel_id, author=username, content=content)
        except Exception as e:
            print(f"Create post error: {e}", flush=True)
    
    return redirect(url_for('channels.view_channel', channel_id=channel_id))


@channels_bp.route('/channel/<channel_id>/subscribe', methods=['POST'])
def subscribe_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    try:
        store.subscribe_to_channel(channel_id, session['username'])
    except Exception as e:
        print(f"Subscribe error: {e}", flush=True)
    return redirect(url_for('channels.view_channel', channel_id=channel_id))


@channels_bp.route('/channel/<channel_id>/unsubscribe', methods=['POST'])
def unsubscribe_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    try:
        store.unsubscribe_from_channel(channel_id, session['username'])
    except Exception as e:
        print(f"Unsubscribe error: {e}", flush=True)
    return redirect(url_for('channels.view_channel', channel_id=channel_id))


# ==========================================
# JSON API ENDPOINTS FOR iOS APP
# ==========================================

@channels_bp.route('/api/channels/discover')
def api_discover_channels():
    """Get discoverable channels for iOS app"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    try:
        discover_data = store.get_discover_channels_rotated(username=username)
        channels = discover_data.get('trending', [])[:20]
        
        # Format for iOS
        formatted = []
        for ch in channels:
            formatted.append({
                'id': ch.get('id'),
                'name': ch.get('name'),
                'description': ch.get('description'),
                'avatar': ch.get('avatar_emoji', '📢'),
                'owner': ch.get('owner'),
                'subscriber_count': len(ch.get('subscribers', [])),
                'is_verified': ch.get('verified', False),
                'is_subscribed': username in ch.get('subscribers', []),
                'created_at': ch.get('created_at', ''),
                'category': ch.get('category')
            })
        
        return jsonify({'success': True, 'channels': formatted})
    except Exception as e:
        print(f"API discover error: {e}", flush=True)
        return jsonify({'success': True, 'channels': []})


@channels_bp.route('/api/channels/subscribed')
def api_subscribed_channels():
    """Get user's subscribed channels"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    try:
        channels = store.get_subscribed_channels(username)
        formatted = [{
            'id': ch.get('id'),
            'name': ch.get('name'),
            'description': ch.get('description'),
            'avatar': ch.get('avatar_emoji', '📢'),
            'owner': ch.get('owner'),
            'subscriber_count': len(ch.get('subscribers', [])),
            'is_verified': ch.get('verified', False),
            'is_subscribed': True,
            'created_at': ch.get('created_at', '')
        } for ch in channels]
        
        return jsonify({'success': True, 'channels': formatted})
    except Exception as e:
        print(f"API subscribed error: {e}", flush=True)
        return jsonify({'success': True, 'channels': []})


@channels_bp.route('/api/channels/my')
def api_my_channels():
    """Get channels owned by user"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    try:
        channels = store.get_user_channels(username)
        formatted = [{
            'id': ch.get('id'),
            'name': ch.get('name'),
            'description': ch.get('description'),
            'avatar': ch.get('avatar_emoji', '📢'),
            'owner': ch.get('owner'),
            'subscriber_count': len(ch.get('subscribers', [])),
            'is_verified': ch.get('verified', False),
            'is_subscribed': True,
            'created_at': ch.get('created_at', '')
        } for ch in channels]
        
        return jsonify({'success': True, 'channels': formatted})
    except Exception as e:
        print(f"API my channels error: {e}", flush=True)
        return jsonify({'success': True, 'channels': []})


@channels_bp.route('/api/channel/<channel_id>')
def api_get_channel(channel_id):
    """Get single channel details"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    try:
        channel = store.get_channel(channel_id)
        if not channel:
            return jsonify({'success': False, 'error': 'Channel not found'}), 404
        
        posts = store.get_channel_posts(channel_id)
        
        return jsonify({
            'success': True,
            'channel': {
                'id': channel.get('id'),
                'name': channel.get('name'),
                'description': channel.get('description'),
                'avatar': channel.get('avatar_emoji', '📢'),
                'owner': channel.get('owner'),
                'subscriber_count': len(channel.get('subscribers', [])),
                'is_verified': channel.get('verified', False),
                'is_subscribed': username in channel.get('subscribers', []),
                'is_owner': channel.get('owner') == username,
                'can_post': store.can_post_in_channel(channel_id, username),
                'created_at': channel.get('created_at', ''),
                'posts': [{
                    'id': p.get('id'),
                    'content': p.get('content'),
                    'author': p.get('author'),
                    'likes': len(p.get('likes', [])),
                    'comments': len(p.get('comments', [])),
                    'views': p.get('views', 0),
                    'is_liked': username in p.get('likes', []),
                    'created_at': p.get('timestamp', '')
                } for p in posts]
            }
        })
    except Exception as e:
        print(f"API get channel error: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@channels_bp.route('/api/channel/<channel_id>/subscribe', methods=['POST'])
def api_subscribe_channel(channel_id):
    """Subscribe to a channel"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        result = store.subscribe_to_channel(channel_id, session['username'])
        channel = store.get_channel(channel_id)
        return jsonify({
            'success': True,
            'subscriber_count': len(channel.get('subscribers', [])) if channel else 0
        })
    except Exception as e:
        print(f"API subscribe error: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@channels_bp.route('/api/channel/<channel_id>/unsubscribe', methods=['POST'])
def api_unsubscribe_channel(channel_id):
    """Unsubscribe from a channel"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        result = store.unsubscribe_from_channel(channel_id, session['username'])
        channel = store.get_channel(channel_id)
        return jsonify({
            'success': True,
            'subscriber_count': len(channel.get('subscribers', [])) if channel else 0
        })
    except Exception as e:
        print(f"API unsubscribe error: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@channels_bp.route('/api/channel/<channel_id>/moderators')
def api_get_moderators(channel_id):
    """Get channel moderators"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        channel = store.get_channel(channel_id)
        if not channel:
            return jsonify({'success': False, 'error': 'Channel not found'}), 404
        
        members = store.get_channel_members_with_roles(channel_id)
        moderators = [m for m in members if m.get('role') in ['admin', 'moderator']]
        
        return jsonify({'success': True, 'moderators': moderators})
    except Exception as e:
        print(f"API get moderators error: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@channels_bp.route('/api/channel/<channel_id>/moderator/add', methods=['POST'])
def api_add_moderator(channel_id):
    """Add a moderator to channel (owner only)"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400
    
    username_to_add = data.get('username', '').strip()
    if not username_to_add:
        return jsonify({'success': False, 'error': 'Username required'}), 400
    
    try:
        channel = store.get_channel(channel_id)
        if not channel:
            return jsonify({'success': False, 'error': 'Channel not found'}), 404
        
        # Only owner can add moderators
        if channel.get('owner') != session['username']:
            return jsonify({'success': False, 'error': 'Only channel owner can add moderators'}), 403
        
        # User must be a subscriber first
        if username_to_add not in channel.get('subscribers', []):
            return jsonify({'success': False, 'error': 'User must be a subscriber first'}), 400
        
        # Set role to moderator
        result = store.set_member_role(channel_id, username_to_add, 'moderator', session['username'])
        
        if result:
            return jsonify({'success': True, 'message': f'{username_to_add} is now a moderator'})
        else:
            return jsonify({'success': False, 'error': 'Failed to add moderator'}), 500
    except Exception as e:
        print(f"API add moderator error: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@channels_bp.route('/api/channel/<channel_id>/moderator/remove', methods=['POST'])
def api_remove_moderator(channel_id):
    """Remove a moderator from channel (owner only)"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400
    
    username_to_remove = data.get('username', '').strip()
    if not username_to_remove:
        return jsonify({'success': False, 'error': 'Username required'}), 400
    
    try:
        channel = store.get_channel(channel_id)
        if not channel:
            return jsonify({'success': False, 'error': 'Channel not found'}), 404
        
        # Only owner can remove moderators
        if channel.get('owner') != session['username']:
            return jsonify({'success': False, 'error': 'Only channel owner can remove moderators'}), 403
        
        # Set role back to viewer
        result = store.set_member_role(channel_id, username_to_remove, 'viewer', session['username'])
        
        if result:
            return jsonify({'success': True, 'message': f'{username_to_remove} is no longer a moderator'})
        else:
            return jsonify({'success': False, 'error': 'Failed to remove moderator'}), 500
    except Exception as e:
        print(f"API remove moderator error: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@channels_bp.route('/api/channel/create', methods=['POST'])
def api_create_channel():
    """Create a new channel"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    avatar_emoji = data.get('avatar', '📢')
    
    if len(name) < 3:
        return jsonify({'success': False, 'error': 'Channel name must be at least 3 characters'}), 400
    
    try:
        if store.channel_name_exists(name):
            return jsonify({'success': False, 'error': 'Channel name already exists'}), 409
        
        channel = store.create_channel(
            name=name,
            description=description,
            owner=session['username'],
            avatar_emoji=avatar_emoji,
            discoverable=True
        )
        
        return jsonify({
            'success': True,
            'channel': {
                'id': channel.get('id'),
                'name': channel.get('name'),
                'description': channel.get('description'),
                'owner': channel.get('owner')
            }
        }), 201
    except Exception as e:
        print(f"API create channel error: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@channels_bp.route('/api/channel/<channel_id>/post', methods=['POST'])
def api_create_post(channel_id):
    """Create a post in a channel"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    if not store.can_post_in_channel(channel_id, username):
        return jsonify({'success': False, 'error': 'You do not have permission to post'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400
    
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Content required'}), 400
    
    try:
        post = store.create_post(channel_id=channel_id, author=username, content=content)
        return jsonify({
            'success': True,
            'post': {
                'id': post.get('id'),
                'content': post.get('content'),
                'author': post.get('author'),
                'created_at': post.get('timestamp', '')
            }
        }), 201
    except Exception as e:
        print(f"API create post error: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500
