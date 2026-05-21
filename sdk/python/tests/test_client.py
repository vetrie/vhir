"""Tests for VhirClient — mocked with respx."""
from __future__ import annotations

import httpx
import pytest
import respx
from vhir_sdk.client import VhirClient, collect
from vhir_sdk.exceptions import (
    VhirAuthError,
    VhirNotFoundError,
    VhirServerError,
    VhirValidationError,
)
from vhir_sdk.models.resources import (
    AnimalCreate,
    AppointmentCreate,
    Coding,
    ConditionCreate,
    DeviceCreate,
    DeviceMetricCreate,
    EncounterCreate,
    GroupCreate,
    ImmunizationCreate,
    InsuranceClaimCreate,
    LocationCreate,
    MedicationAdministrationCreate,
    MedicationDispenseCreate,
    MedicationInfo,
    MedicationRequestCreate,
    ObservationCreate,
    OrganizationCreate,
    OwnerCreate,
    OwnerName,
    PractitionerCreate,
    PractitionerName,
    PractitionerRoleCreate,
    ProcedureCreate,
    Reference,
    ScheduleCreate,
    SlotCreate,
)

BASE_URL = "http://test.vhir.local"
TOKEN = "test-token"

ANIMAL_FIXTURE: dict = {
    "resourceType": "Animal",
    "id": "01JXXXXXXXXXXXXXXXXXXXXXXXXX",
    "species": "canis-familiaris",
    "name": "Buddy",
}

BUNDLE_ONE = {"entry": [{"resource": ANIMAL_FIXTURE}]}
BUNDLE_EMPTY = {"entry": []}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_post(mock_api: respx.MockRouter, path: str, response: dict, status: int = 201) -> None:
    mock_api.post(path).mock(return_value=httpx.Response(status, json=response))


def _mock_get(mock_api: respx.MockRouter, path: str, response: dict, status: int = 200) -> None:
    mock_api.get(path).mock(return_value=httpx.Response(status, json=response))


def _mock_put(mock_api: respx.MockRouter, path: str, response: dict, status: int = 200) -> None:
    mock_api.put(path).mock(return_value=httpx.Response(status, json=response))


def _mock_delete(mock_api: respx.MockRouter, path: str, status: int = 204) -> None:
    mock_api.delete(path).mock(return_value=httpx.Response(status))


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


async def test_auth_header_sent(mock_api):
    mock_api.get("/v1/Animal").mock(
        return_value=httpx.Response(200, json=BUNDLE_EMPTY)
    )
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        results = await collect(client.search_animals())
    assert results == []
    request = mock_api.calls[0].request
    assert request.headers["authorization"] == f"Bearer {TOKEN}"


async def test_obtain_dev_token(mock_api):
    mock_api.post("/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "dev-abc"})
    )
    mock_api.get("/v1/Animal").mock(return_value=httpx.Response(200, json=BUNDLE_EMPTY))
    async with VhirClient(BASE_URL) as client:
        token = await client.obtain_dev_token(subject="tester", role="veterinarian")
        assert token == "dev-abc"
        await collect(client.search_animals())
    request = mock_api.calls[1].request
    assert request.headers["authorization"] == "Bearer dev-abc"


async def test_token_refresh_callback(mock_api):
    calls = []

    def refresh() -> str:
        calls.append(1)
        return "refreshed-token"

    mock_api.get("/v1/Animal").mock(return_value=httpx.Response(200, json=BUNDLE_EMPTY))
    async with VhirClient(BASE_URL, token_refresh_callback=refresh) as client:
        await collect(client.search_animals())
    assert calls == [1]
    request = mock_api.calls[0].request
    assert request.headers["authorization"] == "Bearer refreshed-token"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


async def test_not_found_raises(mock_api):
    mock_api.get("/v1/Animal/missing").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        with pytest.raises(VhirNotFoundError):
            await client.read_animal("missing")


async def test_auth_error_raises(mock_api):
    mock_api.get("/v1/Animal").mock(return_value=httpx.Response(401, json={"detail": "unauth"}))
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        with pytest.raises(VhirAuthError):
            await collect(client.search_animals())


async def test_validation_error_raises(mock_api):
    mock_api.post("/v1/Animal").mock(
        return_value=httpx.Response(422, json={"detail": [{"msg": "field required"}]})
    )
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        with pytest.raises(VhirValidationError) as exc_info:
            await client.create_animal(AnimalCreate(species="x"))
    assert exc_info.value.status_code == 422


