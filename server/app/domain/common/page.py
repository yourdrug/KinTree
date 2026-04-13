from dataclasses import dataclass
from typing import Generic, TypeVar

from domain.entities.person import Person


T = TypeVar("T")


@dataclass
class Pagination:
    limit: int
    offset: int


@dataclass
class Page(Generic[T]):
    result: list[T]
    total: int
    limit: int
    offset: int


PersonPage = Page[Person]
