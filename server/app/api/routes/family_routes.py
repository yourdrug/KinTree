"""
api/routes/family_routes.py

HTTP-роуты для агрегата Family.

Принципы:
- Роутер тонкий: принял запрос → создал команду → вызвал сервис → вернул ответ.
- Никакой бизнес-логики в роутере.
- Зависимости инжектируются через Depends.
- Пагинация и фильтры — через FilterSchema.
"""

from __future__ import annotations

from application.family.commands import CreateFamilyCommand
from application.family.services import FamilyService
from domain.entities.account import Account
from domain.entities.family import Family
from domain.filters.base import BaseFilterSpec
from domain.filters.page import Page
from fastapi import APIRouter, Body, Depends, Path, Request, status

from api.dependencies.auth_dependencies import get_current_account
from api.dependencies.dependencies import get_family_service
from api.schemas.family import (
    CreateFamilyRequest,
    FamilyFilterSchema,
    FamilyPageResponse,
    FamilyResponse,
    PatchFamilyRequest,
    PutFamilyRequest,
)


router: APIRouter = APIRouter(prefix="/families", tags=["Families"])


@router.get(path="/", status_code=status.HTTP_200_OK)
async def get_families_list(
    request: Request,
    filters: FamilyFilterSchema = Depends(),
    service: FamilyService = Depends(get_family_service),
) -> FamilyPageResponse:
    """
    Получить список семей с фильтрацией, сортировкой и пагинацией.

    Query-параметры фильтрации:
    - `name__icontains` — поиск по названию
    - `owner_id` — поиск по точному ID владельца
    - `founded_year__gte` / `founded_year__lte` — диапазон года основания
    - `search` — поиск по имени + описанию
    - `order_by` — сортировка (name | founded_year | creation_date)
    - `order_dir` — направление (asc | desc)
    - `limit` / `offset` — пагинация
    """
    spec: BaseFilterSpec = filters.to_spec()
    page: Page[Family] = await service.get_families_list(spec)
    return FamilyPageResponse.from_page(page=page, request=request)


@router.get(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def get_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    """Получить семью по ID."""
    family: Family = await service.get_family(family_id)
    return FamilyResponse.from_domain(family=family)


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def create_family(
    payload: CreateFamilyRequest = Body(...),
    account: Account = Depends(get_current_account),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    """Создание семьи по введенным данным."""
    command: CreateFamilyCommand = payload.to_command()
    created_family: Family = await service.create_family(command=command, account=account)
    return FamilyResponse.from_domain(family=created_family)


@router.put(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def update_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    payload: PutFamilyRequest = Body(...),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    """
    Перезаписать объект семьи для обновления.
    Если необязательный атрибут не передан, он устанавливается как None.
    """
    command = payload.to_command(family_id=family_id)
    updated_family: Family = await service.update_family(command)
    return FamilyResponse.from_domain(family=updated_family)


@router.patch(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def patch_update_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    payload: PatchFamilyRequest = Body(...),
    service: FamilyService = Depends(get_family_service),
) -> FamilyResponse:
    """
    Частично обновить объект семьи.
    Если атрибут не передан, он не изменяется.
    """
    command = payload.to_command(family_id)
    updated_family: Family = await service.patch_update_family(command)
    return FamilyResponse.from_domain(family=updated_family)


@router.delete(path="/{family_id:str}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    service: FamilyService = Depends(get_family_service),
) -> None:
    """Удалить объект семьи."""
    await service.delete_family(family_id)
