from typing import Any, ClassVar, Generic, Type

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from domain.common.filters import SortFieldT, BaseFilters
from domain.common.sort import BaseSort
from domain.exceptions import BaseDomainError


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


class BaseListRequest(BaseModel, Generic[SortFieldT]):
    sort_by: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @classmethod
    def get_sort_enum(cls) -> Type[SortFieldT]:
        raise NotImplementedError

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str | None) -> str | None:
        if not v:
            return v

        raw = v.lstrip("-")
        allowed = {f.value for f in cls.get_sort_enum()}

        if raw not in allowed:
            raise ValueError(
                f"Недопустимое поле сортировки: '{raw}'. "
                f"Допустимые значения: {', '.join(sorted(allowed))}"
            )
        return v

    def build_sort(self) -> BaseSort[SortFieldT] | None:
        return BaseFilters.build_sort(self.sort_by, self.get_sort_enum())
