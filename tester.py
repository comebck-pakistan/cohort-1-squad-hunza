from dotenv import load_dotenv
load_dotenv()

import asyncio

print("Testing Groq connection...")
from langchain_groq import ChatGroq
from config import GROQ_MODEL

llm = ChatGroq(model=GROQ_MODEL)
response = llm.invoke("Say the word CONNECTED and nothing else.")
print(f"Groq response: {response.content}")

print("\nTesting Supabase connection...")
from database import get_db
db = get_db()
result = db.table("users").select("*").limit(1).execute()
print(f"Supabase response: {result}")

print("\nTesting embedding model (via HuggingFace Inference API)...")
from rag.embedder import embed_text  # adjust import path to wherever embed_text now lives

async def test_embedding():
    embedding = await embed_text("This is a test sentence")
    print(f"Embedding length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

asyncio.run(test_embedding())

print("\nAll connections working.")