from application.family.services import FamilyService
from domain.entities.family import Family
from fastapi import APIRouter, Body, Depends, Path, status

from api.dependencies import get_service
from api.schemas.family import CreateFamilyRequest, FamilyResponse, PatchFamilyRequest, PutFamilyRequest


router: APIRouter = APIRouter(prefix="/families", tags=["Families"])


# @router.get(path="/", status_code=status.HTTP_200_OK)
# async def get_persons_list(
#     query: PersonListRequest = Depends(),  # Depends() для query-параметров
#     service: PersonService = Depends(get_service(PersonService, master=False)),
# ) -> PersonPageResponse:
#     page = await service.get_persons_list(query=query.to_query())
#     return PersonPageResponse.from_domain(page)


@router.get(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def get_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    service: FamilyService = Depends(get_service(FamilyService, master=False)),
) -> FamilyResponse:
    family: Family = await service.get_family(family_id=family_id)

    return FamilyResponse.from_domain(family=family)


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def create_family(
    payload: CreateFamilyRequest = Body(...),
    service: FamilyService = Depends(get_service(FamilyService, master=True)),
) -> FamilyResponse:
    family: Family = payload.to_domain()

    created_family: Family = await service.create_family(family=family)

    return FamilyResponse.from_domain(family=created_family)


@router.put(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def update_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    payload: PutFamilyRequest = Body(...),
    service: FamilyService = Depends(get_service(FamilyService, master=True)),
) -> FamilyResponse:
    command = payload.to_command(family_id=family_id)

    updated_family: Family = await service.update_family(command=command)

    return FamilyResponse.from_domain(family=updated_family)


@router.patch(path="/{family_id:str}", status_code=status.HTTP_200_OK)
async def patch_update_family(
    family_id: str = Path(..., min_length=32, max_length=32),
    payload: PatchFamilyRequest = Body(...),
    service: FamilyService = Depends(get_service(FamilyService, master=True)),
) -> FamilyResponse:
    command = payload.to_command(family_id)
    updated_family = await service.patch_update_family(command)

    return FamilyResponse.from_domain(family=updated_family)


@router.delete(path="/{family_id:str}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    family_id: str = Path(..., min_length=32, max_length=32),
    service: FamilyService = Depends(get_service(FamilyService, master=True)),
) -> None:
    await service.delete_family(family_id=family_id)

    return None
