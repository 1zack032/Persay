"""
🔐 Authentication Routes - SECURE
Handles user registration, login, logout, and account recovery.
All passwords are hashed with SHA-256.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from webapp.models import store
from webapp.config import Config
import secrets
import hashlib

auth_bp = Blueprint('auth', __name__)


def hash_password(password: str) -> str:
    """Securely hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed


# BIP39 wordlist (simplified - 256 common words for seed phrases)
WORDLIST = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
    "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
    "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual",
    "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance",
    "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
    "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album",
    "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone",
    "alpha", "already", "also", "alter", "always", "amateur", "amazing", "among",
    "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry",
    "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique",
    "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april",
    "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor",
    "army", "around", "arrange", "arrest", "arrive", "arrow", "art", "artefact",
    "artist", "artwork", "ask", "aspect", "assault", "asset", "assist", "assume",
    "asthma", "athlete", "atom", "attack", "attend", "attitude", "attract", "auction",
    "audit", "august", "aunt", "author", "auto", "autumn", "average", "avocado",
    "avoid", "awake", "aware", "away", "awesome", "awful", "awkward", "axis",
    "baby", "bachelor", "bacon", "badge", "bag", "balance", "balcony", "ball",
    "bamboo", "banana", "banner", "bar", "barely", "bargain", "barrel", "base",
    "basic", "basket", "battle", "beach", "bean", "beauty", "because", "become",
    "beef", "before", "begin", "behave", "behind", "believe", "below", "belt",
    "bench", "benefit", "best", "betray", "better", "between", "beyond", "bicycle",
    "bid", "bike", "bind", "biology", "bird", "birth", "bitter", "black",
    "blade", "blame", "blanket", "blast", "bleak", "bless", "blind", "blood",
    "blossom", "blouse", "blue", "blur", "blush", "board", "boat", "body",
    "boil", "bomb", "bone", "bonus", "book", "boost", "border", "boring",
    "borrow", "boss", "bottom", "bounce", "box", "boy", "bracket", "brain",
    "brand", "brass", "brave", "bread", "breeze", "brick", "bridge", "brief",
    "bright", "bring", "brisk", "broccoli", "broken", "bronze", "broom", "brother",
    "brown", "brush", "bubble", "buddy", "budget", "buffalo", "build", "bulb",
    "bulk", "bullet", "bundle", "bunker", "burden", "burger", "burst", "bus",
    "business", "busy", "butter", "buyer", "buzz", "cabbage", "cabin", "cable"
]


def generate_seed_phrase():
    """Generate a 12-word recovery seed phrase"""
    words = [secrets.choice(WORDLIST) for _ in range(12)]
    return ' '.join(words)


