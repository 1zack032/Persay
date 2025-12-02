"""
💎 Premium Features Module

All premium features for Menza including:
- Custom fonts
- Animated emojis
- Expressions/stickers
- Chat themes
- And more!
"""

from typing import Dict, List, Optional
from datetime import datetime

# ============================================
# PREMIUM FONTS
# ============================================

PREMIUM_FONTS = {
    # Standard (Free)
    'space-grotesk': {
        'name': 'Space Grotesk',
        'family': "'Space Grotesk', sans-serif",
        'preview': 'The quick brown fox jumps',
        'premium': False,
        'category': 'modern'
    },
    
    # Premium Fonts
    'playfair': {
        'name': 'Playfair Display',
        'family': "'Playfair Display', serif",
        'preview': 'Elegant & Sophisticated',
        'premium': True,
        'category': 'elegant',
        'google_font': 'Playfair+Display:wght@400;500;600;700'
    },
    'jetbrains': {
        'name': 'JetBrains Mono',
        'family': "'JetBrains Mono', monospace",
        'preview': 'console.log("Hello");',
        'premium': True,
        'category': 'code',
        'google_font': 'JetBrains+Mono:wght@400;500;600;700'
    },
    'dancing-script': {
        'name': 'Dancing Script',
        'family': "'Dancing Script', cursive",
        'preview': 'Beautiful handwriting',
        'premium': True,
        'category': 'handwriting',
        'google_font': 'Dancing+Script:wght@400;500;600;700'
    },
    'bebas-neue': {
        'name': 'Bebas Neue',
        'family': "'Bebas Neue', sans-serif",
        'preview': 'BOLD HEADLINES',
        'premium': True,
        'category': 'display',
        'google_font': 'Bebas+Neue'
    },
    'comfortaa': {
        'name': 'Comfortaa',
        'family': "'Comfortaa', cursive",
        'preview': 'Rounded & Friendly',
        'premium': True,
        'category': 'rounded',
        'google_font': 'Comfortaa:wght@400;500;600;700'
    },
    'cinzel': {
        'name': 'Cinzel',
        'family': "'Cinzel', serif",
        'preview': 'ANCIENT ROMAN STYLE',
        'premium': True,
        'category': 'elegant',
        'google_font': 'Cinzel:wght@400;500;600;700'
    },
    'permanent-marker': {
        'name': 'Permanent Marker',
        'family': "'Permanent Marker', cursive",
        'preview': 'Hand-drawn vibes',
        'premium': True,
        'category': 'handwriting',
        'google_font': 'Permanent+Marker'
    },
    'press-start': {
        'name': 'Press Start 2P',
        'family': "'Press Start 2P', cursive",
        'preview': 'RETRO GAMING',
        'premium': True,
        'category': 'retro',
        'google_font': 'Press+Start+2P'
    },
    'abril-fatface': {
        'name': 'Abril Fatface',
        'family': "'Abril Fatface', cursive",
        'preview': 'Bold & Beautiful',
        'premium': True,
        'category': 'display',
        'google_font': 'Abril+Fatface'
    },
    'monoton': {
        'name': 'Monoton',
        'family': "'Monoton', cursive",
        'preview': 'NEON LIGHTS',
        'premium': True,
        'category': 'display',
        'google_font': 'Monoton'
    },
}

FONT_CATEGORIES = {
    'modern': {'name': 'Modern', 'icon': '✨'},
    'elegant': {'name': 'Elegant', 'icon': '👑'},
    'code': {'name': 'Code', 'icon': '💻'},
    'handwriting': {'name': 'Handwriting', 'icon': '✍️'},
    'display': {'name': 'Display', 'icon': '🎨'},
    'rounded': {'name': 'Rounded', 'icon': '⭕'},
    'retro': {'name': 'Retro', 'icon': '🕹️'},
}

# ============================================
# ANIMATED EMOJIS (LIVE EMOJIS)
# ============================================

