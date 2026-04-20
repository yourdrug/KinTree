from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """
    Обобщённая страница результатов.
    Используется всеми репозиториями — не дублируем PersonPage/FamilyPage.
    """

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
