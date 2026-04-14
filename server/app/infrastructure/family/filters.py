"""
infrastructure/family/filters.py

Конкретный экземпляр FilterTranslator для ORM-модели.

Здесь прописывается маппинг доменных имён полей → ORM-атрибуты
и набор колонок для оператора SEARCH.

Регистрируются как синглтоны модуля — создаются один раз при импорте.
"""

from __future__ import annotations

from infrastructure.db.filters.translator import FilterTranslator
from infrastructure.db.models.family import Family as ORMFamily


family_filter_translator = FilterTranslator(
    field_map={
        "id": ORMFamily.id,
        "name": ORMFamily.name,
        "owner_id": ORMFamily.owner_id,
        "description": ORMFamily.description,
        "origin_place": ORMFamily.origin_place,
        "founded_year": ORMFamily.founded_year,
        "ended_year": ORMFamily.ended_year,
        "creation_date": ORMFamily.creation_date,
    },
    search_fields=(
        ORMFamily.name,
        ORMFamily.description,
    ),
)
