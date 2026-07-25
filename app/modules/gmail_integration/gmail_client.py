"""
Thin wrapper over the Gmail REST API (raw httpx calls rather than Google's
heavier google-api-python-client, to keep this dependency-light). Talks in
plain dicts - no Gmail-specific types leak outside this file.
"""
import base64
from email.utils import parsedate_to_datetime

import httpx

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


async def get_profile(access_token: str) -> dict:
    """Returns {emailAddress, messagesTotal, historyId, ...} - used to confirm which mailbox was connected."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{GMAIL_API_BASE}/profile", headers=_auth_header(access_token))
        resp.raise_for_status()
        return resp.json()


async def list_message_ids(access_token: str, query: str | None = None, max_results: int = 20) -> list[str]:
    params = {"maxResults": max_results}
    if query:
        params["q"] = query
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{GMAIL_API_BASE}/messages", headers=_auth_header(access_token), params=params)
        resp.raise_for_status()
        data = resp.json()
        return [m["id"] for m in data.get("messages", [])]


async def get_message(access_token: str, message_id: str) -> dict:
    """Fetches one message and parses it into the shape our `emails` table expects."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{GMAIL_API_BASE}/messages/{message_id}",
            headers=_auth_header(access_token),
            params={"format": "full"},
        )
        resp.raise_for_status()
        return _parse_message(resp.json())


def _auth_header(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def _parse_message(raw: dict) -> dict:
    headers = {h["name"].lower(): h["value"] for h in raw.get("payload", {}).get("headers", [])}
    sender_name, sender_email = _parse_from_header(headers.get("from", ""))

    return {
        "gmail_message_id": raw["id"],
        "gmail_thread_id": raw.get("threadId"),
        "sender_email": sender_email,
        "sender_name": sender_name,
        "subject": headers.get("subject"),
        "body_text": _extract_body_text(raw.get("payload", {})),
        "received_at": _parse_date(headers.get("date")),
        "has_attachment": _has_attachment(raw.get("payload", {})),
    }


def _parse_from_header(from_header: str) -> tuple[str | None, str | None]:
    # "Jane Doe <jane@example.com>" -> ("Jane Doe", "jane@example.com")
    if "<" in from_header and ">" in from_header:
        name = from_header.split("<")[0].strip().strip('"') or None
        email = from_header.split("<")[1].split(">")[0].strip()
        return name, email
    return None, from_header.strip() or None


def _parse_date(date_header: str | None) -> str | None:
    if not date_header:
        return None
    try:
        return parsedate_to_datetime(date_header).isoformat()
    except (TypeError, ValueError):
        return None


def _extract_body_text(payload: dict) -> str:
    """Walks Gmail's (possibly nested multipart) payload for the plain-text body."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode_b64url(payload["body"]["data"])

    for part in payload.get("parts", []):
        text = _extract_body_text(part)
        if text:
            return text

    # Fall back to whatever body data exists at this level (e.g. no text/plain part found)
    body_data = payload.get("body", {}).get("data")
    return _decode_b64url(body_data) if body_data else ""


def _has_attachment(payload: dict) -> bool:
    for part in payload.get("parts", []):
        if part.get("filename"):
            return True
        if _has_attachment(part):
            return True
    return False


def _decode_b64url(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
