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
    try:
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
        portfolio_attachment = None
        for att in attachments:
            filename = att["filename"].lower()
            if filename.endswith(".pdf") or filename.endswith(".docx"):
                if resume_attachment is None:
                    resume_attachment = att
                elif portfolio_attachment is None and "portfolio" in filename:
                    portfolio_attachment = att

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

        db.storage.from_("Resumes").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": resume_attachment["mime_type"]}
        )

        portfolio_attachment_url = None
        if portfolio_attachment:
            try:
                portfolio_bytes = await gmail_client.get_attachment(
                    access_token,
                    message_id,
                    portfolio_attachment["attachment_id"]
                )
                portfolio_filename = portfolio_attachment["filename"]
                portfolio_storage_path = f"resumes/{user_id}/{email_id}/portfolio_{portfolio_filename}"

                db.storage.from_("Resumes").upload(
                    path=portfolio_storage_path,
                    file=portfolio_bytes,
                    file_options={"content-type": portfolio_attachment["mime_type"]}
                )
                portfolio_attachment_url = db.storage.from_("Resumes").get_public_url(portfolio_storage_path)
            except Exception as e:
                print(f"Portfolio attachment upload failed for email {email_id}: {e}")

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

        # prefer an actual portfolio attachment over a text-extracted link, if both exist
        if portfolio_attachment_url:
            candidate_info["portfolio_url"] = portfolio_attachment_url


        # save to candidates table
        save_candidate(email_id, user_id, candidate_info, file_url, resume_text)

        return candidate_info

    except Exception as e:
        print(f"Resume processing failed for email {email_id}: {e}")
        return None

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
    llm = get_llm()
    parser = StrOutputParser()
    
    # keep total context small enough for Groq's 8000 TPM limit
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
    - portfolio_url: a link to the candidate's portfolio, GitHub, Behance, personal website, or similar professional showcase site, 
      if mentioned anywhere in the email or resume. Use "N/A" if no such link is present. 
      Do not use LinkedIn URLs for this field even if present — only use it if a dedicated portfolio/GitHub/Behance/personal site link is given.

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
    portfolio_url: <value>
    ''')
])

    chain = prompt | llm | parser
    result = chain.invoke({
        "email_body": email_body[:max_email_chars],
        "resume_text": resume_text[:max_resume_chars]
    })

    # parse the response
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
        "portfolio_url": None,
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
        elif line.startswith("portfolio_url:"):
            info["portfolio_url"] = _clean(line.replace("portfolio_url:", ""))

    return info


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
        "portfolio_url": candidate_info.get("portfolio_url"),
        "resume_text": resume_text,
    }).execute()

    if result.data:
        print(f"Candidate saved: {candidate_info.get('full_name')}")
        return result.data[0]
    return None