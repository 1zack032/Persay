"""
🔒 Bot Security Module

Handles all security-related functionality for the Bot Store:
- API key hashing and verification
- Webhook signature generation and verification
- Permission scopes
- Security scanning
- Rate limiting
- Premium access control
"""

import hmac
import hashlib
import secrets
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
import json

# ============================================
# API KEY SECURITY
# ============================================

def generate_api_key() -> Tuple[str, str]:
    """
    Generate a new API key and its hash.
    Returns: (raw_key, hashed_key)
    
    The raw key is shown to the developer ONCE.
    Only the hash is stored in the database.
    """
    raw_key = f"menza_bot_{secrets.token_hex(32)}"
    hashed_key = hash_api_key(raw_key)
    return raw_key, hashed_key


def hash_api_key(raw_key: str) -> str:
    """
    Hash an API key using SHA-256 with salt.
    We use SHA-256 instead of bcrypt for faster verification
    since API keys are already high-entropy.
    """
    # Use a fixed salt for consistency (in production, use environment variable)
    salt = "menza_bot_salt_v1"
    return hashlib.sha256(f"{salt}{raw_key}".encode()).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash."""
    computed_hash = hash_api_key(raw_key)
    return hmac.compare_digest(computed_hash, stored_hash)


# ============================================
# WEBHOOK SIGNATURE
# ============================================

def generate_webhook_signature(payload: dict, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.
    
    Args:
        payload: The webhook payload (dict)
        secret: The bot's API key or secret
    
    Returns:
        Hex-encoded signature
    """
    # Canonical JSON (sorted keys, no extra spaces)
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def verify_webhook_signature(payload: dict, signature: str, secret: str) -> bool:
    """
    Verify a webhook signature.
    
    Args:
        payload: The received payload
        signature: The X-Menza-Signature header value
        secret: The bot's API key
    
    Returns:
        True if signature is valid
    """
    expected = generate_webhook_signature(payload, secret)
    return hmac.compare_digest(expected, signature)


def generate_webhook_headers(bot_id: str, payload: dict, api_key: str) -> dict:
    """Generate all required headers for a webhook request."""
    timestamp = int(time.time())
    signature = generate_webhook_signature(payload, api_key)
    
    return {
        'Content-Type': 'application/json',
        'X-Menza-Bot-ID': bot_id,
        'X-Menza-Timestamp': str(timestamp),
        'X-Menza-Signature': signature,
        'User-Agent': 'Menza-Webhook/1.0'
    }


# ============================================
# PERMISSION SCOPES
# ============================================

