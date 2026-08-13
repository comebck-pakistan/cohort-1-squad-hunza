from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.modules.drafts import repository as repo
from app.modules.drafts import service
from app.modules.drafts.schemas import DraftEditRequest, DraftOut
from tasks.draft import generate_and_save
from pydantic import BaseModel


router = APIRouter(prefix="/drafts", tags=["drafts"])


class GenerateDraftRequest(BaseModel):
    guidance: str | None = None

@router.get("/by-email/{email_id}", response_model=DraftOut)
async def get_draft_for_email(email_id: str, current_user: dict = Depends(get_current_user)):
    """Drafts are generated automatically during /gmail/{id}/sync - this just reads the latest one for an email."""
    draft = repo.get_draft_for_email(email_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No draft exists yet for this email")
    return draft


@router.post("/generate/{email_id}", response_model=DraftOut)
def generate_draft_for_email(email_id: str):
    return generate_and_save(email_id)


@router.get("/{draft_id}", response_model=DraftOut)
async def get_draft(draft_id: str, current_user: dict = Depends(get_current_user)):
    draft = repo.get_draft_by_id(draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


@router.patch("/{draft_id}", response_model=DraftOut)
async def edit_draft(draft_id: str, body: DraftEditRequest, current_user: dict = Depends(get_current_user)):
    """DRAFT-04 - HR edits the draft text; the correction is logged to draft_corrections."""
    return service.edit_draft(draft_id, body.draft_body, current_user["id"])


@router.post("/{draft_id}/approve", response_model=DraftOut)
async def approve_draft(draft_id: str, current_user: dict = Depends(get_current_user)):
    """DRAFT-03 - HR clicks approve, the draft is sent as a real Gmail reply."""
    return await service.approve_and_send_draft(draft_id, current_user["id"])

@router.get("", response_model=list[DraftOut])
async def list_drafts(current_user: dict = Depends(get_current_user)):
    return repo.list_drafts_for_user(current_user["id"])


@router.post("/generate/{email_id}", response_model=DraftOut)
def generate_draft_for_email(email_id: str, body: GenerateDraftRequest = GenerateDraftRequest()):
    return generate_and_save(email_id, body.guidance)