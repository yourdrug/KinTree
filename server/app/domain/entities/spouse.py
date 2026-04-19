from __future__ import annotations

from dataclasses import dataclass

from domain.enums import MarriageStatus
from domain.exceptions import DomainRelationError
from domain.value_objects.partial_date import PartialDate


@dataclass(frozen=True)
class SpouseRelation:
    """
    Value Object: супружеская связь.

    Ключевая особенность: first_person_id < second_person_id всегда.
    Это каноническая форма — гарантирует что пара (A,B) и (B,A)
    представлены одной записью. Используй фабрику create_spouse_relation().

    Frozen=True — для изменения статуса (развод) обновляем запись
    через репозиторий, возвращая новый объект.
    """

    first_person_id: str  # меньший ID
    second_person_id: str  # больший ID
    marriage_status: MarriageStatus

    marriage_year: int | None = None
    marriage_month: int | None = None
    marriage_day: int | None = None
    marriage_place: str | None = None
    marriage_date_raw: str | None = None

    divorce_year: int | None = None
    divorce_month: int | None = None
    divorce_day: int | None = None
    divorce_date_raw: str | None = None

    def __post_init__(self) -> None:
        self._validate()

    # ── Запросы ──────────────────────────────────────────────────────────────

    def involves(self, person_id: str) -> bool:
        return self.first_person_id == person_id or self.second_person_id == person_id

    def partner_of(self, person_id: str) -> str:
        """Возвращает ID партнёра для данной персоны."""
        if self.first_person_id == person_id:
            return self.second_person_id
        if self.second_person_id == person_id:
            return self.first_person_id
        raise DomainRelationError(
            message="Ошибка",
            errors={"person_id": f"Персона {person_id!r} не участвует в этом браке."},
        )

    def is_active(self) -> bool:
        return self.marriage_status == MarriageStatus.MARRIED

    def marriage_date(self) -> PartialDate | None:
        if self.marriage_year is None and self.marriage_month is None:
            return None
        return PartialDate(
            year=self.marriage_year,
            month=self.marriage_month,
            day=self.marriage_day,
        )

    def divorce_date(self) -> PartialDate | None:
        if self.divorce_year is None:
            return None
        return PartialDate(
            year=self.divorce_year,
            month=self.divorce_month,
            day=self.divorce_day,
        )

    # ── Команды (возвращают новый объект) ────────────────────────────────────

    def divorce(
        self,
        divorce_year: int | None = None,
        divorce_month: int | None = None,
        divorce_day: int | None = None,
        divorce_date_raw: str | None = None,
    ) -> SpouseRelation:
        """Оформить развод — возвращает новую версию с обновлённым статусом."""
        from dataclasses import replace

        return replace(
            self,
            marriage_status=MarriageStatus.DIVORCED,
            divorce_year=divorce_year,
            divorce_month=divorce_month,
            divorce_day=divorce_day,
            divorce_date_raw=divorce_date_raw,
        )

    def mark_widowed(self) -> SpouseRelation:
        """Отметить как вдовца/вдову."""
        from dataclasses import replace

        return replace(self, marriage_status=MarriageStatus.WIDOWED)

    # ── Инварианты ───────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if not self.first_person_id or not self.second_person_id:
            raise DomainRelationError(
                message="Ошибка валидации",
                errors={"ids": "ID супругов не могут быть пустыми."},
            )

        if self.first_person_id == self.second_person_id:
            raise DomainRelationError(
                message="Ошибка валидации",
                errors={"ids": "Человек не может состоять в браке с самим собой."},
            )

        # Каноническая форма: меньший ID первым
        if self.first_person_id > self.second_person_id:
            raise DomainRelationError(
                message="Внутренняя ошибка",
                errors={"ids": "Используйте фабрику create_spouse_relation() для создания."},
            )

        # Развод не раньше свадьбы
        if self.marriage_year is not None and self.divorce_year is not None and self.divorce_year < self.marriage_year:
            raise DomainRelationError(
                message="Ошибка валидации",
                errors={"divorce_year": "Дата развода не может быть раньше даты свадьбы."},
            )

        # Статус DIVORCED требует хотя бы года развода
        if (
            self.marriage_status == MarriageStatus.DIVORCED
            and self.divorce_year is None
            and self.divorce_date_raw is None
        ):
            pass  # допускаем — дата развода может быть неизвестна


def create_spouse_relation(
    person_a_id: str,
    person_b_id: str,
    marriage_status: MarriageStatus = MarriageStatus.MARRIED,
    marriage_year: int | None = None,
    marriage_month: int | None = None,
    marriage_day: int | None = None,
    marriage_place: str | None = None,
    marriage_date_raw: str | None = None,
    divorce_year: int | None = None,
    divorce_month: int | None = None,
    divorce_day: int | None = None,
    divorce_date_raw: str | None = None,
) -> SpouseRelation:
    """
    Фабрика: создаёт SpouseRelation с гарантированной канонической формой.
    Порядок аргументов не важен — фабрика сама определит кто first/second.
    """
    first, second = sorted([person_a_id, person_b_id])
    return SpouseRelation(
        first_person_id=first,
        second_person_id=second,
        marriage_status=marriage_status,
        marriage_year=marriage_year,
        marriage_month=marriage_month,
        marriage_day=marriage_day,
        marriage_place=marriage_place,
        marriage_date_raw=marriage_date_raw,
        divorce_year=divorce_year,
        divorce_month=divorce_month,
        divorce_day=divorce_day,
        divorce_date_raw=divorce_date_raw,
    )
