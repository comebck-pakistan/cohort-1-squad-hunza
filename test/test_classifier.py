from tasks.classifier import classifier

def test_classifier_new_applicant():
    result = classifier(
        subject="Applying for AI Engineer Role",
        body="Hi, I am applying for the AI Engineer position. Please find my CV attached."
    )
    assert result["category"] == "New Applicant"
    assert result["priority"] in ["High", "Medium", "Low"]

def test_classifier_interview_reschedule():
    result = classifier(
        subject="Need to reschedule my interview",
        body="Hi, I had an interview scheduled for tomorrow but I need to reschedule it."
    )
    assert result["category"] == "Interview Reschedule"
    assert result["priority"] == "High"

def test_classifier_spam():
    result = classifier(
        subject="Buy cheap watches now",
        body="Click here for amazing deals on luxury watches at discount prices!"
    )
    assert result["category"] == "General Inquiry"
    assert result["priority"] in ["High", "Medium", "Low"]

def test_classifier_returns_dict():
    result = classifier(
        subject="Test email",
        body="This is a test email body."
    )
    assert isinstance(result, dict)
    assert "category" in result
    assert "priority" in result

def test_classifier_priority_values():
    result = classifier(
        subject="Following up on my application",
        body="Hi, I applied last week and wanted to follow up on my application status."
    )
    assert result["priority"] in ["High", "Medium", "Low"]
    assert result["category"] in [
        "New Applicant",
        "Candidate Follow-up",
        "Interview Scheduling",
        "Interview Reschedule",
        "Documents Submitted",
        "Offer Acceptance",
        "Offer Rejection",
        "General Inquiry",
        "Referral",
        "Candidate Withdrawal"
    ]