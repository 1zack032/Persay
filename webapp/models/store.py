"""
💾 Data Store - MongoDB Backend (Optimized)
With performance monitoring for bottleneck detection.
"""

import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps


def timed_db_op(func):
    """Decorator to track database operation timing"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            
            # Log slow operations
            if duration_ms > 100:
                print(f"🐢 DB SLOW: {func.__name__} took {duration_ms:.0f}ms", flush=True)
            
            # Record in performance monitor
            try:
                from webapp.core.performance_monitor import perf
                perf.record(f"db.{func.__name__}", duration_ms)
            except:
                pass
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            print(f"❌ DB ERROR: {func.__name__} failed after {duration_ms:.0f}ms: {e}", flush=True)
            raise
    return wrapper

# MongoDB connection - LAZY initialization
USE_MONGODB = False
db = None
client = None
_mongo_initialized = False

def _connect_mongodb():
    """Connect to MongoDB - called lazily on first use"""
    global USE_MONGODB, db, client, _mongo_initialized
    
    if _mongo_initialized:
        return USE_MONGODB
    
    _mongo_initialized = True
    
    try:
        from pymongo import MongoClient
        
        uri = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI')
        if not uri:
            print("⚠️ No MONGODB_URI", flush=True)
            return False
        
        # Very short timeouts to prevent worker hangs
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
            maxPoolSize=5,
            minPoolSize=0,
            retryWrites=True,
            w=1,
            appName='Menza'
        )
        
        # Quick ping
        client.admin.command('ping')
        db = client['menza']
        USE_MONGODB = True
        print("✅ MongoDB OK", flush=True)
        return True
        
    except Exception as e:
        print(f"⚠️ MongoDB: {str(e)[:40]}", flush=True)
        USE_MONGODB = False
        return False


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
        # In-memory cache
        self._username_cache = None
        self._username_cache_time = 0
        self._cache_ttl = 60
        self._bots_initialized = False
        self._db_initialized = False
        
        # Start with in-memory
        self.users: Dict[str, dict] = {}
        self.messages: Dict[str, List[dict]] = {}
        self.groups: Dict[str, dict] = {}
        self.channels: Dict[str, dict] = {}
        self.channel_posts: Dict[str, dict] = {}
        self.shared_notes: Dict[str, dict] = {}
        self.chat_settings: Dict[str, dict] = {}
        self.bots: Dict[str, dict] = {}
        self.online_users: Dict[str, str] = {}
    
    def _ensure_db(self):
        """Lazy DB initialization - called on first DB operation"""
        if self._db_initialized:
            return
        self._db_initialized = True
        
        # Try MongoDB connection
        _connect_mongodb()
        
        if USE_MONGODB:
            self.users_col = db['users']
            self.messages_col = db['messages']
            self.groups_col = db['groups']
            self.channels_col = db['channels']
            self.posts_col = db['posts']
            self.notes_col = db['shared_notes']
            self.settings_col = db['chat_settings']
            self.bots_col = db['bots']
            print("✅ DB ready", flush=True)
    
    
    def _ensure_bots_initialized(self):
        """Lazy bot initialization - called on first bot access"""
        if self._bots_initialized:
            return
        self._bots_initialized = True
        try:
            self._init_verified_bots()
        except Exception as e:
            print(f"⚠️ Bot init error (non-fatal): {e}", flush=True)
    
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
        self._ensure_db()
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
        
        # Invalidate username cache
        self.invalidate_username_cache()
        
        return user
    
    @timed_db_op
    def get_user(self, username: str) -> Optional[dict]:
        self._ensure_db()
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
    
    def update_user_preferences(self, username: str, prefs: dict) -> bool:
        """Update user's premium preferences (theme, font, message style)"""
        if USE_MONGODB:
            # Single update with dot notation for nested fields - efficient
            update_ops = {f'preferences.{key}': value for key, value in prefs.items()}
            result = self.users_col.update_one(
                {'username': username},
                {'$set': update_ops}
            )
            return result.matched_count > 0
        else:
            if username not in self.users:
                return False
            if 'preferences' not in self.users[username]:
                self.users[username]['preferences'] = {}
            self.users[username]['preferences'].update(prefs)
            return True
    
    def get_user_preferences(self, username: str) -> dict:
        """Get user's premium preferences"""
        user = self.get_user(username)
        if not user:
            return {}
        return user.get('preferences', {})
    
    @timed_db_op
    def user_exists(self, username: str) -> bool:
        if USE_MONGODB:
            # Use find_one with projection - MUCH faster than count_documents
            return self.users_col.find_one({'username': username}, {'_id': 1}) is not None
        else:
            return username in self.users
    
    def get_all_usernames(self) -> List[str]:
        """Get all usernames with caching for performance"""
        import time
        current_time = time.time()
        
        # Return cached if valid
        if self._username_cache and (current_time - self._username_cache_time) < self._cache_ttl:
            return self._username_cache
        
        if USE_MONGODB:
            usernames = [u['username'] for u in self.users_col.find({}, {'username': 1, '_id': 0})]
        else:
            usernames = list(self.users.keys())
        
        # Update cache
        self._username_cache = usernames
        self._username_cache_time = current_time
        return usernames
    
    def invalidate_username_cache(self):
        """Call this when users are added/deleted"""
        self._username_cache = None
    
    @timed_db_op
    def search_users(self, query: str, exclude_username: str, limit: int = 20) -> List[dict]:
        """Search users by username - optimized single query"""
        if USE_MONGODB:
            # Use $and to combine conditions on same field
            users = list(self.users_col.find(
                {
                    '$and': [
                        {'username': {'$regex': query, '$options': 'i'}},
                        {'username': {'$ne': exclude_username}}
                    ]
                },
                {'username': 1, 'display_name': 1, 'profile_image': 1, '_id': 0}
            ).limit(limit))
            
            return [{
                'username': u['username'],
                'display_name': u.get('display_name') or u['username'],
                'profile_picture': u.get('profile_image')
            } for u in users]
        else:
            # In-memory fallback
            results = []
            for username, user_data in self.users.items():
                if username != exclude_username and query in username.lower():
                    results.append({
                        'username': username,
                        'display_name': user_data.get('display_name') or username,
                        'profile_picture': user_data.get('profile_image')
                    })
                    if len(results) >= limit:
                        break
            return results
    
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
    
    def find_users_by_contacts_batch(self, contact_type: str, values: List[str]) -> Dict[str, str]:
        """BATCH: Find users by multiple contacts in ONE query - returns {value: username}"""
        if not values:
            return {}
        
        values = [v for v in values if v]  # Filter out None/empty
        if not values:
            return {}
        
        result = {}
        if USE_MONGODB:
            query = {contact_type: {'$in': values}, f'find_by_{contact_type}': True}
            users = self.users_col.find(query, {'username': 1, contact_type: 1})
            for user in users:
                result[user[contact_type]] = user['username']
        else:
            for username, user in self.users.items():
                val = user.get(contact_type)
                if val in values and user.get(f'find_by_{contact_type}'):
                    result[val] = username
        return result
    
    # ==========================================
    # ONLINE STATUS (Always in-memory) - OPTIMIZED
    # ==========================================
    
    def set_user_online(self, socket_id: str, username: str):
        self.online_users[socket_id] = username
        # Maintain reverse index for O(1) lookups
        if not hasattr(self, '_user_to_sids'):
            self._user_to_sids = {}
        if username not in self._user_to_sids:
            self._user_to_sids[username] = set()
        self._user_to_sids[username].add(socket_id)
    
    def set_user_offline(self, socket_id: str) -> Optional[str]:
        username = self.online_users.pop(socket_id, None)
        # Update reverse index
        if username and hasattr(self, '_user_to_sids') and username in self._user_to_sids:
            self._user_to_sids[username].discard(socket_id)
            if not self._user_to_sids[username]:
                del self._user_to_sids[username]
        return username
    
    def get_online_users(self) -> List[str]:
        if hasattr(self, '_user_to_sids'):
            return list(self._user_to_sids.keys())
        return list(set(self.online_users.values()))
    
    def is_user_online(self, username: str) -> bool:
        if hasattr(self, '_user_to_sids'):
            return username in self._user_to_sids
        return username in self.online_users.values()
    
    def get_user_sids(self, username: str) -> List[str]:
        """Get all socket IDs for a user - O(1) lookup"""
        if hasattr(self, '_user_to_sids'):
            return list(self._user_to_sids.get(username, set()))
        return [sid for sid, user in self.online_users.items() if user == username]
    
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
    
    @timed_db_op
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
    
    @timed_db_op
    def get_chat_partners(self, username: str) -> List[dict]:
        """Get chat partners - OPTIMIZED: batch user lookups to avoid N+1"""
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
            
            # Extract partner usernames first (avoid N+1 query)
            partner_usernames = set()
            room_data = {}
            for room in rooms:
                room_id = room['_id']
                if room_id.startswith('group_'):
                    continue
                users = room_id.split('_')
                if len(users) == 2:
                    other = users[0] if users[1] == username else users[1]
                    partner_usernames.add(other)
                    room_data[other] = room
            
            # Batch fetch all user data in ONE query
            if partner_usernames:
                users_data = {
                    u['username']: u for u in 
                    self.users_col.find({'username': {'$in': list(partner_usernames)}}, 
                                       {'username': 1, 'display_name': 1, '_id': 0})
                }
            else:
                users_data = {}
            
            # Build result
            partners = []
            for other, room in room_data.items():
                user_data = users_data.get(other, {})
                partners.append({
                    'username': other,
                    'display_name': user_data.get('display_name', other),
                    'last_message_time': room['last_message_time'],
                    'message_count': room['message_count']
                })
            
            return sorted(partners, key=lambda x: x['last_message_time'] or '', reverse=True)
        else:
            # In-memory: collect usernames first, then batch lookup
            partner_data = {}
            for room_id, messages in self.messages.items():
                if room_id.startswith('group_'):
                    continue
                users = room_id.split('_')
                if len(users) == 2 and username in users and messages:
                    other = users[0] if users[1] == username else users[1]
                    partner_data[other] = {
                        'last_message_time': messages[-1].get('timestamp'),
                        'message_count': len(messages)
                    }
            
            # Build result with user data
            partners = []
            for other, data in partner_data.items():
                user = self.users.get(other, {})
                partners.append({
                    'username': other,
                    'display_name': user.get('display_name', other),
                    'last_message_time': data['last_message_time'],
                    'message_count': data['message_count']
                })
            return sorted(partners, key=lambda x: x['last_message_time'] or '', reverse=True)
    
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
    
    def add_pending_member(self, note_id: str, username: str) -> bool:
        """Add a user to the pending members list for a shared note"""
        if USE_MONGODB:
            result = self.notes_col.update_one(
                {'id': note_id},
                {'$addToSet': {'pending_members': username}}
            )
            return result.modified_count > 0 or result.matched_count > 0
        else:
            if note_id not in self.shared_notes:
                return False
            if 'pending_members' not in self.shared_notes[note_id]:
                self.shared_notes[note_id]['pending_members'] = []
            if username not in self.shared_notes[note_id]['pending_members']:
                self.shared_notes[note_id]['pending_members'].append(username)
            return True
    
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
    
    @timed_db_op
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
    
    @timed_db_op
    def get_user_channels(self, username: str) -> List[dict]:
        if USE_MONGODB:
            return list(self.channels_col.find({'owner': username}, {'_id': 0}))
        else:
            return [c for c in self.channels.values() if c['owner'] == username]
    
    @timed_db_op
    def get_subscribed_channels(self, username: str) -> List[dict]:
        if USE_MONGODB:
            return list(self.channels_col.find(
                {'subscribers': username, 'owner': {'$ne': username}},
                {'_id': 0}
            ))
        else:
            return [c for c in self.channels.values() 
                    if username in c.get('subscribers', []) and c['owner'] != username]
    
    @timed_db_op
    def get_all_user_channels(self, username: str) -> List[dict]:
        """Get all channels user owns OR is subscribed to - single query"""
        if USE_MONGODB:
            return list(self.channels_col.find(
                {'$or': [
                    {'owner': username},
                    {'subscribers': username}
                ]},
                {'_id': 0}
            ).limit(50))  # Limit for performance
        else:
            return [c for c in self.channels.values() 
                    if c['owner'] == username or username in c.get('subscribers', [])][:50]
    
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
        """Like a channel - OPTIMIZED: single atomic update"""
        if USE_MONGODB:
            # Atomic update: only add if not already liked
            result = self.channels_col.update_one(
                {'id': channel_id, 'likes': {'$ne': username}},
                {'$addToSet': {'likes': username}}
            )
            if result.matched_count == 0:
                # Either not found or already liked
                channel = self.channels_col.find_one({'id': channel_id}, {'likes': 1})
                if not channel:
                    return {'success': False, 'error': 'Not found'}
                return {'success': False, 'error': 'Already liked', 'likes': len(channel.get('likes', []))}
            return {'success': True, 'likes': result.modified_count}
        else:
            if channel_id not in self.channels:
                return {'success': False, 'error': 'Not found'}
            ch = self.channels[channel_id]
            if 'likes' not in ch:
                ch['likes'] = []
            if username in ch['likes']:
                return {'success': False, 'error': 'Already liked', 'likes': len(ch['likes'])}
            ch['likes'].append(username)
            return {'success': True, 'likes': len(ch['likes'])}
    
    def unlike_channel(self, channel_id: str, username: str) -> dict:
        """Unlike a channel - OPTIMIZED: single atomic update"""
        if USE_MONGODB:
            result = self.channels_col.update_one(
                {'id': channel_id},
                {'$pull': {'likes': username}}
            )
            if result.matched_count == 0:
                return {'success': False, 'error': 'Not found'}
            return {'success': True}
        else:
            if channel_id not in self.channels:
                return {'success': False, 'error': 'Not found'}
            ch = self.channels[channel_id]
            if username in ch.get('likes', []):
                ch['likes'].remove(username)
            return {'success': True, 'likes': len(ch.get('likes', []))}
    
    def has_liked_channel(self, channel_id: str, username: str) -> bool:
        """Check if user liked channel - OPTIMIZED: projection query"""
        if USE_MONGODB:
            result = self.channels_col.find_one(
                {'id': channel_id, 'likes': username},
                {'_id': 1}
            )
            return result is not None
        else:
            ch = self.channels.get(channel_id)
            return ch and username in ch.get('likes', [])
    
    def get_liked_channels_batch(self, channel_ids: List[str], username: str) -> set:
        """Get which channels user has liked - BATCH query for N+1 prevention"""
        if not channel_ids:
            return set()
        if USE_MONGODB:
            liked = self.channels_col.find(
                {'id': {'$in': channel_ids}, 'likes': username},
                {'id': 1}
            )
            return {ch['id'] for ch in liked}
        else:
            return {cid for cid in channel_ids if username in self.channels.get(cid, {}).get('likes', [])}
    
    @timed_db_op
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
    
    @timed_db_op
    def get_discover_channels_rotated(self, username: str = None) -> dict:
        channels = self.get_discoverable_channels(exclude_user=username, limit=50)
        return {
            'trending': channels[:10],
            'most_liked': sorted(channels, key=lambda x: len(x.get('likes', [])), reverse=True)[:10],
            'most_viewed': sorted(channels, key=lambda x: x.get('views', 0), reverse=True)[:10],
            'new': sorted(channels, key=lambda x: x.get('created', ''), reverse=True)[:10],
            'all': channels
        }
    
    def get_all_categories(self) -> List[dict]:
        """Get all available interest categories"""
        return [
            {'id': cat_id, 'name': cat_id.title(), **data}
            for cat_id, data in self.INTEREST_CATEGORIES.items()
        ]
    
    def get_channels_by_category(self, category: str, limit: int = 20) -> List[dict]:
        """Get discoverable channels that match a category"""
        channels = self.get_discoverable_channels(limit=100)
        # Filter by category
        matching = [c for c in channels if category.lower() in c.get('categories', [])]
        return matching[:limit]
    
    def search_channels_by_interest(self, query: str, limit: int = 20) -> dict:
        """Search channels by interest/keyword - OPTIMIZED: use MongoDB queries when available"""
        query_lower = query.lower().strip()
        
        if not query_lower:
            return {'exact_matches': [], 'category_matches': [], 'suggestions': [], 'related_categories': []}
        
        # Find matching categories first (fast, in-memory)
        related_categories = [
            {'id': cat_id, 'name': cat_id.title(), **cat_data}
            for cat_id, cat_data in self.INTEREST_CATEGORIES.items()
            if query_lower in cat_id or any(query_lower in kw for kw in cat_data['keywords'])
        ]
        
        if USE_MONGODB:
            # Use MongoDB text search for efficiency
            exact_matches = list(self.channels_col.find(
                {'discoverable': True, 'name': {'$regex': query_lower, '$options': 'i'}},
                {'_id': 0}
            ).limit(limit))
            
            category_matches = list(self.channels_col.find(
                {'discoverable': True, 'categories': {'$regex': query_lower, '$options': 'i'},
                 'name': {'$not': {'$regex': query_lower, '$options': 'i'}}},
                {'_id': 0}
            ).limit(limit))
            
            suggestions = list(self.channels_col.find(
                {'discoverable': True, 'description': {'$regex': query_lower, '$options': 'i'},
                 'name': {'$not': {'$regex': query_lower, '$options': 'i'}},
                 'categories': {'$not': {'$regex': query_lower, '$options': 'i'}}},
                {'_id': 0}
            ).limit(limit))
        else:
            # In-memory fallback with single pass
            exact_matches, category_matches, suggestions = [], [], []
            for ch in self.channels.values():
                if not ch.get('discoverable', True):
                    continue
                name_lower = ch['name'].lower()
                if query_lower in name_lower:
                    exact_matches.append(ch)
                elif any(query_lower in cat for cat in ch.get('categories', [])):
                    category_matches.append(ch)
                elif query_lower in ch.get('description', '').lower():
                    suggestions.append(ch)
                if len(exact_matches) >= limit and len(category_matches) >= limit:
                    break
        
        return {
            'exact_matches': exact_matches[:limit],
            'category_matches': category_matches[:limit],
            'suggestions': suggestions[:limit],
            'related_categories': related_categories
        }
    
    def get_channel_members_with_roles(self, channel_id: str) -> List[dict]:
        """Get channel members - OPTIMIZED: use already-fetched channel data"""
        channel = self.get_channel(channel_id)
        if not channel:
            return []
        
        owner = channel['owner']
        members_dict = channel.get('members', {})
        
        # Build result directly from channel data (no extra queries)
        return [
            {
                'username': u,
                'role': self.ROLE_ADMIN if u == owner else members_dict.get(u, self.ROLE_VIEWER),
                'is_owner': u == owner
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
    
    # ==========================================
    # BOT METHODS
    # ==========================================
    
    # Bot categories
    BOT_CATEGORIES = {
        'trading': {'name': 'Trading & Finance', 'icon': '📈'},
        'crypto': {'name': 'Cryptocurrency', 'icon': '₿'},
        'news': {'name': 'News & Updates', 'icon': '📰'},
        'utilities': {'name': 'Utilities', 'icon': '🔧'},
        'entertainment': {'name': 'Entertainment', 'icon': '🎮'},
        'productivity': {'name': 'Productivity', 'icon': '📊'},
        'moderation': {'name': 'Moderation', 'icon': '🛡️'},
    }
    
    # Bot status constants
    BOT_STATUS_PENDING = 'pending'
    BOT_STATUS_APPROVED = 'approved'
    BOT_STATUS_REJECTED = 'rejected'
    BOT_STATUS_SUSPENDED = 'suspended'
    
    def _init_verified_bots(self):
        """Initialize pre-verified official bots - OPTIMIZED with batch check"""
        now = self.now()  # Single timestamp for all bots
        
        # Get all existing bot IDs in a single query
        if USE_MONGODB:
            existing_ids = set(b['bot_id'] for b in self.bots_col.find({}, {'bot_id': 1}))
        else:
            existing_ids = set(self.bots.keys())
        
        verified_bots = [
            # FREE BOTS
            {'bot_id': 'coingecko_bot', 'name': 'CoinGecko Price Bot', 'username': '@coingecko',
             'description': 'Get real-time cryptocurrency prices.', 'avatar': '🦎', 'category': 'crypto',
             'developer': 'Menza Official', 'website': 'https://coingecko.com', 'verified': True, 'official': True,
             'free': True, 'status': self.BOT_STATUS_APPROVED, 'api_type': 'coingecko', 'created_at': now,
             'commands': [{'command': '/price', 'description': 'Get price', 'usage': '/price BTC'},
                         {'command': '/top', 'description': 'Top coins', 'usage': '/top 10'}],
             'permissions': ['commands.receive', 'messages.send'], 'installs': 0, 'rating': 4.8,
             'reviews': [], 'reports': [], 'groups': [], 'channels': []},
            {'bot_id': 'phanes_bot', 'name': 'Phanes Trading Bot', 'username': '@phanes',
             'description': 'Advanced trading signals and portfolio management.', 'avatar': '🔮', 'category': 'trading',
             'developer': 'Menza Official', 'website': 'https://phanes.trade', 'verified': True, 'official': True,
             'free': True, 'status': self.BOT_STATUS_APPROVED, 'api_type': 'phanes', 'created_at': now,
             'commands': [{'command': '/trade', 'description': 'Execute trade', 'usage': '/trade BTC buy 0.01'},
                         {'command': '/balance', 'description': 'Check balance', 'usage': '/balance'}],
             'permissions': ['commands.receive', 'messages.send'], 'installs': 0, 'rating': 4.9,
             'reviews': [], 'reports': [], 'groups': [], 'channels': []},
            # PREMIUM BOTS
            {'bot_id': 'news_bot', 'name': 'Crypto News Bot', 'username': '@cryptonews',
             'description': 'Latest cryptocurrency news.', 'avatar': '📰', 'category': 'news',
             'developer': 'Menza Official', 'verified': True, 'official': True, 'free': False,
             'status': self.BOT_STATUS_APPROVED, 'api_type': 'internal', 'created_at': now,
             'commands': [{'command': '/news', 'description': 'Latest news', 'usage': '/news'}],
             'permissions': ['commands.receive', 'messages.send'], 'installs': 0, 'rating': 4.5,
             'reviews': [], 'reports': [], 'groups': [], 'channels': []},
            {'bot_id': 'trading_signals_bot', 'name': 'Trading Signals Pro', 'username': '@signals',
             'description': 'Professional trading signals.', 'avatar': '📊', 'category': 'trading',
             'developer': 'Menza Official', 'verified': True, 'official': True, 'free': False,
             'status': self.BOT_STATUS_APPROVED, 'api_type': 'internal', 'created_at': now,
             'commands': [{'command': '/signal', 'description': 'Get signal', 'usage': '/signal'}],
             'permissions': ['commands.receive', 'messages.send'], 'installs': 0, 'rating': 4.6,
             'reviews': [], 'reports': [], 'groups': [], 'channels': []},
            {'bot_id': 'mod_bot', 'name': 'Moderation Bot', 'username': '@modbot',
             'description': 'Automated moderation for groups.', 'avatar': '🛡️', 'category': 'moderation',
             'developer': 'Menza Official', 'verified': True, 'official': True, 'free': False,
             'status': self.BOT_STATUS_APPROVED, 'api_type': 'internal', 'created_at': now,
             'commands': [{'command': '/warn', 'description': 'Warn user', 'usage': '/warn @user'}],
             'permissions': ['commands.receive', 'messages.send', 'members.manage'], 'installs': 0, 'rating': 4.7,
             'reviews': [], 'reports': [], 'groups': [], 'channels': []},
        ]
        
        # Batch insert new bots only
        new_bots = [b for b in verified_bots if b['bot_id'] not in existing_ids]
        if new_bots:
            if USE_MONGODB:
                self.bots_col.insert_many(new_bots)
            else:
                for bot in new_bots:
                    self.bots[bot['bot_id']] = bot
    
    def _save_bot(self, bot: dict):
        """Save a bot to storage"""
        if USE_MONGODB:
            self.bots_col.update_one(
                {'bot_id': bot['bot_id']},
                {'$set': bot},
                upsert=True
            )
        else:
            self.bots[bot['bot_id']] = bot
    
    def get_bot(self, bot_id: str) -> Optional[dict]:
        """Get a bot by ID"""
        self._ensure_bots_initialized()
        if USE_MONGODB:
            return self.bots_col.find_one({'bot_id': bot_id}, {'_id': 0})
        else:
            return self.bots.get(bot_id)
    
    def get_bot_by_username(self, username: str) -> Optional[dict]:
        """Get a bot by username"""
        if USE_MONGODB:
            return self.bots_col.find_one({'username': username}, {'_id': 0})
        else:
            for bot in self.bots.values():
                if bot.get('username') == username:
                    return bot
            return None
    
    def get_all_bots(self, status: str = None, category: str = None) -> List[dict]:
        """Get all bots, optionally filtered"""
        self._ensure_bots_initialized()
        if USE_MONGODB:
            query = {}
            if status:
                query['status'] = status
            if category:
                query['category'] = category
            return list(self.bots_col.find(query, {'_id': 0}))
        else:
            bots = list(self.bots.values())
            if status:
                bots = [b for b in bots if b.get('status') == status]
            if category:
                bots = [b for b in bots if b.get('category') == category]
            return bots
    
    def get_approved_bots(self, category: str = None) -> List[dict]:
        """Get all approved bots for the bot store"""
        return self.get_all_bots(status=self.BOT_STATUS_APPROVED, category=category)
    
    def get_featured_bots(self, limit: int = 6) -> List[dict]:
        """Get featured/popular bots"""
        bots = self.get_approved_bots()
        # Sort by installs and rating
        bots.sort(key=lambda x: (x.get('official', False), x.get('installs', 0), x.get('rating', 0)), reverse=True)
        return bots[:limit]
    
    def get_free_bots(self) -> List[dict]:
        """Get all free bots available to non-premium users"""
        bots = self.get_approved_bots()
        return [b for b in bots if b.get('free', False)]
    
    def get_premium_bots(self) -> List[dict]:
        """Get bots that require premium subscription"""
        bots = self.get_approved_bots()
        return [b for b in bots if not b.get('free', False)]
    
    def is_free_bot(self, bot_id: str) -> bool:
        """Check if a bot is free for all users"""
        bot = self.get_bot(bot_id)
        return bot and bot.get('free', False)
    
    def create_bot(self, data: dict, developer_username: str) -> dict:
        """Create a new bot (pending approval)"""
        bot_id = f"bot_{self.generate_id()}"
        api_key = secrets.token_hex(32)  # 64 character API key
        
        bot = {
            'bot_id': bot_id,
            'name': data.get('name', 'Unnamed Bot'),
            'username': data.get('username', f'@{bot_id}'),
            'description': data.get('description', ''),
            'avatar': data.get('avatar', '🤖'),
            'category': data.get('category', 'utilities'),
            'developer': developer_username,
            'developer_email': data.get('developer_email'),
            'website': data.get('website'),
            'privacy_policy': data.get('privacy_policy'),
            'terms_of_service': data.get('terms_of_service'),
            'verified': False,
            'official': False,
            'status': self.BOT_STATUS_PENDING,
            'commands': data.get('commands', []),
            'permissions': data.get('permissions', ['read_messages', 'send_messages']),
            'webhook_url': data.get('webhook_url'),
            'api_key': api_key,
            'api_type': 'webhook',
            'allowed_domains': data.get('allowed_domains', []),
            'created_at': self.now(),
            'installs': 0,
            'rating': 0,
            'reviews': [],
            'groups': [],  # Groups this bot is added to
            'channels': [],  # Channels this bot is added to
        }
        
        self._save_bot(bot)
        return bot
    
    def update_bot(self, bot_id: str, data: dict, by_user: str) -> bool:
        """Update bot settings (only by developer or admin)"""
        bot = self.get_bot(bot_id)
        if not bot:
            return False
        
        # Only developer can update
        if bot['developer'] != by_user:
            return False
        
        # Allowed fields to update
        allowed_fields = [
            'name', 'description', 'avatar', 'category', 'commands',
            'webhook_url', 'website', 'privacy_policy', 'terms_of_service'
        ]
        
        for field in allowed_fields:
            if field in data:
                bot[field] = data[field]
        
        bot['updated_at'] = self.now()
        self._save_bot(bot)
        return True
    
    def approve_bot(self, bot_id: str, by_admin: str) -> bool:
        """Approve a bot (admin only)"""
        bot = self.get_bot(bot_id)
        if not bot:
            return False
        
        bot['status'] = self.BOT_STATUS_APPROVED
        bot['approved_by'] = by_admin
        bot['approved_at'] = self.now()
        self._save_bot(bot)
        return True
    
    def reject_bot(self, bot_id: str, by_admin: str, reason: str = None) -> bool:
        """Reject a bot (admin only)"""
        bot = self.get_bot(bot_id)
        if not bot:
            return False
        
        bot['status'] = self.BOT_STATUS_REJECTED
        bot['rejected_by'] = by_admin
        bot['rejected_at'] = self.now()
        bot['rejection_reason'] = reason
        self._save_bot(bot)
        return True
    
    def suspend_bot(self, bot_id: str, by_admin: str, reason: str = None) -> bool:
        """Suspend a bot for policy violations"""
        bot = self.get_bot(bot_id)
        if not bot:
            return False
        
        bot['status'] = self.BOT_STATUS_SUSPENDED
        bot['suspended_by'] = by_admin
        bot['suspended_at'] = self.now()
        bot['suspension_reason'] = reason
        self._save_bot(bot)
        return True
    
    def add_bot_to_group(self, bot_id: str, group_id: str, added_by: str) -> bool:
        """Add a bot to a group"""
        bot = self.get_bot(bot_id)
        group = self.get_group(group_id)
        
        if not bot or not group:
            return False
        
        if bot['status'] != self.BOT_STATUS_APPROVED:
            return False
        
        # Check if user can add bots to this group (must be admin/owner)
        if added_by not in group.get('admins', []) and added_by != group.get('owner'):
            return False
        
        if group_id not in bot.get('groups', []):
            bot['groups'] = bot.get('groups', []) + [group_id]
            bot['installs'] = bot.get('installs', 0) + 1
            self._save_bot(bot)
        
        # Add bot to group's bot list
        if USE_MONGODB:
            self.groups_col.update_one(
                {'id': group_id},
                {'$addToSet': {'bots': bot_id}}
            )
        else:
            if 'bots' not in group:
                group['bots'] = []
            if bot_id not in group['bots']:
                group['bots'].append(bot_id)
        
        return True
    
    def remove_bot_from_group(self, bot_id: str, group_id: str, removed_by: str) -> bool:
        """Remove a bot from a group"""
        bot = self.get_bot(bot_id)
        group = self.get_group(group_id)
        
        if not bot or not group:
            return False
        
        if group_id in bot.get('groups', []):
            bot['groups'].remove(group_id)
            self._save_bot(bot)
        
        if USE_MONGODB:
            self.groups_col.update_one(
                {'id': group_id},
                {'$pull': {'bots': bot_id}}
            )
        else:
            if bot_id in group.get('bots', []):
                group['bots'].remove(bot_id)
        
        return True
    
    def add_bot_to_channel(self, bot_id: str, channel_id: str, added_by: str) -> bool:
        """Add a bot to a channel"""
        bot = self.get_bot(bot_id)
        channel = self.get_channel(channel_id)
        
        if not bot or not channel:
            return False
        
        if bot['status'] != self.BOT_STATUS_APPROVED:
            return False
        
        # Check if user can add bots (must be admin)
        if self.get_member_role(channel_id, added_by) != self.ROLE_ADMIN:
            return False
        
        if channel_id not in bot.get('channels', []):
            bot['channels'] = bot.get('channels', []) + [channel_id]
            bot['installs'] = bot.get('installs', 0) + 1
            self._save_bot(bot)
        
        if USE_MONGODB:
            self.channels_col.update_one(
                {'id': channel_id},
                {'$addToSet': {'bots': bot_id}}
            )
        else:
            if 'bots' not in channel:
                channel['bots'] = []
            if bot_id not in channel['bots']:
                channel['bots'].append(bot_id)
        
        return True
    
    def get_group_bots(self, group_id: str) -> List[dict]:
        """Get all bots in a group"""
        group = self.get_group(group_id)
        if not group:
            return []
        
        bot_ids = group.get('bots', [])
        return [self.get_bot(bid) for bid in bot_ids if self.get_bot(bid)]
    
    def get_channel_bots(self, channel_id: str) -> List[dict]:
        """Get all bots in a channel"""
        channel = self.get_channel(channel_id)
        if not channel:
            return []
        
        bot_ids = channel.get('bots', [])
        return [self.get_bot(bid) for bid in bot_ids if self.get_bot(bid)]
    
    def rate_bot(self, bot_id: str, username: str, rating: int, review: str = None) -> bool:
        """Rate a bot (1-5 stars)"""
        bot = self.get_bot(bot_id)
        if not bot or rating < 1 or rating > 5:
            return False
        
        review_data = {
            'username': username,
            'rating': rating,
            'review': review,
            'created_at': self.now()
        }
        
        reviews = bot.get('reviews', [])
        # Remove existing review from same user
        reviews = [r for r in reviews if r['username'] != username]
        reviews.append(review_data)
        
        # Calculate average rating
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        
        bot['reviews'] = reviews
        bot['rating'] = round(avg_rating, 1)
        self._save_bot(bot)
        return True
    
    def report_bot(self, bot_id: str, reporter: str, reason: str) -> bool:
        """Report a bot for policy violations"""
        bot = self.get_bot(bot_id)
        if not bot:
            return False
        
        reports = bot.get('reports', [])
        reports.append({
            'reporter': reporter,
            'reason': reason,
            'created_at': self.now()
        })
        
        bot['reports'] = reports
        self._save_bot(bot)
        return True
    
    def verify_bot_api_key(self, bot_id: str, api_key: str) -> bool:
        """Verify a bot's API key (legacy - use hashed version)"""
        bot = self.get_bot(bot_id)
        if not bot:
            return False
        return bot.get('api_key') == api_key
    
    def create_bot_secure(self, data: dict, developer_username: str, api_key_hash: str) -> dict:
        """
        Create a new bot with secure API key handling.
        The API key is hashed - raw key is never stored.
        """
        bot_id = f"bot_{self.generate_id()}"
        
        bot = {
            'bot_id': bot_id,
            'name': data.get('name', 'Unnamed Bot'),
            'username': data.get('username', f'@{bot_id}'),
            'description': data.get('description', ''),
            'avatar': data.get('avatar', '🤖'),
            'category': data.get('category', 'utilities'),
            'developer': developer_username,
            'developer_email': data.get('developer_email'),
            'website': data.get('website'),
            'privacy_policy': data.get('privacy_policy'),
            'terms_of_service': data.get('terms_of_service'),
            'verified': False,
            'official': False,
            'status': self.BOT_STATUS_PENDING,
            'commands': data.get('commands', []),
            'permissions': data.get('permissions', ['commands.receive', 'messages.send']),
            'webhook_url': data.get('webhook_url'),
            'api_key_hash': api_key_hash,  # Store hash, not raw key
            'api_type': 'webhook',
            'allowed_domains': data.get('allowed_domains', []),
            'created_at': self.now(),
            'version': data.get('version', '1.0.0'),
            'installs': 0,
            'rating': 0,
            'reviews': [],
            'reports': [],
            'groups': [],
            'channels': [],
            'version_history': [],
            'security_scan': data.get('security_scan', {}),
        }
        
        self._save_bot(bot)
        return bot
    
    def update_bot_api_key(self, bot_id: str, new_api_key_hash: str) -> bool:
        """Update a bot's API key hash"""
        bot = self.get_bot(bot_id)
        if not bot:
            return False
        
        bot['api_key_hash'] = new_api_key_hash
        bot['api_key_updated_at'] = self.now()
        self._save_bot(bot)
        return True
    
    def add_bot_version_history(self, bot_id: str, version_snapshot: dict) -> bool:
        """Add a version snapshot to bot's history"""
        bot = self.get_bot(bot_id)
        if not bot:
            return False
        
        history = bot.get('version_history', [])
        history.append(version_snapshot)
        
        # Keep only last 10 versions
        if len(history) > 10:
            history = history[-10:]
        
        bot['version_history'] = history
        self._save_bot(bot)
        return True
    
    def get_all_groups(self) -> List[dict]:
        """Get all groups"""
        if USE_MONGODB:
            return list(self.groups_col.find({}, {'_id': 0}))
        else:
            return list(self.groups.values())
    
    def get_user_admin_groups(self, username: str) -> List[dict]:
        """Get groups where user is admin/owner - OPTIMIZED: single query"""
        if USE_MONGODB:
            return list(self.groups_col.find(
                {'$or': [
                    {'owner': username},
                    {'admins': username}
                ]},
                {'_id': 0}
            ).limit(20))
        else:
            return [g for g in self.groups.values()
                    if g.get('owner') == username or username in g.get('admins', [])][:20]
    
    def get_user_admin_channels(self, username: str) -> List[dict]:
        """Get channels where user is admin - OPTIMIZED: single query"""
        if USE_MONGODB:
            return list(self.channels_col.find(
                {'$or': [
                    {'owner': username},
                    {f'members.{username}': self.ROLE_ADMIN}
                ]},
                {'_id': 0}
            ).limit(20))
        else:
            return [c for c in self.channels.values()
                    if c.get('owner') == username or 
                    c.get('members', {}).get(username) == self.ROLE_ADMIN][:20]
    
    def get_bots_by_developer(self, developer: str) -> List[dict]:
        """Get bots created by a specific developer - OPTIMIZED: direct query"""
        if USE_MONGODB:
            return list(self.bots_col.find({'developer': developer}, {'_id': 0}))
        else:
            return [b for b in self.bots.values() if b.get('developer') == developer]
    
    def get_bots_grouped_by_status(self) -> dict:
        """Get bots grouped by status - OPTIMIZED: single aggregation"""
        if USE_MONGODB:
            # Use aggregation to group in database
            pipeline = [
                {'$facet': {
                    'pending': [{'$match': {'status': self.BOT_STATUS_PENDING}}],
                    'approved': [{'$match': {'status': self.BOT_STATUS_APPROVED}}],
                    'rejected': [{'$match': {'status': self.BOT_STATUS_REJECTED}}],
                    'suspended': [{'$match': {'status': self.BOT_STATUS_SUSPENDED}}],
                    'reported': [{'$match': {'reports.0': {'$exists': True}}}],
                    'total': [{'$count': 'count'}]
                }}
            ]
            result = list(self.bots_col.aggregate(pipeline))
            if result:
                r = result[0]
                return {
                    'pending': [{k: v for k, v in b.items() if k != '_id'} for b in r.get('pending', [])],
                    'approved': [{k: v for k, v in b.items() if k != '_id'} for b in r.get('approved', [])],
                    'rejected': [{k: v for k, v in b.items() if k != '_id'} for b in r.get('rejected', [])],
                    'suspended': [{k: v for k, v in b.items() if k != '_id'} for b in r.get('suspended', [])],
                    'reported': [{k: v for k, v in b.items() if k != '_id'} for b in r.get('reported', [])],
                    'total': r.get('total', [{}])[0].get('count', 0)
                }
            return {'pending': [], 'approved': [], 'rejected': [], 'suspended': [], 'reported': [], 'total': 0}
        else:
            bots = list(self.bots.values())
            return {
                'pending': [b for b in bots if b.get('status') == self.BOT_STATUS_PENDING],
                'approved': [b for b in bots if b.get('status') == self.BOT_STATUS_APPROVED],
                'rejected': [b for b in bots if b.get('status') == self.BOT_STATUS_REJECTED],
                'suspended': [b for b in bots if b.get('status') == self.BOT_STATUS_SUSPENDED],
                'reported': [b for b in bots if len(b.get('reports', [])) > 0],
                'total': len(bots)
            }
    
    def set_user_premium(self, username: str, is_premium: bool) -> bool:
        """Set user's premium status"""
        user = self.get_user(username)
        if not user:
            return False
        
        user['premium'] = is_premium
        user['premium_updated_at'] = self.now()
        
        if USE_MONGODB:
            self.users_col.update_one(
                {'username': username},
                {'$set': {'premium': is_premium, 'premium_updated_at': user['premium_updated_at']}}
            )
        
        return True
    
    def set_user_admin(self, username: str, is_admin: bool) -> bool:
        """Set user's admin status"""
        user = self.get_user(username)
        if not user:
            return False
        
        user['is_admin'] = is_admin
        
        if USE_MONGODB:
            self.users_col.update_one(
                {'username': username},
                {'$set': {'is_admin': is_admin}}
            )
        
        return True


# Global store instance
store = DataStore()

if USE_MONGODB:
    print("🗄️ Using MongoDB for persistent storage", flush=True)
else:
    print("⚠️ Using in-memory storage (data will be lost on restart)", flush=True)


# ==========================================
# LAZY INITIALIZATION (runs on first request, not import)
# ==========================================
_initialized = False

def ensure_initialized():
    """Initialize test users on first request"""
    global _initialized
    if _initialized:
        return
    _initialized = True
    
    import hashlib
    
    test_users = [
        ('alice_free', 'test123456', 'Alice (Free)', False, False),
        ('bob_free', 'test123456', 'Bob (Free)', False, False),
        ('frank_premium', 'test123456', 'Frank (Premium)', True, False),
        ('admin_user', 'admin123456', 'Admin', True, True),
    ]
    
    try:
        if USE_MONGODB:
            # Check existing users in batch
            existing = set(u['username'] for u in store.users_col.find(
                {'username': {'$in': [t[0] for t in test_users]}},
                {'username': 1}
            ))
            
            new_users = []
            for username, password, display_name, is_premium, is_admin in test_users:
                if username not in existing:
                    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
                    new_users.append({
                        'username': username, 'password': pwd_hash, 'display_name': display_name,
                        'avatar': None, 'email': None, 'phone': None, 'seed_phrase_hash': None,
                        'show_online_status': True, 'read_receipts': True, 'contacts': [],
                        'contacts_synced': False, 'discoverable': True, 'preferences': {},
                        'is_premium': is_premium, 'is_admin': is_admin, 'premium': is_premium,
                        'created_at': store.now()
                    })
            
            if new_users:
                store.users_col.insert_many(new_users)
        else:
            # In-memory
            for username, password, display_name, is_premium, is_admin in test_users:
                if username not in store.users:
                    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
                    store.users[username] = {
                        'username': username, 'password': pwd_hash, 'display_name': display_name,
                        'avatar': None, 'email': None, 'phone': None, 'seed_phrase_hash': None,
                        'show_online_status': True, 'read_receipts': True, 'contacts': [],
                        'contacts_synced': False, 'discoverable': True, 'preferences': {},
                        'is_premium': is_premium, 'is_admin': is_admin, 'premium': is_premium,
                        'created_at': store.now()
                    }
        print("✅ Users ready", flush=True)
    except Exception as e:
        print(f"⚠️ User init: {e}", flush=True)
