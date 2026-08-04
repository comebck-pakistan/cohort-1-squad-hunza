from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str  # service-role key - backend-only, never exposed to frontend

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth2 (recruiter login)
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str  # e.g. http://localhost:8000/auth/google/callback

    # Gmail integration (separate consent from login - broader scopes, offline access)
    GMAIL_REDIRECT_URI: str  # e.g. http://localhost:8000/gmail/callback
    GMAIL_TOKEN_ENCRYPTION_KEY: str  # Fernet key - generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    # Redis (OAuth state storage here today; Celery broker later)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_OAUTH_SUCCESS_PATH: str = "/auth/callback.html"
    ENVIRONMENT: str = "development"  # development | staging | production


@lru_cache
def get_settings() -> Settings:
    return Settings()
