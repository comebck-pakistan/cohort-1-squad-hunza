import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "GPT OSS 20B"
GPT_MODEL=""
# similarity threshold for duplicate question detection
# if a question matches the job posting above this score, flag as duplicate
DUPLICATE_THRESHOLD = 0.45

def get_llm(temperature=0):
    """
    Returns a Groq LLM instance.
    All AI tasks import this instead of creating their own instance.
    This way retry logic and model config is in one place only.
    """
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_retries=3,          # retry up to 3 times on failure
        request_timeout=30,     # timeout after 30 seconds
    )




OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"


def _build_chat_openai(temperature=0):
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=temperature,
        max_retries=1,  # fail fast on quota errors so the Groq fallback kicks in quickly
        request_timeout=30,
    )


def get_chat_llm(temperature=0):
    """
    OpenAI-backed LLM used ONLY by the chat assistant (rag/chat.py,
    rag/retriever.py) - kept separate from get_llm() so draft generation and
    classification keep using Groq exclusively. Falls back to Groq
    automatically if the OpenAI key runs out of credits or errors.
    """
    primary = _build_chat_openai(temperature)
    fallback = get_llm(temperature)  # reuse your existing Groq-based get_llm as the fallback
    return primary.with_fallbacks([fallback])


def get_chat_llm_with_tools(tools, temperature=0):
    """Same as get_chat_llm(), but for tool-calling (used in rag/retriever.py)."""
    primary = _build_chat_openai(temperature).bind_tools(tools)
    fallback = get_llm(temperature).bind_tools(tools)
    return primary.with_fallbacks([fallback])