"""
infrastructure/account/mapper.py
"""

from domain.entities.account import Account as DomainAccount

from infrastructure.db.models.account import Account as ORMAccount


class AccountMapper:
    def to_domain(
        self,
        model: ORMAccount,
        permissions: frozenset[str] = frozenset(),
        role_name: str = "user",
    ) -> DomainAccount:
        return DomainAccount(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            is_acc_blocked=model.is_acc_blocked,
            is_verified=model.is_verified,
            refresh_token=model.refresh_token,
            role_name=role_name,
            permissions=permissions,
        )

    def to_persistence(self, entity: DomainAccount) -> dict:
        return {
            "id": entity.id,
            "email": entity.email,
            "hashed_password": entity.hashed_password,
            "is_acc_blocked": entity.is_acc_blocked,
            "is_verified": entity.is_verified,
            "refresh_token": entity.refresh_token,
        }
