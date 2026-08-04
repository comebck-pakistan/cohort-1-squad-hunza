from pydantic import BaseModel


class EmailOut(BaseModel):
    id: str
    gmail_message_id: str
    gmail_thread_id: str | None = None
    sender_email: str | None = None
    sender_name: str | None = None
    subject: str | None = None
    body_text: str | None = None
    received_at: str | None = None
    has_attachment: bool = False
    is_processed: bool = False
    category: str | None = None
    priority: str | None = None