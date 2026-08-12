import json
from langchain_core.messages import HumanMessage, ToolMessage
from config import get_llm
from rag.tools import query_emails, query_drafts, query_candidates
from rag.embedder import embed_text
from database import get_db
from config import get_chat_llm_with_tools

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "query_emails",
            "description": "Search/list/count the user's received emails with optional filters. Use for any question about emails - their subjects, senders, categories, priorities, or counts, for any time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_range": {
                        "type": "string",
                        "enum": ["today", "yesterday", "this_week", "all_time"],
                        "description": "Time window to filter emails by. Default to all_time if not specified.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by exact category, e.g. 'New Applicant', 'Interview Scheduling', 'General Inquiry'. Omit if not asked.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["High", "Medium", "Low"],
                        "description": "Filter by priority. Omit if not asked.",
                    },
                    "sender_contains": {
                        "type": "string",
                        "description": "Filter by partial sender email match. Omit if not asked.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of emails to return. Default 20.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_drafts",
            "description": "Search/list/count AI-generated draft replies awaiting approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "sent", "edited"],
                        "description": "Filter by draft status. Default pending.",
                    },
                    "limit": {"type": "integer", "description": "Max number to return. Default 20."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_candidates",
            "description": "Search/list/count candidate records - useful for questions about applicants, roles applied for, or skills.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_applied_for": {
                        "type": "string",
                        "description": "Filter by role/position applied for, partial match. Omit if not asked.",
                    },
                    "skill_contains": {
                        "type": "string",
                        "description": "Filter by a specific skill the candidate should have. Omit if not asked.",
                    },
                    "limit": {"type": "integer", "description": "Max number to return. Default 20."},
                },
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "query_emails": query_emails,
    "query_drafts": query_drafts,
    "query_candidates": query_candidates,
}


async def semantic_search(question: str, user_id: str, top_k: int = 5) -> list:
    """Vector similarity search - kept as a fallback for fuzzy/conceptual
    questions the structured tools above can't cleanly express (e.g.
    'candidates similar to our best hires')."""
    db = get_db()
    question_embedding = await embed_text(question)
    result = db.rpc("match_emails", {
        "query_embedding": question_embedding,
        "match_user_id": user_id,
        "match_count": top_k,
    }).execute()
    return result.data if result.data else []


async def retrieve(question: str, user_id: str) -> dict:
    """
    Lets the LLM decide, per-question, which database tool (if any) to call
    and with what filters - replacing hardcoded keyword matching so novel
    phrasings of the same intent ('list today's mail' vs 'what came in
    today') both resolve to the same accurate query.
    """
    llm_with_tools = get_chat_llm_with_tools(TOOLS_SCHEMA)
    response = llm_with_tools.invoke([...])

    response = llm_with_tools.invoke([
        HumanMessage(content=(
            "You are helping answer an HR user's question by choosing the right "
            "database tool call. If the question is about counting, listing, or "
            "filtering emails, drafts, or candidates, call the matching tool with "
            "the appropriate filters. If it's a vague/conceptual question that "
            "doesn't fit a structured filter, don't call any tool.\n\n"
            f"Question: {question}"
        ))
    ])

    if not response.tool_calls:
        # No structured tool fit - fall back to semantic search
        results = await semantic_search(question, user_id)
        return {"type": "semantic", "results": results, "question": question}

    # Execute the tool(s) the LLM chose, with user_id always injected
    # server-side (never trust the LLM to supply this itself)
    tool_results = []
    for call in response.tool_calls:
        fn = TOOL_FUNCTIONS.get(call["name"])
        if not fn:
            continue
        args = {**call["args"], "user_id": user_id}
        try:
            data = fn(**args)
        except Exception as e:
            data = {"error": str(e)}
        tool_results.append({"tool": call["name"], "args": call["args"], "data": data})

    return {"type": "structured", "tool_results": tool_results, "question": question}