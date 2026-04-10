from application.person.dto import PatchPersonCommand, PutPersonCommand
from application.person.service import PersonService
from domain.entities.person import Person
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
    status,
)

from api.dependencies import get_service
from api.schemas.person import (
    CreatePersonRequest,
    PatchPersonRequest,
    PersonResponse,
    PutPersonRequest,
)


router: APIRouter = APIRouter(prefix="/person", tags=["Persons"])


@router.get(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def get_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_service(PersonService, master=False)),
) -> PersonResponse:
    person: Person = await service.get_person(
        person_id=person_id,
    )

    return PersonResponse.from_domain(person=person)


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: CreatePersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    person: Person = payload.to_domain()

    created_person: Person = await service.create_person(
        person=person,
    )

    return PersonResponse.from_domain(person=created_person)


@router.put(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def update_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    payload: PutPersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    command = PutPersonCommand(
        person_id=person_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        gender=payload.gender,
        birth_date=payload.birth_date.to_domain() if payload.birth_date else None,
        death_date=payload.death_date.to_domain() if payload.death_date else None,
        birth_date_raw=payload.birth_date_raw,
        death_date_raw=payload.death_date_raw,
    )

    updated_person: Person = await service.update_person(
        command=command,
    )

    return PersonResponse.from_domain(person=updated_person)


@router.patch(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def patch_update_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    payload: PatchPersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    command = PatchPersonCommand(
        person_id=person_id,
        update_fields=payload.model_fields_set,
        first_name=payload.first_name,
        last_name=payload.last_name,
        gender=payload.gender,
        birth_date=payload.birth_date.to_domain() if payload.birth_date else None,
        death_date=payload.death_date.to_domain() if payload.death_date else None,
        birth_date_raw=payload.birth_date_raw,
        death_date_raw=payload.death_date_raw,
    )

    updated_person = await service.patch_update_person(command)

    return PersonResponse.from_domain(person=updated_person)


@router.delete(path="/{person_id:str}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> None:
    await service.delete_person(person_id=person_id)
    return None
