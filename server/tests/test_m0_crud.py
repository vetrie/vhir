"""Coverage tests for M0 resource CRUD operations not exercised by workflow tests."""
import pytest
from httpx import AsyncClient


# ── Owner ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_owner_crud(client: AsyncClient):
    resp = await client.post("/v1/Owner", json={
        "resourceType": "Owner",
        "name": {"given": "Alice", "family": "Wong"},
        "telecom": [{"system": "email", "value": "alice@example.com"}],
    })
    assert resp.status_code == 201
    oid = resp.json()["id"]

    # Read
    r = await client.get(f"/v1/Owner/{oid}")
    assert r.status_code == 200
    assert r.json()["id"] == oid

    # Update
    u = await client.put(f"/v1/Owner/{oid}", json={
        "resourceType": "Owner",
        "name": {"given": "Alice", "family": "Wong-Chen"},
    })
    assert u.status_code == 200
    assert u.json()["name"]["family"] == "Wong-Chen"

    # Delete
    d = await client.delete(f"/v1/Owner/{oid}")
    assert d.status_code == 204

    assert (await client.get(f"/v1/Owner/{oid}")).status_code == 404


@pytest.mark.asyncio
async def test_owner_search(client: AsyncClient):
    await client.post("/v1/Owner", json={"resourceType": "Owner", "name": {"given": "Bob", "family": "Smith"}, "active": True})
    r = await client.get("/v1/Owner?active=true")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


# ── Practitioner ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_practitioner_crud(client: AsyncClient):
    resp = await client.post("/v1/Practitioner", json={
        "resourceType": "Practitioner",
        "name": {"given": "Carol", "family": "Kim", "suffix": "DVM"},
        "qualifications": [{"code": "DVM", "licenseNumber": "TX-DVM-99001"}],
    })
    assert resp.status_code == 201
    pid = resp.json()["id"]

    r = await client.get(f"/v1/Practitioner/{pid}")
    assert r.status_code == 200

    u = await client.put(f"/v1/Practitioner/{pid}", json={
        "resourceType": "Practitioner",
        "name": {"given": "Carol", "family": "Kim", "suffix": "DVM, PhD"},
    })
    assert u.status_code == 200

    d = await client.delete(f"/v1/Practitioner/{pid}")
    assert d.status_code == 204


# ── Organization ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_organization_crud(client: AsyncClient):
    resp = await client.post("/v1/Organization", json={
        "resourceType": "Organization",
        "name": "Valley Vet Hospital",
        "type": "referral-hospital",
    })
    assert resp.status_code == 201
    oid = resp.json()["id"]

    r = await client.get(f"/v1/Organization/{oid}")
    assert r.status_code == 200

    u = await client.put(f"/v1/Organization/{oid}", json={
        "resourceType": "Organization",
        "name": "Valley Veterinary Hospital",
        "type": "referral-hospital",
    })
    assert u.status_code == 200
    assert u.json()["name"] == "Valley Veterinary Hospital"


# ── Encounter ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_encounter_crud(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal", "name": "Pepper", "species": "felis-catus",
    })).json()

    resp = await client.post("/v1/Encounter", json={
        "resourceType": "Encounter",
        "status": "planned",
        "class": "outpatient",
        "subject": {"ref": f"Animal/{animal['id']}"},
    })
    assert resp.status_code == 201
    eid = resp.json()["id"]

    r = await client.get(f"/v1/Encounter/{eid}")
    assert r.status_code == 200

    u = await client.put(f"/v1/Encounter/{eid}", json={
        "resourceType": "Encounter",
        "status": "completed",
        "class": "outpatient",
        "subject": {"ref": f"Animal/{animal['id']}"},
    })
    assert u.status_code == 200
    assert u.json()["status"] == "completed"

    d = await client.delete(f"/v1/Encounter/{eid}")
    assert d.status_code == 204


