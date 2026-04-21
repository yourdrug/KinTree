from dataclasses import dataclass

from domain.value_objects.unset import UNSET, UnsetType


@dataclass(frozen=True)
class CreateFamilyCommand:
    name: str

    description: str | None
    origin_place: str | None
    founded_year: int | None
    ended_year: int | None


@dataclass(frozen=True)
class PatchFamilyCommand:
    family_id: str

    name: str | UnsetType = UNSET

    description: str | None | UnsetType = UNSET
    origin_place: str | None | UnsetType = UNSET
    founded_year: int | None | UnsetType = UNSET
    ended_year: int | None | UnsetType = UNSET


@dataclass(frozen=True)
class PutFamilyCommand:
    family_id: str

    name: str

    description: str | None
    origin_place: str | None
    founded_year: int | None
    ended_year: int | None
