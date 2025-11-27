"""
🔐 Encryptor Module - The Heart of Our App!

This module handles the REAL encryption using AES-256.

SIMPLE EXPLANATION:
==================
Remember the Caesar Cipher? It shifts letters by a number.
AES-256 is like that but MUCH more complex:

- Caesar: 26 possible keys (easy to guess!)
- AES-256: 2^256 possible keys (impossible to guess!)

Think of AES like a super-complicated blender:
1. Put your message in
2. Add your secret password (key)
3. Blend it up in a special way
4. Out comes scrambled data that looks like random garbage

Only someone with the SAME password can "un-blend" it!
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class Encryptor:
    """
    The main encryption class.
    
    HOW IT WORKS (Simple Version):
    ==============================
    
    1. You give it a PASSWORD (like "mysecret123")
    
    2. We turn that password into a STRONG KEY
       - Why? Because "mysecret123" is too simple
       - We "stretch" it into something much stronger
       - This is called "Key Derivation"
    
    3. We use that key to encrypt/decrypt your data
       - Encrypt: readable → scrambled
       - Decrypt: scrambled → readable
    
    WHAT IS SALT?
    =============
    Salt is random data we add to your password before making the key.
    
    Why? So two people with the SAME password get DIFFERENT keys!
    
    Without salt:
        "password123" → always makes key "ABC123..."
        Hackers can pre-compute common passwords!
    
    With salt:
        "password123" + random_salt_1 → key "XYZ789..."
        "password123" + random_salt_2 → key "QRS456..."
        Much harder to crack!
    """
    
    def __init__(self):
        """
        Initialize the encryptor.
        We don't need any setup - everything happens when you encrypt/decrypt.
        """
        pass
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Turn a simple password into a strong encryption key.
        
        SIMPLE EXPLANATION:
        This is like taking a small seed and growing it into a big tree.
        
        password: Your password like "mysecret123"
        salt: Random bytes to make the key unique
        
        Returns: A strong 32-byte key for AES-256
        
        THE PROCESS:
        1. Take your password
        2. Add the salt
        3. Run it through PBKDF2 (a "key stretching" algorithm)
        4. Do this 480,000 times (makes it SLOW for hackers!)
        5. Out comes a strong key
        """
        # PBKDF2 = Password-Based Key Derivation Function 2
        # It's like a meat grinder for passwords - makes them stronger!
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),  # The blending recipe
            length=32,                   # 32 bytes = 256 bits (AES-256!)
            salt=salt,                   # Our random salt
            iterations=480000,           # Do it 480,000 times (slow = secure)
        )
        
        # Convert password to bytes and derive the key
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str, password: str) -> dict:
        """
        Encrypt your data with a password.
        
        data: The message you want to hide (like "Hello World!")
        password: Your secret password
        
        Returns: A dictionary with the encrypted data and salt
        
        WHAT HAPPENS INSIDE:
        ====================
        1. Generate random salt (16 bytes of random garbage)
        2. Turn password + salt into a strong key
        3. Use that key to encrypt your data
        4. Return both the encrypted data AND the salt
           (You need the salt to decrypt later!)
        
        EXAMPLE:
        --------
        Input:  "Hello World!" with password "secret123"
        Output: {
            "encrypted": "gAAAAABl2x3...(long random-looking string)...",
            "salt": "a3f8b2c1...(random bytes as hex)..."
        }
        """
        # Step 1: Generate random salt
        # os.urandom() gives us truly random bytes from your computer
        salt = os.urandom(16)  # 16 bytes = 128 bits of randomness
        
        # Step 2: Turn password into a strong key
        key = self._derive_key(password, salt)
        
        # Step 3: Create the encryption tool (Fernet)
        # Fernet is a high-level encryption recipe that's safe to use
        # It handles all the tricky parts for us!
        fernet = Fernet(key)
        
        # Step 4: Encrypt the data
        # First convert string to bytes, then encrypt
        encrypted_data = fernet.encrypt(data.encode())
        
        # Step 5: Return the results
        # We store salt as hex (human-readable) for easy storage
        return {
            "encrypted": encrypted_data.decode(),  # The scrambled message
            "salt": salt.hex()                      # The salt (needed to decrypt!)
        }
    
    def decrypt(self, encrypted_data: str, password: str, salt_hex: str) -> str:
        """
        Decrypt data back to readable text.
        
        encrypted_data: The scrambled message
        password: The same password used to encrypt
        salt_hex: The salt that was used (as hex string)
        
        Returns: The original message!
        
        WHAT HAPPENS INSIDE:
        ====================
        1. Convert salt from hex back to bytes
        2. Recreate the SAME key from password + salt
        3. Use that key to decrypt
        4. Return the original message
        
        IMPORTANT:
        - You MUST use the same password
        - You MUST use the same salt
        - If either is wrong, decryption FAILS
        """
        # Step 1: Convert salt from hex string back to bytes
        salt = bytes.fromhex(salt_hex)
        
        # Step 2: Recreate the exact same key
        # Same password + same salt = same key!
        key = self._derive_key(password, salt)
        
        # Step 3: Create decryption tool with that key
        fernet = Fernet(key)
        
        # Step 4: Decrypt and return
        decrypted_data = fernet.decrypt(encrypted_data.encode())
        
        # Convert bytes back to string
        return decrypted_data.decode()
    
    def encrypt_file(self, input_path: str, output_path: str, password: str) -> str:
        """
        Encrypt an entire file!
        
        input_path: The file you want to encrypt (like "secret.txt")
        output_path: Where to save the encrypted file (like "secret.txt.enc")
        password: Your secret password
        
        Returns: The salt (you need this to decrypt later!)
        
        HOW IT WORKS:
        1. Read all the bytes from the file
        2. Encrypt those bytes
        3. Save the encrypted bytes to a new file
        """
        # Step 1: Generate salt and derive key
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        
        # Step 2: Read the original file
        with open(input_path, "rb") as file:  # "rb" = read bytes
            original_data = file.read()
        
        # Step 3: Encrypt the data
        encrypted_data = fernet.encrypt(original_data)
        
        # Step 4: Write to the output file
        with open(output_path, "wb") as file:  # "wb" = write bytes
            file.write(encrypted_data)
        
        # Return the salt so user can save it
        return salt.hex()
    
    def decrypt_file(self, input_path: str, output_path: str, password: str, salt_hex: str):
        """
        Decrypt an encrypted file back to normal.
        
        input_path: The encrypted file (like "secret.txt.enc")
        output_path: Where to save the decrypted file (like "secret_recovered.txt")
        password: The same password used to encrypt
        salt_hex: The salt that was used
        """
        # Step 1: Recreate the key
        salt = bytes.fromhex(salt_hex)
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        
        # Step 2: Read the encrypted file
        with open(input_path, "rb") as file:
            encrypted_data = file.read()
        
        # Step 3: Decrypt it
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Step 4: Write the decrypted data
        with open(output_path, "wb") as file:
            file.write(decrypted_data)


# ============================================
# QUICK TEST - Run this file directly to test!
# ============================================

if __name__ == "__main__":
    print("🔐 PERSAY ENCRYPTION TEST")
    print("=" * 40)
    print()
    
    # Create our encryptor
    enc = Encryptor()
    
    # Test message
    secret_message = "Hello! This is my super secret message! 🎉"
    password = "my_secret_password_123"
    
    print(f"📝 Original message: {secret_message}")
    print(f"🔑 Password: {password}")
    print()
    
    # Encrypt it!
    print("🔒 Encrypting...")
    result = enc.encrypt(secret_message, password)
    print(f"📦 Encrypted: {result['encrypted'][:50]}...")
    print(f"🧂 Salt: {result['salt']}")
    print()
    
    # Decrypt it!
    print("🔓 Decrypting...")
    decrypted = enc.decrypt(result["encrypted"], password, result["salt"])
    print(f"📝 Decrypted: {decrypted}")
    print()
    
    # Check if it worked
    if secret_message == decrypted:
        print("✅ SUCCESS! Encryption and decryption worked perfectly!")
    else:
        print("❌ ERROR: Something went wrong!")

