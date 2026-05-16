"""Integration tests — complete clinical workflow."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_companion_animal_visit(client: AsyncClient):
    """Full GP visit: owner → animal → encounter → observation → condition → med rx."""
    # 1. Create owner
    owner_resp = await client.post("/v1/Owner", json={
        "resourceType": "Owner",
        "name": {"given": "John", "family": "Smith"},
        "telecom": [{"system": "email", "value": "john@example.com"}],
    })
    assert owner_resp.status_code == 201
    owner_id = owner_resp.json()["id"]

    # 2. Create practitioner
    vet_resp = await client.post("/v1/Practitioner", json={
        "resourceType": "Practitioner",
        "name": {"given": "Jane", "family": "Doe", "suffix": "DVM"},
        "qualifications": [{"code": "DVM", "licenseNumber": "CA-DVM-99999"}],
    })
    assert vet_resp.status_code == 201
    vet_id = vet_resp.json()["id"]

    # 3. Create animal
    animal_resp = await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Mochi",
        "species": "felis-catus",
        "sex": "female",
        "neuterStatus": "spayed",
        "identifiers": [{"type": "microchip-iso", "value": "956000011111111"}],
        "owners": [{"ref": f"Owner/{owner_id}", "role": "primary"}],
    })
    assert animal_resp.status_code == 201
    animal_id = animal_resp.json()["id"]
    assert animal_resp.json()["owners"][0]["ref"] == f"Owner/{owner_id}"

    # 4. Create encounter
    enc_resp = await client.post("/v1/Encounter", json={
        "resourceType": "Encounter",
        "status": "completed",
        "class": "outpatient",
        "subject": {"ref": f"Animal/{animal_id}"},
        "practitioners": [{"practitioner": {"ref": f"Practitioner/{vet_id}"}, "role": "attending"}],
        "reasonText": "Vomiting x 2 days",
    })
    assert enc_resp.status_code == 201
    enc_id = enc_resp.json()["id"]

    # 5. Record vitals
    obs_resp = await client.post("/v1/Observation", json={
        "resourceType": "Observation",
        "status": "final",
        "category": ["vital-signs"],
        "code": {"code": "body-weight", "display": "Body weight"},
        "subject": {"ref": f"Animal/{animal_id}"},
        "encounter": {"ref": f"Encounter/{enc_id}"},
        "valueQuantity": {"value": 4.2, "unit": "kg"},
    })
    assert obs_resp.status_code == 201

    # 6. Diagnose
    cond_resp = await client.post("/v1/Condition", json={
        "resourceType": "Condition",
        "status": "active",
        "code": {"system": "urn:aaha:diagnostic-terms", "code": "GI-001", "display": "Gastroenteritis"},
        "subject": {"ref": f"Animal/{animal_id}"},
        "encounter": {"ref": f"Encounter/{enc_id}"},
    })
    assert cond_resp.status_code == 201

    # 7. Prescribe medication
    rx_resp = await client.post("/v1/MedicationRequest", json={
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medication": {"name": "Metronidazole 250mg", "form": "tablet"},
        "subject": {"ref": f"Animal/{animal_id}"},
        "requester": {"ref": f"Practitioner/{vet_id}"},
        "dosageInstruction": [{"text": "1 tab BID x 7 days", "route": "oral"}],
    })
    assert rx_resp.status_code == 201

    # 8. Verify search retrieves all linked records
    conds = await client.get(f"/v1/Condition?subject=Animal/{animal_id}")
    assert conds.json()["total"] == 1

    meds = await client.get(f"/v1/MedicationRequest?subject=Animal/{animal_id}")
    assert meds.json()["total"] == 1

    obs = await client.get(f"/v1/Observation?encounter=Encounter/{enc_id}")
    assert obs.json()["total"] == 1


@pytest.mark.asyncio
async def test_food_animal_medication_with_withdrawal(client: AsyncClient):
    """Food-animal Rx with withdrawal periods — core VHIR differentiator."""
    animal_resp = await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "species": "bos-taurus",
        "identifiers": [{"type": "usda-840", "value": "840123456789012"}],
    })
    animal_id = animal_resp.json()["id"]

    vet_resp = await client.post("/v1/Practitioner", json={
        "resourceType": "Practitioner",
        "name": {"family": "Kovacs", "suffix": "DVM"},
    })
    vet_id = vet_resp.json()["id"]

    rx_resp = await client.post("/v1/MedicationRequest", json={
        "resourceType": "MedicationRequest",
        "status": "active",
        "intent": "order",
        "medication": {"name": "Pirlimycin HCl 50mg/mL", "form": "intramammary infusion"},
        "subject": {"ref": f"Animal/{animal_id}"},
        "requester": {"ref": f"Practitioner/{vet_id}"},
        "withdrawal": {"milkHours": 36, "meatHours": 720},
        "extraLabel": False,
        "dosageInstruction": [{"route": "intramammary", "text": "1 tube per quarter, once daily x 2d"}],
    })
    assert rx_resp.status_code == 201
    rx = rx_resp.json()
    assert rx["withdrawal"]["milkHours"] == 36
    assert rx["withdrawal"]["meatHours"] == 720
    assert rx["extraLabel"] is False


@pytest.mark.asyncio
async def test_capabilities_endpoint(client: AsyncClient):
    resp = await client.get("/v1/metadata")
    assert resp.status_code == 200
    body = resp.json()
    assert body["resourceType"] == "CapabilityStatement"
    resource_types = [r["type"] for r in body["rest"][0]["resource"]]
    assert "Animal" in resource_types
    assert "MedicationRequest" in resource_types
