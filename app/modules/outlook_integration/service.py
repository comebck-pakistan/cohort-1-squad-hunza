from fastapi import HTTPException, status

from app.core.crypto import decrypt, encrypt
from app.modules.emails import repository as emails_repo
from app.modules.outlook_integration import outlook_client, repository as repo
from app.modules.outlook_integration.microsoft_oauth import (
    exchange_code_for_outlook_tokens,
    refresh_outlook_access_token,
)
from tasks.classifier import classify_and_save
from tasks.duplicate import check_and_save
from tasks.resume import process_resume_from_outlook
from tasks.queue import check_needs_attention
from rag.embedder import embed_and_save_email

from app.core.config import get_settings

settings = get_settings()


async def handle_outlook_callback(code: str, user_id: str) -> dict:
    tokens = await exchange_code_for_outlook_tokens(code)
    refresh_token = tokens.get("refresh_token")
    access_token = tokens.get("access_token")

    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Outlook token exchange failed")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Microsoft did not return a refresh token. Try connecting again.",
        )

    profile = await outlook_client.get_profile(access_token)
    email_address = profile.get("mail") or profile.get("userPrincipalName")

    encrypted = encrypt(refresh_token)
    existing = repo.get_connection_by_user_and_address(user_id, email_address)
    if existing:
        connection = repo.reactivate_connection(existing["id"], encrypted)
    else:
        connection = repo.create_connection(user_id, email_address, encrypted)

    await start_subscription(connection["id"], user_id)
    return connection


def disconnect(connection_id: str, user_id: str) -> None:
    connection = repo.get_connection_by_id(connection_id)
    if not connection or connection["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outlook connection not found")
    repo.set_active(connection_id, is_active=False)


async def sync_now(connection_id: str, user_id: str, max_results: int = 20) -> dict:
    """Manual fetch-and-store, mirroring the Gmail sync_now for testing."""
    connection = repo.get_connection_by_id(connection_id)
    if not connection or connection["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outlook connection not found")
    if not connection["is_active"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This Outlook connection is disconnected")

    refresh_token = decrypt(connection["refresh_token"])
    ms_tokens = await refresh_outlook_access_token(refresh_token)
    access_token = ms_tokens["access_token"]

    message_ids = await outlook_client.list_message_ids(access_token, max_results=max_results)

    inserted, skipped = 0, 0

    for message_id in message_ids:
        parsed = await outlook_client.get_message(access_token, message_id)
        if parsed.get("sender_email", "").lower() == connection["email_address"].lower():
            continue  # skip our own sent reply

        parsed["provider"] = "outlook"
        row = emails_repo.insert_email_if_new(user_id, {**parsed, "gmail_connection_id": connection_id})
        if row:
            inserted += 1
            email_id = row["id"]

            if parsed.get("has_attachment"):
                await process_resume_from_outlook(
                    access_token=access_token,
                    message_id=message_id,
                    email_id=email_id,
                    user_id=user_id
                )

            classify_and_save(email_id)
            await check_and_save(email_id, user_id)
            check_needs_attention(email_id, user_id)
        else:
            skipped += 1

    return {"checked": len(message_ids), "inserted": inserted, "skipped_existing": skipped}


async def start_subscription(connection_id: str, user_id: str) -> dict:
    """Graph's equivalent of Gmail's start_watch - registers a webhook subscription."""
    connection = repo.get_connection_by_id(connection_id)
    if not connection or connection["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outlook connection not found")

    refresh_token = decrypt(connection["refresh_token"])
    ms_tokens = await refresh_outlook_access_token(refresh_token)
    access_token = ms_tokens["access_token"]

    result = await outlook_client.create_subscription(access_token, settings.OUTLOOK_WEBHOOK_URL)
    print(f"SUBSCRIPTION RESULT for {connection['email_address']}: {result}")

    subscription_id = result.get("id")
    expiration = result.get("expirationDateTime")
    if subscription_id:
        repo.update_subscription_info(connection_id, subscription_id, expiration)

    return result


async def handle_graph_notification(body: dict, background_tasks) -> None:
    """
    Handles Microsoft Graph change notifications. Graph sends a batch of
    notifications (each referencing a subscriptionId + resource), unlike
    Gmail's single Pub/Sub message per history change - so this loops over
    each notification in the payload.
    """
    try:
        notifications = body.get("value", [])
        if not notifications:
            return

        for note in notifications:
            subscription_id = note.get("subscriptionId")
            if not subscription_id:
                continue

            connection = repo.get_connection_by_subscription_id(subscription_id)
            if not connection or not connection.get("is_active"):
                continue

            user_id = connection["user_id"]
            connection_id = connection["id"]
            email_address = connection["email_address"]

            resource_data = note.get("resourceData", {})
            message_id = resource_data.get("id")
            if not message_id:
                continue

            try:
                refresh_token = decrypt(connection["refresh_token"])
                ms_tokens = await refresh_outlook_access_token(refresh_token)
                access_token = ms_tokens["access_token"]
            except Exception as e:
                print(f"Token refresh failed for {email_address}: {e}")
                repo.set_active(connection_id, is_active=False)
                continue

            try:
                parsed = await outlook_client.get_message(access_token, message_id)
            except Exception as e:
                print(f"Skipping Outlook message {message_id}: {e}")
                continue

            if parsed.get("sender_email", "").lower() == email_address.lower():
                continue  # skip our own sent reply

            parsed["provider"] = "outlook"
            row = emails_repo.insert_email_if_new(user_id, {**parsed, "gmail_connection_id": connection_id})
            if row:
                email_id = row["id"]

                if parsed.get("has_attachment"):
                    await process_resume_from_outlook(
                        access_token=access_token,
                        message_id=message_id,
                        email_id=email_id,
                        user_id=user_id
                    )

                classify_and_save(email_id)
                check_needs_attention(email_id, user_id)
                await check_and_save(email_id, user_id)
                background_tasks.add_task(embed_and_save_email, email_id)

                print(f"Graph webhook: processed 1 new email for {email_address}")

    except Exception as e:
        print(f"Outlook webhook error (non-fatal): {e}")
        return


