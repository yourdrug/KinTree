"""
domain/entities/family.py

Агрегат Family.

Family — корень агрегата, управляет своими членами.
assert_can_add_member() проверяет инварианты перед добавлением персоны.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.entities.person import Person
from domain.exceptions import FamilyDomainError
from domain.utils import generate_uuid


MAX_FAMILY_SIZE = 2


@dataclass
class Family:
    """
    Агрегат Family.

    Инварианты:
    - founded_year <= ended_year (если оба заданы)
    - Размер семьи не превышает MAX_FAMILY_SIZE
    - Нет дублирующихся членов (same name + birth_date)
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

    # ── Запросы ──────────────────────────────────────────────────────────────

    @property
    def members_count(self) -> int:
        return len(self.members)

    # ── Команды ──────────────────────────────────────────────────────────────

    def assert_can_add_member(self, candidate: Person) -> None:
        """
        Проверяет все инварианты перед добавлением члена семьи.
        Вызывается в application-сервисе до сохранения в репозиторий.
        """
        self._assert_size_limit()
        self._assert_no_duplicate(candidate)

    # ── Инварианты ───────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if not self.name or not self.name.strip():
            raise FamilyDomainError(field="name", message="Название семьи не может быть пустым.")
        if not self.owner_id:
            raise FamilyDomainError(field="owner_id", message="Семья должна иметь владельца.")
        self._validate_years()

    def _validate_years(self) -> None:
        if self.founded_year and self.ended_year and self.founded_year > self.ended_year:
            raise FamilyDomainError(
                field="founded_year",
                message="Год основания не может быть больше года окончания.",
            )

    def _assert_size_limit(self) -> None:
        if len(self.members) >= MAX_FAMILY_SIZE:
            raise FamilyDomainError(
                field="family_id",
                message=(
                    f"В семье уже {len(self.members)} человек(а). Максимально допустимое количество: {MAX_FAMILY_SIZE}."
                ),
            )

    def _assert_no_duplicate(self, candidate: Person) -> None:
        for member in self.members:
            if _is_duplicate(member, candidate):
                raise FamilyDomainError(
                    field="person",
                    message=(
                        f"В этой семье уже есть человек с именем «{candidate.full_name()}» и такой же датой рождения."
                    ),
                )


def _is_duplicate(existing: Person, candidate: Person) -> bool:
    """
    Дубль = совпадение (first_name + last_name + birth_date).
    None != None в бизнес-смысле — не считается дублем.
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


def create_family(
    name: str,
    owner_id: str,
    description: str | None = None,
    origin_place: str | None = None,
    founded_year: int | None = None,
    ended_year: int | None = None,
) -> Family:
    """Фабрика агрегата Family. Единственное место, где генерируется ID."""
    return Family(
        id=generate_uuid(),
        name=name,
        owner_id=owner_id,
        description=description,
        origin_place=origin_place,
        founded_year=founded_year,
        ended_year=ended_year,
    )
