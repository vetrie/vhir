"""ezyVet API client — OAuth2 client_credentials, 60 req/min rate limiting, retry."""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from vhir_adapter_ezyvet.config import settings

_RATE_LIMIT = 60  # requests per minute
_WINDOW = 60.0    # seconds


class _TokenBucket:
    """Simple token-bucket enforcing _RATE_LIMIT requests per _WINDOW seconds."""

    def __init__(self, rate: int = _RATE_LIMIT, window: float = _WINDOW) -> None:
        self._rate = rate
        self._window = window
        self._tokens = float(rate)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(
                self._rate,
                self._tokens + elapsed * (self._rate / self._window),
            )
            self._last_refill = now
            if self._tokens < 1:
                wait = (1 - self._tokens) * (self._window / self._rate)
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1


class _TokenCache:
    """In-memory OAuth2 token cache with expiry check."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    def get(self) -> str | None:
        if self._access_token and time.monotonic() < self._expires_at - 30:
            return self._access_token
        return None

    def set(self, token: str, expires_in: int) -> None:
        self._access_token = token
        self._expires_at = time.monotonic() + expires_in


class EzyVetClient:
    """Async HTTP client for the ezyVet REST API v1."""

    def __init__(
        self,
        base_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        partner_id: str | None = None,
    ) -> None:
        self._base_url = (base_url or settings.base_url).rstrip("/")
        self._client_id = client_id or settings.client_id
        self._client_secret = client_secret or settings.client_secret
        self._partner_id = partner_id or settings.partner_id
        self._bucket = _TokenBucket()
        self._token_cache = _TokenCache()
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> EzyVetClient:
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(30.0),
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._http:
            await self._http.aclose()

    # ── Auth ───────────────────────────────────────────────────────────────────

    async def _fetch_token(self) -> str:
        assert self._http is not None
        resp = await self._http.post(
            "/v1/oauth/access_token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "partner_id": self._partner_id,
            },
        )
        resp.raise_for_status()
        payload = resp.json()
        token: str = payload["access_token"]
        expires_in: int = int(payload.get("expires_in", 3600))
        self._token_cache.set(token, expires_in)
        return token

    async def _get_token(self) -> str:
        cached = self._token_cache.get()
        if cached:
            return cached
        return await self._fetch_token()

    # ── Request dispatch ───────────────────────────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        assert self._http is not None
        await self._bucket.acquire()
        token = await self._get_token()

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            stop=stop_after_attempt(4),
            reraise=True,
        ):
            with attempt:
                resp = await self._http.request(
                    method,
                    path,
                    headers={"Authorization": f"Bearer {token}"},
                    **kwargs,
                )
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", "5"))
                    await asyncio.sleep(retry_after)
                    raise httpx.TransportError("rate limited")
                if resp.status_code == 401:
                    # Force token refresh and retry once
                    self._token_cache._access_token = None
                    token = await self._fetch_token()
                    resp = await self._http.request(
                        method,
                        path,
                        headers={"Authorization": f"Bearer {token}"},
                        **kwargs,
                    )
                resp.raise_for_status()
                return resp.json()

    async def get(self, path: str, **params: Any) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: Any) -> Any:
        return await self._request("POST", path, json=json)

    async def patch(self, path: str, json: Any) -> Any:
        return await self._request("PATCH", path, json=json)

    # ── Paginated list helper ──────────────────────────────────────────────────

    async def list_all(
        self,
        resource: str,
        *,
        limit: int = 100,
        modified_since: str | None = None,
        **extra_params: Any,
    ) -> list[dict[str, Any]]:
        """Fetch all pages for a resource, yielding a flat list."""
        results: list[dict[str, Any]] = []
        page = 0
        params: dict[str, Any] = {"limit": limit, "offset": 0, **extra_params}
        if modified_since:
            params["modified_since"] = modified_since
        while True:
            params["offset"] = page * limit
            data = await self.get(f"/v1/{resource}", **params)
            items = data.get("items", [])
            results.extend(items)
            if len(items) < limit:
                break
            page += 1
        return results
