"""
Thin wrapper over Microsoft Graph API (raw httpx calls, mirroring the
gmail_client.py pattern). Returns the same dict shapes as gmail_client so
the rest of the pipeline (classify_and_save, resume processing, embedding)
works identically regardless of provider.
"""
import base64
from datetime import datetime, timedelta, timezone

import httpx

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


async def get_profile(access_token: str) -> dict:
    """Returns {mail, userPrincipalName, ...} - used to confirm which mailbox was connected."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{GRAPH_API_BASE}/me", headers=_auth_header(access_token))
        resp.raise_for_status()
        return resp.json()


async def list_message_ids(access_token: str, max_results: int = 20) -> list[str]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{GRAPH_API_BASE}/me/messages",
            headers=_auth_header(access_token),
            params={"$top": max_results, "$select": "id"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [m["id"] for m in data.get("value", [])]


async def get_message(access_token: str, message_id: str) -> dict:
    """Fetches one message and parses it into the shape our `emails` table expects."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{GRAPH_API_BASE}/me/messages/{message_id}",
            headers=_auth_header(access_token),
        )
        resp.raise_for_status()
        return _parse_message(resp.json())


async def send_message(access_token: str, to: str, subject: str, body_text: str, thread_id: str | None = None) -> dict:
    """
    Sends a reply via Graph API. thread_id (Graph's conversationId) isn't
    directly settable on a new message the way Gmail's threadId is - true
    threading requires replying to the original message via
    /me/messages/{id}/reply instead. For a first pass this sends a new
    message; upgrade to /reply once thread_id is wired through from the caller.
    """
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body_text},
            "toRecipients": [{"emailAddress": {"address": to}}],
        }
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{GRAPH_API_BASE}/me/sendMail",
            headers=_auth_header(access_token),
            json=payload,
        )
        resp.raise_for_status()
        # sendMail returns 202 Accepted with no body
        return {"status": "sent"}


def _auth_header(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def _parse_message(raw: dict) -> dict:
    sender = raw.get("from", {}).get("emailAddress", {})
    sender_email = sender.get("address")
    sender_name = sender.get("name")

    return {
        "provider_message_id": raw["id"],
        "gmail_thread_id": raw.get("conversationId"),  # reused field name; holds Graph's conversationId
        "sender_email": sender_email,
        "sender_name": sender_name,
        "subject": raw.get("subject"),
        "body_text": _extract_body_text(raw),
        "received_at": raw.get("receivedDateTime"),  # already ISO 8601, matches Gmail's parsed format
        "has_attachment": raw.get("hasAttachments", False),
    }


def _extract_body_text(raw: dict) -> str:
    body = raw.get("body", {})
    content = body.get("content", "")
    content_type = body.get("contentType", "text")

    if content_type == "html":
        # crude strip - good enough for classification/embedding; a proper
        # HTML-to-text library can replace this if formatting matters later
        import re
        text = re.sub(r"<[^>]+>", " ", content)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    return content.strip()


async def get_attachment(access_token: str, message_id: str, attachment_id: str) -> bytes:
    """Downloads attachment bytes from Graph API."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{GRAPH_API_BASE}/me/messages/{message_id}/attachments/{attachment_id}",
            headers=_auth_header(access_token),
        )
        resp.raise_for_status()
        data = resp.json()
        content_bytes = data.get("contentBytes", "")
        return base64.b64decode(content_bytes)


def get_attachment_info(message_raw: dict) -> list[dict]:
    """
    Returns list of attachment info dicts, matching gmail_client's shape.
    Graph requires a separate call to list attachments (not embedded in the
    message payload like Gmail), so this expects message_raw to include an
    expanded "attachments" field - see list_attachments() below.
    """
    attachments = []
    for att in message_raw.get("attachments", []):
        if att.get("@odata.type") == "#microsoft.graph.fileAttachment":
            attachments.append({
                "filename": att.get("name", ""),
                "attachment_id": att.get("id"),
                "mime_type": att.get("contentType", ""),
            })
    return attachments


async def list_attachments(access_token: str, message_id: str) -> list[dict]:
    """
    Graph doesn't embed attachment metadata in the base message payload the
    way Gmail does - fetch it separately, then pass through get_attachment_info
    for a consistent shape.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{GRAPH_API_BASE}/me/messages/{message_id}/attachments",
            headers=_auth_header(access_token),
        )
        resp.raise_for_status()
        data = resp.json()
        return get_attachment_info({"attachments": data.get("value", [])})


async def create_subscription(access_token: str, notification_url: str) -> dict:
    """
    Graph's equivalent of Gmail's watch() - registers a webhook subscription
    for new mail. Subscriptions expire (max ~4230 minutes / ~3 days for mail
    resources) and must be renewed, similar to Gmail's 7-day watch expiration.
    Returns {id, expirationDateTime, ...} on success.
    """
    expiration = (datetime.now(timezone.utc) + timedelta(minutes=4200)).isoformat().replace("+00:00", "Z")
    payload = {
        "changeType": "created",
        "notificationUrl": notification_url,
        "resource": "me/mailFolders('Inbox')/messages",
        "expirationDateTime": expiration,
        "clientState": "sortdesk-outlook-webhook",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{GRAPH_API_BASE}/subscriptions",
            headers=_auth_header(access_token),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def renew_subscription(access_token: str, subscription_id: str) -> dict:
    """Extends an existing subscription's expiration - call this before it expires."""
    expiration = (datetime.now(timezone.utc) + timedelta(minutes=4200)).isoformat().replace("+00:00", "Z")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.patch(
            f"{GRAPH_API_BASE}/subscriptions/{subscription_id}",
            headers=_auth_header(access_token),
            json={"expirationDateTime": expiration},
        )
        resp.raise_for_status()
        return resp.json()