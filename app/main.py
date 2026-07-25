from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.gmail_integration.router import router as gmail_router
from app.modules.emails.router import router as emails_router

settings = get_settings()

app = FastAPI(title="AI Recruiter Email Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(gmail_router)
app.include_router(emails_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
