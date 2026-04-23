"""
domain/entities/family.py

Family aggregate root.

Family is the consistency boundary for its members.
assert_can_add_member() enforces all cross-person invariants before persistence.

Изменение (decoupling):
  Раньше assert_can_add_member() принимал Person — объект другого агрегата.
  Теперь принимает FamilyMemberSpec — VO из своего bounded context.
  Family больше не импортирует Person. Зависимость разорвана.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.exceptions import FamilyDomainError
from shared.domain.utils import generate_uuid
from shared.domain.value_objects.unset import UNSET, UnsetType

from genealogy.domain.value_objects.family_member_spec import FamilyMemberSpec


@dataclass
class Family:
    """
    Family aggregate root.

    Invariants:
    - name is non-empty
    - owner_id is non-empty
    - founded_year <= ended_year (when both set)
    - No duplicate members (same name + birth_date)
    """

    id: str
    name: str
    owner_id: str

    # Список FamilyMemberSpec загружается сервисом перед проверкой дублирования.
    # Хранится в памяти только во время use-case, не персистируется здесь.
    _member_specs: list[FamilyMemberSpec] = field(default_factory=list, repr=False)

    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = None
    ended_year: int | None = None

    def __post_init__(self) -> None:
        self._validate()

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def members_count(self) -> int:
        return len(self._member_specs)

    # ── Commands ──────────────────────────────────────────────────────────────

    def load_member_specs(self, specs: list[FamilyMemberSpec]) -> None:
        """
        Загружает спецификации существующих членов семьи для последующей
        проверки дублирования.

        Вызывается в PersonService ДО assert_can_add_member().
        Не персистируется — только для проверки инвариантов в рамках use-case.
        """
        self._member_specs = specs

    def assert_can_add_member(self, candidate: FamilyMemberSpec) -> None:
        """
        Проверяет инварианты перед добавлением нового члена семьи.

        Принимает FamilyMemberSpec, а не Person — Family не знает о Person.
        Вызывается PersonService перед персистированием.

        Raises:
            FamilyDomainError: если кандидат является дубликатом.
        """
        if not candidate.has_identity():
            # Нет имени — проверка дублирования невозможна, пропускаем.
            return
        self._assert_no_duplicate(candidate)

    def apply_put(
        self,
        *,
        name: str,
        description: str | None,
        origin_place: str | None,
        founded_year: int | None,
        ended_year: int | None,
    ) -> None:
        """Full replacement (PUT semantics). Validates after update."""
        self.name = name
        self.description = description
        self.origin_place = origin_place
        self.founded_year = founded_year
        self.ended_year = ended_year
        self._validate()

    def apply_patch(
        self,
        *,
        name: str | UnsetType = UNSET,
        description: str | None | UnsetType = UNSET,
        origin_place: str | None | UnsetType = UNSET,
        founded_year: int | None | UnsetType = UNSET,
        ended_year: int | None | UnsetType = UNSET,
    ) -> None:
        """Partial update (PATCH semantics). UNSET fields are untouched."""
        if not isinstance(name, UnsetType):
            self.name = name
        if not isinstance(description, UnsetType):
            self.description = description
        if not isinstance(origin_place, UnsetType):
            self.origin_place = origin_place
        if not isinstance(founded_year, UnsetType):
            self.founded_year = founded_year
        if not isinstance(ended_year, UnsetType):
            self.ended_year = ended_year
        self._validate()

    # ── Invariants ────────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if not self.name or not self.name.strip():
            raise FamilyDomainError(field="name", message="Family name cannot be empty.")
        if not self.owner_id:
            raise FamilyDomainError(field="owner_id", message="Family must have an owner.")
        self._validate_years()

    def _validate_years(self) -> None:
        if self.founded_year is not None and self.ended_year is not None and self.founded_year > self.ended_year:
            raise FamilyDomainError(
                field="founded_year",
                message="Founded year cannot be greater than ended year.",
            )

    def _assert_no_duplicate(self, candidate: FamilyMemberSpec) -> None:
        for existing in self._member_specs:
            if _is_duplicate(existing, candidate):
                name = " ".join(filter(None, [candidate.first_name, candidate.last_name]))
                raise FamilyDomainError(
                    field="person",
                    message=(f"A person named «{name}» with the same birth date already exists in this family."),
                )


def _is_duplicate(existing: FamilyMemberSpec, candidate: FamilyMemberSpec) -> bool:
    """
    Дубликат = совпадение (first_name + last_name + birth_date).
    None != None в бизнес-терминах — не является дубликатом.
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
    *,
    name: str,
    owner_id: str,
    description: str | None = None,
    origin_place: str | None = None,
    founded_year: int | None = None,
    ended_year: int | None = None,
) -> Family:
    """Factory for brand-new families. Generates ID and validates."""
    return Family(
        id=generate_uuid(),
        name=name,
        owner_id=owner_id,
        description=description,
        origin_place=origin_place,
        founded_year=founded_year,
        ended_year=ended_year,
    )