LIVE_EMOJIS = {
    # Reactions
    'love-burst': {
        'name': 'Love Burst',
        'static': '❤️',
        'animation': 'pulse-grow',
        'category': 'love',
        'premium': True
    },
    'fire-burn': {
        'name': 'Fire Burning',
        'static': '🔥',
        'animation': 'flame-flicker',
        'category': 'reactions',
        'premium': True
    },
    'sparkle-shine': {
        'name': 'Sparkle',
        'static': '✨',
        'animation': 'twinkle',
        'category': 'reactions',
        'premium': True
    },
    'rocket-launch': {
        'name': 'Rocket Launch',
        'static': '🚀',
        'animation': 'launch-shake',
        'category': 'reactions',
        'premium': True
    },
    'party-pop': {
        'name': 'Party Popper',
        'static': '🎉',
        'animation': 'confetti-burst',
        'category': 'celebration',
        'premium': True
    },
    'money-rain': {
        'name': 'Money Rain',
        'static': '💰',
        'animation': 'rain-fall',
        'category': 'money',
        'premium': True
    },
    'diamond-shine': {
        'name': 'Diamond',
        'static': '💎',
        'animation': 'shine-rotate',
        'category': 'premium',
        'premium': True
    },
    'crown-glow': {
        'name': 'Crown',
        'static': '👑',
        'animation': 'golden-glow',
        'category': 'premium',
        'premium': True
    },
    'lightning-strike': {
        'name': 'Lightning',
        'static': '⚡',
        'animation': 'flash-strike',
        'category': 'reactions',
        'premium': True
    },
    'heart-float': {
        'name': 'Floating Hearts',
        'static': '💕',
        'animation': 'float-up',
        'category': 'love',
        'premium': True
    },
    'eyes-look': {
        'name': 'Looking Eyes',
        'static': '👀',
        'animation': 'look-around',
        'category': 'reactions',
        'premium': True
    },
    'clap-hands': {
        'name': 'Clapping',
        'static': '👏',
        'animation': 'clap-motion',
        'category': 'reactions',
        'premium': True
    },
    'thumbs-bounce': {
        'name': 'Thumbs Up',
        'static': '👍',
        'animation': 'bounce-up',
        'category': 'reactions',
        'premium': True
    },
    'laugh-shake': {
        'name': 'Laughing',
        'static': '😂',
        'animation': 'shake-laugh',
        'category': 'emotions',
        'premium': True
    },
    'mind-blown': {
        'name': 'Mind Blown',
        'static': '🤯',
        'animation': 'explode-head',
        'category': 'reactions',
        'premium': True
    },
    'star-spin': {
        'name': 'Spinning Star',
        'static': '⭐',
        'animation': 'spin-glow',
        'category': 'reactions',
        'premium': True
    },
    'gem-sparkle': {
        'name': 'Gem',
        'static': '💠',
        'animation': 'sparkle-rotate',
        'category': 'premium',
        'premium': True
    },
    'moon-phase': {
        'name': 'Moon Phases',
        'static': '🌙',
        'animation': 'phase-cycle',
        'category': 'nature',
        'premium': True
    },
    'sun-rays': {
        'name': 'Sun Rays',
        'static': '☀️',
        'animation': 'ray-pulse',
        'category': 'nature',
        'premium': True
    },
    'wave-hello': {
        'name': 'Waving Hand',
        'static': '👋',
        'animation': 'wave-motion',
        'category': 'greetings',
        'premium': True
    },
}

