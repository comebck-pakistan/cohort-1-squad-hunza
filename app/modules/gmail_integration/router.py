from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.oauth_state import generate_state, verify_state
from app.modules.gmail_integration import repository as repo
from app.modules.gmail_integration import service
from app.modules.gmail_integration.google_oauth import build_gmail_auth_url
from app.modules.gmail_integration.schemas import GmailConnectionOut, GmailConnectUrlOut, SyncResult

router = APIRouter(prefix="/gmail", tags=["gmail"])
settings = get_settings()


@router.get("/connect", response_model=GmailConnectUrlOut)
async def gmail_connect(current_user: dict = Depends(get_current_user)):
    """
    Returns the Google consent URL rather than redirecting directly - this
    route requires a Bearer token (to know which user is connecting), and a
    plain browser navigation can't attach an Authorization header. The
    frontend calls this via fetch(), then does
    `window.location.href = authorization_url` itself. For manual testing,
    just copy the returned URL into your browser's address bar.
    """
    state = generate_state(extra=current_user["id"])
    return {"authorization_url": build_gmail_auth_url(state)}


@router.get("/callback")
async def gmail_callback(request: Request, code: str, state: str):
    is_valid, user_id = verify_state(state)
    if not is_valid or not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")

    await service.handle_gmail_callback(code=code, user_id=user_id)

    return RedirectResponse(f"{settings.FRONTEND_URL}/settings?connected=true")

@router.get("/status", response_model=list[GmailConnectionOut])
async def gmail_status(current_user: dict = Depends(get_current_user)):
    return repo.list_connections_for_user(current_user["id"])


@router.post("/{connection_id}/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def gmail_disconnect(connection_id: str, current_user: dict = Depends(get_current_user)):
    service.disconnect(connection_id, current_user["id"])
    return None


@router.post("/{connection_id}/sync", response_model=SyncResult)
async def gmail_sync(connection_id: str, current_user: dict = Depends(get_current_user)):
    """
    Manual trigger for today's testing. This exact call is what Module 3's
    Celery task (jobs.ingest_email) will make automatically on a webhook/poll -
    nothing here changes when that lands, it just stops being manual.
    """
    return await service.sync_now(connection_id, current_user["id"])

@router.post("/pubsub/webhook")
async def gmail_pubsub_webhook(request: Request):
    """
    INGEST-01: Google Cloud Pub/Sub pushes a notification to this endpoint
    whenever a new email arrives in any connected mailbox.
    No auth header - Google calls this directly, secured by the push
    subscription's URL being secret enough.
    """
    body = await request.json()
    await service.handle_pubsub_notification(body)
    return {"status": "ok"}