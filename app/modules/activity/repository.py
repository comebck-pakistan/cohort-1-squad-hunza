from app.core.supabase_client import get_supabase


def list_activity_for_user(user_id: str) -> list[dict]:
    db = get_supabase()

    # Draft edits: draft_corrections -> email_drafts -> emails (manual joins,
    # since we can't rely on PostgREST FK-embedding being configured)
    corrections = db.table("draft_corrections").select("*").execute().data or []
    draft_ids = list({c["draft_id"] for c in corrections})
    drafts_by_id = {}
    if draft_ids:
        drafts = db.table("email_drafts").select("id, email_id").in_("id", draft_ids).execute().data or []
        drafts_by_id = {d["id"]: d["email_id"] for d in drafts}

    # Category corrections: label_corrections -> emails
    label_corrections = db.table("label_corrections").select("*").execute().data or []

    email_ids = set(drafts_by_id.values()) | {lc["email_id"] for lc in label_corrections}
    emails_by_id = {}
    if email_ids:
        emails = (
            db.table("emails")
            .select("id, subject, sender_name, sender_email, user_id")
            .in_("id", list(email_ids))
            .execute()
            .data or []
        )
        emails_by_id = {e["id"]: e for e in emails}

    activity = []

    for c in corrections:
        email_id = drafts_by_id.get(c["draft_id"])
        email = emails_by_id.get(email_id)
        if not email or email["user_id"] != user_id:
            continue
        activity.append({
            "id": c["id"],
            "type": "Draft Edit",
            "email_id": email_id,
            "email_subject": email.get("subject"),
            "original": c.get("original_text"),
            "corrected": c.get("corrected_text"),
            "corrected_at": c.get("corrected_at"),
        })

    for lc in label_corrections:
        email = emails_by_id.get(lc["email_id"])
        if not email or email["user_id"] != user_id:
            continue
        activity.append({
            "id": lc["id"],
            "type": "Category Fix",
            "email_id": lc["email_id"],
            "email_subject": email.get("subject"),
            "original": lc.get("original_category"),
            "corrected": lc.get("corrected_category"),
            "corrected_at": lc.get("corrected_at"),
        })

    activity.sort(key=lambda a: a["corrected_at"] or "", reverse=True)
    return activity