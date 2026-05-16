"""Shared helpers for resource routers."""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from vhir_server.config import settings
from vhir_server.core.models import Bundle, BundleEntry

VHIR_MEDIA_TYPE = "application/vhir+json"


def resource_response(body: dict[str, Any], status_code: int = 200) -> Response:
    version = body.get("meta", {}).get("version", 1)
    return Response(
        content=json.dumps(body, default=str),
        status_code=status_code,
        media_type=VHIR_MEDIA_TYPE,
        headers={"ETag": f'"{version}"'},
    )


def bundle_response(
    entries: list[dict[str, Any]],
    total: int,
    self_url: str,
    count: int,
    offset: int,
) -> Response:
    bundle_entries = [BundleEntry(resource=e) for e in entries]
    links = [{"relation": "self", "url": self_url}]
    if offset + count < total:
        next_offset = offset + count
        base = self_url.split("?")[0]
        links.append({"relation": "next", "url": f"{base}?_count={count}&_offset={next_offset}"})

    bundle = Bundle(
        type="searchset",
        total=total,
        link=links,
        entry=bundle_entries,
    )
    return Response(
        content=bundle.model_dump_json(exclude_none=True),
        status_code=200,
        media_type=VHIR_MEDIA_TYPE,
    )


def check_if_match(request: Request, current_version: int) -> None:
    """Raise 412 if If-Match header is present and doesn't match."""
    if_match = request.headers.get("If-Match")
    if if_match and if_match.strip('"') != str(current_version):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Version mismatch — resource has been modified",
        )
