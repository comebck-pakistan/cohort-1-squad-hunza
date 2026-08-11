from database import get_db
from datetime import datetime, timezone, timedelta


def check_needs_attention(email_id: str, user_id: str) -> dict:
    """
    Evaluates trigger conditions for a single email and flags it
    as needing attention if any condition is met.
    Called by the pipeline after classification.
    """
    db = get_db()

    # fetch email with its category
    email_data = db.table("emails")\
        .select("*")\
        .eq("id", email_id)\
        .single()\
        .execute()

    if not email_data.data:
        return {"needs_attention": False, "reason": None}

    email = email_data.data
    category_data = db.table("email_categories")\
        .select("*")\
        .eq("email_id", email_id)\
        .single()\
        .execute()

    if not category_data.data:
        return {"needs_attention": False, "reason": None}

    category = category_data.data
    reasons = []

    # Trigger 1: High priority email
    if category.get("priority") == "High":
        reasons.append("High priority email")

    # Trigger 2: Interview scheduling or reschedule
    if category.get("category") in ["Interview Scheduling", "Interview Reschedule"]:
        reasons.append("Interview requires scheduling")

    # Trigger 3: Offer acceptance or rejection
    if category.get("category") in ["Offer Acceptance", "Offer Rejection"]:
        reasons.append("Offer response received")

    # Trigger 4: Candidate withdrawal
    if category.get("category") == "Candidate Withdrawal":
        reasons.append("Candidate withdrew application")

    # Trigger 5: Check for multiple follow-ups from same sender
    sender_email = email.get("sender_email")
    if sender_email:
        followup_count = db.table("emails")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .eq("sender_email", sender_email)\
            .execute()
        if followup_count.count and followup_count.count >= 2:
            reasons.append("Multiple follow-ups from same candidate")

    needs_attention = len(reasons) > 0
    reason = reasons[0] if reasons else None

    return {
        "needs_attention": needs_attention,
        "reason": reason,
        "all_reasons": reasons
    }


def evaluate_pending_emails(user_id: str) -> dict:
    """
    Scheduled job - evaluates ALL unprocessed emails for a user
    and flags ones that need attention.
    Called periodically by Celery beat scheduler.
    """
    db = get_db()

    # get all unresolved emails for this user
    emails = db.table("emails")\
        .select("id")\
        .eq("user_id", user_id)\
        .eq("is_processed", True)\
        .execute()

    if not emails.data:
        return {"evaluated": 0, "flagged": 0}

    evaluated = 0
    flagged = 0

    for email in emails.data:
        email_id = email["id"]
        result = check_needs_attention(email_id, user_id)
        evaluated += 1
        if result["needs_attention"]:
            flagged += 1

    return {"evaluated": evaluated, "flagged": flagged}


if __name__ == "__main__":
    # test manually
    test_email_id = "84289971-071e-4a5b-85d0-af4eeb3435e4"
    test_user_id = "4abe83e2-0bca-465e-8aaa-eff3f3271a4a"

    result = check_needs_attention(test_email_id, test_user_id)
    print(f"Needs attention: {result['needs_attention']}")
    print(f"Reason: {result['reason']}")
    print(f"All reasons: {result['all_reasons']}")