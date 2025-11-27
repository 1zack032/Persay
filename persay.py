#!/usr/bin/env python3
"""
🔐 PERSAY - Your Simple Encryption App

This is the main entry point. Run this file to use the app!

USAGE:
------
python persay.py encrypt "Hello World"
python persay.py decrypt my_vault
python persay.py list
python persay.py --help
"""

from src.cli import cli

if __name__ == "__main__":
    cli()

