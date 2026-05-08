"""
identity/infrastructure/account/mapper.py

Маппер ORM Account ↔ доменный Account.
"""

from __future__ import annotations

import logging

from identity.domain.entities.account import Account as DomainAccount
from identity.domain.entities.permission import get_default_role_name
from identity.domain.permissions.enums import RoleName
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.hashed_password import HashedPassword
from identity.infrastructure.db.models.account import Account as ORMAccount


logger = logging.getLogger(__name__)


class AccountMapper:
    @staticmethod
    def to_domain(
        model: ORMAccount,
        permissions: frozenset[str],
        role_name: str,
    ) -> DomainAccount:
        try:
            role = RoleName(role_name)
        except ValueError:
            # Роль из БД не совпадает ни с одним RoleName — берем дефолт,
            # но логируем: это аномалия (например, ручное изменение БД).
            logger.warning(
                "Unknown role_name %r for account %s, falling back to USER",
                role_name,
                model.id,
            )
            role = get_default_role_name()

        return DomainAccount(
            id=model.id,
            email=Email(value=model.email),
            hashed_password=HashedPassword(value=model.hashed_password),
            is_acc_blocked=model.is_acc_blocked,
            is_verified=model.is_verified,
            role_name=role,
            permissions=permissions,
        )

    @staticmethod
    def to_persistence(entity: DomainAccount) -> dict:
        return {
            "id": entity.id,
            "email": entity.email_str,
            "hashed_password": str(entity.hashed_password),
            "is_acc_blocked": entity.is_acc_blocked,
            "is_verified": entity.is_verified,
        }
