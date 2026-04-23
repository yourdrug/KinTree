"""
api/schemas/person.py

Pydantic schemas for the Person API.

Conventions:
- Request schema  → .to_command() produces an application command
- Response schema → .from_domain(entity) builds the response
- Filter schema   → .to_spec() produces a domain filter specification
- No business logic in schemas — only serialization and deserialization
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, ClassVar

from fastapi import Query, Request
from pydantic import BaseModel, Field
from shared.api.schemas.base import BasePageResponse, BasePaginationParams, BasePatchSchema
from shared.domain.exceptions import FilterValidationError
from shared.domain.value_objects.pagination import Page, SortDirection, SortField
from shared.domain.value_objects.unset import UNSET

from genealogy.application.person.commands import CreatePersonCommand, PatchPersonCommand, UpdatePersonCommand
from genealogy.domain.entities.person import Person
from genealogy.domain.enums import PersonGender
from genealogy.domain.filters.specs import PersonFilterSpec
from genealogy.domain.value_objects.partial_date import PartialDate


# ── Value object schemas ──────────────────────────────────────────────────────


class PartialDateSchema(BaseModel):
    year: int | None = Field(None, ge=1, le=9999, examples=[1990])
    month: int | None = Field(None, ge=1, le=12, examples=[6])
    day: int | None = Field(None, ge=1, le=31, examples=[15])

    def to_domain(self) -> PartialDate:
        return PartialDate(year=self.year, month=self.month, day=self.day)

    @classmethod
    def from_domain(cls, date: PartialDate) -> PartialDateSchema:
        return cls(year=date.year, month=date.month, day=date.day)


# ── Request schemas ───────────────────────────────────────────────────────────


class CreatePersonRequest(BaseModel):
    gender: PersonGender = Field(..., examples=[PersonGender.MALE])
    family_id: str = Field(..., min_length=1)
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    def to_command(self) -> CreatePersonCommand:
        return CreatePersonCommand(
            gender=self.gender,
            family_id=self.family_id,
            first_name=self.first_name,
            last_name=self.last_name,
            birth_date=self.birth_date.to_domain() if self.birth_date else None,
            death_date=self.death_date.to_domain() if self.death_date else None,
            birth_date_raw=self.birth_date_raw,
            death_date_raw=self.death_date_raw,
        )


class UpdatePersonRequest(BaseModel):
    """PUT — full replacement; missing optional fields default to None."""

    gender: PersonGender
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    def to_command(self, person_id: str) -> UpdatePersonCommand:
        return UpdatePersonCommand(
            person_id=person_id,
            gender=self.gender,
            first_name=self.first_name,
            last_name=self.last_name,
            birth_date=self.birth_date.to_domain() if self.birth_date else None,
            death_date=self.death_date.to_domain() if self.death_date else None,
            birth_date_raw=self.birth_date_raw,
            death_date_raw=self.death_date_raw,
        )


class PatchPersonRequest(BasePatchSchema):
    """PATCH — only provided fields are updated."""

    non_nullable: ClassVar[list[str]] = ["gender"]

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    gender: PersonGender | None = None
    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    def to_command(self, person_id: str) -> PatchPersonCommand:
        sent = self.model_fields_set

        def _get(fname: str, transform: Any = None) -> Any:
            if fname not in sent:
                return UNSET
            value = getattr(self, fname)
            return transform(value) if transform and value is not None else value

        return PatchPersonCommand(
            person_id=person_id,
            first_name=_get("first_name"),
            last_name=_get("last_name"),
            gender=_get("gender"),
            birth_date=_get("birth_date", lambda v: v.to_domain()),
            death_date=_get("death_date", lambda v: v.to_domain()),
            birth_date_raw=_get("birth_date_raw"),
            death_date_raw=_get("death_date_raw"),
        )


# ── Response schemas ──────────────────────────────────────────────────────────


class PersonResponse(BaseModel):
    id: str
    full_name: str
    gender: PersonGender
    family_id: str
    is_alive: bool
    first_name: str | None = None
    last_name: str | None = None
    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    @classmethod
    def from_domain(cls, person: Person) -> PersonResponse:
        return cls(
            id=person.id,
            full_name=person.full_name(),
            gender=person.gender,
            family_id=person.family_id,
            is_alive=person.is_alive(),
            first_name=person.first_name,
            last_name=person.last_name,
            birth_date=PartialDateSchema.from_domain(person.birth_date) if person.birth_date else None,
            death_date=PartialDateSchema.from_domain(person.death_date) if person.death_date else None,
            birth_date_raw=person.birth_date_raw,
            death_date_raw=person.death_date_raw,
        )


class PersonPageResponse(BasePageResponse):
    result: list[PersonResponse]

    @classmethod
    def from_page(cls, page: Page[Person], request: Request) -> PersonPageResponse:
        meta = cls._build_meta(
            total=page.total,
            limit=page.limit,
            offset=page.offset,
            base_url=str(request.url.replace(query="")),
            query_params=request.query_params,
        )
        return cls(result=[PersonResponse.from_domain(p) for p in page.result], **meta)


# ── Filter schema ─────────────────────────────────────────────────────────────


@dataclass
class PersonFilterSchema(BasePaginationParams):
    first_name__icontains: Annotated[str | None, Query(alias="first_name__icontains")] = None
    last_name__icontains: Annotated[str | None, Query(alias="last_name__icontains")] = None
    gender: Annotated[PersonGender | None, Query()] = None
    gender__in: Annotated[str | None, Query(alias="gender__in")] = None
    family_id: Annotated[str | None, Query()] = None
    birth_year__gte: Annotated[int | None, Query(ge=1, le=9999)] = None
    birth_year__lte: Annotated[int | None, Query(ge=1, le=9999)] = None
    death_year__gte: Annotated[int | None, Query(ge=1, le=9999)] = None
    death_year__lte: Annotated[int | None, Query(ge=1, le=9999)] = None
    is_alive: Annotated[bool | None, Query()] = None
    search: Annotated[str | None, Query()] = None
    order_by: Annotated[str | None, Query(pattern=r"^(last_name|birth_year|creation_date)$")] = None
    order_dir: Annotated[SortDirection, Query()] = SortDirection.ASC

    _gender_in_parsed: list[PersonGender] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._validate_year_range("birth_year__gte", self.birth_year__gte, "birth_year__lte", self.birth_year__lte)
        self._validate_year_range("death_year__gte", self.death_year__gte, "death_year__lte", self.death_year__lte)
        self._gender_in_parsed = _parse_enum_list(self.gender__in, PersonGender, "gender__in")

    def to_spec(self) -> PersonFilterSpec:
        filters = []
        sort = []

        if self.first_name__icontains:
            filters.append(PersonFilterSpec.by_first_name(self.first_name__icontains))
        if self.last_name__icontains:
            filters.append(PersonFilterSpec.by_last_name(self.last_name__icontains))
        if self.gender is not None:
            filters.append(PersonFilterSpec.by_gender(self.gender))
        if self._gender_in_parsed:
            filters.append(PersonFilterSpec.by_gender_in(self._gender_in_parsed))
        if self.family_id:
            filters.append(PersonFilterSpec.by_family_id(self.family_id))
        if self.birth_year__gte is not None:
            filters.append(PersonFilterSpec.birth_year_gte(self.birth_year__gte))
        if self.birth_year__lte is not None:
            filters.append(PersonFilterSpec.birth_year_lte(self.birth_year__lte))
        if self.death_year__gte is not None:
            filters.append(PersonFilterSpec.death_year_gte(self.death_year__gte))
        if self.death_year__lte is not None:
            filters.append(PersonFilterSpec.death_year_lte(self.death_year__lte))
        if self.is_alive is True:
            filters.append(PersonFilterSpec.is_alive())
        if self.search:
            filters.append(PersonFilterSpec.search(self.search))
        if self.order_by:
            sort.append(SortField(self.order_by, self.order_dir))

        return PersonFilterSpec(
            filters=tuple(filters),
            sort=tuple(sort),
            limit=self.limit,
            offset=self.offset,
        )

    @staticmethod
    def _validate_year_range(gte_name: str, gte_val: int | None, lte_name: str, lte_val: int | None) -> None:
        if gte_val is not None and lte_val is not None and gte_val > lte_val:
            raise FilterValidationError(
                message="Validation error",
                errors={gte_name: f"{gte_name} cannot be greater than {lte_name}"},
            )


def _parse_enum_list(raw: str | None, enum_cls: type[Enum], param_name: str) -> list | None:
    if raw is None:
        return None
    valid = {e.value for e in enum_cls}
    result = []
    for part in raw.split(","):
        value = part.strip()
        if value not in valid:
            raise FilterValidationError(
                message="Validation error",
                errors={param_name: f"Invalid value «{value}». Allowed: {sorted(valid)}"},
            )
        result.append(enum_cls(value))
    return result or None
