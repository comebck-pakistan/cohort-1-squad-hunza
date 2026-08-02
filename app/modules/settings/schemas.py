from pydantic import BaseModel


class SettingsSaveRequest(BaseModel):
    categories: list[str]
    roles: list[str]
    job_descriptions: dict[str, str]
    reply_tone: str


class SettingsOut(BaseModel):
    user_id: str
    categories: list[str]
    job_roles: list[str]
    job_descriptions: dict[str, str]
    reply_tone: str
    updated_at: str | None = None
