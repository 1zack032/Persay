"""
📺 Channel Routes - MIE v2.0 Optimized
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from webapp.models import store
from webapp.config import Config
from webapp.core.menza_intelligence_engine import MIE, cached, rate_limited

channels_bp = Blueprint('channels', __name__)


@channels_bp.route('/channels')
def channels_page():
    """Channel discovery - fully optimized with MIE v2.0"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    discover_filter = request.args.get('filter', 'trending')
    
    MIE.record_request()
    MIE.record_access(username, 'channels')
    
    # Get discover data with hot caching
    discover_cache_key = f"discover:{discover_filter}"
    discover_data = MIE.get_cached_response(discover_cache_key)
    
    if discover_data is None:
        try:
            discover_data = store.get_discover_channels_rotated(username=username)
            MIE.cache_response(discover_cache_key, discover_data, ttl=60, priority='high')
        except Exception:
            discover_data = {'trending': [], 'most_liked': [], 'most_viewed': [], 'new': []}
    
    # Get user channels with high priority
    user_cache_key = f"user_channels_full:{username}"
    user_data = MIE.get_cached_response(user_cache_key)
    
    if user_data is None:
        try:
            my_channels = store.get_user_channels(username)
            subscribed = store.get_subscribed_channels(username)
            for channel in subscribed:
                channel['user_role'] = channel.get('members', {}).get(username, 'viewer')
            user_data = {'my_channels': my_channels, 'subscribed': subscribed}
            MIE.cache_response(user_cache_key, user_data, ttl=120, priority='high')
        except Exception:
            user_data = {'my_channels': [], 'subscribed': []}
    
    # Get channels for display
    filter_map = {'most_liked': 'most_liked', 'most_viewed': 'most_viewed', 'new': 'new'}
    discover_channels = discover_data.get(filter_map.get(discover_filter, 'trending'), [])
    
    # Batch get liked status
    if discover_channels:
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
                         trending_channels=discover_data.get('trending', [])[:5])


@channels_bp.route('/channels/search')
@rate_limited
def search_channels():
    """Search channels - optimized with pagination"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    page = int(request.args.get('page', 1))
    username = session['username']
    
    if category:
        cache_key = f"channel_category:{category}"
        results = MIE.get_cached_response(cache_key)
        
        if results is None:
            results = store.get_channels_by_category(category, limit=50)
            MIE.cache_response(cache_key, results, ttl=60)
        
        # Paginate results
        paginated = MIE.paginate_response(results, page, per_page=20)
        results = paginated['data']
        
        liked = store.get_liked_channels_batch([ch['id'] for ch in results], username) if results else set()
        for ch in results:
            ch['liked_by_user'] = ch['id'] in liked
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'results': results, 
                'category': category, 
                'count': len(results),
                'pagination': paginated['pagination']
            })
        
        return render_template('channels_search.html',
                             username=username,
                             query=query,
                             category=category,
                             results=results,
                             categories=store.get_all_categories())
    
    if len(query) < 1:
        search_results = {'exact_matches': [], 'category_matches': [], 'suggestions': [], 'related_categories': []}
    else:
        cache_key = f"channel_search:{query.lower()}"
        search_results = MIE.get_cached_response(cache_key)
        
        if search_results is None:
            search_results = store.search_channels_by_interest(query, limit=50)
            MIE.cache_response(cache_key, search_results, ttl=30)
        
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
    """Get all categories - long cache"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    cache_key = "all_categories"
    categories = MIE.get_cached_response(cache_key)
    
    if categories is None:
        categories = store.get_all_categories()
        MIE.cache_response(cache_key, categories, ttl=300, priority='high')
    
    return jsonify({'categories': categories})


@channels_bp.route('/api/channels/search')
@rate_limited
def api_search_channels():
    """API search - optimized response"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    query = request.args.get('q', '').strip().lower()
    username = session['username']
    
    if not query or len(query) < 2:
        return jsonify({'channels': []})
    
    cache_key = f"api_channel_search:{query}:{username}"
    cached_result = MIE.get_cached_response(cache_key)
    if cached_result is not None:
        return jsonify({'channels': cached_result})
    
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
    result = matched[:20]
    
    MIE.cache_response(cache_key, result, ttl=30)
    return jsonify({'channels': result})


@channels_bp.route('/channel/<channel_id>/like', methods=['POST'])
@rate_limited
def like_channel(channel_id):
    if 'username' not in session:
        return jsonify({'success': False}), 401
    
    # Invalidate related caches
    username = session['username']
    MIE.invalidate_cache(f"discover:")
    MIE.invalidate_cache(f"user_channels:{username}")
    
    return jsonify(store.like_channel(channel_id, username))


@channels_bp.route('/channel/<channel_id>/unlike', methods=['POST'])
@rate_limited
def unlike_channel(channel_id):
    if 'username' not in session:
        return jsonify({'success': False}), 401
    
    username = session['username']
    MIE.invalidate_cache(f"discover:")
    MIE.invalidate_cache(f"user_channels:{username}")
    
    return jsonify(store.unlike_channel(channel_id, username))


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
        
        # Invalidate caches
        MIE.invalidate_cache(f"user_channels:{session['username']}")
        MIE.invalidate_cache("discover:")
        
        return redirect(url_for('channels.view_channel', channel_id=channel['id']))
    
    return render_template('channel_create.html', username=session['username'])


@channels_bp.route('/channel/<channel_id>')
def view_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    MIE.record_access(username, f'channel:{channel_id}')
    
    # Cache channel data
    channel_cache_key = f"channel_data:{channel_id}"
    channel = MIE.get_cached_response(channel_cache_key)
    
    if channel is None:
        channel = store.get_channel(channel_id)
        if channel:
            MIE.cache_response(channel_cache_key, channel, ttl=60)
    
    if not channel:
        return redirect(url_for('channels.channels_page'))
    
    is_owner = channel['owner'] == username
    user_role = store.get_member_role(channel_id, username)
    can_post = store.can_post_in_channel(channel_id, username)
    can_manage = store.can_manage_channel(channel_id, username)
    members_with_roles = store.get_channel_members_with_roles(channel_id)
    
    # Get user's channels from cache
    my_channels_key = f"user_channels:{username}"
    my_channels = MIE.get_cached_response(my_channels_key)
    if my_channels is None:
        my_channels = store.get_user_channels(username)
        MIE.cache_response(my_channels_key, my_channels, ttl=120)
    
    subscribed_channels = store.get_subscribed_channels(username)
    
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
        
        # Invalidate caches
        MIE.invalidate_cache(f"channel_data:{channel_id}")
        MIE.invalidate_cache("discover:")
        
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
@rate_limited
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
@rate_limited
def subscribe_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    store.subscribe_to_channel(channel_id, username)
    
    # Invalidate caches
    MIE.invalidate_cache(f"user_channels:{username}")
    MIE.invalidate_cache(f"channel_data:{channel_id}")
    
    return redirect(url_for('channels.view_channel', channel_id=channel_id))


@channels_bp.route('/channel/<channel_id>/unsubscribe', methods=['POST'])
@rate_limited
def unsubscribe_channel(channel_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    store.unsubscribe_from_channel(channel_id, username)
    
    # Invalidate caches
    MIE.invalidate_cache(f"user_channels:{username}")
    MIE.invalidate_cache(f"channel_data:{channel_id}")
    
    return redirect(url_for('channels.view_channel', channel_id=channel_id))
