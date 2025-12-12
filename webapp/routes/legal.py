"""
📜 Legal Routes

Privacy Policy, Terms of Service, and other legal pages.
Required for compliance with GDPR, CCPA, and other regulations.
"""

from flask import Blueprint, render_template

legal_bp = Blueprint('legal', __name__)


@legal_bp.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')


@legal_bp.route('/app/privacy')
def app_privacy():
    """App Store Privacy Policy page (iOS/Android)"""
    return render_template('app_privacy.html')


@legal_bp.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

