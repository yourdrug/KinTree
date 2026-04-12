from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from infrastructure.db.models.basemodel import BaseModel


class Account(BaseModel):
    """
    Account: SQLAlchemy model class. Represents an account.
    Index created automatically on id, email fields.
    """

    __tablename__: str = "Account"

    email: Mapped[str] = mapped_column(
        index=True,
        comment="Persons email address",
    )

    is_acc_blocked: Mapped[bool] = mapped_column(
        default=False,
        comment="Flag for account blocking",
    )
