from domain.entities.account import Account as DomainAccount
from infrastructure.db.models.account import Account as ORMAccount


class AccountORMMapper:
    @staticmethod
    def to_domain(model: ORMAccount) -> DomainAccount:
        return DomainAccount(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            is_acc_blocked=model.is_acc_blocked,
            is_verified=model.is_verified,
            refresh_token=model.refresh_token,
        )

    @staticmethod
    def to_persistence(entity: DomainAccount) -> dict:
        return {
            "id": entity.id,
            "email": entity.email,
            "hashed_password": entity.hashed_password,
            "is_acc_blocked": entity.is_acc_blocked,
            "is_verified": entity.is_verified,
            "refresh_token": entity.refresh_token,
        }
