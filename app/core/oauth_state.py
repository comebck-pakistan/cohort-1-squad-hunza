"""
Stateless, signed OAuth `state` parameter - CSRF protection for OAuth flows
without needing Redis/a DB table to remember anything.

Instead of storing a random nonce and looking it up on callback, we sign a
(timestamp + random nonce + optional payload) tuple with HMAC-SHA256 using
JWT_SECRET_KEY. On callback we just recompute the signature and check it
matches + hasn't expired. If someone tampers with the value, the signature
check fails.

The optional `extra` payload is what lets /gmail/callback know which user
initiated the connect flow, even though Google's redirect back doesn't carry
an Authorization header - the user_id rides inside the signed state instead.
Used with no `extra` (empty string), this is exactly what the login flow uses.
"""
import hashlib
import hmac
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode

from app.core.config import get_settings

settings = get_settings()

STATE_TTL_SECONDS = 600  # 10 minutes to complete the consent flow


def _sign(payload: str) -> str:
    return hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_state(extra: str = "") -> str:
    """`extra` must not contain ':' - a uuid (like a user_id) is safe as-is."""
    nonce = secrets.token_urlsafe(16)
    timestamp = str(int(time.time()))
    payload = f"{timestamp}:{nonce}:{extra}"
    signature = _sign(payload)
    raw = f"{payload}:{signature}"
    return urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def verify_state(state: str) -> tuple[bool, str]:
    """Returns (is_valid, extra). `extra` is '' if none was set or verification failed."""
    try:
        raw = urlsafe_b64decode(state.encode("utf-8")).decode("utf-8")
        timestamp_str, nonce, extra, signature = raw.rsplit(":", 3)
    except (ValueError, UnicodeDecodeError, Exception):
        return False, ""

    payload = f"{timestamp_str}:{nonce}:{extra}"
    expected_signature = _sign(payload)

    if not hmac.compare_digest(signature, expected_signature):
        return False, ""

    issued_at = int(timestamp_str)
    if time.time() - issued_at > STATE_TTL_SECONDS:
        return False, ""

    return True, extra
