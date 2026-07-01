from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


_AUTH_FAILURE_MARKERS = (
    "401",
    "unauthorized",
    "unauthorised",
    "authentication required",
    "invalid_token",
    "missing bearer",
    "bearer token",
    "not authenticated",
)


@dataclass(frozen=True)
class AuthErrorDetails:
    auth_rejected: bool
    error_type: str
    summary: str


def auth_error_details(exc: BaseException) -> AuthErrorDetails:
    lines = list(_exception_lines(exc))
    summary = " | ".join(lines)[:1000]
    lowered = summary.lower()
    return AuthErrorDetails(
        auth_rejected=any(marker in lowered for marker in _AUTH_FAILURE_MARKERS),
        error_type=type(exc).__name__,
        summary=summary,
    )


def _exception_lines(exc: BaseException) -> Iterable[str]:
    message = str(exc).replace("\n", " ").strip()
    yield "{}: {}".format(type(exc).__name__, message[:240])
    children = getattr(exc, "exceptions", ())
    if isinstance(children, (list, tuple)):
        for child in children:
            if isinstance(child, BaseException):
                yield from _exception_lines(child)
    cause = getattr(exc, "__cause__", None)
    if isinstance(cause, BaseException):
        yield from _exception_lines(cause)
    context = getattr(exc, "__context__", None)
    if isinstance(context, BaseException):
        yield from _exception_lines(context)
