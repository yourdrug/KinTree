from typing import Optional, Any

from pydantic import Field

from domain.schemas.base import Schema


class HTTPExceptionSchema(Schema):
    """
    HTTPExceptionSchema: Standard format for API error responses.
    """

    message: str = Field(
        min_length=1,
        max_length=4096,
        description='Main error message',
        examples=['Something went wrong'],
    )

    errors: Optional[dict[Any, Any]] = Field(
        default=None,
        description='Field-specific error messages (key=field name, value=error message)',
        examples=[{'email': 'Must be unique'}],
    )
