"""
💬 Messaging WebSocket Events - MINIMAL
"""

from flask import session, request
from flask_socketio import emit, join_room
from webapp.models import store


def register_messaging_events(socketio):
    """Register messaging socket events"""
    
    @socketio.on('connect')
    def handle_connect():
        if 'username' in session:
            username = session['username']
            store.set_user_online(request.sid, username)
            emit('user_online', {'username': username}, broadcast=True)
            emit('online_list', {'users': store.get_online_users()})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        username = store.set_user_offline(request.sid)
        if username and not store.is_user_online(username):
            emit('user_offline', {'username': username}, broadcast=True)
    
    @socketio.on('join_chat')
    def handle_join_chat(data):
        if 'username' not in session:
            return
        
        my_username = session['username']
        friend_username = data.get('friend')
        room_id = store.get_room_id(my_username, friend_username)
        
        join_room(room_id)
        
        try:
            messages = store.get_messages(room_id)
            settings = store.get_chat_settings(room_id)
        except:
            messages = []
            settings = {}
        
        emit('chat_history', {
            'messages': messages,
            'room': room_id,
            'settings': settings
        })
        
        try:
            notes = store.get_shared_notes_for_room(room_id)
            notes_metadata = []
            for n in notes:
                metadata = store.get_note_metadata(n['id'], my_username)
                if metadata:
                    notes_metadata.append(metadata)
            emit('shared_notes_list', {'notes': notes_metadata})
        except:
            emit('shared_notes_list', {'notes': []})
    
    @socketio.on('send_message')
    def handle_send_message(data):
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
    
    @socketio.on('share_public_key')
    def handle_share_key(data):
        if 'username' not in session:
            return
        
        username = session['username']
        public_key = data.get('public_key')
        store.set_user_public_key(username, public_key)
        emit('public_key_update', {'username': username, 'public_key': public_key}, broadcast=True)
    
    @socketio.on('get_public_key')
    def handle_get_key(data):
        target = data.get('username')
        user = store.get_user(target)
        if user and user.get('public_key'):
            emit('receive_public_key', {'username': target, 'public_key': user['public_key']})
    
    @socketio.on('delete_message')
    def handle_delete_message(data):
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        message_id = data.get('message_id')
        room_id = store.get_room_id(username, friend)
        
        if store.delete_message(room_id, message_id, username):
            emit('message_deleted', {'message_id': message_id}, room=room_id)
    
    @socketio.on('clear_chat')
    def handle_clear_chat(data):
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        room_id = store.get_room_id(username, friend)
        
        if store.clear_chat(room_id):
            emit('chat_cleared', {'cleared_by': username}, room=room_id)
    
    @socketio.on('get_chat_settings')
    def handle_get_settings(data):
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        room_id = store.get_room_id(username, friend)
        settings = store.get_chat_settings(room_id)
        emit('chat_settings', {'settings': settings})
    
    @socketio.on('set_auto_delete')
    def handle_set_auto_delete(data):
        if 'username' not in session:
            return
        
        username = session['username']
        friend = data.get('friend')
        period = data.get('period', 'never')
        room_id = store.get_room_id(username, friend)
        settings = store.set_auto_delete(room_id, period)
        emit('settings_updated', {'settings': settings, 'updated_by': username}, room=room_id)
    
    # Group chat events
    @socketio.on('create_group')
    def handle_create_group(data):
        if 'username' not in session:
            return
        
        username = session['username']
        group_name = data.get('name', '').strip()
        members = data.get('members', [])
        
        if not group_name:
            emit('group_error', {'error': 'Group name required'})
            return
        
        try:
            group = store.create_group(group_name, username, members)
            emit('group_created', {'group': group})
        except Exception as e:
            emit('group_error', {'error': str(e)})
    
    @socketio.on('join_group')
    def handle_join_group(data):
        if 'username' not in session:
            return
        
        username = session['username']
        group_id = data.get('group_id')
        
        try:
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
        except Exception as e:
            emit('group_error', {'error': str(e)})
    
    @socketio.on('group_message')
    def handle_group_message(data):
        if 'username' not in session:
            return
        
        username = session['username']
        group_id = data.get('group_id')
        content = data.get('content')
        
        try:
            group = store.get_group(group_id)
            if not group or username not in group['members']:
                return
            
            message = store.add_group_message(group_id, username, content, True)
            room_id = f"group_{group_id}"
            emit('new_group_message', {'group_id': group_id, 'message': message}, room=room_id)
        except Exception as e:
            print(f"Group message error: {e}", flush=True)
    
    @socketio.on('get_user_groups')
    def handle_get_user_groups():
        if 'username' not in session:
            return
        
        try:
            groups = store.get_user_groups(session['username'])
            emit('user_groups', {'groups': groups})
        except:
            emit('user_groups', {'groups': []})
