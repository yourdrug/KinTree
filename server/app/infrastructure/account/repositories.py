"""
infrastructure/account/repositories.py

Репозиторий аккаунтов.
При загрузке аккаунта сразу достаёт разрешения одним запросом.
"""

from __future__ import annotations

from domain.entities.account import Account as DomainAccount
from domain.repositories.account import AbstractAccountRepository
from sqlalchemy import select, update
from sqlalchemy.engine.result import Result

from infrastructure.account.account_mapper import AccountORMMapper
from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.account import Account
from infrastructure.db.models.permission import (
    AccountRole,
    Permission,
    Role,
    RolePermission,
)


class AccountRepository(BaseRepository, AbstractAccountRepository):
    async def exists(self, object_id: str) -> bool:
        return await self._check_exists(object_id=object_id, model=Account)

    async def get_by_id(self, account_id: str) -> DomainAccount:
        result: Result = await self.session.execute(select(Account).where(Account.id == account_id))
        account: Account = result.scalar_one()
        permissions = await self._load_permissions(account_id)
        role_name = await self._load_role_name(account_id)
        return AccountORMMapper.to_domain(account, permissions=permissions, role_name=role_name)

    async def get_by_email(self, email: str) -> DomainAccount | None:
        result: Result = await self.session.execute(select(Account).where(Account.email == email))
        account: Account | None = result.scalar_one_or_none()
        if account is None:
            return None
        permissions = await self._load_permissions(account.id)
        role_name = await self._load_role_name(account.id)
        return AccountORMMapper.to_domain(account, permissions=permissions, role_name=role_name)

    async def create(self, account: DomainAccount) -> DomainAccount:
        from sqlalchemy import insert as sa_insert

        data = AccountORMMapper.to_persistence(account)
        statement = sa_insert(Account).values(**data).returning(Account)
        result: Result = await self.session.execute(statement)
        orm_account: Account = result.scalar_one()

        # Назначаем роль "user" при создании
        await self._assign_default_role(orm_account.id)

        return AccountORMMapper.to_domain(
            orm_account,
            permissions=frozenset(),  # новый аккаунт — загрузим при следующем запросе
            role_name="user",
        )

    async def update_refresh_token(
        self,
        account_id: str,
        hashed_refresh_token: str | None,
    ) -> None:
        statement = update(Account).where(Account.id == account_id).values(refresh_token=hashed_refresh_token)
        await self.session.execute(statement)

    # ── Private helpers ────────────────────────────────────────────────────

    async def _load_permissions(self, account_id: str) -> frozenset[str]:
        """Один JOIN-запрос для всех разрешений аккаунта."""
        result = await self.session.execute(
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        return frozenset(result.scalars().all())

    async def _load_role_name(self, account_id: str) -> str:
        result = await self.session.execute(
            select(Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        return result.scalar_one_or_none() or "user"

    async def _assign_default_role(self, account_id: str) -> None:
        from domain.utils import generate_uuid
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        role_result = await self.session.execute(select(Role).where(Role.name == "user"))
        role = role_result.scalar_one_or_none()
        if not role:
            return  # роли ещё нет — lifespan инициализирует их

        stmt = (
            pg_insert(AccountRole)
            .values(id=generate_uuid(), account_id=account_id, role_id=role.id)
            .on_conflict_do_nothing(index_elements=["account_id"])
        )
        await self.session.execute(stmt)