def hash_seed_phrase(seed_phrase):
    """Hash the seed phrase for storage"""
    return hashlib.sha256(seed_phrase.encode()).hexdigest()


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration page - create a new account
    Requires age verification (18+) for legal compliance
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip() or None  # Optional
        phone = request.form.get('phone', '').strip() or None  # Optional
        age_verified = request.form.get('age_verified')
        terms_accepted = request.form.get('terms_accepted')
        
        # Age verification (COPPA/GDPR compliance)
        if not age_verified:
            return render_template('register.html', 
                error="You must confirm you are 18 or older to use Menza")
        
        # Terms acceptance
        if not terms_accepted:
            return render_template('register.html', 
                error="You must accept the Terms of Service and Privacy Policy")
        
        # Basic validation
        if len(username) < Config.MIN_USERNAME_LENGTH:
            return render_template('register.html', 
                error=f"Username must be at least {Config.MIN_USERNAME_LENGTH} characters")
        
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return render_template('register.html', 
                error=f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
        
        if store.user_exists(username):
            return render_template('register.html', 
                error="Username already taken")
        
        # Generate seed phrase for account recovery
        seed_phrase = generate_seed_phrase()
        seed_hash = hash_seed_phrase(seed_phrase)
        
        # Hash password before storing (SECURITY)
        hashed_password = hash_password(password)
        
        # Create user with hashed password
        user = store.create_user(username, hashed_password)
        store.update_user_profile(username, {
            'email': email,
            'phone': phone,
            'seed_hash': seed_hash
        })
        
        session['username'] = username
        session['show_seed_phrase'] = seed_phrase  # Show once after registration
        
        return redirect(url_for('auth.seed_phrase'))
    
    return render_template('register.html')


@auth_bp.route('/seed-phrase')
def seed_phrase():
    """Show the seed phrase once after registration"""
    if 'username' not in session or 'show_seed_phrase' not in session:
        return redirect(url_for('auth.login'))
    
    phrase = session.pop('show_seed_phrase')
    return render_template('seed_phrase.html', seed_phrase=phrase)


@auth_bp.route('/recover', methods=['GET', 'POST'])
def recover():
    """Account recovery page using seed phrase"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        seed_phrase_raw = request.form.get('seed_phrase', '').strip().lower()
        new_password = request.form.get('new_password', '')
        
        if not username or not seed_phrase_raw or not new_password:
            return render_template('recover.html', error="All fields are required")
        
        # Normalize seed phrase: collapse multiple spaces, strip, lowercase
        seed_words = seed_phrase_raw.split()
        
        # Validate exactly 12 words
        if len(seed_words) != 12:
            return render_template('recover.html', 
                error=f"Recovery phrase must be exactly 12 words (you entered {len(seed_words)})")
        
        # Rejoin with single spaces for consistent hashing
        seed_phrase = ' '.join(seed_words)
        
        if len(new_password) < Config.MIN_PASSWORD_LENGTH:
            return render_template('recover.html', 
                error=f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
        
        user = store.get_user(username)
        if not user:
            return render_template('recover.html', error="Account not found")
        
        # Verify seed phrase
        provided_hash = hash_seed_phrase(seed_phrase)
        stored_hash = user.get('seed_hash')
        
        if not stored_hash:
            return render_template('recover.html', 
                error="This account was created before recovery phrases were enabled. Please contact support.")
        
        if provided_hash != stored_hash:
            return render_template('recover.html', error="Invalid recovery phrase. Please check your words and try again.")
        
        # Update password (hash it first - SECURITY)
        hashed_new_password = hash_password(new_password)
        store.update_user_profile(username, {'password': hashed_new_password})
        
        return render_template('recover.html', 
            success="Password reset successfully! You can now log in with your new password.")
    
    return render_template('recover.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - secure password verification"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        user = store.get_user(username)
        
        if not user:
            return render_template('login.html', error="Invalid credentials")
        
        # Verify hashed password (SECURITY)
        if not verify_password(password, user.get('password', '')):
            return render_template('login.html', error="Invalid credentials")
        
        session['username'] = username
        return redirect(url_for('main.chat'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Log out and clear session"""
    session.pop('username', None)
    return redirect(url_for('main.index'))


# ============================================================
# 📱 JSON API Endpoints for iOS/Mobile App
# ============================================================

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    """JSON API for mobile app registration"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400
    
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    email = data.get('email', '').strip() or None
    phone = data.get('phone', '').strip() or None
    
    # Validation
    if len(username) < Config.MIN_USERNAME_LENGTH:
        return jsonify({
            'success': False, 
            'message': f'Username must be at least {Config.MIN_USERNAME_LENGTH} characters'
        }), 400
    
    if len(password) < Config.MIN_PASSWORD_LENGTH:
        return jsonify({
            'success': False, 
            'message': f'Password must be at least {Config.MIN_PASSWORD_LENGTH} characters'
        }), 400
    
    if store.user_exists(username):
        return jsonify({'success': False, 'message': 'Username already taken'}), 400
    
    # Generate seed phrase
    seed_phrase = generate_seed_phrase()
    seed_hash = hash_seed_phrase(seed_phrase)
    
    # Hash password and create user
    hashed_password = hash_password(password)
    user = store.create_user(username, hashed_password)
    store.update_user_profile(username, {
        'email': email,
        'phone': phone,
        'seed_hash': seed_hash
    })
    
    return jsonify({
        'success': True,
        'message': 'Account created successfully',
        'seed_phrase': seed_phrase,
        'user': {
            'username': username,
            'email': email,
            'phone': phone
        }
    })


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """JSON API for mobile app login"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400
    
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    
    user = store.get_user(username)
    
    if not user:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    if not verify_password(password, user.get('password', '')):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    session['username'] = username
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': {
            'username': username,
            'display_name': user.get('display_name'),
            'email': user.get('email'),
            'phone': user.get('phone'),
            'premium': user.get('premium', False)
        }
    })


@auth_bp.route('/api/auth/logout', methods=['POST', 'GET'])
def api_logout():
    """JSON API for mobile app logout"""
    session.pop('username', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@auth_bp.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    """Check if user is authenticated"""
    if 'username' in session:
        user = store.get_user(session['username'])
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'username': session['username'],
                    'display_name': user.get('display_name'),
                    'email': user.get('email'),
                    'phone': user.get('phone'),
                    'premium': user.get('premium', False)
                }
            })
    return jsonify({'success': False, 'message': 'Not authenticated'}), 401


@auth_bp.route('/api/auth/recover', methods=['POST'])
def api_recover():
    """JSON API for account recovery"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400
    
    username = data.get('username', '').strip().lower()
    seed_phrase_input = data.get('seed_phrase', '').strip().lower()
    new_password = data.get('new_password', '')
    
    user = store.get_user(username)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Verify seed phrase
    input_hash = hash_seed_phrase(seed_phrase_input)
    if input_hash != user.get('seed_hash'):
        return jsonify({'success': False, 'message': 'Invalid recovery phrase'}), 401
    
    # Update password
    new_hashed = hash_password(new_password)
    store.update_user_profile(username, {'password': new_hashed})
    
    return jsonify({'success': True, 'message': 'Password reset successful'})

