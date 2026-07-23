import re
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import EMBEDDING_MODEL, DUPLICATE_THRESHOLD
from database import get_db

# load the embedding model once at module level
# so it doesn't reload every time the function is called
model = SentenceTransformer(EMBEDDING_MODEL)


def get_job_posting_embeddings(user_id: str) -> list:
    """
    Fetches all job postings for a user from Supabase.
    Returns a list of dicts with posting text and metadata.
    """
    db = get_db()
    result = db.table("job_postings")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()

    return result.data if result.data else []


def embed_text(text: str) -> list:
    """
    Converts a piece of text into a vector embedding.
    Returns a list of floats.
    """
    embedding = model.encode(text)
    return embedding.tolist()


def cosine_similarity(vec1: list, vec2: list) -> float:
    """
    Calculates similarity between two vectors.
    Returns a score between 0.0 and 1.0.
    1.0 = identical meaning, 0.0 = completely different.
    """
    import numpy as np
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# NEW: chunk the job posting so a long posting doesn't get flattened into
# one diluted embedding. Paragraph-first, sentence/word fallback.
def chunk_job_posting(text: str, chunk_size: int = 300, chunk_overlap: int = 30) -> list:
    """
    Splits job posting text into overlapping chunks using LangChain's
    recursive splitter (tries paragraphs, then sentences, then words).
    """
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)



# NEW: pull the actual question(s) out of an email instead of embedding
# the whole email body (which includes greetings, signatures, etc.)
def extract_questions_from_email(email_text: str) -> list:
    """
    Pulls out candidate question sentences from an email body.
    Falls back to the full email text if nothing question-like is found,
    so we never silently skip an email.
    """
    if not email_text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', email_text.strip())

    question_starters = ("what", "is", "are", "do", "does", "can", "could",
                          "will", "would", "how", "when", "where", "why")

    questions = []
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if s_clean.endswith("?") or s_clean.lower().startswith(question_starters):
            questions.append(s_clean)

    return questions if questions else [email_text.strip()]


def is_duplicate_question(email_body: str, user_id: str) -> dict:
    """
    Checks if an email is asking something already answered
    in the job posting.

    Compares every extracted question from the email against every
    chunk of every job posting, and keeps the single best match.

    Returns a dict with:
    - is_duplicate: True or False
    - similarity_score: how similar it was (0.0 to 1.0)
    - matched_posting_id: which job posting it matched (or None)
    - matched_question: which extracted question triggered the match
    - matched_chunk: which posting chunk it matched against
    """
    job_postings = get_job_posting_embeddings(user_id)

    if not job_postings:
        # no job postings exist yet, cant check for duplicates
        return {
            "is_duplicate": False,
            "similarity_score": 0.0,
            "matched_posting_id": None,
            "matched_question": None,
            "matched_chunk": None
        }

    # NEW: extract questions from the email instead of embedding the whole body
    questions = extract_questions_from_email(email_body)

    highest_score = 0.0
    matched_posting_id = None
    matched_question = None
    matched_chunk = None

    for posting in job_postings:
        posting_text = posting.get("posting_text", "")
        posting_id = posting.get("id")

        # NEW: chunk the posting instead of embedding it as one blob
        posting_chunks = chunk_job_posting(posting_text)
        if not posting_chunks:
            continue

        # embed all chunks for this posting once
        chunk_embeddings = [embed_text(chunk) for chunk in posting_chunks]

        for question in questions:
            question_embedding = embed_text(question)

            for chunk, chunk_embedding in zip(posting_chunks, chunk_embeddings):
                score = cosine_similarity(question_embedding, chunk_embedding)

                if score > highest_score:
                    highest_score = score
                    matched_posting_id = posting_id
                    matched_question = question
                    matched_chunk = chunk

    is_duplicate = highest_score >= DUPLICATE_THRESHOLD

    return {
        "is_duplicate": is_duplicate,
        "similarity_score": round(highest_score, 4),
        "matched_posting_id": matched_posting_id if is_duplicate else None,
        "matched_question": matched_question if is_duplicate else None,
        "matched_chunk": matched_chunk if is_duplicate else None
    }


def check_and_save(email_id: str, user_id: str):
    """
    Reads an email from the database, checks if it's a duplicate,
    and updates the email_categories table with the result.
    """
    db = get_db()

    # fetch the email
    email_data = db.table("emails")\
        .select("*")\
        .eq("id", email_id)\
        .single()\
        .execute()

    if not email_data.data:
        print(f"Email {email_id} not found")
        return

    email = email_data.data
    body = email.get("body_text", "")

    # run duplicate check
    result = is_duplicate_question(body, user_id)

    print(f"Email {email_id} → Duplicate: {result['is_duplicate']} | Score: {result['similarity_score']}")

    # update the email_categories table
    db.table("email_categories")\
        .update({
            "is_duplicate_question": result["is_duplicate"],
            "matched_job_posting_id": result["matched_posting_id"]
        })\
        .eq("email_id", email_id)\
        .execute()

    return result


if __name__ == "__main__":
    # test manually with fake text
    test_body = "Hi, I wanted to ask what the salary range is for this position?"

    # use the user_id you inserted in Supabase
    test_user_id = "4abe83e2-0bca-465e-8aaa-eff3f3271a4a"

    result = is_duplicate_question(test_body, test_user_id)
    print(f"Is duplicate: {result['is_duplicate']}")
    print(f"Similarity score: {result['similarity_score']}")
    print(f"Matched posting: {result['matched_posting_id']}")
    print(f"Matched question: {result['matched_question']}")
    print(f"Matched chunk: {result['matched_chunk']}")