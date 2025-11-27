"""
📺 Channel Routes

Channel creation, viewing, posting, subscription management,
discoverability settings, and search.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from webapp.models import store
from webapp.config import Config

channels_bp = Blueprint('channels', __name__)


@channels_bp.route('/channels')
def channels_page():
    """Channel discovery and management page"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    
    # Get filter from query params
    discover_filter = request.args.get('filter', 'trending')
    period = request.args.get('period', 'daily')
    
    # Get user's channels
    my_channels = store.get_user_channels(username)
    subscribed = store.get_subscribed_channels(username)
    
    # Add user's role to subscribed channels
    for channel in subscribed:
        channel['user_role'] = store.get_member_role(channel['id'], username)
    
    # Get discover channels with rotation algorithm
    discover_data = store.get_discover_channels_rotated(username=username)
    
    # Select channels based on filter
    if discover_filter == 'most_liked':
        discover_channels = discover_data['most_liked']
    elif discover_filter == 'most_viewed':
        discover_channels = discover_data['most_viewed']
    elif discover_filter == 'new':
        discover_channels = discover_data['new']
    else:  # trending (default)
        discover_channels = discover_data['trending']
    
    # Add like status for current user
    for channel in discover_channels:
        channel['liked_by_user'] = store.has_liked_channel(channel['id'], username)
        channel['like_count'] = len(channel.get('likes', []))
    
    return render_template('channels.html',
                         username=username,
                         my_channels=my_channels,
                         subscribed_channels=subscribed,
                         discover_channels=discover_channels,
                         discover_filter=discover_filter,
                         period=period,
                         trending_channels=discover_data.get('trending', [])[:5])


@channels_bp.route('/channels/search')
def search_channels():
    """Search for channels"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    query = request.args.get('q', '').strip()
    username = session['username']
    
    if len(query) < 2:
        results = []
    else:
        results = store.search_channels(query, discoverable_only=True, limit=20)
    
    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'results': results,
            'query': query,
            'count': len(results)
        })
    
    # Otherwise render full page
    return render_template('channels_search.html',
                         username=username,
                         query=query,
                         results=results)


@channels_bp.route('/channel/<channel_id>/like', methods=['POST'])
def like_channel(channel_id):
    """Like a channel"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    username = session['username']
    result = store.like_channel(channel_id, username)
    
    return jsonify(result)


@channels_bp.route('/channel/<channel_id>/unlike', methods=['POST'])
def unlike_channel(channel_id):
    """Unlike a channel"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    username = session['username']
    result = store.unlike_channel(channel_id, username)
    
    return jsonify(result)


@channels_bp.route('/channel/create', methods=['GET', 'POST'])
def create_channel():
    """Create a new channel"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        accent_color = request.form.get('accent_color', Config.DEFAULT_ACCENT_COLOR)
        avatar_emoji = request.form.get('avatar_emoji', Config.DEFAULT_AVATAR_EMOJI)
        discoverable = request.form.get('discoverable') == 'on'  # Checkbox
        invited_members_json = request.form.get('invited_members', '[]')
        
        # Parse invited members
        import json
        try:
            invited_members = json.loads(invited_members_json)
        except:
            invited_members = []
        
        # Validation
        if len(name) < Config.MIN_CHANNEL_NAME_LENGTH:
            return render_template('channel_create.html', 
                error=f"Channel name must be at least {Config.MIN_CHANNEL_NAME_LENGTH} characters")
        
        if store.channel_name_exists(name):
            return render_template('channel_create.html',
                error="A channel with this name already exists")
        
        # Create channel
        channel = store.create_channel(
            name=name,
            description=description,
            owner=session['username'],
            accent_color=accent_color,
            avatar_emoji=avatar_emoji,
            discoverable=discoverable
        )
        
        # Add invited members with their roles
        for member in invited_members:
            username = member.get('username', '').strip()
            role = member.get('role', 'viewer')
            
            # Validate role
            if role not in ['admin', 'mod', 'viewer']:
                role = 'viewer'
            
            # Only add if user exists
            if username and store.user_exists(username):
                store.subscribe_to_channel(channel['id'], username, role)
        
        return redirect(url_for('channels.view_channel', channel_id=channel['id']))
    
    return render_template('channel_create.html')


