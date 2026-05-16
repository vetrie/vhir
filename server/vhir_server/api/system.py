"""System-level endpoints: /metadata (capability statement), /oauth/token (dev mode)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from vhir_server.auth.smart import TokenPayload, get_current_token, issue_dev_token
from vhir_server.config import settings

router = APIRouter(tags=["System"])


class TokenRequest(BaseModel):
    grant_type: str = "dev"
    subject: str = "dev-user"
    role: str = "veterinarian"
    org_id: str = "dev-org"


@router.get("/.well-known/vhir-configuration")
async def vhir_configuration() -> dict[str, Any]:
    base = settings.server_base_url
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "jwks_uri": f"{base}/oauth/jwks",
        "scopes_supported": [
            "system/*.read", "system/*.write",
            "user/*.read", "user/*.write",
            "animal/*.read", "animal/*.write",
            "owner/*.read", "owner/*.write",
        ],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "code_challenge_methods_supported": ["S256"],
    }


@router.get("/v1/metadata")
async def capability_statement() -> dict[str, Any]:
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.now(tz=timezone.utc).date().isoformat(),
        "kind": "instance",
        "software": {"name": "VHIR Reference Server", "version": "0.1.0"},
        "implementation": {"description": "VHIR reference implementation", "url": settings.server_base_url},
        "fhirVersion": "N/A",
        "vhirVersion": "0.1.0",
        "format": ["application/vhir+json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    _cap_resource("Animal",            ["read", "create", "update", "delete", "search"]),
                    _cap_resource("Owner",             ["read", "create", "update", "delete", "search"]),
                    _cap_resource("Practitioner",      ["read", "create", "update", "delete", "search"]),
                    _cap_resource("PractitionerRole",  ["read", "create", "update", "delete", "search"]),
                    _cap_resource("Organization",      ["read", "create", "update", "delete", "search"]),
                    _cap_resource("Encounter",         ["read", "create", "update", "delete", "search"]),
                    _cap_resource("Observation",       ["read", "create", "update", "delete", "search"]),
                    _cap_resource("Condition",         ["read", "create", "update", "delete", "search"]),
                    _cap_resource("MedicationRequest", ["read", "create", "update", "delete", "search"]),
                ],
            }
        ],
    }


def _cap_resource(resource_type: str, interactions: list[str]) -> dict[str, Any]:
    return {
        "type": resource_type,
        "interaction": [{"code": i} for i in interactions],
        "versioning": "versioned",
    }


@router.post("/oauth/token")
async def dev_token(req: TokenRequest) -> dict[str, Any]:
    """Dev-mode token endpoint. Not for production."""
    if not settings.dev_token_mode:
        raise HTTPException(status_code=404, detail="Not found")
    token = issue_dev_token(subject=req.subject, role=req.role, org_id=req.org_id)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "scope": "system/*.read system/*.write",
    }
