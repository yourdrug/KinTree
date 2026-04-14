from dataclasses import dataclass

from domain.utils import generate_uuid


@dataclass
class Account:
    id: str
    email: str
    hashed_password: str
    is_acc_blocked: bool = False
    is_verified: bool = False
    refresh_token: str | None = None

    def is_active(self) -> bool:
        return not self.is_acc_blocked


def create_account(email: str, hashed_password: str) -> "Account":
    """Factory function — generates a new ID on creation."""
    return Account(
        id=generate_uuid(),
        email=email,
        hashed_password=hashed_password,
    )
