from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from application.family.dto import CreateFamilyCommand, PatchFamilyCommand, PutFamilyCommand
from domain.entities.family import Family
from domain.exceptions import FilterError
from domain.filters.base import SortDirection, SortField
from domain.filters.page import FamilyPage
from domain.filters.specs import FamilyFilterSpec
from domain.value_objects.unset import UNSET
from fastapi import Query, Request
from pydantic import BaseModel, Field

from api.schemas.base import BasePageMeta, BasePaginationParams, BasePatchSchema


class CreateFamilyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Семья Ивановых"])

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
    name: str = Field(..., min_length=1, max_length=255)

    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = Field(None, ge=1, le=9999)
    ended_year: int | None = Field(None, ge=1, le=9999)

    def to_command(self, family_id: str, account_id: str) -> PutFamilyCommand:
        return PutFamilyCommand(
            family_id=family_id,
            owner_id=account_id,
            name=self.name,
            description=self.description,
            origin_place=self.origin_place,
            founded_year=self.founded_year,
            ended_year=self.ended_year,
        )


class PatchFamilyRequest(BasePatchSchema):
    non_nullable = ["owner_id", "name"]

    name: str | None = Field(None, min_length=1, max_length=255)

    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = Field(None, ge=1, le=9999)
    ended_year: int | None = Field(None, ge=1, le=9999)

    def to_command(self, family_id: str) -> PatchFamilyCommand:
        sent = self.model_fields_set

        return PatchFamilyCommand(
            family_id=family_id,
            name=self.name if "name" in sent else UNSET,  # type: ignore
            description=self.description if "description" in sent else UNSET,
            origin_place=self.origin_place if "origin_place" in sent else UNSET,
            founded_year=self.founded_year if "founded_year" in sent else UNSET,
            ended_year=self.ended_year if "ended_year" in sent else UNSET,
        )


class FamilyResponse(BaseModel):
    id: str
    name: str
    owner_id: str

    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = None
    ended_year: int | None = None

    members_count: int

    model_config = {"from_attributes": True}

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
            members_count=len(family.members) if family.members else 0,
        )


class FamilyPageResponse(BasePageMeta):
    result: list[FamilyResponse]

    @classmethod
    def from_domain(cls, page: FamilyPage, request: Request) -> FamilyPageResponse:
        meta = cls._build_meta(
            total=page.total,
            limit=page.limit,
            offset=page.offset,
            base_url=str(request.url.replace(query="")),
            query_params=request.query_params,
        )

        return cls(
            result=[FamilyResponse.from_domain(f) for f in page.result],
            **meta,
        )


@dataclass
class FamilyFilterSchema(BasePaginationParams):
    """
    Query-параметры фильтрации для Family.

    Доступные параметры:
        name__icontains      — ILIKE '%value%' по названию
        owner_id             — точный ID владельца
        founded_year__gte    — год основания >=
        founded_year__lte    — год основания <=
        search               — ILIKE по name + description
        order_by             — name | founded_year | creation_date
        order_dir            — asc | desc
    """

    name__icontains: Annotated[
        str | None,
        Query(alias="name__icontains", min_length=1, max_length=255),
    ] = None

    owner_id: Annotated[str | None, Query(min_length=32, max_length=32)] = None

    founded_year__gte: Annotated[int | None, Query(alias="founded_year__gte", ge=1, le=9999)] = None
    founded_year__lte: Annotated[int | None, Query(alias="founded_year__lte", ge=1, le=9999)] = None

    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None

    order_by: Annotated[
        str | None,
        Query(pattern=r"^(name|founded_year|creation_date)$"),
    ] = None
    order_dir: Annotated[SortDirection, Query()] = SortDirection.ASC

    def __post_init__(self) -> None:
        if (
            self.founded_year__gte is not None
            and self.founded_year__lte is not None
            and self.founded_year__gte > self.founded_year__lte
        ):
            raise FilterError(
                message="Ошибка валидации",
                errors={"founded_year__gte": "founded_year__gte не может быть больше founded_year__lte"},
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
