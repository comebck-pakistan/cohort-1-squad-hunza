from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.modules.emails import repository as emails_repo
from app.modules.queue import repository as repo
from app.modules.queue.schemas import QueueItemOut

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("", response_model=list[QueueItemOut])
async def get_queue(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """QUEUE-02 - high-priority emails that haven't been resolved (replied to, or manually dismissed) yet."""
    return repo.list_needs_attention(current_user["id"], limit=limit, offset=offset)


@router.delete("/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_from_queue(email_id: str, current_user: dict = Depends(get_current_user)):
    """
    QUEUE-02 - removes an item from the needs-attention queue. Use this when
    the recruiter has handled it some other way (phone call, handled
    manually in Gmail directly, etc). Sending an approved draft
    (POST /drafts/{id}/approve) already does this automatically, so you
    normally won't need to call this yourself after sending a reply.
    """
    email = emails_repo.get_email_by_id(email_id, current_user["id"])
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    repo.resolve_email(email_id)
    return None
