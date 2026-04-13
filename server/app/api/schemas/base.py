from typing import Any, ClassVar, Generic, TypeVar
from urllib.parse import urlencode

from domain.exceptions import BaseDomainError
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


T = TypeVar("T")


class BasePageResponse(BaseModel, Generic[T]):
    result: list[T]
    total: int
    limit: int
    offset: int

    next_url: str | None
    prev_url: str | None
    total_pages: int

    @classmethod
    def build(
        cls,
        *,
        items: list[T],
        total: int,
        limit: int,
        offset: int,
        base_url: str,
        query_params: dict,
    ) -> "BasePageResponse[T]":
        total_pages = (total + limit - 1) // limit

        next_url = None
        if offset + limit < total:
            next_url = cls._make_url(
                new_offset=offset + limit,
                base_url=base_url,
                query_params=query_params,
                limit=limit,
            )

        prev_url = None
        if offset > 0:
            prev_offset = max(0, offset - limit)
            prev_url = cls._make_url(
                new_offset=prev_offset,
                base_url=base_url,
                query_params=query_params,
                limit=limit,
            )

        return cls(
            result=items,
            total=total,
            limit=limit,
            offset=offset,
            total_pages=total_pages,
            next_url=next_url,
            prev_url=prev_url,
        )

    @classmethod
    def _make_url(cls, new_offset: int, query_params: dict[str, Any], limit: int, base_url: str) -> str:
        params = {**query_params, "limit": limit, "offset": new_offset}
        return f"{base_url}?{urlencode(params)}"
