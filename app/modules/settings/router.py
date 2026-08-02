from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.modules.settings import repository as repo
from app.modules.settings.schemas import SettingsOut, SettingsSaveRequest

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/save", response_model=dict)
async def save_settings(
    body: SettingsSaveRequest,
    current_user: dict = Depends(get_current_user),
):
    saved = repo.upsert_user_settings(current_user["id"], body.dict())
    if not saved:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save settings")
    return {"status": "saved", "data": saved}


@router.get("", response_model=SettingsOut)
async def get_settings(current_user: dict = Depends(get_current_user)):
    existing = repo.get_settings_by_user_id(current_user["id"])
    if existing:
        return existing
    return SettingsOut(
        user_id=current_user["id"],
        categories=[],
        job_roles=[],
        job_descriptions={},
        reply_tone="Friendly",
        updated_at=None,
    )