async def test_server_error_raises(mock_api):
    mock_api.post("/v1/Animal").mock(return_value=httpx.Response(500, json={"detail": "oops"}))
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        with pytest.raises(VhirServerError):
            await client.create_animal(AnimalCreate(species="x"))


# ---------------------------------------------------------------------------
# Animal CRUD
# ---------------------------------------------------------------------------


async def test_create_animal(mock_api):
    _mock_post(mock_api, "/v1/Animal", ANIMAL_FIXTURE)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_animal(AnimalCreate(species="canis-familiaris", name="Buddy"))
    assert result["id"] == ANIMAL_FIXTURE["id"]


async def test_read_animal(mock_api):
    rid = ANIMAL_FIXTURE["id"]
    _mock_get(mock_api, f"/v1/Animal/{rid}", ANIMAL_FIXTURE)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.read_animal(rid)
    assert result["species"] == "canis-familiaris"


async def test_update_animal(mock_api):
    rid = ANIMAL_FIXTURE["id"]
    updated = {**ANIMAL_FIXTURE, "name": "Max"}
    _mock_put(mock_api, f"/v1/Animal/{rid}", updated)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.update_animal(rid, AnimalCreate(species="canis-familiaris", name="Max"))
    assert result["name"] == "Max"


async def test_delete_animal(mock_api):
    rid = ANIMAL_FIXTURE["id"]
    _mock_delete(mock_api, f"/v1/Animal/{rid}")
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        await client.delete_animal(rid)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


async def test_search_single_page(mock_api):
    mock_api.get("/v1/Animal").mock(return_value=httpx.Response(200, json=BUNDLE_ONE))
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        results = await collect(client.search_animals())
    assert len(results) == 1
    assert results[0]["id"] == ANIMAL_FIXTURE["id"]


