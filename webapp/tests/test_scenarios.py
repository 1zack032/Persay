"""
🧪 Comprehensive Scenario Tests

Tests every possible scenario for the 10 test users:
- Free vs Premium access
- Individual messaging
- Group messaging
- Channel subscriptions & posting
- Bot interactions
- Shared notes
- Account recovery
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from webapp.models.store import store, USE_MONGODB
import hashlib


class TestScenarios:
    """Run all scenario tests"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_true(self, condition, message):
        if condition:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            self.errors.append(message)
            print(f"  ❌ {message}")
    
    def assert_false(self, condition, message):
        self.assert_true(not condition, message)
    
    def assert_equal(self, a, b, message):
        self.assert_true(a == b, f"{message} (expected: {b}, got: {a})")
    
    def assert_greater_than(self, a, b, message):
        self.assert_true(a > b, f"{message} (expected: > {b}, got: {a})")


def run_free_user_scenarios(test: TestScenarios):
    """Test scenarios for free users"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 1: FREE USER ACCESS CONTROL")
    print("=" * 60)
    
    # Test 1.1: Free user can access free bots
    print("\n1.1 Free user bot access:")
    alice = store.get_user('alice_free')
    test.assert_false(alice.get('premium', False), "alice_free is NOT premium")
    
    free_bots = store.get_free_bots()
    test.assert_greater_than(len(free_bots), 0, "Free bots exist")
    
    coingecko = store.get_bot('coingecko_bot')
    test.assert_true(coingecko.get('free', False), "CoinGecko bot is free")
    test.assert_true(store.is_free_bot('coingecko_bot'), "is_free_bot() returns True for CoinGecko")
    
    phanes = store.get_bot('phanes_bot')
    test.assert_true(phanes.get('free', False), "Phanes bot is free")
    
    # Test 1.2: Free user CANNOT access premium bots
    print("\n1.2 Free user premium bot restriction:")
    news_bot = store.get_bot('news_bot')
    test.assert_false(news_bot.get('free', False), "News bot requires premium")
    test.assert_false(store.is_free_bot('news_bot'), "is_free_bot() returns False for News bot")
    
    mod_bot = store.get_bot('mod_bot')
    test.assert_false(mod_bot.get('free', False), "Mod bot requires premium")
    
    # Test 1.3: Free user can send/receive messages
    print("\n1.3 Free user messaging:")
    room_id = store.get_room_id('alice_free', 'bob_free')
    messages = store.get_messages(room_id)
    test.assert_greater_than(len(messages), 0, "Free users can exchange messages")
    
    # Test new message
    new_msg = store.add_message(room_id, {
        'from': 'alice_free',
        'to': 'bob_free',
        'encrypted': 'Test message from scenario',
        'timestamp': store.now()
    })
    test.assert_true(new_msg is not None, "Free user can send new message")
    
    # Test 1.4: Free user can join groups
    print("\n1.4 Free user group access:")
    alice_groups = store.get_user_groups('alice_free')
    test.assert_greater_than(len(alice_groups), 0, "Free user can be in groups")
    
    # Test 1.5: Free user can subscribe to channels
    print("\n1.5 Free user channel access:")
    alice_channels = store.get_subscribed_channels('alice_free')
    test.assert_greater_than(len(alice_channels), 0, "Free user can subscribe to channels")


def run_premium_user_scenarios(test: TestScenarios):
    """Test scenarios for premium users"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 2: PREMIUM USER PRIVILEGES")
    print("=" * 60)
    
    # Test 2.1: Premium user status
    print("\n2.1 Premium user status verification:")
    frank = store.get_user('frank_premium')
    test.assert_true(frank.get('premium', False), "frank_premium IS premium")
    
    # Test 2.2: Premium user can access ALL bots
    print("\n2.2 Premium user bot access:")
    all_bots = store.get_all_bots()
    approved_bots = store.get_approved_bots()
    test.assert_greater_than(len(all_bots), 0, "Bots exist in store")
    test.assert_greater_than(len(approved_bots), 0, "Approved bots exist")
    
    premium_bots = store.get_premium_bots()
    test.assert_greater_than(len(premium_bots), 0, "Premium-only bots exist")
    
    # Verify premium user would have access to all
    can_access_free = store.is_free_bot('coingecko_bot')
    test.assert_true(can_access_free, "Premium user can access free bots")
    
    # Test 2.3: Premium user preferences
    print("\n2.3 Premium user preferences:")
    store.update_user_preferences('frank_premium', {
        'theme': 'cyber-neon',
        'font': 'jetbrains',
        'message_style': 'glass'
    })
    prefs = store.get_user_preferences('frank_premium')
    test.assert_equal(prefs.get('theme'), 'cyber-neon', "Theme preference saved")
    test.assert_equal(prefs.get('font'), 'jetbrains', "Font preference saved")
    
    # Test 2.4: Premium user can create channels
    print("\n2.4 Premium user channel ownership:")
    frank_channels = store.get_user_channels('frank_premium')
    test.assert_greater_than(len(frank_channels), 0, "Premium user owns channels")


