"""Tests for Device resource (microchips, EIDs, wearables)."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_microchip_device(client: AsyncClient):
    animal = (await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Luna",
        "species": "felis-catus",
    })).json()

    resp = await client.post("/v1/Device", json={
        "resourceType": "Device",
        "type": "microchip-iso",
        "status": "active",
        "identifiers": [{"type": "microchip-iso", "value": "956000088888888"}],
        "subject": {"ref": f"Animal/{animal['id']}"},
        "manufacturer": "HomeAgain",
        "model": "Bio-Bond",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "microchip-iso"
    assert body["identifiers"][0]["value"] == "956000088888888"


@pytest.mark.asyncio
async def test_search_device_by_identifier(client: AsyncClient):
    await client.post("/v1/Device", json={
        "resourceType": "Device",
        "type": "microchip-iso",
        "identifiers": [{"type": "microchip-iso", "value": "956000077777777"}],
    })
    resp = await client.get("/v1/Device?identifier=microchip-iso|956000077777777")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_lookup_microchip_local(client: AsyncClient):
    """$lookup-microchip finds a locally registered animal."""
    # Register animal with chip
    await client.post("/v1/Animal", json={
        "resourceType": "Animal",
        "name": "Max",
        "species": "canis-familiaris",
        "identifiers": [{"type": "microchip-iso", "value": "956000055555555"}],
    })
    resp = await client.post("/v1/$lookup-microchip", json={"chipId": "956000055555555"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is True
    assert "Animal/" in body["localAnimal"]


@pytest.mark.asyncio
async def test_lookup_microchip_not_found(client: AsyncClient):
    """$lookup-microchip returns stub broker info for unknown ISO chip."""
    resp = await client.post("/v1/$lookup-microchip", json={"chipId": "999999999999999"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is False
    assert body["broker"] is not None
