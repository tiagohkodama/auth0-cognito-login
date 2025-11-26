import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash a token using SHA256"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_state_parameter() -> str:
    """Generate OAuth2 state parameter for CSRF protection"""
    return generate_secure_token(32)


def verify_state_hash(state: str, stored_hash: str) -> bool:
    """Verify OAuth2 state parameter"""
    return hash_token(state) == stored_hash
