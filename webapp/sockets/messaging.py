"""
💬 Messaging WebSocket Events - Memory Optimized

Handles real-time private messaging between users.
"""

from flask import session, request
from flask_socketio import emit, join_room
from webapp.models import store
from webapp.utils.bot_security import BotAnalytics, generate_webhook_headers
import requests


# Simple bot response cache (lightweight)
class BotResponseCache:
    """Simple cache for bot responses"""
    _cache = {}
    _max_entries = 20  # Small cache
    
    @classmethod
    def get(cls, key):
        import time
        entry = cls._cache.get(key)
        if entry and entry['expires'] > time.time():
            return entry['data']
        return None
    
    @classmethod
    def set(cls, key, data, cache_type='default'):
        import time
        # TTL based on type
        ttl = {'coingecko_price': 60, 'coingecko_trending': 300, 'default': 120}.get(cache_type, 120)
        
        # Evict oldest if full
        if len(cls._cache) >= cls._max_entries:
            oldest = min(cls._cache.items(), key=lambda x: x[1]['expires'])
            del cls._cache[oldest[0]]
        
        cls._cache[key] = {'data': data, 'expires': time.time() + ttl}


def register_messaging_events(socketio):
    """Register all messaging-related socket events"""
    
    @socketio.on('connect')
    def handle_connect():
        """When a user connects"""
        if 'username' in session:
            username = session['username']
            store.set_user_online(request.sid, username)
            emit('user_online', {'username': username}, broadcast=True)
            emit('online_list', {'users': store.get_online_users()})
            print(f"✅ {username} connected", flush=True)
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """When a user disconnects"""
        username = store.set_user_offline(request.sid)
        if username and not store.is_user_online(username):
            emit('user_offline', {'username': username}, broadcast=True)
            print(f"👋 {username} disconnected", flush=True)
    
    @socketio.on('join_chat')
    def handle_join_chat(data):
        """When a user wants to chat"""
        if 'username' not in session:
            return
        
        my_username = session['username']
        friend_username = data.get('friend')
        room_id = store.get_room_id(my_username, friend_username)
        
        join_room(room_id)
        
        # Get chat data
        chat_data = {
            'messages': store.get_messages(room_id),
            'settings': store.get_chat_settings(room_id)
        }
        
        emit('chat_history', {
            'messages': chat_data['messages'],
            'room': room_id,
            'settings': chat_data['settings']
        })
        
        # Get shared notes
        notes = store.get_shared_notes_for_room(room_id)
        notes_metadata = []
        for n in notes:
            metadata = store.get_note_metadata(n['id'], my_username)
            if metadata:
                notes_metadata.append(metadata)
        
        emit('shared_notes_list', {'notes': notes_metadata})
        print(f"💬 {my_username} joined chat with {friend_username}", flush=True)
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Send encrypted message"""
        if 'username' not in session:
            return
        
        sender = session['username']
        recipient = data.get('to')
        encrypted_message = data.get('encrypted_message')
        
        room_id = store.get_room_id(sender, recipient)
        
        message_data = {
            'from': sender,
            'to': recipient,
            'encrypted': encrypted_message,
            'timestamp': store.now()
        }
        
        store.add_message(room_id, message_data)
        emit('new_message', message_data, room=room_id)
        print(f"📨 Message from {sender} to {recipient}", flush=True)
    
    @socketio.on('share_public_key')
    def handle_share_key(data):
        """When a user shares their public key"""
        if 'username' not in session:
            return
        
        username = session['username']
        public_key = data.get('public_key')
        
        store.set_user_public_key(username, public_key)
        emit('public_key_update', {
            'username': username,
            'public_key': public_key
        }, broadcast=True)
        print(f"🔑 {username} shared their public key", flush=True)
    
    @socketio.on('get_public_key')
    def handle_get_key(data):
        """When someone wants another user's public key"""
        target_username = data.get('username')
        user = store.get_user(target_username)
        
        if user and user.get('public_key'):
            emit('receive_public_key', {
                'username': target_username,
                'public_key': user['public_key']
            })
    
    # ==========================================
    # MESSAGE DELETION EVENTS
    # ==========================================
    
    @socketio.on('delete_message')
    def handle_delete_message(data):
        """Delete a specific message"""
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        message_id = data.get('message_id')
        
        room_id = store.get_room_id(username, friend)
        
        if store.delete_message(room_id, message_id, username):
            emit('message_deleted', {'message_id': message_id}, room=room_id)
            print(f"🗑️ {username} deleted a message", flush=True)
        else:
            emit('delete_error', {'error': 'Could not delete message'})
    
    @socketio.on('clear_chat')
    def handle_clear_chat(data):
        """Clear all messages in a chat"""
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        room_id = store.get_room_id(username, friend)
        
        if store.clear_chat(room_id):
            emit('chat_cleared', {'cleared_by': username}, room=room_id)
            print(f"🧹 {username} cleared chat with {friend}", flush=True)
    
    @socketio.on('set_auto_delete')
    def handle_set_auto_delete(data):
        """Set auto-delete period for messages"""
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        period = data.get('period', 'never')
        
        room_id = store.get_room_id(username, friend)
        settings = store.set_auto_delete(room_id, period)
        
        emit('settings_updated', {
            'settings': settings,
            'updated_by': username
        }, room=room_id)
        print(f"⏰ {username} set auto-delete to {period}", flush=True)
    
    @socketio.on('get_chat_settings')
    def handle_get_settings(data):
        """Get current chat settings"""
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        
        room_id = store.get_room_id(username, friend)
        settings = store.get_chat_settings(room_id)
        emit('chat_settings', {'settings': settings})
    
    # ==========================================
    # SHARED NOTES EVENTS
    # ==========================================
    
    @socketio.on('create_shared_note')
    def handle_create_shared_note(data):
        """Create a new shared note"""
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        creator_phrase = data.get('phrase', '').strip()
        
        if not title or not content or not creator_phrase:
            emit('note_error', {'error': 'Title, content, and phrase are required'})
            return
        
        room_id = store.get_room_id(username, friend)
        
        note = store.create_shared_note(
            room_id=room_id,
            title=title,
            content=content,
            created_by=username,
            creator_phrase=creator_phrase
        )
        
        store.add_pending_member(note['id'], friend)
        
        emit('shared_note_created', {
            'id': note['id'],
            'title': note['title'],
            'created_by': username,
            'created_at': note['created_at']
        }, room=room_id)
        
        emit('prompt_set_phrase', {
            'note_id': note['id'],
            'title': note['title'],
            'created_by': username
        }, room=room_id)
        
        # Send updated notes list
        notes = store.get_shared_notes_for_room(room_id)
        notes_metadata = [store.get_note_metadata(n['id'], username) for n in notes]
        notes_metadata = [m for m in notes_metadata if m]
        emit('shared_notes_list', {'notes': notes_metadata})
        
        print(f"📝 {username} created shared note '{title}'", flush=True)
    
    @socketio.on('set_note_phrase')
    def handle_set_note_phrase(data):
        """Set your secret phrase for a shared note"""
        if 'username' not in session:
            return
        
        username = session['username']
        note_id = data.get('note_id')
        phrase = data.get('phrase', '').strip()
        
        if not phrase:
            emit('note_error', {'error': 'Phrase is required'})
            return
        
        if store.set_note_phrase(note_id, username, phrase):
            emit('phrase_set_success', {
                'note_id': note_id,
                'message': 'Your secret phrase has been set!'
            })
            print(f"🔐 {username} set phrase for note", flush=True)
        else:
            emit('note_error', {'error': 'Could not set phrase'})
    
    @socketio.on('unlock_note')
    def handle_unlock_note(data):
        """Unlock a shared note with phrase"""
        if 'username' not in session:
            return
        
        username = session['username']
        note_id = data.get('note_id')
        phrase = data.get('phrase', '').strip()
        
        content = store.verify_note_phrase(note_id, username, phrase)
        
        if content is not None:
            note = store.get_shared_note(note_id)
            emit('note_unlocked', {
                'note_id': note_id,
                'title': note['title'],
                'content': content,
                'created_by': note['created_by'],
                'last_edited_by': note.get('last_edited_by'),
                'last_edited_at': note.get('last_edited_at')
            })
        else:
            emit('note_unlock_failed', {
                'note_id': note_id,
                'error': 'Incorrect phrase'
            })
    
    @socketio.on('get_shared_notes')
    def handle_get_shared_notes(data):
        """Get all shared notes for a chat"""
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        
        room_id = store.get_room_id(username, friend)
        notes = store.get_shared_notes_for_room(room_id)
        
        notes_metadata = []
        for note in notes:
            metadata = store.get_note_metadata(note['id'], username)
            if metadata:
                notes_metadata.append(metadata)
        
        emit('shared_notes_list', {'notes': notes_metadata})
    
    @socketio.on('edit_shared_note')
    def handle_edit_shared_note(data):
        """Edit a shared note"""
        if 'username' not in session:
            return
        
        username = session['username']
        note_id = data.get('note_id')
        phrase = data.get('phrase', '').strip()
        new_title = data.get('title', '').strip()
        new_content = data.get('content', '').strip()
        friend = data.get('friend')
        
        if not phrase:
            emit('note_error', {'error': 'Phrase is required to edit'})
            return
        
        if not new_title and not new_content:
            emit('note_error', {'error': 'Nothing to update'})
            return
        
        result = store.edit_shared_note(note_id, username, phrase, new_title, new_content)
        
        if result['status'] == 'success':
            room_id = store.get_room_id(username, friend)
            emit('note_edited', {
                'note_id': note_id,
                'title': result['note']['title'],
                'edited_by': username,
                'edited_at': result['note']['last_edited_at']
            }, room=room_id)
            emit('note_edit_success', {
                'note_id': note_id,
                'message': 'Note updated successfully!'
            })
        else:
            emit('note_error', {'error': result['message']})
    
    @socketio.on('request_delete_note')
    def handle_request_delete_note(data):
        """Request deletion of a shared note"""
        if 'username' not in session:
            return
        
        username = session['username']
        note_id = data.get('note_id')
        friend = data.get('friend')
        
        if not note_id:
            emit('note_error', {'error': 'Note ID required'})
            return
        
        result = store.request_note_deletion(note_id, username)
        
        if result['status'] == 'deleted':
            room_id = store.get_room_id(username, friend)
            emit('note_deleted', {
                'note_id': note_id,
                'message': 'Note deleted by mutual agreement'
            }, room=room_id)
        elif result['status'] == 'requested':
            room_id = store.get_room_id(username, friend)
            emit('note_delete_requested', {
                'note_id': note_id,
                'requested_by': username,
                'message': f'{username} requested to delete this note'
            }, room=room_id)
        else:
            emit('note_error', {'error': result.get('message', 'Could not process request')})
    
    @socketio.on('cancel_delete_request')
    def handle_cancel_delete_request(data):
        """Cancel a deletion request"""
        if 'username' not in session:
            return
        
        username = session['username']
        note_id = data.get('note_id')
        friend = data.get('friend')
        
        if store.cancel_delete_request(note_id, username):
            room_id = store.get_room_id(username, friend)
            emit('note_delete_cancelled', {
                'note_id': note_id,
                'cancelled_by': username
            }, room=room_id)
    
    # ==========================================
    # GROUP CHAT EVENTS
    # ==========================================
    
    @socketio.on('create_group')
    def handle_create_group(data):
        """Create a new group chat"""
        if 'username' not in session:
            return
        
        username = session['username']
        group_name = data.get('name', '').strip()
        members = data.get('members', [])
        invite_code = data.get('invite_code')
        
        if not group_name:
            emit('group_error', {'error': 'Group name is required'})
            return
        
        group = store.create_group(group_name, username, members, invite_code)
        emit('group_created', {'group': group})
        
        # Notify members
        for member in group['members']:
            if member != username:
                for sid in store.get_user_sids(member):
                    emit('group_invite', {'group': group}, room=sid)
        
        print(f"👥 {username} created group '{group_name}'", flush=True)
    
    @socketio.on('join_group')
    def handle_join_group(data):
        """Join a group chat room"""
        if 'username' not in session:
            return
        
        username = session['username']
        group_id = data.get('group_id')
        
        group = store.get_group(group_id)
        if not group or username not in group['members']:
            emit('group_error', {'error': 'Not authorized'})
            return
        
        room_id = f"group_{group_id}"
        join_room(room_id)
        
        emit('group_history', {
            'group_id': group_id,
            'messages': store.get_group_messages(group_id),
            'group': group
        })
    
    @socketio.on('group_message')
    def handle_group_message(data):
        """Send a message to a group"""
        if 'username' not in session:
            return
        
        username = session['username']
        group_id = data.get('group_id')
        content = data.get('content')
        encrypted = data.get('encrypted', True)
        
        group = store.get_group(group_id)
        if not group or username not in group['members']:
            emit('group_error', {'error': 'Not authorized'})
            return
        
        message = store.add_group_message(group_id, username, content, encrypted)
        
        room_id = f"group_{group_id}"
        emit('new_group_message', {
            'group_id': group_id,
            'message': message
        }, room=room_id)
    
    @socketio.on('get_user_groups')
    def handle_get_user_groups():
        """Get all groups for the current user"""
        if 'username' not in session:
            return
        
        username = session['username']
        groups = store.get_user_groups(username)
        emit('user_groups', {'groups': groups})
    
    # ==========================================
    # GROUP SHARED NOTES EVENTS
    # ==========================================
    
    @socketio.on('get_group_notes')
    def handle_get_group_notes(data):
        """Get shared notes for a group"""
        if 'username' not in session:
            return
        
        username = session['username']
        group_id = data.get('group_id')
        
        group = store.get_group(group_id)
        if not group or username not in group['members']:
            emit('group_error', {'error': 'Not authorized'})
            return
        
        room_id = f"group_{group_id}"
        notes = store.get_shared_notes_for_room(room_id)
        
        notes_metadata = []
        for note in notes:
            metadata = store.get_note_metadata(note['id'], username)
            if metadata:
                notes_metadata.append(metadata)
        
        emit('group_notes_list', {
            'group_id': group_id,
            'notes': notes_metadata
        })
    
    @socketio.on('create_group_note')
    def handle_create_group_note(data):
        """Create a shared note in a group"""
        if 'username' not in session:
            return
        
        username = session['username']
        group_id = data.get('group_id')
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        phrase = data.get('phrase', '').strip()
        
        if not all([group_id, title, content, phrase]):
            emit('note_error', {'error': 'Missing required fields'})
            return
        
        group = store.get_group(group_id)
        if not group or username not in group['members']:
            emit('group_error', {'error': 'Not authorized'})
            return
        
        room_id = f"group_{group_id}"
        note = store.create_shared_note(room_id, title, content, username, phrase)
        
        for member in group['members']:
            if member != username:
                store.add_pending_member(note['id'], member)
        
        emit('shared_note_created', {
            'note': store.get_note_metadata(note['id'], username),
            'group_id': group_id
        }, room=room_id)
        
        for member in group['members']:
            if member != username:
                for sid in store.get_user_sids(member):
                    emit('prompt_set_phrase', {
                        'note_id': note['id'],
                        'note_title': title,
                        'created_by': username,
                        'group_id': group_id,
                        'group_name': group['name']
                    }, room=sid)
        
        print(f"📝 {username} created group note '{title}'", flush=True)
    
    # ==========================================
    # BOT COMMANDS
    # ==========================================
    
    def process_bot_command(message, sender, target_type, target_id, room_id):
        """Check if message is a bot command and process it"""
        if not message or not message.startswith('/'):
            return False
        
        parts = message.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if target_type == 'group':
            bots = store.get_group_bots(target_id)
        else:
            return False
        
        for bot in bots:
            if bot['status'] != store.BOT_STATUS_APPROVED:
                continue
            
            for cmd in bot.get('commands', []):
                if cmd['command'] == command:
                    response = process_command(bot, command, args, sender, target_type, target_id)
                    
                    if response:
                        bot_message = {
                            'from': bot['username'],
                            'content': response,
                            'is_bot': True,
                            'bot_id': bot['bot_id'],
                            'timestamp': store.now()
                        }
                        
                        if target_type == 'group':
                            store.add_group_message(target_id, bot['username'], response, False)
                            emit('new_group_message', {
                                'group_id': target_id,
                                'message': bot_message
                            }, room=room_id)
                    
                    return True
        
        return False
    
    def process_command(bot, command, args, sender, target_type, target_id):
        """Process a bot command"""
        BotAnalytics.track_event(bot['bot_id'], 'command', {
            'command': command, 'user': sender, 'args': args
        })
        
        api_type = bot.get('api_type', 'internal')
        
        if api_type == 'coingecko':
            return process_coingecko_command(command, args)
        elif api_type == 'phanes':
            return process_phanes_command(command, args, sender)
        elif api_type == 'internal':
            return process_internal_command(bot, command, args, sender)
        elif api_type == 'webhook':
            return call_webhook(bot, command, args, sender, target_type, target_id)
        
        return None
    
    def process_coingecko_command(command, args):
        """Process CoinGecko commands"""
        try:
            if command == '/price':
                if not args:
                    return "❌ Usage: /price <coin>\nExample: /price bitcoin"
                
                coin = args[0].lower()
                coin_map = {
                    'btc': 'bitcoin', 'eth': 'ethereum', 'sol': 'solana',
                    'doge': 'dogecoin', 'xrp': 'ripple', 'ada': 'cardano'
                }
                coin_id = coin_map.get(coin, coin)
                
                cache_key = f"coingecko_price_{coin_id}"
                cached = BotResponseCache.get(cache_key)
                
                if cached:
                    data = cached
                else:
                    try:
                        response = requests.get(
                            'https://api.coingecko.com/api/v3/simple/price',
                            params={'ids': coin_id, 'vs_currencies': 'usd', 'include_24hr_change': 'true'},
                            timeout=3
                        )
                        response.raise_for_status()
                        data = response.json()
                        BotResponseCache.set(cache_key, data, 'coingecko_price')
                    except:
                        return "⚠️ Price lookup failed. Try again."
                
                if coin_id in data:
                    price = data[coin_id]['usd']
                    change = data[coin_id].get('usd_24hr_change', 0)
                    emoji = '📈' if change >= 0 else '📉'
                    return f"{emoji} **{coin_id.upper()}**\n💰 ${price:,.2f}\n{'+' if change >= 0 else ''}{change:.2f}% (24h)"
                else:
                    return f"❌ Coin '{coin}' not found"
            
            elif command == '/top':
                limit = min(int(args[0]) if args else 5, 10)
                
                cache_key = f"coingecko_top_{limit}"
                cached = BotResponseCache.get(cache_key)
                
                if cached:
                    data = cached
                else:
                    try:
                        response = requests.get(
                            'https://api.coingecko.com/api/v3/coins/markets',
                            params={'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': limit, 'page': 1},
                            timeout=3
                        )
                        response.raise_for_status()
                        data = response.json()
                        BotResponseCache.set(cache_key, data, 'default')
                    except:
                        return "⚠️ Request failed. Try again."
                
                result = "🏆 **Top Cryptocurrencies**\n\n"
                for i, coin in enumerate(data, 1):
                    change = coin.get('price_change_percentage_24h', 0) or 0
                    emoji = '📈' if change >= 0 else '📉'
                    result += f"{i}. **{coin['symbol'].upper()}** - ${coin['current_price']:,.2f} {emoji} {change:+.2f}%\n"
                return result
        except Exception as e:
            print(f"❌ CoinGecko error: {e}", flush=True)
            return "⚠️ Error fetching crypto data"
        
        return None
    
    def process_phanes_command(command, args, sender):
        """Process Phanes Trading Bot commands"""
        try:
            if command == '/trade':
                if len(args) < 3:
                    return "❌ Usage: /trade <coin> <buy/sell> <amount>"
                
                coin, action, amount = args[0].upper(), args[1].lower(), args[2]
                if action not in ['buy', 'sell']:
                    return "❌ Use 'buy' or 'sell'"
                
                emoji = '🟢' if action == 'buy' else '🔴'
                return f"{emoji} **Trade Order**\n📊 {coin}/USDT\n📈 {action.upper()}\n💰 {amount} {coin}\n_Demo mode_"
            
            elif command == '/balance':
                return "💰 **Portfolio**\n🪙 BTC: 0.5 ($22,500)\n🔷 ETH: 2.5 ($4,125)\n📊 Total: $26,625"
            
            elif command == '/pnl':
                return "📊 **P&L**\n🟢 +12 wins\n🔴 -5 losses\n📈 70.6% win rate"
        except Exception as e:
            print(f"❌ Phanes error: {e}", flush=True)
        
        return None
    
    def process_internal_command(bot, command, args, sender):
        """Process internal bot commands"""
        bot_id = bot['bot_id']
        
        if bot_id == 'news_bot':
            if command == '/news':
                return "📰 **Latest News**\n1. Bitcoin reaches new highs\n2. ETH 2.0 staking grows"
        elif bot_id == 'trading_signals_bot':
            if command == '/signal':
                return "📊 **Signal**\n🟢 BTC/USD\nEntry: $45,000\nTarget: $48,000"
        elif bot_id == 'mod_bot':
            if command == '/rules':
                return "📜 **Rules**\n1. Be respectful\n2. No spam\n3. No NSFW"
        
        return f"🤖 {bot['name']} received: {command}"
    
    def call_webhook(bot, command, args, sender, target_type, target_id):
        """Call external bot webhook"""
        webhook_url = bot.get('webhook_url')
        if not webhook_url:
            return None
        
        try:
            payload = {
                'event': 'command', 'command': command, 'args': args,
                'sender': sender, 'type': target_type, 'target_id': target_id,
                'timestamp': store.now()
            }
            
            api_key = bot.get('api_key') or bot.get('api_key_hash', '')
            headers = generate_webhook_headers(bot['bot_id'], payload, api_key)
            
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('message') or data.get('response')
        except Exception as e:
            print(f"❌ Webhook error: {e}", flush=True)
        
        return None
    
    @socketio.on('bot_command')
    def handle_bot_command(data):
        """Process a bot command directly"""
        if 'username' not in session:
            return
        
        username = session['username']
        command = data.get('command', '')
        args = data.get('args', [])
        group_id = data.get('group_id')
        
        if not command.startswith('/'):
            command = '/' + command
        
        if group_id:
            group = store.get_group(group_id)
            if not group or username not in group['members']:
                emit('bot_error', {'error': 'Not authorized'})
                return
            
            room_id = f"group_{group_id}"
            
            bots = store.get_group_bots(group_id)
            for bot in bots:
                if bot['status'] != store.BOT_STATUS_APPROVED:
                    continue
                
                for cmd in bot.get('commands', []):
                    if cmd['command'] == command:
                        response = process_command(bot, command, args, username, 'group', group_id)
                        
                        if response:
                            bot_message = {
                                'from': bot['username'],
                                'content': response,
                                'is_bot': True,
                                'bot_id': bot['bot_id'],
                                'timestamp': store.now()
                            }
                            
                            store.add_group_message(group_id, bot['username'], response, False)
                            emit('new_group_message', {
                                'group_id': group_id,
                                'message': bot_message
                            }, room=room_id)
                        return
            
            emit('bot_error', {'error': 'No bot found for this command'})
