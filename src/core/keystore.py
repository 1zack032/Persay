"""
🔑 Keystore Module - Managing Your Secrets

This module helps you save and load encryption data safely.

SIMPLE EXPLANATION:
==================
When you encrypt something, you get:
1. The encrypted data (scrambled message)
2. The salt (random bytes used to make the key)

You need BOTH to decrypt later!

This module helps you:
- Save encrypted data with its salt
- Load it back later
- Keep everything organized in one file
"""

import json
import os
from datetime import datetime


class Keystore:
    """
    A simple storage system for encrypted data.
    
    Think of it like a safe deposit box:
    - Each "vault" has a name
    - Each vault stores encrypted data + the salt needed to decrypt
    - Everything is saved to a JSON file
    
    EXAMPLE:
    --------
    keystore = Keystore("my_secrets.json")
    keystore.save("my_diary", encrypted_data, salt)
    
    Later:
    data, salt = keystore.load("my_diary")
    """
    
    def __init__(self, filepath: str = "keystore.json"):
        """
        Create or open a keystore.
        
        filepath: Where to save the keystore file
        """
        self.filepath = filepath
        self.data = self._load_file()
    
    def _load_file(self) -> dict:
        """
        Load existing keystore or create empty one.
        
        Returns: Dictionary of all stored vaults
        """
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {"vaults": {}}
    
    def _save_file(self):
        """
        Save the keystore to disk.
        
        This happens automatically when you add/remove vaults.
        """
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def save(self, name: str, encrypted_data: str, salt: str, description: str = ""):
        """
        Save encrypted data to the keystore.
        
        name: A name for this vault (like "my_diary" or "passwords")
        encrypted_data: The scrambled message
        salt: The salt needed to decrypt (as hex string)
        description: Optional note about what this is
        
        EXAMPLE:
        --------
        keystore.save(
            name="bank_password",
            encrypted_data="gAAAAABl2x3...",
            salt="a3f8b2c1...",
            description="My bank account password"
        )
        """
        self.data["vaults"][name] = {
            "encrypted": encrypted_data,
            "salt": salt,
            "description": description,
            "created": datetime.now().isoformat(),
        }
        self._save_file()
        print(f"✅ Saved vault: {name}")
    
    def load(self, name: str) -> tuple:
        """
        Load encrypted data from the keystore.
        
        name: The name of the vault to load
        
        Returns: (encrypted_data, salt) tuple
        
        EXAMPLE:
        --------
        encrypted, salt = keystore.load("bank_password")
        # Now you can decrypt it with your password!
        """
        if name not in self.data["vaults"]:
            raise KeyError(f"❌ Vault '{name}' not found!")
        
        vault = self.data["vaults"][name]
        return vault["encrypted"], vault["salt"]
    
    def list_vaults(self) -> list:
        """
        List all vaults in the keystore.
        
        Returns: List of vault information
        
        EXAMPLE:
        --------
        for vault in keystore.list_vaults():
            print(vault["name"], vault["description"])
        """
        vaults = []
        for name, data in self.data["vaults"].items():
            vaults.append({
                "name": name,
                "description": data.get("description", ""),
                "created": data.get("created", "Unknown"),
            })
        return vaults
    
    def delete(self, name: str):
        """
        Delete a vault from the keystore.
        
        name: The name of the vault to delete
        
        ⚠️ WARNING: This is permanent! The encrypted data will be lost!
        """
        if name not in self.data["vaults"]:
            raise KeyError(f"❌ Vault '{name}' not found!")
        
        del self.data["vaults"][name]
        self._save_file()
        print(f"🗑️ Deleted vault: {name}")
    
    def exists(self, name: str) -> bool:
        """
        Check if a vault exists.
        
        name: The name to check
        
        Returns: True if it exists, False if not
        """
        return name in self.data["vaults"]


# ============================================
# QUICK TEST - Run this file directly to test!
# ============================================

if __name__ == "__main__":
    print("🔑 KEYSTORE TEST")
    print("=" * 40)
    print()
    
    # Create a test keystore (in memory, deleted after)
    ks = Keystore("test_keystore.json")
    
    # Save some test data
    print("📝 Saving test vaults...")
    ks.save(
        name="test_secret",
        encrypted_data="gAAAAABl2x3fake_encrypted_data_here",
        salt="a1b2c3d4e5f6",
        description="This is a test vault"
    )
    
    ks.save(
        name="another_secret",
        encrypted_data="gAAAAABl2x3another_fake_data",
        salt="1a2b3c4d5e6f",
        description="Another test vault"
    )
    
    # List all vaults
    print("\n📋 Listing all vaults:")
    for vault in ks.list_vaults():
        print(f"  - {vault['name']}: {vault['description']}")
    
    # Load one back
    print("\n📤 Loading 'test_secret':")
    encrypted, salt = ks.load("test_secret")
    print(f"  Encrypted: {encrypted[:30]}...")
    print(f"  Salt: {salt}")
    
    # Clean up test file
    os.remove("test_keystore.json")
    print("\n✅ Test completed! (test file cleaned up)")

