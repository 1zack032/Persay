"""
🤖 Bot Store and API Routes

Handles bot browsing, creation, and management.
PREMIUM FEATURE - Requires subscription for full access.

Security Features:
- API key hashing
- Webhook signature verification
- Rate limiting
- Automated security scanning
- Admin approval workflow
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
from webapp.models.store import store
from webapp.utils.bot_security import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
    generate_webhook_signature,
    verify_webhook_signature,
    generate_webhook_headers,
    BotPermissions,
    BotSecurityScanner,
    BotRateLimiter,
    BotResponseCache,
    PremiumFeatures,
    BotVersioning,
    BotAnalytics
)
import re

bots_bp = Blueprint('bots', __name__)


# ==========================================
# DECORATORS
# ==========================================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def premium_required(f):
    """Decorator to require premium subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        
        username = session['username']
        user = store.get_user(username)
        
        if not user or not user.get('premium', False):
            if request.is_json:
                return jsonify({
                    'error': 'Premium subscription required',
                    'upgrade_url': url_for('settings.upgrade')
                }), 403
            flash('Bot Store is a premium feature. Please upgrade to access.', 'warning')
            return redirect(url_for('settings.upgrade'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        
        username = session['username']
        user = store.get_user(username)
        
        if not user or not user.get('is_admin', False):
            return "Access denied", 403
        
        return f(*args, **kwargs)
    return decorated_function


def rate_limit_bot_api(f):
    """Decorator to apply rate limiting to bot API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        bot_id = request.headers.get('X-Bot-ID')
        if bot_id:
            allowed, info = BotRateLimiter.check_rate_limit(bot_id)
            
            # Add rate limit headers to response
            response = None
            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': info['retry_after']
                })
                response.status_code = 429
            else:
                response = f(*args, **kwargs)
            
            # Add headers
            if hasattr(response, 'headers'):
                for key, value in BotRateLimiter.get_rate_limit_headers(info).items():
                    response.headers[key] = value
            
            return response
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# BOT STORE ROUTES (PREMIUM)
# ==========================================

@bots_bp.route('/bots')
@login_required
@premium_required
def bot_store():
    """Bot Store - Browse available bots (Premium Feature)"""
    username = session.get('username')
    category = request.args.get('category')
    
    # Get bots
    if category:
        bots = store.get_approved_bots(category=category)
    else:
        bots = store.get_approved_bots()
    
    featured_bots = store.get_featured_bots(limit=4)
    categories = store.BOT_CATEGORIES
    
    # Get user's premium status
    user = store.get_user(username)
    is_premium = user.get('premium', False) if user else False
    
    return render_template('bot_store.html',
                         username=username,
                         bots=bots,
                         featured_bots=featured_bots,
                         categories=categories,
                         selected_category=category,
                         is_premium=is_premium,
                         permission_scopes=BotPermissions.get_all_scopes())


@bots_bp.route('/bots/<bot_id>')
@login_required
@premium_required
def bot_detail(bot_id):
    """Bot detail page"""
    username = session.get('username')
    bot = store.get_bot(bot_id)
    
    if not bot:
        return "Bot not found", 404
    
    # Track view
    BotAnalytics.track_event(bot_id, 'view', {'user': username})
    
    # Get user's groups and channels to add bot to
    user_groups = [g for g in store.get_all_groups() 
                   if username in g.get('members', []) and 
                   (username in g.get('admins', []) or username == g.get('owner'))]
    
    user_channels = [c for c in store.get_all_user_channels(username)
                     if store.get_member_role(c['id'], username) == store.ROLE_ADMIN]
    
    # Get permission info
    permission_details = []
    for perm in bot.get('permissions', []):
        info = BotPermissions.get_scope_info(perm)
        if info:
            permission_details.append({**info, 'scope': perm})
    
    return render_template('bot_detail.html',
                         username=username,
                         bot=bot,
                         user_groups=user_groups,
                         user_channels=user_channels,
                         permission_details=permission_details,
                         risk_level=BotPermissions.get_risk_level(bot.get('permissions', [])))


@bots_bp.route('/bots/<bot_id>/add', methods=['POST'])
@login_required
@premium_required
def add_bot(bot_id):
    """Add bot to a group or channel"""
    username = session.get('username')
    data = request.json
    
    target_type = data.get('type')
    target_id = data.get('target_id')
    
    # Track installation
    BotAnalytics.track_event(bot_id, 'install', {
        'user': username,
        'target_type': target_type,
        'target_id': target_id
    })
    
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
@premium_required
def remove_bot(bot_id):
    """Remove bot from a group"""
    username = session.get('username')
    data = request.json
    
    target_type = data.get('type')
    target_id = data.get('target_id')
    
    # Track uninstall
    BotAnalytics.track_event(bot_id, 'uninstall', {
        'user': username,
        'target_type': target_type
    })
    
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
@premium_required
def rate_bot(bot_id):
    """Rate a bot"""
    username = session.get('username')
    data = request.json
    
    rating = data.get('rating', 0)
    review = data.get('review', '')
    
    success = store.rate_bot(bot_id, username, rating, review)
    
    if success:
        BotAnalytics.track_event(bot_id, 'rating', {'user': username, 'rating': rating})
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to rate bot'}), 400


@bots_bp.route('/bots/<bot_id>/report', methods=['POST'])
@login_required
@premium_required
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
    username = session.get('username')
    user = store.get_user(username) if username else None
    is_premium = user.get('premium', False) if user else False
    
    return render_template('developer_portal.html',
                         username=username,
                         is_premium=is_premium)


@bots_bp.route('/developers/docs')
def developer_docs():
    """API Documentation"""
    return render_template('developer_docs.html',
                         username=session.get('username'),
                         permission_scopes=BotPermissions.get_all_scopes())


@bots_bp.route('/developers/create', methods=['GET', 'POST'])
@login_required
@premium_required
def create_bot():
    """Create a new bot (Premium Feature)"""
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
                                 categories=store.BOT_CATEGORIES,
                                 permission_scopes=BotPermissions.get_all_scopes(),
                                 error='Invalid bot username. Use only lowercase letters, numbers, and underscores.')
        
        # Check if username is taken
        existing = store.get_bot_by_username(bot_username)
        if existing:
            return render_template('bot_create.html',
                                 username=username,
                                 categories=store.BOT_CATEGORIES,
                                 permission_scopes=BotPermissions.get_all_scopes(),
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
        
        # Parse permissions
        permissions = request.form.getlist('permissions')
        if not permissions:
            permissions = BotPermissions.DEFAULT_SCOPES
        
        # Validate permissions
        valid, invalid = BotPermissions.validate_scopes(permissions)
        if not valid:
            return render_template('bot_create.html',
                                 username=username,
                                 categories=store.BOT_CATEGORIES,
                                 permission_scopes=BotPermissions.get_all_scopes(),
                                 error=f'Invalid permissions: {", ".join(invalid)}')
        
        data['username'] = bot_username
        data['commands'] = commands
        data['permissions'] = permissions
        data['developer_email'] = data.get('developer_email')
        
        # Generate secure API key
        raw_api_key, hashed_api_key = generate_api_key()
        data['api_key_hash'] = hashed_api_key
        
        # Run security scan
        scan_result = BotSecurityScanner.scan_bot(data)
        data['security_scan'] = scan_result
        
        # Create bot with version
        data['version'] = BotVersioning.generate_version()
        
        bot = store.create_bot_secure(data, username, hashed_api_key)
        
        # Store the raw API key in session to show once
        session['new_bot_api_key'] = raw_api_key
        session['new_bot_id'] = bot['bot_id']
        
        return redirect(url_for('bots.bot_created', bot_id=bot['bot_id']))
    
    return render_template('bot_create.html',
                         username=username,
                         categories=store.BOT_CATEGORIES,
                         permission_scopes=BotPermissions.get_all_scopes())


@bots_bp.route('/developers/bot-created/<bot_id>')
@login_required
@premium_required
def bot_created(bot_id):
    """Show API key after bot creation (one-time view)"""
    username = session.get('username')
    
    # Get API key from session (one-time display)
    api_key = session.pop('new_bot_api_key', None)
    stored_bot_id = session.pop('new_bot_id', None)
    
    if not api_key or stored_bot_id != bot_id:
        flash('API key can only be viewed once after creation.', 'warning')
        return redirect(url_for('bots.my_bots'))
    
    bot = store.get_bot(bot_id)
    if not bot or bot.get('developer') != username:
        return "Bot not found", 404
    
    return render_template('bot_created.html',
                         username=username,
                         bot=bot,
                         api_key=api_key)


@bots_bp.route('/developers/my-bots')
@login_required
@premium_required
def my_bots():
    """List developer's bots"""
    username = session.get('username')
    
    all_bots = store.get_all_bots()
    my_bots_list = [b for b in all_bots if b.get('developer') == username]
    
    # Get analytics for each bot
    for bot in my_bots_list:
        bot['analytics'] = BotAnalytics.get_stats(bot['bot_id'], days=7)
    
    return render_template('my_bots.html',
                         username=username,
                         bots=my_bots_list)


@bots_bp.route('/developers/my-bots/<bot_id>/edit', methods=['GET', 'POST'])
@login_required
@premium_required
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
        
        # Update version
        data['version'] = BotVersioning.generate_version()
        
        # Store version snapshot
        version_snapshot = BotVersioning.create_version_snapshot(bot)
        store.add_bot_version_history(bot_id, version_snapshot)
        
        store.update_bot(bot_id, data, username)
        
        flash('Bot updated successfully!', 'success')
        return redirect(url_for('bots.my_bots'))
    
    return render_template('bot_edit.html',
                         username=username,
                         bot=bot,
                         categories=store.BOT_CATEGORIES,
                         permission_scopes=BotPermissions.get_all_scopes())


@bots_bp.route('/developers/my-bots/<bot_id>/analytics')
@login_required
@premium_required
def bot_analytics(bot_id):
    """View bot analytics"""
    username = session.get('username')
    bot = store.get_bot(bot_id)
    
    if not bot or bot.get('developer') != username:
        return "Bot not found or access denied", 404
    
    stats = BotAnalytics.get_stats(bot_id, days=30)
    daily = BotAnalytics.get_daily_breakdown(bot_id, days=30)
    
    return render_template('bot_analytics.html',
                         username=username,
                         bot=bot,
                         stats=stats,
                         daily_breakdown=daily)


@bots_bp.route('/developers/my-bots/<bot_id>/regenerate-key', methods=['POST'])
@login_required
@premium_required
def regenerate_api_key(bot_id):
    """Regenerate a bot's API key"""
    username = session.get('username')
    bot = store.get_bot(bot_id)
    
    if not bot or bot.get('developer') != username:
        return jsonify({'error': 'Bot not found or access denied'}), 404
    
    # Generate new key
    raw_api_key, hashed_api_key = generate_api_key()
    
    # Update in store
    store.update_bot_api_key(bot_id, hashed_api_key)
    
    return jsonify({
        'success': True,
        'api_key': raw_api_key,
        'message': 'API key regenerated. Save this key - it will not be shown again!'
    })


# ==========================================
# ADMIN ROUTES
# ==========================================

@bots_bp.route('/admin/bots')
@login_required
@admin_required
def admin_bots():
    """Admin panel for bot management"""
    username = session.get('username')
    
    # Get all bots by status
    all_bots = store.get_all_bots()
    
    pending = [b for b in all_bots if b.get('status') == store.BOT_STATUS_PENDING]
    approved = [b for b in all_bots if b.get('status') == store.BOT_STATUS_APPROVED]
    rejected = [b for b in all_bots if b.get('status') == store.BOT_STATUS_REJECTED]
    suspended = [b for b in all_bots if b.get('status') == store.BOT_STATUS_SUSPENDED]
    
    # Get reported bots
    reported = [b for b in all_bots if len(b.get('reports', [])) > 0]
    
    return render_template('admin_bots.html',
                         username=username,
                         pending_bots=pending,
                         approved_bots=approved,
                         rejected_bots=rejected,
                         suspended_bots=suspended,
                         reported_bots=reported,
                         total_bots=len(all_bots))


@bots_bp.route('/admin/bots/<bot_id>/review')
@login_required
@admin_required
def admin_review_bot(bot_id):
    """Review a pending bot"""
    username = session.get('username')
    bot = store.get_bot(bot_id)
    
    if not bot:
        return "Bot not found", 404
    
    # Run security scan
    scan_result = BotSecurityScanner.scan_bot(bot)
    
    # Get permission details
    permission_details = []
    for perm in bot.get('permissions', []):
        info = BotPermissions.get_scope_info(perm)
        if info:
            permission_details.append({**info, 'scope': perm})
    
    return render_template('admin_bot_review.html',
                         username=username,
                         bot=bot,
                         scan_result=scan_result,
                         permission_details=permission_details,
                         risk_level=BotPermissions.get_risk_level(bot.get('permissions', [])))


@bots_bp.route('/admin/bots/<bot_id>/approve', methods=['POST'])
@login_required
@admin_required
def admin_approve_bot(bot_id):
    """Approve a bot"""
    username = session.get('username')
    
    if store.approve_bot(bot_id, username):
        flash(f'Bot {bot_id} approved successfully!', 'success')
    else:
        flash('Failed to approve bot.', 'error')
    
    return redirect(url_for('bots.admin_bots'))


@bots_bp.route('/admin/bots/<bot_id>/reject', methods=['POST'])
@login_required
@admin_required
def admin_reject_bot(bot_id):
    """Reject a bot"""
    username = session.get('username')
    reason = request.form.get('reason', 'Does not meet guidelines')
    
    if store.reject_bot(bot_id, username, reason):
        flash(f'Bot {bot_id} rejected.', 'info')
    else:
        flash('Failed to reject bot.', 'error')
    
    return redirect(url_for('bots.admin_bots'))


@bots_bp.route('/admin/bots/<bot_id>/suspend', methods=['POST'])
@login_required
@admin_required
def admin_suspend_bot(bot_id):
    """Suspend a bot"""
    username = session.get('username')
    reason = request.form.get('reason', 'Policy violation')
    
    if store.suspend_bot(bot_id, username, reason):
        flash(f'Bot {bot_id} suspended.', 'warning')
    else:
        flash('Failed to suspend bot.', 'error')
    
    return redirect(url_for('bots.admin_bots'))


@bots_bp.route('/admin/bots/<bot_id>/reinstate', methods=['POST'])
@login_required
@admin_required
def admin_reinstate_bot(bot_id):
    """Reinstate a suspended bot"""
    username = session.get('username')
    
    if store.approve_bot(bot_id, username):
        flash(f'Bot {bot_id} reinstated.', 'success')
    else:
        flash('Failed to reinstate bot.', 'error')
    
    return redirect(url_for('bots.admin_bots'))


# ==========================================
# BOT API ENDPOINTS (with security)
# ==========================================

@bots_bp.route('/api/bot/send', methods=['POST'])
@rate_limit_bot_api
def bot_send_message():
    """API endpoint for bots to send messages"""
    # Authenticate bot with hashed key verification
    api_key = request.headers.get('X-Bot-API-Key')
    bot_id = request.headers.get('X-Bot-ID')
    
    if not api_key or not bot_id:
        return jsonify({'error': 'Missing authentication'}), 401
    
    bot = store.get_bot(bot_id)
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    # Verify API key against stored hash
    if not verify_api_key(api_key, bot.get('api_key_hash', '')):
        return jsonify({'error': 'Invalid API key'}), 401
    
    if bot['status'] != store.BOT_STATUS_APPROVED:
        return jsonify({'error': 'Bot is not approved'}), 403
    
    # Check permissions
    if 'messages.send' not in bot.get('permissions', []):
        return jsonify({'error': 'Bot lacks messages.send permission'}), 403
    
    data = request.json
    target_type = data.get('type')
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
    
    # Track message
    BotAnalytics.track_event(bot_id, 'message_sent', {
        'target_type': target_type,
        'target_id': target_id
    })
    
    # Store the message
    msg_id = store.generate_id()
    msg = {
        'id': msg_id,
        'sender': bot['username'],
        'content': message,
        'is_bot': True,
        'bot_id': bot_id,
        'timestamp': store.now()
    }
    
    if target_type == 'group':
        store.add_group_message(target_id, bot['username'], message, False)
    
    return jsonify({'success': True, 'message_id': msg_id})


@bots_bp.route('/api/bot/webhook-test', methods=['POST'])
@rate_limit_bot_api
def test_webhook():
    """Test endpoint for developers to verify webhook setup"""
    api_key = request.headers.get('X-Bot-API-Key')
    bot_id = request.headers.get('X-Bot-ID')
    
    if not api_key or not bot_id:
        return jsonify({'error': 'Missing authentication'}), 401
    
    bot = store.get_bot(bot_id)
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    if not verify_api_key(api_key, bot.get('api_key_hash', '')):
        return jsonify({'error': 'Invalid API key'}), 401
    
    return jsonify({
        'success': True,
        'message': 'Webhook test successful',
        'bot_id': bot_id,
        'version': bot.get('version', '1.0.0')
    })


@bots_bp.route('/api/bot/verify-signature', methods=['POST'])
def verify_signature_endpoint():
    """Endpoint for bots to verify webhook signatures"""
    data = request.json
    payload = data.get('payload', {})
    signature = data.get('signature', '')
    secret = data.get('secret', '')
    
    is_valid = verify_webhook_signature(payload, signature, secret)
    
    return jsonify({'valid': is_valid})
