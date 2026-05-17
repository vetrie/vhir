"""Polling daemon — cursor-based sync from ezyVet into VHIR."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vhir_adapter_ezyvet.client import EzyVetClient
from vhir_adapter_ezyvet.config import settings
from vhir_adapter_ezyvet.mappings import (
    animal_to_vhir,
    contact_to_vhir,
    encounter_to_vhir,
    clinical_note_to_vhir,
    prescription_to_medication_request,
    dispense_item_to_medication_dispense,
    vaccination_to_vhir,
    appointment_to_vhir,
)
from vhir_adapter_ezyvet.sync.vhir_client import VHIRClient

logger = logging.getLogger(__name__)

_CURSOR_FILE = Path(".ezyvet_sync_cursor.json")

_RESOURCE_MAP: list[tuple[str, str, Any]] = [
    ("animal", "Animal", animal_to_vhir),
    ("contact", "Owner", contact_to_vhir),
    ("consultation", "Encounter", encounter_to_vhir),
    ("clinicalnote", "Observation", clinical_note_to_vhir),
    ("prescription", "MedicationRequest", prescription_to_medication_request),
    ("dispensingitem", "MedicationDispense", dispense_item_to_medication_dispense),
    ("vaccination", "Immunization", vaccination_to_vhir),
    ("appointment", "Appointment", appointment_to_vhir),
]


def _load_cursors() -> dict[str, str]:
    if _CURSOR_FILE.exists():
        try:
            return json.loads(_CURSOR_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_cursors(cursors: dict[str, str]) -> None:
    _CURSOR_FILE.write_text(json.dumps(cursors))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _sync_resource(
    ez: EzyVetClient,
    vhir: VHIRClient,
    ez_type: str,
    vhir_type: str,
    mapper: Any,
    modified_since: str | None,
) -> str:
    """Sync all pages of one ezyVet resource type into VHIR. Returns new cursor timestamp."""
    run_start = _now_iso()
    items = await ez.list_all(ez_type, modified_since=modified_since)
    logger.info("Syncing %d %s records", len(items), ez_type)
    for item in items:
        ezyvet_id = str(item.get("id", ""))
        if not ezyvet_id:
            continue
        try:
            payload = mapper(item)
            await vhir.upsert(vhir_type, payload, ezyvet_id)
        except Exception:
            logger.exception("Failed to upsert %s/%s", vhir_type, ezyvet_id)
    return run_start


async def run_poll_loop(once: bool = False) -> None:
    """Continuously poll ezyVet and push changes to VHIR.

    Set ``once=True`` in tests / one-shot runs.
    """
    cursors = _load_cursors()

    async with EzyVetClient() as ez, VHIRClient() as vhir:
        while True:
            run_start = _now_iso()
            for ez_type, vhir_type, mapper in _RESOURCE_MAP:
                cursor = cursors.get(ez_type)
                try:
                    new_cursor = await _sync_resource(ez, vhir, ez_type, vhir_type, mapper, cursor)
                    cursors[ez_type] = new_cursor
                except Exception:
                    logger.exception("Sync failed for %s", ez_type)
            _save_cursors(cursors)
            logger.info("Poll cycle complete at %s", run_start)
            if once:
                break
            await asyncio.sleep(settings.poll_interval_seconds)
