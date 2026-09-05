"""
Standard error envelope and domain exceptions, matching the API Design
Document, Section 2.5 (error format) and Appendix B (error codes).
"""
import uuid
from typing import Any, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class APIError(Exception):
    """Base class for domain-level errors that map to a specific HTTP status
    and machine-readable error code, per the API Design Document."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "VALIDATION_ERROR"

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationAPIError(APIError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "VALIDATION_ERROR"


class UnauthorizedError(APIError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"


class ForbiddenError(APIError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


class NotFoundError(APIError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class ConflictError(APIError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"


class RateLimitedError(APIError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "RATE_LIMITED"


class UpstreamSourceError(APIError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "UPSTREAM_SOURCE_ERROR"


def _envelope(code: str, message: str, details: Optional[dict[str, Any]] = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
        }
    }


def register_exception_handlers(app) -> None:
    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        from fastapi.encoders import jsonable_encoder

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_envelope(
                "VALIDATION_ERROR", "Request validation failed.", {"errors": jsonable_encoder(exc.errors())}
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope("HTTP_ERROR", str(exc.detail)),
        )
