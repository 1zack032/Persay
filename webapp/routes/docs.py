"""
📚 Documentation Routes

Handles all documentation pages including privacy policy sections,
terms of service, security information, and guides.
"""

from flask import Blueprint, render_template

docs_bp = Blueprint('docs', __name__, url_prefix='/docs')


@docs_bp.route('/')
def docs_home():
    """Documentation hub page"""
    return render_template('docs/index.html')


# ===========================================
# PRIVACY POLICY PAGES
# ===========================================

@docs_bp.route('/privacy')
def privacy_overview():
    """Privacy policy overview"""
    return render_template('docs/privacy/overview.html',
                         active_section='privacy',
                         current_page='privacy-overview')


@docs_bp.route('/privacy/data-collection')
def privacy_data_collection():
    """Data collection details"""
    return render_template('docs/privacy/data-collection.html',
                         active_section='privacy',
                         current_page='data-collection')


@docs_bp.route('/privacy/data-usage')
def privacy_data_usage():
    """Data usage information"""
    return render_template('docs/privacy/data-usage.html',
                         active_section='privacy',
                         current_page='data-usage')


@docs_bp.route('/privacy/your-rights')
def privacy_your_rights():
    """User rights (GDPR, CCPA)"""
    return render_template('docs/privacy/your-rights.html',
                         active_section='privacy',
                         current_page='your-rights')


@docs_bp.route('/privacy/cookies')
def privacy_cookies():
    """Cookie policy"""
    return render_template('docs/privacy/cookies.html',
                         active_section='privacy',
                         current_page='cookies')


@docs_bp.route('/privacy/retention')
def privacy_retention():
    """Data retention policy"""
    return render_template('docs/privacy/retention.html',
                         active_section='privacy',
                         current_page='retention')


@docs_bp.route('/privacy/third-parties')
def privacy_third_parties():
    """Third party data sharing"""
    return render_template('docs/privacy/third-parties.html',
                         active_section='privacy',
                         current_page='third-parties')


# ===========================================
# TERMS & SECURITY
# ===========================================

@docs_bp.route('/terms')
def terms():
    """Terms of Service"""
    return render_template('docs/terms.html',
                         active_section='terms',
                         current_page='terms')


@docs_bp.route('/security')
def security():
    """Security information"""
    return render_template('docs/security.html',
                         active_section='security',
                         current_page='security')


# ===========================================
# GUIDES
# ===========================================

@docs_bp.route('/guides/getting-started')
def guide_getting_started():
    """Getting started guide"""
    return render_template('docs/guides/getting-started.html',
                         active_section='docs',
                         current_page='getting-started')


@docs_bp.route('/guides/encryption')
def guide_encryption():
    """Encryption guide"""
    return render_template('docs/guides/encryption.html',
                         active_section='docs',
                         current_page='encryption')


@docs_bp.route('/guides/channels')
def guide_channels():
    """Channels guide"""
    return render_template('docs/guides/channels.html',
                         active_section='docs',
                         current_page='channels')

