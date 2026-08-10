from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.modules.activity import repository as repo

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("")
async def list_activity(current_user: dict = Depends(get_current_user)):
    return repo.list_activity_for_user(current_user["id"])