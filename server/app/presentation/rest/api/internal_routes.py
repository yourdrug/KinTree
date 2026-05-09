"""
routes.py: File, containing routes for common module.
"""

from datetime import (
    UTC,
    datetime,
)

from fastapi import (
    APIRouter,
    Response,
    status,
)
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
)
from shared.infrastructure.db.settings import settings

from presentation.rest.api.openapi import InfoOpenAPIDescription, InfoOpenAPIResponses


router: APIRouter = APIRouter(prefix="", tags=["Info ℹ️"])


@router.get(
    path="/web/{full_path:path}",
    include_in_schema=False,
)
async def web_page(full_path: str) -> HTMLResponse:
    """
    web_page: Endpoint for web page.

    Args:
        full_path (str): Full path to web page.

    Raises:
        HTTPException: Raised when unexpected error occurs.

    Returns:
        Response: Web page static.
    """

    with open("../static/web/index.html") as f:
        return HTMLResponse(
            content=f.read(),
        )


@router.get(
    path="/web",
    include_in_schema=False,
)
async def web_redirect() -> Response:
    """
    web_redirect: Redirects to web/.

    Returns:
        Response: Redirects to web/.
    """

    return Response(
        headers={"Location": "/web/"},
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )


@router.get(
    path="/",
    include_in_schema=False,
)
async def main_page() -> HTMLResponse:
    """
    main_page: Endpoint for main page.

    Raises:
        HTTPException: Raised when unexpected error occurs.

    Returns:
        Response: Main page static.
    """

    with open("../static/web/index.html") as f:
        return HTMLResponse(
            content=f.read(),
        )


@router.get(
    path="/index.html",
    include_in_schema=False,
)
async def index() -> Response:
    """
    index: Redirects to /.

    Returns:
        Response: Redirects to /.
    """

    return Response(
        headers={"Location": "/"},
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )


@router.get(
    path="/server",
    include_in_schema=False,
)
async def server_page() -> HTMLResponse:
    """
    server_page: Endpoint for server page.

    Raises:
        HTTPException: Raised when unexpected error occurs.

    Returns:
        Response: Server page static.
    """

    with open("../static/server/index.html") as f:
        return HTMLResponse(
            content=f.read(),
        )


@router.get(
    path="/server/index.html",
    include_in_schema=False,
)
async def server_index() -> Response:
    """
    server_index: Redirects to /server.

    Returns:
        Response: Redirects to /server.
    """

    return Response(
        headers={"Location": "/server"},
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )


@router.get(
    path="/docs",
    include_in_schema=False,
)
async def custom_swagger_ui() -> HTMLResponse:
    """
    custom_swagger_ui: Endpoint for custom swagger ui.

    Raises:
        HTTPException: Raised when unexpected error occurs.

    Returns:
        HTMLResponse: Custom swagger static.
    """

    with open("../static/swagger/index.html") as f:
        return HTMLResponse(
            content=f.read(),
        )


@router.get(
    path="/docs/",
    include_in_schema=False,
)
async def docs() -> Response:
    """
    docs: Redirects to docs.

    Returns:
        Response: Redirects to docs.
    """

    return Response(
        headers={"Location": "/docs"},
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )


@router.get(
    path="/health",
    status_code=status.HTTP_200_OK,
    description=InfoOpenAPIDescription.health,
    responses=InfoOpenAPIResponses.health,
    response_class=PlainTextResponse,
)
async def health() -> str:
    """
    health: Endpoint for health check.

    Returns:
        str: Amount of seconds since service start.
    """

    if not settings.SERVICE_START_DATETIME:
        return "0"

    return f"{(datetime.now(UTC) - settings.SERVICE_START_DATETIME).seconds}"
