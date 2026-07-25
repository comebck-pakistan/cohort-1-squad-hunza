from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.oauth_state import generate_state, verify_state
from app.modules.auth import repository as repo
from app.modules.auth import service
from app.modules.auth.google_oauth import build_google_auth_url
from app.modules.auth.schemas import LoginResponse, LogoutRequest, RefreshRequest, TokenPair, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.get("/google/login")
async def google_login():
    state = generate_state()
    return RedirectResponse(build_google_auth_url(state))


@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: str):
    # Unlike a stored-nonce approach, this state can be verified once and is
    # then simply discarded - there's nothing to "delete" since nothing was
    # ever stored. A replayed state is still only valid within its 10-minute
    # TTL and requires the matching `code`, which Google invalidates after
    # first use anyway.
    is_valid, _ = verify_state(state)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")

    result = await service.login_with_google(
        code=code,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    tokens = result["tokens"]
    redirect_url = (
        f"{settings.FRONTEND_URL}{settings.FRONTEND_OAUTH_SUCCESS_PATH}"
        f"#access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
    )
    return RedirectResponse(redirect_url)


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, request: Request):
    result = service.refresh_tokens(
        raw_refresh_token=body.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return result["tokens"]


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest):
    service.logout(body.refresh_token)
    return None


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    user = repo.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
