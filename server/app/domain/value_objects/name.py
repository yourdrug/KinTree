from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import PersonDomainError


@dataclass(frozen=True)
class PersonName:
    """
    Value Object: имя персоны.

    Инвариант: хотя бы одно из полей (first_name или last_name) должно быть заполнено.
    Оба могут присутствовать; оба None — недопустимо.
    """

    first_name: str | None
    last_name: str | None

    def __post_init__(self) -> None:
        if not self.first_name and not self.last_name:
            raise PersonDomainError(
                field="name",
                message="Хотя бы одно из полей (имя или фамилия) должно быть заполнено.",
            )

    def full(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name]))

    def __str__(self) -> str:
        return self.full()
