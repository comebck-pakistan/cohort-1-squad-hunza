from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL
from database import get_db

model = SentenceTransformer(EMBEDDING_MODEL)


def embed_text(text: str) -> list:
    """Converts text to vector embedding."""
    return model.encode(text).tolist()


def embed_and_save_email(email_id: str) -> bool:
    """
    Reads an email from Supabase, generates its embedding,
    and saves it to email_embeddings table.
    Called automatically after every email is processed.
    """
    db = get_db()

    # fetch email
    email_data = db.table("emails")\
        .select("body_text, subject")\
        .eq("id", email_id)\
        .single()\
        .execute()

    if not email_data.data:
        print(f"Email {email_id} not found")
        return False

    email = email_data.data
    # combine subject and body for richer embedding
    text = f"{email.get('subject', '')} {email.get('body_text', '')}"

    embedding = embed_text(text)

    # save to email_embeddings table
    db.table("email_embeddings").insert({
        "email_id": email_id,
        "embedding": embedding
    }).execute()

    print(f"Email {email_id} embedded and saved")
    return True


def embed_and_save_candidate(candidate_id: str) -> bool:
    """
    Embeds candidate resume text and skills for semantic search.
    Saves to email_embeddings table linked via email_id.
    """
    db = get_db()

    candidate_data = db.table("candidates")\
        .select("*")\
        .eq("id", candidate_id)\
        .single()\
        .execute()

    if not candidate_data.data:
        print(f"Candidate {candidate_id} not found")
        return False

    candidate = candidate_data.data

    # build searchable text from candidate fields
    skills = candidate.get("skills_extracted") or []
    if isinstance(skills, list):
        skills_text = ", ".join(skills)
    else:
        skills_text = str(skills)

    text = f"""
    Candidate: {candidate.get('full_name', '')}
    Role: {candidate.get('role_applied_for', '')}
    Skills: {skills_text}
    """

    embedding = embed_text(text)

    # save to email_embeddings table using the candidate's email_id
    email_id = candidate.get("email_id")
    if email_id:
        db.table("email_embeddings").insert({
            "email_id": email_id,
            "embedding": embedding
        }).execute()

    print(f"Candidate {candidate_id} embedded and saved")
    return True