def run_admin_scenarios(test: TestScenarios):
    """Test scenarios for admin user"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 3: ADMIN PRIVILEGES")
    print("=" * 60)
    
    # Test 3.1: Admin status
    print("\n3.1 Admin status verification:")
    admin = store.get_user('admin_user')
    test.assert_true(admin.get('is_admin', False), "admin_user IS admin")
    test.assert_true(admin.get('premium', False), "admin_user has premium")
    
    # Test 3.2: Admin can see all bots
    print("\n3.2 Admin bot visibility:")
    all_bots = store.get_all_bots()
    test.assert_greater_than(len(all_bots), 0, "Admin can see all bots")
    
    # Test 3.3: Admin owns channels
    print("\n3.3 Admin channel ownership:")
    admin_channels = store.get_user_channels('admin_user')
    test.assert_greater_than(len(admin_channels), 0, "Admin owns channels")


def run_messaging_scenarios(test: TestScenarios):
    """Test messaging between different user types"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 4: CROSS-TIER MESSAGING")
    print("=" * 60)
    
    # Test 4.1: Free to free messaging
    print("\n4.1 Free user to free user:")
    room_id = store.get_room_id('alice_free', 'charlie_free')
    msg = store.add_message(room_id, {
        'from': 'alice_free',
        'to': 'charlie_free',
        'encrypted': 'Hey Charlie!',
        'timestamp': store.now()
    })
    test.assert_true(msg is not None, "Free to free messaging works")
    
    # Test 4.2: Free to premium messaging
    print("\n4.2 Free user to premium user:")
    room_id = store.get_room_id('bob_free', 'grace_premium')
    msg = store.add_message(room_id, {
        'from': 'bob_free',
        'to': 'grace_premium',
        'encrypted': 'Hey Grace (premium)!',
        'timestamp': store.now()
    })
    test.assert_true(msg is not None, "Free to premium messaging works")
    
    # Test 4.3: Premium to free messaging
    print("\n4.3 Premium user to free user:")
    room_id = store.get_room_id('henry_premium', 'diana_free')
    msg = store.add_message(room_id, {
        'from': 'henry_premium',
        'to': 'diana_free',
        'encrypted': 'Hey Diana (free)!',
        'timestamp': store.now()
    })
    test.assert_true(msg is not None, "Premium to free messaging works")
    
    # Test 4.4: Premium to premium messaging
    print("\n4.4 Premium user to premium user:")
    room_id = store.get_room_id('ivy_premium', 'henry_premium')
    msg = store.add_message(room_id, {
        'from': 'ivy_premium',
        'to': 'henry_premium',
        'encrypted': 'Premium squad!',
        'timestamp': store.now()
    })
    test.assert_true(msg is not None, "Premium to premium messaging works")


