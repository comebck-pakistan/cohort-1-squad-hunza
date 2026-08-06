import httpx
from urllib.parse import urlencode

from app.core.config import get_settings

settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# gmail.modify covers read + label changes (needed for Feature 1's category
# labels); gmail.send is separate and only needed once the drafts module
# actually sends replies. Requesting it now avoids a second re-consent later.
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


def build_gmail_auth_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "state": state,
        "access_type": "offline",   # required to get a refresh_token back
        "prompt": "consent",        # forces Google to re-issue a refresh_token even on repeat connects
        "include_granted_scopes": "true",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_gmail_tokens(code: str) -> dict:
    """Returns Google's token response: access_token, refresh_token, expires_in, ..."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GMAIL_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_gmail_access_token(refresh_token: str) -> dict:
    """Google access tokens expire (~1hr) - exchange the stored refresh_token for a fresh one before each API call."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code != 200:
            print(f"GOOGLE TOKEN REFRESH FAILED: {resp.status_code} - {resp.text}")
        resp.raise_for_status()
        return resp.json()
