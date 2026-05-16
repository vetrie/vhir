"""Tests for InsuranceClaim resource — pre-auth and post-service flows."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_insurance_claim_pre_auth_flow(client: AsyncClient):
    """Simulate Trupanion VetDirectPay pre-authorization workflow."""
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Bruno",
        "species": "canis-familiaris",
        "breed": "German Shepherd",
    })).json()

    org = (await client.post("/v1/Organization", json={
        "resourceType": "Organization",
        "name": "Trupanion",
        "type": "insurer",
    })).json()

    # Pre-authorization request
    resp = await client.post("/v1/InsuranceClaim", json={
        "resourceType": "InsuranceClaim",
        "status": "active",
        "type": "professional",
        "subject": {"ref": f"Animal/{animal['id']}"},
        "insurer": {"ref": f"Organization/{org['id']}"},
        "policyNumber": "TRU-1234567",
        "claimType": "pre-auth",
        "priority": "normal",
        "preAuth": {
            "requestedAt": "2026-05-17T08:00:00Z",
            "estimatedAmount": 3500.00,
            "currency": "USD",
            "status": "pending",
        },
        "item": [
            {"sequence": 1, "code": {"code": "surgery", "display": "TPLO surgery"}, "net": 3500.00},
        ],
        "totalAmount": 3500.00,
        "currency": "USD",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["preAuth"]["estimatedAmount"] == 3500.00
    assert body["policyNumber"] == "TRU-1234567"
    claim_id = body["id"]

    # Update with pre-auth response
    update_body = {**body}
    update_body.pop("id", None)
    update_body.pop("meta", None)
    update_body["status"] = "active"
    update_body["preAuth"]["status"] = "approved"
    update_body["preAuth"]["authNumber"] = "AUTH-99887766"
    update_body["preAuth"]["approvedAmount"] = 3200.00

    upd = await client.put(f"/v1/InsuranceClaim/{claim_id}", json=update_body)
    assert upd.status_code == 200
    assert upd.json()["preAuth"]["authNumber"] == "AUTH-99887766"


@pytest.mark.asyncio
async def test_insurance_claim_post_service(client: AsyncClient):
    """Simulate post-service claim (Nationwide / Pets Best style)."""
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Luna",
        "species": "felis-catus",
    })).json()

    resp = await client.post("/v1/InsuranceClaim", json={
        "resourceType": "InsuranceClaim",
        "status": "submitted",
        "type": "professional",
        "subject": {"ref": f"Animal/{animal['id']}"},
        "policyNumber": "NW-987654",
        "claimType": "post-service",
        "item": [
            {"sequence": 1, "code": {"code": "exam", "display": "Office visit"}, "net": 85.00},
            {"sequence": 2, "code": {"code": "lab", "display": "Blood panel"}, "net": 215.00},
        ],
        "totalAmount": 300.00,
        "currency": "USD",
        "submission": {
            "submittedAt": "2026-05-17T15:00:00Z",
            "claimedAmount": 300.00,
            "currency": "USD",
        },
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["submission"]["claimedAmount"] == 300.00
    assert len(body["item"]) == 2


@pytest.mark.asyncio
async def test_insurance_claim_adjudication(client: AsyncClient):
    """Full cycle: submit → adjudicate → paid."""
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Milo",
        "species": "canis-familiaris",
    })).json()

    claim = (await client.post("/v1/InsuranceClaim", json={
        "resourceType": "InsuranceClaim",
        "status": "submitted",
        "type": "professional",
        "subject": {"ref": f"Animal/{animal['id']}"},
        "policyNumber": "PB-112233",
        "totalAmount": 500.00,
    })).json()
    claim_id = claim["id"]

    # Adjudication update
    adj_body = {**claim}
    adj_body.pop("id", None)
    adj_body.pop("meta", None)
    adj_body["status"] = "completed"
    adj_body["adjudication"] = {
        "adjudicatedAt": "2026-05-20T10:00:00Z",
        "outcome": "approved",
        "approvedAmount": 500.00,
        "deductibleApplied": 50.00,
        "coinsuranceApplied": 45.00,
        "paidAmount": 405.00,
        "eobNumber": "EOB-2026-001234",
    }

    upd = await client.put(f"/v1/InsuranceClaim/{claim_id}", json=adj_body)
    assert upd.status_code == 200
    adj = upd.json()["adjudication"]
    assert adj["paidAmount"] == 405.00
    assert adj["outcome"] == "approved"


@pytest.mark.asyncio
async def test_insurance_claim_search(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Ziggy",
        "species": "canis-familiaris",
    })).json()
    animal_id = animal["id"]

    await client.post("/v1/InsuranceClaim", json={
        "resourceType": "InsuranceClaim",
        "status": "active",
        "subject": {"ref": f"Animal/{animal_id}"},
        "totalAmount": 100.00,
    })

    resp = await client.get(f"/v1/InsuranceClaim?subject=Animal/{animal_id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
