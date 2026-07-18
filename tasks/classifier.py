from langchain_core.prompts import ChatMessagePromptTemplate,ChatPromptTemplate 
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
    return result

result = classifier(
    subject="Interview tomorrow at 10am - can we reschedule?",
    body="Hi, I have a conflict tomorrow morning. Can we move the interview to the afternoon?"
)
print(result)