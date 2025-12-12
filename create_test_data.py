#!/usr/bin/env python3
"""
Create test data for iOS app testing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.models import store
from datetime import datetime
import uuid

# The main user
MAIN_USER = "1zack032"

# Test users (already created via API)
TEST_USERS = ["sarah_test", "mike_demo", "alex_dev", "emma_test"]

def create_test_groups():
    """Create 3 test groups with the main user"""
    groups = [
        {
            "name": "🚀 Startup Squad",
            "description": "Discussing our next big idea",
            "members": [MAIN_USER, "sarah_test", "mike_demo"]
        },
        {
            "name": "🎮 Gaming Night",
            "description": "Coordinating game sessions",
            "members": [MAIN_USER, "alex_dev", "emma_test"]
        },
        {
            "name": "💼 Work Project",
            "description": "Q4 planning and updates",
            "members": [MAIN_USER, "mike_demo", "alex_dev", "sarah_test"]
        }
    ]
    
    created_groups = []
    for g in groups:
        group = store.create_group(
            name=g["name"],
            owner=MAIN_USER,
            members=g["members"]
        )
        if group:
            # Add description to the group
            try:
                if hasattr(store, 'data') and 'groups' in store.data:
                    store.data['groups'][group['id']]['description'] = g["description"]
            except:
                pass  # Skip if MongoDB
            created_groups.append(group)
            print(f"✅ Created group: {g['name']}")
        else:
            print(f"❌ Failed to create group: {g['name']}")
    
    return created_groups

def create_test_channels():
    """Create 3 test channels owned by the main user"""
    channels = [
        {
            "name": "Tech News Daily",
            "description": "Latest updates from the tech world",
            "emoji": "📱",
            "color": "#7c3aed"
        },
        {
            "name": "Crypto Insights",
            "description": "Cryptocurrency market analysis and tips",
            "emoji": "💰",
            "color": "#10b981"
        },
        {
            "name": "Menza Updates",
            "description": "Official updates and announcements",
            "emoji": "🚀",
            "color": "#ec4899"
        }
    ]
    
    created_channels = []
    for c in channels:
        channel = store.create_channel(
            name=c["name"],
            description=c["description"],
            owner=MAIN_USER,
            accent_color=c["color"],
            avatar_emoji=c["emoji"],
            discoverable=True
        )
        if channel:
            # Add some subscribers
            for user in TEST_USERS[:2]:
                store.subscribe_to_channel(channel['id'], user)
            created_channels.append(channel)
            print(f"✅ Created channel: {c['name']}")
        else:
            print(f"❌ Failed to create channel: {c['name']}")
    
    return created_channels

def create_test_messages():
    """Create some test messages between users"""
    from datetime import datetime
    
    messages = [
        {"from": "sarah_test", "to": MAIN_USER, "content": "Hey! How's the app coming along?"},
        {"from": "mike_demo", "to": MAIN_USER, "content": "Ready for our call later?"},
        {"from": "alex_dev", "to": MAIN_USER, "content": "Check out this new feature idea 🚀"},
        {"from": "emma_test", "to": MAIN_USER, "content": "The design looks amazing!"},
    ]
    
    for msg in messages:
        # Create room ID for DM (sorted usernames)
        users = sorted([msg["from"], msg["to"]])
        room_id = f"dm_{users[0]}_{users[1]}"
        
        message = {
            "sender": msg["from"],
            "recipient": msg["to"],
            "content": msg["content"],
            "timestamp": datetime.utcnow().isoformat(),
            "encrypted": False,
            "type": "text"
        }
        
        store.add_message(room_id, message)
        print(f"✅ Message from {msg['from']}: {msg['content'][:30]}...")

def main():
    print("\n" + "="*50)
    print("🧪 Creating Test Data for iOS App")
    print("="*50 + "\n")
    
    print("📝 Creating Groups...")
    create_test_groups()
    
    print("\n📢 Creating Channels...")
    create_test_channels()
    
    print("\n💬 Creating Test Messages...")
    create_test_messages()
    
    print("\n" + "="*50)
    print("✅ Test data created successfully!")
    print("="*50)
    print("\n👤 Test Users (password: testpass123):")
    for user in TEST_USERS:
        print(f"   - {user}")
    print(f"\n🎯 Main User: {MAIN_USER}")
    print("\n")

if __name__ == "__main__":
    main()

