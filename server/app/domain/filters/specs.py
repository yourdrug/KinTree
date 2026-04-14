"""
domain/filters/specs.py

Конкретные спецификации фильтрации для каждого агрегата.

Каждый класс:
  - наследует BaseFilterSpec
  - предоставляет типобезопасные фабричные методы
  - не содержит импортов инфраструктуры

"""

from __future__ import annotations

from dataclasses import dataclass

from domain.enums import PersonGender
from domain.filters.base import (
    BaseFilterSpec,
    FilterField,
    FilterOperator,
    SortDirection,
    SortField,
)


@dataclass(frozen=True)
class PersonFilterSpec(BaseFilterSpec):
    """
    Спецификация фильтрации агрегата Person.

    Фабричные методы гарантируют, что бизнес-логика
    (какие поля фильтруемы и с каким оператором) остаётся в домене.
    """

    @staticmethod
    def by_first_name(value: str) -> FilterField:
        return FilterField("first_name", FilterOperator.ICONTAINS, value)

    @staticmethod
    def by_last_name(value: str) -> FilterField:
        return FilterField("last_name", FilterOperator.ICONTAINS, value)

    @staticmethod
    def by_gender(value: PersonGender) -> FilterField:
        return FilterField("gender", FilterOperator.EXACT, value)

    @staticmethod
    def by_family_id(value: str) -> FilterField:
        return FilterField("family_id", FilterOperator.EXACT, value)

    @staticmethod
    def birth_year_gte(value: int) -> FilterField:
        return FilterField("birth_year", FilterOperator.GTE, value)

    @staticmethod
    def birth_year_lte(value: int) -> FilterField:
        return FilterField("birth_year", FilterOperator.LTE, value)

    @staticmethod
    def death_year_gte(value: int) -> FilterField:
        return FilterField("death_year", FilterOperator.GTE, value)

    @staticmethod
    def death_year_lte(value: int) -> FilterField:
        return FilterField("death_year", FilterOperator.LTE, value)

    @staticmethod
    def by_gender_in(values: list[PersonGender]) -> FilterField:
        return FilterField("gender", FilterOperator.IN, values)

    @staticmethod
    def search(value: str) -> FilterField:
        """Поиск по first_name + last_name одновременно."""
        return FilterField("__search__", FilterOperator.SEARCH, value)

    @staticmethod
    def is_alive() -> FilterField:
        """Фильтр: только живые (death_year IS NULL)."""
        return FilterField("death_year", FilterOperator.IS_NULL, True)

    # Сортировка

    @staticmethod
    def sort_by_last_name(direction: SortDirection = SortDirection.ASC) -> SortField:
        return SortField("last_name", direction)

    @staticmethod
    def sort_by_birth_year(direction: SortDirection = SortDirection.ASC) -> SortField:
        return SortField("birth_year", direction)

    @staticmethod
    def sort_by_created_at(direction: SortDirection = SortDirection.DESC) -> SortField:
        return SortField("creation_date", direction)


@dataclass(frozen=True)
class FamilyFilterSpec(BaseFilterSpec):
    """Спецификация фильтрации агрегата Family."""

    @staticmethod
    def by_name(value: str) -> FilterField:
        return FilterField("name", FilterOperator.ICONTAINS, value)

    @staticmethod
    def by_owner_id(value: str) -> FilterField:
        return FilterField("owner_id", FilterOperator.EXACT, value)

    @staticmethod
    def founded_year_gte(value: int) -> FilterField:
        return FilterField("founded_year", FilterOperator.GTE, value)

    @staticmethod
    def founded_year_lte(value: int) -> FilterField:
        return FilterField("founded_year", FilterOperator.LTE, value)

    @staticmethod
    def search(value: str) -> FilterField:
        """Поиск по name + description."""
        return FilterField("__search__", FilterOperator.SEARCH, value)

    @staticmethod
    def sort_by_name(direction: SortDirection = SortDirection.ASC) -> SortField:
        return SortField("name", direction)

    @staticmethod
    def sort_by_founded_year(direction: SortDirection = SortDirection.DESC) -> SortField:
        return SortField("founded_year", direction)
