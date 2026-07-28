from pydantic import BaseModel


class GmailConnectionOut(BaseModel):
    id: str
    gmail_address: str
    is_active: bool
    connected_at: str | None = None


class GmailConnectUrlOut(BaseModel):
    authorization_url: str


class SyncResult(BaseModel):
    checked: int
    inserted: int
    skipped_existing: int