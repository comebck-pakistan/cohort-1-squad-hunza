from langchain_core.prompts import ChatPromptTemplate 
from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from database import get_db
def classifier(subject:str,body:str) -> str:
    llm=get_llm()
    parser=StrOutputParser()

    prompt=ChatPromptTemplate.from_messages([
        ('system','''You are an Hr assistant Ai that will deal with 
        incomming emails to the Hr's inbox. You are tsked to do to main things. You will first read the Subject and Body of the Email and
        identify the email's core querry or a set of Questions being asked in the 
        email and then tag the email to a specific Label on the basis of those questions or the type of email, from the ones provided below.
        Each email will be provided a category from the ones below.
        
        1. Read the email below and classify it into EXACTLY ONE of these categories:
        - New Applicant: someone applying for a role for the first time
        - Candidate Follow-up: a candidate checking in on their application status
        - Interview Scheduling: a request or confirmation to schedule an interview
        - Interview Reschedule: a request to change an existing interview time
        - Documents Submitted: candidate sending required documents or certificates
        - Offer Acceptance: candidate accepting a job offer
        - Offer Rejection: candidate declining a job offer
        - General Inquiry: a genuine question about the role or company
        - Referral: someone referring another candidate for a role
        - Candidate Withdrawal: candidate withdrawing their application
        
        Now the second task is to identify the priority of the email on the basis of urgency and you have to prioritize on the basis given below.

        2. Priority — exactly one from: High, Medium, Low
        High = urgent time-sensitive (interview tomorrow, offer expiring, etc.)
        Medium = needs response soon but not urgent
        Low = informational, no immediate action needed

        Email Subject: {subject}
        Email Body: {body}

        Respond in this exact format and nothing else:
        Category: <category here>
        Priority: <priority here>''' 
        )])

    chain=prompt|llm|parser
    result=chain.invoke({"subject":subject,"body":body})
    lines=result.strip().split("\n")
    category='General Inquiry'
    priority='Medium'

    for line in lines:
        if line.startswith('Category:'):
            category=line.replace("Category:","")
        elif line.startswith("Priority:"):
            priority=line.replace("Priority:","")


    return {"category": category.strip(), "priority": priority.strip()}


def classify_and_save(email_id:str):
    db=get_db()
    email_data=db.table("emails").select("*")\
    .eq("id",email_id).single()\
    .execute()

    if not email_data.data:
        print("Email not found")
        return

    email=email_data.data
    subject=email.get('subject','')
    body=email.get('body_text','')

    classification=classifier(subject,body)
    category=classification.get("category","")
    priority=classification.get("priority","")
    print(f"Email {email_id} → Category: {category} | Priority: {priority}")

    db.table('email_categories').insert({
        "email_id":email_id,
        "category":category,
        "priority":priority,
        "confidence_score":1.0,
        "is_duplicate_question":False
    }).execute()

    db.table('emails').update({
        "is_processed":True
    }).eq("id",email_id).execute()

    return f"Category: {category} Priority: {priority}"




    # #def classify_and_save(email_id: str):
    # db = get_db()

    # email_data = db.table("emails")\
    #     .select("*")\
    #     .eq("id", email_id)\
    #     .single()\
    #     .execute()

    # if not email_data.data:
    #     print(f"Email {email_id} not found")
    #     return

    # email = email_data.data
    # subject = email.get("subject", "")
    # body = email.get("body_text", "")

    # # run classification
    # result = classify_email(subject, body)
    # category = result.get("category", "General Inquiry")
    # priority = result.get("priority", "Medium")

    # print(f"Email {email_id} → Category: {category} | Priority: {priority}")

    # # save to email_categories table
    # db.table("email_categories").insert({
    #     "email_id": email_id,
    #     "category": category,
    #     "priority": priority,
    #     "confidence_score": 1.0,
    #     "is_duplicate_question": False,
    # }).execute()

    # # mark email as processed
    # db.table("emails")\
    #     .update({"is_processed": True})\
    #     .eq("id", email_id)\
    #     .execute()

    # return {"category": category, "priority": priority}