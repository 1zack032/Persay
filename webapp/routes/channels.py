"""
📺 Channel Routes - MIE Optimized

Channel creation, viewing, posting, subscription management,
discoverability settings, and search.
Uses Menza Intelligence Engine for caching.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from webapp.models import store
from webapp.config import Config
from webapp.core import get_engine

channels_bp = Blueprint('channels', __name__)


@channels_bp.route('/channels')
def channels_page():
    """Channel discovery - MIE cached"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    engine = get_engine()
    discover_filter = request.args.get('filter', 'trending')
    period = request.args.get('period', 'daily')
    
    # Cache key for discover data (shared across users, refreshed often)
    discover_key = f"discover_channels:{discover_filter}"
    discover_data = engine.get_cached(discover_key)
    
    if not discover_data:
        discover_data = store.get_discover_channels_rotated(username=username)
        engine.set_cached(discover_key, discover_data, ttl=60)
    
    # User-specific data (shorter cache)
    user_key = f"user_channels_page:{username}"
    user_data = engine.get_cached(user_key)
    
    if not user_data:
        my_channels = store.get_user_channels(username)
        subscribed = store.get_subscribed_channels(username)
        # Roles are already in channel.members dict - no extra queries needed
        for channel in subscribed:
            channel['user_role'] = channel.get('members', {}).get(username, 'viewer')
        user_data = {'my_channels': my_channels, 'subscribed': subscribed}
        engine.set_cached(user_key, user_data, ttl=120)
    
    # Select channels based on filter
    filter_map = {'most_liked': 'most_liked', 'most_viewed': 'most_viewed', 'new': 'new'}
    discover_channels = discover_data.get(filter_map.get(discover_filter, 'trending'), [])
    
    # BATCH: Get all liked channels in one query (N+1 prevention)
    channel_ids = [ch['id'] for ch in discover_channels]
    liked_channels = store.get_liked_channels_batch(channel_ids, username)
    
    for channel in discover_channels:
        channel['liked_by_user'] = channel['id'] in liked_channels
        channel['like_count'] = len(channel.get('likes', []))
    
    return render_template('channels.html',
                         username=username,
                         my_channels=user_data['my_channels'],
                         subscribed_channels=user_data['subscribed'],
                         discover_channels=discover_channels,
                         discover_filter=discover_filter,
                         period=period,
                         trending_channels=discover_data.get('trending', [])[:5])


@channels_bp.route('/channels/search')
def search_channels():
    """Search for channels by name, interest, or category"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    username = session['username']
    
    # If searching by category
    if category:
        results = store.get_channels_by_category(category, limit=20)
        # BATCH: Get liked status in one query
        liked = store.get_liked_channels_batch([ch['id'] for ch in results], username)
        for ch in results:
            ch['liked_by_user'] = ch['id'] in liked
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'results': results,
                'category': category,
                'count': len(results)
            })
        
        return render_template('channels_search.html',
                             username=username,
                             query=query,
                             category=category,
                             results=results,
                             categories=store.get_all_categories())
    
    # Interest-based search
    if len(query) < 1:
        search_results = {'exact_matches': [], 'category_matches': [], 'suggestions': [], 'related_categories': []}
    else:
        search_results = store.search_channels_by_interest(query, limit=20)
        
        # BATCH: Get all channel IDs and liked status in one query
        all_ids = [ch['id'] for key in ['exact_matches', 'category_matches', 'suggestions'] for ch in search_results[key]]
        liked = store.get_liked_channels_batch(all_ids, username)
        for key in ['exact_matches', 'category_matches', 'suggestions']:
            for ch in search_results[key]:
                ch['liked_by_user'] = ch['id'] in liked
    
    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'exact_matches': search_results['exact_matches'],
            'category_matches': search_results['category_matches'],
            'suggestions': search_results['suggestions'],
            'related_categories': search_results['related_categories'],
            'query': query,
            'total_count': len(search_results['exact_matches']) + len(search_results['category_matches']) + len(search_results['suggestions'])
        })
    
    # Otherwise render full page
    all_results = search_results['exact_matches'] + search_results['category_matches'] + search_results['suggestions']
    return render_template('channels_search.html',
                         username=username,
                         query=query,
                         results=all_results,
                         related_categories=search_results['related_categories'],
                         categories=store.get_all_categories())


@channels_bp.route('/channels/categories')
def get_categories():
    """Get all interest categories"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    categories = store.get_all_categories()
    return jsonify({'categories': categories})


@channels_bp.route('/api/channels/search')
def api_search_channels():
    """API endpoint to search channels - OPTIMIZED: single pass, no N+1"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    query = request.args.get('q', '').strip().lower()
    username = session['username']
    include_subscription = request.args.get('include_subscription', 'false') == 'true'
    
    if not query or len(query) < 2:
        return jsonify({'channels': []})
    
    engine = get_engine()
    cache_key = f"channel_search:{query}:{username}"
    cached = engine.get_cached(cache_key)
    if cached:
        return jsonify({'channels': cached})
    
    # Get user's channels in a single batch (combined in get_all_user_channels)
    user_channel_ids = set(ch['id'] for ch in store.get_all_user_channels(username))
    
    # Search channels - use store's optimized search
    search_results = store.search_channels(query, discoverable_only=False, limit=50)
    
    matched_channels = []
    for channel in search_results:
        is_member = channel['id'] in user_channel_ids
        
        # Only include if discoverable OR user is member
        if channel.get('discoverable') or is_member:
            matched_channels.append({
                'id': channel['id'],
                'name': channel['name'],
                'description': channel.get('description', ''),
                'branding': channel.get('branding', {}),
                'subscribers': len(channel.get('subscribers', [])),  # Just count, not full list
                'discoverable': channel.get('discoverable', False),
                'likes': len(channel.get('likes', [])),
                'views': channel.get('views', 0),
                'is_subscribed': is_member if include_subscription else None
            })
    
    # Sort: subscribed first, then by subscriber count
    matched_channels.sort(key=lambda x: (
        -(1 if x.get('is_subscribed') else 0),
        -x.get('subscribers', 0)
    ))
    
    result = matched_channels[:20]
    engine.set_cached(cache_key, result, ttl=30)
    
    return jsonify({'channels': result})


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
        avatar_type = request.form.get('avatar_type', 'emoji')
        avatar_image_data = request.form.get('avatar_image_data', '')
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
            discoverable=discoverable,
            avatar_type=avatar_type,
            avatar_image=avatar_image_data if avatar_type == 'image' else None
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
                         subscribed_channels=subscribed_channels)


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
    
    # Get posts for statistics
    posts = store.get_channel_posts(channel_id)
    total_likes = sum(len(p.get('likes', [])) for p in posts)
    
    return render_template('channel_settings.html',
                         channel=channel,
                         username=username,
                         members_with_roles=members_with_roles,
                         total_likes=total_likes,
                         posts_count=len(posts))


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
