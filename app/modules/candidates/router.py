from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.modules.candidates import repository as repo

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("")
async def list_candidates(current_user: dict = Depends(get_current_user)):
    return repo.list_candidates_for_user(current_user["id"])