"""
shared/domain/value_objects/pagination.py

Value Objects для описания условий выборки.

FilterField — одно условие (field + operator + value).
SortField   — одно условие сортировки.
BaseFilterSpec — совокупность условий + пагинация.

"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Generic, TypeVar


T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """Обобщённая страница результатов."""

    result: list[T]
    total: int
    limit: int
    offset: int

    @property
    def has_next(self) -> bool:
        return self.offset + self.limit < self.total

    @property
    def has_prev(self) -> bool:
        return self.offset > 0

    @property
    def total_pages(self) -> int:
        if self.limit <= 0:
            return 0
        return max(1, (self.total + self.limit - 1) // self.limit)

    @property
    def next_offset(self) -> int | None:
        return self.offset + self.limit if self.has_next else None

    @property
    def prev_offset(self) -> int | None:
        return max(0, self.offset - self.limit) if self.has_prev else None


class FilterOperator(str, Enum):
    """Доступные операции для фильтрации"""
    EXACT = "exact"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    ICONTAINS = "icontains"
    IN = "in"
    SEARCH = "search"
    IS_NULL = "is_null"


class SortDirection(str, Enum):
    """Параметры сортировки по убыванию или возрастанию"""
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True)
class FilterField:
    """Поле для фильтрации"""
    field_name: str
    operator: FilterOperator
    value: Any

    def __post_init__(self) -> None:
        if self.value is None and self.operator not in (FilterOperator.IS_NULL, FilterOperator.EXACT):
            raise ValueError(
                f"FilterField '{self.field_name}': value=None допустимо "
                f"только для EXACT и IS_NULL, получен {self.operator}."
            )
        if self.operator == FilterOperator.IN and not isinstance(self.value, (list, tuple, set, frozenset)):
            raise ValueError(f"FilterField '{self.field_name}': оператор IN требует коллекцию.")


@dataclass(frozen=True)
class SortField:
    """Поле для сортировки"""
    field_name: str
    direction: SortDirection = SortDirection.ASC


@dataclass(frozen=True)
class BaseFilterSpec:
    """Совокупность полей для фильтраций и полей для сортировок"""
    filters: tuple[FilterField, ...] = field(default_factory=tuple)
    sort: tuple[SortField, ...] = field(default_factory=tuple)
    limit: int = 20
    offset: int = 0

    def add_filter(self, f: FilterField) -> BaseFilterSpec:
        return replace(self, filters=(*self.filters, f))

    def add_sort(self, s: SortField) -> BaseFilterSpec:
        return replace(self, sort=(*self.sort, s))

    def has_filter(self, field_name: str) -> bool:
        return any(f.field_name == field_name for f in self.filters)

    def is_empty(self) -> bool:
        return not self.filters and not self.sort
