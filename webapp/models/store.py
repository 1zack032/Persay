"""
💾 Data Store

Centralized in-memory data storage.
In production, replace with a real database (PostgreSQL, MongoDB, etc.)

This module provides a single source of truth for all app data,
making it easy to swap out for a database later.
"""

import secrets
from datetime import datetime
from typing import Dict, List, Optional, Any


class DataStore:
    """
    In-memory data store for the application.
    
    STRUCTURE:
    - users: username -> user_data
    - messages: room_id -> [messages]
    - online_users: socket_id -> username
    - channels: channel_id -> channel_data
    - channel_posts: post_id -> post_data
    """
    
    def __init__(self):
        # User data
        self.users: Dict[str, dict] = {}
        
        # Private messaging
        self.messages: Dict[str, List[dict]] = {}
        self.online_users: Dict[str, str] = {}
        self.chat_settings: Dict[str, dict] = {}  # room_id -> settings
        
        # Shared notes (persist across chat clears)
        # note_id -> {id, room_id, title, content, created_by, created_at, member_phrases: {username: hashed_phrase}}
        self.shared_notes: Dict[str, dict] = {}
        
        # Groups (group chats)
        self.groups: Dict[str, dict] = {}
        # group_id -> {id, name, members: [], owner, created_at, invite_code}
        
        # Channels
        self.channels: Dict[str, dict] = {}
        self.channel_posts: Dict[str, dict] = {}
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID"""
        return secrets.token_hex(8)
    
    @staticmethod
    def now() -> str:
        """Get current timestamp as ISO string"""
        return datetime.now().isoformat()
    
    # ==========================================
    # USER METHODS
    # ==========================================
    
    def create_user(self, username: str, password: str) -> dict:
        """Create a new user with extended profile fields"""
        user = {
            'username': username,
            'password': password,  # TODO: Hash in production!
            'public_key': None,
            'created': self.now(),
            'age_verified': True,
            'terms_accepted': self.now(),
            # Profile fields
            'display_name': None,
            'email': None,
            'email_verified': False,
            'phone': None,
            'phone_verified': False,
            'profile_image': None,
            'reset_method': 'email',  # 'email' or 'phone'
            # Privacy settings
            'show_online_status': True,
            'show_read_receipts': True,
        }
        self.users[username] = user
        return user
    
    def get_user(self, username: str) -> Optional[dict]:
        """Get user by username"""
        user = self.users.get(username)
        if user:
            # Ensure all profile fields exist (for backward compatibility)
            defaults = {
                'display_name': None,
                'email': None,
                'email_verified': False,
                'phone': None,
                'phone_verified': False,
                'profile_image': None,
                'reset_method': 'email',
                'show_online_status': True,
                'show_read_receipts': True,
            }
            for key, value in defaults.items():
                if key not in user:
                    user[key] = value
        return user
    
    def update_user_profile(self, username: str, data: dict) -> bool:
        """Update user profile fields"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        # Allowed fields to update
        allowed_fields = [
            'display_name', 'email', 'phone', 'profile_image',
            'reset_method', 'show_online_status', 'show_read_receipts',
            'contact_sync_enabled', 'allow_contact_discovery',
            'find_by_username', 'find_by_phone', 'find_by_email',
            'synced_contacts', 'last_contact_sync',
            'seed_hash', 'password'  # For account recovery
        ]
        
        for field in allowed_fields:
            if field in data:
                user[field] = data[field]
                
                # Reset verification when email/phone changes
                if field == 'email' and data[field] != user.get('email'):
                    user['email_verified'] = False
                if field == 'phone' and data[field] != user.get('phone'):
                    user['phone_verified'] = False
        
        return True
    
    def find_user_by_contact(self, contact_type: str, value: str) -> Optional[str]:
        """Find a user by phone or email if they allow discovery"""
        if not value:
            return None
        
        # Normalize phone number (remove non-digits)
        if contact_type == 'phone':
            value = ''.join(filter(str.isdigit, value))
        else:
            value = value.lower().strip()
        
        for username, user in self.users.items():
            # Check if user allows this type of discovery
            if contact_type == 'phone':
                if not user.get('find_by_phone', False):
                    continue
                user_phone = ''.join(filter(str.isdigit, user.get('phone', '')))
                if user_phone and value in user_phone:
                    return username
            elif contact_type == 'email':
                if not user.get('find_by_email', False):
                    continue
                user_email = user.get('email', '').lower().strip()
                if user_email and value == user_email:
                    return username
        
        return None
    
    def change_user_password(self, username: str, current_password: str, new_password: str) -> bool:
        """Change user password after verifying current password"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        # Verify current password
        if user.get('password') != current_password:
            return False
        
        # Update password
        user['password'] = new_password
        return True
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return username in self.users
    
    def get_all_usernames(self) -> List[str]:
        """Get list of all usernames"""
        return list(self.users.keys())
    
    def set_user_public_key(self, username: str, public_key: str):
        """Set user's public key"""
        if username in self.users:
            self.users[username]['public_key'] = public_key
    
    # ==========================================
    # ONLINE STATUS METHODS
    # ==========================================
    
    def set_user_online(self, socket_id: str, username: str):
        """Mark user as online"""
        self.online_users[socket_id] = username
    
    def set_user_offline(self, socket_id: str) -> Optional[str]:
        """Mark user as offline, return username"""
        return self.online_users.pop(socket_id, None)
    
    def get_online_users(self) -> List[str]:
        """Get list of unique online usernames"""
        return list(set(self.online_users.values()))
    
    def is_user_online(self, username: str) -> bool:
        """Check if user is online"""
        return username in self.online_users.values()
    
    # ==========================================
    # MESSAGING METHODS
    # ==========================================
    
    def get_room_id(self, user1: str, user2: str) -> str:
        """Get consistent room ID for two users"""
        return '_'.join(sorted([user1, user2]))
    
    def add_message(self, room_id: str, message: dict):
        """Add message to a room"""
        if room_id not in self.messages:
            self.messages[room_id] = []
        
        # Add unique ID to message
        message['id'] = self.generate_id()
        
        # Add expiry time if room has auto-delete setting
        settings = self.chat_settings.get(room_id, {})
        auto_delete = settings.get('auto_delete')
        if auto_delete and auto_delete != 'never':
            message['expires_at'] = self._calculate_expiry(auto_delete)
        
        self.messages[room_id].append(message)
        return message
    
    def _calculate_expiry(self, period: str) -> str:
        """Calculate expiry timestamp based on period"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        deltas = {
            '1_day': timedelta(days=1),
            '1_week': timedelta(weeks=1),
            '1_month': timedelta(days=30),
            '1_year': timedelta(days=365)
        }
        
        delta = deltas.get(period)
        if delta:
            return (now + delta).isoformat()
        return None
    
    def get_messages(self, room_id: str) -> List[dict]:
        """Get messages for a room, filtering out expired ones"""
        messages = self.messages.get(room_id, [])
        
        # Filter out expired messages
        from datetime import datetime
        now = datetime.now()
        valid_messages = []
        
        for msg in messages:
            expires_at = msg.get('expires_at')
            if expires_at:
                try:
                    expiry = datetime.fromisoformat(expires_at)
                    if expiry <= now:
                        continue  # Skip expired message
                except:
                    pass
            valid_messages.append(msg)
        
        # Update stored messages to remove expired ones
        if len(valid_messages) != len(messages):
            self.messages[room_id] = valid_messages
        
        return valid_messages
    
    def delete_message(self, room_id: str, message_id: str, username: str) -> bool:
        """
        Delete a specific message.
        Only the sender can delete their own messages.
        """
        if room_id not in self.messages:
            return False
        
        messages = self.messages[room_id]
        for i, msg in enumerate(messages):
            if msg.get('id') == message_id:
                # Verify sender
                if msg.get('from') == username:
                    messages.pop(i)
                    return True
                break
        
        return False
    
    def clear_chat(self, room_id: str) -> bool:
        """Clear all messages and shared notes in a chat room (start completely fresh)"""
        if room_id in self.messages:
            self.messages[room_id] = []
            # Also clear all shared notes for this room
            self.clear_shared_notes_for_room(room_id)
            return True
        return False
    
    def get_chat_partners(self, username: str) -> List[dict]:
        """Get list of users that this user has chatted with (most recent first)"""
        partners = {}
        
        # Scan all message rooms to find chat partners
        for room_id, messages in self.messages.items():
            # Skip group rooms
            if room_id.startswith('group_'):
                continue
            
            # Check if this user is in the room
            users_in_room = room_id.split('_')
            if len(users_in_room) == 2 and username in users_in_room:
                other_user = users_in_room[0] if users_in_room[1] == username else users_in_room[1]
                
                # Get last message timestamp
                last_msg_time = None
                if messages:
                    last_msg = messages[-1]
                    last_msg_time = last_msg.get('timestamp')
                
                # Only include if there are messages
                if messages:
                    user_data = self.get_user(other_user)
                    partners[other_user] = {
                        'username': other_user,
                        'display_name': user_data.get('display_name', other_user) if user_data else other_user,
                        'profile_image': user_data.get('profile_image') if user_data else None,
                        'last_message_time': last_msg_time,
                        'message_count': len(messages)
                    }
        
        # Sort by last message time (most recent first)
        sorted_partners = sorted(
            partners.values(), 
            key=lambda x: x['last_message_time'] or '', 
            reverse=True
        )
        
        return sorted_partners
    
    # ==========================================
    # CHAT SETTINGS METHODS
    # ==========================================
    
    def get_chat_settings(self, room_id: str) -> dict:
        """Get settings for a chat room"""
        if room_id not in self.chat_settings:
            self.chat_settings[room_id] = {
                'auto_delete': 'never',  # Default: don't auto-delete
                'created': self.now()
            }
        return self.chat_settings[room_id]
    
    def set_auto_delete(self, room_id: str, period: str) -> dict:
        """
        Set auto-delete period for a chat.
        period: 'never', '1_day', '1_week', '1_month', '1_year'
        """
        valid_periods = ['never', '1_day', '1_week', '1_month', '1_year']
        if period not in valid_periods:
            period = 'never'
        
        settings = self.get_chat_settings(room_id)
        settings['auto_delete'] = period
        settings['updated'] = self.now()
        
        return settings
    
    # ==========================================
    # SHARED NOTES METHODS
    # ==========================================
    
    def create_shared_note(self, room_id: str, title: str, content: str, 
                          created_by: str, creator_phrase: str) -> dict:
        """
        Create a shared note in a chat room.
        The note persists even if messages are cleared.
        """
        import hashlib
        
        note_id = self.generate_id()
        
        # Hash the creator's phrase
        hashed_phrase = hashlib.sha256(creator_phrase.encode()).hexdigest()
        
        note = {
            'id': note_id,
            'room_id': room_id,
            'title': title,
            'content': content,
            'created_by': created_by,
            'created_at': self.now(),
            'member_phrases': {
                created_by: hashed_phrase
            },
            'pending_members': []  # Members who haven't set their phrase yet
        }
        
        self.shared_notes[note_id] = note
        return note
    
    def get_shared_notes_for_room(self, room_id: str) -> List[dict]:
        """Get all shared notes for a room"""
        return [note for note in self.shared_notes.values() if note['room_id'] == room_id]
    
    def get_shared_note(self, note_id: str) -> Optional[dict]:
        """Get a specific shared note"""
        return self.shared_notes.get(note_id)
    
    def set_note_phrase(self, note_id: str, username: str, phrase: str) -> bool:
        """Set a user's secret phrase for a shared note"""
        import hashlib
        
        if note_id not in self.shared_notes:
            return False
        
        note = self.shared_notes[note_id]
        hashed_phrase = hashlib.sha256(phrase.encode()).hexdigest()
        note['member_phrases'][username] = hashed_phrase
        
        # Remove from pending if they were pending
        if username in note.get('pending_members', []):
            note['pending_members'].remove(username)
        
        return True
    
    def verify_note_phrase(self, note_id: str, username: str, phrase: str) -> Optional[str]:
        """
        Verify a user's phrase and return note content if correct.
        Returns None if incorrect.
        """
        import hashlib
        
        if note_id not in self.shared_notes:
            return None
        
        note = self.shared_notes[note_id]
        
        if username not in note['member_phrases']:
            return None
        
        hashed_phrase = hashlib.sha256(phrase.encode()).hexdigest()
        stored_hash = note['member_phrases'][username]
        
        if hashed_phrase == stored_hash:
            return note['content']
        
        return None
    
    def user_has_phrase_set(self, note_id: str, username: str) -> bool:
        """Check if a user has set their phrase for a note"""
        if note_id not in self.shared_notes:
            return False
        return username in self.shared_notes[note_id]['member_phrases']
    
    def add_pending_member(self, note_id: str, username: str):
        """Add a user to the pending list for phrase setup"""
        if note_id in self.shared_notes:
            note = self.shared_notes[note_id]
            if username not in note['member_phrases'] and username not in note.get('pending_members', []):
                if 'pending_members' not in note:
                    note['pending_members'] = []
                note['pending_members'].append(username)
    
    def get_note_metadata(self, note_id: str, username: str) -> Optional[dict]:
        """
        Get note metadata (without content) for display.
        Shows whether user has phrase set, can unlock, etc.
        """
        if note_id not in self.shared_notes:
            return None
        
        note = self.shared_notes[note_id]
        has_phrase = username in note['member_phrases']
        
        return {
            'id': note['id'],
            'title': note['title'],
            'created_by': note['created_by'],
            'created_at': note['created_at'],
            'has_phrase': has_phrase,
            'is_pending': username in note.get('pending_members', []),
            'delete_requested_by': note.get('delete_requested_by', []),
            'last_edited_by': note.get('last_edited_by'),
            'last_edited_at': note.get('last_edited_at')
        }
    
    def edit_shared_note(self, note_id: str, username: str, phrase: str, 
                         new_title: str = None, new_content: str = None) -> dict:
        """
        Edit a shared note. User must provide correct phrase to edit.
        Returns status: 'success', 'unauthorized', or 'error'
        """
        import hashlib
        
        if note_id not in self.shared_notes:
            return {'status': 'error', 'message': 'Note not found'}
        
        note = self.shared_notes[note_id]
        
        # Verify user has access and correct phrase
        if username not in note['member_phrases']:
            return {'status': 'unauthorized', 'message': 'You do not have access to this note'}
        
        hashed_phrase = hashlib.sha256(phrase.encode()).hexdigest()
        if note['member_phrases'][username] != hashed_phrase:
            return {'status': 'unauthorized', 'message': 'Incorrect phrase'}
        
        # Update the note
        if new_title:
            note['title'] = new_title.strip()
        if new_content:
            note['content'] = new_content.strip()
        
        note['last_edited_by'] = username
        note['last_edited_at'] = self.now()
        
        return {
            'status': 'success',
            'note': {
                'id': note['id'],
                'title': note['title'],
                'last_edited_by': username,
                'last_edited_at': note['last_edited_at']
            }
        }
    
    def clear_shared_notes_for_room(self, room_id: str):
        """Delete all shared notes for a room"""
        notes_to_delete = [
            note_id for note_id, note in self.shared_notes.items()
            if note['room_id'] == room_id
        ]
        for note_id in notes_to_delete:
            del self.shared_notes[note_id]
    
    def request_note_deletion(self, note_id: str, username: str) -> dict:
        """
        Request deletion of a shared note.
        Both users must request deletion for the note to be deleted.
        Returns status: 'requested', 'deleted', or 'error'
        """
        if note_id not in self.shared_notes:
            return {'status': 'error', 'message': 'Note not found'}
        
        note = self.shared_notes[note_id]
        
        # Initialize delete_requested_by if not exists
        if 'delete_requested_by' not in note:
            note['delete_requested_by'] = []
        
        # Check if user is part of this note's room
        if username not in note['member_phrases'] and username not in note.get('pending_members', []):
            # Check if user is the creator
            if username != note['created_by']:
                return {'status': 'error', 'message': 'Not authorized'}
        
        # Add user to delete request list
        if username not in note['delete_requested_by']:
            note['delete_requested_by'].append(username)
        
        # Get the two participants (from room_id which is like "room_user1_user2")
        room_parts = note['room_id'].split('_')
        # Room ID format is typically sorted usernames joined
        
        # Check if both participants have requested deletion
        # We need at least 2 people to agree for deletion
        if len(note['delete_requested_by']) >= 2:
            # Both agreed - delete the note
            del self.shared_notes[note_id]
            return {'status': 'deleted', 'message': 'Note deleted by mutual agreement'}
        
        return {
            'status': 'requested',
            'message': 'Deletion requested. Waiting for the other person to agree.',
            'requested_by': note['delete_requested_by']
        }
    
    def cancel_delete_request(self, note_id: str, username: str) -> bool:
        """Cancel a deletion request"""
        if note_id not in self.shared_notes:
            return False
        
        note = self.shared_notes[note_id]
        if 'delete_requested_by' in note and username in note['delete_requested_by']:
            note['delete_requested_by'].remove(username)
            return True
        return False
    
    # ==========================================
    # GROUP (GROUP CHAT) METHODS
    # ==========================================
    
    def create_group(self, name: str, owner: str, members: List[str], invite_code: str = None) -> dict:
        """Create a new group chat"""
        group_id = self.generate_id()
        
        # Ensure owner is in members list
        all_members = list(set([owner] + members))
        
        group = {
            'id': group_id,
            'name': name,
            'owner': owner,
            'members': all_members,
            'created_at': self.now(),
            'invite_code': invite_code or secrets.token_urlsafe(8),
            'avatar_emoji': '👥',
            'last_message': None,
            'last_message_time': None
        }
        
        self.groups[group_id] = group
        return group
    
    def get_group(self, group_id: str) -> Optional[dict]:
        """Get a group by ID"""
        return self.groups.get(group_id)
    
    def get_user_groups(self, username: str) -> List[dict]:
        """Get all groups a user is a member of"""
        user_groups = []
        for group in self.groups.values():
            if username in group['members']:
                user_groups.append(group)
        # Sort by last message time (most recent first)
        user_groups.sort(key=lambda g: g.get('last_message_time') or g['created_at'], reverse=True)
        return user_groups
    
    def add_group_member(self, group_id: str, username: str) -> bool:
        """Add a member to a group"""
        if group_id not in self.groups:
            return False
        group = self.groups[group_id]
        if username not in group['members']:
            group['members'].append(username)
        return True
    
    def remove_group_member(self, group_id: str, username: str) -> bool:
        """Remove a member from a group"""
        if group_id not in self.groups:
            return False
        group = self.groups[group_id]
        if username in group['members'] and username != group['owner']:
            group['members'].remove(username)
            return True
        return False
    
    def get_group_by_invite_code(self, invite_code: str) -> Optional[dict]:
        """Find a group by its invite code"""
        for group in self.groups.values():
            if group.get('invite_code') == invite_code:
                return group
        return None
    
    def update_group_last_message(self, group_id: str, message: str):
        """Update the last message preview for a group"""
        if group_id in self.groups:
            self.groups[group_id]['last_message'] = message[:50]  # Truncate preview
            self.groups[group_id]['last_message_time'] = self.now()
    
    def get_group_messages(self, group_id: str) -> List[dict]:
        """Get all messages for a group"""
        room_id = f"group_{group_id}"
        return self.messages.get(room_id, [])
    
    def add_group_message(self, group_id: str, sender: str, content: str, encrypted: bool = True) -> dict:
        """Add a message to a group"""
        room_id = f"group_{group_id}"
        
        if room_id not in self.messages:
            self.messages[room_id] = []
        
        message = {
            'id': self.generate_id(),
            'sender': sender,
            'content': content,
            'encrypted': encrypted,
            'timestamp': self.now()
        }
        
        self.messages[room_id].append(message)
        
        # Update group's last message
        self.update_group_last_message(group_id, f"{sender}: {content}" if not encrypted else f"{sender}: [Encrypted]")
        
        return message
    
    # ==========================================
    # CHANNEL METHODS
    # ==========================================
    
    # Role constants
    ROLE_ADMIN = 'admin'       # Full rights: manage members, settings, posts, comments
    ROLE_MODERATOR = 'mod'     # Can post, comment, but can't manage permissions
    ROLE_VIEWER = 'viewer'     # Read-only access
    
    # Predefined interest categories for channel discovery
    INTEREST_CATEGORIES = {
        'trading': {'emoji': '📈', 'keywords': ['trading', 'stocks', 'forex', 'options', 'day trading', 'swing']},
        'crypto': {'emoji': '₿', 'keywords': ['crypto', 'bitcoin', 'ethereum', 'blockchain', 'defi', 'nft', 'web3']},
        'news': {'emoji': '📰', 'keywords': ['news', 'breaking', 'updates', 'daily', 'headlines', 'current events']},
        'communities': {'emoji': '👥', 'keywords': ['community', 'group', 'club', 'network', 'social', 'meetup']},
        'tech': {'emoji': '💻', 'keywords': ['tech', 'technology', 'software', 'coding', 'programming', 'ai', 'startup']},
        'gaming': {'emoji': '🎮', 'keywords': ['gaming', 'games', 'esports', 'stream', 'playstation', 'xbox', 'pc']},
        'music': {'emoji': '🎵', 'keywords': ['music', 'artist', 'producer', 'beats', 'hip hop', 'edm', 'rock']},
        'sports': {'emoji': '⚽', 'keywords': ['sports', 'football', 'basketball', 'soccer', 'nfl', 'nba', 'fitness']},
        'lifestyle': {'emoji': '✨', 'keywords': ['lifestyle', 'fashion', 'travel', 'food', 'health', 'wellness']},
        'education': {'emoji': '📚', 'keywords': ['education', 'learning', 'tutorial', 'course', 'study', 'school']},
        'entertainment': {'emoji': '🎬', 'keywords': ['entertainment', 'movies', 'tv', 'shows', 'celebrity', 'media']},
        'business': {'emoji': '💼', 'keywords': ['business', 'entrepreneur', 'startup', 'marketing', 'sales', 'finance']},
        'art': {'emoji': '🎨', 'keywords': ['art', 'design', 'creative', 'illustration', 'photography', 'visual']},
        'science': {'emoji': '🔬', 'keywords': ['science', 'research', 'space', 'physics', 'biology', 'chemistry']},
    }

    def create_channel(self, name: str, description: str, owner: str,
                       accent_color: str, avatar_emoji: str,
                       discoverable: bool = True, tags: list = None,
                       avatar_type: str = 'emoji', avatar_image: str = None) -> dict:
        """Create a new channel"""
        channel_id = self.generate_id()
        
        # Auto-detect categories from name and description
        detected_categories = self._detect_channel_categories(name, description)
        
        channel = {
            'id': channel_id,
            'name': name,
            'description': description,
            'owner': owner,
            'created': self.now(),
            'branding': {
                'accent_color': accent_color,
                'avatar_emoji': avatar_emoji,
                'avatar_type': avatar_type,  # 'emoji' or 'image'
                'avatar_image': avatar_image,  # Base64 encoded image data
            },
            'subscribers': [owner],  # For backwards compatibility
            'members': {
                owner: self.ROLE_ADMIN  # Owner is always admin
            },
            'posts': [],
            'discoverable': discoverable,
            'views': 0,
            'view_history': [],  # List of {timestamp, username} for tracking daily/weekly
            'likes': [],  # List of usernames who liked
            'like_history': [],  # List of {timestamp, username} for tracking daily/weekly
            'tags': tags or [],  # User-defined tags
            'categories': detected_categories,  # Auto-detected categories
        }
        self.channels[channel_id] = channel
        return channel
    
    def _detect_channel_categories(self, name: str, description: str) -> list:
        """Auto-detect categories based on channel name and description"""
        text = f"{name} {description}".lower()
        detected = []
        
        for category, data in self.INTEREST_CATEGORIES.items():
            for keyword in data['keywords']:
                if keyword.lower() in text:
                    if category not in detected:
                        detected.append(category)
                    break
        
        return detected
    
    def update_channel_tags(self, channel_id: str, tags: list) -> bool:
        """Update channel tags"""
        if channel_id in self.channels:
            self.channels[channel_id]['tags'] = tags
            # Re-detect categories
            channel = self.channels[channel_id]
            channel['categories'] = self._detect_channel_categories(
                channel['name'], 
                channel['description']
            )
            return True
        return False
    
    def search_channels_by_interest(self, query: str, limit: int = 20) -> dict:
        """
        Search channels by interest/category or name.
        Returns both exact matches and category suggestions.
        """
        query_lower = query.lower().strip()
        results = {
            'exact_matches': [],
            'category_matches': [],
            'suggestions': [],
            'related_categories': []
        }
        
        if not query_lower:
            return results
        
        # Find matching categories
        matching_categories = []
        for category, data in self.INTEREST_CATEGORIES.items():
            if query_lower in category.lower():
                matching_categories.append(category)
            else:
                for keyword in data['keywords']:
                    if query_lower in keyword.lower() or keyword.lower() in query_lower:
                        if category not in matching_categories:
                            matching_categories.append(category)
                        break
        
        results['related_categories'] = [
            {'name': cat, 'emoji': self.INTEREST_CATEGORIES[cat]['emoji']}
            for cat in matching_categories
        ]
        
        # Search discoverable channels
        for channel in self.channels.values():
            if not channel.get('discoverable', False):
                continue
            
            channel_data = channel.copy()
            channel_data['like_count'] = len(channel.get('likes', []))
            
            name_lower = channel['name'].lower()
            desc_lower = (channel.get('description') or '').lower()
            tags = [t.lower() for t in channel.get('tags', [])]
            categories = channel.get('categories', [])
            
            # Exact name match
            if query_lower in name_lower:
                results['exact_matches'].append(channel_data)
            # Category match
            elif any(cat in matching_categories for cat in categories):
                results['category_matches'].append(channel_data)
            # Tag match
            elif any(query_lower in tag for tag in tags):
                results['category_matches'].append(channel_data)
            # Description match
            elif query_lower in desc_lower:
                results['suggestions'].append(channel_data)
        
        # Sort by engagement
        for key in ['exact_matches', 'category_matches', 'suggestions']:
            results[key] = sorted(
                results[key], 
                key=lambda x: x.get('like_count', 0) + len(x.get('subscribers', [])),
                reverse=True
            )[:limit]
        
        return results
    
    def get_channels_by_category(self, category: str, limit: int = 20) -> list:
        """Get all discoverable channels in a specific category"""
        channels = []
        
        for channel in self.channels.values():
            if not channel.get('discoverable', False):
                continue
            
            if category in channel.get('categories', []):
                channel_data = channel.copy()
                channel_data['like_count'] = len(channel.get('likes', []))
                channels.append(channel_data)
        
        # Sort by engagement
        channels = sorted(
            channels,
            key=lambda x: x.get('like_count', 0) + len(x.get('subscribers', [])),
            reverse=True
        )
        
        return channels[:limit]
    
    def get_all_categories(self) -> list:
        """Get all interest categories with channel counts"""
        categories = []
        
        for category, data in self.INTEREST_CATEGORIES.items():
            count = sum(
                1 for ch in self.channels.values()
                if ch.get('discoverable', False) and category in ch.get('categories', [])
            )
            categories.append({
                'name': category,
                'emoji': data['emoji'],
                'channel_count': count
            })
        
        return sorted(categories, key=lambda x: x['channel_count'], reverse=True)
    
    def get_channel(self, channel_id: str) -> Optional[dict]:
        """Get channel by ID"""
        return self.channels.get(channel_id)
    
    def get_user_channel_role(self, channel_id: str, username: str) -> str:
        """Get user's role in a channel. Returns 'admin', 'mod', 'viewer', or None"""
        channel = self.channels.get(channel_id)
        if not channel:
            return None
        
        # Owner is always admin
        if channel.get('owner') == username:
            return 'admin'
        
        # Check members dict
        members = channel.get('members', {})
        if username in members:
            return members[username]
        
        # If subscribed but no specific role, they're a viewer
        if username in channel.get('subscribers', []):
            return 'viewer'
        
        return None
    
    def channel_exists(self, channel_id: str) -> bool:
        """Check if channel exists"""
        return channel_id in self.channels
    
    def get_all_channels(self) -> List[dict]:
        """Get all channels"""
        return list(self.channels.values())
    
    def get_user_channels(self, username: str) -> List[dict]:
        """Get channels owned by user"""
        return [c for c in self.channels.values() if c['owner'] == username]
    
    def get_subscribed_channels(self, username: str) -> List[dict]:
        """Get channels user is subscribed to (but doesn't own)"""
        return [c for c in self.channels.values() 
                if username in c.get('subscribers', []) and c['owner'] != username]
    
    def channel_name_exists(self, name: str) -> bool:
        """Check if channel name already exists"""
        return any(c['name'].lower() == name.lower() for c in self.channels.values())
    
    def subscribe_to_channel(self, channel_id: str, username: str, role: str = None) -> bool:
        """Subscribe user to channel with a role (default: viewer)"""
        if channel_id in self.channels:
            channel = self.channels[channel_id]
            
            # Add to subscribers list (backwards compatibility)
            if username not in channel['subscribers']:
                channel['subscribers'].append(username)
            
            # Initialize members dict if needed
            if 'members' not in channel:
                channel['members'] = {channel['owner']: self.ROLE_ADMIN}
            
            # Add to members with role (default to viewer for new joins)
            if username not in channel['members']:
                channel['members'][username] = role or self.ROLE_VIEWER
                return True
        return False
    
    def unsubscribe_from_channel(self, channel_id: str, username: str) -> bool:
        """Unsubscribe user from channel (owners can't unsubscribe)"""
        if channel_id in self.channels:
            channel = self.channels[channel_id]
            if username in channel['subscribers'] and channel['owner'] != username:
                channel['subscribers'].remove(username)
                # Also remove from members
                if 'members' in channel and username in channel['members']:
                    del channel['members'][username]
                return True
        return False
    
    def set_member_role(self, channel_id: str, username: str, role: str, by_user: str) -> bool:
        """
        Set a member's role in a channel.
        Only admins can change roles. Owner's role cannot be changed.
        """
        if channel_id not in self.channels:
            return False
        
        channel = self.channels[channel_id]
        
        # Check if the user making the change is an admin
        if 'members' not in channel:
            channel['members'] = {channel['owner']: self.ROLE_ADMIN}
        
        if channel['members'].get(by_user) != self.ROLE_ADMIN:
            return False  # Only admins can change roles
        
        # Can't change owner's role
        if username == channel['owner']:
            return False
        
        # Validate role
        if role not in [self.ROLE_ADMIN, self.ROLE_MODERATOR, self.ROLE_VIEWER]:
            return False
        
        # Set role (user must be a member)
        if username in channel.get('subscribers', []):
            channel['members'][username] = role
            return True
        
        return False
    
    def get_member_role(self, channel_id: str, username: str) -> Optional[str]:
        """Get a user's role in a channel"""
        if channel_id not in self.channels:
            return None
        
        channel = self.channels[channel_id]
        
        # Owner is always admin
        if username == channel['owner']:
            return self.ROLE_ADMIN
        
        # Check members dict
        if 'members' in channel:
            return channel['members'].get(username)
        
        # Fallback: if in subscribers but not in members, they're a viewer
        if username in channel.get('subscribers', []):
            return self.ROLE_VIEWER
        
        return None
    
    def can_post_in_channel(self, channel_id: str, username: str) -> bool:
        """Check if user can post in channel (admin or moderator)"""
        role = self.get_member_role(channel_id, username)
        return role in [self.ROLE_ADMIN, self.ROLE_MODERATOR]
    
    def can_manage_channel(self, channel_id: str, username: str) -> bool:
        """Check if user can manage channel settings/members (admin only)"""
        role = self.get_member_role(channel_id, username)
        return role == self.ROLE_ADMIN
    
    def get_channel_members_with_roles(self, channel_id: str) -> List[dict]:
        """Get all members of a channel with their roles"""
        if channel_id not in self.channels:
            return []
        
        channel = self.channels[channel_id]
        members = []
        
        for username in channel.get('subscribers', []):
            role = self.get_member_role(channel_id, username)
            members.append({
                'username': username,
                'role': role,
                'is_owner': username == channel['owner']
            })
        
        return members
    
    def set_channel_discoverable(self, channel_id: str, discoverable: bool) -> bool:
        """Set whether a channel is discoverable"""
        if channel_id in self.channels:
            self.channels[channel_id]['discoverable'] = discoverable
            return True
        return False
    
    def increment_channel_views(self, channel_id: str, username: str = None):
        """Increment view count for a channel and track view history"""
        if channel_id in self.channels:
            channel = self.channels[channel_id]
            channel['views'] = channel.get('views', 0) + 1
            
            # Track view history for trending calculations
            if 'view_history' not in channel:
                channel['view_history'] = []
            
            channel['view_history'].append({
                'timestamp': self.now(),
                'username': username
            })
            
            # Keep only last 7 days of view history to save memory
            self._cleanup_old_history(channel, 'view_history', days=7)
    
    def like_channel(self, channel_id: str, username: str) -> dict:
        """Like a channel. Returns success status and current like count."""
        if channel_id not in self.channels:
            return {'success': False, 'error': 'Channel not found'}
        
        channel = self.channels[channel_id]
        
        # Initialize likes if not exists
        if 'likes' not in channel:
            channel['likes'] = []
        if 'like_history' not in channel:
            channel['like_history'] = []
        
        # Check if already liked
        if username in channel['likes']:
            return {'success': False, 'error': 'Already liked', 'likes': len(channel['likes'])}
        
        # Add like
        channel['likes'].append(username)
        channel['like_history'].append({
            'timestamp': self.now(),
            'username': username
        })
        
        return {'success': True, 'likes': len(channel['likes'])}
    
    def unlike_channel(self, channel_id: str, username: str) -> dict:
        """Unlike a channel."""
        if channel_id not in self.channels:
            return {'success': False, 'error': 'Channel not found'}
        
        channel = self.channels[channel_id]
        
        if 'likes' not in channel or username not in channel['likes']:
            return {'success': False, 'error': 'Not liked', 'likes': len(channel.get('likes', []))}
        
        channel['likes'].remove(username)
        return {'success': True, 'likes': len(channel['likes'])}
    
    def has_liked_channel(self, channel_id: str, username: str) -> bool:
        """Check if user has liked a channel"""
        if channel_id not in self.channels:
            return False
        return username in self.channels[channel_id].get('likes', [])
    
    def _cleanup_old_history(self, channel: dict, history_key: str, days: int = 7):
        """Remove history entries older than specified days"""
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        if history_key in channel:
            channel[history_key] = [
                entry for entry in channel[history_key]
                if entry.get('timestamp', '') > cutoff
            ]
    
    def _get_history_count(self, channel: dict, history_key: str, period: str = 'daily') -> int:
        """Get count of history entries for a period (daily or weekly)"""
        from datetime import datetime, timedelta
        
        if period == 'daily':
            cutoff = (datetime.now() - timedelta(days=1)).isoformat()
        else:  # weekly
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        
        history = channel.get(history_key, [])
        return len([e for e in history if e.get('timestamp', '') > cutoff])
    
    def get_trending_channels(self, period: str = 'daily', sort_by: str = 'likes', limit: int = 20) -> List[dict]:
        """
        Get trending discoverable channels based on recent activity.
        
        Args:
            period: 'daily' or 'weekly'
            sort_by: 'likes', 'views', or 'combined'
            limit: maximum number of channels to return
        
        Returns channels sorted by trending score with rotation.
        """
        from datetime import datetime
        import random
        
        discoverable = [c for c in self.channels.values() if c.get('discoverable', False)]
        
        # Calculate trending scores
        for channel in discoverable:
            # Get recent activity counts
            recent_likes = self._get_history_count(channel, 'like_history', period)
            recent_views = self._get_history_count(channel, 'view_history', period)
            total_likes = len(channel.get('likes', []))
            total_views = channel.get('views', 0)
            
            # Calculate trending scores with recency boost
            if sort_by == 'likes':
                channel['_trending_score'] = (recent_likes * 10) + (total_likes * 2)
            elif sort_by == 'views':
                channel['_trending_score'] = (recent_views * 5) + (total_views * 0.5)
            else:  # combined
                channel['_trending_score'] = (recent_likes * 10) + (recent_views * 3) + (total_likes * 2) + (total_views * 0.2)
            
            # Add small random factor for rotation (0-5% variance)
            channel['_trending_score'] *= (1 + random.uniform(0, 0.05))
            
            # Add metadata for display
            channel['_recent_likes'] = recent_likes
            channel['_recent_views'] = recent_views
        
        # Sort by trending score
        sorted_channels = sorted(discoverable, key=lambda x: x.get('_trending_score', 0), reverse=True)
        
        return sorted_channels[:limit]
    
    def get_discover_channels_rotated(self, username: str = None) -> dict:
        """
        Get channels for the discover page with rotation algorithm.
        Returns categorized channels: trending, most_liked, most_viewed, new.
        """
        from datetime import datetime, timedelta
        import random
        
        discoverable = [c for c in self.channels.values() if c.get('discoverable', False)]
        
        # Don't show channels user is already subscribed to
        if username:
            discoverable = [c for c in discoverable if username not in c.get('subscribers', [])]
        
        # Get trending channels (combined score)
        trending = self.get_trending_channels(period='daily', sort_by='combined', limit=10)
        
        # Most liked this week
        most_liked = self.get_trending_channels(period='weekly', sort_by='likes', limit=10)
        
        # Most viewed this week  
        most_viewed = self.get_trending_channels(period='weekly', sort_by='views', limit=10)
        
        # New channels (created in last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        new_channels = [c for c in discoverable if c.get('created', '') > week_ago]
        new_channels = sorted(new_channels, key=lambda x: x.get('created', ''), reverse=True)[:10]
        
        # Apply rotation - shuffle within top sections periodically
        # This ensures fresh content appears even if scores are similar
        if trending and len(trending) > 3:
            top_trending = trending[:3]
            rest_trending = trending[3:]
            random.shuffle(rest_trending)
            trending = top_trending + rest_trending
        
        return {
            'trending': trending,
            'most_liked': most_liked,
            'most_viewed': most_viewed,
            'new': new_channels,
            'all': discoverable
        }
    
    def get_channel_engagement_score(self, channel: dict) -> float:
        """
        Calculate engagement score for ranking channels.
        
        ALGORITHM:
        - Subscribers: 10 points each
        - Posts: 5 points each
        - Total likes across posts: 2 points each
        - Total comments across posts: 3 points each
        - Views: 0.1 points each
        
        This rewards active channels with engaged communities.
        """
        score = 0.0
        
        # Subscriber count (most important)
        score += len(channel.get('subscribers', [])) * 10
        
        # Post count
        post_ids = channel.get('posts', [])
        score += len(post_ids) * 5
        
        # Engagement on posts
        for post_id in post_ids:
            post = self.channel_posts.get(post_id, {})
            # Likes
            score += len(post.get('likes', [])) * 2
            # Comments
            score += len(post.get('comments', [])) * 3
            # Reactions (total across all emojis)
            for users in post.get('reactions', {}).values():
                score += len(users) * 1.5
        
        # Views (less weight, prevents gaming)
        score += channel.get('views', 0) * 0.1
        
        return score
    
    def get_discoverable_channels(self, exclude_user: str = None, limit: int = 50) -> List[dict]:
        """
        Get discoverable channels ranked by engagement.
        Excludes channels the user already owns or subscribes to.
        """
        discoverable = []
        
        for channel in self.channels.values():
            # Only discoverable channels
            if not channel.get('discoverable', True):
                continue
            
            # Optionally exclude channels user is already part of
            if exclude_user:
                if channel['owner'] == exclude_user:
                    continue
                if exclude_user in channel.get('subscribers', []):
                    continue
            
            # Add engagement score for sorting
            channel_with_score = channel.copy()
            channel_with_score['_score'] = self.get_channel_engagement_score(channel)
            discoverable.append(channel_with_score)
        
        # Sort by engagement score (highest first)
        discoverable.sort(key=lambda x: x['_score'], reverse=True)
        
        # Remove internal score field and limit results
        for ch in discoverable:
            ch.pop('_score', None)
        
        return discoverable[:limit]
    
    def search_channels(self, query: str, discoverable_only: bool = True, 
                        limit: int = 20) -> List[dict]:
        """
        Search channels by name or description.
        
        Args:
            query: Search term
            discoverable_only: If True, only search discoverable channels
            limit: Max results to return
        
        Returns:
            List of matching channels, sorted by relevance
        """
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.lower().strip()
        results = []
        
        for channel in self.channels.values():
            # Skip non-discoverable if flag is set
            if discoverable_only and not channel.get('discoverable', True):
                continue
            
            # Calculate relevance score
            relevance = 0
            name_lower = channel['name'].lower()
            desc_lower = (channel.get('description') or '').lower()
            
            # Exact name match (highest priority)
            if name_lower == query:
                relevance = 100
            # Name starts with query
            elif name_lower.startswith(query):
                relevance = 80
            # Name contains query
            elif query in name_lower:
                relevance = 60
            # Description contains query
            elif query in desc_lower:
                relevance = 30
            # Check owner name
            elif query in channel['owner'].lower():
                relevance = 20
            else:
                continue  # No match
            
            # Add engagement bonus (max 20 points)
            engagement = min(self.get_channel_engagement_score(channel) / 100, 20)
            relevance += engagement
            
            channel_copy = channel.copy()
            channel_copy['_relevance'] = relevance
            results.append(channel_copy)
        
        # Sort by relevance (highest first)
        results.sort(key=lambda x: x['_relevance'], reverse=True)
        
        # Clean up and limit
        for ch in results:
            ch.pop('_relevance', None)
        
        return results[:limit]
    
    # ==========================================
    # CHANNEL POST METHODS
    # ==========================================
    
    def create_post(self, channel_id: str, author: str, content: str,
                    linked_post: Optional[str] = None) -> dict:
        """Create a new post in a channel"""
        post_id = self.generate_id()
        post = {
            'id': post_id,
            'channel_id': channel_id,
            'author': author,
            'content': content,
            'timestamp': self.now(),
            'linked_post': linked_post,
            'reactions': {},
            'comments': [],
            'likes': []
        }
        self.channel_posts[post_id] = post
        
        # Add to channel's post list
        if channel_id in self.channels:
            self.channels[channel_id]['posts'].append(post_id)
        
        return post
    
    def get_post(self, post_id: str) -> Optional[dict]:
        """Get post by ID"""
        return self.channel_posts.get(post_id)
    
    def get_channel_posts(self, channel_id: str) -> List[dict]:
        """Get all posts for a channel (newest first)"""
        if channel_id not in self.channels:
            return []
        
        posts = []
        for post_id in self.channels[channel_id].get('posts', []):
            if post_id in self.channel_posts:
                posts.append(self.channel_posts[post_id])
        
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        return posts
    
    def toggle_like(self, post_id: str, username: str) -> Optional[dict]:
        """Toggle like on a post, return updated post"""
        if post_id not in self.channel_posts:
            return None
        
        post = self.channel_posts[post_id]
        if username in post['likes']:
            post['likes'].remove(username)
        else:
            post['likes'].append(username)
        
        return post
    
    def toggle_reaction(self, post_id: str, emoji: str, username: str) -> Optional[dict]:
        """Toggle reaction on a post, return updated reactions"""
        if post_id not in self.channel_posts:
            return None
        
        post = self.channel_posts[post_id]
        
        if emoji not in post['reactions']:
            post['reactions'][emoji] = []
        
        if username in post['reactions'][emoji]:
            post['reactions'][emoji].remove(username)
            if not post['reactions'][emoji]:
                del post['reactions'][emoji]
        else:
            post['reactions'][emoji].append(username)
        
        return post
    
    def add_comment(self, post_id: str, author: str, content: str) -> Optional[dict]:
        """Add comment to a post, return the comment"""
        if post_id not in self.channel_posts:
            return None
        
        comment = {
            'id': self.generate_id(),
            'author': author,
            'content': content,
            'timestamp': self.now()
        }
        
        self.channel_posts[post_id]['comments'].append(comment)
        return comment


# Global store instance
store = DataStore()

# No test users in production - users must register

