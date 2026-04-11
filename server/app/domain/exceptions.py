from typing import (
    Any,
)


class BaseExc(Exception):
    """
    BaseExc: Base exception class for all custom exceptions in the application.
    """

    def __init__(
        self,
        message: str,
        errors: dict | None = None,
    ) -> None:
        """
        __init__.py: Initializes the base exception.

        Args:
            message: Human-readable error message.
            errors: Optional dictionary containing field-specific error details.
        """

        self.message: str = message
        self.errors: dict | None = errors

    def __str__(
        self,
    ) -> str:
        """
        __str__.py: Returns string representation of the exception.

        Returns:
            The error message as a string.
        """

        return self.message

    def __repr__(
        self,
    ) -> str:
        """
        __repr__: Returns official string representation of the exception.

        Returns:
            The error message as a string for debugging purposes.
        """

        return self.message

    def dict(
        self,
    ) -> dict:
        """
        dict: Converts exception to dictionary format for API responses.

        Returns:
            Dictionary containing:
                - message: The error message
                - errors: Field-specific errors if present

            Example:
                {
                    'message': 'Validation failed',
                    'errors': {
                        'email': 'Must be unique'
                    }
                }
        """

        result: dict[str, Any] = {
            "message": self.message,
        }

        if self.errors:
            result["errors"] = self.errors

        return result


class ClientException(BaseExc):
    """
    ClientException: Base class for all client-side exceptions.
    """

    pass


class ServerException(BaseExc):
    """
    ServerException: Base class for all server-side exceptions.
    """

    pass


class DatabaseInteractionError(ServerException):
    """
    DatabaseInteractionError: Exception raised when a database interaction error occurs.
    This typically indicates a 500 Internal Server Error scenario.
    """

    pass


class NotFoundValidationError(ClientException):
    """
    NotFoundValidationError: Exception raised when a requested resource is not found.
    This typically indicates a 404 Not Found error scenario.
    """

    pass


class DomainPersonError(ClientException):
    """
    DomainPersonError: Exception raised when a domain validating person error occurs.
    This typically indicates a 400 Bad Request error scenario.
    """

    pass


class DomainFamilyError(ClientException):
    """
    DomainFamilyError: Нарушение бизнес-правил внутри семьи.
    """

    pass
