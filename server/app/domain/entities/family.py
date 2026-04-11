from __future__ import annotations

from dataclasses import dataclass, field

from domain.entities.person import Person
from domain.exceptions import DomainFamilyError


MAX_FAMILY_SIZE = 2  # пример ограничения для демонстрации


@dataclass
class Family:
    """
    Агрегат Family.
    Знает о своих членах и применяет бизнес-инварианты
    на уровне всей семьи.
    """

    id: str
    name: str
    members: list[Person] = field(default_factory=list)

    def assert_can_add_member(self, candidate: Person) -> None:
        """
        Проверяет все инварианты перед добавлением нового члена семьи.
        Выбрасывает DomainFamilyError при нарушении любого правила.
        """
        self._assert_family_size_limit()
        self._assert_no_duplicate_member(candidate)

    def _assert_family_size_limit(self) -> None:
        """Инвариант: в семье не более MAX_FAMILY_SIZE человек."""
        if len(self.members) >= MAX_FAMILY_SIZE:
            raise DomainFamilyError(
                message="Ошибка валидации",
                errors={
                    "family_id": (
                        f"В семье уже {len(self.members)} "
                        f"{'человек' if len(self.members) >= 5 else 'человека'}. "
                        f"Максимально допустимое количество: {MAX_FAMILY_SIZE}."
                    )
                },
            )

    def _assert_no_duplicate_member(self, candidate: Person) -> None:
        """
        Инвариант: в одной семье не может быть двух людей
        с одинаковыми first_name, last_name и birth_date.
        """
        for member in self.members:
            if self._is_duplicate(member, candidate):
                raise DomainFamilyError(
                    message="Ошибка валидации",
                    errors={
                        "person": (
                            "В этой семье уже есть человек "
                            f"с именем «{candidate.full_name()}» "
                            "и такой же датой рождения."
                        )
                    },
                )

    @staticmethod
    def _is_duplicate(existing: Person, candidate: Person) -> bool:
        """
        Дубль — совпадение first_name + last_name + birth_date.
        Пустые имена и даты в сравнении не участвуют
        (None != None в бизнес-смысле не считается дублем).
        """
        names_match = (
            existing.first_name is not None
            and existing.last_name is not None
            and existing.first_name == candidate.first_name
            and existing.last_name == candidate.last_name
        )
        dates_match = (
            existing.birth_date is not None
            and candidate.birth_date is not None
            and existing.birth_date == candidate.birth_date
        )
        return names_match and dates_match
