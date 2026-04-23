"""
api/schemas/family.py

Pydantic schemas for the Family API.

Note on members_count:
  This field reflects the in-memory list of members on the Family aggregate.
  - On GET /families/{id}        : always 0 (members not loaded in this endpoint)
  - On POST /families (create)   : always 0 (no members yet)
  To get member count, use GET /persons?family_id=<id> with pagination metadata.

  If you need count in the list, add a COUNT subquery to FamilyRepositoryImpl.list().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, ClassVar

from genealogy.application.family.commands import CreateFamilyCommand, PatchFamilyCommand, PutFamilyCommand
from genealogy.domain.entities.family import Family
from shared.domain.exceptions import FilterValidationError
from genealogy.domain.filters.specs import FamilyFilterSpec
from shared.domain.value_objects.pagination import Page, SortDirection, SortField
from shared.domain.value_objects.unset import UNSET
from fastapi import Query, Request
from pydantic import BaseModel, Field

from shared.api.schemas.base import BasePageResponse, BasePaginationParams, BasePatchSchema


# ── Request schemas ───────────────────────────────────────────────────────────


class CreateFamilyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Иванов"])
    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = Field(None, ge=1, le=9999)
    ended_year: int | None = Field(None, ge=1, le=9999)

    def to_command(self) -> CreateFamilyCommand:
        return CreateFamilyCommand(
            name=self.name,
            description=self.description,
            origin_place=self.origin_place,
            founded_year=self.founded_year,
            ended_year=self.ended_year,
        )


class PutFamilyRequest(BaseModel):
    """PUT — all fields required; missing optionals reset to None."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = Field(None, ge=1, le=9999)
    ended_year: int | None = Field(None, ge=1, le=9999)

    def to_command(self, family_id: str) -> PutFamilyCommand:
        return PutFamilyCommand(
            family_id=family_id,
            name=self.name,
            description=self.description,
            origin_place=self.origin_place,
            founded_year=self.founded_year,
            ended_year=self.ended_year,
        )


class PatchFamilyRequest(BasePatchSchema):
    """PATCH — only provided fields are updated."""

    non_nullable: ClassVar[list[str]] = ["name"]

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = Field(None, ge=1, le=9999)
    ended_year: int | None = Field(None, ge=1, le=9999)

    def to_command(self, family_id: str) -> PatchFamilyCommand:
        sent = self.model_fields_set
        return PatchFamilyCommand(
            family_id=family_id,
            name=self.name if "name" in sent else UNSET,  # type: ignore[arg-type]
            description=self.description if "description" in sent else UNSET,
            origin_place=self.origin_place if "origin_place" in sent else UNSET,
            founded_year=self.founded_year if "founded_year" in sent else UNSET,
            ended_year=self.ended_year if "ended_year" in sent else UNSET,
        )


# ── Response schemas ──────────────────────────────────────────────────────────


class FamilyResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = None
    ended_year: int | None = None

    @classmethod
    def from_domain(cls, family: Family) -> FamilyResponse:
        return cls(
            id=family.id,
            name=family.name,
            owner_id=family.owner_id,
            description=family.description,
            origin_place=family.origin_place,
            founded_year=family.founded_year,
            ended_year=family.ended_year,
        )


class FamilyPageResponse(BasePageResponse):
    result: list[FamilyResponse]

    @classmethod
    def from_page(cls, page: Page[Family], request: Request) -> FamilyPageResponse:
        meta = cls._build_meta(
            total=page.total,
            limit=page.limit,
            offset=page.offset,
            base_url=str(request.url.replace(query="")),
            query_params=request.query_params,
        )
        return cls(result=[FamilyResponse.from_domain(f) for f in page.result], **meta)


# ── Filter schema ─────────────────────────────────────────────────────────────


@dataclass
class FamilyFilterSchema(BasePaginationParams):
    name__icontains: Annotated[str | None, Query(alias="name__icontains", min_length=1, max_length=255)] = None
    owner_id: Annotated[str | None, Query(min_length=32, max_length=32)] = None
    founded_year__gte: Annotated[int | None, Query(alias="founded_year__gte", ge=1, le=9999)] = None
    founded_year__lte: Annotated[int | None, Query(alias="founded_year__lte", ge=1, le=9999)] = None
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None
    order_by: Annotated[str | None, Query(pattern=r"^(name|founded_year|creation_date)$")] = None
    order_dir: Annotated[SortDirection, Query()] = SortDirection.ASC

    def __post_init__(self) -> None:
        if (
            self.founded_year__gte is not None
            and self.founded_year__lte is not None
            and self.founded_year__gte > self.founded_year__lte
        ):
            raise FilterValidationError(
                message="Validation error",
                errors={"founded_year__gte": "founded_year__gte cannot be greater than founded_year__lte"},
            )

    def to_spec(self) -> FamilyFilterSpec:
        filters = []
        sort = []

        if self.name__icontains:
            filters.append(FamilyFilterSpec.by_name(self.name__icontains))
        if self.owner_id:
            filters.append(FamilyFilterSpec.by_owner_id(self.owner_id))
        if self.founded_year__gte is not None:
            filters.append(FamilyFilterSpec.founded_year_gte(self.founded_year__gte))
        if self.founded_year__lte is not None:
            filters.append(FamilyFilterSpec.founded_year_lte(self.founded_year__lte))
        if self.search:
            filters.append(FamilyFilterSpec.search(self.search))
        if self.order_by:
            sort.append(SortField(self.order_by, self.order_dir))

        return FamilyFilterSpec(
            filters=tuple(filters),
            sort=tuple(sort),
            limit=self.limit,
            offset=self.offset,
        )
