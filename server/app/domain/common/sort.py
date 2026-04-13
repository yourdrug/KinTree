from dataclasses import dataclass
from enum import StrEnum
from typing import Type, TypeVar, Generic


SortFieldT = TypeVar("SortFieldT", bound=StrEnum)


@dataclass(frozen=True)
class BaseSort(Generic[SortFieldT]):
    field: SortFieldT
    desc: bool = False

    @classmethod
    def from_string(cls, value: str, enum_cls: Type[SortFieldT]) -> "BaseSort[SortFieldT]":
        if value.startswith("-"):
            return cls(field=enum_cls(value[1:]), desc=True)
        return cls(field=enum_cls(value), desc=False)
