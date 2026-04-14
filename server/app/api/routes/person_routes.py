from application.person.service import PersonService
from domain.entities.person import Person
from domain.filters.base import BaseFilterSpec
from domain.filters.page import PersonPage
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
    Request,
    status,
)

from application.dependencies import get_service
from api.schemas.person import (
    CreatePersonRequest,
    PatchPersonRequest,
    PersonFilterSchema,
    PersonPageResponse,
    PersonResponse,
    PutPersonRequest,
)


router: APIRouter = APIRouter(prefix="/person", tags=["Persons"])


@router.get(path="/", status_code=status.HTTP_200_OK)
async def get_persons_list(
    request: Request,
    filters: PersonFilterSchema = Depends(),
    service: PersonService = Depends(get_service(PersonService, master=False)),
) -> PersonPageResponse:
    """
    Получить список персон с фильтрацией, сортировкой и пагинацией.

    Query-параметры фильтрации:
    - `first_name__icontains` — поиск по имени
    - `last_name__icontains` — поиск по фамилии
    - `gender` — точное совпадение (MALE | FEMALE | UNKNOWN)
    - `gender__in` — несколько значений гендера через запятую
    - `family_id` — фильтр по семье
    - `birth_year__gte` / `birth_year__lte` — диапазон года рождения
    - `death_year__gte` / `death_year__lte` — диапазон года смерти
    - `is_alive` — только живые
    - `search` — поиск по имени + фамилии
    - `order_by` — сортировка (last_name | birth_year | creation_date)
    - `order_dir` — направление (asc | desc)
    - `limit` / `offset` — пагинация
    """

    spec: BaseFilterSpec = filters.to_spec()
    page: PersonPage = await service.get_persons_list(filters=spec)
    return PersonPageResponse.from_domain(page=page, request=request)


@router.get(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def get_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_service(PersonService, master=False)),
) -> PersonResponse:
    """
    Получить члена семьи по ID
    """

    person: Person = await service.get_person(person_id=person_id)
    return PersonResponse.from_domain(person=person)


@router.post(path="/", status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: CreatePersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    """
    Создать члена семьи по введенным данным
    """

    person: Person = payload.to_domain()
    created_person: Person = await service.create_person(person=person)
    return PersonResponse.from_domain(person=created_person)


@router.put(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def update_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    payload: PutPersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    """
    Перезаписать объект члена семьи для обновления.
    Если необязательный атрибут не передан, он устанавливается как None
    """

    command = payload.to_command(person_id=person_id)
    updated_person: Person = await service.update_person(command=command)
    return PersonResponse.from_domain(person=updated_person)


@router.patch(path="/{person_id:str}", status_code=status.HTTP_200_OK)
async def patch_update_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    payload: PatchPersonRequest = Body(...),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> PersonResponse:
    """
    Частично обновить объект члена семьи.
    Если атрибут не передан, он не изменяется.
    """

    command = payload.to_command(person_id)
    updated_person = await service.patch_update_person(command)
    return PersonResponse.from_domain(person=updated_person)


@router.delete(path="/{person_id:str}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: PersonService = Depends(get_service(PersonService, master=True)),
) -> None:
    """
    Удалить члена семьи по ID
    """

    await service.delete_person(person_id=person_id)
    return None
