from database import get_db


def list_candidates_for_user(user_id: str) -> list[dict]:
    db = get_db()
    result = db.table("candidates")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()
    return result.data or []