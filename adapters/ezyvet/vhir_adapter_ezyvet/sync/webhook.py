"""FastAPI webhook endpoint for ezyVet push events (resource.created / resource.updated)."""
from __future__ import annotations

import hashlib
import hmac
import logging
from collections import OrderedDict
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from vhir_adapter_ezyvet.config import settings
from vhir_adapter_ezyvet.mappings import (
    animal_to_vhir,
    appointment_to_vhir,
    clinical_note_to_vhir,
    contact_to_vhir,
    dispense_item_to_medication_dispense,
    encounter_to_vhir,
    prescription_to_medication_request,
    vaccination_to_vhir,
)
from vhir_adapter_ezyvet.sync.vhir_client import VHIRClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook/ezyvet", tags=["ezyvet-webhook"])

# Map ezyVet resource type names to (VHIR type, mapper)
_HANDLER: dict[str, tuple[str, Any]] = {
    "animal": ("Animal", animal_to_vhir),
    "contact": ("Owner", contact_to_vhir),
    "consultation": ("Encounter", encounter_to_vhir),
    "clinicalnote": ("Observation", clinical_note_to_vhir),
    "prescription": ("MedicationRequest", prescription_to_medication_request),
    "dispensingitem": ("MedicationDispense", dispense_item_to_medication_dispense),
    "vaccination": ("Immunization", vaccination_to_vhir),
    "appointment": ("Appointment", appointment_to_vhir),
}

# Tracks recently processed event IDs to handle deduplication.
# OrderedDict used as an LRU set: oldest entries are evicted on overflow
# so dedup works across a rolling window rather than clearing all at once.
_SEEN_EVENTS: OrderedDict[str, None] = OrderedDict()
_MAX_SEEN = 10_000


def _verify_signature(body: bytes, signature: str | None) -> None:
    """HMAC-SHA256 verification — only enforced when EZYVET_WEBHOOK_SECRET is set."""
    secret = settings.webhook_secret
    if not secret:
        return
    if not signature:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing webhook signature")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature.removeprefix("sha256=")):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")


async def _process_event(event: dict[str, Any]) -> None:
    event_id = str(event.get("id", ""))
    if event_id and event_id in _SEEN_EVENTS:
        logger.debug("Duplicate event %s — skipping", event_id)
        return
    if event_id:
        if len(_SEEN_EVENTS) >= _MAX_SEEN:
            _SEEN_EVENTS.popitem(last=False)  # evict oldest entry
        _SEEN_EVENTS[event_id] = None

    resource_type = str(event.get("resource_type", "")).lower()
    resource = event.get("resource", {})
    ezyvet_id = str(resource.get("id", ""))

    handler = _HANDLER.get(resource_type)
    if not handler:
        logger.warning("Unhandled ezyVet resource type: %s", resource_type)
        return

    vhir_type, mapper = handler
    try:
        payload = mapper(resource)
        async with VHIRClient() as vhir:
            await vhir.upsert(vhir_type, payload, ezyvet_id)
        logger.info("Upserted %s/%s from webhook event %s", vhir_type, ezyvet_id, event_id)
    except Exception:
        logger.exception("Failed to process event %s for %s/%s", event_id, vhir_type, ezyvet_id)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_ezyvet_signature: str | None = Header(default=None),
) -> dict[str, str]:
    """Receive ezyVet push events and enqueue them for background processing."""
    body = await request.body()
    _verify_signature(body, x_ezyvet_signature)

    payload = await request.json()
    events: list[dict[str, Any]] = (
        payload if isinstance(payload, list) else [payload]
    )
    for event in events:
        background_tasks.add_task(_process_event, event)

    return {"status": "accepted", "count": str(len(events))}
