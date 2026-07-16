from ai_worker.tasks.draft import generate_draft_reply


def test_generate_draft_reply():
    assert generate_draft_reply("Hello") == ""
