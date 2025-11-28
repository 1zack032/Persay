"""
💾 Data Store - MongoDB Backend

Persistent data storage using MongoDB.
All data persists across server restarts.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# MongoDB connection
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    
    MONGODB_URI = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI')
    
    if MONGODB_URI:
        client = MongoClient(MONGODB_URI)
        # Test connection
        client.admin.command('ping')
        db = client.get_default_database() or client['menza']
        print("✅ Connected to MongoDB")
        USE_MONGODB = True
    else:
        print("⚠️ MONGODB_URI not set - using in-memory storage (data will be lost on restart)")
        USE_MONGODB = False
        db = None
except ImportError:
    print("⚠️ pymongo not installed - using in-memory storage")
    USE_MONGODB = False
    db = None
except ConnectionFailure as e:
    print(f"⚠️ MongoDB connection failed: {e} - using in-memory storage")
    USE_MONGODB = False
    db = None
except Exception as e:
    print(f"⚠️ MongoDB error: {e} - using in-memory storage")
    USE_MONGODB = False
    db = None


class DataStore:
    """
    Data store with MongoDB backend.
    Falls back to in-memory storage if MongoDB is unavailable.
    """
    
    # Role constants
    ROLE_ADMIN = 'admin'
    ROLE_MODERATOR = 'mod'
    ROLE_VIEWER = 'viewer'
    
    # Interest categories
    INTEREST_CATEGORIES = {
        'trading': {'emoji': '📈', 'keywords': ['trading', 'stocks', 'forex', 'options']},
        'crypto': {'emoji': '₿', 'keywords': ['crypto', 'bitcoin', 'ethereum', 'blockchain']},
        'news': {'emoji': '📰', 'keywords': ['news', 'breaking', 'updates', 'daily']},
        'communities': {'emoji': '👥', 'keywords': ['community', 'group', 'club', 'network']},
        'tech': {'emoji': '💻', 'keywords': ['tech', 'technology', 'software', 'coding']},
        'gaming': {'emoji': '🎮', 'keywords': ['gaming', 'games', 'esports', 'stream']},
        'music': {'emoji': '🎵', 'keywords': ['music', 'artist', 'producer', 'beats']},
        'sports': {'emoji': '⚽', 'keywords': ['sports', 'football', 'basketball', 'soccer']},
        'lifestyle': {'emoji': '✨', 'keywords': ['lifestyle', 'fashion', 'travel', 'food']},
        'education': {'emoji': '📚', 'keywords': ['education', 'learning', 'tutorial', 'course']},
    }
    
    def __init__(self):
        if USE_MONGODB:
            # MongoDB collections
            self.users_col = db['users']
            self.messages_col = db['messages']
            self.groups_col = db['groups']
            self.channels_col = db['channels']
            self.posts_col = db['posts']
            self.notes_col = db['shared_notes']
            self.settings_col = db['chat_settings']
            
            # Create indexes for faster queries
            self.users_col.create_index('username', unique=True)
            self.channels_col.create_index('name')
            self.messages_col.create_index('room_id')
            self.groups_col.create_index('invite_code')
            
            print("✅ MongoDB collections initialized")
        else:
            # Fallback to in-memory storage
            self.users: Dict[str, dict] = {}
            self.messages: Dict[str, List[dict]] = {}
            self.groups: Dict[str, dict] = {}
            self.channels: Dict[str, dict] = {}
            self.channel_posts: Dict[str, dict] = {}
            self.shared_notes: Dict[str, dict] = {}
            self.chat_settings: Dict[str, dict] = {}
        
        # Always in-memory (doesn't need persistence)
        self.online_users: Dict[str, str] = {}
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    @staticmethod
    def generate_id() -> str:
        return secrets.token_hex(8)
    
    @staticmethod
    def now() -> str:
        return datetime.now().isoformat()
    
    # ==========================================
    # USER METHODS
    # ==========================================
    
    def create_user(self, username: str, password: str) -> dict:
        user = {
            'username': username,
            'password': password,
            'public_key': None,
            'created': self.now(),
            'age_verified': True,
            'terms_accepted': self.now(),
            'display_name': None,
            'email': None,
            'phone': None,
            'profile_image': None,
            'show_online_status': True,
            'show_read_receipts': True,
        }
        
        if USE_MONGODB:
            self.users_col.insert_one(user)
        else:
            self.users[username] = user
        
        return user
    
    def get_user(self, username: str) -> Optional[dict]:
        if USE_MONGODB:
            user = self.users_col.find_one({'username': username}, {'_id': 0})
            return user
        else:
            return self.users.get(username)
    
    def update_user_profile(self, username: str, data: dict) -> bool:
        allowed_fields = [
            'display_name', 'email', 'phone', 'profile_image',
            'reset_method', 'show_online_status', 'show_read_receipts',
            'seed_hash', 'password'
        ]
        
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if USE_MONGODB:
            result = self.users_col.update_one(
                {'username': username},
                {'$set': update_data}
            )
            return result.modified_count > 0 or result.matched_count > 0
        else:
            if username not in self.users:
                return False
            for k, v in update_data.items():
                self.users[username][k] = v
            return True
    
    def user_exists(self, username: str) -> bool:
        if USE_MONGODB:
            return self.users_col.count_documents({'username': username}) > 0
        else:
            return username in self.users
    
    def get_all_usernames(self) -> List[str]:
        if USE_MONGODB:
            return [u['username'] for u in self.users_col.find({}, {'username': 1, '_id': 0})]
        else:
            return list(self.users.keys())
    
    def change_user_password(self, username: str, current_password: str, new_password: str) -> bool:
        user = self.get_user(username)
        if not user or user.get('password') != current_password:
            return False
        return self.update_user_profile(username, {'password': new_password})
    
    def set_user_public_key(self, username: str, public_key: str):
        self.update_user_profile(username, {'public_key': public_key})
    
    def find_user_by_contact(self, contact_type: str, value: str) -> Optional[str]:
        if not value:
            return None
        
        if USE_MONGODB:
            query = {contact_type: value, f'find_by_{contact_type}': True}
            user = self.users_col.find_one(query, {'username': 1})
            return user['username'] if user else None
        else:
            for username, user in self.users.items():
                if user.get(contact_type) == value and user.get(f'find_by_{contact_type}'):
                    return username
            return None
    
    # ==========================================
    # ONLINE STATUS (Always in-memory)
    # ==========================================
    
    def set_user_online(self, socket_id: str, username: str):
        self.online_users[socket_id] = username
    
    def set_user_offline(self, socket_id: str) -> Optional[str]:
        return self.online_users.pop(socket_id, None)
    
    def get_online_users(self) -> List[str]:
        return list(set(self.online_users.values()))
    
    def is_user_online(self, username: str) -> bool:
        return username in self.online_users.values()
    
    # ==========================================
    # MESSAGING METHODS
    # ==========================================
    
    def get_room_id(self, user1: str, user2: str) -> str:
        return '_'.join(sorted([user1, user2]))
    
    def add_message(self, room_id: str, message: dict):
        message['id'] = self.generate_id()
        message['room_id'] = room_id
        
        if USE_MONGODB:
            self.messages_col.insert_one(message)
        else:
            if room_id not in self.messages:
                self.messages[room_id] = []
            self.messages[room_id].append(message)
        
        return message
    
    def get_messages(self, room_id: str) -> List[dict]:
        if USE_MONGODB:
            messages = list(self.messages_col.find(
                {'room_id': room_id},
                {'_id': 0}
            ).sort('timestamp', 1))
            return messages
        else:
            return self.messages.get(room_id, [])
    
    def delete_message(self, room_id: str, message_id: str, username: str) -> bool:
        if USE_MONGODB:
            result = self.messages_col.delete_one({
                'id': message_id,
                'room_id': room_id,
                'from': username
            })
            return result.deleted_count > 0
        else:
            if room_id not in self.messages:
                return False
            for i, msg in enumerate(self.messages[room_id]):
                if msg.get('id') == message_id and msg.get('from') == username:
                    self.messages[room_id].pop(i)
                    return True
            return False
    
    def clear_chat(self, room_id: str) -> bool:
        if USE_MONGODB:
            self.messages_col.delete_many({'room_id': room_id})
            self.notes_col.delete_many({'room_id': room_id})
            return True
        else:
            if room_id in self.messages:
                self.messages[room_id] = []
            return True
    
    def get_chat_partners(self, username: str) -> List[dict]:
        if USE_MONGODB:
            # Find all rooms this user is part of
            pipeline = [
                {'$match': {'room_id': {'$regex': f'^{username}_|_{username}$'}}},
                {'$group': {
                    '_id': '$room_id',
                    'last_message_time': {'$max': '$timestamp'},
                    'message_count': {'$sum': 1}
                }}
            ]
            rooms = list(self.messages_col.aggregate(pipeline))
            
            partners = []
            for room in rooms:
                room_id = room['_id']
                if room_id.startswith('group_'):
                    continue
                users = room_id.split('_')
                if len(users) == 2:
                    other = users[0] if users[1] == username else users[1]
                    user_data = self.get_user(other)
                    partners.append({
                        'username': other,
                        'display_name': user_data.get('display_name', other) if user_data else other,
                        'last_message_time': room['last_message_time'],
                        'message_count': room['message_count']
                    })
            
            return sorted(partners, key=lambda x: x['last_message_time'] or '', reverse=True)
        else:
            partners = {}
            for room_id, messages in self.messages.items():
                if room_id.startswith('group_'):
                    continue
                users = room_id.split('_')
                if len(users) == 2 and username in users:
                    other = users[0] if users[1] == username else users[1]
                    if messages:
                        user_data = self.get_user(other)
                        partners[other] = {
                            'username': other,
                            'display_name': user_data.get('display_name', other) if user_data else other,
                            'last_message_time': messages[-1].get('timestamp'),
                            'message_count': len(messages)
                        }
            return sorted(partners.values(), key=lambda x: x['last_message_time'] or '', reverse=True)
    
    # ==========================================
    # CHAT SETTINGS
    # ==========================================
    
    def get_chat_settings(self, room_id: str) -> dict:
        if USE_MONGODB:
            settings = self.settings_col.find_one({'room_id': room_id}, {'_id': 0})
            if not settings:
                settings = {'room_id': room_id, 'auto_delete': 'never', 'created': self.now()}
                self.settings_col.insert_one(settings)
            return settings
        else:
            if room_id not in self.chat_settings:
                self.chat_settings[room_id] = {'auto_delete': 'never', 'created': self.now()}
            return self.chat_settings[room_id]
    
    def set_auto_delete(self, room_id: str, period: str) -> dict:
        valid = ['never', '1_day', '1_week', '1_month', '1_year']
        if period not in valid:
            period = 'never'
        
        if USE_MONGODB:
            self.settings_col.update_one(
                {'room_id': room_id},
                {'$set': {'auto_delete': period, 'updated': self.now()}},
                upsert=True
            )
        else:
            settings = self.get_chat_settings(room_id)
            settings['auto_delete'] = period
        
        return self.get_chat_settings(room_id)
    
    # ==========================================
    # SHARED NOTES
    # ==========================================
    
    def create_shared_note(self, room_id: str, title: str, content: str,
                          created_by: str, creator_phrase: str) -> dict:
        import hashlib
        
        note = {
            'id': self.generate_id(),
            'room_id': room_id,
            'title': title,
            'content': content,
            'created_by': created_by,
            'created_at': self.now(),
            'member_phrases': {created_by: hashlib.sha256(creator_phrase.encode()).hexdigest()},
            'pending_members': []
        }
        
        if USE_MONGODB:
            self.notes_col.insert_one(note)
        else:
            self.shared_notes[note['id']] = note
        
        return note
    
    def get_shared_notes_for_room(self, room_id: str) -> List[dict]:
        if USE_MONGODB:
            return list(self.notes_col.find({'room_id': room_id}, {'_id': 0}))
        else:
            return [n for n in self.shared_notes.values() if n['room_id'] == room_id]
    
    def get_shared_note(self, note_id: str) -> Optional[dict]:
        if USE_MONGODB:
            return self.notes_col.find_one({'id': note_id}, {'_id': 0})
        else:
            return self.shared_notes.get(note_id)
    
    def set_note_phrase(self, note_id: str, username: str, phrase: str) -> bool:
        import hashlib
        hashed = hashlib.sha256(phrase.encode()).hexdigest()
        
        if USE_MONGODB:
            result = self.notes_col.update_one(
                {'id': note_id},
                {
                    '$set': {f'member_phrases.{username}': hashed},
                    '$pull': {'pending_members': username}
                }
            )
            return result.modified_count > 0
        else:
            if note_id not in self.shared_notes:
                return False
            self.shared_notes[note_id]['member_phrases'][username] = hashed
            return True
    
    def verify_note_phrase(self, note_id: str, username: str, phrase: str) -> Optional[str]:
        import hashlib
        note = self.get_shared_note(note_id)
        if not note or username not in note.get('member_phrases', {}):
            return None
        
        hashed = hashlib.sha256(phrase.encode()).hexdigest()
        if hashed == note['member_phrases'][username]:
            return note['content']
        return None
    
    def user_has_phrase_set(self, note_id: str, username: str) -> bool:
        note = self.get_shared_note(note_id)
        return note and username in note.get('member_phrases', {})
    
    def get_note_metadata(self, note_id: str, username: str) -> Optional[dict]:
        note = self.get_shared_note(note_id)
        if not note:
            return None
        return {
            'id': note['id'],
            'title': note['title'],
            'created_by': note['created_by'],
            'created_at': note['created_at'],
            'has_phrase': username in note.get('member_phrases', {}),
            'is_pending': username in note.get('pending_members', [])
        }
    
    def clear_shared_notes_for_room(self, room_id: str):
        if USE_MONGODB:
            self.notes_col.delete_many({'room_id': room_id})
        else:
            to_delete = [nid for nid, n in self.shared_notes.items() if n['room_id'] == room_id]
            for nid in to_delete:
                del self.shared_notes[nid]
    
    # ==========================================
    # GROUP METHODS
    # ==========================================
    
    def create_group(self, name: str, owner: str, members: List[str], invite_code: str = None) -> dict:
        group = {
            'id': self.generate_id(),
            'name': name,
            'owner': owner,
            'members': list(set([owner] + members)),
            'created_at': self.now(),
            'invite_code': invite_code or secrets.token_urlsafe(8),
            'avatar_emoji': '👥',
            'last_message': None,
            'last_message_time': None
        }
        
        if USE_MONGODB:
            self.groups_col.insert_one(group)
        else:
            self.groups[group['id']] = group
        
        return group
    
    def get_group(self, group_id: str) -> Optional[dict]:
        if USE_MONGODB:
            return self.groups_col.find_one({'id': group_id}, {'_id': 0})
        else:
            return self.groups.get(group_id)
    
    def get_user_groups(self, username: str) -> List[dict]:
        if USE_MONGODB:
            groups = list(self.groups_col.find({'members': username}, {'_id': 0}))
            return sorted(groups, key=lambda g: g.get('last_message_time') or g['created_at'], reverse=True)
        else:
            groups = [g for g in self.groups.values() if username in g['members']]
            return sorted(groups, key=lambda g: g.get('last_message_time') or g['created_at'], reverse=True)
    
    def add_group_member(self, group_id: str, username: str) -> bool:
        if USE_MONGODB:
            result = self.groups_col.update_one(
                {'id': group_id},
                {'$addToSet': {'members': username}}
            )
            return result.modified_count > 0
        else:
            if group_id in self.groups and username not in self.groups[group_id]['members']:
                self.groups[group_id]['members'].append(username)
                return True
            return False
    
    def get_group_by_invite_code(self, invite_code: str) -> Optional[dict]:
        if USE_MONGODB:
            return self.groups_col.find_one({'invite_code': invite_code}, {'_id': 0})
        else:
            for g in self.groups.values():
                if g.get('invite_code') == invite_code:
                    return g
            return None
    
    def update_group_last_message(self, group_id: str, message: str):
        if USE_MONGODB:
            self.groups_col.update_one(
                {'id': group_id},
                {'$set': {'last_message': message[:50], 'last_message_time': self.now()}}
            )
        else:
            if group_id in self.groups:
                self.groups[group_id]['last_message'] = message[:50]
                self.groups[group_id]['last_message_time'] = self.now()
    
    def get_group_messages(self, group_id: str) -> List[dict]:
        return self.get_messages(f"group_{group_id}")
    
    def add_group_message(self, group_id: str, sender: str, content: str, encrypted: bool = True) -> dict:
        message = {
            'sender': sender,
            'content': content,
            'encrypted': encrypted,
            'timestamp': self.now()
        }
        result = self.add_message(f"group_{group_id}", message)
        self.update_group_last_message(group_id, f"{sender}: [Encrypted]" if encrypted else f"{sender}: {content}")
        return result
    
    # ==========================================
    # CHANNEL METHODS
    # ==========================================
    
    def create_channel(self, name: str, description: str, owner: str,
                       accent_color: str, avatar_emoji: str,
                       discoverable: bool = True, tags: list = None,
                       avatar_type: str = 'emoji', avatar_image: str = None) -> dict:
        channel = {
            'id': self.generate_id(),
            'name': name,
            'description': description,
            'owner': owner,
            'created': self.now(),
            'branding': {
                'accent_color': accent_color,
                'avatar_emoji': avatar_emoji,
                'avatar_type': avatar_type,
                'avatar_image': avatar_image,
            },
            'subscribers': [owner],
            'members': {owner: self.ROLE_ADMIN},
            'posts': [],
            'discoverable': discoverable,
            'views': 0,
            'likes': [],
            'tags': tags or [],
            'categories': self._detect_channel_categories(name, description),
        }
        
        if USE_MONGODB:
            self.channels_col.insert_one(channel)
        else:
            self.channels[channel['id']] = channel
        
        return channel
    
    def _detect_channel_categories(self, name: str, description: str) -> list:
        text = f"{name} {description}".lower()
        detected = []
        for cat, data in self.INTEREST_CATEGORIES.items():
            for kw in data['keywords']:
                if kw.lower() in text:
                    if cat not in detected:
                        detected.append(cat)
                    break
        return detected
    
    def get_channel(self, channel_id: str) -> Optional[dict]:
        if USE_MONGODB:
            return self.channels_col.find_one({'id': channel_id}, {'_id': 0})
        else:
            return self.channels.get(channel_id)
    
    def channel_exists(self, channel_id: str) -> bool:
        if USE_MONGODB:
            return self.channels_col.count_documents({'id': channel_id}) > 0
        else:
            return channel_id in self.channels
    
    def channel_name_exists(self, name: str) -> bool:
        if USE_MONGODB:
            return self.channels_col.count_documents({'name': {'$regex': f'^{name}$', '$options': 'i'}}) > 0
        else:
            return any(c['name'].lower() == name.lower() for c in self.channels.values())
    
    def get_all_channels(self) -> List[dict]:
        if USE_MONGODB:
            return list(self.channels_col.find({}, {'_id': 0}))
        else:
            return list(self.channels.values())
    
    def get_user_channels(self, username: str) -> List[dict]:
        if USE_MONGODB:
            return list(self.channels_col.find({'owner': username}, {'_id': 0}))
        else:
            return [c for c in self.channels.values() if c['owner'] == username]
    
    def get_subscribed_channels(self, username: str) -> List[dict]:
        if USE_MONGODB:
            return list(self.channels_col.find(
                {'subscribers': username, 'owner': {'$ne': username}},
                {'_id': 0}
            ))
        else:
            return [c for c in self.channels.values() 
                    if username in c.get('subscribers', []) and c['owner'] != username]
    
    def subscribe_to_channel(self, channel_id: str, username: str, role: str = None) -> bool:
        if USE_MONGODB:
            result = self.channels_col.update_one(
                {'id': channel_id},
                {
                    '$addToSet': {'subscribers': username},
                    '$set': {f'members.{username}': role or self.ROLE_VIEWER}
                }
            )
            return result.modified_count > 0
        else:
            if channel_id in self.channels:
                ch = self.channels[channel_id]
                if username not in ch['subscribers']:
                    ch['subscribers'].append(username)
                if 'members' not in ch:
                    ch['members'] = {ch['owner']: self.ROLE_ADMIN}
                if username not in ch['members']:
                    ch['members'][username] = role or self.ROLE_VIEWER
                return True
            return False
    
    def unsubscribe_from_channel(self, channel_id: str, username: str) -> bool:
        channel = self.get_channel(channel_id)
        if not channel or channel['owner'] == username:
            return False
        
        if USE_MONGODB:
            result = self.channels_col.update_one(
                {'id': channel_id},
                {
                    '$pull': {'subscribers': username},
                    '$unset': {f'members.{username}': ''}
                }
            )
            return result.modified_count > 0
        else:
            if channel_id in self.channels:
                ch = self.channels[channel_id]
                if username in ch['subscribers']:
                    ch['subscribers'].remove(username)
                if username in ch.get('members', {}):
                    del ch['members'][username]
                return True
            return False
    
    def get_member_role(self, channel_id: str, username: str) -> Optional[str]:
        channel = self.get_channel(channel_id)
        if not channel:
            return None
        if username == channel['owner']:
            return self.ROLE_ADMIN
        return channel.get('members', {}).get(username)
    
    def get_user_channel_role(self, channel_id: str, username: str) -> str:
        return self.get_member_role(channel_id, username)
    
    def can_post_in_channel(self, channel_id: str, username: str) -> bool:
        role = self.get_member_role(channel_id, username)
        return role in [self.ROLE_ADMIN, self.ROLE_MODERATOR]
    
    def can_manage_channel(self, channel_id: str, username: str) -> bool:
        return self.get_member_role(channel_id, username) == self.ROLE_ADMIN
    
    def set_channel_discoverable(self, channel_id: str, discoverable: bool) -> bool:
        if USE_MONGODB:
            result = self.channels_col.update_one(
                {'id': channel_id},
                {'$set': {'discoverable': discoverable}}
            )
            return result.modified_count > 0
        else:
            if channel_id in self.channels:
                self.channels[channel_id]['discoverable'] = discoverable
                return True
            return False
    
    def increment_channel_views(self, channel_id: str, username: str = None):
        if USE_MONGODB:
            self.channels_col.update_one(
                {'id': channel_id},
                {'$inc': {'views': 1}}
            )
        else:
            if channel_id in self.channels:
                self.channels[channel_id]['views'] = self.channels[channel_id].get('views', 0) + 1
    
    def like_channel(self, channel_id: str, username: str) -> dict:
        channel = self.get_channel(channel_id)
        if not channel:
            return {'success': False, 'error': 'Not found'}
        
        if username in channel.get('likes', []):
            return {'success': False, 'error': 'Already liked', 'likes': len(channel.get('likes', []))}
        
        if USE_MONGODB:
            self.channels_col.update_one({'id': channel_id}, {'$addToSet': {'likes': username}})
        else:
            if 'likes' not in self.channels[channel_id]:
                self.channels[channel_id]['likes'] = []
            self.channels[channel_id]['likes'].append(username)
        
        return {'success': True, 'likes': len(channel.get('likes', [])) + 1}
    
    def unlike_channel(self, channel_id: str, username: str) -> dict:
        channel = self.get_channel(channel_id)
        if not channel:
            return {'success': False, 'error': 'Not found'}
        
        if USE_MONGODB:
            self.channels_col.update_one({'id': channel_id}, {'$pull': {'likes': username}})
        else:
            if username in self.channels[channel_id].get('likes', []):
                self.channels[channel_id]['likes'].remove(username)
        
        return {'success': True, 'likes': len(channel.get('likes', [])) - 1}
    
    def has_liked_channel(self, channel_id: str, username: str) -> bool:
        channel = self.get_channel(channel_id)
        return channel and username in channel.get('likes', [])
    
    def get_discoverable_channels(self, exclude_user: str = None, limit: int = 50) -> List[dict]:
        if USE_MONGODB:
            query = {'discoverable': True}
            if exclude_user:
                query['owner'] = {'$ne': exclude_user}
                query['subscribers'] = {'$ne': exclude_user}
            return list(self.channels_col.find(query, {'_id': 0}).limit(limit))
        else:
            channels = []
            for ch in self.channels.values():
                if not ch.get('discoverable', True):
                    continue
                if exclude_user and (ch['owner'] == exclude_user or exclude_user in ch.get('subscribers', [])):
                    continue
                channels.append(ch)
            return channels[:limit]
    
    def search_channels(self, query: str, discoverable_only: bool = True, limit: int = 20) -> List[dict]:
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.lower().strip()
        
        if USE_MONGODB:
            filter_q = {'name': {'$regex': query, '$options': 'i'}}
            if discoverable_only:
                filter_q['discoverable'] = True
            return list(self.channels_col.find(filter_q, {'_id': 0}).limit(limit))
        else:
            results = []
            for ch in self.channels.values():
                if discoverable_only and not ch.get('discoverable', True):
                    continue
                if query in ch['name'].lower() or query in (ch.get('description') or '').lower():
                    results.append(ch)
            return results[:limit]
    
    def get_trending_channels(self, period: str = 'daily', sort_by: str = 'likes', limit: int = 20) -> List[dict]:
        channels = self.get_discoverable_channels(limit=100)
        # Sort by likes count
        channels.sort(key=lambda x: len(x.get('likes', [])), reverse=True)
        return channels[:limit]
    
    def get_discover_channels_rotated(self, username: str = None) -> dict:
        channels = self.get_discoverable_channels(exclude_user=username, limit=50)
        return {
            'trending': channels[:10],
            'most_liked': sorted(channels, key=lambda x: len(x.get('likes', [])), reverse=True)[:10],
            'most_viewed': sorted(channels, key=lambda x: x.get('views', 0), reverse=True)[:10],
            'new': sorted(channels, key=lambda x: x.get('created', ''), reverse=True)[:10],
            'all': channels
        }
    
    def get_channel_members_with_roles(self, channel_id: str) -> List[dict]:
        channel = self.get_channel(channel_id)
        if not channel:
            return []
        
        return [
            {
                'username': u,
                'role': self.get_member_role(channel_id, u),
                'is_owner': u == channel['owner']
            }
            for u in channel.get('subscribers', [])
        ]
    
    def set_member_role(self, channel_id: str, username: str, role: str, by_user: str) -> bool:
        channel = self.get_channel(channel_id)
        if not channel or channel['owner'] == username:
            return False
        if self.get_member_role(channel_id, by_user) != self.ROLE_ADMIN:
            return False
        
        if USE_MONGODB:
            result = self.channels_col.update_one(
                {'id': channel_id},
                {'$set': {f'members.{username}': role}}
            )
            return result.modified_count > 0
        else:
            if channel_id in self.channels:
                self.channels[channel_id]['members'][username] = role
                return True
            return False
    
    # ==========================================
    # CHANNEL POST METHODS
    # ==========================================
    
    def create_post(self, channel_id: str, author: str, content: str,
                    linked_post: Optional[str] = None) -> dict:
        post = {
            'id': self.generate_id(),
            'channel_id': channel_id,
            'author': author,
            'content': content,
            'timestamp': self.now(),
            'linked_post': linked_post,
            'reactions': {},
            'comments': [],
            'likes': []
        }
        
        if USE_MONGODB:
            self.posts_col.insert_one(post)
            self.channels_col.update_one(
                {'id': channel_id},
                {'$push': {'posts': post['id']}}
            )
        else:
            self.channel_posts[post['id']] = post
            if channel_id in self.channels:
                self.channels[channel_id]['posts'].append(post['id'])
        
        return post
    
    def get_post(self, post_id: str) -> Optional[dict]:
        if USE_MONGODB:
            return self.posts_col.find_one({'id': post_id}, {'_id': 0})
        else:
            return self.channel_posts.get(post_id)
    
    def get_channel_posts(self, channel_id: str) -> List[dict]:
        if USE_MONGODB:
            posts = list(self.posts_col.find({'channel_id': channel_id}, {'_id': 0}))
            return sorted(posts, key=lambda x: x['timestamp'], reverse=True)
        else:
            channel = self.get_channel(channel_id)
            if not channel:
                return []
            posts = [self.channel_posts[pid] for pid in channel.get('posts', []) if pid in self.channel_posts]
            return sorted(posts, key=lambda x: x['timestamp'], reverse=True)
    
    def toggle_like(self, post_id: str, username: str) -> Optional[dict]:
        post = self.get_post(post_id)
        if not post:
            return None
        
        if username in post['likes']:
            if USE_MONGODB:
                self.posts_col.update_one({'id': post_id}, {'$pull': {'likes': username}})
            else:
                self.channel_posts[post_id]['likes'].remove(username)
        else:
            if USE_MONGODB:
                self.posts_col.update_one({'id': post_id}, {'$addToSet': {'likes': username}})
            else:
                self.channel_posts[post_id]['likes'].append(username)
        
        return self.get_post(post_id)
    
    def toggle_reaction(self, post_id: str, emoji: str, username: str) -> Optional[dict]:
        post = self.get_post(post_id)
        if not post:
            return None
        
        if USE_MONGODB:
            if username in post.get('reactions', {}).get(emoji, []):
                self.posts_col.update_one({'id': post_id}, {'$pull': {f'reactions.{emoji}': username}})
            else:
                self.posts_col.update_one({'id': post_id}, {'$addToSet': {f'reactions.{emoji}': username}})
        else:
            if emoji not in self.channel_posts[post_id]['reactions']:
                self.channel_posts[post_id]['reactions'][emoji] = []
            if username in self.channel_posts[post_id]['reactions'][emoji]:
                self.channel_posts[post_id]['reactions'][emoji].remove(username)
            else:
                self.channel_posts[post_id]['reactions'][emoji].append(username)
        
        return self.get_post(post_id)
    
    def add_comment(self, post_id: str, author: str, content: str) -> Optional[dict]:
        comment = {
            'id': self.generate_id(),
            'author': author,
            'content': content,
            'timestamp': self.now()
        }
        
        if USE_MONGODB:
            result = self.posts_col.update_one(
                {'id': post_id},
                {'$push': {'comments': comment}}
            )
            if result.modified_count > 0:
                return comment
            return None
        else:
            if post_id in self.channel_posts:
                self.channel_posts[post_id]['comments'].append(comment)
                return comment
            return None


# Global store instance
store = DataStore()

if USE_MONGODB:
    print("🗄️ Using MongoDB for persistent storage")
else:
    print("⚠️ Using in-memory storage (data will be lost on restart)")
