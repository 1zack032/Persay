# 🔐 Persay - Simple & Secure Encryption

A beginner-friendly encryption app built for learning and practical use.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Encrypt Your First Message

```bash
python persay.py encrypt "Hello World" --name my_first_secret
```

### 3. View Your Saved Secrets

```bash
python persay.py list
```

### 4. Decrypt Your Message

```bash
python persay.py decrypt my_first_secret
```

---

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `encrypt` | Encrypt a message | `python persay.py encrypt "secret"` |
| `decrypt` | Decrypt a message | `python persay.py decrypt vault_name` |
| `list` | Show all vaults | `python persay.py list` |
| `delete` | Delete a vault | `python persay.py delete vault_name` |
| `encrypt-file` | Encrypt a file | `python persay.py encrypt-file doc.txt` |
| `decrypt-file` | Decrypt a file | `python persay.py decrypt-file doc.txt.enc` |

---

## Examples

### Encrypt a Message

```bash
# Interactive (prompts for password)
python persay.py encrypt "My secret diary entry"

# Save to keystore
python persay.py encrypt "My secret" --name diary

# With password inline (less secure)
python persay.py encrypt "My secret" -p mypassword
```

### Decrypt a Message

```bash
# From keystore
python persay.py decrypt diary

# Raw data with salt
python persay.py decrypt "gAAAAABl..." --salt "a1b2c3..."
```

### Encrypt Files

```bash
# Encrypt a file
python persay.py encrypt-file secret.txt --name important_doc

# Decrypt it later
python persay.py decrypt-file secret.txt.enc --salt important_doc
```

---

## Project Structure

```
Persay/
├── persay.py           # 🚀 Main entry point
├── requirements.txt    # 📦 Dependencies
├── README.md           # 📖 This file
├── keystore.json       # 🔑 Your saved vaults (auto-created)
├── src/
│   ├── cli.py          # 🖥️ Command line interface
│   └── core/
│       ├── encryptor.py    # 🔐 Encryption logic (AES-256)
│       └── keystore.py     # 💾 Vault storage
└── lessons/            # 📚 Learning materials
    ├── 01-what-is-encryption.md
    └── 02-setup-and-first-code.md
```

---

## How It Works

### The Encryption Process

```
Your Password + Random Salt
          ↓
    Key Derivation (PBKDF2)
          ↓
    Strong 256-bit Key
          ↓
    AES Encryption (Fernet)
          ↓
    Encrypted Data + Salt
```

### Security Features

- **AES-256**: Industry-standard symmetric encryption
- **PBKDF2**: 480,000 iterations for key derivation
- **Random Salt**: Each encryption is unique
- **Fernet**: Authenticated encryption (tamper-proof)

---

## Learn More

Check out the `lessons/` folder for step-by-step tutorials:

1. `01-what-is-encryption.md` - Basics of encryption
2. `02-setup-and-first-code.md` - Your first code

---

## Security Notes

⚠️ **Important:**
- Never share your password
- The `keystore.json` file contains encrypted data (safe) but reveals vault names
- Use strong passwords (12+ characters, mixed case, numbers, symbols)
- This app is for learning - for production use, consider established tools

---

Made with ❤️ for learning encryption

