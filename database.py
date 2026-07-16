from supabase import create_client,Client
from config import SUPABASE_URL,SUPABASE_SERVICE_KEY

db_url=SUPABASE_URL
db_key=SUPABASE_SERVICE_KEY

supabase:Client=create_client(db_url,db_key)

def get_db():
    return supabase