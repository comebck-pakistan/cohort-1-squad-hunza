import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.3-70b-versatile"
GPT_MODEL=""
# similarity threshold for duplicate question detection
# if a question matches the job posting above this score, flag as duplicate
DUPLICATE_THRESHOLD = 0.75

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