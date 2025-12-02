"""
💬 Messaging WebSocket Events - MIE Optimized

Handles real-time private messaging between users.
Uses Menza Intelligence Engine for:
- Predictive caching
- Connection optimization
- Rate limiting
- Message prioritization
"""

from flask import session, request
from flask_socketio import emit, join_room
from webapp.models import store
from webapp.core import get_engine
from webapp.utils.bot_security import BotAnalytics, generate_webhook_headers
import requests


def register_messaging_events(socketio):
    """Register all messaging-related socket events"""
    
    @socketio.on('connect')
    def handle_connect():
        """When a user connects - MIE optimized"""
        if 'username' in session:
            username = session['username']
            store.set_user_online(request.sid, username)
            
            # Register with MIE for optimization
            engine = get_engine()
            engine.on_user_connect(request.sid, username, {
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')[:100]
            })
            
            emit('user_online', {'username': username}, broadcast=True)
            emit('online_list', {'users': store.get_online_users()})
            print(f"✅ {username} connected")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """When a user disconnects"""
        username = store.set_user_offline(request.sid)
        
        # Unregister from MIE
        get_engine().on_user_disconnect(request.sid)
        
        if username and not store.is_user_online(username):
            emit('user_offline', {'username': username}, broadcast=True)
            print(f"👋 {username} disconnected")
    
    @socketio.on('join_chat')
    def handle_join_chat(data):
        """When a user wants to chat - MIE optimized with caching"""
        if 'username' not in session:
            return
        
        my_username = session['username']
        friend_username = data.get('friend')
        room_id = store.get_room_id(my_username, friend_username)
        engine = get_engine()
        
        join_room(room_id)
        
        # Record interaction for predictions
        engine.predictor.record_interaction(my_username, friend_username, 'message')
        
        # Get cached or fetch chat data
        cache_key = f"chat_data:{room_id}"
        chat_data = engine.get_cached(cache_key)
        
        if not chat_data:
            chat_data = {
                'messages': store.get_messages(room_id),
                'settings': store.get_chat_settings(room_id)
            }
            engine.set_cached(cache_key, chat_data, ttl=30)
        
        emit('chat_history', {
            'messages': chat_data['messages'],
            'room': room_id,
            'settings': chat_data['settings']
        })
        
        # Get shared notes (less frequently accessed, shorter cache)
        notes_key = f"notes:{room_id}:{my_username}"
        notes_metadata = engine.get_cached(notes_key)
        
        if notes_metadata is None:
            notes = store.get_shared_notes_for_room(room_id)
            notes_metadata = [
                m for n in notes 
                if (m := store.get_note_metadata(n['id'], my_username))
            ]
            engine.set_cached(notes_key, notes_metadata, ttl=60)
        
        emit('shared_notes_list', {'notes': notes_metadata})
        print(f"💬 {my_username} joined chat with {friend_username}")
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Send encrypted message - MIE optimized with rate limiting"""
        if 'username' not in session:
            return
        
        sender = session['username']
        recipient = data.get('to')
        encrypted_message = data.get('encrypted_message')
        engine = get_engine()
        
        # Check rate limit
        user = store.get_user(sender)
        allowed, info = engine.check_rate_limit(sender, user.get('premium', False))
        if not allowed:
            emit('rate_limited', {'retry_after': info.get('retry_after', 60)})
            return
        
        room_id = store.get_room_id(sender, recipient)
        
        # Record interaction and determine priority
        priority = engine.on_message_sent(sender, recipient, 'dm')
        
        message_data = {
            'from': sender,
            'to': recipient,
            'encrypted': encrypted_message,
            'timestamp': store.now()
        }
        
        store.add_message(room_id, message_data)
        
        # Invalidate cache for this chat
        engine.cache.invalidate(f"chat_data:{room_id}")
        
        emit('new_message', message_data, room=room_id)
        print(f"📨 Message from {sender} to {recipient}")
    
    @socketio.on('share_public_key')
    def handle_share_key(data):
        """
        When a user shares their public key.
        Others need this to encrypt messages TO this user.
        """
        if 'username' not in session:
            return
        
        username = session['username']
        public_key = data.get('public_key')
        
        # Store the public key
        store.set_user_public_key(username, public_key)
        
        # Broadcast to everyone
        emit('public_key_update', {
            'username': username,
            'public_key': public_key
        }, broadcast=True)
        
        print(f"🔑 {username} shared their public key")
    
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
        """
        Delete a specific message.
        Only the sender can delete their own messages.
        """
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        message_id = data.get('message_id')
        
        room_id = store.get_room_id(username, friend)
        
        if store.delete_message(room_id, message_id, username):
            # Notify everyone in the room that message was deleted
            emit('message_deleted', {
                'message_id': message_id
            }, room=room_id)
            print(f"🗑️ {username} deleted a message")
        else:
            emit('delete_error', {'error': 'Could not delete message'})
    
    @socketio.on('clear_chat')
    def handle_clear_chat(data):
        """
        Clear all messages in a chat (start fresh).
        Both users need to agree, OR the initiator just clears for themselves.
        For simplicity, we'll clear for both users.
        """
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        
        room_id = store.get_room_id(username, friend)
        
        if store.clear_chat(room_id):
            # Notify everyone in the room
            emit('chat_cleared', {
                'cleared_by': username
            }, room=room_id)
            print(f"🧹 {username} cleared chat with {friend}")
    
    @socketio.on('set_auto_delete')
    def handle_set_auto_delete(data):
        """
        Set auto-delete period for messages in this chat.
        Options: 'never', '1_day', '1_week', '1_month', '1_year'
        """
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        period = data.get('period', 'never')
        
        room_id = store.get_room_id(username, friend)
        
        settings = store.set_auto_delete(room_id, period)
        
        # Notify everyone in the room about settings change
        emit('settings_updated', {
            'settings': settings,
            'updated_by': username
        }, room=room_id)
        
        print(f"⏰ {username} set auto-delete to {period} for chat with {friend}")
    
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
        """
        Create a new shared note in a chat.
        The creator sets their secret phrase immediately.
        Other members are prompted to set their own phrases.
        """
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
        
        # Create the note
        note = store.create_shared_note(
            room_id=room_id,
            title=title,
            content=content,
            created_by=username,
            creator_phrase=creator_phrase
        )
        
        # Add the other user(s) to pending list
        store.add_pending_member(note['id'], friend)
        
        # Broadcast to the room that a note was created
        emit('shared_note_created', {
            'id': note['id'],
            'title': note['title'],
            'created_by': username,
            'created_at': note['created_at']
        }, room=room_id)
        
        # Prompt the friend to set their phrase
        emit('prompt_set_phrase', {
            'note_id': note['id'],
            'title': note['title'],
            'created_by': username
        }, room=room_id)
        
        # Also send updated notes list to the creator immediately
        notes = store.get_shared_notes_for_room(room_id)
        print(f"📝 DEBUG: Found {len(notes)} notes for room {room_id}")
        notes_metadata = []
        for n in notes:
            metadata = store.get_note_metadata(n['id'], username)
            print(f"📝 DEBUG: Note metadata for {n['id']}: {metadata}")
            if metadata:
                notes_metadata.append(metadata)
        
        print(f"📝 DEBUG: Sending {len(notes_metadata)} notes to client")
        emit('shared_notes_list', {
            'notes': notes_metadata
        })
        
        print(f"📝 {username} created shared note '{title}' with {friend}")
    
    @socketio.on('set_note_phrase')
    def handle_set_note_phrase(data):
        """
        Set your secret phrase for a shared note.
        Each user sets their own unique phrase.
        """
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
            print(f"🔐 {username} set their phrase for note {note_id}")
        else:
            emit('note_error', {'error': 'Could not set phrase'})
    
    @socketio.on('unlock_note')
    def handle_unlock_note(data):
        """
        Attempt to unlock a shared note with your phrase.
        """
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
            print(f"🔓 {username} unlocked note {note_id}")
        else:
            emit('note_unlock_failed', {
                'note_id': note_id,
                'error': 'Incorrect phrase'
            })
    
    @socketio.on('get_shared_notes')
    def handle_get_shared_notes(data):
        """
        Get all shared notes for a chat room.
        Returns metadata only (not content - need to unlock for that).
        """
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        
        room_id = store.get_room_id(username, friend)
        notes = store.get_shared_notes_for_room(room_id)
        
        # Return metadata for each note
        notes_metadata = []
        for note in notes:
            metadata = store.get_note_metadata(note['id'], username)
            if metadata:
                notes_metadata.append(metadata)
        
        emit('shared_notes_list', {
            'notes': notes_metadata
        })
    
    @socketio.on('edit_shared_note')
    def handle_edit_shared_note(data):
        """
        Edit a shared note. User must provide their phrase to edit.
        """
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
            
            # Notify both users about the edit
            emit('note_edited', {
                'note_id': note_id,
                'title': result['note']['title'],
                'edited_by': username,
                'edited_at': result['note']['last_edited_at']
            }, room=room_id)
            
            # Send success to the editor
            emit('note_edit_success', {
                'note_id': note_id,
                'message': 'Note updated successfully!'
            })
            
            print(f"✏️ {username} edited note '{result['note']['title']}'")
        else:
            emit('note_error', {'error': result['message']})
    
    @socketio.on('request_delete_note')
    def handle_request_delete_note(data):
        """
        Request deletion of a shared note.
        Both users must agree for the note to be deleted.
        """
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
            # Notify both users that note was deleted
            room_id = store.get_room_id(username, friend)
            emit('note_deleted', {
                'note_id': note_id,
                'message': 'Note deleted by mutual agreement'
            }, room=room_id)
            print(f"🗑️ Note {note_id} deleted by mutual agreement")
        
        elif result['status'] == 'requested':
            # Notify both users about the deletion request
            room_id = store.get_room_id(username, friend)
            emit('note_delete_requested', {
                'note_id': note_id,
                'requested_by': username,
                'message': f'{username} requested to delete this note'
            }, room=room_id)
            print(f"🗑️ {username} requested to delete note {note_id}")
        
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
            print(f"↩️ {username} cancelled delete request for note {note_id}")
    
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
        
        # Create the group
        group = store.create_group(group_name, username, members, invite_code)
        
        # Notify the creator
        emit('group_created', {'group': group})
        
        # Notify all members - OPTIMIZED: use get_user_sids for O(1) lookup
        for member in group['members']:
            if member != username:
                for sid in store.get_user_sids(member):
                    emit('group_invite', {'group': group}, room=sid)
        
        print(f"👥 {username} created group '{group_name}' with {len(members)} members")
    
    @socketio.on('join_group')
    def handle_join_group(data):
        """Join a group chat room to receive messages"""
        if 'username' not in session:
            return
        
        username = session['username']
        group_id = data.get('group_id')
        
        group = store.get_group(group_id)
        if not group or username not in group['members']:
            emit('group_error', {'error': 'Not authorized to join this group'})
            return
        
        room_id = f"group_{group_id}"
        join_room(room_id)
        
        # Send group history
        emit('group_history', {
            'group_id': group_id,
            'messages': store.get_group_messages(group_id),
            'group': group
        })
        
        print(f"👥 {username} joined group '{group['name']}'")
    
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
        
        # Add message to store
        message = store.add_group_message(group_id, username, content, encrypted)
        
        # Broadcast to group room
        room_id = f"group_{group_id}"
        emit('new_group_message', {
            'group_id': group_id,
            'message': message
        }, room=room_id)
        
        print(f"💬 Group message in '{group['name']}' from {username}")
    
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
        
        # Add other group members as pending
        for member in group['members']:
            if member != username:
                store.add_pending_member(note['id'], member)
        
        # Notify all group members
        emit('shared_note_created', {
            'note': store.get_note_metadata(note['id'], username),
            'group_id': group_id
        }, room=room_id)
        
        # Prompt other members - OPTIMIZED: use get_user_sids for O(1) lookup
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
        
        group_name = group['name']
        print(f"📝 {username} created group note '{title}' in '{group_name}'")
    
    # ==========================================
    # BOT COMMAND EVENTS
    # ==========================================
    
    def process_bot_command(message, sender, target_type, target_id, room_id):
        """
        Check if a message is a bot command and process it.
        Returns True if a command was processed, False otherwise.
        """
        # Check if message starts with /
        if not message or not message.startswith('/'):
            return False
        
        # Parse command and args
        parts = message.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Get bots for this target
        if target_type == 'group':
            bots = store.get_group_bots(target_id)
        else:
            return False  # DM commands not supported yet
        
        # Find a bot that handles this command
        for bot in bots:
            if bot['status'] != store.BOT_STATUS_APPROVED:
                continue
            
            for cmd in bot.get('commands', []):
                if cmd['command'] == command:
                    # Process the command
                    response = process_command(bot, command, args, sender, target_type, target_id)
                    
                    if response:
                        # Send bot response
                        bot_message = {
                            'from': bot['username'],
                            'content': response,
                            'is_bot': True,
                            'bot_id': bot['bot_id'],
                            'timestamp': store.now()
                        }
                        
                        # Store and emit the message
                        if target_type == 'group':
                            store.add_group_message(target_id, bot['username'], response, False)
                            emit('new_group_message', {
                                'group_id': target_id,
                                'message': bot_message
                            }, room=room_id)
                    
                    return True
        
        return False
    
    def process_command(bot, command, args, sender, target_type, target_id):
        """
        Process a bot command and return a response.
        For internal bots, handle directly. For webhook bots, call the webhook.
        """
        # Track command usage
        BotAnalytics.track_event(bot['bot_id'], 'command', {
            'command': command,
            'user': sender,
            'args': args
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
        """Process CoinGecko bot commands with caching"""
        try:
            if command == '/price':
                if not args:
                    return "❌ Usage: /price <coin>\nExample: /price bitcoin"
                
                coin = args[0].lower()
                # Map common symbols to CoinGecko IDs
                coin_map = {
                    'btc': 'bitcoin', 'eth': 'ethereum', 'sol': 'solana',
                    'doge': 'dogecoin', 'xrp': 'ripple', 'ada': 'cardano',
                    'dot': 'polkadot', 'matic': 'polygon', 'link': 'chainlink',
                    'avax': 'avalanche-2', 'bnb': 'binancecoin'
                }
                coin_id = coin_map.get(coin, coin)
                
                # Check cache first
                cache_key = f"coingecko_price_{coin_id}"
                cached = BotResponseCache.get(cache_key)
                
                if cached:
                    data = cached
                else:
                    try:
                        response = requests.get(
                            'https://api.coingecko.com/api/v3/simple/price',
                            params={
                                'ids': coin_id,
                                'vs_currencies': 'usd',
                                'include_24hr_change': 'true'
                            },
                            timeout=3  # Reduced timeout
                        )
                        response.raise_for_status()
                        data = response.json()
                        BotResponseCache.set(cache_key, data, 'coingecko_price')
                    except requests.exceptions.Timeout:
                        return "⏱️ Price lookup timed out. Try again."
                    except Exception:
                        return "⚠️ Temporarily unavailable. Try again."
                
                if coin_id in data:
                    price = data[coin_id]['usd']
                    change = data[coin_id].get('usd_24hr_change', 0)
                    emoji = '📈' if change >= 0 else '📉'
                    return f"{emoji} **{coin_id.upper()}**\n💰 ${price:,.2f}\n{'+' if change >= 0 else ''}{change:.2f}% (24h)"
                else:
                    return f"❌ Coin '{coin}' not found. Try /price bitcoin"
            
            elif command == '/top':
                limit = int(args[0]) if args else 5
                limit = min(limit, 10)  # Max 10
                
                # Check cache
                cache_key = f"coingecko_top_{limit}"
                cached = BotResponseCache.get(cache_key)
                
                if cached:
                    data = cached
                else:
                    try:
                        response = requests.get(
                            'https://api.coingecko.com/api/v3/coins/markets',
                            params={
                                'vs_currency': 'usd',
                                'order': 'market_cap_desc',
                                'per_page': limit,
                                'page': 1
                            },
                            timeout=3  # Reduced timeout
                        )
                        response.raise_for_status()
                        data = response.json()
                        BotResponseCache.set(cache_key, data, 'default')
                    except requests.exceptions.Timeout:
                        return "⏱️ Request timed out. Try again."
                    except Exception:
                        return "⚠️ Temporarily unavailable. Try again."
                
                result = "🏆 **Top Cryptocurrencies**\n\n"
                for i, coin in enumerate(data, 1):
                    change = coin.get('price_change_percentage_24h', 0)
                    emoji = '📈' if change >= 0 else '📉'
                    result += f"{i}. **{coin['symbol'].upper()}** - ${coin['current_price']:,.2f} {emoji} {change:+.2f}%\n"
                
                return result
            
            elif command == '/trending':
                # Check cache
                cache_key = "coingecko_trending"
                cached = BotResponseCache.get(cache_key)
                
                if cached:
                    data = cached
                else:
                    try:
                        response = requests.get(
                            'https://api.coingecko.com/api/v3/search/trending',
                            timeout=3  # Reduced timeout
                        )
                        response.raise_for_status()
                        data = response.json()
                        BotResponseCache.set(cache_key, data, 'coingecko_trending')
                    except requests.exceptions.Timeout:
                        return "⏱️ Request timed out. Try again."
                    except Exception:
                        return "⚠️ Temporarily unavailable. Try again."
                
                result = "🔥 **Trending Coins**\n\n"
                for i, item in enumerate(data.get('coins', [])[:7], 1):
                    coin = item['item']
                    result += f"{i}. **{coin['symbol'].upper()}** - {coin['name']}\n"
                
                return result
            
        except Exception as e:
            print(f"❌ CoinGecko error: {e}")
            return "⚠️ Error fetching crypto data. Please try again."
        
        return None
    
    def process_phanes_command(command, args, sender):
        """
        Process Phanes Trading Bot commands
        FREE bot - Available to all users
        """
        try:
            if command == '/trade':
                if len(args) < 3:
                    return "❌ Usage: /trade <coin> <buy/sell> <amount>\nExample: /trade BTC buy 0.01"
                
                coin = args[0].upper()
                action = args[1].lower()
                amount = args[2]
                
                if action not in ['buy', 'sell']:
                    return "❌ Invalid action. Use 'buy' or 'sell'"
                
                # Simulated trade response
                emoji = '🟢' if action == 'buy' else '🔴'
                return f"{emoji} **Trade Order Placed**\n\n" + \
                       f"📊 Pair: {coin}/USDT\n" + \
                       f"📈 Action: {action.upper()}\n" + \
                       f"💰 Amount: {amount} {coin}\n" + \
                       f"⏱️ Status: Pending\n\n" + \
                       f"_Connect your exchange API to execute real trades_"
            
            elif command == '/balance':
                # Simulated portfolio balance
                return "💰 **Portfolio Balance**\n\n" + \
                       "🪙 BTC: 0.5 ($22,500)\n" + \
                       "🔷 ETH: 2.5 ($4,125)\n" + \
                       "◎ SOL: 50 ($2,500)\n" + \
                       "💵 USDT: 1,000\n\n" + \
                       "📊 Total: $30,125\n" + \
                       "📈 24h Change: +2.3%\n\n" + \
                       "_Connect your wallet for real balances_"
            
            elif command == '/pnl':
                period = args[0] if args else '7d'
                
                return f"📊 **P&L Report ({period})**\n\n" + \
                       "🟢 Winning trades: 12\n" + \
                       "🔴 Losing trades: 5\n" + \
                       "📈 Win rate: 70.6%\n\n" + \
                       "💰 Realized P&L: +$1,245\n" + \
                       "📊 Unrealized: +$320\n" + \
                       "🏆 Best trade: BTC +$450\n" + \
                       "💔 Worst trade: DOGE -$85"
            
            elif command == '/copy':
                if not args:
                    return "❌ Usage: /copy @trader\n\n" + \
                           "🏆 **Top Traders to Copy:**\n" + \
                           "1. @crypto_whale - 85% win rate\n" + \
                           "2. @btc_master - +120% YTD\n" + \
                           "3. @defi_guru - 72% win rate"
                
                trader = args[0]
                return f"✅ **Copy Trading Activated**\n\n" + \
                       f"Following: {trader}\n" + \
                       f"Mode: Mirror trades\n" + \
                       f"Risk: 10% of portfolio\n\n" + \
                       f"_You'll receive notifications for each trade_"
            
            elif command == '/alert':
                if len(args) < 2:
                    return "❌ Usage: /alert <coin> <price>\nExample: /alert BTC 50000"
                
                coin = args[0].upper()
                price = args[1]
                
                return f"🔔 **Price Alert Set**\n\n" + \
                       f"📊 Coin: {coin}\n" + \
                       f"🎯 Target: ${price}\n" + \
                       f"📱 Notification: Push + Message\n\n" + \
                       f"_You'll be notified when {coin} reaches ${price}_"
            
            elif command == '/positions':
                return "📊 **Open Positions**\n\n" + \
                       "🟢 BTC Long @ $44,200\n" + \
                       "   P&L: +$320 (+1.6%)\n\n" + \
                       "🟢 ETH Long @ $2,280\n" + \
                       "   P&L: +$85 (+2.1%)\n\n" + \
                       "🔴 SOL Short @ $105\n" + \
                       "   P&L: -$15 (-0.8%)\n\n" + \
                       "📈 Total Unrealized: +$390"
            
            else:
                return f"🔮 **Phanes Trading Bot**\n\n" + \
                       "Available commands:\n" + \
                       "• /trade <coin> <buy/sell> <amount>\n" + \
                       "• /balance - Portfolio balance\n" + \
                       "• /pnl - Profit/loss report\n" + \
                       "• /copy @trader - Copy trading\n" + \
                       "• /alert <coin> <price>\n" + \
                       "• /positions - Open positions"
        
        except Exception as e:
            print(f"❌ Phanes error: {e}")
            return "⚠️ Error processing command. Please try again."
        
        return None
    
    def process_internal_command(bot, command, args, sender):
        """Process internal bot commands"""
        bot_id = bot['bot_id']
        
        if bot_id == 'news_bot':
            if command == '/news':
                return "📰 **Latest Crypto News**\n\n" + \
                       "1. Bitcoin reaches new highs as institutional adoption grows\n" + \
                       "2. Ethereum 2.0 staking rewards increase\n" + \
                       "3. Major exchange announces new trading pairs\n\n" + \
                       "_Data from crypto news aggregators_"
            elif command == '/tldr':
                return "📋 **Today's Summary**\n\n" + \
                       "• Crypto market cap up 2.3%\n" + \
                       "• BTC dominance at 52%\n" + \
                       "• Top gainer: SOL (+8%)\n" + \
                       "• Fear & Greed Index: 65 (Greed)"
        
        elif bot_id == 'trading_signals_bot':
            if command == '/signal':
                return "📊 **Trading Signal**\n\n" + \
                       "🟢 **BTC/USD**\n" + \
                       "Entry: $45,000\n" + \
                       "Target: $48,000\n" + \
                       "Stop Loss: $43,500\n" + \
                       "Risk/Reward: 1:2.5\n\n" + \
                       "_This is not financial advice_"
            elif command == '/analysis':
                coin = args[0].upper() if args else 'BTC'
                return f"📈 **{coin} Analysis**\n\n" + \
                       "Trend: Bullish 🟢\n" + \
                       "Support: $42,000\n" + \
                       "Resistance: $48,500\n" + \
                       "RSI: 58 (Neutral)\n" + \
                       "MACD: Bullish crossover"
        
        elif bot_id == 'mod_bot':
            if command == '/rules':
                return "📜 **Group Rules**\n\n" + \
                       "1. Be respectful to all members\n" + \
                       "2. No spam or self-promotion\n" + \
                       "3. No NSFW content\n" + \
                       "4. No financial advice as facts\n" + \
                       "5. Use appropriate channels"
        
        return f"🤖 {bot['name']} received command: {command}"
    
    def call_webhook(bot, command, args, sender, target_type, target_id):
        """Call external bot webhook with secure signature"""
        webhook_url = bot.get('webhook_url')
        if not webhook_url:
            return None
        
        try:
            # Build payload
            payload = {
                'event': 'command',
                'command': command,
                'args': args,
                'sender': sender,
                'type': target_type,
                'target_id': target_id,
                'timestamp': store.now()
            }
            
            # Generate secure headers with HMAC signature
            # Use the raw API key if available, otherwise the hash (for verification on their end)
            api_key = bot.get('api_key') or bot.get('api_key_hash', '')
            headers = generate_webhook_headers(bot['bot_id'], payload, api_key)
            
            # Track webhook call
            BotAnalytics.track_event(bot['bot_id'], 'webhook_call', {
                'command': command,
                'sender': sender
            })
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('message') or data.get('response')
        except Exception as e:
            print(f"❌ Webhook error for {bot['bot_id']}: {e}")
            BotAnalytics.track_event(bot['bot_id'], 'webhook_error', {
                'error': str(e)
            })
        
        return None
    
    @socketio.on('bot_command')
    def handle_bot_command(data):
        """
        Process a bot command directly.
        Used when user explicitly invokes a command.
        """
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
            
            # Process the command
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

