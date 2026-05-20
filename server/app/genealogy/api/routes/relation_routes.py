"""
genealogy/api/routes/relation_routes.py
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Path, status
from presentation.rest.dependencies.auth import get_current_account_id
from presentation.rest.dependencies.services import get_relation_service

from genealogy.api.schemas.relations import (
    AddParentChildRequest,
    AddSpouseRequest,
    DivorceRequest,
    FamilyGraphResponse,
    ParentChildResponse,
    SiblingResponse,
    SpouseResponse,
)
from genealogy.application.relations.commands import FamilyGraphResult
from genealogy.application.relations.service import RelationService
from genealogy.domain.entities.parent_child import ParentChildRelation
from genealogy.domain.entities.sibling import SiblingRelation
from genealogy.domain.entities.spouse import SpouseRelation


router = APIRouter(prefix="/relations", tags=["Relations"])


@router.post(
    path="/parent-child",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить связь родитель–ребёнок",
    response_description="Созданная связь",
)
async def add_parent_child(
    payload: AddParentChildRequest = Body(...),
    _account_id: str = Depends(get_current_account_id),
    service: RelationService = Depends(get_relation_service),
) -> ParentChildResponse:
    relation: ParentChildRelation = await service.add_parent_child(payload.to_command())
    return ParentChildResponse(
        parent_id=relation.parent_id,
        child_id=relation.child_id,
        relation_type=relation.relation_type,
    )


@router.delete(
    path="/parent-child/{parent_id}/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить связь родитель–ребёнок",
)
async def remove_parent_child(
    parent_id: str = Path(..., min_length=32, max_length=32),
    child_id: str = Path(..., min_length=32, max_length=32),
    _account_id: str = Depends(get_current_account_id),
    service: RelationService = Depends(get_relation_service),
) -> None:
    await service.remove_parent_child(parent_id, child_id)


# ── Spouse ────────────────────────────────────────────────────────────────────


@router.post(
    path="/spouse",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить супружескую связь",
)
async def add_spouse(
    payload: AddSpouseRequest = Body(...),
    _account_id: str = Depends(get_current_account_id),
    service: RelationService = Depends(get_relation_service),
) -> SpouseResponse:
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
        divorce_year=relation.divorce_year,
        divorce_month=relation.divorce_month,
        divorce_day=relation.divorce_day,
        divorce_date_raw=relation.divorce_date_raw,
    )


@router.post(
    path="/divorce",
    status_code=status.HTTP_200_OK,
    summary="Оформить развод",
)
async def divorce(
    payload: DivorceRequest = Body(...),
    _account_id: str = Depends(get_current_account_id),
    service: RelationService = Depends(get_relation_service),
) -> SpouseResponse:
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
    path="/spouse/{person_a_id}/{person_b_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить супружескую связь",
)
async def remove_spouse(
    person_a_id: str = Path(..., min_length=32, max_length=32),
    person_b_id: str = Path(..., min_length=32, max_length=32),
    _account_id: str = Depends(get_current_account_id),
    service: RelationService = Depends(get_relation_service),
) -> None:
    await service.remove_spouse(person_a_id, person_b_id)


@router.get(
    path="/siblings/{person_id}",
    status_code=status.HTTP_200_OK,
    summary="Получить братьев и сестёр персоны",
    response_description=(
        "Список сиблинговых связей, отсортированных FULL → HALF → STEP. "
        "Сиблинги — производная связь, вычисляемая из parent_child. "
        "Не хранится в БД отдельно."
    ),
)
async def get_siblings(
    person_id: str = Path(..., min_length=32, max_length=32),
    service: RelationService = Depends(get_relation_service),
) -> list[SiblingResponse]:
    """
    Возвращает братьев и сестёр персоны с их типом:

    - **FULL** — оба биологических родителя общие
    - **HALF** — один общий биологический родитель
    - **STEP** — общий только приёмный / неродной родитель

    Поле `shared_parent_ids` содержит ID общих родителей —
    клиент может использовать их для tooltip-подсказок на UI.

    Доступен без авторизации (публичные данные семейного дерева).
    """
    siblings: list[SiblingRelation] = await service.get_siblings_of(person_id)
    return [SiblingResponse.from_domain(rel) for rel in siblings]


@router.get(
    path="/family-graph/{family_id}",
    status_code=status.HTTP_200_OK,
    summary="Граф семьи (узлы + рёбра)",
    response_description=(
        "Структура для рендеринга дерева: nodes + edges. Рёбра трёх типов: parent_child, spouse, sibling."
    ),
)
async def get_family_graph(
    family_id: str = Path(..., min_length=32, max_length=32),
    service: RelationService = Depends(get_relation_service),
) -> FamilyGraphResponse:
    """
    Возвращает граф семьи для отрисовки на клиенте.

    **Узлы** (`nodes`) — персоны с базовыми полями для рендеринга карточки.

    **Рёбра** (`edges`) — связи трёх типов:

    | type | Поля | Рендеринг |
    |------|------|-----------|
    | `parent_child` | `relation_type` | Вертикальная линия поколений |
    | `spouse` | `marriage_status`, `marriage_year`, `divorce_year` | Горизонтальная линия пары |
    | `sibling` | `sibling_type`, `shared_parent_ids` | Горизонтальная линия братьев/сестёр |

    **sibling_type** для стилизации линии:
    - `FULL` → сплошная (━━━)
    - `HALF` → пунктирная (╌╌╌)
    - `STEP` → точечная (·····)

    **meta** содержит счётчики по типам для быстрой статистики.
    """
    result: FamilyGraphResult = await service.get_family_graph(family_id)
    return FamilyGraphResponse.from_result(result)
