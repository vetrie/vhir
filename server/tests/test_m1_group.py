"""Tests for Group resource (herd/flock/litter)."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient):
    resp = await client.post("/v1/Group", json={
        "resourceType": "Group",
        "name": "North Pasture Herd",
        "type": "animal",
        "productionPurpose": "dairy",
        "premisesId": "US-PIN-123456",
        "quantity": 42,
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "North Pasture Herd"
    assert body["productionPurpose"] == "dairy"
    assert "id" in body


@pytest.mark.asyncio
async def test_group_with_members(client: AsyncClient):
    # Create two animals
    a1 = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "species": "bos-taurus",
        "identifiers": [{"type": "usda-840", "value": "840000000000001"}],
    })).json()
    a2 = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "species": "bos-taurus",
        "identifiers": [{"type": "usda-840", "value": "840000000000002"}],
    })).json()

    resp = await client.post("/v1/Group", json={
        "resourceType": "Group",
        "name": "Dairy Herd 1",
        "type": "animal",
        "productionPurpose": "dairy",
        "members": [
            {"ref": f"Animal/{a1['id']}"},
            {"ref": f"Animal/{a2['id']}"},
        ],
    })
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["members"]) == 2


@pytest.mark.asyncio
async def test_search_group_by_production_purpose(client: AsyncClient):
    await client.post("/v1/Group", json={
        "resourceType": "Group",
        "name": "Beef Lot A",
        "type": "animal",
        "productionPurpose": "beef",
    })
    resp = await client.get("/v1/Group?productionPurpose=beef")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all(e["resource"]["productionPurpose"] == "beef" for e in body["entry"])