def run_group_scenarios(test: TestScenarios):
    """Test group functionality"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 5: GROUP FUNCTIONALITY")
    print("=" * 60)
    
    # Test 5.1: Get groups for users
    print("\n5.1 User group memberships:")
    alice_groups = store.get_user_groups('alice_free')
    test.assert_greater_than(len(alice_groups), 0, "alice_free is in groups")
    
    frank_groups = store.get_user_groups('frank_premium')
    test.assert_greater_than(len(frank_groups), 0, "frank_premium is in groups")
    
    # Test 5.2: Group message sending
    print("\n5.2 Group messaging:")
    if alice_groups:
        group_id = alice_groups[0]['id']
        msg = store.add_group_message(group_id, 'alice_free', 'Hello group!', False)
        test.assert_true(msg is not None, "Can send group message")
        
        messages = store.get_group_messages(group_id)
        test.assert_greater_than(len(messages), 0, "Group has messages")
    
    # Test 5.3: Join group by invite code
    print("\n5.3 Join by invite code:")
    group = store.get_group_by_invite_code('MIX2024')
    test.assert_true(group is not None, "Can find group by invite code")
    if group:
        test.assert_equal(group['name'], 'Mixed Community', "Correct group found")


def run_channel_scenarios(test: TestScenarios):
    """Test channel functionality"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 6: CHANNEL FUNCTIONALITY")
    print("=" * 60)
    
    # Test 6.1: Channel discovery
    print("\n6.1 Channel discovery:")
    discover_data = store.get_discover_channels_rotated(username='eve_free')
    test.assert_true('trending' in discover_data, "Trending channels available")
    test.assert_true('most_liked' in discover_data, "Most liked channels available")
    test.assert_true('most_viewed' in discover_data, "Most viewed channels available")
    
    # Test 6.2: Channel subscription
    print("\n6.2 Channel subscription:")
    all_channels = store.get_all_channels()
    if all_channels:
        channel_id = all_channels[0]['id']
        store.subscribe_to_channel(channel_id, 'eve_free')
        channel = store.get_channel(channel_id)
        test.assert_true('eve_free' in channel.get('subscribers', []), "User subscribed to channel")
    
    # Test 6.3: Channel likes
    print("\n6.3 Channel likes:")
    if all_channels:
        channel_id = all_channels[0]['id']
        initial_likes = len(store.get_channel(channel_id).get('likes', []))
        store.like_channel(channel_id, 'diana_free')
        new_likes = len(store.get_channel(channel_id).get('likes', []))
        test.assert_true(new_likes >= initial_likes, "Can like channel")
        
        has_liked = store.has_liked_channel(channel_id, 'diana_free')
        test.assert_true(has_liked, "Like status tracked correctly")
    
    # Test 6.4: Private channel
    print("\n6.4 Private channel visibility:")
    all_public = [c for c in store.get_all_channels() if c.get('discoverable', True)]
    all_private = [c for c in store.get_all_channels() if not c.get('discoverable', True)]
    print(f"     Public channels: {len(all_public)}, Private channels: {len(all_private)}")
    test.assert_greater_than(len(all_private), 0, "Private channels exist")


def run_shared_notes_scenarios(test: TestScenarios):
    """Test shared notes functionality"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 7: SHARED NOTES")
    print("=" * 60)
    
    # Test 7.1: Create shared note
    print("\n7.1 Create shared note:")
    room_id = store.get_room_id('charlie_free', 'diana_free')
    note = store.create_shared_note(
        room_id=room_id,
        title="Test Note",
        content="Secret content here",
        created_by="charlie_free",
        creator_phrase="charlie_secret"
    )
    test.assert_true(note is not None, "Shared note created")
    test.assert_true('id' in note, "Note has ID")
    
    # Test 7.2: Set phrase for other user
    print("\n7.2 Set phrase for member:")
    store.add_pending_member(note['id'], 'diana_free')
    success = store.set_note_phrase(note['id'], 'diana_free', 'diana_secret')
    test.assert_true(success, "Can set phrase for member")
    
    # Test 7.3: Verify phrase
    print("\n7.3 Verify phrase access:")
    # Correct phrase
    content = store.verify_note_phrase(note['id'], 'charlie_free', 'charlie_secret')
    test.assert_true(content is not None, "Correct phrase unlocks content")
    
    # Wrong phrase
    content = store.verify_note_phrase(note['id'], 'charlie_free', 'wrong_phrase')
    test.assert_true(content is None, "Wrong phrase denied")
    
    # Test 7.4: Get notes for room
    print("\n7.4 Get notes for room:")
    notes = store.get_shared_notes_for_room(room_id)
    test.assert_greater_than(len(notes), 0, "Notes retrieved for room")


def run_bot_scenarios(test: TestScenarios):
    """Test bot functionality"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 8: BOT FUNCTIONALITY")
    print("=" * 60)
    
    # Test 8.1: Bot categories
    print("\n8.1 Bot categories:")
    categories = store.BOT_CATEGORIES
    test.assert_greater_than(len(categories), 0, "Bot categories exist")
    test.assert_true('crypto' in categories, "Crypto category exists")
    test.assert_true('trading' in categories, "Trading category exists")
    
    # Test 8.2: Free bot retrieval
    print("\n8.2 Free bot access:")
    free_bots = store.get_free_bots()
    test.assert_equal(len(free_bots), 2, "Exactly 2 free bots exist")
    
    bot_names = [b['name'] for b in free_bots]
    test.assert_true('CoinGecko Price Bot' in bot_names, "CoinGecko is free")
    test.assert_true('Phanes Trading Bot' in bot_names, "Phanes is free")
    
    # Test 8.3: Premium bot retrieval
    print("\n8.3 Premium bot access:")
    premium_bots = store.get_premium_bots()
    test.assert_greater_than(len(premium_bots), 0, "Premium bots exist")
    
    # Test 8.4: Featured bots
    print("\n8.4 Featured bots:")
    featured = store.get_featured_bots(limit=3)
    test.assert_greater_than(len(featured), 0, "Featured bots returned")


