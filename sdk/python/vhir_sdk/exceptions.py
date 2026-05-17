from __future__ import annotations


class VhirError(Exception):
    """Base class for all VHIR SDK errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class VhirAuthError(VhirError):
    """401/403 — bad or missing token."""


class VhirNotFoundError(VhirError):
    """404 — resource does not exist."""


class VhirValidationError(VhirError):
    """422 — request body failed schema validation."""

    def __init__(self, message: str, detail: object = None) -> None:
        super().__init__(message, status_code=422)
        self.detail = detail


class VhirConflictError(VhirError):
    """409 — resource conflict."""


class VhirServerError(VhirError):
    """5xx — server-side error."""
