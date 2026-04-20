"""
domain/entities/family.py

Family aggregate root.

Family is the consistency boundary for its members.
assert_can_add_member() enforces all cross-person invariants before persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.entities.person import Person
from domain.exceptions import FamilyDomainError
from domain.utils import generate_uuid
from domain.value_objects.unset import UNSET, UnsetType


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
    members: list[Person] = field(default_factory=list)

    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = None
    ended_year: int | None = None

    def __post_init__(self) -> None:
        self._validate()

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def members_count(self) -> int:
        return len(self.members)

    # ── Commands ──────────────────────────────────────────────────────────────

    def assert_can_add_member(self, candidate: Person) -> None:
        """
        Validates all invariants before a new member is added.
        Called by PersonService before persisting — never by the repository.
        """
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

    def _assert_no_duplicate(self, candidate: Person) -> None:
        for member in self.members:
            if _is_duplicate(member, candidate):
                raise FamilyDomainError(
                    field="person",
                    message=(
                        f"A person named «{candidate.full_name()}» with the same "
                        f"birth date already exists in this family."
                    ),
                )


def _is_duplicate(existing: Person, candidate: Person) -> bool:
    """
    Duplicate = same (first_name + last_name + birth_date).
    None != None in business terms — not a duplicate.
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
