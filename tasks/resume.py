import io
import httpx
from pypdf import PdfReader
from docx import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from database import get_db
from app.modules.gmail_integration import gmail_client


async def process_resume_from_gmail(
    access_token: str,
    message_id: str,
    email_id: str,
    user_id: str
) -> dict:
    """
    Main entry point called from service.py.
    Downloads attachment from Gmail, uploads to Supabase Storage,
    extracts candidate info, saves to candidates table.
    """
    db = get_db()

    # get raw message payload to find attachment info
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"format": "full"}
        )
        resp.raise_for_status()
        raw_message = resp.json()

    # get attachment info from payload
    attachments = gmail_client.get_attachment_info(raw_message.get("payload", {}))

    if not attachments:
        print(f"No attachments found for email {email_id}")
        return None

    # process first resume attachment found
    # filter for PDF and DOCX only
    resume_attachment = None
    for att in attachments:
        filename = att["filename"].lower()
        if filename.endswith(".pdf") or filename.endswith(".docx"):
            resume_attachment = att
            break

    if not resume_attachment:
        print(f"No PDF or DOCX attachment found for email {email_id}")
        return None

    # download attachment bytes from Gmail
    file_bytes = await gmail_client.get_attachment(
        access_token,
        message_id,
        resume_attachment["attachment_id"]
    )

    # upload to Supabase Storage
    filename = resume_attachment["filename"]
    storage_path = f"resumes/{user_id}/{email_id}/{filename}"

    db.storage.from_("resumes").upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": resume_attachment["mime_type"]}
    )

    # get public URL
    file_url = db.storage.from_("Resumes").get_public_url(storage_path)

    # save to candidate_documents table
    db.table("candidate_documents").insert({
        "email_id": email_id,
        "file_url": file_url,
        "original_filename": filename,
        "uploaded_at": "now()"
    }).execute()

    print(f"Resume uploaded: {file_url}")

    # extract text from file
    resume_text = extract_text_from_bytes(file_bytes, filename)

    # fetch email body for context
    email_data = db.table("emails")\
        .select("body_text")\
        .eq("id", email_id)\
        .single()\
        .execute()

    email_body = email_data.data.get("body_text", "") if email_data.data else ""

    # extract candidate info using AI
    candidate_info = extract_candidate_info(email_body, resume_text)

    # save to candidates table
    save_candidate(email_id, user_id, candidate_info, file_url)

    return candidate_info


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extracts plain text from PDF or DOCX file bytes.
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()

    elif filename_lower.endswith(".docx"):
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()

    return ""


def extract_candidate_info(email_body: str, resume_text: str) -> dict:
    """
    Uses Groq to extract structured candidate information
    from email body and resume text.
    Returns a dict with name, email, role, skills.
    """
    llm = get_llm()
    parser = StrOutputParser()

    prompt = ChatPromptTemplate.from_messages([
        ('system', '''You are an HR assistant extracting candidate information.

        Read the email body and resume text below and extract the following:
        - full_name: candidate's full name
        - candidate_email: candidate's email address
        - role_applied_for: the role they are applying for
        - years_of_experience: number of years of experience (number only)
        - skills: list of technical skills mentioned (comma separated)

        Email Body: {email_body}
        Resume Text: {resume_text}

        Respond in this exact format and nothing else:
        full_name: <value>
        candidate_email: <value>
        role_applied_for: <value>
        years_of_experience: <value>
        skills: <comma separated skills>
        ''')
    ])

    chain = prompt | llm | parser
    result = chain.invoke({
        "email_body": email_body,
        "resume_text": resume_text[:3000]  # limit to avoid token overflow
    })

    # parse the response
    info = {
        "full_name": None,
        "candidate_email": None,
        "role_applied_for": None,
        "years_of_experience": None,
        "skills": []
    }

    for line in result.strip().split("\n"):
        if line.startswith("full_name:"):
            info["full_name"] = line.replace("full_name:", "").strip()
        elif line.startswith("candidate_email:"):
            info["candidate_email"] = line.replace("candidate_email:", "").strip()
        elif line.startswith("role_applied_for:"):
            info["role_applied_for"] = line.replace("role_applied_for:", "").strip()
        elif line.startswith("years_of_experience:"):
            info["years_of_experience"] = line.replace("years_of_experience:", "").strip()
        elif line.startswith("skills:"):
            skills_str = line.replace("skills:", "").strip()
            info["skills"] = [s.strip() for s in skills_str.split(",")]

    return info


def save_candidate(
    email_id: str,
    user_id: str,
    candidate_info: dict,
    file_url: str
) -> dict:
    """
    Saves extracted candidate information to the candidates table.
    """
    db = get_db()

    result = db.table("candidates").insert({
        "email_id": email_id,
        "user_id": user_id,
        "full_name": candidate_info.get("full_name"),
        "candidate_email": candidate_info.get("candidate_email"),
        "role_applied_for": candidate_info.get("role_applied_for"),
        "skills_extracted": candidate_info.get("skills"),
        "resume_file_url": file_url
    }).execute()

    if result.data:
        print(f"Candidate saved: {candidate_info.get('full_name')}")
        return result.data[0]

    return None