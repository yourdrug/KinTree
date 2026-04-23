"""
cli.py: File, containing cli app.
"""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

from shared.infrastructure.db.database import database
from typer import Typer

from presentation.cli.commands.upload_all_fixtures import upload_all_fixtures
from presentation.cli.commands.upload_roles_and_permissions import upload_roles_and_permissions


class CLI:
    """
    CLI: Class, containing cli app.
    """

    def __init__(
        self,
    ) -> None:
        """
        __init__: Initialize cli.
        """

        self.cli: Typer = Typer()
        self._register_commands()

    def _register(
        self,
        name: str,
        func: Callable,
        need_db_connection: bool = True,
    ) -> None:
        """
        _register: Register function as command in typer instance.

        Args:
            func (Callable): Function to be registered.
        """

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            def sync_wrapper(
                *args: Any,
                **kwargs: Any,
            ) -> Any:
                if need_db_connection:
                    asyncio.run(database.connect())

                    try:

                        async def runner() -> Callable:
                            return await func(*args, **kwargs)

                        return asyncio.run(runner())

                    finally:
                        asyncio.run(database.disconnect())
                else:
                    return asyncio.run(func(*args, **kwargs))

            self.cli.command(name=name, add_help_option=True)(sync_wrapper)
        else:
            self.cli.command(name=name, add_help_option=True)(func)

    def _register_commands(
        self,
    ) -> None:
        """
        _register_commands: Register commands.
        """

        commands_with_db: list[tuple] = [
            ("upload-roles-permissions", upload_roles_and_permissions),
            ("upload-all-fixtures", upload_all_fixtures),
        ]

        commands_without_db: list[tuple] = [
            # добавить если будет что-то
        ]

        for name, func in commands_with_db:
            self._register(name=name, func=func, need_db_connection=True)

        for name, func in commands_without_db:
            self._register(name=name, func=func, need_db_connection=False)

    def execute_command(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        execute_command: Execute command. Call Typer instance.
        """

        self.cli(*args, **kwargs)


cli: CLI = CLI()
