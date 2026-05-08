"""
identity/infrastructure/email_token/mapper.py

Маппер ORM EmailToken ↔ доменный EmailToken.
"""

from __future__ import annotations

from identity.domain.entities.email_token import EmailToken as DomainEmailToken
from identity.domain.entities.email_token import EmailTokenType
from identity.infrastructure.db.models.email_token import EmailToken as EmailTokenORM


class EmailTokenMapper:
    @staticmethod
    def to_domain(orm: EmailTokenORM) -> DomainEmailToken:
        return DomainEmailToken(
            id=orm.id,
            account_id=orm.account_id,
            token_hash=orm.token_hash,
            token_type=EmailTokenType(orm.token_type),
            expires_at=orm.expires_at,
            created_at=orm.creation_date,  # ORM.creation_date → domain.created_at
            is_used=orm.is_used,
        )

    @staticmethod
    def to_persistence(entity: DomainEmailToken) -> dict:
        return {
            "id": entity.id,
            "account_id": entity.account_id,
            "token_hash": entity.token_hash,
            "token_type": entity.token_type.value,
            "expires_at": entity.expires_at,
            "is_used": entity.is_used,
            # created_at не передаём — управляется БД через BaseModel.creation_date
        }
