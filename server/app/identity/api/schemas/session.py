"""
identity/api/schemas/session.py
"""

from datetime import datetime

from pydantic import BaseModel


class SessionResponse(BaseModel):
    session_id: str
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    expires_at: datetime
    is_current: bool

    model_config = {"from_attributes": True}
