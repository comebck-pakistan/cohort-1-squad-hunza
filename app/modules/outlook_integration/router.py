from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.oauth_state import generate_state, verify_state
from app.modules.outlook_integration import repository as repo
from app.modules.outlook_integration import service
from app.modules.outlook_integration.microsoft_oauth import build_outlook_auth_url
from app.modules.outlook_integration.schemas import OutlookConnectionOut, OutlookConnectUrlOut, SyncResult

router = APIRouter(prefix="/outlook", tags=["outlook"])
settings = get_settings()


@router.get("/connect", response_model=OutlookConnectUrlOut)
async def outlook_connect(current_user: dict = Depends(get_current_user)):
    """
    Returns the Microsoft consent URL rather than redirecting directly -
    mirrors /gmail/connect's reasoning exactly (Bearer token needed to know
    which user is connecting).
    """
    state = generate_state(extra=current_user["id"])
    return {"authorization_url": build_outlook_auth_url(state)}


@router.get("/callback")
async def outlook_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None, error_description: str | None = None):
    if error:
        print(f"Outlook OAuth error from Microsoft: {error} - {error_description}")
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?outlook_error={error}")

    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code or state")

    is_valid, user_id = verify_state(state)
    if not is_valid or not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")

    await service.handle_outlook_callback(code=code, user_id=user_id)

    return RedirectResponse(f"{settings.FRONTEND_URL}/settings?connected=true")

@router.get("/status", response_model=list[OutlookConnectionOut])
async def outlook_status(current_user: dict = Depends(get_current_user)):
    return repo.list_connections_for_user(current_user["id"])


@router.post("/{connection_id}/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def outlook_disconnect(connection_id: str, current_user: dict = Depends(get_current_user)):
    service.disconnect(connection_id, current_user["id"])
    return None


@router.post("/{connection_id}/sync", response_model=SyncResult)
async def outlook_sync(connection_id: str, current_user: dict = Depends(get_current_user)):
    """Manual trigger for testing - same exact logic the webhook uses."""
    return await service.sync_now(connection_id, current_user["id"])


@router.delete("/{connection_id}/delete-all-data")
async def outlook_delete_connection_and_data(connection_id: str, current_user: dict = Depends(get_current_user)):
    success = repo.delete_connection_and_data(connection_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return {"status": "deleted"}


@router.post("/subscription/webhook")
async def outlook_subscription_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Microsoft Graph pushes a change notification here whenever new mail
    arrives in any subscribed mailbox. Graph also sends a validation
    request on subscription creation - it expects the raw validationToken
    echoed back as plain text within 10 seconds, which is why this checks
    for it before touching the JSON body at all.
    """
    validation_token = request.query_params.get("validationToken")
    if validation_token:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=validation_token, status_code=200)

    body = await request.json()
    await service.handle_graph_notification(body, background_tasks)
    return {"status": "ok"}