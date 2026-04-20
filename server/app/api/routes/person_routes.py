"""
api/routes/person_routes.py

HTTP-роуты для агрегата Person.

Принципы:
- Роутер тонкий: принял запрос → создал команду → вызвал сервис → вернул ответ.
- Никакой бизнес-логики в роутере.
- Зависимости инжектируются через Depends.
- Пагинация и фильтры — через FilterSchema.
"""

from __future__ import annotations

from application.person.service import PersonService
from fastapi import APIRouter, Body, Depends, Path, Request, status

from api.dependencies.dependencies import get_person_service
from api.schemas.person import (
    CreatePersonRequest,
    PatchPersonRequest,
    PersonFilterSchema,
    PersonPageResponse,
    PersonResponse,
    UpdatePersonRequest,
)


router = APIRouter(prefix="/persons", tags=["Persons"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=PersonPageResponse)
async def list_persons(
    request: Request,
    filters: PersonFilterSchema = Depends(),
    service: PersonService = Depends(get_person_service),
) -> PersonPageResponse:
    """Список персон с фильтрацией, сортировкой и пагинацией."""
    page = await service.list_persons(filters.to_spec())
    return PersonPageResponse.from_page(page=page, request=request)


@router.get("/{person_id}", status_code=status.HTTP_200_OK, response_model=PersonResponse)
async def get_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_person_service),
) -> PersonResponse:
    """Получить персону по ID."""
    person = await service.get_person(person_id=person_id)
    return PersonResponse.from_domain(person)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PersonResponse)
async def create_person(
    payload: CreatePersonRequest = Body(...),
    service: PersonService = Depends(get_person_service),
) -> PersonResponse:
    """Создать нового члена семьи."""
    person = await service.create_person(payload.to_command())
    return PersonResponse.from_domain(person)


@router.put("/{person_id}", status_code=status.HTTP_200_OK, response_model=PersonResponse)
async def update_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    payload: UpdatePersonRequest = Body(...),
    service: PersonService = Depends(get_person_service),
) -> PersonResponse:
    """Полное обновление персоны (PUT-семантика)."""
    person = await service.update_person(payload.to_command(person_id))
    return PersonResponse.from_domain(person)


@router.patch("/{person_id}", status_code=status.HTTP_200_OK, response_model=PersonResponse)
async def patch_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    payload: PatchPersonRequest = Body(...),
    service: PersonService = Depends(get_person_service),
) -> PersonResponse:
    """Частичное обновление персоны (PATCH-семантика)."""
    person = await service.patch_person(payload.to_command(person_id))
    return PersonResponse.from_domain(person)


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_person_service),
) -> None:
    """Удалить персону по ID."""
    await service.delete_person(person_id=person_id)
