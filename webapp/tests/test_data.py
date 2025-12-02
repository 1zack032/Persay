"""
🧪 Test Data Generator

Creates 10 test users with various scenarios:
- Free vs Premium users
- Individual messaging
- Group messaging
- Channel subscriptions
- Bot interactions
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from webapp.models.store import store, USE_MONGODB
import hashlib
import secrets


def hash_seed(phrase):
    return hashlib.sha256(phrase.encode()).hexdigest()


def create_test_users():
    """Create 10 test users with different characteristics"""
    
    test_users = [
        # FREE USERS (5)
        {
            'username': 'alice_free',
            'password': 'test123456',
            'display_name': 'Alice (Free User)',
            'email': 'alice@test.com',
            'phone': '1234567890',
            'premium': False,
            'is_admin': False,
        },
        {
            'username': 'bob_free',
            'password': 'test123456',
            'display_name': 'Bob (Free User)',
            'email': 'bob@test.com',
            'phone': '1234567891',
            'premium': False,
            'is_admin': False,
        },
        {
            'username': 'charlie_free',
            'password': 'test123456',
            'display_name': 'Charlie (Free User)',
            'email': None,  # No email
            'phone': None,  # No phone - recovery via seed only
            'premium': False,
            'is_admin': False,
        },
        {
            'username': 'diana_free',
            'password': 'test123456',
            'display_name': 'Diana (Free User)',
            'email': 'diana@test.com',
            'phone': None,
            'premium': False,
            'is_admin': False,
        },
        {
            'username': 'eve_free',
            'password': 'test123456',
            'display_name': 'Eve (Free User)',
            'email': None,
            'phone': '1234567894',
            'premium': False,
            'is_admin': False,
        },
        
        # PREMIUM USERS (4)
        {
            'username': 'frank_premium',
            'password': 'test123456',
            'display_name': 'Frank (Premium)',
            'email': 'frank@test.com',
            'phone': '1234567895',
            'premium': True,
            'is_admin': False,
        },
        {
            'username': 'grace_premium',
            'password': 'test123456',
            'display_name': 'Grace (Premium)',
            'email': 'grace@test.com',
            'phone': '1234567896',
            'premium': True,
            'is_admin': False,
        },
        {
            'username': 'henry_premium',
            'password': 'test123456',
            'display_name': 'Henry (Premium)',
            'email': 'henry@test.com',
            'phone': None,
            'premium': True,
            'is_admin': False,
        },
        {
            'username': 'ivy_premium',
            'password': 'test123456',
            'display_name': 'Ivy (Premium Bot Dev)',
            'email': 'ivy@test.com',
            'phone': '1234567898',
            'premium': True,
            'is_admin': False,
        },
        
        # ADMIN USER (1)
        {
            'username': 'admin_user',
            'password': 'admin123456',
            'display_name': 'Admin User',
            'email': 'admin@menza.app',
            'phone': '1234567899',
            'premium': True,  # Admins have premium
            'is_admin': True,
        },
    ]
    
    created_users = []
    
    for user_data in test_users:
        username = user_data['username']
        
        # Check if user already exists
        if store.user_exists(username):
            print(f"⏭️  User {username} already exists, updating...")
            # Update existing user
            store.update_user_profile(username, {
                'display_name': user_data['display_name'],
                'email': user_data['email'],
                'phone': user_data['phone'],
            })
            store.set_user_premium(username, user_data['premium'])
            store.set_user_admin(username, user_data['is_admin'])
        else:
            # Create new user
            print(f"✅ Creating user: {username}")
            store.create_user(username, user_data['password'])
            
            # Set profile
            seed_phrase = f"test seed phrase for {username}"
            store.update_user_profile(username, {
                'display_name': user_data['display_name'],
                'email': user_data['email'],
                'phone': user_data['phone'],
                'seed_hash': hash_seed(seed_phrase),
            })
            
            # Set premium/admin status
            store.set_user_premium(username, user_data['premium'])
            store.set_user_admin(username, user_data['is_admin'])
        
        created_users.append(user_data)
    
    return created_users


def create_test_messages(users):
    """Create test messages between users"""
    
    print("\n📨 Creating test messages...")
    
    # Alice and Bob chat (free users)
    room_id = store.get_room_id('alice_free', 'bob_free')
    messages = [
        {'from': 'alice_free', 'to': 'bob_free', 'encrypted': 'Hello Bob! This is a test message.', 'timestamp': store.now()},
        {'from': 'bob_free', 'to': 'alice_free', 'encrypted': 'Hi Alice! Great to hear from you!', 'timestamp': store.now()},
        {'from': 'alice_free', 'to': 'bob_free', 'encrypted': 'How are you doing today?', 'timestamp': store.now()},
    ]
    for msg in messages:
        store.add_message(room_id, msg)
    print(f"  ✅ Created chat between alice_free and bob_free")
    
    # Frank and Grace chat (premium users)
    room_id = store.get_room_id('frank_premium', 'grace_premium')
    messages = [
        {'from': 'frank_premium', 'to': 'grace_premium', 'encrypted': 'Hey Grace, loving the premium features!', 'timestamp': store.now()},
        {'from': 'grace_premium', 'to': 'frank_premium', 'encrypted': 'Same here! The themes are amazing.', 'timestamp': store.now()},
    ]
    for msg in messages:
        store.add_message(room_id, msg)
    print(f"  ✅ Created chat between frank_premium and grace_premium")
    
    # Cross free-premium chat
    room_id = store.get_room_id('alice_free', 'frank_premium')
    messages = [
        {'from': 'alice_free', 'to': 'frank_premium', 'encrypted': 'Hi Frank, I see you have premium!', 'timestamp': store.now()},
        {'from': 'frank_premium', 'to': 'alice_free', 'encrypted': 'Yes! You should upgrade, it\'s worth it!', 'timestamp': store.now()},
    ]
    for msg in messages:
        store.add_message(room_id, msg)
    print(f"  ✅ Created cross-tier chat between alice_free and frank_premium")


def create_test_groups(users):
    """Create test group chats"""
    
    print("\n👥 Creating test groups...")
    
    # Group 1: Free users only
    group1 = store.create_group(
        name="Free Users Hangout",
        owner="alice_free",
        members=["bob_free", "charlie_free", "diana_free"],
        invite_code="FREE2024"
    )
    print(f"  ✅ Created group: {group1['name']} (ID: {group1['id']})")
    
    # Add some messages
    store.add_group_message(group1['id'], 'alice_free', 'Welcome to the free users group!', False)
    store.add_group_message(group1['id'], 'bob_free', 'Thanks for adding me!', False)
    store.add_group_message(group1['id'], 'charlie_free', 'This is great!', False)
    
    # Group 2: Premium users only
    group2 = store.create_group(
        name="Premium Exclusive",
        owner="frank_premium",
        members=["grace_premium", "henry_premium", "ivy_premium"],
        invite_code="PREM2024"
    )
    print(f"  ✅ Created group: {group2['name']} (ID: {group2['id']})")
    
    store.add_group_message(group2['id'], 'frank_premium', 'Premium squad!', False)
    store.add_group_message(group2['id'], 'grace_premium', 'Loving the features!', False)
    
    # Group 3: Mixed free and premium
    group3 = store.create_group(
        name="Mixed Community",
        owner="admin_user",
        members=["alice_free", "bob_free", "frank_premium", "grace_premium"],
        invite_code="MIX2024"
    )
    print(f"  ✅ Created group: {group3['name']} (ID: {group3['id']})")
    
    store.add_group_message(group3['id'], 'admin_user', 'Welcome everyone to the community!', False)
    store.add_group_message(group3['id'], 'alice_free', 'Happy to be here!', False)
    store.add_group_message(group3['id'], 'frank_premium', 'Great initiative admin!', False)
    
    return [group1, group2, group3]


def create_test_channels(users):
    """Create test channels with different settings"""
    
    print("\n📺 Creating test channels...")
    
    # Channel 1: Discoverable public channel by premium user
    channel1 = store.create_channel(
        name="Crypto Trading Tips",
        description="Daily trading tips and market analysis. Join us for crypto insights!",
        owner="frank_premium",
        accent_color="#8b5cf6",
        avatar_emoji="📈",
        discoverable=True,
        tags=["crypto", "trading", "bitcoin"]
    )
    # Add some subscribers
    store.subscribe_to_channel(channel1['id'], 'alice_free')
    store.subscribe_to_channel(channel1['id'], 'bob_free')
    store.subscribe_to_channel(channel1['id'], 'grace_premium')
    # Add views and likes
    store.increment_channel_views(channel1['id'])
    store.increment_channel_views(channel1['id'])
    store.increment_channel_views(channel1['id'])
    store.like_channel(channel1['id'], 'alice_free')
    store.like_channel(channel1['id'], 'bob_free')
    print(f"  ✅ Created channel: {channel1['name']} (3 subscribers, 3 views, 2 likes)")
    
    # Channel 2: Private channel (not discoverable)
    channel2 = store.create_channel(
        name="Private Investment Club",
        description="Exclusive investment discussions for members only",
        owner="grace_premium",
        accent_color="#10b981",
        avatar_emoji="💰",
        discoverable=False,
        tags=["investment", "private"]
    )
    store.subscribe_to_channel(channel2['id'], 'henry_premium')
    store.subscribe_to_channel(channel2['id'], 'ivy_premium')
    print(f"  ✅ Created channel: {channel2['name']} (Private, 2 subscribers)")
    
    # Channel 3: News channel
    channel3 = store.create_channel(
        name="Tech News Daily",
        description="Stay updated with the latest technology news and updates",
        owner="admin_user",
        accent_color="#ef4444",
        avatar_emoji="📰",
        discoverable=True,
        tags=["news", "tech", "updates"]
    )
    for user in ['alice_free', 'bob_free', 'charlie_free', 'diana_free', 'eve_free', 'frank_premium']:
        store.subscribe_to_channel(channel3['id'], user)
    store.increment_channel_views(channel3['id'])
    store.increment_channel_views(channel3['id'])
    store.increment_channel_views(channel3['id'])
    store.increment_channel_views(channel3['id'])
    store.increment_channel_views(channel3['id'])
    store.like_channel(channel3['id'], 'alice_free')
    store.like_channel(channel3['id'], 'frank_premium')
    store.like_channel(channel3['id'], 'charlie_free')
    print(f"  ✅ Created channel: {channel3['name']} (6 subscribers, 5 views, 3 likes)")
    
    # Channel 4: Community channel
    channel4 = store.create_channel(
        name="Gaming Community",
        description="Chat about games, esports, and gaming news",
        owner="henry_premium",
        accent_color="#fbbf24",
        avatar_emoji="🎮",
        discoverable=True,
        tags=["gaming", "esports", "community"]
    )
    store.subscribe_to_channel(channel4['id'], 'eve_free')
    store.subscribe_to_channel(channel4['id'], 'diana_free')
    store.increment_channel_views(channel4['id'])
    store.like_channel(channel4['id'], 'eve_free')
    print(f"  ✅ Created channel: {channel4['name']} (2 subscribers, 1 view, 1 like)")
    
    return [channel1, channel2, channel3, channel4]


def create_test_shared_notes():
    """Create test shared notes between users"""
    
    print("\n📝 Creating test shared notes...")
    
    # Shared note between Alice and Bob
    room_id = store.get_room_id('alice_free', 'bob_free')
    note = store.create_shared_note(
        room_id=room_id,
        title="Meeting Notes",
        content="Important discussion points:\n1. Project deadline\n2. Budget review\n3. Team updates",
        created_by="alice_free",
        creator_phrase="secret123"
    )
    # Bob sets his phrase
    store.add_pending_member(note['id'], 'bob_free')
    store.set_note_phrase(note['id'], 'bob_free', 'bobsecret456')
    print(f"  ✅ Created shared note: '{note['title']}' between alice_free and bob_free")
    
    # Shared note between Frank and Grace (premium users)
    room_id = store.get_room_id('frank_premium', 'grace_premium')
    note2 = store.create_shared_note(
        room_id=room_id,
        title="Investment Ideas",
        content="Crypto portfolio:\n- BTC 40%\n- ETH 30%\n- SOL 20%\n- Others 10%",
        created_by="frank_premium",
        creator_phrase="premiumsecret"
    )
    store.add_pending_member(note2['id'], 'grace_premium')
    store.set_note_phrase(note2['id'], 'grace_premium', 'gracesecret')
    print(f"  ✅ Created shared note: '{note2['title']}' between frank_premium and grace_premium")


def run_all_tests():
    """Run comprehensive tests on all features"""
    
    print("\n" + "=" * 60)
    print("🧪 RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Test 1: User retrieval
    print("\n📋 Test 1: User Retrieval")
    for username in ['alice_free', 'frank_premium', 'admin_user']:
        user = store.get_user(username)
        if not user:
            errors.append(f"User {username} not found!")
        else:
            print(f"  ✅ {username}: premium={user.get('premium', False)}, admin={user.get('is_admin', False)}")
    
    # Test 2: Message retrieval
    print("\n📋 Test 2: Message Retrieval")
    room_id = store.get_room_id('alice_free', 'bob_free')
    messages = store.get_messages(room_id)
    if len(messages) == 0:
        warnings.append("No messages found between alice_free and bob_free")
    else:
        print(f"  ✅ Found {len(messages)} messages between alice_free and bob_free")
    
    # Test 3: Group retrieval
    print("\n📋 Test 3: Group Retrieval")
    alice_groups = store.get_user_groups('alice_free')
    print(f"  ✅ alice_free is in {len(alice_groups)} groups")
    for g in alice_groups:
        print(f"      - {g['name']}")
    
    # Test 4: Channel retrieval
    print("\n📋 Test 4: Channel Retrieval")
    alice_channels = store.get_all_user_channels('alice_free')
    print(f"  ✅ alice_free is in {len(alice_channels)} channels")
    for c in alice_channels:
        print(f"      - {c['name']} (owner: {c['owner']})")
    
    # Test 5: Premium vs Free bot access
    print("\n📋 Test 5: Bot Access Control")
    free_bots = store.get_free_bots()
    premium_bots = store.get_premium_bots()
    print(f"  ✅ Free bots: {len(free_bots)}")
    for bot in free_bots:
        print(f"      - {bot['name']} ({bot['bot_id']})")
    print(f"  ✅ Premium bots: {len(premium_bots)}")
    for bot in premium_bots:
        print(f"      - {bot['name']} ({bot['bot_id']})")
    
    # Test 6: Discoverable channels
    print("\n📋 Test 6: Channel Discovery")
    discover_data = store.get_discover_channels_rotated(username='alice_free')
    print(f"  ✅ Trending channels: {len(discover_data.get('trending', []))}")
    print(f"  ✅ Most liked: {len(discover_data.get('most_liked', []))}")
    print(f"  ✅ Most viewed: {len(discover_data.get('most_viewed', []))}")
    print(f"  ✅ New: {len(discover_data.get('new', []))}")
    
    # Test 7: Search users
    print("\n📋 Test 7: User Search")
    search_results = store.search_users('free', 'admin_user', limit=10)
    print(f"  ✅ Search for 'free' returned {len(search_results)} results")
    
    # Test 8: Chat partners
    print("\n📋 Test 8: Chat Partners")
    partners = store.get_chat_partners('alice_free')
    print(f"  ✅ alice_free has chatted with {len(partners)} users")
    for p in partners:
        print(f"      - {p['username']}")
    
    # Test 9: Shared notes
    print("\n📋 Test 9: Shared Notes")
    room_id = store.get_room_id('alice_free', 'bob_free')
    notes = store.get_shared_notes_for_room(room_id)
    print(f"  ✅ Found {len(notes)} shared notes between alice_free and bob_free")
    
    # Test 10: Premium user preferences
    print("\n📋 Test 10: User Preferences")
    store.update_user_preferences('frank_premium', {
        'theme': 'midnight-purple',
        'font': 'playfair',
        'message_style': 'neon'
    })
    prefs = store.get_user_preferences('frank_premium')
    print(f"  ✅ frank_premium preferences: {prefs}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    
    if errors:
        print("\n❌ ERRORS:")
        for err in errors:
            print(f"  - {err}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warn in warnings:
            print(f"  - {warn}")
    
    if not errors and not warnings:
        print("\n✅ ALL TESTS PASSED!")
    
    return len(errors) == 0


def main():
    """Main entry point for test data creation"""
    
    print("=" * 60)
    print("🧪 MENZA TEST DATA GENERATOR")
    print("=" * 60)
    print(f"Storage: {'MongoDB' if USE_MONGODB else 'In-Memory'}")
    print("=" * 60)
    
    # Create test users
    print("\n👤 Creating test users...")
    users = create_test_users()
    print(f"✅ Created/Updated {len(users)} test users")
    
    # Create test messages
    create_test_messages(users)
    
    # Create test groups
    groups = create_test_groups(users)
    print(f"✅ Created {len(groups)} test groups")
    
    # Create test channels
    channels = create_test_channels(users)
    print(f"✅ Created {len(channels)} test channels")
    
    # Create shared notes
    create_test_shared_notes()
    
    # Run tests
    success = run_all_tests()
    
    # Print login info
    print("\n" + "=" * 60)
    print("🔑 TEST USER LOGIN CREDENTIALS")
    print("=" * 60)
    print("\nFREE USERS:")
    print("  alice_free / test123456")
    print("  bob_free / test123456")
    print("  charlie_free / test123456")
    print("  diana_free / test123456")
    print("  eve_free / test123456")
    print("\nPREMIUM USERS:")
    print("  frank_premium / test123456")
    print("  grace_premium / test123456")
    print("  henry_premium / test123456")
    print("  ivy_premium / test123456")
    print("\nADMIN USER:")
    print("  admin_user / admin123456")
    print("=" * 60)
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

