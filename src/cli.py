"""
🖥️ Command Line Interface - Talk to Your App!

This is how you interact with the encryption app from the terminal.

WHAT IS A CLI?
=============
CLI = Command Line Interface

Instead of clicking buttons, you type commands:
    python cli.py encrypt "Hello World" --password secret123

Think of it like giving orders:
    "Hey app, ENCRYPT this MESSAGE using this PASSWORD"

COMMANDS AVAILABLE:
==================
1. encrypt  - Encrypt a message or file
2. decrypt  - Decrypt a message or file
3. list     - Show all saved vaults
4. delete   - Delete a vault
"""

import click
import getpass
import sys
import os

# Add the parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.encryptor import Encryptor
from src.core.keystore import Keystore


# Create the main group of commands
# Think of this as the "menu" of our app
@click.group()
@click.version_option(version="1.0.0", prog_name="Persay")
def cli():
    """
    🔐 PERSAY - Simple & Secure Encryption
    
    Encrypt your messages and files with strong AES-256 encryption!
    
    \b
    QUICK START:
    ------------
    Encrypt a message:  persay encrypt "Hello World"
    Decrypt a message:  persay decrypt vault_name
    List all vaults:    persay list
    
    \b
    EXAMPLES:
    ---------
    # Encrypt text and save it
    persay encrypt "My secret message" --name diary
    
    # Encrypt a file
    persay encrypt-file secret.txt --name important_file
    
    # Decrypt later
    persay decrypt diary
    """
    pass


@cli.command()
@click.argument("message")
@click.option("--name", "-n", help="Name to save this as (optional)")
@click.option("--password", "-p", help="Password (will prompt if not provided)")
def encrypt(message: str, name: str, password: str):
    """
    🔒 Encrypt a message.
    
    MESSAGE is the text you want to encrypt.
    
    \b
    EXAMPLES:
    ---------
    # Basic encryption (shows result)
    persay encrypt "Hello World"
    
    # Save to keystore with a name
    persay encrypt "Hello World" --name greeting
    
    # Provide password directly (less secure)
    persay encrypt "Hello World" -p mypassword
    """
    # Get password securely if not provided
    if not password:
        password = getpass.getpass("🔑 Enter password: ")
        password_confirm = getpass.getpass("🔑 Confirm password: ")
        
        if password != password_confirm:
            click.echo("❌ Passwords don't match!")
            return
    
    # Encrypt the message
    enc = Encryptor()
    result = enc.encrypt(message, password)
    
    click.echo()
    click.echo("✅ Message encrypted successfully!")
    click.echo()
    
    # If a name was provided, save to keystore
    if name:
        ks = Keystore()
        ks.save(name, result["encrypted"], result["salt"])
        click.echo(f"💾 Saved as '{name}' in keystore")
    else:
        # Show the encrypted data
        click.echo("📦 Encrypted data:")
        click.echo(f"   {result['encrypted']}")
        click.echo()
        click.echo("🧂 Salt (SAVE THIS!):")
        click.echo(f"   {result['salt']}")
        click.echo()
        click.echo("⚠️  You need BOTH the encrypted data AND salt to decrypt!")


@cli.command()
@click.argument("name_or_data")
@click.option("--salt", "-s", help="Salt value (if not using keystore)")
@click.option("--password", "-p", help="Password (will prompt if not provided)")
def decrypt(name_or_data: str, salt: str, password: str):
    """
    🔓 Decrypt a message.
    
    NAME_OR_DATA is either:
    - A vault name (if saved to keystore)
    - The encrypted data string (if using --salt)
    
    \b
    EXAMPLES:
    ---------
    # Decrypt from keystore
    persay decrypt greeting
    
    # Decrypt raw data with salt
    persay decrypt "gAAAAABl..." --salt "a1b2c3..."
    """
    # Get password
    if not password:
        password = getpass.getpass("🔑 Enter password: ")
    
    enc = Encryptor()
    
    # Check if it's a vault name or raw data
    ks = Keystore()
    
    if ks.exists(name_or_data):
        # It's a vault name - load from keystore
        encrypted_data, salt = ks.load(name_or_data)
        click.echo(f"📂 Loaded vault: {name_or_data}")
    elif salt:
        # It's raw encrypted data with salt provided
        encrypted_data = name_or_data
    else:
        click.echo("❌ Vault not found and no --salt provided!")
        click.echo("   Either use a vault name or provide --salt with raw data")
        return
    
    try:
        # Decrypt!
        decrypted = enc.decrypt(encrypted_data, password, salt)
        click.echo()
        click.echo("✅ Decryption successful!")
        click.echo()
        click.echo("📝 Your message:")
        click.echo(f"   {decrypted}")
    except Exception as e:
        click.echo()
        click.echo("❌ Decryption failed!")
        click.echo("   Possible reasons:")
        click.echo("   - Wrong password")
        click.echo("   - Wrong salt")
        click.echo("   - Corrupted data")


