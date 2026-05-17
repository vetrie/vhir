"""Tests for EzyVetClient — OAuth2 token handling, rate limiting, retry."""
import pytest
import httpx
import respx

from vhir_adapter_ezyvet.client import EzyVetClient, _TokenBucket, _TokenCache


# ── TokenCache ─────────────────────────────────────────────────────────────────

def test_token_cache_miss_on_empty():
    cache = _TokenCache()
    assert cache.get() is None


def test_token_cache_hit():
    cache = _TokenCache()
    cache.set("tok123", 3600)
    assert cache.get() == "tok123"


def test_token_cache_expired():
    import time
    cache = _TokenCache()
    cache.set("expired", 1)
    cache._expires_at = time.monotonic() - 1  # force expiry
    assert cache.get() is None


# ── TokenBucket ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_bucket_allows_burst():
    bucket = _TokenBucket(rate=5, window=1.0)
    # Should not raise or sleep for the first 5 requests
    for _ in range(5):
        await bucket.acquire()


# ── EzyVetClient ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_client_fetches_token_on_first_request(mock_ezyvet):
    mock_ezyvet.get("/v1/animal").mock(
        return_value=httpx.Response(200, json={"items": [], "meta": {"total": 0}})
    )
    async with EzyVetClient(base_url="https://api.ezyvet.com", client_id="id", client_secret="sec", partner_id="p") as client:
        result = await client.get("/v1/animal")
    assert result == {"items": [], "meta": {"total": 0}}


@pytest.mark.asyncio
async def test_client_reuses_cached_token(mock_ezyvet):
    mock_ezyvet.get("/v1/animal").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    async with EzyVetClient(base_url="https://api.ezyvet.com", client_id="id", client_secret="sec", partner_id="p") as client:
        await client.get("/v1/animal")
        await client.get("/v1/animal")
    # Token endpoint should only have been called once
    token_calls = [
        call for call in mock_ezyvet.calls
        if "/oauth/access_token" in str(call.request.url)
    ]
    assert len(token_calls) == 1


@pytest.mark.asyncio
async def test_client_refreshes_token_on_401(mock_ezyvet):
    first = True

    def side_effect(request, route):
        nonlocal first
        if first:
            first = False
            return httpx.Response(401, json={"error": "unauthorized"})
        return httpx.Response(200, json={"items": []})

    mock_ezyvet.get("/v1/animal").mock(side_effect=side_effect)
    async with EzyVetClient(base_url="https://api.ezyvet.com", client_id="id", client_secret="sec", partner_id="p") as client:
        result = await client.get("/v1/animal")
    assert result == {"items": []}


@pytest.mark.asyncio
async def test_list_all_paginates(mock_ezyvet):
    page_1 = {"items": [{"id": "1"}] * 3}
    page_2 = {"items": [{"id": "2"}] * 2}

    call_count = 0

    def paginate(request, route):
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json=page_1 if call_count == 1 else page_2)

    mock_ezyvet.get("/v1/animal").mock(side_effect=paginate)
    async with EzyVetClient(base_url="https://api.ezyvet.com", client_id="id", client_secret="sec", partner_id="p") as client:
        items = await client.list_all("animal", limit=3)
    assert len(items) == 5
