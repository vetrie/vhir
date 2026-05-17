"""Resource routers for all M0 types except Animal (which has its own module)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from vhir_server.api.base import bundle_response, check_if_match, resource_response
from vhir_server.auth.smart import TokenPayload, require_scope
from vhir_server.core.models import (
    ConditionCreate,
    EncounterCreate,
    MedicationRequestCreate,
    ObservationCreate,
    OrganizationCreate,
    OwnerCreate,
    PractitionerCreate,
    PractitionerRoleCreate,
)
from vhir_server.storage.database import get_db
from vhir_server.storage.repository import ResourceRepository, VersionConflictError

# ── Owner ──────────────────────────────────────────────────────────────────────
owner_router = APIRouter(prefix="/Owner", tags=["Owner"])
_OW = "Owner"


@owner_router.post("", status_code=status.HTTP_201_CREATED)
async def create_owner(body: OwnerCreate, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OW, "write"))) -> Response:
    return resource_response(await ResourceRepository(_OW, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)


@owner_router.get("/{rid}")
async def read_owner(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OW, "read"))) -> Response:
    r = await ResourceRepository(_OW, db).read(rid)
    if r is None:
        raise HTTPException(404, f"Owner/{rid} not found")
    return resource_response(r)


@owner_router.put("/{rid}")
async def update_owner(rid: str, body: OwnerCreate, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OW, "write"))) -> Response:
    repo = ResourceRepository(_OW, db)
    ex = await repo.read(rid)
    if ex:
        check_if_match(request, ex["meta"]["version"])
    try:
        r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
    except VersionConflictError as e:
        raise HTTPException(412, str(e)) from e
    if r is None:
        raise HTTPException(404, f"Owner/{rid} not found")
    return resource_response(r)


@owner_router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_owner(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OW, "write"))) -> None:
    if not await ResourceRepository(_OW, db).delete(rid):
        raise HTTPException(404, f"Owner/{rid} not found")


@owner_router.get("")
async def search_owners(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OW, "read"))) -> Response:
    p = dict(request.query_params)
    es, total = await ResourceRepository(_OW, db).search(p)
    return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))


# ── Practitioner ───────────────────────────────────────────────────────────────
practitioner_router = APIRouter(prefix="/Practitioner", tags=["Practitioner"])
_PR = "Practitioner"


@practitioner_router.post("", status_code=status.HTTP_201_CREATED)
async def create_practitioner(body: PractitionerCreate, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PR, "write"))) -> Response:
    return resource_response(await ResourceRepository(_PR, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)


@practitioner_router.get("/{rid}")
async def read_practitioner(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PR, "read"))) -> Response:
    r = await ResourceRepository(_PR, db).read(rid)
    if r is None:
        raise HTTPException(404, f"Practitioner/{rid} not found")
    return resource_response(r)


@practitioner_router.put("/{rid}")
async def update_practitioner(rid: str, body: PractitionerCreate, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PR, "write"))) -> Response:
    repo = ResourceRepository(_PR, db)
    ex = await repo.read(rid)
    if ex:
        check_if_match(request, ex["meta"]["version"])
    try:
        r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
    except VersionConflictError as e:
        raise HTTPException(412, str(e)) from e
    if r is None:
        raise HTTPException(404, f"Practitioner/{rid} not found")
    return resource_response(r)


@practitioner_router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_practitioner(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PR, "write"))) -> None:
    if not await ResourceRepository(_PR, db).delete(rid):
        raise HTTPException(404, f"Practitioner/{rid} not found")


@practitioner_router.get("")
async def search_practitioners(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PR, "read"))) -> Response:
    p = dict(request.query_params)
    es, total = await ResourceRepository(_PR, db).search(p)
    return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))


# ── PractitionerRole ───────────────────────────────────────────────────────────
practitioner_role_router = APIRouter(prefix="/PractitionerRole", tags=["PractitionerRole"])
_PRR = "PractitionerRole"


@practitioner_role_router.post("", status_code=status.HTTP_201_CREATED)
async def create_practitioner_role(body: PractitionerRoleCreate, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PRR, "write"))) -> Response:
    return resource_response(await ResourceRepository(_PRR, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)


@practitioner_role_router.get("/{rid}")
async def read_practitioner_role(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PRR, "read"))) -> Response:
    r = await ResourceRepository(_PRR, db).read(rid)
    if r is None:
        raise HTTPException(404, f"PractitionerRole/{rid} not found")
    return resource_response(r)


@practitioner_role_router.put("/{rid}")
async def update_practitioner_role(rid: str, body: PractitionerRoleCreate, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PRR, "write"))) -> Response:
    repo = ResourceRepository(_PRR, db)
    ex = await repo.read(rid)
    if ex:
        check_if_match(request, ex["meta"]["version"])
    try:
        r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
    except VersionConflictError as e:
        raise HTTPException(412, str(e)) from e
    if r is None:
        raise HTTPException(404, f"PractitionerRole/{rid} not found")
    return resource_response(r)


@practitioner_role_router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_practitioner_role(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PRR, "write"))) -> None:
    if not await ResourceRepository(_PRR, db).delete(rid):
        raise HTTPException(404, f"PractitionerRole/{rid} not found")


@practitioner_role_router.get("")
async def search_practitioner_roles(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_PRR, "read"))) -> Response:
    p = dict(request.query_params)
    es, total = await ResourceRepository(_PRR, db).search(p)
    return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))


# ── Organization ───────────────────────────────────────────────────────────────
organization_router = APIRouter(prefix="/Organization", tags=["Organization"])
_ORG = "Organization"


@organization_router.post("", status_code=status.HTTP_201_CREATED)
async def create_organization(body: OrganizationCreate, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ORG, "write"))) -> Response:
    return resource_response(await ResourceRepository(_ORG, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)


@organization_router.get("/{rid}")
async def read_organization(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ORG, "read"))) -> Response:
    r = await ResourceRepository(_ORG, db).read(rid)
    if r is None:
        raise HTTPException(404, f"Organization/{rid} not found")
    return resource_response(r)


@organization_router.put("/{rid}")
async def update_organization(rid: str, body: OrganizationCreate, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ORG, "write"))) -> Response:
    repo = ResourceRepository(_ORG, db)
    ex = await repo.read(rid)
    if ex:
        check_if_match(request, ex["meta"]["version"])
    try:
        r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
    except VersionConflictError as e:
        raise HTTPException(412, str(e)) from e
    if r is None:
        raise HTTPException(404, f"Organization/{rid} not found")
    return resource_response(r)


@organization_router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ORG, "write"))) -> None:
    if not await ResourceRepository(_ORG, db).delete(rid):
        raise HTTPException(404, f"Organization/{rid} not found")


@organization_router.get("")
async def search_organizations(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ORG, "read"))) -> Response:
    p = dict(request.query_params)
    es, total = await ResourceRepository(_ORG, db).search(p)
    return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))


# ── Encounter ──────────────────────────────────────────────────────────────────
encounter_router = APIRouter(prefix="/Encounter", tags=["Encounter"])
_ENC = "Encounter"


@encounter_router.post("", status_code=status.HTTP_201_CREATED)
async def create_encounter(body: EncounterCreate, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ENC, "write"))) -> Response:
    return resource_response(await ResourceRepository(_ENC, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)


@encounter_router.get("/{rid}")
async def read_encounter(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ENC, "read"))) -> Response:
    r = await ResourceRepository(_ENC, db).read(rid)
    if r is None:
        raise HTTPException(404, f"Encounter/{rid} not found")
    return resource_response(r)


@encounter_router.put("/{rid}")
async def update_encounter(rid: str, body: EncounterCreate, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ENC, "write"))) -> Response:
    repo = ResourceRepository(_ENC, db)
    ex = await repo.read(rid)
    if ex:
        check_if_match(request, ex["meta"]["version"])
    try:
        r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
    except VersionConflictError as e:
        raise HTTPException(412, str(e)) from e
    if r is None:
        raise HTTPException(404, f"Encounter/{rid} not found")
    return resource_response(r)


@encounter_router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_encounter(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ENC, "write"))) -> None:
    if not await ResourceRepository(_ENC, db).delete(rid):
        raise HTTPException(404, f"Encounter/{rid} not found")


@encounter_router.get("")
async def search_encounters(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_ENC, "read"))) -> Response:
    p = dict(request.query_params)
    es, total = await ResourceRepository(_ENC, db).search(p)
    return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))


# ── Observation ────────────────────────────────────────────────────────────────
observation_router = APIRouter(prefix="/Observation", tags=["Observation"])
_OBS = "Observation"


@observation_router.post("", status_code=status.HTTP_201_CREATED)
async def create_observation(body: ObservationCreate, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OBS, "write"))) -> Response:
    return resource_response(await ResourceRepository(_OBS, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)


@observation_router.get("/{rid}")
async def read_observation(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OBS, "read"))) -> Response:
    r = await ResourceRepository(_OBS, db).read(rid)
    if r is None:
        raise HTTPException(404, f"Observation/{rid} not found")
    return resource_response(r)


@observation_router.put("/{rid}")
async def update_observation(rid: str, body: ObservationCreate, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OBS, "write"))) -> Response:
    repo = ResourceRepository(_OBS, db)
    ex = await repo.read(rid)
    if ex:
        check_if_match(request, ex["meta"]["version"])
    try:
        r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
    except VersionConflictError as e:
        raise HTTPException(412, str(e)) from e
    if r is None:
        raise HTTPException(404, f"Observation/{rid} not found")
    return resource_response(r)


@observation_router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_observation(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OBS, "write"))) -> None:
    if not await ResourceRepository(_OBS, db).delete(rid):
        raise HTTPException(404, f"Observation/{rid} not found")


@observation_router.get("")
async def search_observations(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_OBS, "read"))) -> Response:
    p = dict(request.query_params)
    es, total = await ResourceRepository(_OBS, db).search(p)
    return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))


# ── Condition ──────────────────────────────────────────────────────────────────
condition_router = APIRouter(prefix="/Condition", tags=["Condition"])
_CON = "Condition"


@condition_router.post("", status_code=status.HTTP_201_CREATED)
async def create_condition(body: ConditionCreate, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_CON, "write"))) -> Response:
    return resource_response(await ResourceRepository(_CON, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)


@condition_router.get("/{rid}")
async def read_condition(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_CON, "read"))) -> Response:
    r = await ResourceRepository(_CON, db).read(rid)
    if r is None:
        raise HTTPException(404, f"Condition/{rid} not found")
    return resource_response(r)


@condition_router.put("/{rid}")
async def update_condition(rid: str, body: ConditionCreate, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_CON, "write"))) -> Response:
    repo = ResourceRepository(_CON, db)
    ex = await repo.read(rid)
    if ex:
        check_if_match(request, ex["meta"]["version"])
    try:
        r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
    except VersionConflictError as e:
        raise HTTPException(412, str(e)) from e
    if r is None:
        raise HTTPException(404, f"Condition/{rid} not found")
    return resource_response(r)


@condition_router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_condition(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_CON, "write"))) -> None:
    if not await ResourceRepository(_CON, db).delete(rid):
        raise HTTPException(404, f"Condition/{rid} not found")


@condition_router.get("")
async def search_conditions(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_CON, "read"))) -> Response:
    p = dict(request.query_params)
    es, total = await ResourceRepository(_CON, db).search(p)
    return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))


# ── MedicationRequest ──────────────────────────────────────────────────────────
medication_request_router = APIRouter(prefix="/MedicationRequest", tags=["MedicationRequest"])
_MR = "MedicationRequest"


@medication_request_router.post("", status_code=status.HTTP_201_CREATED)
async def create_medication_request(body: MedicationRequestCreate, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_MR, "write"))) -> Response:
    return resource_response(await ResourceRepository(_MR, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)


@medication_request_router.get("/{rid}")
async def read_medication_request(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_MR, "read"))) -> Response:
    r = await ResourceRepository(_MR, db).read(rid)
    if r is None:
        raise HTTPException(404, f"MedicationRequest/{rid} not found")
    return resource_response(r)


@medication_request_router.put("/{rid}")
async def update_medication_request(rid: str, body: MedicationRequestCreate, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_MR, "write"))) -> Response:
    repo = ResourceRepository(_MR, db)
    ex = await repo.read(rid)
    if ex:
        check_if_match(request, ex["meta"]["version"])
    try:
        r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
    except VersionConflictError as e:
        raise HTTPException(412, str(e)) from e
    if r is None:
        raise HTTPException(404, f"MedicationRequest/{rid} not found")
    return resource_response(r)


@medication_request_router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication_request(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_MR, "write"))) -> None:
    if not await ResourceRepository(_MR, db).delete(rid):
        raise HTTPException(404, f"MedicationRequest/{rid} not found")


@medication_request_router.get("")
async def search_medication_requests(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(_MR, "read"))) -> Response:
    p = dict(request.query_params)
    es, total = await ResourceRepository(_MR, db).search(p)
    return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))
