# identity/infrastructure/refresh_token/mapper.py

from identity.domain.entities.refresh_token import RefreshToken
from identity.infrastructure.db.models.refresh_token import RefreshToken as RefreshTokenORM


class RefreshTokenMapper:
    @staticmethod
    def to_domain(orm: RefreshTokenORM) -> RefreshToken:
        return RefreshToken(
            id=orm.id,
            account_id=orm.account_id,
            session_id=orm.session_id,
            token_hash=orm.token_hash,
            expires_at=orm.expires_at,
            revoked=orm.revoked,
            user_agent=orm.user_agent,
            ip_address=orm.ip_address,
        )

    @staticmethod
    def to_persistence(entity: RefreshToken) -> dict:
        return {
            "id": entity.id,
            "account_id": entity.account_id,
            "session_id": entity.session_id,
            "token_hash": entity.token_hash,
            "expires_at": entity.expires_at,
            "revoked": entity.revoked,
            "user_agent": entity.user_agent,
            "ip_address": entity.ip_address,
        }