@channels_bp.route('/channel/<channel_id>')
def view_channel(channel_id):
    """View a channel and its posts"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    channel = store.get_channel(channel_id)
    if not channel:
        return redirect(url_for('channels.channels_page'))
    
    username = session['username']
    is_owner = channel['owner'] == username
    
    # Get user's role and permissions
    user_role = store.get_member_role(channel_id, username)
    can_post = store.can_post_in_channel(channel_id, username)
    can_manage = store.can_manage_channel(channel_id, username)
    
    # Get all members with roles for display
    members_with_roles = store.get_channel_members_with_roles(channel_id)
    
    # Get user's channels for sidebar
    my_channels = store.get_user_channels(username)
    subscribed_channels = store.get_subscribed_channels(username)
    
    # Increment view count (only for non-owners and subscribers)
    if not is_owner:
        store.increment_channel_views(channel_id)
    
    return render_template('channel_view.html',
                         channel=channel,
                         posts=store.get_channel_posts(channel_id),
                         username=username,
                         is_owner=is_owner,
                         is_subscribed=(username in channel.get('subscribers', [])),
                         user_role=user_role,
                         can_post=can_post,
                         can_manage=can_manage,
                         members_with_roles=members_with_roles,
                         my_channels=my_channels,
                         subscribed_channels=subscribed_channels,
                         channel_posts=store.channel_posts)


@channels_bp.route('/channel/<channel_id>/settings', methods=['GET', 'POST'])
def channel_settings(channel_id):
    """Channel settings page (admins only)"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    channel = store.get_channel(channel_id)
    if not channel:
        return redirect(url_for('channels.channels_page'))
    
    username = session['username']
    
    # Only admins can access settings
    if not store.can_manage_channel(channel_id, username):
        return redirect(url_for('channels.view_channel', channel_id=channel_id))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'toggle_discoverable':
            current = channel.get('discoverable', True)
            store.set_channel_discoverable(channel_id, not current)
        
        elif action == 'update_branding':
            accent_color = request.form.get('accent_color', channel['branding']['accent_color'])
            avatar_emoji = request.form.get('avatar_emoji', channel['branding']['avatar_emoji'])
            channel['branding']['accent_color'] = accent_color
            channel['branding']['avatar_emoji'] = avatar_emoji
        
        elif action == 'update_description':
            description = request.form.get('description', '').strip()
            channel['description'] = description
        
        elif action == 'update_member_role':
            member_username = request.form.get('member_username', '').strip()
            new_role = request.form.get('new_role', 'viewer')
            
            # Validate role
            if new_role in ['admin', 'mod', 'viewer']:
                store.set_member_role(channel_id, member_username, new_role, username)
        
        return redirect(url_for('channels.channel_settings', channel_id=channel_id))
    
    # Get all members with their roles
    members_with_roles = store.get_channel_members_with_roles(channel_id)
    
    return render_template('channel_settings.html',
                         channel=channel,
                         username=username,
                         members_with_roles=members_with_roles,
                         channel_posts=store.channel_posts)


@channels_bp.route('/channel/<channel_id>/post', methods=['POST'])
def create_post(channel_id):
    """Create a new post in a channel"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    channel = store.get_channel(channel_id)
    if not channel:
        return redirect(url_for('channels.channels_page'))
    
    username = session['username']
    
    # Only admins and moderators can post
    if not store.can_post_in_channel(channel_id, username):
        return redirect(url_for('channels.view_channel', channel_id=channel_id))
    
    content = request.form.get('content', '').strip()
    linked_post_id = request.form.get('linked_post', None) or None
    
    if content:
        # Import socketio here to avoid circular imports
        from webapp.app import socketio
        
        post = store.create_post(
            channel_id=channel_id,
            author=session['username'],
            content=content,
            linked_post=linked_post_id
        )
        
        # Notify subscribers via WebSocket
        socketio.emit('new_channel_post', {
            'channel_id': channel_id,
            'post': post
        }, room=f'channel_{channel_id}')
    
    return redirect(url_for('channels.view_channel', channel_id=channel_id))


@channels_bp.route('/channel/<channel_id>/subscribe', methods=['POST'])
def subscribe_channel(channel_id):
    """Subscribe to a channel"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    store.subscribe_to_channel(channel_id, session['username'])
    return redirect(url_for('channels.view_channel', channel_id=channel_id))


@channels_bp.route('/channel/<channel_id>/unsubscribe', methods=['POST'])
def unsubscribe_channel(channel_id):
    """Unsubscribe from a channel"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    store.unsubscribe_from_channel(channel_id, session['username'])
    return redirect(url_for('channels.view_channel', channel_id=channel_id))
