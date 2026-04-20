from __future__ import annotations

from application.relations.service import RelationService
from domain.entities.parent_child import ParentChildRelation
from domain.entities.spouse import SpouseRelation
from fastapi import APIRouter, Body, Depends, Path, status

from api.dependencies.dependencies import get_relation_service
from api.schemas.relations import (
    AddParentChildRequest,
    AddSpouseRequest,
    DivorceRequest,
    FamilyGraphResponse,
    ParentChildResponse,
    SpouseResponse,
)


router: APIRouter = APIRouter(prefix="/relations", tags=["Relations"])


# ── ParentChild ───────────────────────────────────────────────────────────────


@router.post(
    "/parent-child",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить связь родитель–ребёнок",
)
async def add_parent_child(
    payload: AddParentChildRequest = Body(...),
    service: RelationService = Depends(get_relation_service),
) -> ParentChildResponse:
    """
    Создаёт связь между двумя персонами: родитель → ребёнок.

    Проверки:
    - Обе персоны должны существовать
    - Связь не должна уже существовать
    - Не более 2 биологических родителей у одного ребёнка
    - Нельзя быть одновременно родителем и супругом
    """
    relation: ParentChildRelation = await service.add_parent_child(payload.to_command())
    return ParentChildResponse(
        parent_id=relation.parent_id,
        child_id=relation.child_id,
        relation_type=relation.relation_type,
    )


@router.delete(
    "/parent-child/{parent_id}/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить связь родитель–ребёнок",
)
async def remove_parent_child(
    parent_id: str = Path(..., min_length=32, max_length=32),
    child_id: str = Path(..., min_length=32, max_length=32),
    service: RelationService = Depends(get_relation_service),
) -> None:
    await service.remove_parent_child(parent_id=parent_id, child_id=child_id)


# ── Spouse ────────────────────────────────────────────────────────────────────


@router.post(
    "/spouses",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить супружескую связь",
)
async def add_spouse(
    payload: AddSpouseRequest = Body(...),
    service: RelationService = Depends(get_relation_service),
) -> SpouseResponse:
    """
    Создаёт супружескую связь между двумя персонами.

    Проверки:
    - Обе персоны должны существовать
    - Пара не должна уже быть в браке
    - Нельзя быть одновременно родителем и супругом
    """
    relation: SpouseRelation = await service.add_spouse(payload.to_command())
    return SpouseResponse(
        first_person_id=relation.first_person_id,
        second_person_id=relation.second_person_id,
        marriage_status=relation.marriage_status,
        marriage_year=relation.marriage_year,
        marriage_month=relation.marriage_month,
        marriage_day=relation.marriage_day,
        marriage_place=relation.marriage_place,
        marriage_date_raw=relation.marriage_date_raw,
    )


@router.post(
    "/spouses/divorce",
    status_code=status.HTTP_200_OK,
    summary="Оформить развод",
)
async def divorce(
    payload: DivorceRequest = Body(...),
    service: RelationService = Depends(get_relation_service),
) -> SpouseResponse:
    """Обновляет статус брака на DIVORCED, сохраняет дату развода."""
    relation: SpouseRelation = await service.divorce(payload.to_command())
    return SpouseResponse(
        first_person_id=relation.first_person_id,
        second_person_id=relation.second_person_id,
        marriage_status=relation.marriage_status,
        marriage_year=relation.marriage_year,
        marriage_month=relation.marriage_month,
        marriage_day=relation.marriage_day,
        marriage_place=relation.marriage_place,
        marriage_date_raw=relation.marriage_date_raw,
        divorce_year=relation.divorce_year,
        divorce_month=relation.divorce_month,
        divorce_day=relation.divorce_day,
        divorce_date_raw=relation.divorce_date_raw,
    )


@router.delete(
    "/spouses/{person_a_id}/{person_b_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить запись о браке",
)
async def remove_spouse(
    person_a_id: str = Path(..., min_length=32, max_length=32),
    person_b_id: str = Path(..., min_length=32, max_length=32),
    service: RelationService = Depends(get_relation_service),
) -> None:
    await service.remove_spouse(person_a_id=person_a_id, person_b_id=person_b_id)


# ── Graph ─────────────────────────────────────────────────────────────────────


@router.get(
    "/graph/{family_id}",
    status_code=status.HTTP_200_OK,
    summary="Граф семьи",
)
async def get_family_graph(
    family_id: str = Path(..., min_length=32, max_length=32),
    service: RelationService = Depends(get_relation_service),
) -> FamilyGraphResponse:
    """
    Возвращает граф семьи: узлы (персоны) + рёбра (связи).

    3 запроса к БД на весь граф:
    - Все персоны семьи
    - Все родительские связи
    - Все супружеские связи

    Формат совместим с React Flow, D3.js, Cytoscape.js, vis.js.
    """
    result = await service.get_family_graph(family_id=family_id)
    return FamilyGraphResponse.from_result(result)
