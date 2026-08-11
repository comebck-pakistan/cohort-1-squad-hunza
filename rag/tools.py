from datetime import datetime, timezone, timedelta
from database import get_db


def _date_range_bounds(date_range: str) -> tuple[str | None, str | None]:
    """Converts a natural date_range keyword into (start_iso, end_iso) bounds."""
    now = datetime.now(timezone.utc)
    today_start = now.strftime("%Y-%m-%dT00:00:00")

    if date_range == "today":
        return today_start, None
    if date_range == "yesterday":
        y = (now - timedelta(days=1))
        return y.strftime("%Y-%m-%dT00:00:00"), y.strftime("%Y-%m-%dT23:59:59")
    if date_range == "this_week":
        week_start = (now - timedelta(days=now.weekday()))
        return week_start.strftime("%Y-%m-%dT00:00:00"), None
    return None, None  # "all_time" or unrecognized


def query_emails(
    user_id: str,
    date_range: str = "all_time",
    category: str | None = None,
    priority: str | None = None,
    sender_contains: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Queries real email rows with optional filters. This is the single
    source of truth for 'list/show/count emails' style questions - the LLM
    picks the filters, this function runs the actual safe query."""
    db = get_db()
    q = db.table("emails").select("id, subject, sender_name, sender_email, category, priority, received_at").eq("user_id", user_id)

    start, end = _date_range_bounds(date_range)
    if start:
        q = q.gte("received_at", start)
    if end:
        q = q.lte("received_at", end)
    if category:
        q = q.eq("category", category)
    if priority:
        q = q.eq("priority", priority)
    if sender_contains:
        q = q.ilike("sender_email", f"%{sender_contains}%")

    q = q.order("received_at", desc=True).limit(limit)
    return q.execute().data or []


def query_drafts(user_id: str, status: str | None = "pending", limit: int = 20) -> list[dict]:
    """Queries drafts belonging to this user's emails (joined through emails,
    since email_drafts has no user_id column of its own)."""
    db = get_db()
    email_ids = [e["id"] for e in db.table("emails").select("id").eq("user_id", user_id).execute().data or []]
    if not email_ids:
        return []

    q = db.table("email_drafts").select("id, email_id, draft_body, status, generated_at").in_("email_id", email_ids)
    if status:
        q = q.eq("status", status)
    q = q.order("generated_at", desc=True).limit(limit)
    return q.execute().data or []


def query_candidates(
    user_id: str,
    role_applied_for: str | None = None,
    skill_contains: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Queries candidate records with optional filters."""
    db = get_db()
    q = db.table("candidates").select("id, email_id, full_name, candidate_email, role_applied_for, skills_extracted").eq("user_id", user_id)

    if role_applied_for:
        q = q.ilike("role_applied_for", f"%{role_applied_for}%")
    q = q.order("created_at", desc=True).limit(limit)
    result = q.execute().data or []

    if skill_contains:
        skill_lower = skill_contains.lower()
        result = [
            c for c in result
            if any(skill_lower in str(s).lower() for s in (c.get("skills_extracted") or []))
        ]

    return result