class BotPermissions:
    """Bot permission scopes with granular access control."""
    
    # Permission definitions
    SCOPES = {
        # Message permissions
        'messages.read': {
            'name': 'Read Messages',
            'description': 'Read messages in groups where bot is added',
            'risk': 'medium',
            'category': 'messages'
        },
        'messages.send': {
            'name': 'Send Messages',
            'description': 'Send messages to groups and channels',
            'risk': 'low',
            'category': 'messages'
        },
        'messages.delete': {
            'name': 'Delete Messages',
            'description': 'Delete messages sent by the bot',
            'risk': 'low',
            'category': 'messages'
        },
        
        # Command permissions
        'commands.receive': {
            'name': 'Receive Commands',
            'description': 'Receive slash command invocations',
            'risk': 'low',
            'category': 'commands'
        },
        'commands.register': {
            'name': 'Register Commands',
            'description': 'Register new slash commands dynamically',
            'risk': 'medium',
            'category': 'commands'
        },
        
        # Member permissions
        'members.list': {
            'name': 'View Members',
            'description': 'View the member list of groups',
            'risk': 'medium',
            'category': 'members'
        },
        'members.manage': {
            'name': 'Manage Members',
            'description': 'Kick, ban, or mute members',
            'risk': 'high',
            'category': 'members'
        },
        
        # Group permissions
        'groups.info': {
            'name': 'Group Info',
            'description': 'View group name, description, settings',
            'risk': 'low',
            'category': 'groups'
        },
        'groups.settings': {
            'name': 'Modify Settings',
            'description': 'Change group settings',
            'risk': 'high',
            'category': 'groups'
        },
        
        # Webhook permissions
        'webhooks.receive': {
            'name': 'Receive Webhooks',
            'description': 'Receive event notifications via webhook',
            'risk': 'low',
            'category': 'webhooks'
        },
        
        # Analytics permissions
        'analytics.read': {
            'name': 'Read Analytics',
            'description': 'Access usage statistics',
            'risk': 'low',
            'category': 'analytics'
        }
    }
    
    # Default scopes for new bots
    DEFAULT_SCOPES = ['commands.receive', 'messages.send']
    
    # High-risk scopes that require extra review
    HIGH_RISK_SCOPES = ['members.manage', 'groups.settings', 'messages.read']
    
    @classmethod
    def get_scope_info(cls, scope: str) -> Optional[dict]:
        """Get information about a specific scope."""
        return cls.SCOPES.get(scope)
    
    @classmethod
    def get_all_scopes(cls) -> dict:
        """Get all available scopes."""
        return cls.SCOPES
    
    @classmethod
    def validate_scopes(cls, scopes: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate a list of scopes.
        Returns: (is_valid, invalid_scopes)
        """
        invalid = [s for s in scopes if s not in cls.SCOPES]
        return len(invalid) == 0, invalid
    
    @classmethod
    def has_high_risk_scopes(cls, scopes: List[str]) -> bool:
        """Check if any high-risk scopes are requested."""
        return any(s in cls.HIGH_RISK_SCOPES for s in scopes)
    
    @classmethod
    def get_risk_level(cls, scopes: List[str]) -> str:
        """Get overall risk level for a set of scopes."""
        if any(cls.SCOPES.get(s, {}).get('risk') == 'high' for s in scopes):
            return 'high'
        elif any(cls.SCOPES.get(s, {}).get('risk') == 'medium' for s in scopes):
            return 'medium'
        return 'low'


# ============================================
# SECURITY SCANNING
# ============================================

class BotSecurityScanner:
    """Automated security scanning for bots."""
    
    # Suspicious patterns in bot names/descriptions
    SUSPICIOUS_PATTERNS = [
        r'password',
        r'credential',
        r'hack',
        r'exploit',
        r'phish',
        r'steal',
        r'malware',
        r'virus',
        r'keylog',
        r'inject',
    ]
    
    # Blocked webhook domains
    BLOCKED_DOMAINS = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '192.168.',
        '10.0.',
        '172.16.',
        'example.com',
        'test.com',
    ]
    
    # Required for webhook URLs
    WEBHOOK_REQUIREMENTS = {
        'must_be_https': True,
        'max_redirects': 3,
        'timeout_seconds': 5,
    }
    
    @classmethod
    def scan_bot(cls, bot_data: dict) -> dict:
        """
        Perform comprehensive security scan on a bot.
        
        Returns:
            {
                'passed': bool,
                'score': int (0-100),
                'warnings': list,
                'errors': list,
                'recommendations': list
            }
        """
        warnings = []
        errors = []
        recommendations = []
        score = 100
        
        # 1. Scan name and description
        name = bot_data.get('name', '').lower()
        description = bot_data.get('description', '').lower()
        
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, name) or re.search(pattern, description):
                errors.append(f"Suspicious term detected: '{pattern}'")
                score -= 30
        
        # 2. Validate webhook URL
        webhook_url = bot_data.get('webhook_url', '')
        if webhook_url:
            webhook_issues = cls._scan_webhook_url(webhook_url)
            for issue in webhook_issues:
                if issue['type'] == 'error':
                    errors.append(issue['message'])
                    score -= 20
                else:
                    warnings.append(issue['message'])
                    score -= 10
        else:
            recommendations.append("Consider adding a webhook URL for real-time responses")
        
        # 3. Check permissions
        permissions = bot_data.get('permissions', [])
        if BotPermissions.has_high_risk_scopes(permissions):
            warnings.append("Bot requests high-risk permissions - requires manual review")
            score -= 15
        
        # 4. Check for required fields
        if not bot_data.get('privacy_policy'):
            warnings.append("No privacy policy URL provided")
            score -= 5
            recommendations.append("Add a privacy policy URL for user transparency")
        
        if not bot_data.get('terms_of_service'):
            recommendations.append("Consider adding terms of service URL")
        
        # 5. Check commands
        commands = bot_data.get('commands', [])
        if len(commands) == 0:
            warnings.append("No commands defined - bot may not be useful")
            score -= 5
        
        for cmd in commands:
            if not cmd.get('description'):
                warnings.append(f"Command {cmd.get('command')} has no description")
        
        # Ensure score is in valid range
        score = max(0, min(100, score))
        
        return {
            'passed': len(errors) == 0 and score >= 60,
            'score': score,
            'warnings': warnings,
            'errors': errors,
            'recommendations': recommendations,
            'risk_level': BotPermissions.get_risk_level(permissions),
            'scanned_at': datetime.now().isoformat()
        }
    
    @classmethod
    def _scan_webhook_url(cls, url: str) -> List[dict]:
        """Scan a webhook URL for security issues."""
        issues = []
        
        # Check HTTPS
        if not url.startswith('https://'):
            issues.append({
                'type': 'error',
                'message': 'Webhook URL must use HTTPS'
            })
        
        # Check blocked domains
        for domain in cls.BLOCKED_DOMAINS:
            if domain in url.lower():
                issues.append({
                    'type': 'error',
                    'message': f'Webhook URL contains blocked domain: {domain}'
                })
        
        # Check for valid URL format
        url_pattern = r'^https?://[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(/.*)?$'
        if not re.match(url_pattern, url):
            issues.append({
                'type': 'warning',
                'message': 'Webhook URL format may be invalid'
            })
        
        return issues


# ============================================
# RATE LIMITING
# ============================================

class BotRateLimiter:
    """Rate limiting for bot API calls."""
    
    # Rate limit configurations
    LIMITS = {
        'default': {'requests': 60, 'window': 60},  # 60 req/min
        'premium': {'requests': 300, 'window': 60},  # 300 req/min
        'messages': {'requests': 100, 'window': 3600},  # 100 msg/hour per target
    }
    
    # In-memory rate limit tracking
    _requests: Dict[str, List[float]] = {}
    
    @classmethod
    def check_rate_limit(cls, bot_id: str, limit_type: str = 'default') -> Tuple[bool, dict]:
        """
        Check if a bot is within rate limits.
        
        Returns:
            (allowed: bool, info: dict)
        """
        config = cls.LIMITS.get(limit_type, cls.LIMITS['default'])
        key = f"{bot_id}:{limit_type}"
        now = time.time()
        window = config['window']
        max_requests = config['requests']
        
        # Clean old requests
        if key in cls._requests:
            cls._requests[key] = [t for t in cls._requests[key] if now - t < window]
        else:
            cls._requests[key] = []
        
        current_count = len(cls._requests[key])
        
        if current_count >= max_requests:
            retry_after = window - (now - cls._requests[key][0])
            return False, {
                'allowed': False,
                'limit': max_requests,
                'remaining': 0,
                'reset': int(now + retry_after),
                'retry_after': int(retry_after)
            }
        
        # Record this request
        cls._requests[key].append(now)
        
        return True, {
            'allowed': True,
            'limit': max_requests,
            'remaining': max_requests - current_count - 1,
            'reset': int(now + window)
        }
    
    @classmethod
    def get_rate_limit_headers(cls, info: dict) -> dict:
        """Generate rate limit headers for API responses."""
        return {
            'X-RateLimit-Limit': str(info['limit']),
            'X-RateLimit-Remaining': str(info['remaining']),
            'X-RateLimit-Reset': str(info['reset'])
        }


# ============================================
# RESPONSE CACHING
# ============================================

class BotResponseCache:
    """Cache for external API responses."""
    
    # Cache storage: {key: {'data': ..., 'expires': timestamp}}
    _cache: Dict[str, dict] = {}
    
    # Default TTL in seconds
    DEFAULT_TTL = 30
    
    # TTL by API type
    TTL_CONFIG = {
        'coingecko_price': 30,      # 30 seconds for prices
        'coingecko_trending': 300,   # 5 minutes for trending
        'news': 600,                 # 10 minutes for news
        'default': 60
    }
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get a cached value if not expired."""
        if key not in cls._cache:
            return None
        
        entry = cls._cache[key]
        if time.time() > entry['expires']:
            del cls._cache[key]
            return None
        
        return entry['data']
    
    @classmethod
    def set(cls, key: str, data: Any, ttl_type: str = 'default') -> None:
        """Cache a value with appropriate TTL."""
        ttl = cls.TTL_CONFIG.get(ttl_type, cls.DEFAULT_TTL)
        cls._cache[key] = {
            'data': data,
            'expires': time.time() + ttl,
            'cached_at': time.time()
        }
    
    @classmethod
    def invalidate(cls, key: str) -> None:
        """Remove a key from cache."""
        if key in cls._cache:
            del cls._cache[key]
    
    @classmethod
    def clear_expired(cls) -> int:
        """Clear all expired entries. Returns count of cleared entries."""
        now = time.time()
        expired_keys = [k for k, v in cls._cache.items() if now > v['expires']]
        for key in expired_keys:
            del cls._cache[key]
        return len(expired_keys)
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get cache statistics."""
        now = time.time()
        total = len(cls._cache)
        expired = sum(1 for v in cls._cache.values() if now > v['expires'])
        return {
            'total_entries': total,
            'active_entries': total - expired,
            'expired_entries': expired
        }


# ============================================
# PREMIUM ACCESS CONTROL
# ============================================

class PremiumFeatures:
    """Control access to premium features."""
    
    # Feature flags
    FEATURES = {
        'bot_store_access': {
            'name': 'Bot Store Access',
            'description': 'Access to browse and add bots',
            'tier': 'premium'
        },
        'bot_creation': {
            'name': 'Create Custom Bots',
            'description': 'Create and publish your own bots',
            'tier': 'premium'
        },
        'unlimited_bots': {
            'name': 'Unlimited Bots',
            'description': 'Add unlimited bots to groups',
            'tier': 'premium',
            'free_limit': 2
        },
        'api_access': {
            'name': 'Bot API Access',
            'description': 'Access to the Bot API for developers',
            'tier': 'premium'
        },
        'priority_support': {
            'name': 'Priority Bot Support',
            'description': 'Faster bot approval and support',
            'tier': 'premium'
        },
        'analytics': {
            'name': 'Bot Analytics',
            'description': 'Detailed usage analytics for your bots',
            'tier': 'premium'
        }
    }
    
    @classmethod
    def check_access(cls, username: str, feature: str, store=None) -> Tuple[bool, str]:
        """
        Check if user has access to a premium feature.
        
        Returns:
            (has_access: bool, reason: str)
        """
        if feature not in cls.FEATURES:
            return False, "Unknown feature"
        
        feature_config = cls.FEATURES[feature]
        
        # Check if user is premium
        if store:
            user = store.get_user(username)
            if user and user.get('premium', False):
                return True, "Premium user"
            
            # Check for free tier limits
            if 'free_limit' in feature_config:
                # Could check actual usage here
                pass
        
        # For now, return based on tier requirement
        if feature_config['tier'] == 'free':
            return True, "Free feature"
        
        return False, "Premium subscription required"
    
    @classmethod
    def require_premium(cls, feature: str):
        """Decorator to require premium access for a route."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                from webapp.models.store import store
                
                username = session.get('username')
                if not username:
                    return redirect(url_for('auth.login'))
                
                has_access, reason = cls.check_access(username, feature, store)
                
                if not has_access:
                    if request.is_json:
                        return jsonify({
                            'error': 'Premium required',
                            'feature': feature,
                            'message': reason
                        }), 403
                    flash(f'This feature requires a premium subscription: {reason}', 'error')
                    return redirect(url_for('settings.upgrade'))
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator


# ============================================
# BOT VERSIONING
# ============================================

class BotVersioning:
    """Handle bot versioning for updates and rollbacks."""
    
    @staticmethod
    def generate_version() -> str:
        """Generate a new version string."""
        return f"1.0.{int(time.time())}"
    
    @staticmethod
    def parse_version(version: str) -> Tuple[int, int, int]:
        """Parse a version string into components."""
        parts = version.split('.')
        return (
            int(parts[0]) if len(parts) > 0 else 0,
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0
        )
    
    @staticmethod
    def compare_versions(v1: str, v2: str) -> int:
        """
        Compare two versions.
        Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        p1 = BotVersioning.parse_version(v1)
        p2 = BotVersioning.parse_version(v2)
        
        for a, b in zip(p1, p2):
            if a < b:
                return -1
            if a > b:
                return 1
        return 0
    
    @staticmethod
    def create_version_snapshot(bot_data: dict) -> dict:
        """Create a snapshot of bot configuration for versioning."""
        return {
            'version': bot_data.get('version', '1.0.0'),
            'name': bot_data.get('name'),
            'description': bot_data.get('description'),
            'commands': bot_data.get('commands', []),
            'permissions': bot_data.get('permissions', []),
            'webhook_url': bot_data.get('webhook_url'),
            'created_at': datetime.now().isoformat()
        }


# ============================================
# BOT ANALYTICS
# ============================================

class BotAnalytics:
    """Track and analyze bot usage."""
    
    # In-memory analytics (in production, use database)
    _events: Dict[str, List[dict]] = {}
    
    @classmethod
    def track_event(cls, bot_id: str, event_type: str, data: dict = None) -> None:
        """Track an analytics event."""
        if bot_id not in cls._events:
            cls._events[bot_id] = []
        
        cls._events[bot_id].append({
            'type': event_type,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 1000 events per bot
        if len(cls._events[bot_id]) > 1000:
            cls._events[bot_id] = cls._events[bot_id][-1000:]
    
    @classmethod
    def get_stats(cls, bot_id: str, days: int = 7) -> dict:
        """Get usage statistics for a bot."""
        if bot_id not in cls._events:
            return {
                'total_events': 0,
                'command_count': 0,
                'unique_users': 0,
                'top_commands': []
            }
        
        events = cls._events[bot_id]
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter to time window
        recent_events = [
            e for e in events 
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        # Calculate stats
        command_events = [e for e in recent_events if e['type'] == 'command']
        users = set(e['data'].get('user') for e in recent_events if e['data'].get('user'))
        
        # Count commands
        command_counts = {}
        for e in command_events:
            cmd = e['data'].get('command', 'unknown')
            command_counts[cmd] = command_counts.get(cmd, 0) + 1
        
        top_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_events': len(recent_events),
            'command_count': len(command_events),
            'unique_users': len(users),
            'top_commands': [{'command': c, 'count': n} for c, n in top_commands],
            'period_days': days
        }
    
    @classmethod
    def get_daily_breakdown(cls, bot_id: str, days: int = 7) -> List[dict]:
        """Get daily breakdown of usage."""
        if bot_id not in cls._events:
            return []
        
        events = cls._events[bot_id]
        daily = {}
        
        for e in events:
            date = e['timestamp'][:10]  # Get YYYY-MM-DD
            if date not in daily:
                daily[date] = {'date': date, 'events': 0, 'commands': 0}
            daily[date]['events'] += 1
            if e['type'] == 'command':
                daily[date]['commands'] += 1
        
        # Sort by date and return last N days
        result = sorted(daily.values(), key=lambda x: x['date'], reverse=True)
        return result[:days]

