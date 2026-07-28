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


def create_user(email: str, full_name: str | None) -> dict:
    db = get_supabase()
    res = db.table("users").insert({"email": email, "full_name": full_name}).execute()
    return res.data[0]


def get_or_create_user(email: str, full_name: str | None) -> dict:
    user = get_user_by_email(email)
    if user:
        return user
    return create_user(email, full_name)


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
