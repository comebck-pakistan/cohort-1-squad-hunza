import io
import httpx
import re
from urllib.parse import urlparse
from pypdf import PdfReader
from docx import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from database import get_db
from app.modules.gmail_integration import gmail_client

BLOCKED_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
}
SUSPICIOUS_TLDS = {".zip", ".mov", ".xyz", ".top", ".click", ".gq", ".tk"}


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
    try:
        db = get_db()

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"format": "full"}
            )
            resp.raise_for_status()
            raw_message = resp.json()

        attachments = gmail_client.get_attachment_info(raw_message.get("payload", {}))

        if not attachments:
            print(f"No attachments found for email {email_id}")
            return None

        resume_attachment = None
        extra_attachments = []
        for att in attachments:
            filename = att["filename"].lower()
            is_doc = filename.endswith(".pdf") or filename.endswith(".docx")
            if not is_doc:
                continue
            if resume_attachment is None and ("resume" in filename or "cv" in filename):
                resume_attachment = att
            else:
                extra_attachments.append(att)

        # fallback: if nothing matched "resume"/"cv" by name, treat the first doc as the resume
        if not resume_attachment and extra_attachments:
            resume_attachment = extra_attachments.pop(0)

        if not resume_attachment:
            print(f"No PDF or DOCX attachment found for email {email_id}")
            return None

        file_bytes = await gmail_client.get_attachment(
            access_token,
            message_id,
            resume_attachment["attachment_id"]
        )

        filename = resume_attachment["filename"]
        storage_path = f"resumes/{user_id}/{email_id}/{filename}"

        db.storage.from_("Resumes").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": resume_attachment["mime_type"]}
        )

        file_url = db.storage.from_("Resumes").get_public_url(storage_path)

        
        db.table("candidate_documents").insert({
            "email_id": email_id,
            "file_url": file_url,
            "original_filename": filename,
            "uploaded_at": "now()"
        }).execute()

        print(f"Resume uploaded: {file_url}")

        extra_document_urls = []
        for extra_att in extra_attachments:
            try:
                extra_bytes = await gmail_client.get_attachment(
                    access_token,
                    message_id,
                    extra_att["attachment_id"]
                )
                extra_filename = extra_att["filename"]
                extra_storage_path = f"resumes/{user_id}/{email_id}/{extra_filename}"

                db.storage.from_("Resumes").upload(
                    path=extra_storage_path,
                    file=extra_bytes,
                    file_options={"content-type": extra_att["mime_type"]}
                )
                extra_url = db.storage.from_("Resumes").get_public_url(extra_storage_path)
                extra_document_urls.append(extra_url)

                db.table("candidate_documents").insert({
                    "email_id": email_id,
                    "file_url": extra_url,
                    "original_filename": extra_filename,
                    "uploaded_at": "now()"
                }).execute()
            except Exception as e:
                print(f"Extra document upload failed for {extra_att['filename']} on email {email_id}: {e}")

        resume_text = extract_text_from_bytes(file_bytes, filename)

        email_data = db.table("emails")\
            .select("body_text")\
            .eq("id", email_id)\
            .single()\
            .execute()

        email_body = email_data.data.get("body_text", "") if email_data.data else ""

        candidate_info = extract_candidate_info(email_body, resume_text)

        # sanitize extracted text links, then merge in real attachment urls (if any)
        safe_links = sanitize_links(candidate_info.get("all_links", []))
        candidate_info["all_links"] = extra_document_urls + safe_links

        save_candidate(email_id, user_id, candidate_info, file_url, resume_text)

        return candidate_info

    except Exception as e:
        print(f"Resume processing failed for email {email_id}: {e}")
        return None


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
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
    llm = get_llm()
    parser = StrOutputParser()

    max_resume_chars = 1800
    max_email_chars = 500 if len(resume_text) > 500 else 1000

    prompt = ChatPromptTemplate.from_messages([
        ('system', '''You are an HR assistant extracting candidate information.

    Read the email body and resume text below and extract the following.
    Only extract information that is explicitly stated in the text below.
    Do not guess, infer, or fill in typical/plausible values.
    If a field is not clearly present, respond with "N/A" for that field.

    - full_name: candidate's full name
    - candidate_email: candidate's email address
    - role_applied_for: the role they are applying for
    - years_of_experience: number of years of experience (number only)
    - skills: list of technical skills mentioned (comma separated)
    - summary: a 1-2 sentence professional summary of the candidate, based only on what is written
    - education_degree: the degree name exactly as written (e.g. "B.S. Computer Science"). Use "N/A" if not mentioned.
    - education_institution: the university/institution name exactly as written. Use "N/A" if not mentioned.
    - education_gpa: the GPA/CGPA exactly as written, including scale if given (e.g. "3.8/4.0"). Use "N/A" if not mentioned anywhere in the resume — do not estimate or assume a typical GPA.
    - all_links: every http:// or https:// URL mentioned anywhere in the email or resume text, comma separated. 
      Include GitHub, Behance, personal websites, LinkedIn, or any other links exactly as written. 
      Do not invent or modify any URL — only include links that literally appear in the text. Use "N/A" if no links are present.

    Email Body: {email_body}
    Resume Text: {resume_text}

    Respond in this exact format and nothing else:
    full_name: <value>
    candidate_email: <value>
    role_applied_for: <value>
    years_of_experience: <value>
    skills: <comma separated skills>
    summary: <value>
    education_degree: <value>
    education_institution: <value>
    education_gpa: <value>
    all_links: <comma separated urls>
    ''')
    ])

    chain = prompt | llm | parser
    result = chain.invoke({
        "email_body": email_body[:max_email_chars],
        "resume_text": resume_text[:max_resume_chars]
    })

    info = {
        "full_name": None,
        "candidate_email": None,
        "role_applied_for": None,
        "years_of_experience": None,
        "skills": [],
        "summary": None,
        "education_degree": None,
        "education_institution": None,
        "education_gpa": None,
        "all_links": [],
    }

    def _clean(value: str) -> str | None:
        value = value.strip()
        if value.upper() in ("N/A", "NA", "NONE", ""):
            return None
        return value

    for line in result.strip().split("\n"):
        if line.startswith("full_name:"):
            info["full_name"] = _clean(line.replace("full_name:", ""))
        elif line.startswith("candidate_email:"):
            info["candidate_email"] = _clean(line.replace("candidate_email:", ""))
        elif line.startswith("role_applied_for:"):
            info["role_applied_for"] = _clean(line.replace("role_applied_for:", ""))
        elif line.startswith("years_of_experience:"):
            info["years_of_experience"] = _clean(line.replace("years_of_experience:", ""))
        elif line.startswith("skills:"):
            skills_str = line.replace("skills:", "").strip()
            if skills_str.upper() not in ("N/A", "NA", "NONE", ""):
                info["skills"] = [s.strip() for s in skills_str.split(",") if s.strip()]
        elif line.startswith("summary:"):
            info["summary"] = _clean(line.replace("summary:", ""))
        elif line.startswith("education_degree:"):
            info["education_degree"] = _clean(line.replace("education_degree:", ""))
        elif line.startswith("education_institution:"):
            info["education_institution"] = _clean(line.replace("education_institution:", ""))
        elif line.startswith("education_gpa:"):
            info["education_gpa"] = _clean(line.replace("education_gpa:", ""))
        elif line.startswith("all_links:"):
            links_str = line.replace("all_links:", "").strip()
            if links_str.upper() not in ("N/A", "NA", "NONE", ""):
                info["all_links"] = [u.strip() for u in links_str.split(",") if u.strip()]

    return info


