# app/core/security.py
"""Centralized security module - Single source of truth for JWT"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext

# Load the JWT secret - YOUR .env has JWT_SECRET, not SECRET_KEY
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this").strip('"')
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip('"')
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Password context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

print(f"[SECURITY] Initialized with JWT_SECRET: {JWT_SECRET[:30]}...")
print(f"[SECURITY] Algorithm: {JWT_ALGORITHM}")
print(f"[SECURITY] Expiration: {JWT_EXPIRATION_HOURS} hours")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"[SECURITY] Password verification error: {e}")
        return False


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("[SECURITY] Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[SECURITY] Invalid token: {e}")
        return None
    except Exception as e:
        print(f"[SECURITY] Token error: {e}")
        return None


def generate_password_reset_token() -> str:
    """Generate password reset token"""
    import secrets

    return secrets.token_urlsafe(32)


def generate_random_password(length: int = 12) -> str:
    """Generate random password"""
    import string
    import random

    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(characters) for _ in range(length))


# Export all
__all__ = [
    "verify_password",
    "hash_password",
    "create_access_token",
    "verify_token",
    "generate_password_reset_token",
    "generate_random_password",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "JWT_EXPIRATION_HOURS",
]