async def test_search_pagination_follows_offset(mock_api):
    page1 = {"entry": [{"resource": {**ANIMAL_FIXTURE, "id": "ID1"}}]}
    page2 = {"entry": [{"resource": {**ANIMAL_FIXTURE, "id": "ID2"}}]}

    call_count = 0

    def side_effect(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if "_offset=0" in str(request.url) or "_offset" not in str(request.url):
            return httpx.Response(200, json=page1)
        return httpx.Response(200, json=page2)

    mock_api.get("/v1/Animal").mock(side_effect=side_effect)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        results = await collect(client.search_animals(page_size=1))
    assert len(results) == 2
    assert call_count == 2


async def test_search_empty_stops(mock_api):
    mock_api.get("/v1/Animal").mock(return_value=httpx.Response(200, json=BUNDLE_EMPTY))
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        results = await collect(client.search_animals())
    assert results == []


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------


async def test_create_owner(mock_api):
    owner = {"resourceType": "Owner", "id": "OWN1", "ownerType": "individual"}
    _mock_post(mock_api, "/v1/Owner", owner)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_owner(
            OwnerCreate(name=OwnerName(given="Jane", family="Doe"))
        )
    assert result["id"] == "OWN1"


# ---------------------------------------------------------------------------
# Practitioner
# ---------------------------------------------------------------------------


async def test_create_practitioner(mock_api):
    prac = {"resourceType": "Practitioner", "id": "PRAC1"}
    _mock_post(mock_api, "/v1/Practitioner", prac)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_practitioner(
            PractitionerCreate(name=PractitionerName(family="Smith"))
        )
    assert result["id"] == "PRAC1"


# ---------------------------------------------------------------------------
# PractitionerRole
# ---------------------------------------------------------------------------


async def test_create_practitioner_role(mock_api):
    pr = {"resourceType": "PractitionerRole", "id": "PR1"}
    _mock_post(mock_api, "/v1/PractitionerRole", pr)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_practitioner_role(
            PractitionerRoleCreate(
                practitioner=Reference(ref="Practitioner/PRAC1"),
                organization=Reference(ref="Organization/ORG1"),
                role="veterinarian",
            )
        )
    assert result["id"] == "PR1"


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------


async def test_create_organization(mock_api):
    org = {"resourceType": "Organization", "id": "ORG1"}
    _mock_post(mock_api, "/v1/Organization", org)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_organization(OrganizationCreate(name="City Vet Clinic"))
    assert result["id"] == "ORG1"


# ---------------------------------------------------------------------------
# Encounter
# ---------------------------------------------------------------------------


async def test_create_encounter(mock_api):
    enc = {"resourceType": "Encounter", "id": "ENC1"}
    _mock_post(mock_api, "/v1/Encounter", enc)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_encounter(
            EncounterCreate(
                status="in-progress",
                **{"class": "AMB"},
                subject=Reference(ref="Animal/ANM1"),
            )
        )
    assert result["id"] == "ENC1"


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------


async def test_create_observation(mock_api):
    obs = {"resourceType": "Observation", "id": "OBS1"}
    _mock_post(mock_api, "/v1/Observation", obs)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_observation(
            ObservationCreate(
                status="final",
                code=Coding(code="8867-4", system="http://loinc.org", display="Heart rate"),
                subject=Reference(ref="Animal/ANM1"),
            )
        )
    assert result["id"] == "OBS1"


# ---------------------------------------------------------------------------
# Condition
# ---------------------------------------------------------------------------


async def test_create_condition(mock_api):
    cond = {"resourceType": "Condition", "id": "COND1"}
    _mock_post(mock_api, "/v1/Condition", cond)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_condition(
            ConditionCreate(
                status="active",
                code=Coding(code="K29.70", display="Gastritis"),
                subject=Reference(ref="Animal/ANM1"),
            )
        )
    assert result["id"] == "COND1"


# ---------------------------------------------------------------------------
# Immunization
# ---------------------------------------------------------------------------


async def test_create_immunization(mock_api):
    imm = {"resourceType": "Immunization", "id": "IMM1"}
    _mock_post(mock_api, "/v1/Immunization", imm)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_immunization(
            ImmunizationCreate(
                status="completed",
                vaccineCode=Coding(code="rabies", display="Rabies"),
                subject=Reference(ref="Animal/ANM1"),
            )
        )
    assert result["id"] == "IMM1"


# ---------------------------------------------------------------------------
# MedicationRequest
# ---------------------------------------------------------------------------


async def test_create_medication_request(mock_api):
    rx = {"resourceType": "MedicationRequest", "id": "RX1"}
    _mock_post(mock_api, "/v1/MedicationRequest", rx)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_medication_request(
            MedicationRequestCreate(
                status="active",
                intent="order",
                medication=MedicationInfo(name="Amoxicillin"),
                subject=Reference(ref="Animal/ANM1"),
                requester=Reference(ref="Practitioner/PRAC1"),
            )
        )
    assert result["id"] == "RX1"


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------


async def test_create_device(mock_api):
    dev = {"resourceType": "Device", "id": "DEV1"}
    _mock_post(mock_api, "/v1/Device", dev)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_device(DeviceCreate(type="thermometer"))
    assert result["id"] == "DEV1"


# ---------------------------------------------------------------------------
# DeviceMetric
# ---------------------------------------------------------------------------


async def test_create_device_metric(mock_api):
    dm = {"resourceType": "DeviceMetric", "id": "DM1"}
    _mock_post(mock_api, "/v1/DeviceMetric", dm)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_device_metric(
            DeviceMetricCreate(
                device=Reference(ref="Device/DEV1"),
                type=Coding(code="temp"),
                category="measurement",
            )
        )
    assert result["id"] == "DM1"


# ---------------------------------------------------------------------------
# Group
# ---------------------------------------------------------------------------


async def test_create_group(mock_api):
    grp = {"resourceType": "Group", "id": "GRP1"}
    _mock_post(mock_api, "/v1/Group", grp)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_group(GroupCreate(name="Herd A"))
    assert result["id"] == "GRP1"


# ---------------------------------------------------------------------------
# InsuranceClaim
# ---------------------------------------------------------------------------


async def test_create_insurance_claim(mock_api):
    claim = {"resourceType": "InsuranceClaim", "id": "CLM1"}
    _mock_post(mock_api, "/v1/InsuranceClaim", claim)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_insurance_claim(
            InsuranceClaimCreate(
                status="active",
                subject=Reference(ref="Animal/ANM1"),
            )
        )
    assert result["id"] == "CLM1"


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------


async def test_create_appointment(mock_api):
    apt = {"resourceType": "Appointment", "id": "APT1"}
    _mock_post(mock_api, "/v1/Appointment", apt)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_appointment(
            AppointmentCreate(
                status="booked",
                subject=Reference(ref="Animal/ANM1"),
            )
        )
    assert result["id"] == "APT1"


# ---------------------------------------------------------------------------
# Schedule & Slot
# ---------------------------------------------------------------------------


async def test_create_schedule(mock_api):
    sched = {"resourceType": "Schedule", "id": "SCH1"}
    _mock_post(mock_api, "/v1/Schedule", sched)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_schedule(
            ScheduleCreate(actor=[Reference(ref="Practitioner/PRAC1")])
        )
    assert result["id"] == "SCH1"


async def test_create_slot(mock_api):
    slot = {"resourceType": "Slot", "id": "SLT1"}
    _mock_post(mock_api, "/v1/Slot", slot)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_slot(
            SlotCreate(
                schedule=Reference(ref="Schedule/SCH1"),
                status="free",
                start="2026-06-01T09:00:00Z",
                end="2026-06-01T09:30:00Z",
            )
        )
    assert result["id"] == "SLT1"


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


async def test_create_location(mock_api):
    loc = {"resourceType": "Location", "id": "LOC1"}
    _mock_post(mock_api, "/v1/Location", loc)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_location(LocationCreate(name="Exam Room 1"))
    assert result["id"] == "LOC1"


# ---------------------------------------------------------------------------
# Procedure
# ---------------------------------------------------------------------------


async def test_create_procedure(mock_api):
    proc = {"resourceType": "Procedure", "id": "PROC1"}
    _mock_post(mock_api, "/v1/Procedure", proc)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_procedure(
            ProcedureCreate(
                status="completed",
                code=Coding(code="73761001", display="Colonoscopy"),
                subject=Reference(ref="Animal/ANM1"),
            )
        )
    assert result["id"] == "PROC1"


# ---------------------------------------------------------------------------
# MedicationDispense & MedicationAdministration
# ---------------------------------------------------------------------------


async def test_create_medication_dispense(mock_api):
    disp = {"resourceType": "MedicationDispense", "id": "DISP1"}
    _mock_post(mock_api, "/v1/MedicationDispense", disp)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_medication_dispense(
            MedicationDispenseCreate(
                status="completed",
                medication=MedicationInfo(name="Amoxicillin"),
                subject=Reference(ref="Animal/ANM1"),
            )
        )
    assert result["id"] == "DISP1"


async def test_create_medication_administration(mock_api):
    adm = {"resourceType": "MedicationAdministration", "id": "ADM1"}
    _mock_post(mock_api, "/v1/MedicationAdministration", adm)
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.create_medication_administration(
            MedicationAdministrationCreate(
                status="completed",
                medication=MedicationInfo(name="Penicillin"),
                subject=Reference(ref="Group/GRP1"),
            )
        )
    assert result["id"] == "ADM1"


# ---------------------------------------------------------------------------
# System ops
# ---------------------------------------------------------------------------


async def test_microchip_lookup_found(mock_api):
    mock_api.post("/v1/$lookup-microchip").mock(
        return_value=httpx.Response(
            200,
            json={"found": True, "localAnimal": "Animal/ANM1"},
        )
    )
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.lookup_microchip("900123456789012")
    assert result.found is True
    assert result.localAnimal == "Animal/ANM1"


async def test_microchip_lookup_not_found(mock_api):
    mock_api.post("/v1/$lookup-microchip").mock(
        return_value=httpx.Response(200, json={"found": False})
    )
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.lookup_microchip("999000000000000")
    assert result.found is False


async def test_capability_statement(mock_api):
    mock_api.get("/v1/metadata").mock(
        return_value=httpx.Response(200, json={"resourceType": "CapabilityStatement"})
    )
    async with VhirClient(BASE_URL, token=TOKEN) as client:
        result = await client.get_capability_statement()
    assert result["resourceType"] == "CapabilityStatement"


# ---------------------------------------------------------------------------
# Model serialisation
# ---------------------------------------------------------------------------


def test_animal_model_dump_excludes_none():
    animal = AnimalCreate(species="felis-catus")
    dumped = animal.model_dump(exclude_none=True)
    assert "name" not in dumped
    assert dumped["species"] == "felis-catus"
    assert dumped["resourceType"] == "Animal"


def test_encounter_class_alias():
    enc = EncounterCreate(
        status="finished",
        **{"class": "AMB"},
        subject=Reference(ref="Animal/ANM1"),
    )
    dumped = enc.model_dump(exclude_none=True)
    assert "class" in dumped
    assert dumped["class"] == "AMB"
