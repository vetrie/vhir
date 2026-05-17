"""Generic CRUD repository for VHIR resources backed by Postgres JSONB."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Table, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from vhir_server.storage import tables

_TABLE_MAP: dict[str, Table] = {
    "Animal":                    tables.animal,
    "Owner":                     tables.owner,
    "Practitioner":              tables.practitioner,
    "PractitionerRole":          tables.practitioner_role,
    "Organization":              tables.organization,
    "Encounter":                 tables.encounter,
    "Observation":               tables.observation,
    "Condition":                 tables.condition_table,
    "MedicationRequest":         tables.medication_request,
    # M1
    "Group":                     tables.vhir_group,
    "Location":                  tables.location_table,
    "Device":                    tables.device,
    "DeviceMetric":              tables.device_metric,
    "Procedure":                 tables.procedure_table,
    "Immunization":              tables.immunization,
    "MedicationDispense":        tables.medication_dispense,
    "MedicationAdministration":  tables.medication_administration,
    "Appointment":               tables.appointment,
    "Schedule":                  tables.schedule_table,
    "Slot":                      tables.slot,
    # M2
    "InsuranceClaim":            tables.insurance_claim,
}


def new_id() -> str:
    return str(ULID())


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _embed_meta(body: dict[str, Any], resource_id: str, version: int) -> dict[str, Any]:
    body["id"] = resource_id
    body["meta"] = {
        "version": version,
        "lastUpdated": _now().isoformat(),
        "profiles": body.get("meta", {}).get("profiles", []) if isinstance(body.get("meta"), dict) else [],
    }
    return body


class ResourceRepository:
    def __init__(self, resource_type: str, db: AsyncSession):
        self._type = resource_type
        self._table = _TABLE_MAP[resource_type]
        self._db = db

    async def create(self, body: dict[str, Any]) -> dict[str, Any]:
        resource_id = new_id()
        body = _embed_meta(body, resource_id, version=1)
        now = _now()
        stmt = insert(self._table).values(
            id=resource_id, version=1, last_updated=now, body=body, deleted=False
        )
        await self._db.execute(stmt)
        await self._record_history(resource_id, 1, body, "create")
        await self._db.commit()
        return body

    async def read(self, resource_id: str) -> dict[str, Any] | None:
        stmt = select(self._table).where(
            self._table.c.id == resource_id,
            self._table.c.deleted == False,  # noqa: E712
        )
        row = (await self._db.execute(stmt)).one_or_none()
        return row._mapping["body"] if row else None  # type: ignore[union-attr]

    async def update(self, resource_id: str, body: dict[str, Any], if_match: int | None = None) -> dict[str, Any] | None:
        existing = await self.read(resource_id)
        if existing is None:
            return None
        current_version = existing["meta"]["version"]
        if if_match is not None and if_match != current_version:
            raise VersionConflictError(current_version)
        new_version = current_version + 1
        body = _embed_meta(body, resource_id, new_version)
        now = _now()
        stmt = (
            update(self._table)
            .where(self._table.c.id == resource_id)
            .values(version=new_version, last_updated=now, body=body)
        )
        await self._db.execute(stmt)
        await self._record_history(resource_id, new_version, body, "update")
        await self._db.commit()
        return body

    async def delete(self, resource_id: str) -> bool:
        existing = await self.read(resource_id)
        if existing is None:
            return False
        version = existing["meta"]["version"] + 1
        now = _now()
        stmt = (
            update(self._table)
            .where(self._table.c.id == resource_id)
            .values(deleted=True, last_updated=now, version=version)
        )
        await self._db.execute(stmt)
        await self._record_history(resource_id, version, existing, "delete")
        await self._db.commit()
        return True

    async def search(self, params: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
        """Simple search — returns (entries, total). Handles basic JSONB filters."""
        from vhir_server.search.engine import build_query
        stmt, count_stmt = build_query(self._table, params)
        rows = (await self._db.execute(stmt)).fetchall()
        total_row = (await self._db.execute(count_stmt)).scalar()
        entries = [r._mapping["body"] for r in rows]  # type: ignore[union-attr]
        return entries, total_row or 0

    async def _record_history(self, resource_id: str, version: int, body: dict[str, Any], operation: str) -> None:
        stmt = insert(tables.resource_history).values(
            resource_type=self._type,
            resource_id=resource_id,
            version=version,
            body=body,
            operation=operation,
        )
        await self._db.execute(stmt)


class VersionConflictError(Exception):
    def __init__(self, current_version: int):
        self.current_version = current_version
        super().__init__(f"Version conflict: current version is {current_version}")
