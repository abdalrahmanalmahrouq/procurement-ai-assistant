"""Request correlation shared by HTTP responses and AI traces."""

from uuid import UUID, uuid4

from fastapi import Request


REQUEST_ID_HEADER = "X-Request-ID"


def normalize_request_id(value: str | None) -> str:
    """Accept UUID request IDs from trusted callers or create a new one."""
    if value:
        try:
            return str(UUID(value))
        except ValueError:
            pass
    return str(uuid4())


def get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = normalize_request_id(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
    return request_id
