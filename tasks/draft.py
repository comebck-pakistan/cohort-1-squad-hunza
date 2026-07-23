from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from database import get_db
from datetime import datetime, timezone


def generate_draft(email_id: str) -> str:
    """
    Fetches email content and category from Supabase,
    then generates a professional draft reply using Groq.
    Returns the draft text as a string.
    """
    db = get_db()

    # fetch email from emails table
    email_data = db.table("emails")\
        .select("*")\
        .eq("id", email_id)\
        .single()\
        .execute()

    if not email_data.data:
        print(f"Email {email_id} not found")
        return None

    email = email_data.data
    subject = email.get("subject", "")
    body = email.get("body_text", "")

    # fetch category from email_categories table
    category_data = db.table("email_categories")\
        .select("category, priority")\
        .eq("email_id", email_id)\
        .single()\
        .execute()

    category = "General Inquiry"
    priority = "Medium"

    if category_data.data:
        category = category_data.data.get("category", "General Inquiry")
        priority = category_data.data.get("priority", "Medium")

    # build the prompt
    llm = get_llm()
    parser = StrOutputParser()

    prompt = ChatPromptTemplate.from_messages([
        ('system', '''You are a professional HR assistant writing email replies 
        on behalf of an HR recruiter.

        Write a professional, polite, and concise reply to the email below.
        
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
        "body": body
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


def generate_and_save(email_id: str) -> dict:
    """
    Main entry point - called by Celery worker.
    Generates a draft reply and saves it to the database.
    Returns the saved draft record.
    """
    print(f"Generating draft for email {email_id}...")

    # generate the draft
    draft_body = generate_draft(email_id)

    if not draft_body:
        print(f"Draft generation failed for email {email_id}")
        return None

    # save it to the database
    saved_draft = save_draft(email_id, draft_body)

    print(f"Draft generated and saved for email {email_id}")
    print(f"Draft preview: {draft_body[:100]}...")

    return saved_draft


if __name__ == "__main__":
    # test manually using a real email_id from your Supabase emails table
    test_email_id = "84289971-071e-4a5b-85d0-af4eeb3435e4"
    result = generate_and_save(test_email_id)
    print(f"\nFull draft:\n{result}")