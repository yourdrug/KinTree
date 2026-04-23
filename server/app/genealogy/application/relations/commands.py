from __future__ import annotations

from dataclasses import dataclass

from genealogy.domain.enums import MarriageStatus, RelationType


# ── Команды ───────────────────────────────────────────────────────────────────


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


# ── Граф ─────────────────────────────────────────────────────────────────────


@dataclass
class NodeDTO:
    """
    Узел графа — персона.
    Содержит только данные нужные для рендера карточки на фронте.
    Полные данные персоны загружаются отдельно по клику.
    """

    id: str
    full_name: str
    gender: str  # "MALE" | "FEMALE" | "UNKNOWN"
    is_alive: bool
    name: str

    birth_year: int | None = None
    death_year: int | None = None
    birth_date_raw: str | None = None


@dataclass
class EdgeDTO:
    """
    Ребро графа — связь между двумя персонами.

    type: "parent_child" | "spouse"

    Для parent_child:
        source_id → родитель
        target_id → ребёнок
        relation_type: "BIOLOGICAL" | "ADOPTED" | "STEP"

    Для spouse:
        source_id, target_id — порядок не важен для отображения
        marriage_status: "MARRIED" | "DIVORCED" | "WIDOWED"
        marriage_year, divorce_year — для подписей на линиях
    """

    type: str  # "parent_child" | "spouse"
    source_id: str
    target_id: str

    # parent_child specific
    relation_type: str | None = None

    # spouse specific
    marriage_status: str | None = None
    marriage_year: int | None = None
    divorce_year: int | None = None


@dataclass
class FamilyGraphResult:
    """
    Граф семьи: список узлов + список рёбер.

    Формат специально выбран под графовые библиотеки фронта:
    - React Flow, D3.js, Cytoscape.js, vis.js — все работают с nodes+edges.

    Фронт может строить дерево обходом графа:
    - Корни: персоны без родителей в этой семье
    - Связи parent_child — вертикальные линии (поколения)
    - Связи spouse — горизонтальные линии (пары)

    Пример структуры которую фронт получит:
    {
      "nodes": [
        {"id": "abc", "full_name": "Иван Иванов", "gender": "MALE", ...},
        {"id": "def", "full_name": "Мария Иванова", "gender": "FEMALE", ...}
      ],
      "edges": [
        {"type": "spouse", "source_id": "abc", "target_id": "def",
         "marriage_status": "MARRIED", "marriage_year": 1965},
        {"type": "parent_child", "source_id": "abc", "target_id": "xyz",
         "relation_type": "BIOLOGICAL"}
      ]
    }
    """

    nodes: list[NodeDTO]
    edges: list[EdgeDTO]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)
