"""
Encrypts the Gmail refresh token before it's stored in gmail_connections.
A DB leak (backup, misconfigured RLS, SQL injection elsewhere) shouldn't
directly hand out live access to someone's Gmail inbox - this is the one
thing standing between "leaked row" and "leaked row + attacker can read/send
mail as that account", so it's worth the small overhead.

Fernet is symmetric encryption (not hashing, unlike refresh_tokens for our
own JWT auth) because we need the plaintext back out to call the Gmail API.
"""
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


@lru_cache
def _cipher() -> Fernet:
    return Fernet(get_settings().GMAIL_TOKEN_ENCRYPTION_KEY.encode("utf-8"))


def encrypt(raw: str) -> str:
    return _cipher().encrypt(raw.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    try:
        return _cipher().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("Could not decrypt stored Gmail token - was GMAIL_TOKEN_ENCRYPTION_KEY rotated?") from e
