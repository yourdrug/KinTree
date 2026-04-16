"""
infrastructure/db/models/permission.py

ORM-модели для системы разрешений.

Схема:
    permissions  — справочник разрешений (codename уникален)
    roles        — справочник ролей
    role_permissions — M2M: роль ↔ разрешение
    account_roles    — M2M: аккаунт ↔ роль (один аккаунт = одна роль в нашем случае)
"""

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.models.basemodel import BaseModel


class Permission(BaseModel):
    __tablename__ = "permissions"

    __table_args__ = (Index("idx_permission_codename", "codename", unique=True),)

    codename: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        comment="Уникальный строковый ключ: 'resource:action'",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default="",
        comment="Человекочитаемое описание разрешения",
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
    )


class RolePermission(BaseModel):
    """M2M: роль → разрешение."""

    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        Index("idx_rp_role", "role_id"),
        Index("idx_rp_permission", "permission_id"),
    )

    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    permission_id: Mapped[str] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
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
    )

    role_id: Mapped[str] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
