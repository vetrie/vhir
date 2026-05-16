"""Tests for the Animal resource — CRUD + search."""
import pytest
from httpx import AsyncClient


ANIMAL_BASE = {
    "resourceType": "Animal",
    "name": "Biscuit",
    "species": "canis-familiaris",
    "breed": "Labrador Retriever",
    "sex": "male",
    "neuterStatus": "neutered",
    "birthDate": "2019-03-15",
    "weightKg": 32.5,
    "identifiers": [{"type": "microchip-iso", "value": "956000004287442"}],
}


@pytest.mark.asyncio
async def test_create_animal(client: AsyncClient):
    resp = await client.post("/v1/Animal", json=ANIMAL_BASE)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Biscuit"
    assert body["species"] == "canis-familiaris"
    assert "id" in body
    assert body["meta"]["version"] == 1
    assert resp.headers["ETag"] == '"1"'


@pytest.mark.asyncio
async def test_read_animal(client: AsyncClient):
    create_resp = await client.post("/v1/Animal", json=ANIMAL_BASE)
    rid = create_resp.json()["id"]

    resp = await client.get(f"/v1/Animal/{rid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == rid
    assert resp.headers["ETag"] == '"1"'


@pytest.mark.asyncio
async def test_read_not_found(client: AsyncClient):
    resp = await client.get("/v1/Animal/01NONEXISTENT0000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_animal(client: AsyncClient):
    create_resp = await client.post("/v1/Animal", json=ANIMAL_BASE)
    rid = create_resp.json()["id"]

    updated = {**ANIMAL_BASE, "weightKg": 30.0, "note": "Lost 2.5 kg — good progress"}
    resp = await client.put(f"/v1/Animal/{rid}", json=updated)
    assert resp.status_code == 200
    body = resp.json()
    assert body["weightKg"] == 30.0
    assert body["meta"]["version"] == 2


@pytest.mark.asyncio
async def test_optimistic_concurrency(client: AsyncClient):
    create_resp = await client.post("/v1/Animal", json=ANIMAL_BASE)
    rid = create_resp.json()["id"]

    # Update with wrong ETag
    resp = await client.put(
        f"/v1/Animal/{rid}",
        json={**ANIMAL_BASE, "weightKg": 29.0},
        headers={"If-Match": '"999"'},
    )
    assert resp.status_code == 412


@pytest.mark.asyncio
async def test_delete_animal(client: AsyncClient):
    create_resp = await client.post("/v1/Animal", json=ANIMAL_BASE)
    rid = create_resp.json()["id"]

    del_resp = await client.delete(f"/v1/Animal/{rid}")
    assert del_resp.status_code == 204

    # Deleted resource should 404
    get_resp = await client.get(f"/v1/Animal/{rid}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_search_by_species(client: AsyncClient):
    await client.post("/v1/Animal", json=ANIMAL_BASE)
    resp = await client.get("/v1/Animal?species=canis-familiaris")
    assert resp.status_code == 200
    body = resp.json()
    assert body["resourceType"] == "Bundle"
    assert body["type"] == "searchset"
    assert body["total"] >= 1
    assert all(e["resource"]["species"] == "canis-familiaris" for e in body["entry"])


@pytest.mark.asyncio
async def test_search_by_microchip(client: AsyncClient):
    await client.post("/v1/Animal", json={**ANIMAL_BASE, "identifiers": [{"type": "microchip-iso", "value": "956000099999999"}]})
    resp = await client.get("/v1/Animal?identifier=microchip-iso|956000099999999")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    # All returned animals should have that chip
    chips = [
        ident["value"]
        for e in body["entry"]
        for ident in e["resource"]["identifiers"]
        if ident["type"] == "microchip-iso"
    ]
    assert "956000099999999" in chips


@pytest.mark.asyncio
async def test_search_by_name_prefix(client: AsyncClient):
    await client.post("/v1/Animal", json={**ANIMAL_BASE, "name": "Caramel"})
    resp = await client.get("/v1/Animal?name=cara")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_search_pagination(client: AsyncClient):
    for i in range(5):
        await client.post("/v1/Animal", json={**ANIMAL_BASE, "name": f"TestDog{i}"})
    resp = await client.get("/v1/Animal?_count=2&_offset=0&species=canis-familiaris")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["entry"]) <= 2
