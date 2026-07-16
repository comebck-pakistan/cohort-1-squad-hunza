from ai_worker.tasks.classifier import classify_email


def test_classify_email():
    assert classify_email("Hello") == "unclassified"
