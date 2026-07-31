from pydantic import BaseModel


class DraftOut(BaseModel):
    id: str
    email_id: str
    draft_body: str
    status: str
    gmail_draft_id: str | None = None
    generated_at: str | None = None
    approved_at: str | None = None
    sent_at: str | None = None


class DraftEditRequest(BaseModel):
    draft_body: str
