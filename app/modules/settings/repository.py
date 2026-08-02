from app.core.supabase_client import get_supabase


def get_settings_by_user_id(user_id: str) -> dict | None:
    db = get_supabase()
    res = db.table("user_settings").select("*").eq("user_id", user_id).limit(1).execute()
    return res.data[0] if res.data else None


def upsert_user_settings(user_id: str, settings: dict) -> dict:
    db = get_supabase()
    res = db.table("user_settings").upsert(
        {
            "user_id": user_id,
            "categories": settings["categories"],
            "job_roles": settings["roles"],
            "job_descriptions": settings["job_descriptions"],
            "reply_tone": settings["reply_tone"],
        },
        on_conflict="user_id",
    ).execute()
    return res.data[0]
