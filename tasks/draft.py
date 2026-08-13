from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from database import get_db
from datetime import datetime, timezone


def generate_draft(email_id: str, guidance: str | None = None) -> str:
    """
    Fetches email content and category from Supabase,
    then generates a professional draft reply using Groq.
    If guidance is provided, the HR's specific instructions are followed;
    otherwise a normal generic professional reply is generated.
    Returns the draft text as a string.
    """
    db = get_db()

    email_data = db.table("emails")\
        .select("*")\
        .eq("id", email_id)\
        .maybe_single()\
        .execute()

    if not email_data.data:
        print(f"Email {email_id} not found")
        return None

    email = email_data.data
    subject = email.get("subject", "")
    body = email.get("body_text", "")

    category_data = db.table("email_categories")\
        .select("category, priority")\
        .eq("email_id", email_id)\
        .maybe_single()\
        .execute()

    category = "General Inquiry"
    priority = "Medium"

    if category_data.data:
        category = category_data.data.get("category", "General Inquiry")
        priority = category_data.data.get("priority", "Medium")

    llm = get_llm()
    parser = StrOutputParser()

    guidance_block = (
        f"\nAdditional instructions from the HR recruiter for this specific reply "
        f"(follow these closely, they take priority over the default guidelines below):\n{guidance}\n"
        if guidance and guidance.strip()
        else ""
    )

    prompt = ChatPromptTemplate.from_messages([
        ('system', '''You are a professional HR assistant writing email replies 
        on behalf of an HR recruiter.

        Write a professional, polite, and concise reply to the email below.
        {guidance_block}
        Guidelines:
        - Match the tone to the category and priority
        - For High priority emails be more prompt and urgent in tone
        - For New Applicant emails acknowledge receipt and set expectations
        - For Interview Scheduling emails confirm or propose times
        - For Offer Acceptance emails be warm and welcoming
        - For Candidate Withdrawal emails be understanding and professional
        - Keep the reply focused and under 150 words
        - Do not include a subject line
        - Do not include placeholders like [Your Name] - write as "HR Team"
        - Write only the email body, nothing else

        Email Category: {category}
        Email Priority: {priority}
        Email Subject: {subject}
        Email Body: {body}
        ''')
    ])

    chain = prompt | llm | parser
    draft = chain.invoke({
        "category": category,
        "priority": priority,
        "subject": subject,
        "body": body,
        "guidance_block": guidance_block,
    })

    return draft.strip()


def save_draft(email_id: str, draft_body: str) -> dict:
    """
    Saves a generated draft to the email_drafts table
    with status set to pending.
    Returns the saved record.
    """
    db = get_db()

    result = db.table("email_drafts").insert({
        "email_id": email_id,
        "draft_body": draft_body,
        "status": "pending",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }).execute()

    if result.data:
        print(f"Draft saved for email {email_id} with status: pending")
        return result.data[0]
    else:
        print(f"Failed to save draft for email {email_id}")
        return None


def generate_and_save(email_id: str, guidance: str | None = None) -> dict:
    """
    Generates and saves a draft reply. Only called when HR explicitly
    requests it. If guidance is given, the draft follows those specific
    instructions; otherwise a normal generic reply is generated.
    """
    draft_body = generate_draft(email_id, guidance)
    if not draft_body:
        return None
    return save_draft(email_id, draft_body)

   


if __name__ == "__main__":
    # test manually using a real email_id from your Supabase emails table
    test_email_id = "84289971-071e-4a5b-85d0-af4eeb3435e4"
    result = generate_and_save(test_email_id)
    print(f"\nFull draft:\n{result}")