from database import get_db
from rag.embedder import embed_text


# keywords that signal a structured database query
STRUCTURED_KEYWORDS = [
    "how many", "count", "total", "number of",
    "yesterday", "today", "this week", "last week",
    "how much", "statistics", "summary"
]


def detect_intent(question: str) -> str:
    """
    Decides whether the question needs:
    - "structured": a database count/filter query
    - "semantic": a vector similarity search
    """
    question_lower = question.lower()
    for keyword in STRUCTURED_KEYWORDS:
        if keyword in question_lower:
            return "structured"
    return "semantic"


def structured_query(question: str, user_id: str) -> dict:
    """
    Handles counting and filtering questions by querying
    Supabase directly. Returns exact counts, never guesses.
    """
    db = get_db()
    question_lower = question.lower()

    # how many emails today
    if "today" in question_lower and "email" in question_lower:
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = db.table("emails")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .gte("received_at", f"{today}T00:00:00")\
            .execute()
        count = result.count or 0
        return {
            "type": "structured",
            "answer": f"You received {count} emails today.",
            "data": {"count": count}
        }

    # how many applicants
    if "applicant" in question_lower or "application" in question_lower:
        result = db.table("candidates")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        count = result.count or 0
        return {
            "type": "structured",
            "answer": f"You have {count} total applicants.",
            "data": {"count": count}
        }

    # how many emails yesterday
    if "yesterday" in question_lower:
        from datetime import datetime, timezone, timedelta
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        result = db.table("emails")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .gte("received_at", f"{yesterday}T00:00:00")\
            .lte("received_at", f"{yesterday}T23:59:59")\
            .execute()
        count = result.count or 0
        return {
            "type": "structured",
            "answer": f"You received {count} emails yesterday.",
            "data": {"count": count}
        }

    # how many pending drafts
    if "draft" in question_lower or "pending" in question_lower:
        result = db.table("email_drafts")\
            .select("id", count="exact")\
            .eq("status", "pending")\
            .execute()
        count = result.count or 0
        return {
            "type": "structured",
            "answer": f"You have {count} drafts pending approval.",
            "data": {"count": count}
        }

    # default fallback
    return {
        "type": "structured",
        "answer": "I couldn't find a specific answer for that question. Try asking about emails, applicants, or drafts.",
        "data": {}
    }


async def semantic_search(question: str, user_id: str, top_k: int = 5) -> list:
    db = get_db()
    question_embedding = await embed_text(question)
    result = db.rpc("match_emails", {
        "query_embedding": question_embedding,
        "match_user_id": user_id,
        "match_count": top_k
    }).execute()
    return result.data if result.data else []


async def retrieve(question: str, user_id: str) -> dict:
    intent = detect_intent(question)
    if intent == "structured":
        return structured_query(question, user_id)
    else:
        results = await semantic_search(question, user_id)
        return {"type": "semantic", "results": results, "question": question}