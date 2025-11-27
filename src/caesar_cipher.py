# caesar_cipher.py
# My First Encryption Program!

def encrypt(message, key):
    """
    Encrypts a message using Caesar Cipher.
    
    message: The text you want to hide
    key: How many positions to shift (1-25)
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = ""
    
    # Make the message all uppercase
    message = message.upper()
    
    # Go through each letter
    for letter in message:
        if letter in alphabet:
            # Find where this letter is in the alphabet
            position = alphabet.find(letter)
            
            # Shift it by the key amount
            new_position = (position + key) % 26
            
            # Get the new letter and add it to result
            result = result + alphabet[new_position]
        else:
            # If it's not a letter (like space or !), keep it as is
            result = result + letter
    
    return result


def decrypt(message, key):
    """
    Decrypts a message - just shift backwards!
    """
    # Decrypting is just encrypting with the opposite key
    return encrypt(message, -key)


# ============================================
# Let's test it out!
# ============================================

if __name__ == "__main__":
    # Our secret message
    original = "HELLO WORLD"
    secret_key = 3
    
    print("🔐 CAESAR CIPHER DEMO")
    print("=" * 30)
    print()
    
    # Encrypt it!
    encrypted = encrypt(original, secret_key)
    print(f"Original message:  {original}")
    print(f"Secret key:        {secret_key}")
    print(f"Encrypted message: {encrypted}")
    print()
    
    # Decrypt it!
    decrypted = decrypt(encrypted, secret_key)
    print(f"Decrypted back:    {decrypted}")
    print()
    
    # Did it work?
    if original == decrypted:
        print("✅ Success! The message was encrypted and decrypted correctly!")
    else:
        print("❌ Something went wrong...")

