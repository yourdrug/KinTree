"""
API Schemas — Pydantic-модели для HTTP-слоя.

Ключевой принцип:
  - CreatePersonRequest  — НЕТ поля id (клиент не задаёт его)
  - UpdatePersonRequest  — все поля Optional (PATCH-семантика)
  - PersonResponse       — всегда содержит id (отдаём клиенту)

Маппинг domain <-> schema живёт здесь же, рядом со схемами,
чтобы не размазывать логику преобразования по всему коду.
"""

from __future__ import annotations

from typing import Any

from application.person.dto import PatchPersonCommand, PersonListQuery, PutPersonCommand
from domain.entities.person import Person, create_person
from domain.enums import PersonGender
from domain.exceptions import DomainPersonError
from domain.repositories.person import PersonPage, PersonSort, PersonSortField
from domain.value_objects.partial_date import PartialDate
from domain.value_objects.unset import UNSET
from pydantic import BaseModel, Field, field_validator, model_validator


class PartialDateSchema(BaseModel):
    year: int | None = Field(None, ge=1, le=9999, examples=[1990])
    month: int | None = Field(None, ge=1, le=12, examples=[6])
    day: int | None = Field(None, ge=1, le=31, examples=[15])

    def to_domain(self) -> PartialDate:
        return PartialDate(year=self.year, month=self.month, day=self.day)

    @classmethod
    def from_domain(cls, date: PartialDate) -> PartialDateSchema:
        return cls(year=date.year, month=date.month, day=date.day)


class CreatePersonRequest(BaseModel):
    """Запрос на создание Person. ID генерируется сервером."""

    gender: PersonGender = Field(..., examples=[PersonGender.MALE])
    family_id: str = Field(..., min_length=1, examples=["98ce28f633d7546b51c8c2cff566d342"])

    first_name: str | None = Field(..., min_length=1, max_length=100, examples=["Иван"])
    last_name: str | None = Field(..., min_length=1, max_length=100, examples=["Иванов"])

    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = Field(None, examples=["около 1990"])
    death_date_raw: str | None = None

    def to_domain(self) -> Person:
        """Создаёт доменный объект с новым UUID."""
        return create_person(
            first_name=self.first_name,
            last_name=self.last_name,
            gender=self.gender,
            family_id=self.family_id,
            birth_date=self.birth_date.to_domain() if self.birth_date else None,
            death_date=self.death_date.to_domain() if self.death_date else None,
            birth_date_raw=self.birth_date_raw,
            death_date_raw=self.death_date_raw,
        )


class PutPersonRequest(BaseModel):
    """
    PUT-семантика: клиент передаёт полное представление ресурса.
    Все поля обязательны — отсутствующее поле означает сброс в None.
    """

    gender: PersonGender

    first_name: str | None = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(..., min_length=1, max_length=100)

    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    def to_command(self, person_id: str) -> PutPersonCommand:
        """
        Конвертирует схему в команду PutPersonCommand
        """

        return PutPersonCommand(
            person_id=person_id,
            first_name=self.first_name,
            last_name=self.last_name,
            gender=self.gender,
            birth_date=self.birth_date.to_domain() if self.birth_date else None,
            death_date=self.death_date.to_domain() if self.death_date else None,
            birth_date_raw=self.birth_date_raw,
            death_date_raw=self.death_date_raw,
        )


class PatchPersonRequest(BaseModel):
    """
    PATCH-семантика: клиент передаёт только изменяемые поля.
    """

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    gender: PersonGender | None = None

    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_non_nullable_fields(cls, data: Any) -> Any:
        """
        Проверяет поля которые необязательны, но не могут быть null если переданы.
        Один валидатор на все такие поля — никаких дублей.
        """
        non_nullable = ["gender"]

        errors = {}
        for field in non_nullable:
            if field in data and data[field] is None:
                errors[field] = "Не может быть null"

        if errors:
            raise DomainPersonError(message="Ошибка валидации", errors=errors)

        return data

    def to_command(self, person_id: str) -> PatchPersonCommand:
        """
        Конвертирует запрос в команду, подставляя UNSET для непереданных полей.
        model_fields_set содержит только те поля, которые клиент передал явно.
        """
        sent = self.model_fields_set

        return PatchPersonCommand(
            person_id=person_id,
            first_name=self.first_name if "first_name" in sent else UNSET,
            last_name=self.last_name if "last_name" in sent else UNSET,
            gender=self.gender if "gender" in sent else UNSET,  # type: ignore
            birth_date=(self.birth_date.to_domain() if self.birth_date else None) if "birth_date" in sent else UNSET,
            death_date=(self.death_date.to_domain() if self.death_date else None) if "death_date" in sent else UNSET,
            birth_date_raw=self.birth_date_raw if "birth_date_raw" in sent else UNSET,
            death_date_raw=self.death_date_raw if "death_date_raw" in sent else UNSET,
        )


class PersonResponse(BaseModel):
    """Полное представление Person для клиента. Всегда содержит id."""

    id: str
    full_name: str
    gender: PersonGender
    family_id: str
    is_alive: bool

    first_name: str | None
    last_name: str | None

    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_domain(cls, person: Person) -> PersonResponse:
        """Единственная точка конвертации domain -> response schema."""
        return cls(
            id=person.id,
            first_name=person.first_name,
            last_name=person.last_name,
            full_name=person.full_name(),
            gender=person.gender,
            family_id=person.family_id,
            is_alive=person.is_alive(),
            birth_date=(PartialDateSchema.from_domain(person.birth_date) if person.birth_date else None),
            death_date=(PartialDateSchema.from_domain(person.death_date) if person.death_date else None),
            birth_date_raw=person.birth_date_raw,
            death_date_raw=person.death_date_raw,
        )


class PersonListRequest(BaseModel):
    family_id: str | None = None
    gender: PersonGender | None = None
    first_name: str | None = None
    last_name: str | None = None
    sort_by: str = "last_name"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        raw = v.lstrip("-")
        allowed = {f.value for f in PersonSortField}
        if raw not in allowed:
            raise ValueError(
                f"Недопустимое поле сортировки: '{raw}'. Допустимые значения: {', '.join(sorted(allowed))}"
            )
        return v

    def to_query(self) -> PersonListQuery:
        return PersonListQuery(
            family_id=self.family_id,
            gender=self.gender,
            first_name=self.first_name,
            last_name=self.last_name,
            sort=PersonSort.from_string(self.sort_by),
            limit=self.limit,
            offset=self.offset,
        )


class PersonPageResponse(BaseModel):
    result: list[PersonResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool

    @classmethod
    def from_domain(cls, page: PersonPage) -> PersonPageResponse:
        return cls(
            result=[PersonResponse.from_domain(p) for p in page.result],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
            has_next=page.has_next,
            has_prev=page.has_prev,
        )