EMOJI_ANIMATIONS_CSS = """
/* Live Emoji Animations */
@keyframes pulse-grow {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.3); }
}

@keyframes flame-flicker {
    0%, 100% { transform: scaleY(1) rotate(-3deg); opacity: 1; }
    25% { transform: scaleY(1.1) rotate(3deg); opacity: 0.9; }
    50% { transform: scaleY(0.95) rotate(-2deg); opacity: 1; }
    75% { transform: scaleY(1.05) rotate(2deg); opacity: 0.95; }
}

@keyframes twinkle {
    0%, 100% { opacity: 1; transform: scale(1) rotate(0deg); }
    25% { opacity: 0.7; transform: scale(0.9) rotate(10deg); }
    50% { opacity: 1; transform: scale(1.1) rotate(-5deg); }
    75% { opacity: 0.8; transform: scale(0.95) rotate(5deg); }
}

@keyframes launch-shake {
    0% { transform: translateY(0) rotate(0deg); }
    25% { transform: translateY(-5px) rotate(-5deg); }
    50% { transform: translateY(-10px) rotate(5deg); }
    75% { transform: translateY(-5px) rotate(-3deg); }
    100% { transform: translateY(0) rotate(0deg); }
}

@keyframes confetti-burst {
    0% { transform: scale(1); }
    50% { transform: scale(1.2) rotate(10deg); }
    100% { transform: scale(1) rotate(-5deg); }
}

@keyframes rain-fall {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(3px) rotate(5deg); }
}

@keyframes shine-rotate {
    0% { transform: rotate(0deg); filter: brightness(1); }
    50% { transform: rotate(180deg); filter: brightness(1.3); }
    100% { transform: rotate(360deg); filter: brightness(1); }
}

@keyframes golden-glow {
    0%, 100% { filter: drop-shadow(0 0 3px gold); }
    50% { filter: drop-shadow(0 0 10px gold); }
}

@keyframes flash-strike {
    0%, 90%, 100% { opacity: 1; transform: scale(1); }
    95% { opacity: 0.3; transform: scale(1.2); }
}

@keyframes float-up {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
}

@keyframes look-around {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-3px); }
    75% { transform: translateX(3px); }
}

@keyframes clap-motion {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-10deg); }
    75% { transform: rotate(10deg); }
}

@keyframes bounce-up {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-5px) scale(1.1); }
}

@keyframes shake-laugh {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-5deg); }
    75% { transform: rotate(5deg); }
}

@keyframes explode-head {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.15); filter: brightness(1.2); }
}

@keyframes spin-glow {
    0% { transform: rotate(0deg); filter: brightness(1); }
    100% { transform: rotate(360deg); filter: brightness(1.2); }
}

@keyframes sparkle-rotate {
    0%, 100% { transform: rotate(0deg) scale(1); }
    50% { transform: rotate(180deg) scale(1.1); }
}

@keyframes phase-cycle {
    0%, 100% { opacity: 1; filter: brightness(1); }
    50% { opacity: 0.7; filter: brightness(0.8); }
}

@keyframes ray-pulse {
    0%, 100% { transform: scale(1); filter: brightness(1); }
    50% { transform: scale(1.1); filter: brightness(1.3); }
}

@keyframes wave-motion {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(20deg); }
    75% { transform: rotate(-10deg); }
}

.live-emoji {
    display: inline-block;
    animation-duration: 1s;
    animation-iteration-count: infinite;
    animation-timing-function: ease-in-out;
}
"""

# ============================================
# EXPRESSIONS / STICKER PACKS
# ============================================

