"""
📺 Channel WebSocket Events

Handles real-time channel interactions:
- Joining/leaving channel rooms
- Reactions (emoji)
- Likes
- Comments
"""

from flask import session
from flask_socketio import emit, join_room, leave_room
from webapp.models import store


def register_channel_events(socketio):
    """Register all channel-related socket events"""
    
    @socketio.on('join_channel')
    def handle_join_channel(data):
        """Join a channel room for real-time updates"""
        if 'username' not in session:
            return
        
        channel_id = data.get('channel_id')
        channel = store.get_channel(channel_id)
        
        if channel:
            join_room(f'channel_{channel_id}')
            print(f"📺 {session['username']} joined channel {channel['name']}")
    
    @socketio.on('leave_channel')
    def handle_leave_channel(data):
        """Leave a channel room"""
        if 'username' not in session:
            return
        
        channel_id = data.get('channel_id')
        leave_room(f'channel_{channel_id}')
    
    @socketio.on('add_reaction')
    def handle_add_reaction(data):
        """Add an emoji reaction to a post"""
        if 'username' not in session:
            return
        
        post_id = data.get('post_id')
        emoji = data.get('emoji')
        username = session['username']
        
        if not emoji:
            return
        
        post = store.toggle_reaction(post_id, emoji, username)
        
        if post:
            emit('reaction_update', {
                'post_id': post_id,
                'reactions': post['reactions']
            }, room=f'channel_{post["channel_id"]}')
    
    @socketio.on('toggle_like')
    def handle_toggle_like(data):
        """Like or unlike a post"""
        if 'username' not in session:
            return
        
        post_id = data.get('post_id')
        username = session['username']
        
        post = store.toggle_like(post_id, username)
        
        if post:
            emit('like_update', {
                'post_id': post_id,
                'likes': post['likes'],
                'like_count': len(post['likes'])
            }, room=f'channel_{post["channel_id"]}')
    
    @socketio.on('add_comment')
    def handle_add_comment(data):
        """Add a comment to a post"""
        if 'username' not in session:
            return
        
        post_id = data.get('post_id')
        content = data.get('content', '').strip()
        username = session['username']
        
        if not content:
            return
        
        comment = store.add_comment(post_id, username, content)
        post = store.get_post(post_id)
        
        if comment and post:
            emit('new_comment', {
                'post_id': post_id,
                'comment': comment
            }, room=f'channel_{post["channel_id"]}')

