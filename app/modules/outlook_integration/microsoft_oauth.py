import httpx
from urllib.parse import urlencode

from app.core.config import get_settings

settings = get_settings()

# common (multi-tenant + personal accounts) endpoint - works for both
# work/school and personal outlook.com/hotmail.com accounts
MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

# Mail.Send is separate from Mail.Read/ReadWrite; offline_access is required
# to get a refresh_token back (same purpose as Gmail's access_type=offline)
OUTLOOK_SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read",
]


def build_outlook_auth_url(state: str) -> str:
    params = {
        "client_id": settings.OUTLOOK_CLIENT_ID,
        "redirect_uri": settings.OUTLOOK_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(OUTLOOK_SCOPES),
        "state": state,
        "response_mode": "query",
        "prompt": "select_account",  # lets the user pick which Outlook account to connect
    }
    return f"{MICROSOFT_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_outlook_tokens(code: str) -> dict:
    """Returns Microsoft's token response: access_token, refresh_token, expires_in, ..."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            MICROSOFT_TOKEN_URL,
            data={
                "client_id": settings.OUTLOOK_CLIENT_ID,
                "client_secret": settings.OUTLOOK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.OUTLOOK_REDIRECT_URI,
                "grant_type": "authorization_code",
                "scope": " ".join(OUTLOOK_SCOPES),
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_outlook_access_token(refresh_token: str) -> dict:
    """Microsoft access tokens expire (~1hr) - exchange the stored refresh_token for a fresh one before each API call."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            MICROSOFT_TOKEN_URL,
            data={
                "client_id": settings.OUTLOOK_CLIENT_ID,
                "client_secret": settings.OUTLOOK_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": " ".join(OUTLOOK_SCOPES),
            },
        )
        if resp.status_code != 200:
            print(f"MICROSOFT TOKEN REFRESH FAILED: {resp.status_code} - {resp.text}")
        resp.raise_for_status()
        return resp.json()