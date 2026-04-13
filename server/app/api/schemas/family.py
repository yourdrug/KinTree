"""
API Schemas — Family.

Принципы те же:
  - CreateFamilyRequest  — без id
  - PutFamilyRequest     — полный объект (PUT)
  - PatchFamilyRequest   — частичное обновление (PATCH)
  - FamilyResponse       — всегда с id

Маппинг domain <-> schema живёт здесь же.
"""

from __future__ import annotations

from typing import Any

from api.schemas.base import BasePatchSchema
from application.family.dto import PatchFamilyCommand, PutFamilyCommand
from domain.entities.family import Family
from domain.exceptions import DomainFamilyError
from domain.value_objects.unset import UNSET
from pydantic import BaseModel, Field, model_validator


class CreateFamilyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Семья Ивановых"])
    owner_id: str = Field(..., min_length=1)

    description: str | None = None
    origin_place: str | None = None
    founded_year: int | None = Field(None, ge=1, le=9999)
    ended_year: int | None = Field(None, ge=1, le=9999)

    def to_domain(self) -> Family:
        return Family.create_family(
            name=self.name,
            owner_id=self.owner_id,
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


# class FamilyListRequest(BaseModel):
#     name: str | None = None
#     owner_id: str | None = None
#
#     limit: int = Field(default=20, ge=1, le=100)
#     offset: int = Field(default=0, ge=0)
#
#     def to_query(self) -> FamilyListQuery:
#         return FamilyListQuery(
#             name=self.name,
#             owner_id=self.owner_id,
#             limit=self.limit,
#             offset=self.offset,
#         )
#
#
# class FamilyPageResponse(BaseModel):
#     result: list[FamilyResponse]
#     total: int
#     limit: int
#     offset: int
#     has_next: bool
#     has_prev: bool
#
#     @classmethod
#     def from_domain(cls, page: FamilyPage) -> FamilyPageResponse:
#         return cls(
#             result=[FamilyResponse.from_domain(f) for f in page.result],
#             total=page.total,
#             limit=page.limit,
#             offset=page.offset,
#             has_next=page.has_next,
#             has_prev=page.has_prev,
#         )
