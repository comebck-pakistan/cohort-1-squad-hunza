import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from database import get_db
from rag.retriever import retrieve
from datetime import datetime, timezone
from config import get_chat_llm

def rewrite_question_with_history(question: str, history: list[dict]) -> str:
    """
    Uses recent conversation turns to rewrite a possibly-ambiguous follow-up
    question into a standalone question retrieval can act on directly.
    No-op if there's no history, or if the question is already self-contained.
    """
    if not history:
        return question

    history_text = "\n".join(
        f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['text']}"
        for h in history[-6:]
    )

    llm = get_chat_llm()
    parser = StrOutputParser()
    prompt = ChatPromptTemplate.from_messages([
        ('system', '''Given the recent conversation and a new follow-up question,
        rewrite the follow-up into a complete, standalone question that makes
        sense on its own - resolving pronouns like "they/them/their" and vague
        references like "that" using the conversation history.

        If the follow-up question is already standalone and doesn't depend on
        the conversation, return it EXACTLY as-is.

        Only output the rewritten question, nothing else - no explanation.

        Conversation so far:
        {history}

        Follow-up question: {question}

        Standalone question:''')
    ])
    chain = prompt | llm | parser
    rewritten = chain.invoke({"history": history_text, "question": question})
    return rewritten.strip()


def _sources_from_tool_results(tool_results: list[dict]) -> list[dict]:
    """Extracts {email_id, subject} pairs from tool results for frontend
    'referenced links' - best-effort, since not every tool/row has an
    email_id (e.g. candidates without a linked email)."""
    sources = []
    for tr in tool_results:
        rows = tr["data"] if isinstance(tr["data"], list) else []
        for row in rows:
            email_id = row.get("id") if tr["tool"] == "query_emails" else row.get("email_id")
            if not email_id:
                continue
            label = row.get("subject") or row.get("full_name") or row.get("draft_body", "")[:40] or "View details"
            sources.append({"email_id": email_id, "subject": label})
    return sources


async def ask(question: str, user_id: str, history: list[dict] | None = None) -> dict:
    """
    Main entry point for the RAG chat assistant.

    Flow:
    1. rewrite_question_with_history() resolves follow-ups into standalone questions
    2. retrieve() lets the LLM pick a database tool (structured) or falls back
       to vector similarity search (semantic)
    3. Either way, results are handed to the LLM to write the final answer,
       grounded strictly in the actual returned data
    """
    standalone_question = rewrite_question_with_history(question, history or [])
    retrieval = await retrieve(standalone_question, user_id)

    llm = get_chat_llm()
    parser = StrOutputParser()

    if retrieval["type"] == "structured":
        tool_results = retrieval["tool_results"]

        if not tool_results:
            answer = "I couldn't find a way to answer that from the available data."
            sources = []
        else:
            context = "\n\n".join(
                f"Tool called: {tr['tool']}\nFilters used: {tr['args']}\nResults: {json.dumps(tr['data'], default=str)}"
                for tr in tool_results
            )
            sources = _sources_from_tool_results(tool_results)

            prompt = ChatPromptTemplate.from_messages([
                ('system', '''You are an HR assistant. Answer the user's question using the
                database results below as your source of truth - never invent facts not
                present in them.

                You MAY reason over the data: compare candidates, rank them, summarize
                patterns, or explain your reasoning - this is expected when asked to
                compare or evaluate. If asked "how many", count the items in the results
                yourself if an explicit count isn't given. If the results are empty, say
                so plainly instead of guessing.

                Database Results:
                {context}

                Question: {question}

                Answer:''')
            ])
            chain = prompt | llm | parser
            answer = chain.invoke({"context": context, "question": question}).strip()

        save_chat_message(user_id, question, answer)
        return {"question": question, "answer": answer, "type": "structured", "sources": sources}

    # semantic path - vector similarity fallback for fuzzy/conceptual questions
    results = retrieval.get("results", [])

    if not results:
        answer = "I couldn't find any relevant emails matching your question."
        save_chat_message(user_id, question, answer)
        return {"question": question, "answer": answer, "type": "semantic", "sources": []}

    context = ""
    sources = []
    for i, result in enumerate(results):
        email_id = result.get("email_id")
        subject = result.get("subject", "No subject")
        body = result.get("body_text", "")[:500]
        context += f"\nEmail {i+1}:\nSubject: {subject}\nContent: {body}\n"
        sources.append({"email_id": email_id, "subject": subject})

    prompt = ChatPromptTemplate.from_messages([
        ('system', '''You are an HR assistant answering questions about
        the HR's email inbox.

        Answer the question based ONLY on the email context provided below.
        Be concise and specific. If the answer is not in the context, say so.
        Never make up information.

        Email Context:
        {context}

        Question: {question}

        Provide a clear, helpful answer:''')
    ])
    chain = prompt | llm | parser
    answer = chain.invoke({"context": context, "question": question}).strip()

    save_chat_message(user_id, question, answer)
    return {"question": question, "answer": answer, "type": "semantic", "sources": sources}


def save_chat_message(user_id: str, question: str, answer: str):
    """Saves chat history to chat_messages table."""
    db = get_db()
    db.table("chat_messages").insert({
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()


if __name__ == "__main__":
    import asyncio

    async def main():
        from rag.embedder import embed_and_save_email
        await embed_and_save_email("84289971-071e-4a5b-85d0-af4eeb3435e4")
        test_user_id = "4abe83e2-0bca-465e-8aaa-eff3f3271a4a"

        questions = [
            "How many emails did I receive today?",
            "Do we have any candidates with Python experience?",
            "How many pending drafts do I have?",
        ]

        for q in questions:
            print(f"\nQuestion: {q}")
            result = await ask(q, test_user_id)
            print(f"Answer: {result['answer']}")
            print(f"Type: {result['type']}")

    asyncio.run(main())