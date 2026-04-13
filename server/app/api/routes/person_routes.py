from application.person.service import PersonService
from domain.entities.person import Person
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
    Query,
    Request,
    status,
)
from fastapi_filter import FilterDepends
from infrastructure.person.filters import PersonFilter

from api.dependencies import get_service
from api.schemas.base import BasePageResponse
from api.schemas.person import (
    CreatePersonRequest,
    PatchPersonRequest,
    PersonPageResponse,
    PersonResponse,
    PutPersonRequest,
)


router: APIRouter = APIRouter(prefix="/person", tags=["Persons"])


@router.get(path="/", status_code=status.HTTP_200_OK)
async def get_persons_list(
    request: Request,
    person_filter: PersonFilter = FilterDepends(PersonFilter),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: PersonService = Depends(get_service(PersonService, master=False)),
) -> BasePageResponse[PersonResponse]:
    page = await service.get_persons_list(filters=person_filter, limit=limit, offset=offset)
    return PersonPageResponse.from_domain(page=page, request=request)


@router.get(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def get_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_service(PersonService, master=False)),
) -> PersonResponse:
    person: Person = await service.get_person(person_id=person_id)

    return PersonResponse.from_domain(person=person)


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: CreatePersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    person: Person = payload.to_domain()

    created_person: Person = await service.create_person(person=person)

    return PersonResponse.from_domain(person=created_person)


@router.put(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def update_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    payload: PutPersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    command = payload.to_command(person_id=person_id)

    updated_person: Person = await service.update_person(command=command)

    return PersonResponse.from_domain(person=updated_person)


@router.patch(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def patch_update_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    payload: PatchPersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    command = payload.to_command(person_id)
    updated_person = await service.patch_update_person(command)

    return PersonResponse.from_domain(person=updated_person)


@router.delete(path="/{person_id:str}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> None:
    await service.delete_person(person_id=person_id)

    return None
