from functools import wraps
from typing import (
    Any,
    Callable,
)

from infrastructure.common.exceptions import ServerException


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
        # except ClientException as exception:
        #     message = f'Expected Client Exception in function <{func.__name__}> {exception.message}'
        #
        #     if exception.errors:
        #         message += f' with: {exception.errors}'
        #
        #     logger.error(message)
        except ServerException as exception:
            message = f'Expected Server Exception in function <{func.__name__}> {exception.message}'

            if exception.errors:
                message += f' with: {exception.errors}'

            # logger.error(message)
        except Exception as exception:
            pass
            # logger.error(f'Unexpected Exception in function <{func.__name__}> {exception}')

    return wrapper