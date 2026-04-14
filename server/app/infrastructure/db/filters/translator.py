"""
infrastructure/db/filters/translator.py

Инфраструктурный транслятор: доменная спецификация → SQLAlchemy-запрос.

Принципы:
  - Знает о SQLAlchemy, ORM-моделях и их колонках.
  - Не знает ничего о HTTP / Pydantic.
  - Получает BaseFilterSpec, возвращает изменённый Select.
  - Поддерживает конфигурацию search-полей per-модель.
"""

from __future__ import annotations

from typing import Any

from domain.filters.base import (
    BaseFilterSpec,
    FilterField,
    FilterOperator,
    SortDirection,
    SortField,
)
from sqlalchemy import Select, asc, desc, or_
from sqlalchemy.orm import InstrumentedAttribute


# Маппинг: имя поля агрегата → атрибут ORM-модели
FieldMap = dict[str, InstrumentedAttribute]

# Поля, по которым работает SEARCH (задаются для каждой модели)
SearchFields = tuple[InstrumentedAttribute, ...]


class FilterTranslator:
    """
    Общий транслятор доменных спецификаций в SQLAlchemy Select.

    Usage:
        translator = FilterTranslator(
            field_map={
                "first_name": Person.first_name,
                "last_name":  Person.last_name,
                "birth_year": Person.birth_year,
                ...
            },
            search_fields=(Person.first_name, Person.last_name),
        )
        stmt = translator.apply(stmt, spec)
    """

    def __init__(
        self,
        field_map: FieldMap,
        search_fields: SearchFields = (),
    ) -> None:
        """
        Args:
            field_map:     Маппинг доменных имён полей → ORM-атрибуты.
            search_fields: Поля для оператора SEARCH (ILIKE '%q%').
        """
        self._field_map = field_map
        self._search_fields = search_fields

    def apply(self, stmt: Select, spec: BaseFilterSpec) -> Select:
        """
        Применяет все условия спецификации к запросу.

        Args:
            stmt: Исходный SQLAlchemy Select.
            spec: Доменная спецификация фильтрации.

        Returns:
            Модифицированный Select с WHERE и ORDER BY.
        """
        stmt = self._apply_filters(stmt, spec.filters)
        stmt = self._apply_sort(stmt, spec.sort)
        return stmt

    def apply_pagination(self, stmt: Select, spec: BaseFilterSpec) -> Select:
        """Применяет LIMIT / OFFSET."""
        return stmt.limit(spec.limit).offset(spec.offset)

    def _apply_filters(
        self,
        stmt: Select,
        filters: tuple[FilterField, ...],
    ) -> Select:
        for f in filters:
            clause = self._build_clause(f)
            if clause is not None:
                stmt = stmt.where(clause)
        return stmt

    def _build_clause(self, f: FilterField) -> Any:  # noqa: ANN401
        """
        Транслирует один FilterField в SQLAlchemy-выражение.
        Возвращает None, если поле не найдено в field_map
        (позволяет игнорировать неизвестные поля вместо краша).
        """
        # Специальный мета-ключ для SEARCH
        if f.field_name == "__search__":
            return self._build_search_clause(f.value)

        column = self._field_map.get(f.field_name)
        if column is None:
            return None

        match f.operator:
            case FilterOperator.EXACT:
                return column == f.value

            case FilterOperator.GT:
                return column > f.value

            case FilterOperator.GTE:
                return column >= f.value

            case FilterOperator.LT:
                return column < f.value

            case FilterOperator.LTE:
                return column <= f.value

            case FilterOperator.ICONTAINS:
                return column.ilike(f"%{f.value}%")

            case FilterOperator.IN:
                return column.in_(f.value)

            case FilterOperator.IS_NULL:
                return column.is_(None) if f.value else column.is_not(None)

            case FilterOperator.SEARCH:
                # Если попали сюда — поле не __search__, обрабатываем как icontains
                return column.ilike(f"%{f.value}%")

            case _:
                return None

    def _build_search_clause(self, value: str) -> Any:  # noqa: ANN401
        """
        Полнотекстовый поиск: ILIKE '%value%' по всем search_fields.
        Условия объединяются через OR.
        """
        if not self._search_fields:
            return None

        pattern = f"%{value}%"
        return or_(*(col.ilike(pattern) for col in self._search_fields))

    def _apply_sort(
        self,
        stmt: Select,
        sort_fields: tuple[SortField, ...],
    ) -> Select:
        for s in sort_fields:
            column = self._field_map.get(s.field_name)
            if column is None:
                continue

            order_expr = asc(column) if s.direction == SortDirection.ASC else desc(column)
            stmt = stmt.order_by(order_expr)

        return stmt
