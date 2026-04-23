"""
domain/value_objects/family_member_spec.py

Value Object: минимальный набор данных для проверки дублирования
внутри агрегата Family.

Зачем:
  Family.assert_can_add_member() раньше принимал Person — объект другого
  агрегата. Это создавало прямую зависимость Family → Person на уровне типов.

  FamilyMemberSpec разрывает эту зависимость:
    - Family знает только о VO из своего bounded context.
    - Person знает только свой family_id: str (ссылка, не объект).
    - PersonService строит FamilyMemberSpec из команды и передаёт в Family.

Инвариант дублирования:
  Дубликат = совпадение (first_name + last_name + birth_date).
  None-поля не участвуют в сравнении (нет данных ≠ совпадение).
"""

from __future__ import annotations

from dataclasses import dataclass

from genealogy.domain.value_objects.partial_date import PartialDate


@dataclass(frozen=True)
class FamilyMemberSpec:
    """
    Минимум данных для проверки дублирования внутри Family.

    Используется только в Family.assert_can_add_member().
    Не хранится, не персистируется — живёт только во время use-case.
    """

    first_name: str | None
    last_name: str | None
    birth_date: PartialDate | None

    def has_identity(self) -> bool:
        """
        Есть ли достаточно данных для проверки дублирования.
        Если нет имени вообще — проверка невозможна, пропускаем.
        """
        return bool(self.first_name or self.last_name)
