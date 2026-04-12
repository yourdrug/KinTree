from __future__ import annotations

from dataclasses import dataclass, field

from domain.entities.person import Person
from domain.exceptions import DomainFamilyError
from domain.utils import generate_uuid


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
    owner_id: str
    members: list[Person] = field(default_factory=list)

    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = None
    ended_year: int | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        self._validate_years()

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

    def _validate_years(self) -> None:
        if self.founded_year and self.ended_year:
            if self.founded_year > self.ended_year:
                raise DomainFamilyError(
                    message="Ошибка валидации",
                    errors={"years": "Год основания не может быть больше года окончания"},
                )

    @staticmethod
    def create_family(
        name: str,
        owner_id: str,
        description: str | None = None,
        origin_place: str | None = None,
        founded_year: int | None = None,
        ended_year: int | None = None,
    ) -> Family:
        return Family(
            id=generate_uuid(),
            name=name,
            owner_id=owner_id,
            description=description,
            origin_place=origin_place,
            founded_year=founded_year,
            ended_year=ended_year,
        )
