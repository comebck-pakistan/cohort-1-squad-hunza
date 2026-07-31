from pydantic import BaseModel


class ClassificationOut(BaseModel):
    category: str | None = None
    confidence_score: float | None = None
    priority: str | None = None
    priority_reason: str | None = None
    resolved_at: str | None = None


class QueueItemOut(BaseModel):
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
    email_categories: list[ClassificationOut] | ClassificationOut | None = None
    # Supabase's embedded-resource select returns a list even for this
    # effectively one-to-one relationship; both shapes are accepted here.
