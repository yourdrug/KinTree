from fastapi import (
    APIRouter,
    Depends,
    Path,
    status, Body,
)

from domain.models.person import Person
from domain.schemas.person import PersonSchema, CreatePersonSchema, PersonIdSchema
from application.services.person_service import PersonService
from infrastructure.common.dependencies import get_service


router: APIRouter = APIRouter(prefix="/person", tags=["Persons"])


@router.get(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def get_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_service(PersonService, master=False)),
) -> PersonSchema:

    person: Person = await service.get_person(
        person_id=person_id,
    )

    return PersonSchema.model_validate(person)


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def create_person(
    person: CreatePersonSchema = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonIdSchema:
    person_data: dict = person.model_dump()

    person_id: str = await service.create_person(
        person_data=person_data,
    )

    return PersonIdSchema(id=person_id)