STICKER_PACKS = {
    'crypto-traders': {
        'name': 'Crypto Traders',
        'description': 'For the moon boys and diamond hands',
        'icon': '📈',
        'premium': True,
        'stickers': [
            {'id': 'to-the-moon', 'name': 'To The Moon', 'emoji': '🚀🌙'},
            {'id': 'diamond-hands', 'name': 'Diamond Hands', 'emoji': '💎🙌'},
            {'id': 'wen-lambo', 'name': 'Wen Lambo', 'emoji': '🏎️💨'},
            {'id': 'buy-dip', 'name': 'Buy The Dip', 'emoji': '📉🛒'},
            {'id': 'hodl', 'name': 'HODL', 'emoji': '💪📊'},
            {'id': 'whale-alert', 'name': 'Whale Alert', 'emoji': '🐋🚨'},
            {'id': 'pump-it', 'name': 'Pump It', 'emoji': '📈⬆️'},
            {'id': 'rekt', 'name': 'REKT', 'emoji': '💀📉'},
        ]
    },
    'reactions-deluxe': {
        'name': 'Reactions Deluxe',
        'description': 'Express yourself with style',
        'icon': '🎭',
        'premium': True,
        'stickers': [
            {'id': 'slow-clap', 'name': 'Slow Clap', 'emoji': '👏😏'},
            {'id': 'mic-drop', 'name': 'Mic Drop', 'emoji': '🎤⬇️'},
            {'id': 'mind-blown', 'name': 'Mind = Blown', 'emoji': '🤯💥'},
            {'id': 'chef-kiss', 'name': 'Chef\'s Kiss', 'emoji': '👨‍🍳💋'},
            {'id': 'big-brain', 'name': 'Big Brain', 'emoji': '🧠✨'},
            {'id': 'this-is-fine', 'name': 'This Is Fine', 'emoji': '🔥🐕'},
            {'id': 'take-my-money', 'name': 'Take My Money', 'emoji': '💵➡️'},
            {'id': 'facepalm', 'name': 'Facepalm', 'emoji': '🤦‍♂️'},
        ]
    },
    'celebration': {
        'name': 'Celebration',
        'description': 'Party time vibes',
        'icon': '🎉',
        'premium': True,
        'stickers': [
            {'id': 'confetti', 'name': 'Confetti Blast', 'emoji': '🎊🎉'},
            {'id': 'champagne', 'name': 'Pop The Champagne', 'emoji': '🍾🥂'},
            {'id': 'fireworks', 'name': 'Fireworks', 'emoji': '🎆✨'},
            {'id': 'trophy', 'name': 'Winner', 'emoji': '🏆👑'},
            {'id': 'cake', 'name': 'Cake Time', 'emoji': '🎂🕯️'},
            {'id': 'balloon', 'name': 'Balloons', 'emoji': '🎈🎈'},
            {'id': 'dance', 'name': 'Dance Party', 'emoji': '💃🕺'},
            {'id': 'cheers', 'name': 'Cheers', 'emoji': '🍻🥳'},
        ]
    },
    'love-vibes': {
        'name': 'Love Vibes',
        'description': 'Spread the love',
        'icon': '💕',
        'premium': True,
        'stickers': [
            {'id': 'heart-eyes', 'name': 'Heart Eyes', 'emoji': '😍❤️'},
            {'id': 'love-letter', 'name': 'Love Letter', 'emoji': '💌💕'},
            {'id': 'kiss', 'name': 'Sending Kiss', 'emoji': '😘💋'},
            {'id': 'hug', 'name': 'Virtual Hug', 'emoji': '🤗💖'},
            {'id': 'couple', 'name': 'Couple Goals', 'emoji': '👫❤️'},
            {'id': 'roses', 'name': 'Roses For You', 'emoji': '🌹💐'},
            {'id': 'cupid', 'name': 'Cupid Arrow', 'emoji': '💘🏹'},
            {'id': 'forever', 'name': 'Forever', 'emoji': '♾️❤️'},
        ]
    },
    'work-life': {
        'name': 'Work Life',
        'description': 'Office humor and hustle',
        'icon': '💼',
        'premium': True,
        'stickers': [
            {'id': 'coffee', 'name': 'Need Coffee', 'emoji': '☕😴'},
            {'id': 'deadline', 'name': 'Deadline Mode', 'emoji': '⏰🔥'},
            {'id': 'meeting', 'name': 'In A Meeting', 'emoji': '📊🤐'},
            {'id': 'done', 'name': 'Task Done', 'emoji': '✅🎉'},
            {'id': 'bug', 'name': 'It\'s A Bug', 'emoji': '🐛💻'},
            {'id': 'friday', 'name': 'Friday Vibes', 'emoji': '🎉📅'},
            {'id': 'grind', 'name': 'On The Grind', 'emoji': '💪📈'},
            {'id': 'brb', 'name': 'BRB', 'emoji': '🏃‍♂️⏳'},
        ]
    },
}

