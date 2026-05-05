"""
identity/infrastructure/refresh_token/mapper.py

Маппер ORM RefreshToken ↔ доменный RefreshToken.

ORM-модель наследует creation_date от BaseModel.
Доменная сущность использует created_at (более явное имя для сессий).
Маппер делает это преобразование явным.
"""

from __future__ import annotations

from identity.domain.entities.refresh_token import RefreshToken as DomainRefreshToken
from identity.infrastructure.db.models.refresh_token import RefreshToken as RefreshTokenORM


class RefreshTokenMapper:
    @staticmethod
    def to_domain(orm: RefreshTokenORM) -> DomainRefreshToken:
        return DomainRefreshToken(
            id=orm.id,
            account_id=orm.account_id,
            session_id=orm.session_id,
            token_hash=orm.token_hash,
            expires_at=orm.expires_at,
            created_at=orm.creation_date,  # ORM.creation_date → domain.created_at
            revoked=orm.revoked,
            user_agent=orm.user_agent,
            ip_address=orm.ip_address,
        )

    @staticmethod
    def to_persistence(entity: DomainRefreshToken) -> dict:
        return {
            "id": entity.id,
            "account_id": entity.account_id,
            "session_id": entity.session_id,
            "token_hash": entity.token_hash,
            "expires_at": entity.expires_at,
            "revoked": entity.revoked,
            "user_agent": entity.user_agent,
            "ip_address": entity.ip_address,
            # created_at не передаём — управляется БД через BaseModel.creation_date
        }
