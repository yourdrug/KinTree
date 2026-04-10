from dataclasses import dataclass


@dataclass(frozen=True)
class PartialDate:
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
        year, month, day = self.year, self.month, self.day

        # (optional)
        # if month is not None and year is None:
        #     raise ValueError("Year must be provided if month is set")

        if month is not None and not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")

        if day is not None:
            if month is None:
                raise ValueError("Month must be provided if day is set")

            max_day = self._days_in_month(year, month)
            if not (1 <= day <= max_day):
                raise ValueError(f"Day must be between 1 and {max_day} for month {month}")

    @staticmethod
    def _days_in_month(year: int | None, month: int) -> int:
        if month in {1, 3, 5, 7, 8, 10, 12}:
            return 31
        if month in {4, 6, 9, 11}:
            return 30

        # February
        if year is not None and PartialDate._is_leap_year(year):
            return 29
        return 28

    @staticmethod
    def _is_leap_year(year: int) -> bool:
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
