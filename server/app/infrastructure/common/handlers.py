from collections.abc import Callable
from functools import wraps
from logging import Logger, getLogger
from typing import Any

from fastapi import status
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from infrastructure.common.exceptions import ClientException, ServerException
from infrastructure.common.schemas import HTTPExceptionSchema


logger: Logger = getLogger("default")


def handle_exceptions(
    func: Callable,
) -> Callable:
    """
    handle_exceptions: Decorator for handling exceptions.

    Args:
        func (Callable): Function to be decorated.

    Returns:
        Callable: Decorated function.
    """

    @wraps(func)
    async def wrapper(
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        wrapper: Wrapper for handling exceptions.

        Args:
            *args (Any): Any position arguments.
            **kwargs (Any): Any keyword arguments.

        Returns:
            Any: Function result.
        """

        try:
            return await func(*args, **kwargs)

        except ClientException as exception:
            message = f"Expected Client Exception in function <{func.__name__}> {exception.message}"

            if exception.errors:
                message += f" with: {exception.errors}"

            logger.error(message)
        except ServerException as exception:
            message = f"Expected Server Exception in function <{func.__name__}> {exception.message}"

            if exception.errors:
                message += f" with: {exception.errors}"

            logger.error(message)
        except Exception as exception:
            logger.error(f"Unexpected Exception in function <{func.__name__}> {exception}")

    return wrapper


async def handle_fastapi_validation_exceptions(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """
    handle_fastapi_validation_exceptions: Handles FastAPI validation exceptions.

    Args:
        request (Request): FastAPI request.
        exception (Exception): Validation exception.

    Returns:
        JSONResponse: JSON response.
    """

    if not isinstance(request, Request):
        raise exception

    if not isinstance(exception, RequestValidationError):
        logger.critical(f"Internal Server Error {exception}", exc_info=True)

        return JSONResponse(
            content=HTTPExceptionSchema(message="Internal Server Error").model_dump(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    messages: dict = {  # pydantic validation error messages in russian
        "missing": "Обязательное поле",
        "extra_forbidden": "Запрещено добавлять лишние поля",
        "frozen_field": "Нельзя изменять это поле",
        "int_parsing": "Должно быть целым числом",
        "float_parsing": "Должно быть числом (дробь разрешена)",
        "bool_parsing": "Должно быть True или False",
        "string_type": "Должно быть строкой",
        "greater_than": "Должно быть больше {gt}",
        "less_than": "Должно быть меньше {lt}",
        "multiple_of": "Должно быть кратно {multiple_of}",
        "string_too_short": "Минимум {min_length} символов",
        "string_too_long": "Максимум {max_length} символов",
        "string_pattern_mismatch": "Некорректный формат (формат {pattern})",
        "enum": "Допустимые значения: {expected}",
        "literal_error": "Допустимо только: {expected}",
        "date_parsing": "Некорректная дата (формат: ГГГГ-ММ-ДД)",
        "time_parsing": "Некорректное время (формат: ЧЧ:ММ:СС)",
        "datetime_parsing": "Некорректная дата и время (формат: ГГГГ-ММ-ДДTЧЧ:ММ:СС)",
        "datetime_from_date_parsing": "Некорректная дата и время (формат: ГГГГ-ММ-ДДTЧЧ:ММ:СС)",
        "value_error": "Некорректное значение: {error}",
    }

    errors: dict = {}

    for error in exception.errors():
        if "type" not in error or "loc" not in error or not len(error["loc"]) or "msg" not in error:
            continue

        field: str = error["loc"][-1]
        errors[field] = messages.get(error["type"], error["msg"]).format(**error.get("ctx", {}))

    content: dict

    if errors:
        content = {"message": "Ошибка валидации", "errors": errors}
    else:
        content = {"message": "Ошибка валидации"}

    return JSONResponse(
        content=HTTPExceptionSchema(**content).model_dump(),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
