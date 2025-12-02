"""
⚙️ Settings Routes

User profile management, password changes, and account settings.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from webapp.models import store
import hashlib
import os

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
def settings_page():
    """Main settings page"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    user = store.get_user(username)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('settings.html',
                         username=username,
                         user=user)


@settings_bp.route('/settings/profile', methods=['POST'])
def update_profile():
    """Update user profile information"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    username = session['username']
    
    # Get form data
    display_name = request.form.get('display_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    
    # Handle avatar upload
    avatar_data = None
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename:
            # In a real app, you'd save to cloud storage
            # For now, we'll store as base64 or skip
            pass
    
    # Update user profile
    success = store.update_user_profile(username, {
        'display_name': display_name if display_name else None,
        'email': email if email else None,
        'phone': phone if phone else None,
    })
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to update profile'})


@settings_bp.route('/settings/password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.get_json()
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if len(new_password) < 8:
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters'})
    
    # Verify current password and update
    success = store.change_user_password(username, current_password, new_password)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Current password is incorrect'})


@settings_bp.route('/settings/reset-method', methods=['POST'])
def update_reset_method():
    """Update password reset method preference"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.get_json()
    method = data.get('method', 'email')
    
    if method not in ['email', 'phone']:
        return jsonify({'success': False, 'error': 'Invalid method'})
    
    success = store.update_user_profile(username, {'reset_method': method})
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to update'})


@settings_bp.route('/settings/privacy', methods=['POST'])
def update_privacy():
    """Update privacy settings"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    username = session['username']
    data = request.get_json()
    
    success = store.update_user_profile(username, {
        'show_online_status': data.get('show_online_status', True),
        'show_read_receipts': data.get('show_read_receipts', True),
    })
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to update'})


@settings_bp.route('/api/settings/toggle', methods=['POST'])
def toggle_setting():
    """Toggle a boolean setting"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    username = session['username']
    setting_name = request.form.get('setting_name')
    value = request.form.get('value') == 'true'
    
    if not setting_name:
        return jsonify({'success': False, 'message': 'No setting specified'})
    
    # Valid privacy settings
    valid_settings = [
        'show_online_status', 'show_read_receipts', 'contact_sync_enabled',
        'allow_contact_discovery', 'find_by_username', 'find_by_phone', 'find_by_email'
    ]
    
    if setting_name not in valid_settings:
        return jsonify({'success': False, 'message': 'Invalid setting'})
    
    success = store.update_user_profile(username, {setting_name: value})
    
    if success:
        return jsonify({'success': True, 'message': 'Setting updated'})
    else:
        return jsonify({'success': False, 'message': 'Failed to update setting'})