# ============================================
# CHAT THEMES
# ============================================

CHAT_THEMES = {
    # Default (Free)
    'default': {
        'name': 'Default Dark',
        'premium': False,
        'colors': {
            'bg': '#0a0a0f',
            'sidebar': '#06060a',
            'accent': '#7c3aed',
            'text': '#f8fafc'
        }
    },
    
    # Premium Themes
    'midnight-purple': {
        'name': 'Midnight Purple',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #1a0a2e, #16082a)',
            'sidebar': '#0d0418',
            'accent': '#9333ea',
            'text': '#f0e6ff'
        }
    },
    'ocean-blue': {
        'name': 'Ocean Blue',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #0a192f, #0d1f3c)',
            'sidebar': '#051025',
            'accent': '#0ea5e9',
            'text': '#e0f2fe'
        }
    },
    'forest-green': {
        'name': 'Forest Green',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #0a1f0a, #0d2d0d)',
            'sidebar': '#051005',
            'accent': '#22c55e',
            'text': '#dcfce7'
        }
    },
    'sunset-orange': {
        'name': 'Sunset Orange',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #1f0a0a, #2d1010)',
            'sidebar': '#150505',
            'accent': '#f97316',
            'text': '#ffedd5'
        }
    },
    'rose-gold': {
        'name': 'Rose Gold',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #1f0f15, #2d1520)',
            'sidebar': '#150a10',
            'accent': '#ec4899',
            'text': '#fce7f3'
        }
    },
    'cyber-neon': {
        'name': 'Cyber Neon',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #000000, #0a0a1a)',
            'sidebar': '#000005',
            'accent': '#00ff88',
            'text': '#00ff88'
        }
    },
    'golden-luxury': {
        'name': 'Golden Luxury',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #1a1500, #2d2000)',
            'sidebar': '#0f0d00',
            'accent': '#fbbf24',
            'text': '#fef3c7'
        }
    },
    'arctic-frost': {
        'name': 'Arctic Frost',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #0f1729, #1e293b)',
            'sidebar': '#0a1120',
            'accent': '#38bdf8',
            'text': '#e0f2fe'
        }
    },
    'blood-moon': {
        'name': 'Blood Moon',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #1a0505, #2d0a0a)',
            'sidebar': '#100000',
            'accent': '#dc2626',
            'text': '#fecaca'
        }
    },
    'aurora': {
        'name': 'Aurora Borealis',
        'premium': True,
        'colors': {
            'bg': 'linear-gradient(135deg, #0a1628, #1a0f3d, #0a2540)',
            'sidebar': '#050d1a',
            'accent': '#06b6d4',
            'text': '#a5f3fc'
        }
    },
}

# ============================================
# MESSAGE BUBBLE STYLES
# ============================================

MESSAGE_STYLES = {
    'default': {
        'name': 'Default',
        'premium': False,
        'borderRadius': '12px',
        'style': 'solid'
    },
    'rounded': {
        'name': 'Rounded',
        'premium': True,
        'borderRadius': '24px',
        'style': 'solid'
    },
    'sharp': {
        'name': 'Sharp',
        'premium': True,
        'borderRadius': '4px',
        'style': 'solid'
    },
    'gradient': {
        'name': 'Gradient',
        'premium': True,
        'borderRadius': '12px',
        'style': 'gradient'
    },
    'glass': {
        'name': 'Glass',
        'premium': True,
        'borderRadius': '16px',
        'style': 'glass'
    },
    'neon': {
        'name': 'Neon Glow',
        'premium': True,
        'borderRadius': '12px',
        'style': 'neon'
    },
    'outlined': {
        'name': 'Outlined',
        'premium': True,
        'borderRadius': '12px',
        'style': 'outlined'
    },
}

