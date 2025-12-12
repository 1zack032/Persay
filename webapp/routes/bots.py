"""
🤖 Bot Store - SIMPLIFIED

FREE BOTS:
- CoinGecko (crypto prices)
- Phanes (trading signals)

PREMIUM BOTS:
- Wallet Tracker
- Trading Bot
- News Bot
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from webapp.models import store

bots_bp = Blueprint('bots', __name__)


# ============================================
# BOT DEFINITIONS
# ============================================

FREE_BOTS = {
    'coingecko': {
        'id': 'coingecko',
        'name': 'CoinGecko',
        'description': 'Get real-time crypto prices',
        'avatar': '🦎',
        'commands': [
            {'command': '/price', 'description': 'Get price', 'usage': '/price BTC'},
            {'command': '/top', 'description': 'Top coins', 'usage': '/top 10'}
        ],
        'free': True
    },
    'phanes': {
        'id': 'phanes',
        'name': 'Phanes Trading',
        'description': 'Trading signals and portfolio tracking',
        'avatar': '🔮',
        'commands': [
            {'command': '/trade', 'description': 'Trade info', 'usage': '/trade BTC'},
            {'command': '/balance', 'description': 'Check balance', 'usage': '/balance'}
        ],
        'free': True
    }
}

PREMIUM_BOTS = {
    'wallet_tracker': {
        'id': 'wallet_tracker',
        'name': 'Wallet Tracker',
        'description': 'Track wallet addresses and transactions',
        'avatar': '👛',
        'commands': [
            {'command': '/track', 'description': 'Track wallet', 'usage': '/track 0x...'},
            {'command': '/txs', 'description': 'Recent transactions', 'usage': '/txs'}
        ],
        'free': False
    },
    'trading_bot': {
        'id': 'trading_bot',
        'name': 'Auto Trader',
        'description': 'Automated trading strategies',
        'avatar': '📈',
        'commands': [
            {'command': '/strategy', 'description': 'Set strategy', 'usage': '/strategy dca'},
            {'command': '/pnl', 'description': 'Profit/Loss', 'usage': '/pnl'}
        ],
        'free': False
    },
    'news_bot': {
        'id': 'news_bot',
        'name': 'Crypto News',
        'description': 'Latest crypto news and alerts',
        'avatar': '📰',
        'commands': [
            {'command': '/news', 'description': 'Latest news', 'usage': '/news'},
            {'command': '/alert', 'description': 'Set alert', 'usage': '/alert BTC 50000'}
        ],
        'free': False
    }
}

ALL_BOTS = {**FREE_BOTS, **PREMIUM_BOTS}


# ============================================
# ROUTES
# ============================================

@bots_bp.route('/bots')
def bot_store():
    """Bot store page"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    user = store.get_user(username)
    is_premium = user.get('premium', False) if user else False
    
    return render_template('bot_store_simple.html',
                         username=username,
                         is_premium=is_premium,
                         free_bots=list(FREE_BOTS.values()),
                         premium_bots=list(PREMIUM_BOTS.values()))


@bots_bp.route('/api/bots')
def get_bots():
    """Get available bots"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = store.get_user(session['username'])
    is_premium = user.get('premium', False) if user else False
    
    available = list(FREE_BOTS.values())
    if is_premium:
        available.extend(PREMIUM_BOTS.values())
    
    return jsonify({
        'bots': available,
        'is_premium': is_premium
    })


@bots_bp.route('/api/bots/<bot_id>')
def get_bot(bot_id):
    """Get bot details"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    bot = ALL_BOTS.get(bot_id)
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    user = store.get_user(session['username'])
    is_premium = user.get('premium', False) if user else False
    
    # Check access
    if not bot['free'] and not is_premium:
        return jsonify({
            'error': 'Premium required',
            'bot': {'id': bot['id'], 'name': bot['name']},
            'upgrade_url': '/premium'
        }), 403
    
    return jsonify({'bot': bot})


@bots_bp.route('/api/bots/<bot_id>/add', methods=['POST'])
def add_bot_to_chats(bot_id):
    """Add a bot to user's chat list"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    bot = ALL_BOTS.get(bot_id)
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    username = session['username']
    user = store.get_user(username)
    is_premium = user.get('premium', False) if user else False
    
    # Check access for premium bots
    if not bot['free'] and not is_premium:
        return jsonify({'error': 'Premium required'}), 403
    
    # Add bot to user's bot list
    result = store.add_user_bot(username, bot_id)
    if result['success']:
        if result['already_added']:
            return jsonify({
                'success': True,
                'message': f'{bot["name"]} is already in your chats',
                'bot': bot,
                'already_added': True
            })
        return jsonify({
            'success': True,
            'message': f'{bot["name"]} added to your chats',
            'bot': bot
        })
    else:
        return jsonify({'error': 'Failed to add bot'}), 400


@bots_bp.route('/api/bots/my')
def get_my_bots():
    """Get user's added bots"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    user_bots = store.get_user_bots(username)
    
    # Get full bot info for each added bot
    bots = []
    for bot_id in user_bots:
        if bot_id in ALL_BOTS:
            bots.append(ALL_BOTS[bot_id])
    
    return jsonify({'bots': bots})


