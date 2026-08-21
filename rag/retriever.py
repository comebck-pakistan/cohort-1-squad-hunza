import json
from langchain_core.messages import HumanMessage, ToolMessage
from rag.tools import (
    query_emails,
    query_drafts,
    query_candidates,
    get_candidate_details,
    query_candidate_documents,
)
from rag.embedder import embed_text
from database import get_db
from config import get_chat_llm_with_tools

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "query_emails",
            "description": "Search/list/count the user's received emails with optional filters. Use for any question about emails - subjects, senders, categories, priorities, or counts, for any time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_range": {"type": "string", "enum": ["today", "yesterday", "this_week", "all_time"]},
                    "category": {"type": "string", "description": "e.g. 'New Applicant', 'Interview Scheduling'. Omit if not asked."},
                    "priority": {"type": "string", "enum": ["High", "Medium", "Low"]},
                    "sender_contains": {"type": "string"},
                    "limit": {"type": "integer", "description": "Default 50."},
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
                    "status": {"type": "string", "enum": ["pending", "sent", "edited"]},
                    "limit": {"type": "integer", "description": "Default 50."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_candidates",
            "description": "List/count candidates, applicants, or resumes on file, with a summary-level profile for each (name, role, skills, experience, education). Use this for any question about how many candidates/applicants/resumes exist, or listing them by role or skill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_applied_for": {"type": "string"},
                    "skill_contains": {"type": "string"},
                    "limit": {"type": "integer", "description": "Default 50."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_candidate_details",
            "description": "Fetch ONE specific candidate's COMPLETE profile, including their full resume text, by email or name. Use this when the question is about a specific named candidate, or when comparing two or more specific candidates - call this tool once per candidate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "The candidate's email, if known."},
                    "name": {"type": "string", "description": "The candidate's name, if email isn't known."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_candidate_documents",
            "description": "List/count uploaded resume/document files on record.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "Default 50."}},
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "query_emails": query_emails,
    "query_drafts": query_drafts,
    "query_candidates": query_candidates,
    "get_candidate_details": get_candidate_details,
    "query_candidate_documents": query_candidate_documents,
}


async def semantic_search(question: str, user_id: str, top_k: int = 5) -> list:
    """Vector similarity search - fallback for fuzzy/conceptual questions
    the structured tools above can't cleanly express."""
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
    Runs a bounded multi-round tool-calling loop so the LLM can call
    multiple tools across turns when needed (e.g. get_candidate_details
    once per candidate when comparing two named people), not just one
    tool per question.
    """
    llm_with_tools = get_chat_llm_with_tools(TOOLS_SCHEMA)

    messages = [
        HumanMessage(content=(
            "You are helping answer an HR user's question by choosing database "
            "tool calls. Call query_emails / query_drafts / query_candidates for "
            "counting, listing, or filtering questions. Use get_candidate_details "
            "when the question is about one or more SPECIFIC named candidates and "
            "needs their full profile or resume - call it once per distinct "
            "candidate (e.g. call it twice when comparing two people). "
            "If the question doesn't fit any structured tool, don't call a tool.\n\n"
            f"Question: {question}"
        ))
    ]

    all_tool_results = []
    max_rounds = 4

    for _ in range(max_rounds):
        response = llm_with_tools.invoke(messages)

        if not response.tool_calls:
            if not all_tool_results:
                results = await semantic_search(question, user_id)
                return {"type": "semantic", "results": results, "question": question}
            break

        messages.append(response)

        for call in response.tool_calls:
            fn = TOOL_FUNCTIONS.get(call["name"])
            if not fn:
                tool_output = {"error": f"Unknown tool {call['name']}"}
            else:
                args = {**call["args"], "user_id": user_id}
                try:
                    tool_output = fn(**args)
                except Exception as e:
                    tool_output = {"error": str(e)}

            all_tool_results.append({"tool": call["name"], "args": call["args"], "data": tool_output})
            messages.append(ToolMessage(content=json.dumps(tool_output, default=str), tool_call_id=call["id"]))

    return {"type": "structured", "tool_results": all_tool_results, "question": question}