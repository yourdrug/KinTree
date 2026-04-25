"""
domain/entities/family.py

Family aggregate root.

Family is the consistency boundary for its members.
assert_can_add_member() enforces all cross-person invariants before persistence.

Изменение (decoupling):
  Раньше assert_can_add_member() принимал Person — объект другого агрегата.
  Теперь принимает FamilyMemberSpec — VO из своего bounded context.
  Family больше не импортирует Person. Зависимость разорвана.

Исправление порядка полей dataclass:
  _member_specs вынесен из полей dataclass в __post_init__ через object.__setattr__,
  чтобы избежать проблем с порядком полей (non-default после default).
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.exceptions import FamilyDomainError
from shared.domain.utils import generate_uuid
from shared.domain.value_objects.unset import UNSET, UnsetType

from genealogy.domain.value_objects.family_member_spec import FamilyMemberSpec


_MAX_NAME_LENGTH = 255
_MIN_YEAR = 1
_MAX_YEAR = 9999


@dataclass
class Family:
    """
    Family aggregate root.

    Invariants:
    - name is non-empty and <= 255 chars
    - owner_id is non-empty
    - founded_year <= ended_year (when both set)
    - both years in range [1, 9999]
    - No duplicate members (same name + birth_date)

    _member_specs is NOT a dataclass field — it is set in __post_init__
    to avoid MRO / field-ordering issues with defaults.
    """

    id: str
    name: str
    owner_id: str
    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = None
    ended_year: int | None = None

    def __post_init__(self) -> None:
        # Not a dataclass field — managed manually to avoid ordering issues.
        # Private; only mutated via load_member_specs().
        object.__setattr__(self, "_member_specs", [])
        self._validate()

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def members_count(self) -> int:
        return len(self._member_specs)  # type: ignore[attr-defined]

    # ── Commands ──────────────────────────────────────────────────────────────

    def load_member_specs(self, specs: list[FamilyMemberSpec]) -> None:
        """
        Загружает спецификации существующих членов семьи для последующей
        проверки дублирования.

        Вызывается в PersonService ДО assert_can_add_member().
        Не персистируется — только для проверки инвариантов в рамках use-case.
        """
        object.__setattr__(self, "_member_specs", list(specs))

    def assert_can_add_member(self, candidate: FamilyMemberSpec) -> None:
        """
        Проверяет инварианты перед добавлением нового члена семьи.

        Принимает FamilyMemberSpec, а не Person — Family не знает о Person.
        Вызывается PersonService перед персистированием.

        Raises:
            FamilyDomainError: если кандидат является дубликатом.
        """
        if not candidate.has_identity():
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

        if len(self.name) > _MAX_NAME_LENGTH:
            raise FamilyDomainError(
                field="name",
                message=f"Family name cannot exceed {_MAX_NAME_LENGTH} characters.",
            )

        if not self.owner_id or not self.owner_id.strip():
            raise FamilyDomainError(field="owner_id", message="Family must have an owner.")

        if not self.id or not self.id.strip():
            raise FamilyDomainError(field="id", message="Family ID cannot be empty.")

        self._validate_optional_strings()
        self._validate_years()

    def _validate_optional_strings(self) -> None:
        if self.description is not None and not self.description.strip():
            raise FamilyDomainError(
                field="description",
                message="Description cannot be an empty string; use null to clear it.",
            )

        if self.origin_place is not None and not self.origin_place.strip():
            raise FamilyDomainError(
                field="origin_place",
                message="Origin place cannot be an empty string; use null to clear it.",
            )

    def _validate_years(self) -> None:
        if self.founded_year is not None and not (_MIN_YEAR <= self.founded_year <= _MAX_YEAR):
            raise FamilyDomainError(
                field="founded_year",
                message=f"Founded year must be between {_MIN_YEAR} and {_MAX_YEAR}.",
            )

        if self.ended_year is not None and not (_MIN_YEAR <= self.ended_year <= _MAX_YEAR):
            raise FamilyDomainError(
                field="ended_year",
                message=f"Ended year must be between {_MIN_YEAR} and {_MAX_YEAR}.",
            )

        if self.founded_year is not None and self.ended_year is not None and self.founded_year > self.ended_year:
            raise FamilyDomainError(
                field="founded_year",
                message="Founded year cannot be greater than ended year.",
            )

    def _assert_no_duplicate(self, candidate: FamilyMemberSpec) -> None:
        for existing in self._member_specs:  # type: ignore[attr-defined]
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
    if not owner_id or not owner_id.strip():
        raise FamilyDomainError(field="owner_id", message="owner_id cannot be empty.")

    return Family(
        id=generate_uuid(),
        name=name,
        owner_id=owner_id,
        description=description,
        origin_place=origin_place,
        founded_year=founded_year,
        ended_year=ended_year,
    )
