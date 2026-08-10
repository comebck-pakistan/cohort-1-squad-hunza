from app.core.supabase_client import get_supabase


def get_draft_by_id(draft_id: str) -> dict | None:
    db = get_supabase()
    res = db.table("email_drafts").select("*").eq("id", draft_id).limit(1).execute()
    return res.data[0] if res.data else None


def get_draft_for_email(email_id: str) -> dict | None:
    db = get_supabase()
    res = (
        db.table("email_drafts")
        .select("*")
        .eq("email_id", email_id)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def update_draft_body(draft_id: str, new_body: str, status: str = "edited") -> dict:
    db = get_supabase()
    res = (
        db.table("email_drafts")
        .update({"draft_body": new_body, "status": status})
        .eq("id", draft_id)
        .execute()
    )
    return res.data[0]


def log_correction(draft_id: str, original_text: str | None, corrected_text: str) -> dict:
    """DRAFT-04: every HR edit to a draft is logged here - this is the raw
    material a future prompt-tuning pass would use to see what recruiters
    consistently change about the AI's drafts."""
    db = get_supabase()
    res = db.table("draft_corrections").insert({
        "draft_id": draft_id,
        "original_text": original_text,
        "corrected_text": corrected_text,
    }).execute()
    return res.data[0]


def mark_approved_and_sent(draft_id: str, gmail_draft_id: str | None) -> dict:
    from datetime import datetime, timezone
    db = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    res = (
        db.table("email_drafts")
        .update({
            "status": "sent",
            "approved_at": now,
            "sent_at": now,
            "gmail_draft_id": gmail_draft_id,
        })
        .eq("id", draft_id)
        .execute()
    )
    return res.data[0]

def list_drafts_for_user(user_id: str) -> list[dict]:
    """Returns all drafts belonging to this user's emails, in one query
    instead of N individual by-email lookups."""
    db = get_supabase()
    email_ids = [
        row["id"]
        for row in db.table("emails").select("id").eq("user_id", user_id).execute().data or []
    ]
    if not email_ids:
        return []
    res = db.table("email_drafts").select("*").in_("email_id", email_ids).execute()
    return res.data or []