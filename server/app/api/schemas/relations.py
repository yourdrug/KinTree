from __future__ import annotations

from application.relations.dto import (
    AddParentChildCommand,
    AddSpouseCommand,
    DivorceCommand,
    EdgeDTO,
    FamilyGraphResult,
    NodeDTO,
)
from domain.enums import MarriageStatus, RelationType
from pydantic import BaseModel, Field


# ── Request схемы ─────────────────────────────────────────────────────────────


class AddParentChildRequest(BaseModel):
    parent_id: str = Field(..., min_length=32, max_length=32)
    child_id: str = Field(..., min_length=32, max_length=32)
    relation_type: RelationType = Field(
        default=RelationType.BIOLOGICAL,
        description="BIOLOGICAL | ADOPTED | STEP",
    )

    def to_command(self) -> AddParentChildCommand:
        return AddParentChildCommand(
            parent_id=self.parent_id,
            child_id=self.child_id,
            relation_type=self.relation_type,
        )


class AddSpouseRequest(BaseModel):
    person_a_id: str = Field(..., min_length=32, max_length=32)
    person_b_id: str = Field(..., min_length=32, max_length=32)
    marriage_status: MarriageStatus = MarriageStatus.MARRIED

    marriage_year: int | None = Field(None, ge=1, le=9999)
    marriage_month: int | None = Field(None, ge=1, le=12)
    marriage_day: int | None = Field(None, ge=1, le=31)
    marriage_place: str | None = Field(None, max_length=255)
    marriage_date_raw: str | None = Field(None, max_length=100)

    def to_command(self) -> AddSpouseCommand:
        return AddSpouseCommand(
            person_a_id=self.person_a_id,
            person_b_id=self.person_b_id,
            marriage_status=self.marriage_status,
            marriage_year=self.marriage_year,
            marriage_month=self.marriage_month,
            marriage_day=self.marriage_day,
            marriage_place=self.marriage_place,
            marriage_date_raw=self.marriage_date_raw,
        )


class DivorceRequest(BaseModel):
    person_a_id: str = Field(..., min_length=32, max_length=32)
    person_b_id: str = Field(..., min_length=32, max_length=32)

    divorce_year: int | None = Field(None, ge=1, le=9999)
    divorce_month: int | None = Field(None, ge=1, le=12)
    divorce_day: int | None = Field(None, ge=1, le=31)
    divorce_date_raw: str | None = Field(None, max_length=100)

    def to_command(self) -> DivorceCommand:
        return DivorceCommand(
            person_a_id=self.person_a_id,
            person_b_id=self.person_b_id,
            divorce_year=self.divorce_year,
            divorce_month=self.divorce_month,
            divorce_day=self.divorce_day,
            divorce_date_raw=self.divorce_date_raw,
        )


# ── Response схемы ────────────────────────────────────────────────────────────


class ParentChildResponse(BaseModel):
    parent_id: str
    child_id: str
    relation_type: RelationType

    model_config = {"from_attributes": True}


class SpouseResponse(BaseModel):
    first_person_id: str
    second_person_id: str
    marriage_status: MarriageStatus

    marriage_year: int | None = None
    marriage_month: int | None = None
    marriage_day: int | None = None
    marriage_place: str | None = None
    marriage_date_raw: str | None = None

    divorce_year: int | None = None
    divorce_month: int | None = None
    divorce_day: int | None = None
    divorce_date_raw: str | None = None

    model_config = {"from_attributes": True}


# ── Graph response ────────────────────────────────────────────────────────────


class NodeResponse(BaseModel):
    """
    Узел графа для фронта.
    Данные минимальные — только для рендера карточки.
    """

    id: str
    full_name: str
    gender: str
    is_alive: bool
    first_name: str | None = None
    last_name: str | None = None
    birth_year: int | None = None
    death_year: int | None = None
    birth_date_raw: str | None = None

    @classmethod
    def from_dto(cls, dto: NodeDTO) -> NodeResponse:
        return cls(**dto.__dict__)


class EdgeResponse(BaseModel):
    """
    Ребро графа для фронта.

    type: "parent_child" | "spouse"

    Для "parent_child":
        source → родитель, target → ребёнок
        relation_type: "BIOLOGICAL" | "ADOPTED" | "STEP"

    Для "spouse":
        source и target взаимозаменяемы
        marriage_status: "MARRIED" | "DIVORCED" | "WIDOWED"
    """

    type: str
    source_id: str
    target_id: str

    relation_type: str | None = None  # parent_child
    marriage_status: str | None = None  # spouse
    marriage_year: int | None = None  # spouse
    divorce_year: int | None = None  # spouse

    @classmethod
    def from_dto(cls, dto: EdgeDTO) -> EdgeResponse:
        return cls(**dto.__dict__)


class FamilyGraphResponse(BaseModel):
    """
    Граф семьи — формат для React Flow / D3.js / Cytoscape.

    Фронтенд строит дерево так:
    1. Находит корни: nodes у которых нет входящих parent_child рёбер
    2. BFS/DFS от корней вниз по parent_child рёбрам
    3. Рисует горизонтальные линии для spouse рёбер

    Пример ответа:
    {
      "nodes": [
        {
          "id": "aabbcc...",
          "full_name": "Иван Петрович Иванов",
          "gender": "MALE",
          "is_alive": false,
          "birth_year": 1920,
          "death_year": 1985
        }
      ],
      "edges": [
        {
          "type": "spouse",
          "source_id": "aabbcc...",
          "target_id": "ddeeff...",
          "marriage_status": "MARRIED",
          "marriage_year": 1945
        },
        {
          "type": "parent_child",
          "source_id": "aabbcc...",
          "target_id": "112233...",
          "relation_type": "BIOLOGICAL"
        }
      ],
      "meta": {
        "node_count": 15,
        "edge_count": 14
      }
    }
    """

    nodes: list[NodeResponse]
    edges: list[EdgeResponse]
    meta: dict

    @classmethod
    def from_result(cls, result: FamilyGraphResult) -> FamilyGraphResponse:
        return cls(
            nodes=[NodeResponse.from_dto(n) for n in result.nodes],
            edges=[EdgeResponse.from_dto(e) for e in result.edges],
            meta={
                "node_count": result.node_count,
                "edge_count": result.edge_count,
            },
        )
