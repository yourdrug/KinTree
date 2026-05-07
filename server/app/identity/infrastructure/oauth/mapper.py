"""
identity/infrastructure/oauth/mapper.py

Маппер ORM OAuthAccount ↔ доменный OAuthAccount.
"""

from __future__ import annotations

import logging

from identity.domain.entities.oauth_account import OAuthAccount as DomainOAuthAccount
from identity.domain.entities.oauth_account import OAuthProvider
from identity.infrastructure.db.models.oauth_account import OAuthAccount as ORMOAuthAccount


logger = logging.getLogger(__name__)


class OAuthAccountMapper:
    @staticmethod
    def to_domain(model: ORMOAuthAccount) -> DomainOAuthAccount:
        return DomainOAuthAccount(
            id=model.id,
            account_id=model.account_id,
            provider=OAuthProvider(model.provider),
            provider_user_id=model.provider_user_id,
        )

    @staticmethod
    def to_persistence(entity: DomainOAuthAccount) -> dict:
        return {
            "id": entity.id,
            "account_id": entity.account_id,
            "provider": str(entity.provider),
            "provider_user_id": entity.provider_user_id,
        }
