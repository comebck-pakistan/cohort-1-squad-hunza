from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.gmail_integration.router import router as gmail_router
from app.modules.emails.router import router as emails_router
from app.modules.drafts.router import router as drafts_router
from app.modules.queue.router import router as queue_router
from app.modules.settings.router import router as settings_router
from app.modules.activity.router import router as activity_router
from app.modules.chat.router import router as chat_router

settings = get_settings()

app = FastAPI(title="AI Recruiter Email Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    settings.FRONTEND_URL,
    "https://frontend-hunza1.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(gmail_router)
app.include_router(emails_router)
app.include_router(drafts_router)
app.include_router(queue_router)
app.include_router(settings_router)
app.include_router(activity_router)
app.include_router(chat_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
