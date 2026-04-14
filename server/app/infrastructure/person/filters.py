"""
infrastructure/person/filters.py

Конкретный экземпляр FilterTranslator для ORM-модели.

Здесь прописывается маппинг доменных имён полей → ORM-атрибуты
и набор колонок для оператора SEARCH.

Регистрируются как синглтоны модуля — создаются один раз при импорте.
"""

from __future__ import annotations

from infrastructure.db.filters.translator import FilterTranslator
from infrastructure.db.models.person import Person as ORMPerson


person_filter_translator = FilterTranslator(
    field_map={
        # Идентификаторы
        "id": ORMPerson.id,
        "family_id": ORMPerson.family_id,
        # Имя
        "first_name": ORMPerson.first_name,
        "last_name": ORMPerson.last_name,
        # Перечисление
        "gender": ORMPerson.gender,
        # Даты
        "birth_year": ORMPerson.birth_year,
        "birth_month": ORMPerson.birth_month,
        "birth_day": ORMPerson.birth_day,
        "death_year": ORMPerson.death_year,
        "death_month": ORMPerson.death_month,
        "death_day": ORMPerson.death_day,
        # Аудит
        "creation_date": ORMPerson.creation_date,
    },
    search_fields=(
        ORMPerson.first_name,
        ORMPerson.last_name,
    ),
)
