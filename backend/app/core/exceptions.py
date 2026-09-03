from typing import Any


class AppError(Exception):
    """Base exception class for all application errors."""
    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        status_code: int = 500,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} '{identifier}' not found",
            code="not_found",
            status_code=404,
            retryable=False,
        )


class ValidationError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=422,
            retryable=False,
            details=details,
        )


class AuthError(AppError):
    def __init__(self, message: str = "Invalid credentials or token"):
        super().__init__(
            message=message,
            code="unauthorized",
            status_code=401,
            retryable=False,
        )


class PermissionDeniedError(AppError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code="forbidden",
            status_code=403,
            retryable=False,
        )


class RateLimitedError(AppError):
    def __init__(self, retry_after_seconds: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Try again in {retry_after_seconds} seconds.",
            code="rate_limited",
            status_code=429,
            retryable=True,
            details={"retry_after": retry_after_seconds},
        )


class UpstreamError(AppError):
    def __init__(self, service_name: str, original_error: str | None = None):
        super().__init__(
            message=f"Upstream service '{service_name}' failed or timed out",
            code="upstream_error",
            status_code=502,
            retryable=True,
            details={"service": service_name, "original_error": original_error},
        )


class DegradedError(AppError):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Service running in degraded state: {reason}",
            code="degraded_mode",
            status_code=200,
            retryable=False,
            details={"reason": reason},
        )


class GroundingError(AppError):
    def __init__(self, message: str = "No picks survived candidate set grounding validation"):
        super().__init__(
            message=message,
            code="grounding_failure",
            status_code=502,
            retryable=True,
        )
