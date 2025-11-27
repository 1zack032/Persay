"""
🔐 Authentication Routes

Handles user registration, login, and logout.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for
from webapp.models import store
from webapp.config import Config

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration page - create a new account
    Requires age verification (18+) for legal compliance
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        age_verified = request.form.get('age_verified')
        terms_accepted = request.form.get('terms_accepted')
        
        # Age verification (COPPA/GDPR compliance)
        if not age_verified:
            return render_template('register.html', 
                error="You must confirm you are 18 or older to use Persay")
        
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
        
        # Create user
        store.create_user(username, password)
        
        session['username'] = username
        return redirect(url_for('main.chat'))
    
    return render_template('register.html')


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

