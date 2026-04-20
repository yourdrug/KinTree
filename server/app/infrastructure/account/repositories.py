"""
infrastructure/account/repositories.py

Репозиторий аккаунтов.
При загрузке аккаунта сразу достаёт разрешения одним запросом.
"""

from __future__ import annotations

from domain.entities.account import Account as DomainAccount
from sqlalchemy import exists, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.account.mapper import AccountMapper
from infrastructure.db.models.account import Account as ORMAccount
from infrastructure.db.models.permission import (
    AccountRole,
    Permission,
    Role,
    RolePermission,
)


class AccountRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._mapper = AccountMapper()

    async def exists(self, account_id: str) -> bool:
        stmt = select(exists().where(ORMAccount.id == account_id))
        result: Result = await self._session.execute(stmt)
        return result.scalar() or False

    async def get_by_id(self, account_id: str) -> DomainAccount:
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.id == account_id))
        account: ORMAccount = result.scalar_one()
        permissions = await self._load_permissions(account_id)
        role_name = await self._load_role_name(account_id)
        return self._mapper.to_domain(account, permissions=permissions, role_name=role_name)

    async def get_by_email(self, email: str) -> DomainAccount | None:
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.email == email))
        account: ORMAccount | None = result.scalar_one_or_none()
        if account is None:
            return None
        permissions = await self._load_permissions(account.id)
        role_name = await self._load_role_name(account.id)
        return self._mapper.to_domain(account, permissions=permissions, role_name=role_name)

    async def save(self, account: DomainAccount) -> DomainAccount:
        """Protocol alias: создать или обновить."""
        if await self.exists(account.id):
            # точечное обновление — только изменяемые поля
            stmt = (
                update(ORMAccount)
                .where(ORMAccount.id == account.id)
                .values(
                    email=account.email,
                    hashed_password=account.hashed_password,
                    is_acc_blocked=account.is_acc_blocked,
                    is_verified=account.is_verified,
                    refresh_token=account.refresh_token,
                )
                .returning(ORMAccount)
            )
            result: Result = await self._session.execute(stmt)
            orm_account: ORMAccount = result.scalar_one()
            permissions = await self._load_permissions(orm_account.id)
            role_name = await self._load_role_name(orm_account.id)
            return self._mapper.to_domain(orm_account, permissions, role_name)
        return await self.create(account)

    async def create(self, account: DomainAccount) -> DomainAccount:
        from sqlalchemy import insert as sa_insert

        data = self._mapper.to_persistence(account)
        statement = sa_insert(ORMAccount).values(**data).returning(ORMAccount)
        result: Result = await self._session.execute(statement)
        orm_account: ORMAccount = result.scalar_one()

        # Назначаем роль "user" при создании
        await self._assign_default_role(orm_account.id)

        return self._mapper.to_domain(
            orm_account,
            permissions=frozenset(),  # новый аккаунт — загрузим при следующем запросе
            role_name="user",
        )

    async def update_refresh_token(
        self,
        account_id: str,
        hashed_refresh_token: str | None,
    ) -> None:
        statement = update(ORMAccount).where(ORMAccount.id == account_id).values(refresh_token=hashed_refresh_token)
        await self._session.execute(statement)

    # ── Private helpers ────────────────────────────────────────────────────

    async def _load_permissions(self, account_id: str) -> frozenset[str]:
        """Один JOIN-запрос для всех разрешений аккаунта."""
        result = await self._session.execute(
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        return frozenset(result.scalars().all())

    async def _load_role_name(self, account_id: str) -> str:
        result = await self._session.execute(
            select(Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        return result.scalar_one_or_none() or "user"

    async def _assign_default_role(self, account_id: str) -> None:
        from domain.utils import generate_uuid
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        role_result = await self._session.execute(select(Role).where(Role.name == "user"))
        role = role_result.scalar_one_or_none()
        if not role:
            return  # роли ещё нет — lifespan инициализирует их

        stmt = (
            pg_insert(AccountRole)
            .values(id=generate_uuid(), account_id=account_id, role_id=role.id)
            .on_conflict_do_nothing(index_elements=["account_id"])
        )
        await self._session.execute(stmt)
