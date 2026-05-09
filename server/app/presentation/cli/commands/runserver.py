"""
runserver.py: File, containing runserver command for common app.
"""

import logging
import sys
from typing import Literal, cast

from shared.infrastructure.logging.configuration import logging_config
import uvicorn


logger: logging.Logger = logging.getLogger("default")


def runserver(
    host: str = "0.0.0.0",
    port: int = 8000,
    loop: str = "auto",
    reload: bool = False,
    proxy_headers: bool = True,
    forwarded_allow_ips: str | None = None,
) -> None:
    """
    runserver: Run uvicorn server.

    Args:
        loop (str): Loop to use.
        reload (bool): Reload flag.
        proxy_headers (bool): Proxy headers flag.
        forwarded_allow_ips (Optional[str]): Forward allowed ips.
    """

    try:
        loop = cast(Literal["none", "auto", "asyncio", "uvloop"], loop)

        uvicorn.run(
            app="main:create_application",
            host=host,
            port=port,
            loop=loop,
            reload=reload,
            proxy_headers=proxy_headers,
            forwarded_allow_ips=forwarded_allow_ips,
            log_config=logging_config,
        )
    except Exception as exception:
        logger.error("Ошибка при запуске uvicorn server", exc_info=exception)
        sys.exit(-1)
