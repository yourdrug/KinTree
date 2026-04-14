from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated

from application.person.dto import PatchPersonCommand, PutPersonCommand
from domain.entities.person import Person, create_person
from domain.enums import PersonGender
from domain.exceptions import FilterError
from domain.filters.base import SortDirection, SortField
from domain.filters.specs import PersonFilterSpec
from domain.repositories.person import PersonPage
from domain.value_objects.partial_date import PartialDate
from domain.value_objects.unset import UNSET
from fastapi import Query, Request
from pydantic import BaseModel, Field

from api.schemas.base import BasePageMeta, BasePaginationParams, BasePatchSchema


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


class PatchPersonRequest(BasePatchSchema):
    """
    PATCH-семантика: клиент передаёт только изменяемые поля.
    """

    non_nullable = ["gender"]

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    gender: PersonGender | None = None

    birth_date: PartialDateSchema | None = None
    death_date: PartialDateSchema | None = None
    birth_date_raw: str | None = None
    death_date_raw: str | None = None

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


class PersonPageResponse(BasePageMeta):
    """
    Ответ со списком персон.

    Наследует BasePageMeta (total, limit, offset, has_next, has_prev, urls).
    Добавляет result: list[PersonResponse].

    from_domain() принимает PersonPage.
    """

    result: list[PersonResponse]

    @classmethod
    def from_domain(cls, page: PersonPage, request: Request) -> PersonPageResponse:
        meta = cls._build_meta(
            total=page.total,
            limit=page.limit,
            offset=page.offset,
            base_url=str(request.url.replace(query="")),
            query_params=request.query_params,
        )
        return cls(
            result=[PersonResponse.from_domain(p) for p in page.result],
            **meta,
        )


