"""ezyVet Appointment ↔ VHIR Appointment + Slot mapping."""
from __future__ import annotations

from typing import Any

_STATUS_MAP: dict[str, str] = {
    "confirmed": "booked",
    "booked": "booked",
    "arrived": "arrived",
    "checked in": "arrived",
    "fulfilled": "fulfilled",
    "cancelled": "cancelled",
    "no show": "noshow",
    "no-show": "noshow",
    "pending": "pending",
    "proposed": "proposed",
}


def appointment_to_vhir(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet Appointment to a VHIR AppointmentCreate payload."""
    f = ez.get("fields", {})

    status_raw = _nested_name(f.get("appointment_status_id") or f.get("status", {}))
    status = _STATUS_MAP.get(status_raw.lower().strip(), "proposed")

    animal_id = f.get("animal_id")
    contact_id = f.get("contact_id") or f.get("owner_id")
    vet_id = f.get("vet_id") or (f.get("vet", {}) or {}).get("id")
    resource_id = f.get("resource_id") or f.get("location_id")

    participants: list[dict[str, Any]] = []
    if animal_id:
        participants.append({
            "actor": {"ref": f"Animal/{animal_id}"},
            "status": "accepted",
            "required": "required",
        })
    if contact_id:
        participants.append({
            "actor": {"ref": f"Owner/{contact_id}"},
            "status": "accepted",
            "required": "required",
        })
    if vet_id:
        participants.append({
            "actor": {"ref": f"Practitioner/{vet_id}"},
            "status": "accepted",
            "required": "required",
        })

    start = _isodatetime(f.get("start_at") or f.get("date"))
    end = _isodatetime(f.get("end_at") or f.get("end_date"))
    duration_mins: int | None = None
    try:
        duration_mins = int(f.get("duration", 0) or 0) or None
    except (TypeError, ValueError):
        pass

    return {
        "resourceType": "Appointment",
        "status": status,
        "description": f.get("description") or f.get("appointment_type") or None,
        "start": start,
        "end": end,
        "minutesDuration": duration_mins,
        "participants": participants,
        "slot": [{"ref": f"Location/{resource_id}"}] if resource_id else [],
        "identifiers": [
            {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
        ],
        "extensions": {"ezyvet_id": str(ez["id"])},
    }


def slot_to_vhir(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet Resource (diary slot block) to a VHIR SlotCreate payload."""
    f = ez.get("fields", {})

    start = _isodatetime(f.get("start_at"))
    end = _isodatetime(f.get("end_at"))
    resource_id = f.get("resource_id") or str(ez["id"])

    return {
        "resourceType": "Slot",
        "status": "free",
        "start": start,
        "end": end,
        "schedule": {"ref": f"Schedule/{resource_id}"},
        "identifiers": [
            {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
        ],
        "extensions": {"ezyvet_id": str(ez["id"])},
    }


def _nested_name(val: Any) -> str:
    if isinstance(val, dict):
        return str(val.get("name", ""))
    return str(val) if val else ""


def _isodatetime(val: Any) -> str | None:
    if not val:
        return None
    s = str(val).strip()
    if not s or s == "0000-00-00":
        return None
    if s.isdigit():
        import datetime
        return datetime.datetime.fromtimestamp(int(s)).isoformat()
    return s
