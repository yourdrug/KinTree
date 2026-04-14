"""
domain/filters/base.py

Доменный слой фильтрации.

Принципы:
  - FilterField    — Value Object, описывает одно условие фильтрации
  - FilterSpec     — совокупность условий для конкретного агрегата
  - SortSpec       — сортировка (тоже Value Object)
  - FilterOperator — перечисление допустимых операторов

Это чистый домен: только бизнес-смысл условий выборки.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any


class FilterOperator(str, Enum):
    """
    Перечисление поддерживаемых операторов фильтрации.

    Naming convention намеренно совпадает с Django ORM / SQLAlchemy lookups,
    чтобы инфраструктурный слой мог транслировать их без доп. маппинга.
    """

    EXACT = "exact"          # field = value
    GT = "gt"                # field > value
    GTE = "gte"              # field >= value
    LT = "lt"                # field < value
    LTE = "lte"              # field <= value
    ICONTAINS = "icontains"  # ILIKE '%value%'
    IN = "in"                # field IN (v1, v2, ...)
    SEARCH = "search"        # full-text / multi-column ILIKE (настраивается в инфраструктуре)
    IS_NULL = "is_null"      # field IS NULL / IS NOT NULL


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True)
class FilterField:
    """
    Value Object одного условия фильтрации.

    Attributes:
        field_name: Имя поля агрегата (доменное, не колонка БД).
        operator:   Оператор сравнения.
        value:      Значение для сравнения.
    """

    field_name: str
    operator: FilterOperator
    value: Any

    def __post_init__(self) -> None:
        if self.value is None and self.operator not in (
            FilterOperator.IS_NULL,
            FilterOperator.EXACT,
        ):
            raise ValueError(
                f"FilterField '{self.field_name}': value=None допустимо "
                f"только для операторов EXACT и IS_NULL, получен {self.operator}."
            )

        if self.operator == FilterOperator.IN and not isinstance(self.value, (list, tuple, set, frozenset)):
            raise ValueError(
                f"FilterField '{self.field_name}': оператор IN требует коллекцию, "
                f"получен {type(self.value).__name__}."
            )


@dataclass(frozen=True)
class SortField:
    """
    Value Object одного условия сортировки.

    Attributes:
        field_name: Имя поля агрегата.
        direction:  Направление сортировки.
    """

    field_name: str
    direction: SortDirection = SortDirection.ASC


@dataclass(frozen=True)
class BaseFilterSpec:
    """
    Базовая спецификация фильтрации и сортировки.

    Конкретные агрегаты наследуют этот класс и добавляют
    фабричные методы для типобезопасного построения условий.

    Attributes:
        filters: Неизменяемый список условий фильтрации.
        sort:    Неизменяемый список условий сортировки.
        limit:   Максимальное количество записей.
        offset:  Смещение выборки.
    """

    filters: tuple[FilterField, ...] = field(default_factory=tuple)
    sort: tuple[SortField, ...] = field(default_factory=tuple)
    limit: int = 20
    offset: int = 0

    def add_filter(self, f: FilterField) -> BaseFilterSpec:
        return self._replace(filters=(*self.filters, f))

    def add_sort(self, s: SortField) -> BaseFilterSpec:
        return self._replace(sort=(*self.sort, s))

    def with_pagination(self, limit: int, offset: int) -> BaseFilterSpec:
        return self._replace(limit=limit, offset=offset)

    def _replace(self, **changes: Any) -> BaseFilterSpec:
        return replace(self, **changes)

    def get_filters_by_field(self, field_name: str) -> list[FilterField]:
        return [f for f in self.filters if f.field_name == field_name]

    def has_filter(self, field_name: str) -> bool:
        return any(f.field_name == field_name for f in self.filters)

    def is_empty(self) -> bool:
        return not self.filters and not self.sort