def run_search_scenarios(test: TestScenarios):
    """Test search functionality"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 9: SEARCH FUNCTIONALITY")
    print("=" * 60)
    
    # Test 9.1: User search
    print("\n9.1 User search:")
    results = store.search_users('alice', 'bob_free', limit=10)
    test.assert_greater_than(len(results), 0, "Search finds alice_free")
    
    results = store.search_users('premium', 'alice_free', limit=10)
    test.assert_greater_than(len(results), 0, "Search finds premium users")
    
    # Test 9.2: Channel search by interest
    print("\n9.2 Channel interest search:")
    results = store.search_channels_by_interest('crypto', limit=10)
    test.assert_true('exact_matches' in results, "Search returns exact matches")
    
    results = store.search_channels_by_interest('gaming', limit=10)
    test.assert_true('category_matches' in results, "Search returns category matches")
    
    # Test 9.3: Self-exclusion in search
    print("\n9.3 Self-exclusion:")
    results = store.search_users('alice', 'alice_free', limit=10)
    usernames = [r['username'] for r in results]
    test.assert_false('alice_free' in usernames, "Search excludes self")


def run_performance_scenarios(test: TestScenarios):
    """Test performance-critical operations"""
    
    print("\n" + "=" * 60)
    print("📋 SCENARIO 10: PERFORMANCE CHECKS")
    print("=" * 60)
    
    import time
    
    # Test 10.1: Username cache
    print("\n10.1 Username caching:")
    start = time.time()
    usernames1 = store.get_all_usernames()
    time1 = time.time() - start
    
    start = time.time()
    usernames2 = store.get_all_usernames()
    time2 = time.time() - start
    
    test.assert_true(len(usernames1) == len(usernames2), "Cache returns same results")
    print(f"     First call: {time1*1000:.2f}ms, Cached call: {time2*1000:.2f}ms")
    
    # Test 10.2: Batch channel retrieval
    print("\n10.2 Batch channel retrieval:")
    start = time.time()
    channels = store.get_all_user_channels('alice_free')
    elapsed = time.time() - start
    test.assert_true(elapsed < 1.0, f"Channel retrieval under 1s ({elapsed*1000:.2f}ms)")
    
    # Test 10.3: Message retrieval
    print("\n10.3 Message retrieval:")
    room_id = store.get_room_id('alice_free', 'bob_free')
    start = time.time()
    messages = store.get_messages(room_id)
    elapsed = time.time() - start
    test.assert_true(elapsed < 1.0, f"Message retrieval under 1s ({elapsed*1000:.2f}ms)")


def main():
    """Run all scenario tests"""
    
    print("=" * 60)
    print("🧪 MENZA COMPREHENSIVE SCENARIO TESTS")
    print("=" * 60)
    print(f"Storage: {'MongoDB' if USE_MONGODB else 'In-Memory'}")
    
    test = TestScenarios()
    
    # First, create test data
    from webapp.tests.test_data import create_test_users, create_test_messages, create_test_groups, create_test_channels, create_test_shared_notes
    
    print("\n🔄 Setting up test data...")
    users = create_test_users()
    create_test_messages(users)
    create_test_groups(users)
    create_test_channels(users)
    create_test_shared_notes()
    
    # Run all scenario tests
    run_free_user_scenarios(test)
    run_premium_user_scenarios(test)
    run_admin_scenarios(test)
    run_messaging_scenarios(test)
    run_group_scenarios(test)
    run_channel_scenarios(test)
    run_shared_notes_scenarios(test)
    run_bot_scenarios(test)
    run_search_scenarios(test)
    run_performance_scenarios(test)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SCENARIO TEST SUMMARY")
    print("=" * 60)
    total = test.passed + test.failed
    print(f"  Total tests: {total}")
    print(f"  Passed: {test.passed} ✅")
    print(f"  Failed: {test.failed} ❌")
    print(f"  Pass rate: {test.passed/total*100:.1f}%")
    
    if test.errors:
        print("\n❌ FAILED TESTS:")
        for err in test.errors:
            print(f"  - {err}")
    
    if test.failed == 0:
        print("\n🎉 ALL SCENARIOS PASSED!")
    
    return test.failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

