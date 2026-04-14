"""
domain/common/page.py

Представление страницы результатов в доменном слое.

Каждый агрегат имеет свой явный класс страницы
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.entities.family import Family
from domain.entities.person import Person


@dataclass
class BasePage:
    """
    Базовый класс страницы результатов.

    Наследники добавляют поле result с конкретным типом.
    Базовый класс содержит всю пагинационную логику.
    """

    total: int
    limit: int
    offset: int

    @property
    def total_pages(self) -> int:
        """Общее количество страниц."""
        if self.limit <= 0:
            return 0
        return max(1, (self.total + self.limit - 1) // self.limit)

    @property
    def current_page(self) -> int:
        """Номер текущей страницы (с 1)."""
        if self.limit <= 0:
            return 1
        return self.offset // self.limit + 1

    @property
    def has_next(self) -> bool:
        """Есть ли следующая страница."""
        return self.offset + self.limit < self.total

    @property
    def has_prev(self) -> bool:
        """Есть ли предыдущая страница."""
        return self.offset > 0

    @property
    def next_offset(self) -> int | None:
        """Offset для следующей страницы или None."""
        return self.offset + self.limit if self.has_next else None

    @property
    def prev_offset(self) -> int | None:
        """Offset для предыдущей страницы или None."""
        return max(0, self.offset - self.limit) if self.has_prev else None


@dataclass
class PersonPage(BasePage):
    """Страница результатов для агрегата Person."""

    result: list[Person]

    @property
    def is_empty(self) -> bool:
        return len(self.result) == 0


@dataclass
class FamilyPage(BasePage):
    """Страница результатов для агрегата Family."""

    result: list[Family]

    @property
    def is_empty(self) -> bool:
        return len(self.result) == 0
