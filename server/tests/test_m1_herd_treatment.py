"""Tests for herd-level MedicationAdministration — core VHIR differentiator."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_herd_medication_administration(client: AsyncClient):
    """Administer drug to a Group with per-member completion tracking."""
    # Create three cattle
    animals = []
    for tag in ["840111111111111", "840111111111112", "840111111111113"]:
        r = await client.post("/v1/Animal", json={
            "resourceType": "Animal",
            "species": "bos-taurus",
            "identifiers": [{"type": "usda-840", "value": tag}],
        })
        assert r.status_code == 201
        animals.append(r.json()["id"])

    # Create a herd group
    grp = await client.post("/v1/Group", json={
        "resourceType": "Group",
        "name": "Pen 7",
        "type": "animal",
        "productionPurpose": "beef",
        "members": [{"ref": f"Animal/{aid}"} for aid in animals],
    })
    assert grp.status_code == 201
    grp_id = grp.json()["id"]

    # Create vet
    vet = await client.post("/v1/Practitioner", json={
        "resourceType": "Practitioner",
        "name": {"family": "Nguyen", "suffix": "DVM"},
    })
    vet_id = vet.json()["id"]

    # Administer penicillin to the whole group
    rx_resp = await client.post("/v1/MedicationAdministration", json={
        "resourceType": "MedicationAdministration",
        "status": "completed",
        "medication": {"name": "Penicillin G 300,000 IU/mL", "form": "injectable"},
        "subject": {"ref": f"Group/{grp_id}"},
        "performer": [{"ref": f"Practitioner/{vet_id}"}],
        "effectiveDateTime": "2026-05-17T09:00:00Z",
        "dosage": {"route": "intramuscular", "text": "3 mL/100 lb BW"},
        "withdrawalEnds": {"meat": "2026-06-01", "milk": "2026-05-20"},
        "memberCompletion": [
            {"animal": f"Animal/{animals[0]}", "status": "completed", "effectiveDateTime": "2026-05-17T09:01:00Z"},
            {"animal": f"Animal/{animals[1]}", "status": "completed", "effectiveDateTime": "2026-05-17T09:04:00Z"},
            {"animal": f"Animal/{animals[2]}", "status": "refused"},
        ],
    })
    assert rx_resp.status_code == 201
    body = rx_resp.json()

    assert body["subject"]["ref"] == f"Group/{grp_id}"
    assert body["withdrawalEnds"]["meat"] == "2026-06-01"
    assert body["withdrawalEnds"]["milk"] == "2026-05-20"
    assert len(body["memberCompletion"]) == 3
    assert body["memberCompletion"][2]["status"] == "refused"

    # Search by subject group
    search = await client.get(f"/v1/MedicationAdministration?subject=Group/{grp_id}")
    assert search.status_code == 200
    assert search.json()["total"] == 1
