"""
genealogy/application/relations/commands.py

"""

from __future__ import annotations

from dataclasses import dataclass, field

from genealogy.domain.enums import MarriageStatus, RelationType


@dataclass(frozen=True)
class AddParentChildCommand:
    parent_id: str
    child_id: str
    relation_type: RelationType


@dataclass(frozen=True)
class AddSpouseCommand:
    person_a_id: str
    person_b_id: str
    marriage_status: MarriageStatus = MarriageStatus.MARRIED
    marriage_year: int | None = None
    marriage_month: int | None = None
    marriage_day: int | None = None
    marriage_place: str | None = None
    marriage_date_raw: str | None = None


@dataclass(frozen=True)
class DivorceCommand:
    person_a_id: str
    person_b_id: str
    divorce_year: int | None = None
    divorce_month: int | None = None
    divorce_day: int | None = None
    divorce_date_raw: str | None = None


@dataclass
class NodeDTO:
    """
    Узел графа — персона.
    """

    id: str
    full_name: str
    gender: str
    is_alive: bool
    first_name: str | None
    last_name: str | None
    generation: int | None

    birth_year: int | None = None
    death_year: int | None = None
    birth_date_raw: str | None = None


@dataclass
class EdgeDTO:
    """
    Ребро графа — связь между двумя персонами.

    type: "parent_child" | "spouse" | "sibling"

    parent_child: source → родитель, target → ребёнок
    spouse: source/target — лексикографический порядок (canonical)
    sibling: source/target — порядок не важен (симметричная связь)
    """

    type: str
    source_id: str
    target_id: str

    # parent_child
    relation_type: str | None = None

    # spouse
    marriage_status: str | None = None
    marriage_year: int | None = None
    divorce_year: int | None = None

    # sibling
    sibling_type: str | None = None
    shared_parent_ids: list[str] = field(default_factory=list)


@dataclass
class FamilyGraphResult:
    """
    Граф семьи: список узлов + список рёбер.

    nodes содержат generation для layout на клиенте.
    edges трёх типов: parent_child, spouse, sibling.
    """

    nodes: list[NodeDTO]
    edges: list[EdgeDTO]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)
