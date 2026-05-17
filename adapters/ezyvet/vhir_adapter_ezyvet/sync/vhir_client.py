"""Thin async client for upserting resources into the VHIR server."""
from __future__ import annotations

from typing import Any

import httpx

from vhir_adapter_ezyvet.config import settings


class VHIRClient:
    """Async VHIR REST client with idempotent upsert via ezyvet-id identifier search."""

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self._base_url = (base_url or settings.vhir_base_url).rstrip("/")
        self._token = token or settings.vhir_token
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> VHIRClient:
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(30.0),
            headers={"Authorization": f"Bearer {self._token}"} if self._token else {},
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._http:
            await self._http.aclose()

    async def upsert(self, resource_type: str, payload: dict[str, Any], ezyvet_id: str) -> dict[str, Any]:
        """Create or update a VHIR resource, keyed by its ezyvet-id identifier."""
        assert self._http is not None
        # Search for an existing resource by ezyvet-id
        search = await self._http.get(
            f"/v1/{resource_type}",
            params={"identifier": f"ezyvet-id|{ezyvet_id}"},
        )
        search.raise_for_status()
        bundle = search.json()
        entries = bundle.get("entry", [])

        if entries:
            rid = entries[0]["resource"]["id"]
            resp = await self._http.put(f"/v1/{resource_type}/{rid}", json=payload)
        else:
            resp = await self._http.post(f"/v1/{resource_type}", json=payload)

        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
