"""
identity/api/schemas/session.py
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from identity.domain.entities.refresh_token import RefreshToken
from identity.domain.ports.token_service import AccessTokenPayload


class SessionResponse(BaseModel):
    session_id: str
    user_agent: str | None
    ip_address: str | None
    created_at: datetime
    expires_at: datetime
    is_current: bool

    @classmethod
    def from_domain(cls, session: RefreshToken, token_payload: AccessTokenPayload) -> SessionResponse:
        return cls(
            session_id=session.session_id,
            user_agent=session.user_agent,
            ip_address=session.ip_address,
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_current=(session.session_id == token_payload.session_id),
        )
