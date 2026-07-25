from fastapi import HTTPException, status

from app.core.crypto import decrypt, encrypt
from app.modules.emails import repository as emails_repo
from app.modules.gmail_integration import gmail_client, repository as repo
from app.modules.gmail_integration.google_oauth import (
    exchange_code_for_gmail_tokens,
    refresh_gmail_access_token,
)


async def handle_gmail_callback(code: str, user_id: str) -> dict:
    tokens = await exchange_code_for_gmail_tokens(code)
    refresh_token = tokens.get("refresh_token")
    access_token = tokens.get("access_token")

    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gmail token exchange failed")

    if not refresh_token:
        # Google only returns a refresh_token on first-ever consent for this
        # client+account, or when prompt=consent forces re-issue. We always
        # send prompt=consent (see google_oauth.py), so this should be rare -
        # most likely cause is the account previously granted consent and
        # something suppressed the re-prompt.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return a refresh token. Revoke this app's access at "
                   "https://myaccount.google.com/permissions and try connecting again.",
        )

    profile = await gmail_client.get_profile(access_token)
    gmail_address = profile["emailAddress"]

    encrypted = encrypt(refresh_token)
    existing = repo.get_connection_by_user_and_address(user_id, gmail_address)
    if existing:
        connection = repo.reactivate_connection(existing["id"], encrypted)
    else:
        connection = repo.create_connection(user_id, gmail_address, encrypted)

    return connection


def disconnect(connection_id: str, user_id: str) -> None:
    connection = repo.get_connection_by_id(connection_id)
    if not connection or connection["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gmail connection not found")
    repo.set_active(connection_id, is_active=False)
    # Note: this doesn't revoke the token at Google's end, just stops us from
    # using it. Revoking server-side too (POST to Google's /revoke endpoint)
    # is a reasonable Module-2.1 follow-up if you want "disconnect" to be final.


async def sync_now(connection_id: str, user_id: str, max_results: int = 20) -> dict:
    """
    Synchronous fetch-and-store for today's manual testing. Module 3 wraps
    this exact logic in a Celery task triggered by a Gmail webhook/poll -
    the ingestion logic itself doesn't change, only what calls it.
    """
    connection = repo.get_connection_by_id(connection_id)
    if not connection or connection["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gmail connection not found")
    if not connection["is_active"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This Gmail connection is disconnected")

    refresh_token = decrypt(connection["refresh_token"])
    google_tokens = await refresh_gmail_access_token(refresh_token)
    access_token = google_tokens["access_token"]

    message_ids = await gmail_client.list_message_ids(access_token, max_results=max_results)

    inserted, skipped = 0, 0
    for message_id in message_ids:
        parsed = await gmail_client.get_message(access_token, message_id)
        row = emails_repo.insert_email_if_new(user_id, parsed)
        if row:
            inserted += 1
        else:
            skipped += 1  # already existed - safe to sync repeatedly

    return {"checked": len(message_ids), "inserted": inserted, "skipped_existing": skipped}
