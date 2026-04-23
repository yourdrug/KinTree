"""
infrastructure/db/models/permission.py

ORM-модели для системы разрешений.

Схема:
  permissions      — справочник пермишенов (codename уникален)
  roles            — справочник ролей (name уникален)
  role_permissions — M2M: роль ↔ пермишен
  account_roles    — один аккаунт = одна роль

Решения:
- role_permissions и account_roles используют LinkedBaseModel (без суррогатного id).
  Исключение: account_roles всё же имеет id для конфликт-разрешения в pg_insert.
- Все уникальные ограничения явные, с именами — для читаемых ошибок и миграций.
"""

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.db.basemodel import BaseModel, LinkedBaseModel


class Permission(BaseModel):
    __tablename__ = "permissions"

    __table_args__ = (Index("idx_permission_codename", "codename", unique=True),)

    codename: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        comment="Уникальный строковый ключ: 'resource:action[:scope]'",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
        comment="Человекочитаемое описание пермишена",
    )


class Role(BaseModel):
    __tablename__ = "roles"

    __table_args__ = (Index("idx_role_name", "name", unique=True),)

    name: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="Уникальное имя роли: 'user', 'admin', ...",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
        comment="Описание роли",
    )


class RolePermission(LinkedBaseModel):
    """M2M: роль → пермишен. Составной PK."""

    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        Index("idx_rp_role", "role_id"),
        Index("idx_rp_permission", "permission_id"),
    )

    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    permission_id: Mapped[str] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )


class AccountRole(BaseModel):
    """Связь аккаунт → роль. Один аккаунт — одна роль."""

    __tablename__ = "account_roles"

    __table_args__ = (
        UniqueConstraint("account_id", name="uq_account_role"),
        Index("idx_ar_account", "account_id"),
        Index("idx_ar_role", "role_id"),
    )

    account_id: Mapped[str] = mapped_column(
        ForeignKey("Account.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="ID аккаунта (один аккаунт — одна роль)",
    )

    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        comment="ID роли",
    )
