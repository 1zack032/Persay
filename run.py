#!/usr/bin/env python3
"""
🚀 Menza Server Runner

Start the Menza secure messaging server.
- Development: python run.py
- Production: gunicorn --worker-class eventlet -w 1 run:app
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.app import app, socketio

# Export for gunicorn
application = app


def setup_test_data():
    """Create persistent test data for iOS app testing"""
    from webapp.models import store
    from webapp.routes.auth import hash_password, generate_seed_phrase, hash_seed_phrase
    from datetime import datetime
    
    MAIN_USER = '1zack032'
    
    # Main test user
    if not store.user_exists(MAIN_USER):
        hashed = hash_password('1234567890')
        store.create_user(MAIN_USER, hashed)
        seed = generate_seed_phrase()
        store.update_user_profile(MAIN_USER, {'seed_hash': hash_seed_phrase(seed)})
        print(f"   ✅ Created user: {MAIN_USER} (password: 1234567890)")
    
    # Test users with display names
    test_users = [
        ('sarah_test', 'Sarah Wilson', '👩‍💼'),
        ('mike_demo', 'Mike Johnson', '👨‍💻'),
        ('alex_dev', 'Alex Chen', '🧑‍🔬'),
        ('emma_test', 'Emma Davis', '👩‍🎨')
    ]
    
    for username, display_name, emoji in test_users:
        if not store.user_exists(username):
            hashed = hash_password('testpass123')
            store.create_user(username, hashed)
            store.update_user_profile(username, {'display_name': display_name})
            print(f"   ✅ Created user: {username} ({display_name})")
    
    # Create DM conversations with test messages
    test_messages = [
        ('sarah_test', "Hey! How's the app coming along? 🚀"),
        ('mike_demo', "Ready for our call later? Let me know!"),
        ('alex_dev', "Check out this new feature idea I had 💡"),
        ('emma_test', "The design looks amazing! Great work! ✨")
    ]
    
    for sender, content in test_messages:
        users = sorted([MAIN_USER, sender])
        room_id = f"dm_{users[0]}_{users[1]}"
        
        # Check if messages already exist
        existing = store.get_messages(room_id)
        if not existing:
            message = {
                'sender': sender,
                'recipient': MAIN_USER,
                'content': content,
                'timestamp': datetime.utcnow().isoformat(),
                'encrypted': False,
                'type': 'text'
            }
            store.add_message(room_id, message)
            print(f"   💬 Message from {sender}")
    
    # Create groups if they don't exist
    existing_groups = [g.get('name') for g in store.get_user_groups(MAIN_USER)]
    groups = [
        ("🚀 Startup Squad", ['1zack032', 'sarah_test', 'mike_demo']),
        ("🎮 Gaming Night", ['1zack032', 'alex_dev', 'emma_test']),
        ("💼 Work Project", ['1zack032', 'mike_demo', 'alex_dev', 'sarah_test'])
    ]
    for name, members in groups:
        if name not in existing_groups:
            store.create_group(name=name, owner=MAIN_USER, members=members)
            print(f"   ✅ Created group: {name}")
    
    # Create channels if they don't exist
    existing_channels = [c.get('name') for c in store.get_user_channels(MAIN_USER)]
    channels = [
        ("Tech News Daily", "Latest tech updates", "📱", "#7c3aed"),
        ("Crypto Insights", "Crypto analysis", "💰", "#10b981"),
        ("Menza Updates", "Official announcements", "🚀", "#ec4899")
    ]
    for name, desc, emoji, color in channels:
        if name not in existing_channels:
            store.create_channel(name=name, description=desc, owner=MAIN_USER,
                               accent_color=color, avatar_emoji=emoji)
            print(f"   ✅ Created channel: {name}")


if __name__ == '__main__':
    # Get port from environment (for cloud platforms) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    print()
    print("🔐 " + "=" * 50)
    print("🚀 Starting Menza Encrypted Messaging Server")
    print(f"📍 Open http://localhost:{port} in your browser")
    print("🔐 " + "=" * 50)
    
    # Setup test data for iOS development
    print("\n📱 Setting up iOS test data...")
    try:
        setup_test_data()
        print("   ✅ Test data ready!\n")
    except Exception as e:
        print(f"   ⚠️ Test data setup: {e}\n")
    
    socketio.run(
        app,
        debug=debug,
        host='0.0.0.0',
        port=port,
        allow_unsafe_werkzeug=True  # Allow development server
    )