# ── Observation ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_observation_crud(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal", "name": "Ginger", "species": "canis-familiaris",
    })).json()

    resp = await client.post("/v1/Observation", json={
        "resourceType": "Observation",
        "status": "final",
        "category": ["vital-signs"],
        "code": {"code": "body-weight", "display": "Body weight"},
        "subject": {"ref": f"Animal/{animal['id']}"},
        "valueQuantity": {"value": 5.2, "unit": "kg"},
    })
    assert resp.status_code == 201
    oid = resp.json()["id"]

    r = await client.get(f"/v1/Observation/{oid}")
    assert r.status_code == 200

    d = await client.delete(f"/v1/Observation/{oid}")
    assert d.status_code == 204


# ── Condition ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_condition_crud(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal", "name": "Coco", "species": "canis-familiaris",
    })).json()

    resp = await client.post("/v1/Condition", json={
        "resourceType": "Condition",
        "status": "active",
        "code": {"system": "urn:aaha:diagnostic-terms", "code": "DM-001", "display": "Diabetes mellitus"},
        "subject": {"ref": f"Animal/{animal['id']}"},
    })
    assert resp.status_code == 201
    cid = resp.json()["id"]

    r = await client.get(f"/v1/Condition/{cid}")
    assert r.status_code == 200

    u = await client.put(f"/v1/Condition/{cid}", json={
        "resourceType": "Condition",
        "status": "resolved",
        "code": {"system": "urn:aaha:diagnostic-terms", "code": "DM-001", "display": "Diabetes mellitus"},
        "subject": {"ref": f"Animal/{animal['id']}"},
    })
    assert u.status_code == 200
    assert u.json()["status"] == "resolved"


# ── MedicationRequest ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_medication_request_crud(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal", "name": "Kona", "species": "canis-familiaris",
    })).json()
    vet = (await client.post("/v1/Practitioner", json={
        "resourceType": "Practitioner", "name": {"family": "Park", "suffix": "DVM"},
    })).json()

    resp = await client.post("/v1/MedicationRequest", json={
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medication": {"name": "Prednisone 5mg", "form": "tablet"},
        "subject": {"ref": f"Animal/{animal['id']}"},
        "requester": {"ref": f"Practitioner/{vet['id']}"},
    })
    assert resp.status_code == 201
    rid = resp.json()["id"]

    r = await client.get(f"/v1/MedicationRequest/{rid}")
    assert r.status_code == 200

    u = await client.put(f"/v1/MedicationRequest/{rid}", json={
        "resourceType": "MedicationRequest",
        "status": "completed",
        "intent": "order",
        "medication": {"name": "Prednisone 5mg", "form": "tablet"},
        "subject": {"ref": f"Animal/{animal['id']}"},
        "requester": {"ref": f"Practitioner/{vet['id']}"},
    })
    assert u.status_code == 200
    assert u.json()["status"] == "completed"


# ── Not-found paths ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_not_found_paths(client: AsyncClient):
    for path in ["/v1/Owner/NOTEXIST", "/v1/Practitioner/NOTEXIST",
                 "/v1/Organization/NOTEXIST", "/v1/Encounter/NOTEXIST",
                 "/v1/Observation/NOTEXIST", "/v1/Condition/NOTEXIST",
                 "/v1/MedicationRequest/NOTEXIST"]:
        assert (await client.get(path)).status_code == 404


@pytest.mark.asyncio
async def test_optimistic_concurrency_resources(client: AsyncClient):
    """PUT with stale ETag returns 412 for M0 resources."""
    owner = (await client.post("/v1/Owner", json={
        "resourceType": "Owner", "name": {"given": "Test", "family": "User"},
    })).json()
    oid = owner["id"]

    resp = await client.put(f"/v1/Owner/{oid}",
        json={"resourceType": "Owner", "name": {"given": "Test", "family": "User"}},
        headers={"If-Match": '"999"'},
    )
    assert resp.status_code == 412
