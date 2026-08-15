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
    old_category = email.get("category")
    repo.update_email_category(email_id, body.category)
    if old_category and old_category != body.category:
        repo.log_category_correction(email_id, old_category, body.category)
    return repo.get_email_by_id(email_id, current_user["id"])

@router.get("", response_model=list[EmailOut])
async def list_emails(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    return repo.list_emails_for_user(current_user["id"], limit=limit, offset=offset)

@router.get("/count")
async def get_email_count(
    current_user: dict = Depends(get_current_user),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    count = repo.count_emails_for_user(current_user["id"], start_date=start_date, end_date=end_date)
    return {"count": count}

@router.delete("/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email(email_id: str, current_user: dict = Depends(get_current_user)):
    email = repo.get_email_by_id(email_id, current_user["id"])
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    repo.delete_email(email_id, current_user["id"])
    return None

@router.get("/{email_id}", response_model=EmailOut)
async def get_email(email_id: str, current_user: dict = Depends(get_current_user)):
    email = repo.get_email_by_id(email_id, current_user["id"])
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    return email
