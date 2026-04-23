# genealogy/domain/value_objects/person_name.py
from __future__ import annotations

from dataclasses import dataclass

from shared.domain.exceptions import PersonDomainError


@dataclass(frozen=True)
class PersonName:
    """
    Value Object: имя персоны.

    Нормализует пустые строки в None при создании.
    Инвариант: хотя бы одно из полей непустое после нормализации.
    """

    first_name: str | None
    last_name: str | None

    def __post_init__(self) -> None:
        fn = self.first_name.strip() if self.first_name else None
        ln = self.last_name.strip() if self.last_name else None
        object.__setattr__(self, "first_name", fn or None)
        object.__setattr__(self, "last_name", ln or None)

        if not self.first_name and not self.last_name:
            raise PersonDomainError(
                field="name",
                message="Хотя бы одно из полей (имя или фамилия) должно быть заполнено.",
            )

    def full(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name]))

    def __str__(self) -> str:
        return self.full()
