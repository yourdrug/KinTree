from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from domain.enums import RelationType
from domain.models.basemodel import BaseModel


class ParentChild(BaseModel):
    __tablename__: str = "parent_child"

    __table_args__: tuple = (
        CheckConstraint("parent_id <> child_id"),
        Index("idx_pc_parent", "parent_id"),
        Index("idx_pc_child", "child_id"),
    )

    parent_id: Mapped[int] = mapped_column(
        ForeignKey("Person.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Parent person ID",
    )

    child_id: Mapped[int] = mapped_column(
        ForeignKey("Person.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Child person ID",
    )

    relation_type: Mapped[RelationType] = mapped_column(
        ENUM(
            RelationType,
            name="person_relation_type_enum",
        ),
        comment="Type of relation for the person",
    )
