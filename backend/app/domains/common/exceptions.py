"""
Domain-level exceptions.

Map these to HTTP responses in the global exception handler (main.py).
"""

from typing import Any


class DomainError(Exception):
    """Base exception for domain logic errors."""

    def __init__(self, message: str, code: str = "domain_error", details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(DomainError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, code="not_found")


class ValidationError(DomainError):
    """Business validation failed."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="validation_error", details=details)


class AuthenticationError(DomainError):
    """Authentication or authorization failed."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, code="authentication_error")


class ForbiddenError(DomainError):
    """Authenticated, but not permitted to touch this resource.

    Distinct from AuthenticationError (401): the caller is known, they just don't own
    the club / lack the role. Multi-tenant club scoping raises this.
    """

    def __init__(self, message: str = "Not permitted") -> None:
        super().__init__(message=message, code="forbidden")


class RateLimitError(DomainError):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Too many requests") -> None:
        super().__init__(message=message, code="rate_limit_exceeded")