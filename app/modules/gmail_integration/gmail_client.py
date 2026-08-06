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


async def send_message(access_token: str, to: str, subject: str, body_text: str, thread_id: str | None = None) -> dict:
    """Sends a reply via Gmail. Passing thread_id keeps it in the same Gmail conversation as the original email."""
    raw = _build_raw_message(to=to, subject=subject, body_text=body_text)
    payload = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{GMAIL_API_BASE}/messages/send",
            headers=_auth_header(access_token),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


def _build_raw_message(to: str, subject: str, body_text: str) -> str:
    import email.mime.text
    msg = email.mime.text.MIMEText(body_text)
    msg["to"] = to
    msg["subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")


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


async def get_attachment(access_token: str, message_id: str, attachment_id: str) -> bytes:
    """Downloads attachment bytes from Gmail API."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{GMAIL_API_BASE}/messages/{message_id}/attachments/{attachment_id}",
            headers=_auth_header(access_token)
        )
        resp.raise_for_status()
        data = resp.json().get("data", "")
        padded = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded)


def get_attachment_info(payload: dict) -> list[dict]:
    """
    Returns list of attachment info dicts from email payload.
    Each dict has: filename, attachment_id, mime_type
    """
    attachments = []
    for part in payload.get("parts", []):
        if part.get("filename") and part.get("body", {}).get("attachmentId"):
            attachments.append({
                "filename": part["filename"],
                "attachment_id": part["body"]["attachmentId"],
                "mime_type": part.get("mimeType", "")
            })
        # check nested parts
        if part.get("parts"):
            attachments.extend(get_attachment_info(part))
    return attachments

async def list_new_message_ids(access_token: str, start_history_id: str) -> list[str]:
    """
    Uses Gmail history.list to find message IDs added since start_history_id.
    This is what makes Pub/Sub notifications useful — without this we'd
    know something changed but not what.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{GMAIL_API_BASE}/history",
            headers=_auth_header(access_token),
            params={
                "startHistoryId": start_history_id,
                "historyTypes": "messageAdded"
            }
        )
        resp.raise_for_status()
        data = resp.json()

    message_ids = []
    for record in data.get("history", []):
        for msg in record.get("messagesAdded", []):
            message_ids.append(msg["message"]["id"])

    return message_ids

async def watch(access_token: str, topic_name: str) -> dict:
    """
    Registers this mailbox with Gmail's push notification system, pointed at
    our Pub/Sub topic. Must be renewed periodically - Google says watches
    expire after 7 days, so this needs re-calling (e.g. via a daily Celery
    beat task) or notifications silently stop.
    Returns {historyId, expiration} on success.
    """
    payload = {
        "topicName": topic_name,
        "labelIds": ["INBOX"],
        "labelFilterAction": "include",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{GMAIL_API_BASE}/watch",
            headers=_auth_header(access_token),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()