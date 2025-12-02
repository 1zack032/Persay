"""
Bot Store and API Routes
Handles bot browsing, creation, and management
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from webapp.models.store import store
import re

bots_bp = Blueprint('bots', __name__)


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# BOT STORE ROUTES
# ==========================================

@bots_bp.route('/bots')
@login_required
def bot_store():
    """Bot Store - Browse available bots"""
    username = session.get('username')
    category = request.args.get('category')
    
    # Get bots
    if category:
        bots = store.get_approved_bots(category=category)
    else:
        bots = store.get_approved_bots()
    
    featured_bots = store.get_featured_bots(limit=4)
    categories = store.BOT_CATEGORIES
    
    return render_template('bot_store.html',
                         username=username,
                         bots=bots,
                         featured_bots=featured_bots,
                         categories=categories,
                         selected_category=category)


@bots_bp.route('/bots/<bot_id>')
@login_required
def bot_detail(bot_id):
    """Bot detail page"""
    username = session.get('username')
    bot = store.get_bot(bot_id)
    
    if not bot:
        return "Bot not found", 404
    
    # Get user's groups and channels to add bot to
    user_groups = [g for g in store.get_all_groups() 
                   if username in g.get('members', []) and 
                   (username in g.get('admins', []) or username == g.get('owner'))]
    
    user_channels = [c for c in store.get_all_user_channels(username)
                     if store.get_member_role(c['id'], username) == store.ROLE_ADMIN]
    
    return render_template('bot_detail.html',
                         username=username,
                         bot=bot,
                         user_groups=user_groups,
                         user_channels=user_channels)


@bots_bp.route('/bots/<bot_id>/add', methods=['POST'])
@login_required
def add_bot(bot_id):
    """Add bot to a group or channel"""
    username = session.get('username')
    data = request.json
    
    target_type = data.get('type')  # 'group' or 'channel'
    target_id = data.get('target_id')
    
    if target_type == 'group':
        success = store.add_bot_to_group(bot_id, target_id, username)
    elif target_type == 'channel':
        success = store.add_bot_to_channel(bot_id, target_id, username)
    else:
        return jsonify({'success': False, 'error': 'Invalid target type'}), 400
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to add bot. Check permissions.'}), 400


@bots_bp.route('/bots/<bot_id>/remove', methods=['POST'])
@login_required
def remove_bot(bot_id):
    """Remove bot from a group"""
    username = session.get('username')
    data = request.json
    
    target_type = data.get('type')
    target_id = data.get('target_id')
    
    if target_type == 'group':
        success = store.remove_bot_from_group(bot_id, target_id, username)
    else:
        success = False
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to remove bot'}), 400


@bots_bp.route('/bots/<bot_id>/rate', methods=['POST'])
@login_required
def rate_bot(bot_id):
    """Rate a bot"""
    username = session.get('username')
    data = request.json
    
    rating = data.get('rating', 0)
    review = data.get('review', '')
    
    success = store.rate_bot(bot_id, username, rating, review)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to rate bot'}), 400


@bots_bp.route('/bots/<bot_id>/report', methods=['POST'])
@login_required
def report_bot(bot_id):
    """Report a bot for violations"""
    username = session.get('username')
    data = request.json
    
    reason = data.get('reason', '')
    
    if not reason:
        return jsonify({'success': False, 'error': 'Reason required'}), 400
    
    success = store.report_bot(bot_id, username, reason)
    
    if success:
        return jsonify({'success': True, 'message': 'Report submitted for review'})
    else:
        return jsonify({'success': False, 'error': 'Failed to submit report'}), 400


# ==========================================
# DEVELOPER PORTAL ROUTES
# ==========================================

@bots_bp.route('/developers')
def developer_portal():
    """Developer documentation and portal"""
    return render_template('developer_portal.html',
                         username=session.get('username'))


@bots_bp.route('/developers/docs')
def developer_docs():
    """API Documentation"""
    return render_template('developer_docs.html',
                         username=session.get('username'))


@bots_bp.route('/developers/create', methods=['GET', 'POST'])
@login_required
def create_bot():
    """Create a new bot"""
    username = session.get('username')
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Validate username format
        bot_username = data.get('username', '')
        if not bot_username.startswith('@'):
            bot_username = '@' + bot_username
        
        if not re.match(r'^@[a-z0-9_]+$', bot_username):
            return render_template('bot_create.html',
                                 username=username,
                                 error='Invalid bot username. Use only lowercase letters, numbers, and underscores.')
        
        # Check if username is taken
        existing = store.get_bot_by_username(bot_username)
        if existing:
            return render_template('bot_create.html',
                                 username=username,
                                 error='This bot username is already taken.')
        
        # Parse commands
        commands = []
        cmd_count = int(data.get('command_count', 0))
        for i in range(cmd_count):
            cmd = data.get(f'command_{i}')
            desc = data.get(f'command_desc_{i}')
            usage = data.get(f'command_usage_{i}')
            if cmd:
                commands.append({
                    'command': cmd if cmd.startswith('/') else '/' + cmd,
                    'description': desc or '',
                    'usage': usage or ''
                })
        
        data['username'] = bot_username
        data['commands'] = commands
        data['developer_email'] = data.get('developer_email')
        
        bot = store.create_bot(data, username)
        
        return redirect(url_for('bots.my_bots'))
    
    return render_template('bot_create.html',
                         username=username,
                         categories=store.BOT_CATEGORIES)


@bots_bp.route('/developers/my-bots')
@login_required
def my_bots():
    """List developer's bots"""
    username = session.get('username')
    
    all_bots = store.get_all_bots()
    my_bots = [b for b in all_bots if b.get('developer') == username]
    
    return render_template('my_bots.html',
                         username=username,
                         bots=my_bots)


