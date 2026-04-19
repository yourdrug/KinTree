"""
ParentChild: связь родитель–ребёнок между двумя персонами.

Решения по схеме:
- Составной PK (parent_id, child_id) — естественный, гарантирует уникальность на уровне БД.
  Убираем суррогатный `id` из BaseModel: он не нужен, связь и так уникальна парой.
- CheckConstraint parent_id <> child_id — человек не может быть родителем самого себя.
- relation_type: BIOLOGICAL | ADOPTED | STEP — тип родства.
- Индексы по обоим направлениям — быстрый поиск и "родителей персоны" и "детей персоны".

Поля которые НЕ добавляем сюда (они принадлежат Person):
- birth_date, gender и т.д. — это данные персоны, не связи
"""

from domain.enums import RelationType
from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.models.basemodel import LinkedBaseModel


class ParentChild(LinkedBaseModel):
    __tablename__: str = "parent_child"

    __table_args__: tuple = (
        # Человек не может быть родителем самого себя
        CheckConstraint("parent_id <> child_id", name="ck_pc_no_self_relation"),
        # Быстрый поиск: "все дети этого родителя"
        Index("idx_pc_parent", "parent_id"),
        # Быстрый поиск: "все родители этого ребёнка"
        Index("idx_pc_child", "child_id"),
    )

    parent_id: Mapped[str] = mapped_column(
        ForeignKey("Person.id", ondelete="CASCADE"),
        primary_key=True,
        comment="ID родителя",
    )

    child_id: Mapped[str] = mapped_column(
        ForeignKey("Person.id", ondelete="CASCADE"),
        primary_key=True,
        comment="ID ребёнка",
    )

    relation_type: Mapped[RelationType] = mapped_column(
        ENUM(
            RelationType,
            name="relation_type_enum",
        ),
        nullable=False,
        comment="Тип родственной связи: BIOLOGICAL | ADOPTED | STEP",
    )
