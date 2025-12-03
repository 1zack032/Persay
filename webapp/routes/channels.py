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
    
    content = request.form.get('content', '').strip()
    if content:
        try:
            store.create_post(channel_id=channel_id, author=session['username'], content=content)
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