# ============================================
# ALL PREMIUM FEATURES
# ============================================

PREMIUM_FEATURES = {
    # Visual Customization
    'custom_fonts': {
        'name': 'Custom Fonts',
        'description': '10+ premium fonts including elegant, handwriting, and retro styles',
        'icon': '🔤',
        'category': 'visual'
    },
    'live_emojis': {
        'name': 'Live Emojis',
        'description': '20+ animated emoji reactions that bring your chats to life',
        'icon': '✨',
        'category': 'visual'
    },
    'sticker_packs': {
        'name': 'Sticker Packs',
        'description': '5 exclusive sticker packs with 40+ expressions',
        'icon': '🎭',
        'category': 'visual'
    },
    'chat_themes': {
        'name': 'Chat Themes',
        'description': '10 premium themes including Cyber Neon, Rose Gold, and Aurora',
        'icon': '🎨',
        'category': 'visual'
    },
    'message_styles': {
        'name': 'Message Styles',
        'description': 'Custom bubble styles: Glass, Neon, Gradient, and more',
        'icon': '💬',
        'category': 'visual'
    },
    
    # Bot Store
    'bot_store': {
        'name': 'Bot Store Access',
        'description': 'Browse, add, and create custom bots for your groups',
        'icon': '🤖',
        'category': 'bots'
    },
    'bot_creation': {
        'name': 'Create Custom Bots',
        'description': 'Build and publish your own bots with full API access',
        'icon': '🛠️',
        'category': 'bots'
    },
    'bot_analytics': {
        'name': 'Bot Analytics',
        'description': 'Detailed usage stats for your bots',
        'icon': '📊',
        'category': 'bots'
    },
    
    # Communication
    'hd_calls': {
        'name': 'HD Video Calls',
        'description': '1080p video quality for crystal clear calls',
        'icon': '📹',
        'category': 'communication'
    },
    'group_calls': {
        'name': 'Extended Group Calls',
        'description': 'Up to 50 participants in group calls (vs 10 free)',
        'icon': '👥',
        'category': 'communication'
    },
    'voice_messages': {
        'name': 'Extended Voice Messages',
        'description': '10 minute voice messages (vs 2 min free)',
        'icon': '🎙️',
        'category': 'communication'
    },
    'message_scheduling': {
        'name': 'Message Scheduling',
        'description': 'Schedule messages to send later',
        'icon': '⏰',
        'category': 'communication'
    },
    'auto_translate': {
        'name': 'Auto Translation',
        'description': 'Automatically translate messages in 50+ languages',
        'icon': '🌍',
        'category': 'communication'
    },
    
    # Organization
    'chat_folders': {
        'name': 'Chat Folders',
        'description': 'Organize chats into custom folders',
        'icon': '📁',
        'category': 'organization'
    },
    'pin_unlimited': {
        'name': 'Unlimited Pins',
        'description': 'Pin unlimited messages in any chat (vs 5 free)',
        'icon': '📌',
        'category': 'organization'
    },
    'advanced_search': {
        'name': 'Advanced Search',
        'description': 'Search across all chats with filters and date ranges',
        'icon': '🔍',
        'category': 'organization'
    },
    
    # Profile
    'animated_avatar': {
        'name': 'Animated Avatar',
        'description': 'Upload animated GIF avatars',
        'icon': '🖼️',
        'category': 'profile'
    },
    'custom_status': {
        'name': 'Custom Status',
        'description': 'Set custom status with emojis and expiration',
        'icon': '💭',
        'category': 'profile'
    },
    'profile_badge': {
        'name': 'Premium Badge',
        'description': 'Exclusive premium badge on your profile',
        'icon': '💎',
        'category': 'profile'
    },
    
    # Storage
    'cloud_storage': {
        'name': '50GB Cloud Storage',
        'description': 'Store files, media, and backups (vs 2GB free)',
        'icon': '☁️',
        'category': 'storage'
    },
    'file_size': {
        'name': '2GB File Uploads',
        'description': 'Send files up to 2GB (vs 100MB free)',
        'icon': '📦',
        'category': 'storage'
    },
    
    # Privacy
    'disappearing_options': {
        'name': 'Custom Disappearing',
        'description': 'Messages that disappear after 1 hour, 12 hours, or custom time',
        'icon': '👻',
        'category': 'privacy'
    },
    'incognito_mode': {
        'name': 'Incognito Mode',
        'description': 'Hide online status and read receipts from specific contacts',
        'icon': '🕵️',
        'category': 'privacy'
    },
    
    # Support
    'priority_support': {
        'name': 'Priority Support',
        'description': '24/7 priority customer support',
        'icon': '🎧',
        'category': 'support'
    },
    'early_access': {
        'name': 'Early Access',
        'description': 'Get new features before everyone else',
        'icon': '🚀',
        'category': 'support'
    },
}

