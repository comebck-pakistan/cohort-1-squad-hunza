from pydantic import BaseModel


class OutlookConnectionOut(BaseModel):
    id: str
    user_id: str
    email_address: str
    is_active: bool
    connected_at: str | None = None
    provider: str


class OutlookConnectUrlOut(BaseModel):
    authorization_url: str


class SyncResult(BaseModel):
    checked: int
    inserted: int
    skipped_existing: int