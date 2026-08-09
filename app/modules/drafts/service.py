from fastapi import HTTPException, status

from app.core.crypto import decrypt
from app.modules.drafts import repository as repo
from app.modules.emails import repository as emails_repo
from app.modules.gmail_integration import gmail_client
from app.modules.gmail_integration import repository as gmail_repo
from app.modules.gmail_integration.google_oauth import refresh_gmail_access_token


def _get_owned_draft(draft_id: str, user_id: str) -> tuple[dict, dict]:
    """Returns (draft, email), raising 404 if the draft doesn't exist or
    doesn't belong to this user (via the email it's attached to - email_drafts
    has no user_id column of its own, so ownership is checked through emails)."""
    draft = repo.get_draft_by_id(draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    email = emails_repo.get_email_by_id(draft["email_id"], user_id)
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    return draft, email


def edit_draft(draft_id: str, new_body: str, user_id: str) -> dict:
    """
    DRAFT-04: HR edits the AI-generated draft before sending. The correction
    (original vs. new text) is logged to draft_corrections regardless of
    whether they end up sending it - this is what builds the feedback trail
    for future prompt tuning.
    """
    draft, _email = _get_owned_draft(draft_id, user_id)

    if draft["status"] == "sent":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a draft that has already been sent")

    repo.log_correction(draft_id, original_text=draft["draft_body"], corrected_text=new_body)
    return repo.update_draft_body(draft_id, new_body, status="edited")


async def approve_and_send_draft(draft_id: str, user_id: str) -> dict:
    """
    DRAFT-03: HR clicks approve -> the current draft_body (whatever it is,
    original or edited) is sent as a real Gmail reply, threaded into the
    original conversation. On success, marks the draft sent AND resolves the
    email out of the needs-attention queue (QUEUE-02) automatically, since a
    reply just went out - the recruiter shouldn't have to also remember to
    dismiss it separately.
    """
    draft, email = _get_owned_draft(draft_id, user_id)

    if draft["status"] == "sent":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This draft has already been sent")

    if not email.get("sender_email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Original email has no sender address to reply to")

    connections = gmail_repo.list_connections_for_user(user_id)

    # Prefer the exact connection this email arrived through (tracked via
    # emails.gmail_connection_id) - sending from the wrong account fails with
    # a 404 from Gmail since the thread_id won't exist in that mailbox.
    # Falls back to "any active connection" for older emails inserted before
    # this column existed.
    active = next(
        (c for c in connections if c["id"] == email.get("gmail_connection_id") and c["is_active"]),
        None,
    )
    if not active:
        active = next((c for c in connections if c["is_active"]), None)

    if not active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active Gmail connection to send from. Connect a mailbox via /gmail/connect first.",
        )

    refresh_token = decrypt(active["refresh_token"])
    google_tokens = await refresh_gmail_access_token(refresh_token)
    access_token = google_tokens["access_token"]

    subject = email.get("subject") or "(no subject)"
    reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

    sent = await gmail_client.send_message(
        access_token=access_token,
        to=email["sender_email"],
        subject=reply_subject,
        body_text=draft["draft_body"],
        thread_id=email.get("gmail_thread_id"),
    )

    updated_draft = repo.mark_approved_and_sent(draft_id, gmail_draft_id=sent.get("id"))

    from app.modules.queue import repository as queue_repo
    queue_repo.resolve_email(email["id"])

    return updated_draft