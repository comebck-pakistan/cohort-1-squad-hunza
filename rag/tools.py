from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from database import get_db

LOCAL_TZ = ZoneInfo("Asia/Karachi")


def _date_range_bounds(date_range: str) -> tuple[str | None, str | None]:
    """Converts a natural date_range keyword into (start_iso, end_iso) UTC
    bounds, anchored to local midnight rather than server UTC midnight -
    avoids 'today' silently shifting by ~5 hours depending on when the
    server happens to run the query."""
    now_local = datetime.now(LOCAL_TZ)
    today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)

    if date_range == "today":
        start_utc = today_start_local.astimezone(timezone.utc)
        return start_utc.strftime("%Y-%m-%dT%H:%M:%S"), None

    if date_range == "yesterday":
        y_start_local = today_start_local - timedelta(days=1)
        y_end_local = today_start_local - timedelta(seconds=1)
        return (
            y_start_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            y_end_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        )

    if date_range == "this_week":
        week_start_local = today_start_local - timedelta(days=now_local.weekday())
        return week_start_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), None

    return None, None  # "all_time" or unrecognized


def query_emails(
    user_id: str,
    date_range: str = "all_time",
    category: str | None = None,
    priority: str | None = None,
    sender_contains: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Queries real email rows with optional filters."""
    db = get_db()
    q = db.table("emails").select(
        "id, subject, sender_name, sender_email, category, priority, received_at"
    ).eq("user_id", user_id)

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


def query_drafts(user_id: str, status: str | None = "pending", limit: int = 50) -> list[dict]:
    """Queries drafts belonging to this user's emails."""
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
    limit: int = 50,
) -> list[dict]:
    """Lists/counts candidates with a summary-level profile (no full resume
    text - use get_candidate_details for one specific candidate's complete
    profile including resume text)."""
    db = get_db()
    q = db.table("candidates").select(
        "id, email_id, full_name, candidate_email, role_applied_for, "
        "years_of_experience, skills_extracted, summary, education_degree, "
        "education_institution, education_gpa"
    ).eq("user_id", user_id)

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


def get_candidate_details(user_id: str, email: str | None = None, name: str | None = None) -> dict:
    """Fetches ONE candidate's COMPLETE profile - including full resume text -
    by email or name. Call this once per candidate when the question needs
    deep detail on specific named candidates (e.g. comparing two people)."""
    db = get_db()
    q = db.table("candidates").select(
        "id, email_id, full_name, candidate_email, role_applied_for, "
        "years_of_experience, skills_extracted, summary, education_degree, "
        "education_institution, education_gpa, resume_text"
    ).eq("user_id", user_id)

    if email:
        q = q.ilike("candidate_email", f"%{email}%")
    elif name:
        q = q.ilike("full_name", f"%{name}%")
    else:
        return {"error": "Must provide either email or name"}

    result = q.limit(1).execute().data or []
    return result[0] if result else {"error": f"No candidate found matching {email or name}"}


def query_candidate_documents(user_id: str, limit: int = 50) -> list[dict]:
    """Lists/counts uploaded resume/document files, scoped to this user."""
    db = get_db()
    email_ids = [e["id"] for e in db.table("emails").select("id").eq("user_id", user_id).execute().data or []]
    if not email_ids:
        return []

    q = db.table("candidate_documents").select(
        "id, email_id, original_filename, uploaded_at"
    ).in_("email_id", email_ids).order("uploaded_at", desc=True).limit(limit)
    return q.execute().data or []