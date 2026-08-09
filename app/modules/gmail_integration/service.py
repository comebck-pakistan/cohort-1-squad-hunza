import os
from fastapi import HTTPException, status

from app.core.crypto import decrypt, encrypt
from app.modules.emails import repository as emails_repo
from app.modules.gmail_integration import gmail_client, repository as repo
from app.modules.gmail_integration.google_oauth import (
    exchange_code_for_gmail_tokens,
    refresh_gmail_access_token,
)
from tasks.classifier import classify_and_save
from tasks.duplicate import check_and_save    
from tasks.resume import process_resume_from_gmail
from worker import process_email_task
from tasks.queue import check_needs_attention
from rag.embedder import embed_and_save_email


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
    await start_watch(connection["id"], user_id)
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
        row = emails_repo.insert_email_if_new(user_id, {**parsed, "gmail_connection_id": connection_id})
        if row:
            inserted += 1
            email_id = row["id"]


            # handle resume attachment if present
            if parsed.get("has_attachment"):
                await process_resume_from_gmail(
                    access_token=access_token,
                    message_id=message_id,
                    email_id=email_id,
                    user_id=user_id
                )

            # trigger AI pipeline
            classify_and_save(email_id)
            await check_and_save(email_id, user_id)
            check_needs_attention(email_id, user_id)
            # process_email_task.delay(email_id, user_id)  NEED TO BE UNCOMMENTED LATER WHILE DEPLOYMENT
        else:
            skipped += 1
    return {"checked": len(message_ids), "inserted": inserted, "skipped_existing": skipped}



GMAIL_PUBSUB_TOPIC = os.environ["PUBSUB_TOPIC"]  # e.g. projects/YOUR_PROJECT_ID/topics/gmail-notifications
print(f"Using PUBSUB_TOPIC: {GMAIL_PUBSUB_TOPIC}")

async def start_watch(connection_id: str, user_id: str) -> dict:
    connection = repo.get_connection_by_id(connection_id)
    if not connection or connection["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gmail connection not found")

    refresh_token = decrypt(connection["refresh_token"])
    google_tokens = await refresh_gmail_access_token(refresh_token)
    access_token = google_tokens["access_token"]

    result = await gmail_client.watch(access_token, GMAIL_PUBSUB_TOPIC)
    print(f"WATCH RESULT for {connection['gmail_address']}: {result}")

    history_id = str(result.get("historyId", ""))
    if history_id:
        repo.update_history_id(connection_id, history_id)

    return result


async def handle_pubsub_notification(body: dict, background_tasks) -> None:
    import base64
    import json

    try:
        message = body.get("message", {})
        data = message.get("data", "")
        
        if not data:
            return

        decoded = base64.urlsafe_b64decode(data + "==").decode("utf-8")
        notification = json.loads(decoded)

        email_address = notification.get("emailAddress")
        history_id = str(notification.get("historyId", ""))

        if not email_address or not history_id:
            return

        connection = repo.get_connection_by_address(email_address)
        if not connection or not connection.get("is_active"):
            return

        user_id = connection["user_id"]
        connection_id = connection["id"]

        try:
            refresh_token = decrypt(connection["refresh_token"])
            google_tokens = await refresh_gmail_access_token(refresh_token)
            access_token = google_tokens["access_token"]
        except Exception as e:
            print(f"Token refresh failed for {email_address}: {e}")
            repo.set_active(connection_id, is_active=False)
            return

        last_history_id = connection.get("history_id")

        if not last_history_id:
            repo.update_history_id(connection_id, history_id)
            return

        new_message_ids = await gmail_client.list_new_message_ids(
            access_token, last_history_id
        )

        inserted = 0
        for message_id in new_message_ids:
            try:
                parsed = await gmail_client.get_message(access_token, message_id)
            except Exception as e:
                print(f"Skipping message {message_id}: {e}")
                continue
            
            row = emails_repo.insert_email_if_new(user_id, {**parsed, "gmail_connection_id": connection_id})
            if row:
                inserted += 1
                email_id = row["id"]

                if parsed.get("has_attachment"):
                    await process_resume_from_gmail(
                        access_token=access_token,
                        message_id=message_id,
                        email_id=email_id,
                        user_id=user_id
                    )

                classify_and_save(email_id)
                check_needs_attention(email_id, user_id)
                await check_and_save(email_id, user_id)
                background_tasks.add_task(embed_and_save_email, email_id)

        repo.update_history_id(connection_id, history_id)
        print(f"Pub/Sub webhook: processed {inserted} new emails for {email_address}")

    except Exception as e:
        print(f"Webhook error (non-fatal): {e}")
        return