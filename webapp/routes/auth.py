"""
🔐 Authentication Routes

Handles user registration, login, logout, and account recovery.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from webapp.models import store
from webapp.config import Config
import secrets
import hashlib

auth_bp = Blueprint('auth', __name__)

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
        
        # Create user with optional email/phone and seed hash
        user = store.create_user(username, password)
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
        seed_phrase = request.form.get('seed_phrase', '').strip().lower()
        new_password = request.form.get('new_password', '')
        
        if not username or not seed_phrase or not new_password:
            return render_template('recover.html', error="All fields are required")
        
        if len(new_password) < Config.MIN_PASSWORD_LENGTH:
            return render_template('recover.html', 
                error=f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
        
        user = store.get_user(username)
        if not user:
            return render_template('recover.html', error="Account not found")
        
        # Verify seed phrase
        provided_hash = hash_seed_phrase(seed_phrase)
        stored_hash = user.get('seed_hash')
        
        if not stored_hash or provided_hash != stored_hash:
            return render_template('recover.html', error="Invalid recovery phrase")
        
        # Update password
        store.update_user_profile(username, {'password': new_password})
        
        return render_template('recover.html', 
            success="Password reset successfully! You can now log in with your new password.")
    
    return render_template('recover.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        
        user = store.get_user(username)
        
        if not user:
            return render_template('login.html', error="User not found")
        
        if user['password'] != password:
            return render_template('login.html', error="Wrong password")
        
        session['username'] = username
        return redirect(url_for('main.chat'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Log out and clear session"""
    session.pop('username', None)
    return redirect(url_for('main.index'))