@bots_bp.route('/developers/my-bots/<bot_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bot(bot_id):
    """Edit a bot"""
    username = session.get('username')
    bot = store.get_bot(bot_id)
    
    if not bot or bot.get('developer') != username:
        return "Bot not found or access denied", 404
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Parse commands
        commands = []
        cmd_count = int(data.get('command_count', 0))
        for i in range(cmd_count):
            cmd = data.get(f'command_{i}')
            desc = data.get(f'command_desc_{i}')
            usage = data.get(f'command_usage_{i}')
            if cmd:
                commands.append({
                    'command': cmd if cmd.startswith('/') else '/' + cmd,
                    'description': desc or '',
                    'usage': usage or ''
                })
        
        data['commands'] = commands
        store.update_bot(bot_id, data, username)
        
        return redirect(url_for('bots.my_bots'))
    
    return render_template('bot_edit.html',
                         username=username,
                         bot=bot,
                         categories=store.BOT_CATEGORIES)


# ==========================================
# BOT API ENDPOINTS
# ==========================================

@bots_bp.route('/api/bot/send', methods=['POST'])
def bot_send_message():
    """API endpoint for bots to send messages"""
    # Authenticate bot
    api_key = request.headers.get('X-Bot-API-Key')
    bot_id = request.headers.get('X-Bot-ID')
    
    if not api_key or not bot_id:
        return jsonify({'error': 'Missing authentication'}), 401
    
    if not store.verify_bot_api_key(bot_id, api_key):
        return jsonify({'error': 'Invalid API key'}), 401
    
    bot = store.get_bot(bot_id)
    if bot['status'] != store.BOT_STATUS_APPROVED:
        return jsonify({'error': 'Bot is not approved'}), 403
    
    data = request.json
    target_type = data.get('type')  # 'group' or 'channel'
    target_id = data.get('target_id')
    message = data.get('message')
    
    if not all([target_type, target_id, message]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify bot has access to target
    if target_type == 'group':
        if target_id not in bot.get('groups', []):
            return jsonify({'error': 'Bot not in this group'}), 403
    elif target_type == 'channel':
        if target_id not in bot.get('channels', []):
            return jsonify({'error': 'Bot not in this channel'}), 403
    
    # Store the message (this would trigger socket events in real implementation)
    msg = {
        'sender': bot['username'],
        'content': message,
        'is_bot': True,
        'bot_id': bot_id,
        'timestamp': store.now()
    }
    
    if target_type == 'group':
        store.add_message(target_id, msg['sender'], msg['content'])
    
    return jsonify({'success': True, 'message_id': store.generate_id()})


@bots_bp.route('/api/bot/webhook-test', methods=['POST'])
def test_webhook():
    """Test endpoint for developers to verify webhook setup"""
    api_key = request.headers.get('X-Bot-API-Key')
    bot_id = request.headers.get('X-Bot-ID')
    
    if not api_key or not bot_id:
        return jsonify({'error': 'Missing authentication'}), 401
    
    if not store.verify_bot_api_key(bot_id, api_key):
        return jsonify({'error': 'Invalid API key'}), 401
    
    return jsonify({
        'success': True,
        'message': 'Webhook test successful',
        'bot_id': bot_id
    })

