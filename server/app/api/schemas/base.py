from dataclasses import dataclass
from typing import Annotated, Any, ClassVar
from urllib.parse import urlencode

from domain.exceptions import BaseDomainError
from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Schema(BaseModel):
    """
    Schema: Base schema with common configuration for all models.
    Provides default Pydantic configuration inherited by all other schemas.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        strict=False,  # Disables strict type checking for more flexible validation.
        frozen=True,  # Makes models immutable after creation.
        extra="ignore",  # Controls handling of extra fields ('ignore' to silently exclude).
        from_attributes=True,  # Enables ORM mode for model instantiation from objects.
    )


class HTTPExceptionSchema(Schema):
    """
    HTTPExceptionSchema: Standard format for API error responses.
    """

    message: str = Field(
        min_length=1,
        max_length=4096,
        description="Main error message",
        examples=["Something went wrong"],
    )

    errors: dict[Any, Any] | None = Field(
        default=None,
        description="Field-specific error messages (key=field name, value=error message)",
        examples=[{"email": "Must be unique"}],
    )


class BasePatchSchema(BaseModel):
    non_nullable: ClassVar[list[str]] = []

    @model_validator(mode="before")
    @classmethod
    def validate_non_nullable_fields(cls, data: Any) -> Any:
        errors = {}
        for field in cls.non_nullable:
            if field in data and data[field] is None:
                errors[field] = "Не может быть null"

        if errors:
            raise BaseDomainError(message="Ошибка валидации", errors=errors)

        return data


@dataclass
class BasePaginationParams:
    """
    Базовые параметры пагинации.

    Наследуется всеми фильтр-схемами.
    dataclass + Annotated[T, Query(...)] — FastAPI читает поля
    как query-параметры, не как request body.
    """

    limit: Annotated[int, Query(ge=1, le=100, description="Количество записей на странице")] = 20
    offset: Annotated[int, Query(ge=0, description="Смещение")] = 0


class BasePageMeta(BaseModel):
    """
    Мета-информация о странице.
    Выносим отдельно, чтобы конкретные Page-схемы
    могли наследовать только мету без поля result.
    """

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
        """
        Вычисляет мета-поля страницы.
        Используется наследниками в их методе from_domain().
        """
        total_pages = max(1, (total + limit - 1) // limit) if limit > 0 else 0
        has_next = offset + limit < total
        has_prev = offset > 0

        next_url = None
        if has_next:
            next_url = cls._make_url(
                base_url=base_url,
                query_params=query_params,
                limit=limit,
                new_offset=offset + limit,
            )

        prev_url = None
        if has_prev:
            prev_url = cls._make_url(
                base_url=base_url,
                query_params=query_params,
                limit=limit,
                new_offset=max(0, offset - limit),
            )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "next_url": next_url,
            "prev_url": prev_url,
        }

    @staticmethod
    def _make_url(
        base_url: str,
        query_params: Any,
        limit: int,
        new_offset: int,
    ) -> str:
        params = {**dict(query_params), "limit": limit, "offset": new_offset}
        return f"{base_url}?{urlencode(params)}"
