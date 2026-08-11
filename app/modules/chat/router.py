from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.deps import get_current_user
from rag.chat import ask
from database import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str

class ChatRequest(BaseModel):
    question: str
    history: list[dict] | None = None

@router.post("/ask")
async def chat_ask(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    return await ask(body.question, current_user["id"])

@router.post("/ask")
async def chat_ask(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    return await ask(body.question, current_user["id"], body.history)

@router.get("/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    db = get_db()
    res = db.table("chat_messages")\
        .select("*")\
        .eq("user_id", current_user["id"])\
        .order("created_at")\
        .execute()
    return res.data or []