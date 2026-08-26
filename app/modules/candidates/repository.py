from database import get_db


def list_candidates_for_user(user_id: str) -> list[dict]:
    db = get_db()
    result = db.table("candidates")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()
    candidates = result.data or []

    email_ids = [c["email_id"] for c in candidates if c.get("email_id")]
    documents_map: dict[str, list[dict]] = {}
    if email_ids:
        docs_result = db.table("candidate_documents")\
            .select("*")\
            .in_("email_id", email_ids)\
            .execute()
        for doc in docs_result.data or []:
            documents_map.setdefault(doc["email_id"], []).append({
                "url": doc["file_url"],
                "filename": doc["original_filename"],
            })

    for c in candidates:
        c["documents"] = documents_map.get(c.get("email_id"), [])

    return candidates