"""Resource routers for M1/M2 types: Group, Location, Device, DeviceMetric, Procedure,
Immunization, MedicationDispense, MedicationAdministration, Appointment, Schedule, Slot,
InsuranceClaim."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from vhir_server.api.base import bundle_response, check_if_match, resource_response
from vhir_server.auth.smart import TokenPayload, require_scope
from vhir_server.core.models import (
    AppointmentCreate,
    DeviceCreate,
    DeviceMetricCreate,
    GroupCreate,
    ImmunizationCreate,
    InsuranceClaimCreate,
    LocationCreate,
    MedicationAdministrationCreate,
    MedicationDispenseCreate,
    ProcedureCreate,
    ScheduleCreate,
    SlotCreate,
)
from vhir_server.storage.database import get_db
from vhir_server.storage.repository import ResourceRepository, VersionConflictError


def _make_router(resource_type: str, prefix: str, create_model_cls, tag: str):
    """Build a standard CRUD+search router for a resource type."""
    router = APIRouter(prefix=prefix, tags=[tag])
    RT = resource_type

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def _create(body: create_model_cls, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(RT, "write"))) -> Response:  # type: ignore[valid-type]
        return resource_response(await ResourceRepository(RT, db).create(body.model_dump(mode="json", by_alias=True, exclude_none=True)), 201)

    @router.get("/{rid}")
    async def _read(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(RT, "read"))) -> Response:
        r = await ResourceRepository(RT, db).read(rid)
        if r is None:
            raise HTTPException(404, f"{RT}/{rid} not found")
        return resource_response(r)

    @router.put("/{rid}")
    async def _update(rid: str, body: create_model_cls, request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(RT, "write"))) -> Response:  # type: ignore[valid-type]
        repo = ResourceRepository(RT, db)
        ex = await repo.read(rid)
        if ex:
            check_if_match(request, ex["meta"]["version"])
        try:
            r = await repo.update(rid, body.model_dump(mode="json", by_alias=True, exclude_none=True))
        except VersionConflictError as e:
            raise HTTPException(412, str(e)) from e
        if r is None:
            raise HTTPException(404, f"{RT}/{rid} not found")
        return resource_response(r)

    @router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
    async def _delete(rid: str, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(RT, "write"))) -> None:
        if not await ResourceRepository(RT, db).delete(rid):
            raise HTTPException(404, f"{RT}/{rid} not found")

    @router.get("")
    async def _search(request: Request, db: AsyncSession = Depends(get_db), _t: TokenPayload = Depends(require_scope(RT, "read"))) -> Response:
        p = dict(request.query_params)
        es, total = await ResourceRepository(RT, db).search(p)
        return bundle_response(es, total, str(request.url), int(p.get("_count", 20)), int(p.get("_offset", 0)))

    return router


group_router = _make_router("Group", "/Group", GroupCreate, "Group")
location_router = _make_router("Location", "/Location", LocationCreate, "Location")
device_router = _make_router("Device", "/Device", DeviceCreate, "Device")
device_metric_router = _make_router("DeviceMetric", "/DeviceMetric", DeviceMetricCreate, "DeviceMetric")
procedure_router = _make_router("Procedure", "/Procedure", ProcedureCreate, "Procedure")
immunization_router = _make_router("Immunization", "/Immunization", ImmunizationCreate, "Immunization")
medication_dispense_router = _make_router("MedicationDispense", "/MedicationDispense", MedicationDispenseCreate, "MedicationDispense")
medication_administration_router = _make_router("MedicationAdministration", "/MedicationAdministration", MedicationAdministrationCreate, "MedicationAdministration")
appointment_router = _make_router("Appointment", "/Appointment", AppointmentCreate, "Appointment")
schedule_router = _make_router("Schedule", "/Schedule", ScheduleCreate, "Schedule")
slot_router = _make_router("Slot", "/Slot", SlotCreate, "Slot")

# M2
insurance_claim_router = _make_router("InsuranceClaim", "/InsuranceClaim", InsuranceClaimCreate, "InsuranceClaim")
