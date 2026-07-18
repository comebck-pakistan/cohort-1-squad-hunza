from tasks.classifier import classify_email

def test_classifier_returns_category():
    result = classify_email(
        subject="I am applying for the AI Engineer role",
        body="Please find my CV attached. I have 3 years of experience."
    )
    assert result["category"] == "New Applicant"
    assert result["priority"] in ["High", "Medium", "Low"]

def test_classifier_detects_spam():
    result = classify_email(
        subject="Buy cheap watches now",
        body="Click here for amazing deals on luxury watches!"
    )
    assert result["category"] != "New Applicant"