@bots_bp.route('/api/bots/<bot_id>/remove', methods=['POST'])
def remove_bot_from_chats(bot_id):
    """Remove a bot from user's chat list"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    success = store.remove_user_bot(username, bot_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Bot removed'})
    else:
        return jsonify({'error': 'Bot not found in your chats'}), 400


@bots_bp.route('/api/user/groups')
def get_user_groups():
    """Get user's groups for bot management"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    groups = store.get_user_groups(username)
    
    return jsonify({'groups': groups})


@bots_bp.route('/api/user/channels')
def get_user_channels():
    """Get channels where user is admin for bot management"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    username = session['username']
    channels = store.get_admin_channels(username)
    
    return jsonify({'channels': channels})


@bots_bp.route('/api/bots/<bot_id>/add-to-group', methods=['POST'])
def add_bot_to_group(bot_id):
    """Add a bot to a group"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    bot = ALL_BOTS.get(bot_id)
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    username = session['username']
    user = store.get_user(username)
    is_premium = user.get('premium', False) if user else False
    
    # Check access for premium bots
    if not bot['free'] and not is_premium:
        return jsonify({'error': 'Premium required'}), 403
    
    data = request.get_json()
    if not data or 'group_id' not in data:
        return jsonify({'error': 'Group ID required'}), 400
    
    group_id = data['group_id']
    
    # Check if user is admin/owner of the group
    group = store.get_group(group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    if username not in group.get('admins', []) and username != group.get('owner'):
        return jsonify({'error': 'You must be an admin to add bots'}), 403
    
    # Add bot to group
    success = store.add_bot_to_group_simple(group_id, bot_id)
    if success:
        return jsonify({
            'success': True,
            'message': f'{bot["name"]} added to group'
        })
    else:
        return jsonify({'error': 'Bot already in group or error occurred'}), 400


@bots_bp.route('/api/bots/<bot_id>/add-to-channel', methods=['POST'])
def add_bot_to_channel(bot_id):
    """Add a bot to a channel"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    bot = ALL_BOTS.get(bot_id)
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    username = session['username']
    user = store.get_user(username)
    is_premium = user.get('premium', False) if user else False
    
    # Check access for premium bots
    if not bot['free'] and not is_premium:
        return jsonify({'error': 'Premium required'}), 403
    
    data = request.get_json()
    if not data or 'channel_id' not in data:
        return jsonify({'error': 'Channel ID required'}), 400
    
    channel_id = data['channel_id']
    
    # Check if user is admin of the channel
    channel = store.get_channel(channel_id)
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    if username != channel.get('creator') and username not in channel.get('admins', []):
        return jsonify({'error': 'You must be an admin to add bots'}), 403
    
    # Add bot to channel
    success = store.add_bot_to_channel_simple(channel_id, bot_id)
    if success:
        return jsonify({
            'success': True,
            'message': f'{bot["name"]} added to channel'
        })
    else:
        return jsonify({'error': 'Bot already in channel or error occurred'}), 400


@bots_bp.route('/api/bots/<bot_id>/command', methods=['POST'])
def run_command(bot_id):
    """Run a bot command"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    bot = ALL_BOTS.get(bot_id)
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    user = store.get_user(session['username'])
    is_premium = user.get('premium', False) if user else False
    
    # Check access
    if not bot['free'] and not is_premium:
        return jsonify({'error': 'Premium required'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    command = data.get('command', '')
    args = data.get('args', [])
    
    # Process command
    response = process_bot_command(bot_id, command, args)
    return jsonify({'response': response})


def process_bot_command(bot_id: str, command: str, args: list) -> str:
    """Process a bot command and return response"""
    
    if bot_id == 'coingecko':
        if command == '/price':
            coin = args[0].upper() if args else 'BTC'
            return f"💰 **{coin}** Price\n$45,230.50 (+2.3%)\n_Data from CoinGecko_"
        elif command == '/top':
            return "🏆 **Top Coins**\n1. BTC $45,230\n2. ETH $2,350\n3. SOL $98"
        return "Use /price <coin> or /top"
    
    elif bot_id == 'phanes':
        if command == '/trade':
            return "📊 **Trade Signal**\nBTC/USD: BUY\nEntry: $45,000\nTarget: $48,000"
        elif command == '/balance':
            return "💰 **Portfolio**\nBTC: 0.5\nETH: 2.0\nTotal: $26,000"
        return "Use /trade or /balance"
    
    elif bot_id == 'wallet_tracker':
        if command == '/track':
            return "👛 **Tracking Wallet**\nAddress added to watchlist"
        return "Use /track <address>"
    
    elif bot_id == 'trading_bot':
        if command == '/strategy':
            return "📈 **Strategy Set**\nDCA mode activated"
        elif command == '/pnl':
            return "💹 **P&L Report**\n+$1,250 (+12.5%)"
        return "Use /strategy or /pnl"
    
    elif bot_id == 'news_bot':
        if command == '/news':
            return "📰 **Latest News**\n• Bitcoin hits new high\n• ETH 2.0 update live"
        return "Use /news"
    
    return "Unknown command"
