# Lesson 2: Setting Up & Your First Encryption Code 💻

## What We'll Do Today

1. ✅ Make sure Python is installed
2. ✅ Create our project folder structure
3. ✅ Write a Caesar Cipher (just like the Romans!)
4. ✅ Encrypt and decrypt real messages

---

## Step 1: Check if Python is Installed

Open your terminal and type:

```bash
python3 --version
```

You should see something like:
```
Python 3.10.0
```

**If you don't have Python:**
- Mac: It usually comes pre-installed, or get it from python.org
- Windows: Download from python.org

---

## Step 2: Understanding Our First Code

Before we write code, let's understand what we're building:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   INPUT:   "HELLO"  +  Key: 3                          │
│                                                         │
│   PROCESS: Shift each letter by 3                       │
│            H → K                                        │
│            E → H                                        │
│            L → O                                        │
│            L → O                                        │
│            O → R                                        │
│                                                         │
│   OUTPUT:  "KHOOR"                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Step 3: The Caesar Cipher - Line by Line

Let me explain each part like you're 5 years old:

### Part 1: The Alphabet

```python
alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
```

**What this does:** Creates a list of all letters. Think of it as a row of 26 boxes, each with a letter inside.

```
Box 0  → A
Box 1  → B
Box 2  → C
...
Box 25 → Z
```

---

### Part 2: The Encrypt Function

```python
def encrypt(message, key):
```

**What this does:** Creates a "recipe" called `encrypt` that needs two ingredients:
- `message` = what you want to hide ("HELLO")
- `key` = how many spots to shift (3)

---

### Part 3: The Loop

```python
for letter in message:
```

**What this does:** Goes through each letter one at a time.

Like reading a word letter by letter:
```
H-E-L-L-O
↓ ↓ ↓ ↓ ↓
First we handle H
Then we handle E
Then we handle L
... and so on
```

---

### Part 4: Finding and Shifting

```python
position = alphabet.find(letter)
new_position = (position + key) % 26
```

**What this does:**

1. `find(letter)` = "Which box is this letter in?"
   - H is in box 7
   
2. `position + key` = "Move forward by the key"
   - Box 7 + 3 = Box 10
   
3. `% 26` = "If we go past Z, wrap around to A"
   - This is like a clock! After 12 comes 1, not 13.

**Example with wrapping:**
```
X is in box 23
23 + 3 = 26
26 % 26 = 0  (wrap around!)
Box 0 = A

So X → A when shifted by 3!
```

---

## Step 4: The Complete Code!

Here's the full program. Don't worry, we'll run it together:

```python
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
```

---

## Step 5: Run Your Code!

1. Save the code as `caesar_cipher.py`
2. Open terminal in your project folder
3. Run it:

```bash
python3 caesar_cipher.py
```

**You should see:**
```
🔐 CAESAR CIPHER DEMO
==============================

Original message:  HELLO WORLD
Secret key:        3
Encrypted message: KHOOR ZRUOG

Decrypted back:    HELLO WORLD

✅ Success! The message was encrypted and decrypted correctly!
```

---

## 🎮 Try It Yourself!

### Challenge 1: Change the message
Edit this line to encrypt your own message:
```python
original = "YOUR SECRET MESSAGE HERE"
```

### Challenge 2: Change the key
Try different keys (1-25):
```python
secret_key = 7  # Try 7 instead of 3!
```

### Challenge 3: Crack a code!
Someone encrypted this message with key = 5:
```
MJQQT BTWQI
```
Can you decrypt it? (Hint: Use the decrypt function!)

<details>
<summary>Click for answer</summary>

It says: **HELLO WORLD**

To decrypt with key 5, you shift backwards by 5:
- M → H
- J → E
- Q → L
- Q → L
- T → O

</details>

---

## What Each Part Does - Summary

| Code | What it does (simple) |
|------|----------------------|
| `def encrypt(...)` | Creates the "encrypt" recipe |
| `for letter in message` | Looks at each letter one by one |
| `alphabet.find(letter)` | Finds which box the letter is in (0-25) |
| `(position + key) % 26` | Shifts forward, wraps around if needed |
| `alphabet[new_position]` | Gets the new shifted letter |
| `result = result + ...` | Builds up the encrypted message |

---

## Why This Encryption is WEAK 🚨

The Caesar Cipher is great for learning, but it's **super easy to crack!**

Why?
- There are only 26 possible keys
- A computer can try all 26 in less than a second
- Patterns in language make it easy to guess

**In real life, we use:**
- AES-256 = 2²⁵⁶ possible keys (that's a number with 77 digits!)
- Would take longer than the age of the universe to crack

---

## Key Vocabulary - New Words!

| Word | Simple Meaning |
|------|----------------|
| `def` | "Define" - creates a new recipe/function |
| `for` | "For each" - do something to every item |
| `%` (modulo) | "Remainder" - helps us wrap around |
| `if/else` | "If this, then that" - makes decisions |
| `return` | "Give back" - the function's answer |

---

## What's Next?

In Lesson 3, we'll:
1. 🔧 Install REAL encryption libraries
2. 🔐 Use AES-256 (industry-standard encryption!)
3. 🛡️ Learn why proper encryption is different

---

## Quick Quiz! 🎯

**Q1:** If you encrypt "ABC" with key=1, what do you get?

<details>
<summary>Answer</summary>

**BCD** - Each letter shifts forward by 1

</details>

**Q2:** What does `% 26` do?

<details>
<summary>Answer</summary>

It makes the position "wrap around" - so after Z (position 25), we go back to A (position 0). Like how a clock goes from 12 back to 1!

</details>

**Q3:** Why is decrypting the same as encrypting with a negative key?

<details>
<summary>Answer</summary>

If you shift forward 3 to encrypt, you shift backward 3 to decrypt. Going backward 3 is the same as going forward -3!

</details>

---

*Ready for Lesson 3? Just say the word!* 🚀