@cli.command("list")
def list_vaults():
    """
    📋 List all saved vaults.
    
    Shows all encrypted items saved in your keystore.
    """
    ks = Keystore()
    vaults = ks.list_vaults()
    
    if not vaults:
        click.echo("📭 No vaults found. Encrypt something first!")
        return
    
    click.echo()
    click.echo("🗄️ YOUR VAULTS")
    click.echo("=" * 50)
    
    for vault in vaults:
        click.echo()
        click.echo(f"📦 {vault['name']}")
        if vault['description']:
            click.echo(f"   📝 {vault['description']}")
        click.echo(f"   📅 Created: {vault['created'][:10]}")
    
    click.echo()
    click.echo(f"Total: {len(vaults)} vault(s)")


@cli.command()
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def delete(name: str, force: bool):
    """
    🗑️ Delete a vault.
    
    NAME is the vault to delete.
    
    ⚠️ WARNING: This is permanent!
    """
    ks = Keystore()
    
    if not ks.exists(name):
        click.echo(f"❌ Vault '{name}' not found!")
        return
    
    if not force:
        click.echo(f"⚠️  Are you sure you want to delete '{name}'?")
        click.echo("   This cannot be undone!")
        confirm = click.prompt("   Type the vault name to confirm")
        
        if confirm != name:
            click.echo("❌ Deletion cancelled.")
            return
    
    ks.delete(name)
    click.echo(f"✅ Vault '{name}' deleted.")


@cli.command("encrypt-file")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output file path (default: adds .enc)")
@click.option("--name", "-n", help="Name to save in keystore")
@click.option("--password", "-p", help="Password (will prompt if not provided)")
def encrypt_file(filepath: str, output: str, name: str, password: str):
    """
    🔒 Encrypt a file.
    
    FILEPATH is the file to encrypt.
    
    \b
    EXAMPLES:
    ---------
    # Encrypt a file
    persay encrypt-file secret.txt
    
    # Specify output name
    persay encrypt-file secret.txt -o hidden.enc
    
    # Save salt to keystore
    persay encrypt-file secret.txt --name my_file
    """
    if not password:
        password = getpass.getpass("🔑 Enter password: ")
        password_confirm = getpass.getpass("🔑 Confirm password: ")
        
        if password != password_confirm:
            click.echo("❌ Passwords don't match!")
            return
    
    # Default output path
    if not output:
        output = filepath + ".enc"
    
    enc = Encryptor()
    salt = enc.encrypt_file(filepath, output, password)
    
    click.echo()
    click.echo(f"✅ File encrypted: {output}")
    
    if name:
        ks = Keystore()
        ks.save(name, f"FILE:{output}", salt, f"Encrypted file: {filepath}")
        click.echo(f"💾 Salt saved as '{name}' in keystore")
    else:
        click.echo()
        click.echo("🧂 Salt (SAVE THIS!):")
        click.echo(f"   {salt}")
        click.echo()
        click.echo("⚠️  You need this salt to decrypt the file!")


@cli.command("decrypt-file")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output file path (default: removes .enc)")
@click.option("--salt", "-s", help="Salt value (or vault name)")
@click.option("--password", "-p", help="Password (will prompt if not provided)")
def decrypt_file(filepath: str, output: str, salt: str, password: str):
    """
    🔓 Decrypt a file.
    
    FILEPATH is the encrypted file.
    
    \b
    EXAMPLES:
    ---------
    # Decrypt using salt from keystore
    persay decrypt-file secret.txt.enc --salt my_file
    
    # Decrypt using raw salt
    persay decrypt-file secret.txt.enc --salt "a1b2c3..."
    """
    if not salt:
        click.echo("❌ Please provide --salt (vault name or salt value)")
        return
    
    if not password:
        password = getpass.getpass("🔑 Enter password: ")
    
    # Check if salt is a vault name
    ks = Keystore()
    if ks.exists(salt):
        _, salt_value = ks.load(salt)
        salt = salt_value
    
    # Default output path
    if not output:
        if filepath.endswith(".enc"):
            output = filepath[:-4] + ".decrypted"
        else:
            output = filepath + ".decrypted"
    
    try:
        enc = Encryptor()
        enc.decrypt_file(filepath, output, password, salt)
        click.echo()
        click.echo(f"✅ File decrypted: {output}")
    except Exception as e:
        click.echo()
        click.echo("❌ Decryption failed!")
        click.echo("   Check your password and salt.")


# Entry point
if __name__ == "__main__":
    cli()

