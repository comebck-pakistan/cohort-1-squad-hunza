from app.core.supabase_client import get_supabase


def list_needs_attention(user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """
    QUEUE-02. Uses !inner so the join actually filters the top-level `emails`
    rows (a plain embedded select only filters the nested array, not which
    parent rows come back at all - `!inner` is what makes unmatched parents
    disappear from the result). ilike on priority guards against the
    classifier occasionally returning inconsistent casing ("high" vs "High").
    """
    db = get_supabase()
    res = (
        db.table("emails")
        .select("*, email_categories!inner(*)")
        .eq("user_id", user_id)
        .ilike("email_categories.priority", "high")
        .is_("email_categories.resolved_at", "null")
        .order("received_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return res.data


def resolve_email(email_id: str) -> dict | None:
    """Marks an email's classification as resolved - it drops out of the
    needs-attention queue. Called both explicitly (DELETE /queue/{id}) and
    automatically after a draft is sent (drafts/service.py)."""
    from datetime import datetime, timezone
    db = get_supabase()
    res = (
        db.table("email_categories")
        .update({"resolved_at": datetime.now(timezone.utc).isoformat()})
        .eq("email_id", email_id)
        .execute()
    )
    return res.data[0] if res.data else None
