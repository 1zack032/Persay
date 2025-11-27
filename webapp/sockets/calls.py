"""
📞 Voice & Video Calling WebSocket Events

Handles real-time voice and video calls using WebRTC.
- 1-on-1 calls (DMs)
- Group calls (multi-peer)
- Channel calls (role-based: admin/mod can speak, viewers listen)

WebRTC Signaling Flow:
1. Caller sends 'start_call' -> creates call room
2. Callee receives 'incoming_call' notification
3. Callee sends 'join_call' -> joins call room
4. Peers exchange 'call_signal' (offer/answer/ICE candidates)
5. Connection established
6. 'leave_call' or 'end_call' to terminate
"""

from flask import session, request
from flask_socketio import emit, join_room, leave_room
from webapp.models import store
from datetime import datetime
import secrets


# Active calls storage
# call_id -> {id, type, room_id, participants: [{username, role, joined_at}], started_at, started_by}
active_calls = {}


def generate_call_id():
    return f"call_{secrets.token_hex(8)}"


def register_call_events(socketio):
    """Register all call-related socket events"""
    
    # ==========================================
    # CALL INITIATION
    # ==========================================
    
    @socketio.on('start_call')
    def handle_start_call(data):
        """
        Start a new call.
        data: {type: 'dm'|'group'|'channel', target_id: user/group/channel_id, video: bool}
        """
        if 'username' not in session:
            return
        
        username = session['username']
        call_type = data.get('type')  # 'dm', 'group', 'channel'
        target_id = data.get('target_id')
        with_video = data.get('video', False)
        
        if not call_type or not target_id:
            emit('call_error', {'error': 'Invalid call parameters'})
            return
        
        call_id = generate_call_id()
        call_room = f"call_room_{call_id}"
        
        # Validate and set up based on call type
        if call_type == 'dm':
            # Direct message call
            room_id = store.get_room_id(username, target_id)
            participants_allowed = [username, target_id]
            
            call = {
                'id': call_id,
                'type': 'dm',
                'room_id': room_id,
                'target': target_id,
                'participants': [{
                    'username': username,
                    'role': 'caller',
                    'video': with_video,
                    'audio': True,
                    'joined_at': datetime.now().isoformat()
                }],
                'started_at': datetime.now().isoformat(),
                'started_by': username,
                'with_video': with_video
            }
            
            active_calls[call_id] = call
            
            # Join the call room
            join_room(call_room)
            
            # Notify the caller
            emit('call_started', {
                'call_id': call_id,
                'call_room': call_room,
                'type': 'dm',
                'target': target_id,
                'with_video': with_video
            })
            
            # Notify the target user
            for sid, user in store.online_users.items():
                if user == target_id:
                    emit('incoming_call', {
                        'call_id': call_id,
                        'call_room': call_room,
                        'type': 'dm',
                        'caller': username,
                        'with_video': with_video
                    }, room=sid)
            
            print(f"📞 {username} started {'video' if with_video else 'voice'} call with {target_id}")
        
        elif call_type == 'group':
            # Group call
            group = store.get_group(target_id)
            if not group or username not in group['members']:
                emit('call_error', {'error': 'Not authorized for this group'})
                return
            
            call = {
                'id': call_id,
                'type': 'group',
                'group_id': target_id,
                'group_name': group['name'],
                'participants': [{
                    'username': username,
                    'role': 'caller',
                    'video': with_video,
                    'audio': True,
                    'joined_at': datetime.now().isoformat()
                }],
                'started_at': datetime.now().isoformat(),
                'started_by': username,
                'with_video': with_video,
                'allowed_members': group['members']
            }
            
            active_calls[call_id] = call
            
            # Join the call room
            join_room(call_room)
            
            # Notify the caller
            emit('call_started', {
                'call_id': call_id,
                'call_room': call_room,
                'type': 'group',
                'group_id': target_id,
                'group_name': group['name'],
                'with_video': with_video
            })
            
            # Notify all group members
            for member in group['members']:
                if member != username:
                    for sid, user in store.online_users.items():
                        if user == member:
                            emit('incoming_call', {
                                'call_id': call_id,
                                'call_room': call_room,
                                'type': 'group',
                                'caller': username,
                                'group_id': target_id,
                                'group_name': group['name'],
                                'with_video': with_video
                            }, room=sid)
            
            print(f"📞 {username} started group {'video' if with_video else 'voice'} call in '{group['name']}'")
        
        elif call_type == 'channel':
            # Channel call - role-based permissions
            channel = store.get_channel(target_id)
            if not channel:
                emit('call_error', {'error': 'Channel not found'})
                return
            
            # Check if user can start call (must be admin or moderator)
            user_role = store.get_user_channel_role(target_id, username)
            if user_role not in ['admin', 'mod']:
                emit('call_error', {'error': 'Only admins and moderators can start channel calls'})
                return
            
            call = {
                'id': call_id,
                'type': 'channel',
                'channel_id': target_id,
                'channel_name': channel['name'],
                'participants': [{
                    'username': username,
                    'role': user_role,  # 'admin' or 'mod'
                    'can_speak': True,
                    'video': with_video,
                    'audio': True,
                    'joined_at': datetime.now().isoformat()
                }],
                'started_at': datetime.now().isoformat(),
                'started_by': username,
                'with_video': with_video
            }
            
            active_calls[call_id] = call
            
            # Join the call room
            join_room(call_room)
            
            # Notify the caller
            emit('call_started', {
                'call_id': call_id,
                'call_room': call_room,
                'type': 'channel',
                'channel_id': target_id,
                'channel_name': channel['name'],
                'with_video': with_video,
                'your_role': user_role,
                'can_speak': True
            })
            
            # Notify all channel subscribers
            for subscriber in channel.get('subscribers', []):
                if subscriber != username:
                    sub_role = store.get_user_channel_role(target_id, subscriber)
                    can_speak = sub_role in ['admin', 'mod']
                    
                    for sid, user in store.online_users.items():
                        if user == subscriber:
                            emit('incoming_call', {
                                'call_id': call_id,
                                'call_room': call_room,
                                'type': 'channel',
                                'caller': username,
                                'channel_id': target_id,
                                'channel_name': channel['name'],
                                'with_video': with_video,
                                'your_role': sub_role,
                                'can_speak': can_speak
                            }, room=sid)
            
            print(f"📞 {username} started channel {'video' if with_video else 'voice'} call in '{channel['name']}'")
    
    # ==========================================
    # CALL JOINING
    # ==========================================
    
    @socketio.on('join_call')
    def handle_join_call(data):
        """Join an existing call"""
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        with_video = data.get('video', False)
        
        if call_id not in active_calls:
            emit('call_error', {'error': 'Call not found or has ended'})
            return
        
        call = active_calls[call_id]
        call_room = f"call_room_{call_id}"
        
        # Check permissions based on call type
        can_speak = True
        user_role = 'participant'
        
        if call['type'] == 'dm':
            if username not in [call['started_by'], call['target']]:
                emit('call_error', {'error': 'Not authorized for this call'})
                return
        
        elif call['type'] == 'group':
            if username not in call['allowed_members']:
                emit('call_error', {'error': 'Not a member of this group'})
                return
        
        elif call['type'] == 'channel':
            user_role = store.get_user_channel_role(call['channel_id'], username)
            can_speak = user_role in ['admin', 'mod']
        
        # Check if already in call
        existing = next((p for p in call['participants'] if p['username'] == username), None)
        if existing:
            emit('call_error', {'error': 'Already in this call'})
            return
        
        # Add to participants
        participant = {
            'username': username,
            'role': user_role,
            'can_speak': can_speak,
            'video': with_video if can_speak else False,
            'audio': can_speak,
            'joined_at': datetime.now().isoformat()
        }
        call['participants'].append(participant)
        
        # Join the call room
        join_room(call_room)
        
        # Notify the joiner
        emit('call_joined', {
            'call_id': call_id,
            'call_room': call_room,
            'type': call['type'],
            'participants': call['participants'],
            'can_speak': can_speak,
            'with_video': call['with_video']
        })
        
        # Notify other participants
        emit('participant_joined', {
            'call_id': call_id,
            'participant': participant
        }, room=call_room, include_self=False)
        
        print(f"📞 {username} joined call {call_id} ({'can speak' if can_speak else 'listener only'})")
    
    # ==========================================
    # WEBRTC SIGNALING
    # ==========================================
    
    @socketio.on('call_signal')
    def handle_call_signal(data):
        """
        Relay WebRTC signaling data between peers.
        data: {call_id, to_user, signal_type, signal_data}
        signal_type: 'offer', 'answer', 'ice-candidate'
        """
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        to_user = data.get('to_user')
        signal_type = data.get('signal_type')
        signal_data = data.get('signal_data')
        
        if call_id not in active_calls:
            return
        
        call = active_calls[call_id]
        
        # Verify sender is in the call
        if not any(p['username'] == username for p in call['participants']):
            return
        
        # Send signal to specific user
        for sid, user in store.online_users.items():
            if user == to_user:
                emit('call_signal', {
                    'call_id': call_id,
                    'from_user': username,
                    'signal_type': signal_type,
                    'signal_data': signal_data
                }, room=sid)
                break
    
    # ==========================================
    # CALL CONTROLS
    # ==========================================
    
    @socketio.on('toggle_audio')
    def handle_toggle_audio(data):
        """Toggle audio mute/unmute"""
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        audio_enabled = data.get('enabled', True)
        
        if call_id not in active_calls:
            return
        
        call = active_calls[call_id]
        call_room = f"call_room_{call_id}"
        
        # Update participant status
        for p in call['participants']:
            if p['username'] == username:
                # Check if user can unmute (channel listeners can't)
                if not p.get('can_speak', True) and audio_enabled:
                    emit('call_error', {'error': 'Listeners cannot unmute'})
                    return
                p['audio'] = audio_enabled
                break
        
        # Notify all participants
        emit('participant_audio_changed', {
            'call_id': call_id,
            'username': username,
            'audio': audio_enabled
        }, room=call_room)
    
    @socketio.on('toggle_video')
    def handle_toggle_video(data):
        """Toggle video on/off"""
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        video_enabled = data.get('enabled', True)
        
        if call_id not in active_calls:
            return
        
        call = active_calls[call_id]
        call_room = f"call_room_{call_id}"
        
        # Update participant status
        for p in call['participants']:
            if p['username'] == username:
                # Check if user can enable video (channel listeners can't)
                if not p.get('can_speak', True) and video_enabled:
                    emit('call_error', {'error': 'Listeners cannot share video'})
                    return
                p['video'] = video_enabled
                break
        
        # Notify all participants
        emit('participant_video_changed', {
            'call_id': call_id,
            'username': username,
            'video': video_enabled
        }, room=call_room)
    
    @socketio.on('start_screen_share')
    def handle_screen_share(data):
        """Start screen sharing"""
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        
        if call_id not in active_calls:
            return
        
        call = active_calls[call_id]
        call_room = f"call_room_{call_id}"
        
        # Check if user can share (must be able to speak)
        participant = next((p for p in call['participants'] if p['username'] == username), None)
        if not participant or not participant.get('can_speak', True):
            emit('call_error', {'error': 'You cannot share screen'})
            return
        
        # Notify all participants
        emit('screen_share_started', {
            'call_id': call_id,
            'username': username
        }, room=call_room)
    
    @socketio.on('stop_screen_share')
    def handle_stop_screen_share(data):
        """Stop screen sharing"""
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        call_room = f"call_room_{call_id}"
        
        emit('screen_share_stopped', {
            'call_id': call_id,
            'username': username
        }, room=call_room)
    
    # ==========================================
    # CALL ENDING
    # ==========================================
    
    @socketio.on('leave_call')
    def handle_leave_call(data):
        """Leave a call (but don't end it for others)"""
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        
        if call_id not in active_calls:
            return
        
        call = active_calls[call_id]
        call_room = f"call_room_{call_id}"
        
        # Remove from participants
        call['participants'] = [p for p in call['participants'] if p['username'] != username]
        
        # Leave the room
        leave_room(call_room)
        
        # Notify others
        emit('participant_left', {
            'call_id': call_id,
            'username': username
        }, room=call_room)
        
        # If no participants left, end the call
        if len(call['participants']) == 0:
            del active_calls[call_id]
            emit('call_ended', {'call_id': call_id, 'reason': 'All participants left'}, room=call_room)
        
        # For DM calls, if one person leaves, end the call
        elif call['type'] == 'dm' and len(call['participants']) == 1:
            remaining = call['participants'][0]['username']
            del active_calls[call_id]
            emit('call_ended', {
                'call_id': call_id,
                'reason': f'{username} left the call'
            }, room=call_room)
        
        print(f"📞 {username} left call {call_id}")
    
    @socketio.on('end_call')
    def handle_end_call(data):
        """End a call for all participants"""
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        
        if call_id not in active_calls:
            return
        
        call = active_calls[call_id]
        call_room = f"call_room_{call_id}"
        
        # Only the caller or admins can end the call
        can_end = username == call['started_by']
        if call['type'] == 'channel':
            user_role = store.get_user_channel_role(call['channel_id'], username)
            can_end = can_end or user_role == 'admin'
        
        if not can_end:
            emit('call_error', {'error': 'Only the caller can end this call'})
            return
        
        # End the call
        del active_calls[call_id]
        
        emit('call_ended', {
            'call_id': call_id,
            'ended_by': username,
            'reason': 'Call ended'
        }, room=call_room)
        
        print(f"📞 {username} ended call {call_id}")
    
    @socketio.on('decline_call')
    def handle_decline_call(data):
        """Decline an incoming call"""
        if 'username' not in session:
            return
        
        username = session['username']
        call_id = data.get('call_id')
        
        if call_id not in active_calls:
            return
        
        call = active_calls[call_id]
        call_room = f"call_room_{call_id}"
        
        # For DM calls, declining ends the call
        if call['type'] == 'dm':
            del active_calls[call_id]
            emit('call_declined', {
                'call_id': call_id,
                'declined_by': username
            }, room=call_room)
        else:
            # For group/channel calls, just notify
            emit('call_declined', {
                'call_id': call_id,
                'declined_by': username
            }, room=call_room)
        
        print(f"📞 {username} declined call {call_id}")
    
    # ==========================================
    # CALL STATUS
    # ==========================================
    
    @socketio.on('get_active_call')
    def handle_get_active_call(data):
        """Check if there's an active call for a chat/group/channel"""
        if 'username' not in session:
            return
        
        call_type = data.get('type')
        target_id = data.get('target_id')
        
        for call_id, call in active_calls.items():
            if call['type'] == call_type:
                if call_type == 'dm' and target_id in [call.get('target'), call.get('started_by')]:
                    emit('active_call_found', {'call': call})
                    return
                elif call_type == 'group' and call.get('group_id') == target_id:
                    emit('active_call_found', {'call': call})
                    return
                elif call_type == 'channel' and call.get('channel_id') == target_id:
                    emit('active_call_found', {'call': call})
                    return
        
        emit('no_active_call', {'type': call_type, 'target_id': target_id})

