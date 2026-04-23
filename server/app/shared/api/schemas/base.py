"""
api/schemas/base.py

Базовые Pydantic-схемы, которые наследуются во всём API.

Принципы:
- BasePageResponse — общий формат пагинированного ответа.
- BasePaginationParams — общие query-параметры limit/offset.
- BasePatchSchema — защита non-nullable полей от явной передачи null.
- ErrorResponse — стандартный формат ошибки.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, ClassVar
from urllib.parse import urlencode

from shared.domain.exceptions import DomainValidationError
from fastapi import Query
from pydantic import BaseModel, Field, model_validator


class ErrorResponse(BaseModel):
    """Стандартный формат ошибки в API."""

    message: str = Field(description="Сообщение об ошибке")
    errors: dict[str, Any] | None = Field(default=None, description="Детали по полям")


class BasePatchSchema(BaseModel):
    """
    Базовая схема для PATCH-запросов.

    non_nullable — список полей, которые нельзя передать как null.
    Например: gender не может быть null, но может быть не передан.
    """

    non_nullable: ClassVar[list[str]] = []

    @model_validator(mode="before")
    @classmethod
    def validate_non_nullable(cls, data: Any) -> Any:
        errors = {}
        for field in cls.non_nullable:
            if field in data and data[field] is None:
                errors[field] = "Не может быть null"

        if errors:
            raise DomainValidationError(message="Ошибка валидации", errors=errors)
        return data


@dataclass
class BasePaginationParams:
    """Базовые параметры пагинации для Filter-схем."""

    limit: Annotated[int, Query(ge=1, le=100, description="Записей на странице")] = 20
    offset: Annotated[int, Query(ge=0, description="Смещение")] = 0


class BasePageResponse(BaseModel):
    """Мета-информация о странице. Наследуется конкретными Page-ответами."""

    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_prev: bool
    next_url: str | None = None
    prev_url: str | None = None

    @classmethod
    def _build_meta(
        cls,
        *,
        total: int,
        limit: int,
        offset: int,
        base_url: str,
        query_params: Any,
    ) -> dict[str, Any]:
        total_pages = max(1, (total + limit - 1) // limit) if limit > 0 else 0
        has_next = offset + limit < total
        has_prev = offset > 0

        def make_url(new_offset: int) -> str:
            params = {**dict(query_params), "limit": limit, "offset": new_offset}
            return f"{base_url}?{urlencode(params)}"

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "next_url": make_url(offset + limit) if has_next else None,
            "prev_url": make_url(max(0, offset - limit)) if has_prev else None,
        }
