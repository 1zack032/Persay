"""
📺 Channel Routes - PRODUCTION
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
    
    # Get discover channels directly (no broken caching)
    try:
        discover_data = store.get_discover_channels_rotated(username=username)
    except Exception:
        discover_data = {'trending': [], 'most_liked': [], 'most_viewed': [], 'new': []}
    
    # Get user channels
    try:
        my_channels = store.get_user_channels(username)
        subscribed = store.get_subscribed_channels(username)
        for channel in subscribed:
            channel['user_role'] = channel.get('members', {}).get(username, 'viewer')
    except Exception:
        my_channels = []
        subscribed = []
    
    # Get channels for display
    filter_map = {'most_liked': 'most_liked', 'most_viewed': 'most_viewed', 'new': 'new'}
    discover_channels = discover_data.get(filter_map.get(discover_filter, 'trending'), [])
    
    # Batch get liked status
    channel_ids = [ch['id'] for ch in discover_channels]
    liked_channels = store.get_liked_channels_batch(channel_ids, username) if channel_ids else set()
    
    for channel in discover_channels:
        channel['liked_by_user'] = channel['id'] in liked_channels
        channel['like_count'] = len(channel.get('likes', []))
    
    return render_template('channels.html',
                         username=username,
                         my_channels=my_channels,
                         subscribed_channels=subscribed,
                         discover_channels=discover_channels,
                         discover_filter=discover_filter,
                         trending_channels=discover_data.get('trending', [])[:5])


@channels_bp.route('/channels/search')
def search_channels():
    """Search for channels"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    username = session['username']
    
    if category:
        results = store.get_channels_by_category(category, limit=20)
        liked = store.get_liked_channels_batch([ch['id'] for ch in results], username)
        for ch in results:
            ch['liked_by_user'] = ch['id'] in liked
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'results': results, 'category': category, 'count': len(results)})
        
        return render_template('channels_search.html',
                             username=username,
                             query=query,
                             category=category,
                             results=results,
                             categories=store.get_all_categories())
    
    if len(query) < 1:
        search_results = {'exact_matches': [], 'category_matches': [], 'suggestions': [], 'related_categories': []}
    else:
        search_results = store.search_channels_by_interest(query, limit=20)
        all_ids = [ch['id'] for key in ['exact_matches', 'category_matches', 'suggestions'] for ch in search_results.get(key, [])]
        liked = store.get_liked_channels_batch(all_ids, username) if all_ids else set()
        for key in ['exact_matches', 'category_matches', 'suggestions']:
            for ch in search_results.get(key, []):
                ch['liked_by_user'] = ch['id'] in liked
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'exact_matches': search_results.get('exact_matches', []),
            'category_matches': search_results.get('category_matches', []),
            'suggestions': search_results.get('suggestions', []),
            'related_categories': search_results.get('related_categories', []),
            'query': query
        })
    
    all_results = search_results.get('exact_matches', []) + search_results.get('category_matches', []) + search_results.get('suggestions', [])
    return render_template('channels_search.html',
                         username=username,
                         query=query,
                         results=all_results,
                         related_categories=search_results.get('related_categories', []),
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
    username = session['username']
    
    if not query or len(query) < 2:
        return jsonify({'channels': []})
    
    try:
        user_channel_ids = set(ch['id'] for ch in store.get_all_user_channels(username))
        search_results = store.search_channels(query, discoverable_only=False, limit=50)
    except Exception:
        return jsonify({'channels': []})
    
    matched = []
    for channel in search_results:
        is_member = channel['id'] in user_channel_ids
        if channel.get('discoverable') or is_member:
            matched.append({
                'id': channel['id'],
                'name': channel['name'],
                'description': channel.get('description', ''),
                'branding': channel.get('branding', {}),
                'subscribers': len(channel.get('subscribers', [])),
                'discoverable': channel.get('discoverable', False),
                'is_subscribed': is_member
            })
    
    matched.sort(key=lambda x: (-1 if x.get('is_subscribed') else 0, -x.get('subscribers', 0)))
    return jsonify({'channels': matched[:20]})


@channels_bp.route('/channel/<channel_id>/like', methods=['POST'])
def like_channel(channel_id):
    if 'username' not in session:
        return jsonify({'success': False}), 401
    return jsonify(store.like_channel(channel_id, session['username']))


@channels_bp.route('/channel/<channel_id>/unlike', methods=['POST'])
def unlike_channel(channel_id):
    if 'username' not in session:
        return jsonify({'success': False}), 401
    return jsonify(store.unlike_channel(channel_id, session['username']))


@channels_bp.route('/channel/create', methods=['GET', 'POST'])
def create_channel():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        accent_color = request.form.get('accent_color', Config.DEFAULT_ACCENT_COLOR)
        avatar_emoji = request.form.get('avatar_emoji', Config.DEFAULT_AVATAR_EMOJI)
        avatar_type = request.form.get('avatar_type', 'emoji')
        avatar_image_data = request.form.get('avatar_image_data', '')
        discoverable = request.form.get('discoverable') == 'on'
        invited_members_json = request.form.get('invited_members', '[]')
        
        import json
        try:
            invited_members = json.loads(invited_members_json)
        except:
            invited_members = []
        
        if len(name) < Config.MIN_CHANNEL_NAME_LENGTH:
            return render_template('channel_create.html', 
                error=f"Channel name must be at least {Config.MIN_CHANNEL_NAME_LENGTH} characters",
                username=session['username'])
        
        if store.channel_name_exists(name):
            return render_template('channel_create.html', 
                error="A channel with this name already exists",
                username=session['username'])
        
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
        
        for member in invited_members:
            member_username = member.get('username', '').strip()
            role = member.get('role', 'viewer')
            if role not in ['admin', 'mod', 'viewer']:
                role = 'viewer'
            if member_username and store.user_exists(member_username):
                store.subscribe_to_channel(channel['id'], member_username, role)
        
        return redirect(url_for('channels.view_channel', channel_id=channel['id']))
    
    return render_template('channel_create.html', username=session['username'])


@channels_bp.route('/channel/<channel_id>')
def view_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    channel = store.get_channel(channel_id)
    if not channel:
        return redirect(url_for('channels.channels_page'))
    
    username = session['username']
    is_owner = channel['owner'] == username
    user_role = store.get_member_role(channel_id, username)
    can_post = store.can_post_in_channel(channel_id, username)
    can_manage = store.can_manage_channel(channel_id, username)
    members_with_roles = store.get_channel_members_with_roles(channel_id)
    
    try:
        my_channels = store.get_user_channels(username)
        subscribed_channels = store.get_subscribed_channels(username)
    except Exception:
        my_channels = []
        subscribed_channels = []
    
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
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    channel = store.get_channel(channel_id)
    if not channel:
        return redirect(url_for('channels.channels_page'))
    
    username = session['username']
    if not store.can_manage_channel(channel_id, username):
        return redirect(url_for('channels.view_channel', channel_id=channel_id))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'toggle_discoverable':
            store.set_channel_discoverable(channel_id, not channel.get('discoverable', True))
        elif action == 'update_member_role':
            member_username = request.form.get('member_username', '').strip()
            new_role = request.form.get('new_role', 'viewer')
            if new_role in ['admin', 'mod', 'viewer']:
                store.set_member_role(channel_id, member_username, new_role, username)
        
        return redirect(url_for('channels.channel_settings', channel_id=channel_id))
    
    members_with_roles = store.get_channel_members_with_roles(channel_id)
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
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    channel = store.get_channel(channel_id)
    if not channel or not store.can_post_in_channel(channel_id, session['username']):
        return redirect(url_for('channels.view_channel', channel_id=channel_id))
    
    content = request.form.get('content', '').strip()
    linked_post_id = request.form.get('linked_post', None) or None
    
    if content:
        try:
            from webapp.app import socketio
            post = store.create_post(channel_id=channel_id, author=session['username'], content=content, linked_post=linked_post_id)
            socketio.emit('new_channel_post', {'channel_id': channel_id, 'post': post}, room=f'channel_{channel_id}')
        except Exception as e:
            print(f"Post error: {e}", flush=True)
    
    return redirect(url_for('channels.view_channel', channel_id=channel_id))


@channels_bp.route('/channel/<channel_id>/subscribe', methods=['POST'])
def subscribe_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    store.subscribe_to_channel(channel_id, session['username'])
    return redirect(url_for('channels.view_channel', channel_id=channel_id))


@channels_bp.route('/channel/<channel_id>/unsubscribe', methods=['POST'])
def unsubscribe_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    store.unsubscribe_from_channel(channel_id, session['username'])
    return redirect(url_for('channels.view_channel', channel_id=channel_id))
