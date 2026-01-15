# Menza Backend (Persay)

**Secure Encrypted Messaging Platform - Backend API**

A privacy-first messaging application featuring end-to-end encryption, real-time communication, voice/video calling, and channel broadcasting.

> **📱 Looking for the iOS app?** See the [Menza iOS repository](https://github.com/1zack032/menza)

---

## Features

### Core Messaging
- **End-to-End Encryption** - AES-256 encryption for all messages
- **Real-time Chat** - Instant messaging with WebSocket technology
- **Group Messaging** - Create and manage group conversations
- **Shared Notes** - Encrypted collaborative notes with secret phrase protection

### Channels
- **Public Channels** - Create discoverable content channels
- **Channel Roles** - Admin, Moderator, and Viewer permissions
- **Rich Content** - Support for formatted posts, reactions, and comments
- **Channel Discovery** - Browse trending, popular, and new channels

### Voice & Video
- **1-on-1 Calls** - Private voice and video calls
- **Group Calls** - Multi-participant voice/video conferences
- **Channel Broadcasts** - Role-based call permissions for channels

### Security & Privacy
- **No Required Email/Phone** - Register with just username and password
- **Seed Phrase Recovery** - 12-word recovery phrase for account backup
- **Message Auto-Delete** - Configurable message expiration
- **Privacy Controls** - Granular privacy settings

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, Flask, Flask-SocketIO |
| Database | MongoDB Atlas |
| Real-time | WebSockets |
| Encryption | AES-256, PBKDF2, Fernet |
| Voice/Video | WebRTC |
| Deployment | Render, Gunicorn |

---

## Project Structure

```
menza/
├── app.py                  # Application entry point
├── wsgi.py                 # WSGI server configuration
├── run.py                  # Local development server
├── requirements.txt        # Python dependencies
├── Procfile                # Deployment configuration
├── runtime.txt             # Python version
├── render.yaml             # Render deployment config
├── LICENSE                 # Proprietary license
├── COPYRIGHT               # Copyright notice
└── webapp/
    ├── app.py              # Flask application factory
    ├── config.py           # Configuration settings
    ├── models/
    │   └── store.py        # Data models & MongoDB integration
    ├── routes/
    │   ├── auth.py         # Authentication (login, register, recovery)
    │   ├── main.py         # Main routes (home, chat)
    │   ├── channels.py     # Channel management
    │   ├── settings.py     # User settings
    │   ├── legal.py        # Legal pages
    │   └── docs.py         # Documentation routes
    ├── sockets/
    │   ├── messaging.py    # Real-time messaging events
    │   ├── channels.py     # Channel socket events
    │   └── calls.py        # Voice/video call signaling
    ├── static/
    │   ├── css/            # Stylesheets
    │   ├── icons/          # PWA icons
    │   ├── manifest.json   # PWA manifest
    │   └── sw.js           # Service worker
    └── templates/          # HTML templates
        ├── chat.html       # Main chat interface
        ├── channels.html   # Channel browsing
        ├── settings.html   # User settings
        └── docs/           # Documentation pages
```

---

## Installation

### Prerequisites
- Python 3.10+
- MongoDB Atlas account (free tier available)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/1zack032/Persay.git
   cd Persay
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your MongoDB URI and secret key
   ```

5. **Run locally**
   ```bash
   python run.py
   ```

   Access at `http://localhost:5000`

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB Atlas connection string | Yes |
| `SECRET_KEY` | Flask session secret key | Yes |
| `FLASK_ENV` | Environment (development/production) | No |
| `FLASK_DEBUG` | Enable debug mode | No |

---

## Deployment

### Render (Recommended)

1. Connect GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy automatically on push

### Manual Deployment

```bash
gunicorn --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT app:app
```

---

## API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | POST | Create new account |
| `/login` | POST | User login |
| `/logout` | GET | User logout |
| `/recover` | POST | Account recovery |

### Messaging
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | GET | Main chat interface |
| `/api/users/search` | GET | Search users |
| `/api/users/contacts` | GET | Get user contacts |

### Channels
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/channels` | GET | Browse channels |
| `/channels/create` | GET/POST | Create channel |
| `/channels/<id>` | GET | View channel |
| `/channels/<id>/settings` | GET/POST | Channel settings |

---

## Security

- All messages encrypted with AES-256
- Passwords hashed with PBKDF2 (480,000 iterations)
- WebSocket connections secured
- HTTPS enforced in production
- No tracking or analytics
- GDPR and CCPA compliant design

---

## Legal

- **Privacy Policy**: Available at `/docs/privacy`
- **Terms of Service**: Available at `/docs/terms`
- **Cookie Policy**: Available at `/docs/privacy/cookies`

---

## License

Copyright 2024-2025 Menza. All Rights Reserved.

This is proprietary software. See [LICENSE](LICENSE) for details.

---

## Contact

For business inquiries: zakriasharif@gmail.com

---

*Built with privacy in mind.*
