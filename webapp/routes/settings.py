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
    
    # Process contacts - find matches on Menza
    matches_found = 0
    synced_contacts = []
    
    for contact in contacts:
        phone = contact.get('phone')
        email = contact.get('email')
        name = contact.get('name', 'Unknown')
        
        # Check if any user has this phone or email
        on_menza = False
        menza_username = None
        
        # Search by phone
        if phone:
            found_user = store.find_user_by_contact('phone', phone)
            if found_user:
                on_menza = True
                menza_username = found_user
                matches_found += 1
        
        # Search by email
        if email and not on_menza:
            found_user = store.find_user_by_contact('email', email)
            if found_user:
                on_menza = True
                menza_username = found_user
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

