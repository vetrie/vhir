"""Tests for MedicationDispense, Schedule, Slot resources."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_medication_dispense(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Buddy",
        "species": "canis-familiaris",
    })).json()

    vet = (await client.post("/v1/Practitioner", json={
        "resourceType": "Practitioner",
        "name": {"family": "Lopez", "suffix": "DVM"},
    })).json()

    rx = (await client.post("/v1/MedicationRequest", json={
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medication": {"name": "Carprofen 25mg", "form": "chewable tablet"},
        "subject": {"ref": f"Animal/{animal['id']}"},
        "requester": {"ref": f"Practitioner/{vet['id']}"},
        "dosageInstruction": [{"text": "1 tab BID with food"}],
    })).json()

    resp = await client.post("/v1/MedicationDispense", json={
        "resourceType": "MedicationDispense",
        "status": "completed",
        "medication": {"name": "Carprofen 25mg", "form": "chewable tablet"},
        "subject": {"ref": f"Animal/{animal['id']}"},
        "authorizingPrescription": {"ref": f"MedicationRequest/{rx['id']}"},
        "quantity": {"value": 30, "unit": "tablets"},
        "daysSupply": 15,
        "whenHandedOver": "2026-05-17T14:00:00Z",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["quantity"]["value"] == 30
    assert body["daysSupply"] == 15

    # Search by authorizing prescription
    search = await client.get(f"/v1/MedicationDispense?authorizingPrescription=MedicationRequest/{rx['id']}")
    assert search.status_code == 200
    assert search.json()["total"] == 1


@pytest.mark.asyncio
async def test_schedule_and_slot(client: AsyncClient):
    vet = (await client.post("/v1/Practitioner", json={
        "resourceType": "Practitioner",
        "name": {"family": "Chen", "suffix": "DVM"},
    })).json()

    schedule = (await client.post("/v1/Schedule", json={
        "resourceType": "Schedule",
        "actor": [{"ref": f"Practitioner/{vet['id']}"}],
        "planningHorizon": {"start": "2026-06-01", "end": "2026-06-30"},
        "active": True,
        "serviceType": [{"code": "wellness"}],
    })).json()
    assert schedule["meta"]["version"] == 1

    slot = (await client.post("/v1/Slot", json={
        "resourceType": "Slot",
        "schedule": {"ref": f"Schedule/{schedule['id']}"},
        "status": "free",
        "start": "2026-06-01T09:00:00Z",
        "end": "2026-06-01T09:30:00Z",
    })).json()
    assert slot["status"] == "free"

    # Search slot by schedule
    resp = await client.get(f"/v1/Slot?schedule=Schedule/{schedule['id']}")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
