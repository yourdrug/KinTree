from dataclasses import dataclass, fields
from typing import Generic, TypeVar, Type, Any
from enum import StrEnum

from domain.common.sort import BaseSort

SortFieldT = TypeVar("SortFieldT", bound=StrEnum)


@dataclass
class BaseFilters(Generic[SortFieldT]):
    sort: BaseSort[SortFieldT] | None = None

    @classmethod
    def build_sort(
        cls,
        sort_by: str | None,
        enum_cls: Type[SortFieldT],
    ) -> BaseSort[SortFieldT] | None:
        if not sort_by:
            return None
        return BaseSort.from_string(sort_by, enum_cls)

    def to_dict(self) -> dict[str, Any]:
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) is not None and f.name != "sort"
        }
