"""Tests for Immunization, Procedure, Location, Appointment resources."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_immunization(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Daisy",
        "species": "canis-familiaris",
    })).json()

    resp = await client.post("/v1/Immunization", json={
        "resourceType": "Immunization",
        "status": "completed",
        "vaccineCode": {"code": "rabies-1yr", "display": "Rabies 1 Year"},
        "subject": {"ref": f"Animal/{animal['id']}"},
        "occurrenceDateTime": "2026-05-17T10:00:00Z",
        "primarySource": True,
        "lotNumber": "LOT-2026-A",
        "expirationDate": "2027-05-17",
        "nextDueDate": "2027-05-17",
        "route": "intramuscular",
        "site": "right-hind-limb",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["vaccineCode"]["code"] == "rabies-1yr"
    assert body["nextDueDate"] == "2027-05-17"


@pytest.mark.asyncio
async def test_create_procedure(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Spot",
        "species": "canis-familiaris",
    })).json()

    resp = await client.post("/v1/Procedure", json={
        "resourceType": "Procedure",
        "status": "completed",
        "code": {"system": "http://snomed.info/sct", "code": "234027", "display": "Teeth cleaning"},
        "subject": {"ref": f"Animal/{animal['id']}"},
        "performedDateTime": "2026-05-17T11:00:00Z",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"]["display"] == "Teeth cleaning"


@pytest.mark.asyncio
async def test_create_location(client: AsyncClient):
    resp = await client.post("/v1/Location", json={
        "resourceType": "Location",
        "name": "Exam Room 3",
        "type": "exam-room",
        "mode": "instance",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Exam Room 3"


@pytest.mark.asyncio
async def test_create_appointment(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Pip",
        "species": "felis-catus",
    })).json()

    vet = (await client.post("/v1/Practitioner", json={
        "resourceType": "Practitioner",
        "name": {"family": "Osei", "suffix": "DVM"},
    })).json()

    resp = await client.post("/v1/Appointment", json={
        "resourceType": "Appointment",
        "status": "booked",
        "serviceType": [{"code": "wellness", "display": "Wellness exam"}],
        "subject": {"ref": f"Animal/{animal['id']}"},
        "practitioners": [{"actor": {"ref": f"Practitioner/{vet['id']}"}, "role": "attending"}],
        "start": "2026-06-01T09:00:00Z",
        "end": "2026-06-01T09:30:00Z",
        "comment": "Annual checkup",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "booked"
    assert body["subject"]["ref"] == f"Animal/{animal['id']}"


@pytest.mark.asyncio
async def test_appointment_search_by_subject(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Rex",
        "species": "canis-familiaris",
    })).json()
    animal_id = animal["id"]

    await client.post("/v1/Appointment", json={
        "resourceType": "Appointment",
        "status": "booked",
        "subject": {"ref": f"Animal/{animal_id}"},
        "start": "2026-07-01T10:00:00Z",
        "end": "2026-07-01T10:30:00Z",
    })
    resp = await client.get(f"/v1/Appointment?subject=Animal/{animal_id}")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
