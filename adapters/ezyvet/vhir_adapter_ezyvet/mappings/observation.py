"""ezyVet Clinical Note ↔ VHIR Observation mapping."""
from __future__ import annotations

from typing import Any


def clinical_note_to_vhir(ez: dict[str, Any]) -> dict[str, Any]:
    """Map an ezyVet ClinicalNote to a VHIR ObservationCreate payload."""
    f = ez.get("fields", {})

    animal_id = f.get("animal_id")
    consultation_id = f.get("consultation_id")

    title = f.get("title") or f.get("clinical_note_type", "Clinical Note")
    text = f.get("description") or f.get("text") or f.get("notes") or ""

    effective_dt = _isodatetime(f.get("date") or f.get("created_at"))

    return {
        "resourceType": "Observation",
        "status": "final",
        "category": ["clinical-note"],
        "code": {
            "system": "http://vhir.org/CodeSystem/observation-types",
            "code": "clinical-note",
            "display": title,
        },
        "subject": {"ref": f"Animal/{animal_id}"} if animal_id else {"ref": "Animal/unknown"},
        "encounter": {"ref": f"Encounter/{consultation_id}"} if consultation_id else None,
        "effectiveDateTime": effective_dt,
        "valueString": text or None,
        "identifiers": [
            {"type": "ezyvet-id", "system": "https://api.ezyvet.com", "value": str(ez["id"])}
        ],
        "extensions": {"ezyvet_id": str(ez["id"]), "ezyvet_title": title},
    }


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
