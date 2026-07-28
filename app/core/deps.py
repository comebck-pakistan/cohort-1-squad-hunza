from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

# Registering this as a FastAPI security scheme (rather than a plain Header
# param) is what makes the "Authorize" lock icon appear in Swagger UI
# (top-right of /docs). Paste your access_token there once and it's sent
# automatically on every "Try it out" call to a route that depends on
# get_current_user - no need to manually add an Authorization header each time.
bearer_scheme = HTTPBearer(
    scheme_name="AccessToken",
    description="Paste the raw access_token here (no 'Bearer ' prefix - Swagger adds that for you).",
    auto_error=False,
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """
    Validates the JWT access token in-process (no DB hit) and returns
    {"id": ..., "email": ...}. Use as: Depends(get_current_user).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token. Click 'Authorize' in Swagger and paste your access_token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"id": payload["sub"], "email": payload["email"]}