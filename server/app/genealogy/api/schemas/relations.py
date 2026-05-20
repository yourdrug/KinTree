"""
genealogy/api/schemas/relations.py
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from genealogy.application.relations.commands import (
    AddParentChildCommand,
    AddSpouseCommand,
    DivorceCommand,
    EdgeDTO,
    FamilyGraphResult,
    NodeDTO,
)
from genealogy.domain.entities.sibling import SiblingRelation, SiblingType
from genealogy.domain.enums import MarriageStatus, RelationType


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


class SiblingResponse(BaseModel):
    """
    Ответ для GET /relations/siblings/{person_id}.

    sibling_type:
      FULL — оба биологических родителя общие
      HALF — один общий биологический родитель
      STEP — общий только приёмный / неродной родитель

    shared_parent_ids — ID общих родителей для tooltip-подсказок.
    """

    person_id: str
    sibling_id: str
    sibling_type: SiblingType
    shared_parent_ids: list[str]

    @classmethod
    def from_domain(cls, rel: SiblingRelation) -> SiblingResponse:
        return cls(
            person_id=rel.person_id,
            sibling_id=rel.sibling_id,
            sibling_type=rel.sibling_type,
            shared_parent_ids=sorted(rel.shared_parent_ids),
        )


class NodeResponse(BaseModel):
    """
    Узел графа для фронта.

    Рекомендации по layout:
        - Группировать узлы по generation по вертикали
        - Внутри generation: супруги рядом, сиблинги рядом
        - Определить «левого» супруга пары по gender (MALE слева по конвенции)
          т.к. source/target в spouse edge — лексикографический порядок ID, не gender-based
    """

    id: str
    full_name: str
    gender: str
    is_alive: bool
    first_name: str | None = None
    last_name: str | None = None
    generation: int | None = None
    birth_year: int | None = None
    death_year: int | None = None
    birth_date_raw: str | None = None

    @classmethod
    def from_dto(cls, dto: NodeDTO) -> NodeResponse:
        return cls(
            id=dto.id,
            full_name=dto.full_name,
            gender=dto.gender,
            is_alive=dto.is_alive,
            first_name=dto.first_name,
            last_name=dto.last_name,
            generation=dto.generation,
            birth_year=dto.birth_year,
            death_year=dto.death_year,
            birth_date_raw=dto.birth_date_raw,
        )


class EdgeResponse(BaseModel):
    """
    Ребро графа для фронта.

    type: "parent_child" | "spouse" | "sibling"

    ── parent_child ────────────────────────────────────────────
    source → родитель, target → ребёнок (направление значимо)
    relation_type: "BIOLOGICAL" | "ADOPTED" | "STEP"

    ── spouse ──────────────────────────────────────────────────
    source/target: лексикографический порядок UUID (canonical form).
    НЕ гарантирует MALE=source. Клиент определяет порядок по gender
    из nodes для визуального расположения пары (мужчина слева).
    marriage_status: "MARRIED" | "DIVORCED" | "WIDOWED"
    marriage_year, divorce_year: для подписей на линии.

    ── sibling ─────────────────────────────────────────────────
    source/target: симметрично, порядок не важен.
    sibling_type: "FULL" | "HALF" | "STEP"
    shared_parent_ids: для tooltip «общие родители: Иван, Мария».

    Рекомендации по стилизации линий:
      FULL  → сплошная линия        (━━━)
      HALF  → пунктирная            (╌╌╌)
      STEP  → точечная              (·····)
    """

    type: str
    source_id: str
    target_id: str

    relation_type: str | None = None
    marriage_status: str | None = None
    marriage_year: int | None = None
    divorce_year: int | None = None
    sibling_type: str | None = None
    shared_parent_ids: list[str] = Field(default_factory=list)

    @classmethod
    def from_dto(cls, dto: EdgeDTO) -> EdgeResponse:
        return cls(
            type=dto.type,
            source_id=dto.source_id,
            target_id=dto.target_id,
            relation_type=dto.relation_type,
            marriage_status=dto.marriage_status,
            marriage_year=dto.marriage_year,
            divorce_year=dto.divorce_year,
            sibling_type=dto.sibling_type,
            shared_parent_ids=dto.shared_parent_ids,
        )


class FamilyGraphResponse(BaseModel):
    """
    Граф семьи.

    nodes: содержат generation для layout, first_name/last_name для UI.
    edges: parent_child | spouse | sibling.
    meta:  счётчики + generation_range для масштабирования layout.

    Пример ответа:
    {
      "nodes": [
        {"id": "...", "full_name": "Иван Иванов", "gender": "MALE",
         "first_name": "Иван", "last_name": "Иванов",
         "generation": 0, "is_alive": false}
      ],
      "edges": [
        {"type": "parent_child", "source_id": "...", "target_id": "...",
         "relation_type": "BIOLOGICAL"},
        {"type": "spouse", "source_id": "...", "target_id": "...",
         "marriage_status": "MARRIED", "marriage_year": 1965},
        {"type": "sibling", "source_id": "...", "target_id": "...",
         "sibling_type": "FULL", "shared_parent_ids": ["...", "..."]}
      ],
      "meta": {
        "node_count": 6,
        "edge_count": 8,
        "parent_child_count": 4,
        "spouse_count": 2,
        "sibling_count": 2,
        "generation_range": {"min": 0, "max": 2}
      }
    }
    """

    nodes: list[NodeResponse]
    edges: list[EdgeResponse]
    meta: dict

    @classmethod
    def from_result(cls, result: FamilyGraphResult) -> FamilyGraphResponse:
        nodes = [NodeResponse.from_dto(n) for n in result.nodes]
        edges = [EdgeResponse.from_dto(e) for e in result.edges]

        parent_child_count = sum(1 for e in edges if e.type == "parent_child")
        spouse_count = sum(1 for e in edges if e.type == "spouse")
        sibling_count = sum(1 for e in edges if e.type == "sibling")

        gens = [n.generation for n in nodes if n.generation is not None]
        generation_range = {"min": min(gens), "max": max(gens)} if gens else {"min": 0, "max": 0}

        return cls(
            nodes=nodes,
            edges=edges,
            meta={
                "node_count": result.node_count,
                "edge_count": result.edge_count,
                "parent_child_count": parent_child_count,
                "spouse_count": spouse_count,
                "sibling_count": sibling_count,
                "generation_range": generation_range,
            },
        )
