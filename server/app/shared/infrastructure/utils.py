from collections.abc import Callable
import hashlib
from typing import Any


def hash_raw_str(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def Singleton(aClass: Any) -> Callable:
    """
    Singleton: Singleton decorator.

    Args:
        aClass (Any): Class to be decorated.

    Returns:
        Callable: Decorated class.
    """

    class Wrapper:
        """
        Wrapper: Wrapper class.
        """

        instance: aClass = None

        def __call__(self, *args: tuple, **kwargs: dict) -> aClass:
            """
            __call__: Call method.

            Args:
                *args (tuple): Positional arguments.
                **kwargs (dict): Keyword arguments.

            Returns:
                aClass: Decorated class.
            """

            if self.instance is None:
                self.instance: aClass = aClass(*args, **kwargs)

            return self.instance

    return Wrapper()
