"""Animal resource router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from vhir_server.api.base import bundle_response, check_if_match, resource_response
from vhir_server.auth.smart import TokenPayload, require_scope
from vhir_server.core.models import AnimalCreate
from vhir_server.storage.database import get_db
from vhir_server.storage.repository import ResourceRepository, VersionConflictError

router = APIRouter(prefix="/Animal", tags=["Animal"])
_RT = "Animal"


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_animal(
    body: AnimalCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _token: TokenPayload = Depends(require_scope(_RT, "write")),
) -> Response:
    repo = ResourceRepository(_RT, db)
    data = body.model_dump(mode="json", by_alias=True, exclude_none=True)
    created = await repo.create(data)
    return resource_response(created, status_code=201)


@router.get("/{resource_id}")
async def read_animal(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    _token: TokenPayload = Depends(require_scope(_RT, "read")),
) -> Response:
    repo = ResourceRepository(_RT, db)
    resource = await repo.read(resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail=f"Animal/{resource_id} not found")
    return resource_response(resource)


@router.put("/{resource_id}")
async def update_animal(
    resource_id: str,
    body: AnimalCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _token: TokenPayload = Depends(require_scope(_RT, "write")),
) -> Response:
    repo = ResourceRepository(_RT, db)
    existing = await repo.read(resource_id)
    if existing:
        check_if_match(request, existing["meta"]["version"])
    data = body.model_dump(mode="json", by_alias=True, exclude_none=True)
    try:
        updated = await repo.update(resource_id, data)
    except VersionConflictError as e:
        raise HTTPException(status_code=412, detail=str(e)) from e
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Animal/{resource_id} not found")
    return resource_response(updated)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    _token: TokenPayload = Depends(require_scope(_RT, "write")),
) -> None:
    repo = ResourceRepository(_RT, db)
    deleted = await repo.delete(resource_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Animal/{resource_id} not found")


@router.get("")
async def search_animals(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _token: TokenPayload = Depends(require_scope(_RT, "read")),
) -> Response:
    params = dict(request.query_params)
    count = int(params.get("_count", 20))
    offset = int(params.get("_offset", 0))
    repo = ResourceRepository(_RT, db)
    entries, total = await repo.search(params)
    return bundle_response(entries, total, str(request.url), count, offset)
