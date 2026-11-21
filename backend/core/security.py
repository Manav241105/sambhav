"""
Password hashing, JWT access tokens and opaque refresh tokens.

- Passwords and OTP codes: Argon2id (argon2-cffi).
- Access tokens: short-lived signed JWTs carrying the user id and role.
- Refresh tokens: random opaque strings; only their SHA-256 hash is stored.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from core.settings import get_settings

_hasher = PasswordHasher()


class TokenError(Exception):
    """Raised when an access token is missing, expired or invalid."""


def utcnow() -> datetime:
    return datetime.now(UTC)


# ── Passwords / OTP codes ─────────────────────────────────────────────────────


def hash_secret(plain: str) -> str:
    return _hasher.hash(plain)


def verify_secret(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return _hasher.verify(hashed, plain)
    except (VerificationError, InvalidHashError):
        return False


def generate_otp() -> str:
    """Six-digit numeric code from a CSPRNG."""
    return f"{secrets.randbelow(1_000_000):06d}"


# ── Access tokens (JWT) ───────────────────────────────────────────────────────


def create_access_token(user_id: int, role: str, extra: dict[str, Any] | None = None) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": int(utcnow().timestamp()),
        "exp": int(expires_at.timestamp()),
        **(extra or {}),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token expired") from exc
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid token") from exc
    if payload.get("type") != "access" or "sub" not in payload:
        raise TokenError("Invalid token type")
    return payload


# ── Refresh tokens (opaque) ───────────────────────────────────────────────────


def new_refresh_token() -> tuple[str, str, datetime]:
    """Return (plain token for the client, hash to store, expiry)."""
    plain = secrets.token_urlsafe(48)
    expires_at = utcnow() + timedelta(days=get_settings().refresh_token_ttl_days)
    return plain, hash_token(plain), expires_at


def hash_token(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()
