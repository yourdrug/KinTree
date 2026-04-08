from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    """
    Schema: Base schema with common configuration for all models.
    Provides default Pydantic configuration inherited by all other schemas.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        strict=False,  # Disables strict type checking for more flexible validation.
        frozen=True,  # Makes models immutable after creation.
        extra='ignore',  # Controls handling of extra fields ('ignore' to silently exclude).
        from_attributes=True,  # Enables ORM mode for model instantiation from objects.
    )
