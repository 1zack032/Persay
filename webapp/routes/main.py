"""
🏠 Main Routes - MIE v2.0 Optimized
"""

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from webapp.models import store
from webapp.core.menza_intelligence_engine import MIE, cached, rate_limited

main_bp = Blueprint('main', __name__)


@main_bp.route('/api/users/search')
@rate_limited
def search_users():
    """Search for users - cached & rate limited"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    query = request.args.get('q', '').lower().strip()
    current_user = session['username']
    
    if not query or len(query) < 2:
        return jsonify({'users': []})
    
    # Check cache
    cache_key = f"user_search:{query}:{current_user}"
    cached_result = MIE.get_cached_response(cache_key)
    if cached_result is not None:
        return jsonify({'users': cached_result})
    
    # Query and cache
    users = store.search_users(query, current_user, limit=20)
    
    # Optimize response - only send needed fields
    optimized = MIE.optimize_response(users, ['username', 'display_name', 'profile_picture'])
    
    MIE.cache_response(cache_key, optimized, ttl=30)
    return jsonify({'users': optimized})


@main_bp.route('/api/users/contacts')
@rate_limited
def get_contacts():
    """Get chat partners - cached & optimized"""
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    username = session['username']
    
    # Record access pattern for prefetching
    MIE.record_access(username, 'contacts')
    
    # Check cache
    cache_key = f"contacts:{username}"
    cached_result = MIE.get_cached_response(cache_key)
    if cached_result is not None:
        return jsonify({'contacts': cached_result})
    
    # Query and cache
    contacts = store.get_chat_partners(username)
    MIE.cache_response(cache_key, contacts, ttl=60, priority='high')
    
    return jsonify({'contacts': contacts})


@main_bp.route('/')
def index():
    """Home page"""
    MIE.record_request()
    
    if 'username' in session:
        return redirect(url_for('main.chat'))
    return render_template('index.html')


@main_bp.route('/chat')
def chat():
    """Main chat page - fully optimized"""
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    MIE.record_request()
    MIE.record_access(username, 'chat')
    
    # Get channels with high-priority caching
    cache_key = f"user_channels:{username}"
    my_channels = MIE.get_cached_response(cache_key)
    
    if my_channels is None:
        try:
            my_channels = store.get_all_user_channels(username)
            MIE.cache_response(cache_key, my_channels, ttl=120, priority='high')
        except Exception:
            my_channels = []
    
    # Prefetch predicted next resources
    predictions = MIE.predict_next_resources(username, 'chat')
    for resource in predictions:
        if resource == 'contacts':
            # Pre-warm cache
            contacts_key = f"contacts:{username}"
            if MIE.get_cached_response(contacts_key) is None:
                try:
                    contacts = store.get_chat_partners(username)
                    MIE.cache_response(contacts_key, contacts, ttl=60)
                except:
                    pass
    
    return render_template('chat.html', 
                         username=username,
                         all_users=[],
                         my_channels=my_channels)


# ============================================
# MIE STATS ENDPOINT
# ============================================

@main_bp.route('/api/mie/stats')
def mie_stats():
    """Get MIE performance statistics"""
    return jsonify(MIE.get_stats())


@main_bp.route('/api/mie/health')
def mie_health():
    """Health check with rate limit info"""
    user_id = session.get('username', 'anonymous')
    rate_info = MIE.get_rate_limit_info(user_id)
    
    return jsonify({
        'status': 'healthy',
        'rate_limit': rate_info,
        'cache_hit_rate': MIE.cache.stats()['hit_rate']
    })
