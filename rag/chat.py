from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from database import get_db
from rag.retriever import retrieve
from datetime import datetime, timezone
import asyncio

def rewrite_question_with_history(question: str, history: list[dict]) -> str:
    """
    Uses recent conversation turns to rewrite a possibly-ambiguous follow-up
    question into a standalone question retrieval can act on directly.
    E.g. "share their subjects" after "how many emails today?" becomes
    "list the subjects of today's emails". No-op if there's no history,
    or if the question is already self-contained.
    """
    if not history:
        return question

    history_text = "\n".join(
        f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['text']}"
        for h in history[-6:]  # last 6 turns is plenty of context
    )

    llm = get_llm()
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


async def ask(question: str, user_id: str, history: list[dict] | None = None) -> dict:
    """
    Main entry point for the RAG chat assistant.
    Takes a plain English question from the HR and returns an answer.

    Flow:
    1. retrieve() decides structured vs semantic
    2. If structured → return direct database answer
    3. If semantic → pass retrieved emails to Groq for answer
    """
    standalone_question = rewrite_question_with_history(question, history or [])

    retrieval = await retrieve(standalone_question, user_id)

    # structured query — already has a direct answer
    if retrieval["type"] == "structured":
        return {
            "question": question,
            "answer": retrieval["answer"],
            "type": "structured",
            "sources": []
        }

    # semantic search — pass results to LLM for natural language answer
    results = retrieval.get("results", [])

    if not results:
        return {
            "question": question,
            "answer": "I couldn't find any relevant emails matching your question.",
            "type": "semantic",
            "sources": []
        }

    # build context from retrieved emails
    context = ""
    sources = []
    for i, result in enumerate(results):
        email_id = result.get("email_id")
        subject = result.get("subject", "No subject")
        body = result.get("body_text", "")[:500]  # limit each email to 500 chars
        context += f"\nEmail {i+1}:\nSubject: {subject}\nContent: {body}\n"
        sources.append({"email_id": email_id, "subject": subject})

    # generate answer using Groq
    llm = get_llm()
    parser = StrOutputParser()

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
    answer = chain.invoke({
        "context": context,
        "question": question
    })

    # save chat history to database
    save_chat_message(user_id, question, answer)

    return {
        "question": question,
        "answer": answer.strip(),
        "type": "semantic",
        "sources": sources
    }


def save_chat_message(user_id: str, question: str, answer: str):
    """
    Saves chat history to chat_messages table.
    """
    db = get_db()
    db.table("chat_messages").insert({
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()


if __name__ == "__main__":
    import asyncio
    # test manually
    # add this to the __main__ block in rag/chat.py temporarily
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
            result =await ask(q, test_user_id)
            print(f"Answer: {result['answer']}")
            print(f"Type: {result['type']}")

    asyncio.run(main())