FEATURE_CATEGORIES = {
    'visual': {'name': 'Visual Customization', 'icon': '🎨'},
    'bots': {'name': 'Bot Store', 'icon': '🤖'},
    'communication': {'name': 'Communication', 'icon': '💬'},
    'organization': {'name': 'Organization', 'icon': '📁'},
    'profile': {'name': 'Profile', 'icon': '👤'},
    'storage': {'name': 'Storage', 'icon': '☁️'},
    'privacy': {'name': 'Privacy', 'icon': '🔒'},
    'support': {'name': 'Support', 'icon': '🎧'},
}

# ============================================
# PRICING TIERS
# ============================================

PRICING_TIERS = {
    'monthly': {
        'price': 9.99,
        'period': 'month',
        'savings': None
    },
    'yearly': {
        'price': 79.99,
        'period': 'year',
        'savings': '33%',
        'monthly_equivalent': 6.67
    },
    'lifetime': {
        'price': 199.99,
        'period': 'lifetime',
        'savings': 'Best Value',
        'monthly_equivalent': None
    }
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_premium_fonts() -> Dict:
    """Get all premium fonts"""
    return {k: v for k, v in PREMIUM_FONTS.items() if v['premium']}

def get_free_fonts() -> Dict:
    """Get all free fonts"""
    return {k: v for k, v in PREMIUM_FONTS.items() if not v['premium']}

def get_fonts_by_category(category: str) -> Dict:
    """Get fonts by category"""
    return {k: v for k, v in PREMIUM_FONTS.items() if v['category'] == category}

def get_live_emojis() -> Dict:
    """Get all live emojis"""
    return LIVE_EMOJIS

def get_sticker_packs() -> Dict:
    """Get all sticker packs"""
    return STICKER_PACKS

def get_chat_themes() -> Dict:
    """Get all chat themes"""
    return CHAT_THEMES

def get_premium_themes() -> Dict:
    """Get premium themes only"""
    return {k: v for k, v in CHAT_THEMES.items() if v['premium']}

def get_message_styles() -> Dict:
    """Get all message styles"""
    return MESSAGE_STYLES

def get_all_features() -> Dict:
    """Get all premium features"""
    return PREMIUM_FEATURES

def get_features_by_category(category: str) -> Dict:
    """Get features by category"""
    return {k: v for k, v in PREMIUM_FEATURES.items() if v['category'] == category}

def get_feature_count() -> int:
    """Get total number of premium features"""
    return len(PREMIUM_FEATURES)

def generate_google_fonts_url() -> str:
    """Generate Google Fonts URL for all premium fonts"""
    fonts = []
    for font_id, font in PREMIUM_FONTS.items():
        if font.get('google_font'):
            fonts.append(font['google_font'])
    
    return f"https://fonts.googleapis.com/css2?family={'&family='.join(fonts)}&display=swap"

