from dataclasses import dataclass


@dataclass(frozen=True)
class AccountRole:
    """
    Value Object: связь аккаунт → роль.

    Не имеет собственного поведения — только данные.
    Один аккаунт имеет ровно одну роль.
    """

    id: str
    account_id: str
    role_id: str