def sanitize_links(links: list[str]) -> list[str]:
    safe_links = []
    for link in links:
        try:
            if not re.match(r"^https?://", link, re.IGNORECASE):
                continue
            parsed = urlparse(link)
            host = parsed.hostname or ""

            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
                continue

            if host.lower() in BLOCKED_DOMAINS:
                continue

            if any(host.lower().endswith(tld) for tld in SUSPICIOUS_TLDS):
                continue

            if len(link) > 500:
                continue

            safe_links.append(link)
        except Exception:
            continue
    return safe_links


def save_candidate(email_id, user_id, candidate_info, file_url, resume_text=None):
    db = get_db()
    result = db.table("candidates").insert({
        "email_id": email_id,
        "user_id": user_id,
        "full_name": candidate_info.get("full_name"),
        "candidate_email": candidate_info.get("candidate_email"),
        "role_applied_for": candidate_info.get("role_applied_for"),
        "skills_extracted": candidate_info.get("skills"),
        "resume_file_url": file_url,
        "years_of_experience": candidate_info.get("years_of_experience"),
        "summary": candidate_info.get("summary"),
        "education_degree": candidate_info.get("education_degree"),
        "education_institution": candidate_info.get("education_institution"),
        "education_gpa": candidate_info.get("education_gpa"),
        "all_links": candidate_info.get("all_links", []),
        "resume_text": resume_text,
    }).execute()

    if result.data:
        print(f"Candidate saved: {candidate_info.get('full_name')}")
        return result.data[0]

    return None