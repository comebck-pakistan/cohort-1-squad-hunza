from app.core.supabase_client import get_supabase


def get_connection_by_id(connection_id: str) -> dict | None:
    db = get_supabase()
    res = db.table("email_connections").select("*").eq("id", connection_id).eq("provider", "outlook").limit(1).execute()
    return res.data[0] if res.data else None


def get_connection_by_user_and_address(user_id: str, outlook_address: str) -> dict | None:
    db = get_supabase()
    res = db.table("email_connections")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("email_address", outlook_address)\
        .eq("provider", "outlook")\
        .limit(1)\
        .execute()
    return res.data[0] if res.data else None


def list_connections_for_user(user_id: str) -> list[dict]:
    db = get_supabase()
    res = db.table("email_connections").select("*").eq("user_id", user_id).eq("provider", "outlook").execute()
    return res.data


def create_connection(user_id: str, outlook_address: str, encrypted_refresh_token: str) -> dict:
    db = get_supabase()
    res = db.table("email_connections").insert({
        "user_id": user_id,
        "email_address": outlook_address,  # reused column name for the connected mailbox address
        "refresh_token": encrypted_refresh_token,
        "is_active": True,
        "provider": "outlook",
    }).execute()
    return res.data[0]


def reactivate_connection(connection_id: str, encrypted_refresh_token: str) -> dict:
    db = get_supabase()
    res = db.table("email_connections")\
        .update({"refresh_token": encrypted_refresh_token, "is_active": True})\
        .eq("id", connection_id)\
        .execute()
    return res.data[0]


def set_active(connection_id: str, is_active: bool) -> None:
    db = get_supabase()
    db.table("email_connections").update({"is_active": is_active}).eq("id", connection_id).execute()


def update_subscription_info(connection_id: str, subscription_id: str, expiration: str) -> None:
    db = get_supabase()
    db.table("email_connections")\
        .update({"subscription_id": subscription_id, "subscription_expiration": expiration})\
        .eq("id", connection_id)\
        .execute()


def get_connection_by_subscription_id(subscription_id: str) -> dict | None:
    """Used by the webhook handler to find which connection a Graph notification belongs to."""
    db = get_supabase()
    res = db.table("email_connections")\
        .select("*")\
        .eq("subscription_id", subscription_id)\
        .eq("provider", "outlook")\
        .limit(1)\
        .execute()
    return res.data[0] if res.data else None


def get_connection_by_id_for_user(connection_id: str, user_id: str) -> dict | None:
    db = get_supabase()
    res = db.table("email_connections")\
        .select("*")\
        .eq("id", connection_id)\
        .eq("user_id", user_id)\
        .eq("provider", "outlook")\
        .limit(1)\
        .execute()
    return res.data[0] if res.data else None


def delete_connection_and_data(connection_id: str, user_id: str) -> bool:
    """Mirrors gmail_integration's delete-everything behavior for Outlook connections."""
    db = get_supabase()
    connection = db.table("email_connections")\
        .select("*")\
        .eq("id", connection_id)\
        .eq("user_id", user_id)\
        .eq("provider", "outlook")\
        .limit(1)\
        .execute()
    if not connection.data:
        return False
    db.table("emails").delete().eq("user_id", user_id).eq("provider", "outlook").execute()
    db.table("email_connections").delete().eq("id", connection_id).eq("user_id", user_id).execute()
    return True
