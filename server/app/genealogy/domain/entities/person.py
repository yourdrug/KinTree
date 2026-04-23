"""
domain/entities/person.py

Person aggregate root.

Design decisions:
- Person owns all mutation via explicit methods (update_*, apply_patch, apply_put).
- Application services call these methods — they never construct PersonName directly.
- reconstruct() is the factory for loading from persistence (no validation side-effects
  that would break on legacy data).
- create_person() is the factory for brand-new persons (full validation).
"""

from __future__ import annotations

from dataclasses import dataclass

from genealogy.domain.enums import PersonGender
from genealogy.domain.value_objects.family_ref import FamilyRef
from shared.domain.exceptions import PersonDomainError
from shared.domain.utils import generate_uuid
from genealogy.domain.value_objects.person_name import PersonName
from genealogy.domain.value_objects.partial_date import PartialDate
from shared.domain.value_objects.unset import UNSET, UnsetType


@dataclass
class Person:
    """
    Aggregate root for a person within a family.

    Invariants enforced here:
    - family_id is always non-empty
    - death_date.year >= birth_date.year (when both are set)
    - PersonName holds the name invariant (at least one of first/last)
    """

    id: str
    name: PersonName
    gender: PersonGender
    family_ref: FamilyRef

    birth_date: PartialDate | None = None
    death_date: PartialDate | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def first_name(self) -> str | None:
        return self.name.first_name

    @property
    def last_name(self) -> str | None:
        return self.name.last_name

    # Обратная совместимость для репозиториев и маппера
    @property
    def family_id(self) -> str:
        return self.family_ref.family_id

    def full_name(self) -> str:
        return self.name.full()

    def is_alive(self) -> bool:
        return self.death_date is None or self.death_date.year is None

    # ── Commands (mutations owned by the entity) ──────────────────────────────

    def apply_put(
        self,
        *,
        gender: PersonGender,
        first_name: str | None,
        last_name: str | None,
        birth_date: PartialDate | None,
        death_date: PartialDate | None,
        birth_date_raw: str | None,
        death_date_raw: str | None,
    ) -> None:
        """
        Full replacement (PUT semantics).
        Validates all invariants after update.
        """
        self.name = PersonName(first_name=first_name, last_name=last_name)
        self.gender = gender
        self.birth_date = birth_date
        self.death_date = death_date
        self.birth_date_raw = birth_date_raw
        self.death_date_raw = death_date_raw
        self._validate()

    def apply_patch(
        self,
        *,
        first_name: str | None | UnsetType = UNSET,
        last_name: str | None | UnsetType = UNSET,
        gender: PersonGender | UnsetType = UNSET,
        birth_date: PartialDate | None | UnsetType = UNSET,
        death_date: PartialDate | None | UnsetType = UNSET,
        birth_date_raw: str | None | UnsetType = UNSET,
        death_date_raw: str | None | UnsetType = UNSET,
    ) -> None:
        """
        Partial update (PATCH semantics).
        UNSET fields are left untouched.
        """
        new_first = self.first_name if isinstance(first_name, UnsetType) else first_name
        new_last = self.last_name if isinstance(last_name, UnsetType) else last_name
        self.name = PersonName(first_name=new_first, last_name=new_last)

        if not isinstance(gender, UnsetType):
            self.gender = gender
        if not isinstance(birth_date, UnsetType):
            self.birth_date = birth_date
        if not isinstance(death_date, UnsetType):
            self.death_date = death_date
        if not isinstance(birth_date_raw, UnsetType):
            self.birth_date_raw = birth_date_raw
        if not isinstance(death_date_raw, UnsetType):
            self.death_date_raw = death_date_raw

        self._validate()

    def identity_fields_changed(
        self,
        *,
        first_name: str | None | UnsetType,
        last_name: str | None | UnsetType,
        birth_date: PartialDate | None | UnsetType,
    ) -> bool:
        """
        Returns True if any field that affects family-level duplicate detection
        is being modified. Used by PersonService to decide whether to re-check
        the family invariant after a PATCH.
        """
        return not (
            isinstance(first_name, UnsetType) and isinstance(last_name, UnsetType) and isinstance(birth_date, UnsetType)
        )

    # ── Invariants ────────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if not self.family_id:
            raise PersonDomainError(
                field="family_id",
                message="Person must belong to a family.",
            )
        self._validate_dates()

    def _validate_dates(self) -> None:
        if self.birth_date and self.death_date:
            b_year = self.birth_date.year
            d_year = self.death_date.year
            if b_year and d_year and d_year < b_year:
                raise PersonDomainError(
                    field="death_date",
                    message="Death date cannot precede birth date.",
                )


def create_person(
    *,
    gender: PersonGender,
    family_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    birth_date: PartialDate | None = None,
    death_date: PartialDate | None = None,
    birth_date_raw: str | None = None,
    death_date_raw: str | None = None,
) -> Person:
    """
    Factory for brand-new persons.
    Generates a fresh ID and runs all invariants.
    """
    return Person(
        id=generate_uuid(),
        name=PersonName(first_name=first_name, last_name=last_name),
        gender=gender,
        family_ref=FamilyRef(family_id=family_id),
        birth_date=birth_date,
        death_date=death_date,
        birth_date_raw=birth_date_raw,
        death_date_raw=death_date_raw,
    )


def reconstruct_person(
    *,
    id: str,
    family_id: str,
    gender: PersonGender,
    first_name: str | None,
    last_name: str | None,
    birth_date: PartialDate | None,
    death_date: PartialDate | None,
    birth_date_raw: str | None,
    death_date_raw: str | None,
) -> Person:
    """
    Factory for rehydrating a Person from persistence.
    Bypasses __post_init__ validation — data is assumed to be already valid
    (it passed validation when it was first saved).
    Use this in mappers only.
    """
    person = object.__new__(Person)
    person.id = id
    person.name = PersonName(first_name=first_name, last_name=last_name)
    person.gender = gender
    person.family_id = family_id
    person.birth_date = birth_date
    person.death_date = death_date
    person.birth_date_raw = birth_date_raw
    person.death_date_raw = death_date_raw
    return person
