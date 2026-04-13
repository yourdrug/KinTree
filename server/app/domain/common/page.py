from dataclasses import dataclass
from typing import Generic, TypeVar, List


T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    result: List[T]
    total: int
    limit: int
    offset: int

    @property
    def has_next(self) -> bool:
        return self.offset + self.limit < self.total

    @property
    def has_prev(self) -> bool:
        return self.offset > 0
