"""Utility helpers — hashing, token generation, input validation."""

import hashlib
import secrets
import re


def hash_password(password):
    """Hash a password with a random salt (SHA-256, hex-encoded).

    Format: salt$hash  where salt is 16 hex chars.
    """
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(password, stored):
    """Check a password against a stored salt$hash string."""
    salt, expected = stored.split("$", 1)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return h == expected


def generate_token():
    """Generate a cryptographically random session token."""
    return secrets.token_hex(32)


def is_valid_username(username):
    """Usernames: 3-30 chars, alphanumeric + underscores only."""
    return bool(re.match(r"^[a-zA-Z0-9_]{3,30}$", username))


def is_valid_email(email):
    """Basic email format check."""
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def sanitize_input(text):
    """Strip leading/trailing whitespace and limit length."""
    if not isinstance(text, str):
        return ""
    return text.strip()[:500]
