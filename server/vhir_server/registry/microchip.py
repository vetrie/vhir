"""Federated microchip lookup broker.

The reference implementation ships an in-process stub that:
1. Searches the local VHIR Animal table for a matching identifier.
2. Falls back to a stub response simulating the AAHA petmicrochiplookup.org broker.

A production deployment would swap the broker backend via dependency injection.
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from vhir_server.auth.smart import TokenPayload, require_scope
from vhir_server.storage.database import get_db
from vhir_server.storage.repository import ResourceRepository

_ISO_PATTERN = re.compile(r"^\d{15}$")

microchip_router = APIRouter(tags=["System Operations"])


class MicrochipLookupRequest(BaseModel):
    chipId: str


class MicrochipLookupResponse(BaseModel):
    found: bool
    localAnimal: str | None = None
    registry: dict[str, Any] | None = None
    registryContact: dict[str, Any] | None = None
    lastUpdated: str | None = None
    broker: str | None = None


@microchip_router.post("/$lookup-microchip", response_model=MicrochipLookupResponse)
async def lookup_microchip(
    body: MicrochipLookupRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    _token: TokenPayload = Depends(require_scope("Animal", "read")),
) -> MicrochipLookupResponse:
    chip_id = body.chipId.strip()

    if not chip_id:
        raise HTTPException(400, "chipId is required")

    # 1. Search locally for ISO-15-digit chip
    identifier_query = f"microchip-iso|{chip_id}" if _ISO_PATTERN.match(chip_id) else chip_id
    animals, total = await ResourceRepository("Animal", db).search({"identifier": identifier_query})

    if total > 0:
        animal = animals[0]
        return MicrochipLookupResponse(
            found=True,
            localAnimal=f"Animal/{animal['id']}",
        )

    # 2. Stub broker response (simulates petmicrochiplookup.org)
    if _ISO_PATTERN.match(chip_id):
        return MicrochipLookupResponse(
            found=False,
            broker="https://petmicrochiplookup.org",
            registryContact={
                "system": "url",
                "value": "https://petmicrochiplookup.org",
            },
        )

    return MicrochipLookupResponse(found=False)
