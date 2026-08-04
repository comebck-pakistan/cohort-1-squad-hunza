from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.modules.emails import repository as repo
from app.modules.emails.schemas import EmailOut

router = APIRouter(prefix="/emails", tags=["emails"])

# Just list/get today, backed by whatever /gmail/{id}/sync has ingested.
# Category/priority filters, needs-attention, etc. land in Module 3 once
# email_categories is actually being populated.
from pydantic import BaseModel

class CategoryUpdate(BaseModel):
    category: str

@router.patch("/{email_id}/category", response_model=EmailOut)
async def update_category(email_id: str, body: CategoryUpdate, current_user: dict = Depends(get_current_user)):
    email = repo.get_email_by_id(email_id, current_user["id"])
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    repo.update_email_category(email_id, body.category)
    return repo.get_email_by_id(email_id, current_user["id"])

@router.get("", response_model=list[EmailOut])
async def list_emails(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    return repo.list_emails_for_user(current_user["id"], limit=limit, offset=offset)


@router.get("/{email_id}", response_model=EmailOut)
async def get_email(email_id: str, current_user: dict = Depends(get_current_user)):
    email = repo.get_email_by_id(email_id, current_user["id"])
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    return email
