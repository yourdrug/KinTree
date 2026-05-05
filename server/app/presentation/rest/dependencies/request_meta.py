from dataclasses import dataclass

from fastapi import Request


@dataclass
class RequestMeta:
    ip_address: str | None
    user_agent: str | None


def get_request_meta(request: Request) -> RequestMeta:
    user_agent = request.headers.get("user-agent")

    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return RequestMeta(
        ip_address=ip,
        user_agent=user_agent,
    )
