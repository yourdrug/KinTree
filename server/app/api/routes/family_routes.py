from application.dependencies import get_service
from application.family.services import FamilyService
from domain.entities.family import Family
from domain.filters.base import BaseFilterSpec
from domain.filters.page import FamilyPage
from fastapi import APIRouter, Body, Depends, Path, Request, status

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
    service: FamilyService = Depends(get_service(FamilyService, master=False)),
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
    page: FamilyPage = await service.get_families_list(filters=spec)
    return FamilyPageResponse.from_domain(page=page, request=request)


@router.get(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def get_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    service: FamilyService = Depends(get_service(FamilyService, master=False)),
) -> FamilyResponse:
    """
    Получить семью по ID
    """

    family: Family = await service.get_family(family_id=family_id)
    return FamilyResponse.from_domain(family=family)


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def create_family(
    payload: CreateFamilyRequest = Body(...),
    service: FamilyService = Depends(get_service(FamilyService, master=True)),
) -> FamilyResponse:
    """
    Создание семьи по введенным данным.
    """

    family: Family = payload.to_domain()
    created_family: Family = await service.create_family(family=family)
    return FamilyResponse.from_domain(family=created_family)


@router.put(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def update_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    payload: PutFamilyRequest = Body(...),
    service: FamilyService = Depends(get_service(FamilyService, master=True)),
) -> FamilyResponse:
    """
    Перезаписать объект семьи для обновления.
    Если необязательный атрибут не передан, он устанавливается как None
    """

    command = payload.to_command(family_id=family_id)
    updated_family: Family = await service.update_family(command=command)
    return FamilyResponse.from_domain(family=updated_family)


@router.patch(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def patch_update_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    payload: PatchFamilyRequest = Body(...),
    service: FamilyService = Depends(get_service(FamilyService, master=True)),
) -> FamilyResponse:
    """
    Частично обновить объект семьи.
    Если атрибут не передан, он не изменяется.
    """

    command = payload.to_command(family_id)
    updated_family = await service.patch_update_family(command)
    return FamilyResponse.from_domain(family=updated_family)


@router.delete(path="/{family_id:str}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    service: FamilyService = Depends(get_service(FamilyService, master=True)),
) -> None:
    """
    Удалить объект семьи
    """

    await service.delete_family(family_id=family_id)
    return None
