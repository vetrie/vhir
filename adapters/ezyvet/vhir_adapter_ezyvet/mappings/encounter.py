"""ezyVet Consultation ↔ VHIR Encounter mapping."""
from __future__ import annotations

from typing import Any

_STATUS_MAP: dict[str, str] = {
    "active": "in-progress",
    "open": "in-progress",
    "closed": "finished",
    "checked out": "finished",
    "cancelled": "cancelled",
    "no show": "cancelled",
}


def encounter_to_vhir(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet Consultation to a VHIR EncounterCreate payload."""
    f = ez.get("fields", {})

    status_raw = _nested_name(f.get("consultation_status_id") or f.get("status", {}))
    status = _STATUS_MAP.get(status_raw.lower().strip(), "unknown")

    animal_id = f.get("animal_id")
    contact_id = f.get("contact_id") or f.get("owner_id")
    vet_raw = f.get("assigned_to") or f.get("vet", {})
    vet_id = vet_raw.get("id") if isinstance(vet_raw, dict) else f.get("vet_id")

    practitioners: list[dict[str, Any]] = []
    if vet_id:
        practitioners.append({
            "practitioner": {"ref": f"Practitioner/{vet_id}"},
            "role": "attending",
        })

    reason_text = f.get("reason_for_visit") or f.get("presenting_complaint") or None

    period: dict[str, Any] = {}
    if f.get("date"):
        period["start"] = _isodate(f["date"])
    if f.get("discharge_date"):
        period["end"] = _isodate(f["discharge_date"])

    return {
        "resourceType": "Encounter",
        "status": status,
        "class": "ambulatory",
        "subject": {"ref": f"Animal/{animal_id}"} if animal_id else {"ref": "Animal/unknown"},
        "owner": {"ref": f"Owner/{contact_id}"} if contact_id else None,
        "practitioners": practitioners,
        "period": period or None,
        "reasonText": reason_text,
        "identifiers": [
            {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
        ],
        "extensions": {"ezyvet_id": str(ez["id"])},
    }


def _nested_name(val: Any) -> str:
    if isinstance(val, dict):
        return str(val.get("name", ""))
    return str(val) if val else ""


def _isodate(val: Any) -> str | None:
    if not val:
        return None
    s = str(val).strip()
    if not s or s == "0000-00-00":
        return None
    if s.isdigit():
        import datetime
        return datetime.date.fromtimestamp(int(s)).isoformat()
    return s[:10]
