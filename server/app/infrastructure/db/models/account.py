"""
infrastructure/db/models/account.py
"""

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.models.basemodel import BaseModel


class Account(BaseModel):
    __tablename__: str = "Account"

    __table_args__: tuple = (Index("idx_account_email", "email", unique=True),)

    email: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        comment="Person's email address",
    )

    hashed_password: Mapped[str] = mapped_column(
        nullable=False,
        comment="Bcrypt-hashed password",
    )

    is_acc_blocked: Mapped[bool] = mapped_column(
        default=False,
        comment="Flag for account blocking",
    )

    is_verified: Mapped[bool] = mapped_column(
        default=False,
        comment="Flag for email verification",
    )

    refresh_token: Mapped[str] = mapped_column(
        nullable=True,
        default=None,
        comment="Hashed refresh token stored server-side for rotation validation",
    )
