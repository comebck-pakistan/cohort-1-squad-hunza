from functools import lru_cache
from supabase import create_client, Client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """
    Service-role client for trusted backend contexts (API process, Celery workers).
    Bypasses RLS - all authorization must happen in the application layer
    (see core/deps.py::get_current_user), not by relying on Supabase RLS here.
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
