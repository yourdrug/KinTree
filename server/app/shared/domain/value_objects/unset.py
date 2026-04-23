from __future__ import annotations

from typing import Final


class UnsetType:
    """
    Sentinel-тип для PATCH-команд.

    Различает два состояния:
    - UNSET  → поле не было передано клиентом (не трогаем)
    - None   → поле передано явно как null (сбрасываем значение)

    Синглтон: все сравнения через `isinstance(v, UnsetType)`.
    """

    _instance: UnsetType | None = None

    def __new__(cls) -> UnsetType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET: Final = UnsetType()
