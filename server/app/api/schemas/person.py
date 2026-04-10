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

from domain.entities.person import Person, create_person
from domain.enums import PersonGender
from domain.value_objects.partial_date import PartialDate
from pydantic import BaseModel, Field


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

    first_name: str = Field(..., min_length=1, max_length=100, examples=["Иван"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Иванов"])
    gender: PersonGender = Field(..., examples=[PersonGender.MALE])
    family_id: str = Field(..., min_length=1, examples=["family-123"])

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

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    gender: PersonGender

    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None


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


class PersonResponse(BaseModel):
    """Полное представление Person для клиента. Всегда содержит id."""

    id: str
    first_name: str
    last_name: str
    full_name: str
    gender: PersonGender
    family_id: str
    is_alive: bool

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
