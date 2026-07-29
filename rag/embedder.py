import os
import httpx
import numpy as np
from config import EMBEDDING_MODEL
from database import get_db

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL_PATH = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL_PATH}"


async def embed_text(text: str) -> list:
    """Converts text to vector embedding via HF Inference API."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": text, "options": {"wait_for_model": True}}
        )
        resp.raise_for_status()
        result = resp.json()
        if isinstance(result[0], list) and isinstance(result[0][0], list):
            arr = np.array(result[0])
            return arr.mean(axis=0).tolist()
        return result


async def embed_and_save_email(email_id: str) -> bool:
    """
    Reads an email from Supabase, generates its embedding,
    and saves it to email_embeddings table.
    Called automatically after every email is processed.
    """
    db = get_db()

    email_data = db.table("emails")\
        .select("body_text, subject")\
        .eq("id", email_id)\
        .single()\
        .execute()

    if not email_data.data:
        print(f"Email {email_id} not found")
        return False

    email = email_data.data
    text = f"{email.get('subject', '')} {email.get('body_text', '')}"

    embedding = await embed_text(text)

    db.table("email_embeddings").insert({
        "email_id": email_id,
        "embedding": embedding
    }).execute()

    print(f"Email {email_id} embedded and saved")
    return True


async def embed_and_save_candidate(candidate_id: str) -> bool:
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

    embedding = await embed_text(text)

    email_id = candidate.get("email_id")
    if email_id:
        db.table("email_embeddings").insert({
            "email_id": email_id,
            "embedding": embedding
        }).execute()

    print(f"Candidate {candidate_id} embedded and saved")
    return True