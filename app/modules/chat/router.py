from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.deps import get_current_user
from rag.chat import ask

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("/ask")
async def chat_ask(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    return await ask(body.question, current_user["id"])