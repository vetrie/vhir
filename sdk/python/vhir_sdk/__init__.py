"""VHIR Python SDK."""
from vhir_sdk.client import VhirClient, collect
from vhir_sdk.exceptions import (
    VhirAuthError,
    VhirConflictError,
    VhirError,
    VhirNotFoundError,
    VhirServerError,
    VhirValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "VhirClient",
    "collect",
    "VhirError",
    "VhirAuthError",
    "VhirNotFoundError",
    "VhirValidationError",
    "VhirConflictError",
    "VhirServerError",
]
