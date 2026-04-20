from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import DomainValidationError


@dataclass(frozen=True)
class PartialDate:
    """
    Value Object: неполная дата (год/месяц/день могут отсутствовать).

    Примеры допустимых значений:
    - PartialDate(year=1990)                  — только год
    - PartialDate(year=1990, month=6)         — год и месяц
    - PartialDate(year=1990, month=6, day=15) — полная дата
    - PartialDate(month=6, day=15)            — без года (редко, но допустимо)

    Недопустимо:
    - PartialDate(day=15) без month
    """

    year: int | None = None
    month: int | None = None
    day: int | None = None

    def __post_init__(self) -> None:
        self._validate()

    def is_empty(self) -> bool:
        return self.year is None and self.month is None and self.day is None

    def is_full(self) -> bool:
        return self.year is not None and self.month is not None and self.day is not None

    def to_tuple(self) -> tuple[int | None, int | None, int | None]:
        return self.year, self.month, self.day

    def _validate(self) -> None:
        if self.month is not None and not (1 <= self.month <= 12):
            raise DomainValidationError(field="month", message="Месяц должен быть от 1 до 12.")

        if self.day is not None:
            if self.month is None:
                raise DomainValidationError(field="day", message="День нельзя указать без месяца.")
            max_day = self._days_in_month(self.year, self.month)
            if not (1 <= self.day <= max_day):
                raise DomainValidationError(
                    field="day",
                    message=f"День должен быть от 1 до {max_day} для месяца {self.month}.",
                )

    @staticmethod
    def _days_in_month(year: int | None, month: int) -> int:
        if month in {1, 3, 5, 7, 8, 10, 12}:
            return 31
        if month in {4, 6, 9, 11}:
            return 30
        # Февраль
        if year is not None and PartialDate._is_leap(year):
            return 29
        return 28

    @staticmethod
    def _is_leap(year: int) -> bool:
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
