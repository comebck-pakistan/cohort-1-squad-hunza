from ai_worker.rag.embedder import embed_text


def test_embed_text():
    assert embed_text("Hello") == []
