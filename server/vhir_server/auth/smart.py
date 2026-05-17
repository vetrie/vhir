"""VHIR-SMART: OAuth2 scope enforcement and dev-token mode."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from vhir_server.config import settings

_bearer = HTTPBearer(auto_error=False)

RESOURCE_TYPES = {
    "Animal", "Owner", "Practitioner", "PractitionerRole",
    "Organization", "Encounter", "Observation", "Condition", "MedicationRequest",
}


def issue_dev_token(subject: str = "dev-user", role: str = "veterinarian", org_id: str = "dev-org") -> str:
    """Only available when dev_token_mode=True. Returns a signed JWT."""
    payload = {
        "sub": subject,
        "role": role,
        "org_id": org_id,
        "scopes": ["system/*.read", "system/*.write"],
        "iat": datetime.now(tz=UTC),
        "exp": datetime.now(tz=UTC) + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return str(jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm))


class TokenPayload:
    def __init__(self, data: dict[str, Any]):
        self.sub: str = data.get("sub", "")
        self.role: str = data.get("role", "")
        self.org_id: str = data.get("org_id", "")
        self.scopes: list[str] = data.get("scopes", [])

    def can(self, resource_type: str, action: str) -> bool:
        """Check if token allows {action} on {resource_type}."""
        action = action.lower()
        rtype = resource_type
        for scope in self.scopes:
            # system/*.read etc.
            parts = scope.split("/")
            if len(parts) != 2:
                continue
            context, rest = parts
            if "." in rest:
                res, act = rest.split(".", 1)
            else:
                res, act = rest, "read"
            if res in ("*", rtype) and act in ("*", action):
                return True
        return False


async def get_current_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenPayload:
    if settings.dev_token_mode and creds is None:
        # Issue implicit dev token
        token_str = issue_dev_token()
        data = jwt.decode(token_str, settings.secret_key, algorithms=[settings.algorithm])
        return TokenPayload(data)

    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        data = jwt.decode(creds.credentials, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}") from e

    return TokenPayload(data)


def require_scope(resource_type: str, action: str) -> Callable[..., Coroutine[Any, Any, TokenPayload]]:
    """FastAPI dependency factory that enforces a scope."""
    async def _check(token: TokenPayload = Depends(get_current_token)) -> TokenPayload:
        if not token.can(resource_type, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope required: {resource_type}.{action}",
            )
        return token
    return _check
