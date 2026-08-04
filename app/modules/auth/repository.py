from datetime import datetime, timezone

from app.core.supabase_client import get_supabase


def get_user_by_email(email: str) -> dict | None:
    db = get_supabase()
    res = db.table("users").select("*").eq("email", email).limit(1).execute()
    return res.data[0] if res.data else None


def get_user_by_id(user_id: str) -> dict | None:
    db = get_supabase()
    res = db.table("users").select("*").eq("id", user_id).limit(1).execute()
    return res.data[0] if res.data else None


def create_user(email: str, full_name: str | None, user_id: str | None = None) -> dict:
    db = get_supabase()
    payload = {"email": email, "full_name": full_name}
    if user_id:
        payload["id"] = user_id
    res = db.table("users").insert(payload).execute()
    return res.data[0]

def get_or_create_user(email: str, full_name: str | None) -> dict:
    user = get_user_by_email(email)
    if user:
        return user
    return create_user(email, full_name)



def get_or_create_user_by_auth_id(auth_id: str, email: str, full_name: str | None = None) -> dict:
    """
    Ensures a public.users row exists with id == auth_id (the Supabase Auth
    user id from the JWT 'sub' claim). Call this from get_current_user so
    every authenticated request self-heals the row.

    Handles three cases:
    1. Row already exists with this id -> return it.
    2. A row exists with this email but a different id (e.g. created by the
       old custom-JWT login flow with a random id) -> migrate its id to
       match auth_id, so future FK references line up.
    3. No row at all -> create one with id explicitly set to auth_id.
    """
    user = get_user_by_id(auth_id)
    if user:
        return user

    existing_by_email = get_user_by_email(email)
    if existing_by_email:
        db = get_supabase()
        res = db.table("users").update({"id": auth_id}).eq("id", existing_by_email["id"]).execute()
        return res.data[0] if res.data else existing_by_email

    return create_user(email, full_name, user_id=auth_id)


def store_refresh_token(
    user_id: str,
    token_hash: str,
    expires_at: datetime,
    user_agent: str | None,
    ip_address: str | None,
) -> dict:
    db = get_supabase()
    res = db.table("refresh_tokens").insert({
        "user_id": user_id,
        "token_hash": token_hash,
        "expires_at": expires_at.isoformat(),
        "user_agent": user_agent,
        "ip_address": ip_address,
    }).execute()
    return res.data[0]


def get_refresh_token_by_hash(token_hash: str) -> dict | None:
    db = get_supabase()
    res = db.table("refresh_tokens").select("*").eq("token_hash", token_hash).limit(1).execute()
    return res.data[0] if res.data else None


def revoke_refresh_token(token_id: str, replaced_by: str | None = None) -> None:
    db = get_supabase()
    update = {"revoked_at": datetime.now(timezone.utc).isoformat()}
    if replaced_by:
        update["replaced_by"] = replaced_by
    db.table("refresh_tokens").update(update).eq("id", token_id).execute()


def revoke_all_user_tokens(user_id: str) -> None:
    """Used on reuse-detection (stolen/replayed refresh token) or explicit 'log out everywhere'."""
    db = get_supabase()
    db.table("refresh_tokens").update(
        {"revoked_at": datetime.now(timezone.utc).isoformat()}
    ).eq("user_id", user_id).is_("revoked_at", "null").execute()
