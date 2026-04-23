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

    def __new__(cls, first_name: str | None, last_name: str | None) -> PersonName:
        # Нормализуем до вызова __post_init__
        fn = first_name.strip() if first_name else None
        ln = last_name.strip() if last_name else None
        instance = object.__new__(cls)
        # frozen=True, поэтому через object.__setattr__
        object.__setattr__(instance, "first_name", fn or None)
        object.__setattr__(instance, "last_name", ln or None)
        return instance

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
