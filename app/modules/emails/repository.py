"""
Deliberately minimal today: insert + list/get. Categorization, priority,
needs-attention, and the full Celery ingestion pipeline are Module 3.
"""
from postgrest.exceptions import APIError

from app.core.supabase_client import get_supabase


def insert_email_if_new(user_id: str, parsed: dict) -> dict | None:
    """
    Returns the inserted row, or None if this gmail_message_id already exists
    (relies on the emails.gmail_message_id UNIQUE constraint - cheaper and
    safer than a separate SELECT-then-INSERT race).
    """
    db = get_supabase()
    try:
        res = db.table("emails").insert({
            "user_id": user_id,
            **parsed,
        }).execute()
        return res.data[0]
    except APIError as e:
        if "duplicate key value" in str(e).lower() or "23505" in str(e):
            return None
        raise


def _latest_category_map(db, email_ids):
    if not email_ids:
        return {}
    res = db.table("email_categories")\
        .select("*")\
        .in_("email_id", email_ids)\
        .order("classified_at", desc=True)\
        .execute()
    cat_map = {}
    for row in res.data:
        cat_map.setdefault(row["email_id"], row)
    return cat_map

def _attach_latest_category(email, cat_map):
    cat = cat_map.get(email["id"])
    email["category"] = cat["category"] if cat else None
    email["priority"] = cat["priority"] if cat else None
    return email


def list_emails_for_user(user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    db = get_supabase()
    res = (
        db.table("emails")
        .select("*")
        .eq("user_id", user_id)
        .order("received_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    emails = res.data
    cat_map = _latest_category_map(db, [e["id"] for e in emails])
    return [_attach_latest_category(e, cat_map) for e in emails]


def get_email_by_id(email_id: str, user_id: str) -> dict | None:
    db = get_supabase()
    res = db.table("emails").select("*").eq("id", email_id).eq("user_id", user_id).limit(1).execute()
    if not res.data:
        return None
    email = res.data[0]
    cat_map = _latest_category_map(db, [email_id])
    return _attach_latest_category(email, cat_map)


def update_email_category(email_id: str, category: str) -> dict:
    """Updates the most recent email_categories row for this email, or creates one if none exists."""
    db = get_supabase()
    existing = (
        db.table("email_categories")
        .select("id")
        .eq("email_id", email_id)
        .order("classified_at", desc=True)
        .limit(1)
        .execute()
    )
    if existing.data:
        db.table("email_categories").update({"category": category}).eq("id", existing.data[0]["id"]).execute()
    else:
        db.table("email_categories").insert({"email_id": email_id, "category": category}).execute()