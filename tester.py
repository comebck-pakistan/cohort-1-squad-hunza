from dotenv import load_dotenv
load_dotenv()

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

print("\nTesting embedding model...")
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL
model = SentenceTransformer(EMBEDDING_MODEL)
embedding = model.encode("This is a test sentence")
print(f"Embedding shape: {embedding.shape}")
print(f"First 5 values: {embedding[:5]}")

print("\nAll connections working.")