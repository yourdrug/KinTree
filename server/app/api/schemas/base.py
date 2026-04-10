from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


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