@dataclass
class PersonFilterSchema(BasePaginationParams):
    """
    Query-параметры фильтрации для Person.

    Использование в роутере:
        filters: PersonFilterSchema = Depends()

    Доступные параметры:
        first_name__icontains  — ILIKE '%value%' по имени
        last_name__icontains   — ILIKE '%value%' по фамилии
        gender                 — точное совпадение (MALE | FEMALE | UNKNOWN)
        gender__in             — несколько значений через запятую (MALE,FEMALE)
        family_id              — точный ID семьи
        birth_year__gte        — год рождения >=
        birth_year__lte        — год рождения <=
        death_year__gte        — год смерти >=
        death_year__lte        — год смерти <=
        is_alive               — true = только живые (death_year IS NULL)
        search                 — ILIKE по first_name + last_name
        order_by               — last_name | birth_year | creation_date
        order_dir              — asc | desc
    """

    # -- Имя --
    first_name__icontains: Annotated[
        str | None,
        Query(alias="first_name__icontains", min_length=1, max_length=100),
    ] = None

    last_name__icontains: Annotated[
        str | None,
        Query(alias="last_name__icontains", min_length=1, max_length=100),
    ] = None

    # -- Гендер --
    gender: Annotated[PersonGender | None, Query()] = None

    # Список через запятую: «MALE,FEMALE» — принимаем строкой, парсим в __post_init__
    gender__in: Annotated[
        str | None,
        Query(alias="gender__in", description="Значения через запятую: MALE,FEMALE"),
    ] = None

    # -- Семья --
    family_id: Annotated[str | None, Query(min_length=32, max_length=32)] = None

    # -- Год рождения --
    birth_year__gte: Annotated[int | None, Query(alias="birth_year__gte", ge=1, le=9999)] = None
    birth_year__lte: Annotated[int | None, Query(alias="birth_year__lte", ge=1, le=9999)] = None

    # -- Год смерти --
    death_year__gte: Annotated[int | None, Query(alias="death_year__gte", ge=1, le=9999)] = None
    death_year__lte: Annotated[int | None, Query(alias="death_year__lte", ge=1, le=9999)] = None

    # -- Специальные --
    is_alive: Annotated[bool | None, Query()] = None
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None

    # -- Сортировка --
    order_by: Annotated[
        str | None,
        Query(pattern=r"^(last_name|birth_year|creation_date)$"),
    ] = None
    order_dir: Annotated[SortDirection, Query()] = SortDirection.ASC

    # Распаршенный gender__in (заполняется в __post_init__)
    _gender_in_parsed: list[PersonGender] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._validate_year_range("birth_year__gte", self.birth_year__gte, "birth_year__lte", self.birth_year__lte)
        self._validate_year_range("death_year__gte", self.death_year__gte, "death_year__lte", self.death_year__lte)
        self._gender_in_parsed = _parse_enum_list(self.gender__in, PersonGender, "gender__in")

    @staticmethod
    def _validate_year_range(
        gte_name: str,
        gte_val: int | None,
        lte_name: str,
        lte_val: int | None,
    ) -> None:
        if gte_val is not None and lte_val is not None and gte_val > lte_val:
            raise FilterError(
                message="Ошибка валидации",
                errors={f"{gte_name}": f"{gte_name} не может быть больше {lte_name}"},
            )

    def to_spec(self) -> PersonFilterSpec:
        """
        Конвертирует query-параметры в доменную спецификацию.
        Добавляет только явно переданные условия.
        """
        filters = []
        sort = []

        if self.first_name__icontains:
            filters.append(PersonFilterSpec.by_first_name(self.first_name__icontains))

        if self.last_name__icontains:
            filters.append(PersonFilterSpec.by_last_name(self.last_name__icontains))

        if self.gender is not None:
            filters.append(PersonFilterSpec.by_gender(self.gender))

        if self._gender_in_parsed:
            filters.append(PersonFilterSpec.by_gender_in(self._gender_in_parsed))

        if self.family_id:
            filters.append(PersonFilterSpec.by_family_id(self.family_id))

        if self.birth_year__gte is not None:
            filters.append(PersonFilterSpec.birth_year_gte(self.birth_year__gte))

        if self.birth_year__lte is not None:
            filters.append(PersonFilterSpec.birth_year_lte(self.birth_year__lte))

        if self.death_year__gte is not None:
            filters.append(PersonFilterSpec.death_year_gte(self.death_year__gte))

        if self.death_year__lte is not None:
            filters.append(PersonFilterSpec.death_year_lte(self.death_year__lte))

        if self.is_alive is True:
            filters.append(PersonFilterSpec.is_alive())

        if self.search:
            filters.append(PersonFilterSpec.search(self.search))

        if self.order_by:
            sort.append(SortField(self.order_by, self.order_dir))

        return PersonFilterSpec(
            filters=tuple(filters),
            sort=tuple(sort),
            limit=self.limit,
            offset=self.offset,
        )


class PartialDateSchema(BaseModel):
    year: int | None = Field(None, ge=1, le=9999, examples=[1990])
    month: int | None = Field(None, ge=1, le=12, examples=[6])
    day: int | None = Field(None, ge=1, le=31, examples=[15])

    def to_domain(self) -> PartialDate:
        return PartialDate(year=self.year, month=self.month, day=self.day)

    @classmethod
    def from_domain(cls, date: PartialDate) -> PartialDateSchema:
        return cls(year=date.year, month=date.month, day=date.day)


def _parse_enum_list(
    raw: str | None,
    enum_cls: type[Enum],
    param_name: str,
) -> list | None:
    """
    Парсит строку «VAL1,VAL2» в список enum-значений.

    FastAPI не умеет нативно принимать list[Enum] через Query как одну строку
    с разделителем-запятой, поэтому принимаем str и парсим вручную.

    Raises:
        FilterError — если хотя бы одно значение не входит в enum.
    """
    if raw is None:
        return None

    result = []
    valid = {e.value for e in enum_cls}

    for part in raw.split(","):
        value = part.strip()
        if value not in valid:
            raise FilterError(
                message="Ошибка валидации",
                errors={param_name: f"Недопустимое значение «{value}». Допустимы: {sorted(valid)}"},
            )
        result.append(enum_cls(value))

    return result or None
