from app.core.supabase_client import get_supabase


def get_connection_by_user_and_address(user_id: str, gmail_address: str) -> dict | None:
    db = get_supabase()
    res = (
        db.table("gmail_connections")
        .select("*")
        .eq("user_id", user_id)
        .eq("gmail_address", gmail_address)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_connection_by_id(connection_id: str) -> dict | None:
    db = get_supabase()
    res = db.table("gmail_connections").select("*").eq("id", connection_id).limit(1).execute()
    return res.data[0] if res.data else None


def list_connections_for_user(user_id: str) -> list[dict]:
    db = get_supabase()
    res = db.table("gmail_connections").select("*").eq("user_id", user_id).execute()
    return res.data


def create_connection(user_id: str, gmail_address: str, encrypted_refresh_token: str) -> dict:
    from datetime import datetime, timezone
    db = get_supabase()
    res = db.table("gmail_connections").insert({
        "user_id": user_id,
        "gmail_address": gmail_address,
        "refresh_token": encrypted_refresh_token,
        "is_active": True,
        "connected_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return res.data[0]

def reactivate_connection(connection_id: str, encrypted_refresh_token: str) -> dict:
    from datetime import datetime, timezone
    db = get_supabase()
    res = (
        db.table("gmail_connections")
        .update({
            "refresh_token": encrypted_refresh_token,
            "is_active": True,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("id", connection_id)
        .execute()
    )
    return res.data[0]


def set_active(connection_id: str, is_active: bool) -> None:
    db = get_supabase()
    db.table("gmail_connections").update({"is_active": is_active}).eq("id", connection_id).execute()


def get_connection_by_address(gmail_address: str) -> dict | None:
    """Find active connection by Gmail address — used by Pub/Sub webhook."""
    db = get_supabase()
    res = db.table("gmail_connections")\
        .select("*")\
        .eq("gmail_address", gmail_address)\
        .eq("is_active", True)\
        .order("connected_at", desc=True)\
        .limit(1)\
        .execute()
    return res.data[0] if res.data else None

def update_history_id(connection_id: str, history_id: str) -> None:
    """Updates the stored history_id after processing a Pub/Sub notification."""
    db = get_supabase()
    db.table("gmail_connections")\
        .update({"history_id": history_id})\
        .eq("id", connection_id)\
        .execute()