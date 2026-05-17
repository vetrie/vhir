"""Tests for VHIRClient upsert logic."""
import pytest
import httpx
import respx

from vhir_adapter_ezyvet.sync.vhir_client import VHIRClient

BASE = "http://localhost:8000"


@pytest.mark.asyncio
async def test_upsert_creates_when_not_found():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/v1/Animal").mock(
            return_value=httpx.Response(200, json={"entry": []})
        )
        mock.post("/v1/Animal").mock(
            return_value=httpx.Response(201, json={"id": "new-id", "resourceType": "Animal"})
        )
        async with VHIRClient(base_url=BASE, token="tok") as vhir:
            result = await vhir.upsert("Animal", {"resourceType": "Animal", "species": "canine"}, "101")
    assert result["id"] == "new-id"


@pytest.mark.asyncio
async def test_upsert_updates_when_existing():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/v1/Animal").mock(
            return_value=httpx.Response(200, json={
                "entry": [{"resource": {"id": "existing-id", "resourceType": "Animal"}}]
            })
        )
        mock.put("/v1/Animal/existing-id").mock(
            return_value=httpx.Response(200, json={"id": "existing-id", "resourceType": "Animal"})
        )
        async with VHIRClient(base_url=BASE, token="tok") as vhir:
            result = await vhir.upsert("Animal", {"resourceType": "Animal", "species": "feline"}, "101")
    assert result["id"] == "existing-id"


@pytest.mark.asyncio
async def test_upsert_raises_on_server_error():
    with respx.mock(base_url=BASE) as mock:
        mock.get("/v1/Animal").mock(
            return_value=httpx.Response(500, json={"error": "server error"})
        )
        async with VHIRClient(base_url=BASE, token="tok") as vhir:
            with pytest.raises(httpx.HTTPStatusError):
                await vhir.upsert("Animal", {}, "999")