@settings_bp.route('/api/settings/sync-contacts', methods=['POST'])
def sync_contacts():
    """Sync contacts from user's device"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    username = session['username']
    data = request.get_json()
    contacts = data.get('contacts', [])
    
    if not contacts:
        return jsonify({'success': False, 'message': 'No contacts provided'})
    
    # OPTIMIZED: Batch lookup for contacts
    phones = [c.get('phone') for c in contacts if c.get('phone')]
    emails = [c.get('email') for c in contacts if c.get('email')]
    
    # Single batch query for all phones and emails
    phone_matches = store.find_users_by_contacts_batch('phone', phones) if phones else {}
    email_matches = store.find_users_by_contacts_batch('email', emails) if emails else {}
    
    synced_contacts = []
    matches_found = 0
    
    for contact in contacts:
        phone = contact.get('phone')
        email = contact.get('email')
        name = contact.get('name', 'Unknown')
        
        # Check batch results
        menza_username = phone_matches.get(phone) or email_matches.get(email)
        on_menza = menza_username is not None
        if on_menza:
            matches_found += 1
        
        synced_contacts.append({
            'name': name,
            'phone': phone,
            'email': email,
            'onMenza': on_menza,
            'menzaUsername': menza_username
        })
    
    # Store synced contacts for user
    from datetime import datetime
    store.update_user_profile(username, {
        'synced_contacts': synced_contacts,
        'last_contact_sync': datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    
    return jsonify({
        'success': True,
        'synced_count': len(contacts),
        'matches_found': matches_found
    })


@settings_bp.route('/api/settings/find-contact', methods=['POST'])
def find_contact():
    """Find a user by phone or email"""
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'success': False, 'message': 'No query provided'})
    
    # Check if it looks like a phone number or email
    found_user = None
    
    if '@' in query:
        # Email search
        found_user = store.find_user_by_contact('email', query)
    else:
        # Phone search - strip non-numeric chars
        phone = ''.join(filter(str.isdigit, query))
        if len(phone) >= 10:
            found_user = store.find_user_by_contact('phone', phone)
    
    if found_user:
        return jsonify({'success': True, 'found': True, 'username': found_user})
    else:
        return jsonify({'success': True, 'found': False})


# ==========================================
# PREMIUM SUBSCRIPTION
# ==========================================

@settings_bp.route('/premium')
def premium_page():
    """Premium subscription page with all features"""
    from webapp.utils.premium_features import (
        PREMIUM_FONTS,
        FONT_CATEGORIES,
        LIVE_EMOJIS,
        EMOJI_ANIMATIONS_CSS,
        CHAT_THEMES,
        PREMIUM_FEATURES,
        FEATURE_CATEGORIES,
        PRICING_TIERS,
        get_feature_count,
        generate_google_fonts_url
    )
    
    username = session.get('username')
    user = store.get_user(username) if username else None
    is_premium = user.get('premium', False) if user else False
    
    return render_template('premium.html',
                         username=username,
                         is_premium=is_premium,
                         fonts=PREMIUM_FONTS,
                         font_categories=FONT_CATEGORIES,
                         live_emojis=LIVE_EMOJIS,
                         emoji_css=EMOJI_ANIMATIONS_CSS,
                         themes=CHAT_THEMES,
                         features=PREMIUM_FEATURES,
                         feature_categories=FEATURE_CATEGORIES,
                         pricing=PRICING_TIERS,
                         feature_count=get_feature_count(),
                         google_fonts_url=generate_google_fonts_url())


@settings_bp.route('/upgrade')
def upgrade():
    """Redirect to premium page"""
    return redirect(url_for('settings.premium_page'))


@settings_bp.route('/settings/theme', methods=['POST'])
def set_theme():
    """Set user's chat theme (premium only)"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    from webapp.utils.premium_features import CHAT_THEMES
    
    username = session['username']
    user = store.get_user(username)
    
    theme_id = request.json.get('theme_id')
    
    if theme_id not in CHAT_THEMES:
        return jsonify({'success': False, 'error': 'Invalid theme'}), 400
    
    theme = CHAT_THEMES[theme_id]
    
    # Check if premium theme requires subscription
    if theme['premium'] and not user.get('premium', False):
        return jsonify({'success': False, 'error': 'Premium subscription required'}), 403
    
    # Save theme preference
    store.update_user_preferences(username, {'theme': theme_id})
    
    return jsonify({'success': True, 'theme': theme})


@settings_bp.route('/settings/font', methods=['POST'])
def set_font():
    """Set user's chat font (premium only)"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    from webapp.utils.premium_features import PREMIUM_FONTS
    
    username = session['username']
    user = store.get_user(username)
    
    font_id = request.json.get('font_id')
    
    if font_id not in PREMIUM_FONTS:
        return jsonify({'success': False, 'error': 'Invalid font'}), 400
    
    font = PREMIUM_FONTS[font_id]
    
    # Check if premium font requires subscription
    if font['premium'] and not user.get('premium', False):
        return jsonify({'success': False, 'error': 'Premium subscription required'}), 403
    
    # Save font preference
    store.update_user_preferences(username, {'font': font_id})
    
    return jsonify({'success': True, 'font': font})


@settings_bp.route('/settings/message-style', methods=['POST'])
def set_message_style():
    """Set user's message bubble style (premium only)"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    from webapp.utils.premium_features import MESSAGE_STYLES
    
    username = session['username']
    user = store.get_user(username)
    
    style_id = request.json.get('style_id')
    
    if style_id not in MESSAGE_STYLES:
        return jsonify({'success': False, 'error': 'Invalid style'}), 400
    
    style = MESSAGE_STYLES[style_id]
    
    # Check if premium style requires subscription
    if style['premium'] and not user.get('premium', False):
        return jsonify({'success': False, 'error': 'Premium subscription required'}), 403
    
    # Save style preference
    store.update_user_preferences(username, {'message_style': style_id})
    
    return jsonify({'success': True, 'style': style})


@settings_bp.route('/api/premium/features')
def get_premium_features_api():
    """API endpoint to get all premium features"""
    from webapp.utils.premium_features import (
        PREMIUM_FONTS,
        LIVE_EMOJIS,
        STICKER_PACKS,
        CHAT_THEMES,
        MESSAGE_STYLES,
        PREMIUM_FEATURES,
        PRICING_TIERS
    )
    
    return jsonify({
        'fonts': PREMIUM_FONTS,
        'emojis': LIVE_EMOJIS,
        'stickers': STICKER_PACKS,
        'themes': CHAT_THEMES,
        'message_styles': MESSAGE_STYLES,
        'features': PREMIUM_FEATURES,
        'pricing': PRICING_TIERS
    })

